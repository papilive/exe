"""
Views for the ejecutor app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
from functools import wraps

from .models import ExecutableFile, ExecutableCategory, ExecutionLog
from .forms import (
    ExecutableFileUploadForm,
    PreinstalledExecutableForm,
    ExecutableSelectionForm,
    ExecutableArgumentsForm
)
from .execution import ExecutionManager

def staff_required(view_func):
    """Decorador para verificar si el usuario es staff."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "Acceso denegado. Se requieren privilegios de administrador.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def handle_unauthorized(view_func):
    """Decorador para manejar errores de autenticación."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            if isinstance(e, PermissionError):
                messages.error(request, "No tiene permisos para realizar esta acción.")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No autorizado',
                    'code': 401,
                    'detail': str(e)
                }, status=401)
            raise
    return _wrapped_view

def ensure_csrf_cookie_wrapped(view_func):
    """Decorador para asegurar que la cookie CSRF está establecida."""
    def wrapped_view(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        get_token(request)  # Forzar generación de token CSRF
        return response
    return wrapped_view

@ensure_csrf_cookie
def home(request):
    """Vista de la página principal."""
    executables = ExecutableFile.objects.filter(is_active=True).order_by('-upload_date')[:5]
    categories = ExecutableCategory.objects.all()
    return render(request, 'ejecutor/home.html', {
        'executables': executables,
        'categories': categories,
    })

def list_executables(request, category_id=None):
    """Vista para listar los ejecutables disponibles."""
    executables = ExecutableFile.objects.filter(is_active=True)
    if category_id:
        executables = executables.filter(category_id=category_id)
    categories = ExecutableCategory.objects.all()
    return render(request, 'ejecutor/list_executables.html', {
        'executables': executables,
        'categories': categories,
        'current_category': category_id,
    })

def user_login(request):
    """Vista para el login de usuarios."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'ejecutor/login.html')

def user_logout(request):
    """Vista para el logout de usuarios."""
    logout(request)
    return redirect('home')

@login_required
def check_auth_status(request):
    """Verificar el estado de autenticación del usuario."""
    return JsonResponse({
        'authenticated': True,
        'is_staff': request.user.is_staff,
        'csrf_token': get_token(request),
    })

@login_required
@staff_required
def admin_dashboard(request):
    """Vista del panel de administración."""
    executables = ExecutableFile.objects.all().order_by('-upload_date')
    categories = ExecutableCategory.objects.all()
    upload_form = ExecutableFileUploadForm()
    preinstalled_form = PreinstalledExecutableForm()
    return render(request, 'ejecutor/admin_dashboard.html', {
        'executables': executables,
        'categories': categories,
        'upload_form': upload_form,
        'preinstalled_form': preinstalled_form,
    })

@login_required
def execute_executable(request, executable_id):
    """Vista para ejecutar un archivo ejecutable."""
    executable = get_object_or_404(ExecutableFile, pk=executable_id, is_active=True)
    if request.method == 'POST':
        form = ExecutableArgumentsForm(request.POST)
        if form.is_valid():
            args = form.cleaned_data.get('command_args', '')
            manager = ExecutionManager()
            execution_id = manager.start_execution(executable, args, request.user)
            return redirect('realtime_execution', execution_id=execution_id)
    else:
        form = ExecutableArgumentsForm(initial={'command_args': executable.command_args})
    return render(request, 'ejecutor/execute_executable.html', {
        'executable': executable,
        'form': form,
    })

@login_required
def realtime_execution(request, execution_id):
    """Vista para mostrar la ejecución en tiempo real."""
    execution = get_object_or_404(ExecutionLog, execution_uuid=execution_id)
    return render(request, 'ejecutor/realtime_execution.html', {
        'execution': execution,
    })

# Admin views
@staff_required
def admin_dashboard(request):
    """Administrative dashboard."""
    executables = ExecutableFile.objects.all()
    categories = ExecutableCategory.objects.all()
    recent_logs = ExecutionLog.objects.all().order_by('-executed_at')[:10]

    context = {
        'executables': executables,
        'categories': categories,
        'recent_logs': recent_logs,
    }
    return render(request, 'ejecutor/admin_dashboard.html', context)

@staff_required
@ensure_csrf_cookie_wrapped
def upload_executable(request):
    """Vista para subir nuevos archivos ejecutables."""
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Acceso denegado. Se requieren privilegios de administrador.")
        return redirect('home')

    if request.method == 'POST':
        form = ExecutableFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            executable = form.save(commit=False)
            executable.uploaded_by = request.user
            executable.save()
            messages.success(request, f"Archivo {executable.name} subido exitosamente.")
            return redirect('admin_dashboard')
    else:
        form = ExecutableFileUploadForm()
    
    return render(request, 'ejecutor/upload_form.html', {'form': form})

@staff_required
@ensure_csrf_cookie_wrapped
def add_preinstalled(request):
    """Vista para agregar ejecutables preinstalados."""
    if request.method == 'POST':
        form = PreinstalledExecutableForm(request.POST)
        if form.is_valid():
            executable = form.save(commit=False)
            executable.uploaded_by = request.user
            executable.save()
            messages.success(request, f"Ejecutable {executable.name} agregado exitosamente.")
            return redirect('admin_dashboard')
    else:
        form = PreinstalledExecutableForm()
    
    return render(request, 'ejecutor/upload_form.html', {
        'form': form,
        'preinstalled': True
    })

@staff_required
@ensure_csrf_cookie_wrapped
def edit_executable(request, executable_id):
    """Vista para editar archivos ejecutables existentes."""
    executable = get_object_or_404(ExecutableFile, pk=executable_id)
    
    if request.method == 'POST':
        form = ExecutableFileUploadForm(request.POST, request.FILES, instance=executable)
        if form.is_valid():
            form.save()
            messages.success(request, f"Archivo {executable.name} actualizado exitosamente.")
            return redirect('admin_dashboard')
    else:
        form = ExecutableFileUploadForm(instance=executable)
    
    return render(request, 'ejecutor/upload_form.html', {
        'form': form,
        'executable': executable,
        'editing': True
    })

@staff_required
@ensure_csrf_cookie_wrapped
def toggle_executable(request, executable_id):
    """Vista para activar/desactivar ejecutables."""
    executable = get_object_or_404(ExecutableFile, pk=executable_id)
    executable.is_active = not executable.is_active
    executable.save()
    
    status = "activado" if executable.is_active else "desactivado"
    messages.success(request, f"Ejecutable {executable.name} {status} exitosamente.")
    return redirect('admin_dashboard')

@staff_required
@ensure_csrf_cookie_wrapped
def execution_logs(request):
    """Vista para ver logs de ejecución."""
    logs = ExecutionLog.objects.all().order_by('-executed_at')
    return render(request, 'ejecutor/execution_logs.html', {'logs': logs})

@staff_required
@ensure_csrf_cookie_wrapped
def check_admin_key_combination(request):
    """Endpoint para verificar combinación de teclas de admin."""
    data = json.loads(request.body)
    key_combination = data.get('combination', '')
    
    is_valid = request.user.is_authenticated and request.user.is_staff
    return JsonResponse({
        'valid': is_valid,
        'redirect': reverse('admin_dashboard') if is_valid else None
    })

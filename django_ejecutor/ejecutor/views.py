"""
Views for the ejecutor app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q

from .models import ExecutableFile, ExecutableCategory, ExecutionLog
from .forms import (
    ExecutableFileUploadForm,
    PreinstalledExecutableForm,
    ExecutableSelectionForm,
    ExecutableArgumentsForm
)

import subprocess
import os
import json
import logging
import uuid
from .execution import ExecutionManager
import platform

logger = logging.getLogger(__name__)

# Helper functions
def is_admin(user):
    """Check if user is an admin."""
    return user.is_authenticated and user.is_staff

def execute_file(executable_path, arguments=None, realtime=False):
    """
    Execute a Windows executable file and return the result.

    Args:
        executable_path: Path to the executable file
        arguments: Command line arguments
        realtime: Whether to use real-time output streaming

    Returns:
        Dictionary with execution result or execution_id for real-time execution
    """
    # Check if we're on Windows
    is_windows = platform.system() == 'Windows'

    if realtime:
        # For real-time execution, we return an execution ID
        # The actual execution happens asynchronously
        execution_id = str(uuid.uuid4())
        ExecutionManager.execute_file_async(executable_path, arguments, execution_id)

        return {
            'execution_id': execution_id,
            'realtime': True
        }
    else:
        # Traditional synchronous execution
        # This should be executed on a Windows server
        cmd = [executable_path]
        if arguments:
            cmd.extend(arguments.split())

        try:
            # If on Windows, use CREATE_NO_WINDOW flag
            creation_flags = 0
            if is_windows and hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creation_flags = subprocess.CREATE_NO_WINDOW

            # Execute the command and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=creation_flags,
                shell=True  # Security note: This is a potential security risk
            )
            stdout, stderr = process.communicate(timeout=60)  # 60 seconds timeout

            output = stdout + stderr
            exit_code = process.returncode
            success = exit_code == 0

            return {
                'success': success,
                'output': output,
                'exit_code': exit_code,
                'realtime': False
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': 'Execution timed out after 60 seconds',
                'exit_code': -1,
                'realtime': False
            }
        except Exception as e:
            return {
                'success': False,
                'output': f'Error executing file: {str(e)}',
                'exit_code': -1,
                'realtime': False
            }

# View functions
def home(request):
    """Home page view."""
    categories = ExecutableCategory.objects.all()
    recent_executables = ExecutableFile.objects.filter(is_active=True).order_by('-last_executed')[:5]

    context = {
        'categories': categories,
        'recent_executables': recent_executables,
    }
    return render(request, 'ejecutor/home.html', context)

def list_executables(request, category_id=None):
    """List available executables, optionally filtered by category."""
    query = request.GET.get('q', '')

    executables = ExecutableFile.objects.filter(is_active=True)

    category = None
    if category_id:
        category = get_object_or_404(ExecutableCategory, id=category_id)
        executables = executables.filter(category=category)

    if query:
        executables = executables.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    categories = ExecutableCategory.objects.all()

    context = {
        'executables': executables,
        'categories': categories,
        'current_category': category_id,
        'query': query,
    }
    return render(request, 'ejecutor/list_executables.html', context)

@login_required
def execute_executable(request, executable_id):
    """View for executing a selected executable."""
    executable = get_object_or_404(ExecutableFile, id=executable_id, is_active=True)

    if request.method == 'POST':
        form = ExecutableArgumentsForm(request.POST)
        if form.is_valid():
            # Check if real-time execution was requested
            use_realtime = 'realtime' in request.POST

            # Combine default arguments with user-provided arguments
            arguments = executable.command_args
            if form.cleaned_data['arguments']:
                if arguments:
                    arguments += ' ' + form.cleaned_data['arguments']
                else:
                    arguments = form.cleaned_data['arguments']

            # Get the full path to the executable
            executable_path = executable.get_full_path()
            if not executable_path or not os.path.exists(executable_path):
                messages.error(request, "El archivo ejecutable no está disponible")
                return redirect('list_executables')

            # Execute the file (with or without real-time streaming)
            result = execute_file(executable_path, arguments, realtime=use_realtime)

            # Create execution log
            execution_uuid = result.get('execution_id', str(uuid.uuid4()))

            # For real-time execution, we create a log entry that will be updated later
            log = ExecutionLog(
                execution_uuid=execution_uuid,
                executable=executable,
                user=request.user,
                success=None if use_realtime else result.get('success', False),
                output='' if use_realtime else result.get('output', ''),
                exit_code=None if use_realtime else result.get('exit_code', -1),
                ip_address=request.META.get('REMOTE_ADDR'),
                is_realtime=use_realtime,
                completed=not use_realtime
            )
            log.save()

            # Update executable statistics
            executable.last_executed = timezone.now()
            executable.execution_count += 1
            executable.save()

            if use_realtime:
                # For real-time execution, redirect to the real-time view
                return redirect('realtime_execution', execution_id=execution_uuid)
            else:
                # For traditional execution, show the result page
                context = {
                    'executable': executable,
                    'result': result,
                    'log': log,
                }
                return render(request, 'ejecutor/execution_result.html', context)
    else:
        form = ExecutableArgumentsForm()

    context = {
        'executable': executable,
        'form': form,
    }
    return render(request, 'ejecutor/execute_executable.html', context)

@login_required
def realtime_execution(request, execution_id):
    """View for displaying real-time execution results."""
    log = get_object_or_404(ExecutionLog, execution_uuid=execution_id)
    executable = log.executable

    context = {
        'executable': executable,
        'log': log,
        'execution_id': execution_id
    }
    return render(request, 'ejecutor/realtime_execution.html', context)

@user_passes_test(is_admin)
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

@user_passes_test(is_admin)
def upload_executable(request):
    """View for uploading new executable files."""
    if request.method == 'POST':
        form = ExecutableFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            executable = form.save(commit=False)
            executable.type = 'uploaded'
            executable.uploader = request.user
            executable.save()

            messages.success(request, "Archivo ejecutable subido correctamente")
            return redirect('admin_dashboard')
    else:
        form = ExecutableFileUploadForm()

    context = {
        'form': form,
        'title': 'Subir Archivo Ejecutable',
    }
    return render(request, 'ejecutor/upload_form.html', context)

@user_passes_test(is_admin)
def add_preinstalled(request):
    """View for adding preinstalled executable files."""
    if request.method == 'POST':
        form = PreinstalledExecutableForm(request.POST)
        if form.is_valid():
            executable = form.save(commit=False)
            executable.uploader = request.user
            executable.save()

            messages.success(request, "Ejecutable preinstalado registrado correctamente")
            return redirect('admin_dashboard')
    else:
        form = PreinstalledExecutableForm()

    context = {
        'form': form,
        'title': 'Registrar Ejecutable Preinstalado',
    }
    return render(request, 'ejecutor/upload_form.html', context)

@user_passes_test(is_admin)
def edit_executable(request, executable_id):
    """View for editing executable files."""
    executable = get_object_or_404(ExecutableFile, id=executable_id)

    if executable.type == 'uploaded':
        form_class = ExecutableFileUploadForm
    else:
        form_class = PreinstalledExecutableForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=executable)
        if form.is_valid():
            form.save()
            messages.success(request, "Ejecutable actualizado correctamente")
            return redirect('admin_dashboard')
    else:
        form = form_class(instance=executable)

    context = {
        'form': form,
        'executable': executable,
        'title': 'Editar Ejecutable',
    }
    return render(request, 'ejecutor/upload_form.html', context)

@user_passes_test(is_admin)
def toggle_executable(request, executable_id):
    """Toggle the active status of an executable."""
    executable = get_object_or_404(ExecutableFile, id=executable_id)
    executable.is_active = not executable.is_active
    executable.save()

    return JsonResponse({
        'success': True,
        'is_active': executable.is_active,
    })

@user_passes_test(is_admin)
def execution_logs(request):
    """View execution logs."""
    logs = ExecutionLog.objects.all().order_by('-executed_at')

    context = {
        'logs': logs,
    }
    return render(request, 'ejecutor/execution_logs.html', context)

@csrf_exempt
def check_admin_key_combination(request):
    """Check if the admin key combination was pressed.

    This is an AJAX endpoint that checks for a specific key combination
    that reveals the admin section.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            key_combination = data.get('key_combination')

            # Check for the specific key combination (e.g., Ctrl+Alt+A)
            if key_combination == 'ctrl+alt+a':
                return JsonResponse({'success': True, 'redirect': reverse('admin_dashboard')})

            return JsonResponse({'success': False})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

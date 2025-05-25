"""
URL patterns for the ejecutor app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication views
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('auth-status/', views.check_auth_status, name='auth_status'),

    # Public views
    path('', views.home, name='home'),
    path('ejecutables/', views.list_executables, name='list_executables'),
    path('ejecutables/categoria/<int:category_id>/', views.list_executables, name='list_executables_by_category'),
    path('ejecutar/<int:executable_id>/', views.execute_executable, name='execute_executable'),
    path('ejecutar/realtime/<str:execution_id>/', views.realtime_execution, name='realtime_execution'),

    # Admin views (hidden behind key combination + login)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('upload/', views.upload_executable, name='upload_executable'),
    path('add-preinstalled/', views.add_preinstalled, name='add_preinstalled'),
    path('edit/<int:executable_id>/', views.edit_executable, name='edit_executable'),
    path('toggle/<int:executable_id>/', views.toggle_executable, name='toggle_executable'),
    path('logs/', views.execution_logs, name='execution_logs'),

    # AJAX endpoints
    path('check-admin-key/', views.check_admin_key_combination, name='check_admin_key'),
]

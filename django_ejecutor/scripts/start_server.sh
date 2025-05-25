#!/bin/bash

# Script para iniciar el servidor Django con Daphne

# Función para manejar errores
handle_error() {
    echo "Error: $1"
    exit 1
}

# Asegurarse de que las variables de entorno estén configuradas
export DJANGO_SETTINGS_MODULE=ejecutor_project.settings
export PYTHONPATH=/workspaces/exe/django_ejecutor

# Configuración para GitHub Codespaces
export CODESPACE_NAME=$(echo $CODESPACE_NAME)
if [ ! -z "$CODESPACE_NAME" ]; then
    echo "Ejecutando en GitHub Codespaces: $CODESPACE_NAME"
    export DJANGO_ALLOWED_HOSTS="*,.app.github.dev"
    export CSRF_TRUSTED_ORIGINS="https://*.app.github.dev"
fi

# Iniciar Redis si no está corriendo
sudo service redis-server start

# Iniciar Xvfb
Xvfb :0 -screen 0 1024x768x24 &
export DISPLAY=:0

# Iniciar x11vnc
x11vnc -display :0 -forever -nopw &

# Iniciar noVNC
websockify --web /usr/share/novnc 6080 localhost:5900 &

# Esperar a que los servicios estén listos
sleep 2

# Inicializar WINE
WINEARCH=win64 WINEPREFIX=$HOME/.wine wineboot --init

# Ejecutar las migraciones de Django
python manage.py migrate

# Crear superusuario si no existe
python3 scripts/create_superuser.py || handle_error "No se pudo crear el superusuario"

# Iniciar el servidor Daphne
echo "Iniciando servidor en 0.0.0.0:8000..."
daphne -b 0.0.0.0 -p 8000 ejecutor_project.asgi:application
daphne -b 0.0.0.0 -p 8000 ejecutor_project.asgi:application

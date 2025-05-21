# Configuración del Proyecto en Windows

Esta guía explica paso a paso cómo configurar el proyecto Gestor de Ejecutables en un sistema Windows, necesario para la ejecución de archivos .exe.

## Requisitos Previos

1. Windows 10 o 11 (64 bits)
2. Python 3.8 o superior
3. Git (opcional, para clonar el repositorio)
4. Derechos de administrador en el sistema

## Pasos de Instalación

### 1. Instalar Python y Pip

1. Descarga el instalador de Python desde [python.org](https://www.python.org/downloads/windows/)
2. Ejecuta el instalador
3. **Importante**: Marca la casilla "Add Python to PATH" durante la instalación
4. Completa la instalación

Verifica la instalación abriendo una nueva ventana de Símbolo del Sistema (CMD) o PowerShell y ejecutando:

```
python --version
pip --version
```

### 2. Clonar o Descargar el Proyecto

**Opción 1: Usando Git:**
```
git clone <url-del-repositorio>
cd django_ejecutor
```

**Opción 2: Descargar ZIP:**
- Descarga el archivo ZIP del proyecto
- Extrae el contenido
- Navega a la carpeta extraída desde CMD o PowerShell

### 3. Crear un Entorno Virtual

```
python -m venv venv
```

### 4. Activar el Entorno Virtual

```
venv\Scripts\activate
```

El prompt debería cambiar para mostrar `(venv)` al inicio.

### 5. Instalar Dependencias

```
pip install -r requirements.txt
```

Este comando instalará Django, Channels y pywin32, necesarios para la ejecución de archivos .exe.

### 6. Crear las Carpetas de Almacenamiento

```
mkdir media\executables
mkdir preinstalled_executables
```

### 7. Aplicar Migraciones

```
python manage.py makemigrations
python manage.py migrate
```

### 8. Crear un Superusuario

```
python manage.py createsuperuser
```

Sigue las instrucciones para crear un usuario administrador.

### 9. Iniciar el Servidor

```
python manage.py runserver
```

La aplicación ahora estará disponible en `http://127.0.0.1:8000/`

## Configuración para Ejecución de Archivos .exe

### 1. Permisos de Ejecución

Asegúrate de que el usuario que ejecuta la aplicación Django tenga permisos suficientes para ejecutar archivos en el sistema. Si ejecutas la aplicación como servicio, configura el servicio para que se ejecute con una cuenta que tenga los permisos necesarios.

### 2. Ubicación de Archivos Preinstalados

Para configurar ejecutables preinstalados:

1. Coloca los archivos .exe en la carpeta `preinstalled_executables`
2. Accede a la sección de administración y añade los archivos usando la opción "Añadir Preinstalado"
3. Para la ruta, especifica el nombre del archivo relativo a la carpeta `preinstalled_executables`

### 3. Consideraciones de Seguridad

- Implementa un firewall para controlar el acceso a la aplicación
- Configura HTTPS para encriptar las comunicaciones
- Limita los permisos del usuario que ejecuta la aplicación Django
- Considera usar un software antivirus que escanee los archivos subidos
- Ejecuta la aplicación en una máquina virtual o ambiente aislado para mayor seguridad

## Solución de Problemas

### Error: No se puede ejecutar archivos .exe

- Verifica que Python y Django se estén ejecutando en Windows (no en WSL o similar)
- Comprueba los permisos del usuario que ejecuta Django
- Asegúrate de que pywin32 esté correctamente instalado: `pip install pywin32`

### Error: WebSockets no funcionan para visualización en tiempo real

- Asegúrate de que Channels y Daphne estén instalados: `pip install channels daphne`
- Verifica que el servidor ASGI esté funcionando correctamente
- Si usas un proxy inverso como Nginx, configúralo para soportar WebSockets

### Error: No se puede acceder a la aplicación desde otras máquinas

Para permitir acceso desde otras máquinas en la red:

```
python manage.py runserver 0.0.0.0:8000
```

Y asegúrate de añadir la dirección IP del servidor a ALLOWED_HOSTS en settings.py:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'IP_DEL_SERVIDOR']
```

## Despliegue en Producción

Para un entorno de producción, se recomienda:

1. Utilizar Daphne como servidor ASGI para soportar WebSockets
2. Configurar un proxy inverso como Nginx o IIS
3. Utilizar un servicio como supervisor para mantener la aplicación en ejecución
4. Implementar HTTPS con certificados SSL

### Ejemplo de Configuración con Daphne y Supervisor

1. Instala Supervisor:
```
pip install supervisor
```

2. Crea una configuración para Supervisor en `/etc/supervisor/conf.d/django_ejecutor.conf`:
```
[program:django_ejecutor]
command=C:\ruta\al\venv\Scripts\daphne.exe -b 0.0.0.0 -p 8000 ejecutor_project.asgi:application
directory=C:\ruta\al\proyecto\django_ejecutor
user=usuario_windows
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=C:\ruta\a\logs\daphne.log
```

3. Inicia Supervisor:
```
supervisord
```

4. Para controlar la aplicación:
```
supervisorctl start django_ejecutor
supervisorctl stop django_ejecutor
supervisorctl restart django_ejecutor
```

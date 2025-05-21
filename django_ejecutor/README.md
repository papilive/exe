# Gestor de Ejecutables Windows

Aplicación Django para gestionar y ejecutar archivos .exe de Windows en un entorno controlado.

## Características

- Almacenamiento y gestión de archivos ejecutables (.exe)
- Ejecución controlada de archivos en un servidor Windows
- Soporte para archivos subidos y preinstalados en el servidor
- Registro detallado de ejecuciones
- Visualización de resultados en tiempo real mediante WebSockets
- Panel de administración protegido
- Acceso de administrador oculto con combinación de teclas

## Requisitos

- Python 3.8 o superior
- Django 4.2 o superior
- Sistema operativo Windows (para la ejecución de archivos .exe)

## Instalación

1. Clonar o descargar este repositorio:

```bash
git clone <repositorio>
cd django_ejecutor
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate  # En Windows
```

3. Instalar las dependencias:

```bash
pip install django
```

4. Realizar las migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crear un superusuario:

```bash
python manage.py createsuperuser
```

6. Iniciar el servidor:

```bash
python manage.py runserver
```

## Uso

### Acceso a la aplicación

- Acceda a la aplicación en su navegador: `http://localhost:8000/`
- Puede ver y ejecutar los archivos disponibles desde la página de inicio o la lista de ejecutables

### Acceso a la administración

Existen dos formas de acceder a la administración:

1. **Panel de administración de Django**: Acceda a `http://localhost:8000/admin/` e inicie sesión con el superusuario creado.

2. **Panel de administración personalizado**:
   - Desde cualquier página, presione la combinación de teclas `Ctrl+Alt+A`
   - Inicie sesión con un usuario con permisos de staff
   - Accederá al panel personalizado para gestionar ejecutables

### Gestión de ejecutables

1. **Subir un nuevo ejecutable**:
   - Acceda al panel de administración
   - Haga clic en "Subir Ejecutable"
   - Complete el formulario con la información del ejecutable
   - Seleccione el archivo .exe a subir

2. **Añadir un ejecutable preinstalado**:
   - Acceda al panel de administración
   - Haga clic en "Añadir Preinstalado"
   - Complete el formulario con la información del ejecutable
   - Especifique la ruta relativa al directorio de ejecutables preinstalados

3. **Ejecutar un archivo**:
   - Navegue a la lista de ejecutables
   - Haga clic en "Ejecutar" junto al ejecutable deseado
   - Opcionalmente, añada argumentos adicionales
   - Haga clic en "Ejecutar" para iniciar la ejecución

## Estructura del Proyecto

- `ejecutor_project/`: Configuración del proyecto Django
- `ejecutor/`: Aplicación principal
  - `models.py`: Definición de modelos para almacenar ejecutables
  - `forms.py`: Formularios para subida y ejecución
  - `views.py`: Vistas para la aplicación
  - `urls.py`: Configuración de URLs
- `templates/`: Plantillas HTML
- `media/executables/`: Directorio para los ejecutables subidos
- `preinstalled_executables/`: Directorio para los ejecutables preinstalados

## Consideraciones de Seguridad

- Esta aplicación está diseñada para ejecutarse en un entorno controlado y seguro
- La ejecución de archivos .exe representa un riesgo potencial de seguridad
- Se recomienda implementar medidas adicionales de seguridad:
  - Ejecutar la aplicación en un entorno aislado (sandbox)
  - Limitar los permisos de ejecución en el servidor
  - Implementar análisis de malware para los archivos subidos
  - Restringir el acceso a usuarios confiables

## Ejecución en Tiempo Real

La aplicación permite visualizar los resultados de la ejecución en tiempo real:

1. Al ejecutar un archivo, marque la opción "Ver resultados en tiempo real"
2. Se mostrará una página con la salida actualizada en tiempo real
3. Cuando finalice la ejecución, podrá ver el resultado completo y el código de salida

## Configuración en Windows

Para ejecutar correctamente archivos .exe, la aplicación debe desplegarse en un servidor Windows. Consulte el archivo `WINDOWS_SETUP.md` para instrucciones detalladas sobre cómo configurar el proyecto en un entorno Windows.

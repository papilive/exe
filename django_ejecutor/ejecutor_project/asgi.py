"""
ASGI config for ejecutor_project project.
"""

import os
import django
import logging
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ejecutor_project.settings')

try:
    django.setup()
    logger.info("Django setup completed successfully")
except Exception as e:
    logger.error(f"Error during Django setup: {e}")
    raise

# Importar patrones de websocket después de configurar Django
try:
    from .routing import websocket_urlpatterns
    logger.info("WebSocket URL patterns imported successfully")
except ImportError as e:
    logger.error(f"Error importing WebSocket URL patterns: {e}")
    # Crear un patrón vacío como fallback
    websocket_urlpatterns = []

# Configuración de la aplicación ASGI
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})

logger.info("ASGI application configured successfully")
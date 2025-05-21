"""
ASGI config for ejecutor_project project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from ejecutor.consumers import ExecutionConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ejecutor_project.settings')

# Definir las rutas WebSocket
websocket_urlpatterns = [
    path('ws/execution/<str:execution_id>/', ExecutionConsumer.as_asgi()),
]

# Configuración de la aplicación ASGI con soporte para WebSockets
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

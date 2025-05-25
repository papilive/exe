"""
WebSocket URL configuration for ejecutor_project.
"""
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from ejecutor.consumers import ExecutionConsumer

websocket_urlpatterns = [
    re_path(r'ws/execution/(?P<execution_id>[^/]+)/$', ExecutionConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

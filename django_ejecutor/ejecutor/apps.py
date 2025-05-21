"""
App configuration for the ejecutor app.
"""
from django.apps import AppConfig

class EjecutorConfig(AppConfig):
    """Configuration for the ejecutor app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ejecutor'
    verbose_name = "Gestor de Ejecutables"

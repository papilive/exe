"""
Models for the ejecutor app.
"""
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import os
import uuid

def executable_file_path(instance, filename):
    """Generate a unique path for uploaded executable files."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('executables', filename)

class ExecutableCategory(models.Model):
    """Category for executable files."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría de Ejecutable"
        verbose_name_plural = "Categorías de Ejecutables"

    def __str__(self):
        return self.name

class ExecutableFile(models.Model):
    """Model for executable files."""
    TYPE_CHOICES = [
        ('uploaded', 'Subido'),
        ('preinstalled', 'Pre-instalado'),
    ]
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    file = models.FileField(upload_to=executable_file_path, null=True, blank=True, verbose_name="Archivo")
    file_path = models.CharField(max_length=500, verbose_name="Ruta del Archivo")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='uploaded', verbose_name="Tipo")
    category = models.ForeignKey(ExecutableCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subido por")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")
    last_executed = models.DateTimeField(null=True, blank=True, verbose_name="Última Ejecución")
    execution_count = models.IntegerField(default=0, verbose_name="Número de Ejecuciones")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    command_args = models.CharField(max_length=500, blank=True, verbose_name="Argumentos de Ejecución")

    class Meta:
        verbose_name = "Archivo Ejecutable"
        verbose_name_plural = "Archivos Ejecutables"

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Return the full path to the executable file."""
        if self.type == 'uploaded' and self.file:
            return self.file.path
        return os.path.join(settings.PREINSTALLED_FILES_DIR, self.file_path)

    def save(self, *args, **kwargs):
        """Override save method to update file_path for uploaded files."""
        super().save(*args, **kwargs)
        if self.type == 'uploaded' and self.file and not self.file_path:
            self.file_path = os.path.basename(self.file.name)
            super().save(update_fields=['file_path'])

class ExecutionLog(models.Model):
    """Log of executable file executions."""
    execution_uuid = models.CharField(max_length=36, unique=True, verbose_name="ID de Ejecución")
    executable = models.ForeignKey(ExecutableFile, on_delete=models.CASCADE, verbose_name="Archivo Ejecutable")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ejecución")
    success = models.BooleanField(null=True, blank=True, verbose_name="Éxito")
    output = models.TextField(blank=True, verbose_name="Salida")
    exit_code = models.IntegerField(null=True, blank=True, verbose_name="Código de Salida")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Dirección IP")
    is_realtime = models.BooleanField(default=False, verbose_name="Visualización en tiempo real")
    completed = models.BooleanField(default=False, verbose_name="Ejecución completada")

    class Meta:
        verbose_name = "Registro de Ejecución"
        verbose_name_plural = "Registros de Ejecuciones"

    def __str__(self):
        return f"{self.executable.name} - {self.executed_at}"

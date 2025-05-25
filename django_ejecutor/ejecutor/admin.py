"""
Admin configurations for the ejecutor app.
"""
from django.contrib import admin
from .models import ExecutableFile, ExecutableCategory, ExecutionLog

@admin.register(ExecutableCategory)
class ExecutableCategoryAdmin(admin.ModelAdmin):
    """Admin view for ExecutableCategory model."""
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(ExecutableFile)
class ExecutableFileAdmin(admin.ModelAdmin):
    """Admin view for ExecutableFile model."""
    list_display = ('name', 'category', 'type', 'upload_date', 'last_executed', 'execution_count', 'is_active')
    list_filter = ('type', 'category', 'is_active')
    search_fields = ('name', 'description', 'file_path')
    readonly_fields = ('upload_date', 'last_executed', 'execution_count')

    def get_fieldsets(self, request, obj=None):
        """Devuelve los fieldsets según el tipo de ejecutable."""
        fieldsets = [
            ('Información Básica', {
                'fields': ('name', 'description', 'category', 'type', 'is_active')
            }),
            ('Metadatos', {
                'fields': ('uploader', 'upload_date', 'last_executed', 'execution_count')
            }),
        ]

        # Si es un ejecutable subido, mostrar el campo de archivo
        if obj is None or obj.type == 'uploaded':
            fieldsets.insert(1, ('Archivo Subido', {
                'fields': ('file', 'command_args')
            }))
        # Si es un ejecutable pre-instalado, mostrar el campo de ruta
        else:
            fieldsets.insert(1, ('Archivo Pre-instalado', {
                'fields': ('file_path', 'command_args')
            }))

        return fieldsets

@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    """Admin view for ExecutionLog model."""
    list_display = ('executable', 'user', 'executed_at', 'success', 'exit_code', 'ip_address')
    list_filter = ('success', 'executable', 'user')
    search_fields = ('executable__name', 'output')
    readonly_fields = ('executable', 'user', 'executed_at', 'success', 'output', 'exit_code', 'ip_address')
    fieldsets = (
        ('Ejecución', {
            'fields': ('executable', 'user', 'executed_at')
        }),
        ('Resultado', {
            'fields': ('success', 'exit_code', 'output')
        }),
        ('Información Adicional', {
            'fields': ('ip_address',)
        }),
    )

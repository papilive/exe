"""
URL configuration for ejecutor_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Disable default admin interface
admin.site.site_header = 'Papiweb Admin'
admin.site.site_title = 'Papiweb Admin'
admin.site.index_title = 'Administración'
admin.autodiscover()
admin.site.enable_nav_sidebar = False

urlpatterns = [
    # No incluimos el admin de Django por defecto
    # path('admin/', admin.site.urls),
    path('', include('ejecutor.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

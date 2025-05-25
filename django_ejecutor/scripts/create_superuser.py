#!/usr/bin/env python
"""
Script para crear un superusuario por defecto.
"""
import os
import sys
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ejecutor_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.utils import IntegrityError

def create_superuser():
    """Crear superusuario por defecto."""
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            print('Superusuario creado exitosamente.')
            print('Usuario: admin')
            print('Contraseña: adminpassword')
        else:
            print('El superusuario ya existe.')
    except IntegrityError:
        print('Error: No se pudo crear el superusuario.')
        sys.exit(1)

if __name__ == '__main__':
    create_superuser()

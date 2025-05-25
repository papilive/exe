#!/bin/bash

# Script para verificar la configuración del entorno

echo "Verificando el entorno de ejecución..."

# Verificar Python y Django
echo -n "Python version: "
python --version
echo -n "Django version: "
python -m django --version

# Verificar Wine
if command -v wine &> /dev/null; then
    echo -n "Wine version: "
    wine --version
    echo "Wine prefix: $WINEPREFIX"
else
    echo "WARNING: Wine no está instalado"
fi

# Verificar directorios necesarios
echo -e "\nVerificando directorios:"
DIRS=(
    "media/executables"
    "preinstalled_executables"
    "staticfiles"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir existe"
    else
        echo "✗ $dir no existe"
    fi
done

# Verificar base de datos
echo -e "\nVerificando base de datos:"
if [ -f "db.sqlite3" ]; then
    echo "✓ Base de datos existe"
else
    echo "✗ Base de datos no existe"
fi

# Verificar configuración de Wine
if [ -d "$HOME/.wine" ]; then
    echo -e "\nConfiguración de Wine:"
    echo "✓ Prefix de Wine existe en $HOME/.wine"
    ls -l "$HOME/.wine/drive_c"
else
    echo "✗ Prefix de Wine no encontrado"
fi

echo -e "\nVerificación completada."

#!/bin/bash

# Script para configurar Wine para el servidor Django Ejecutor

# Verificar si Wine está instalado
if ! command -v wine &> /dev/null; then
    echo "Wine no está instalado. Por favor, instálelo primero."
    echo "En Ubuntu/Debian: sudo apt-get install wine64 wine32"
    exit 1
fi

# Crear directorio .wine si no existe
WINE_PREFIX="$HOME/.wine"
if [ ! -d "$WINE_PREFIX" ]; then
    echo "Inicializando prefix de Wine..."
    WINEARCH=win64 WINEPREFIX="$WINE_PREFIX" wineboot --init
fi

# Configurar variables de entorno
export WINEPREFIX="$WINE_PREFIX"
export WINEARCH=win64
export WINEDEBUG=-all

# Verificar la instalación
echo "Versión de Wine:"
wine --version

echo "Configuración de Wine completada."
echo "WINEPREFIX=$WINEPREFIX"
echo "WINEARCH=$WINEARCH"

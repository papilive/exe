#!/bin/bash
# Script de instalación y ejecución automática de titus.exe con entorno gráfico, VNC, noVNC y DOSBox opcional
# Uso: ./setup_titus_novnc.sh [--dosbox]

set -e

# 1. Instalación de dependencias
sudo apt-get update
sudo apt-get install -y wine xvfb x11vnc wget unzip python3-pip xterm

# Instalar DOSBox si se solicita
INSTALL_DOSBOX=false
for arg in "$@"; do
  if [ "$arg" == "--dosbox" ]; then
    INSTALL_DOSBOX=true
  fi
done
if $INSTALL_DOSBOX; then
  sudo apt-get install -y dosbox
fi

# 2. Instalar noVNC si no existe
NOVNC_DIR="/opt/novnc"
if [ ! -d "$NOVNC_DIR" ]; then
  sudo mkdir -p $NOVNC_DIR
  sudo wget -qO- https://github.com/novnc/noVNC/archive/refs/heads/master.zip | sudo bsdtar -xvf- -C $NOVNC_DIR --strip-components=1
  sudo apt-get install -y websockify
fi

# 3. Variables de entorno
EXE_PATH="/workspaces/exe/preinstalled_executables/titus.exe"
XVFB_DISPLAY=":1"
VNC_PORT=5901
NOVNC_PORT=6080

# 4. Lanzar entorno gráfico virtual y VNC
Xvfb $XVFB_DISPLAY -screen 0 1024x768x16 &
sleep 2
x11vnc -display $XVFB_DISPLAY -nopw -forever -bg -rfbport $VNC_PORT

# 5. Lanzar xterm y Wine/DOSBox según opción
DISPLAY=$XVFB_DISPLAY xterm &
if $INSTALL_DOSBOX; then
  dosbox "$EXE_PATH" &
else
  DISPLAY=$XVFB_DISPLAY wine "$EXE_PATH" &
fi

# 6. Lanzar noVNC
$NOVNC_DIR/utils/novnc_proxy --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &

# 7. Mensaje final
echo "\nEntorno listo. Accede a titus.exe vía navegador en: http://localhost:$NOVNC_PORT/vnc.html"
if $INSTALL_DOSBOX; then
  echo "(Ejecución usando DOSBox)"
else
  echo "(Ejecución usando Wine)"
fi

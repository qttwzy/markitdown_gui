#!/bin/bash
set -e

PIDS=()

cleanup() {
    echo "Shutting down..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

rm -f /tmp/.X0-lock /tmp/.X11-unix/X0 2>/dev/null || true
mkdir -p /tmp/.X11-unix

RESOLUTION="${VNC_RESOLUTION:-1280x800}"
VNC_PORT="${VNC_PORT:-5900}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

echo "Starting Xvfb with resolution ${RESOLUTION}..."
Xvfb :0 -screen 0 "${RESOLUTION}x24" -nolisten tcp &
XVFB_PID=$!
PIDS+=($XVFB_PID)

sleep 2

if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi
echo "Xvfb started (PID: $XVFB_PID)"

VNC_ARGS="-display :0 -forever -shared -noxdamage -noxrecord -noxfixes"
if [ -n "$VNC_PASSWORD" ]; then
    VNC_PASSFILE="/tmp/.vnc_passwd"
    echo -n "$VNC_PASSWORD" | vncpasswd -f > "$VNC_PASSFILE"
    chmod 600 "$VNC_PASSFILE"
    x11vnc $VNC_ARGS -rfbauth "$VNC_PASSFILE" &
else
    x11vnc $VNC_ARGS -nopw &
fi
VNC_PID=$!
PIDS+=($VNC_PID)

sleep 1

if ! kill -0 $VNC_PID 2>/dev/null; then
    echo "ERROR: x11vnc failed to start"
    exit 1
fi
echo "x11vnc started (PID: $VNC_PID)"

NOVNC_DIR="/usr/share/novnc"
if [ ! -d "$NOVNC_DIR" ]; then
    NOVNC_DIR="/usr/share/novnc/web"
fi

websockify --web="$NOVNC_DIR" ${NOVNC_PORT} localhost:${VNC_PORT} &
NOVNC_PID=$!
PIDS+=($NOVNC_PID)

sleep 1

if ! kill -0 $NOVNC_PID 2>/dev/null; then
    echo "ERROR: websockify/noVNC failed to start"
    exit 1
fi
echo "noVNC started (PID: $NOVNC_PID)"

echo ""
echo "============================================"
echo "  MarkItDown GUI - Docker Container"
echo "============================================"
echo ""
echo "  noVNC (Web Browser):"
echo "    http://localhost:${NOVNC_PORT}/vnc.html"
echo ""
echo "  VNC Client:"
echo "    localhost:${VNC_PORT}"
echo ""
if [ -n "$VNC_PASSWORD" ]; then
    echo "  VNC Password: ********"
else
    echo "  VNC Password: (none)"
fi
echo ""
echo "  Input directory:  /app/input"
echo "  Output directory: /app/output"
echo "============================================"
echo ""

cd /app
python main.py &
APP_PID=$!
PIDS+=($APP_PID)

while kill -0 $XVFB_PID 2>/dev/null && kill -0 $APP_PID 2>/dev/null; do
    sleep 2
done

echo "A process has exited, shutting down..."

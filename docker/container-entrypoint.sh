#!/bin/sh
set -eu

export DISPLAY="${DISPLAY:-:0}"
NOVNC_PORT="${NOVNC_PORT:-6080}"
SCREEN_GEOMETRY="${SCREEN_GEOMETRY:-1440x900x24}"
DISPLAY_NUMBER="${DISPLAY##*:}"
DISPLAY_NUMBER="${DISPLAY_NUMBER%%.*}"

rm -f "/tmp/.X${DISPLAY_NUMBER}-lock" "/tmp/.X11-unix/X${DISPLAY_NUMBER}"

Xvfb "$DISPLAY" -screen 0 "$SCREEN_GEOMETRY" -nolisten tcp -ac \
    >/tmp/xvfb.log 2>&1 &

attempt=0
until xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        cat /tmp/xvfb.log >&2
        echo "Virtual display did not start" >&2
        exit 1
    fi
    sleep 1
done

x11vnc -display "$DISPLAY" -forever -shared -nopw -localhost -rfbport 5900 \
    >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc "$NOVNC_PORT" 127.0.0.1:5900 \
    >/tmp/websockify.log 2>&1 &

/opt/venv/bin/python migrate.py

exec "$@"

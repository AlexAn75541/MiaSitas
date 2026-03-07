#!/bin/sh
set -e

# If settings.json exists in /data (MCManager mount), use it
if [ -f /data/settings.json ]; then
    echo "[Entrypoint] Using settings.json from /data"
    cp /data/settings.json /app/settings.json
fi

# Redirect logs to /data/logs if /data is mounted
if [ -d /data ]; then
    mkdir -p /data/logs
    # Symlink /app/logs → /data/logs so the bot writes logs to /data
    rm -rf /app/logs
    ln -sf /data/logs /app/logs
fi

exec python -u main.py

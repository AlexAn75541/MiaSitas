#!/bin/sh
set -e

# Detect mount directory used by MCSManager (/app or /data)
CONFIG_DIR="/data"
if [ -f "/app/settings.json" ] || [ -d "/app" -a ! -d "/data" ]; then
    CONFIG_DIR="/app"
fi

echo "[Entrypoint] Code root: /src, Mount target: ${CONFIG_DIR}"

# 1. Config file resolution
if [ -f "${CONFIG_DIR}/settings.json" ]; then
    echo "[Entrypoint] Found ${CONFIG_DIR}/settings.json. Copying to /src..."
    cp "${CONFIG_DIR}/settings.json" /src/settings.json
elif [ -f "/data/settings.json" ]; then
    echo "[Entrypoint] Found /data/settings.json. Copying to /src..."
    cp "/data/settings.json" /src/settings.json
else
    if [ ! -f "/src/settings.json" ] && [ -f "/src/settings Example.json" ]; then
        echo "[Entrypoint] Initializing settings.json from template..."
        cp "/src/settings Example.json" /src/settings.json
        if [ -d "${CONFIG_DIR}" ]; then
            cp "/src/settings Example.json" "${CONFIG_DIR}/settings.json"
        fi
    fi

    # Hydrate environment variables if no pre-existing settings file
    echo "[Entrypoint] Hydrating settings.json from environment variables..."
    python3 -c "
import os, json

path = '/src/settings.json'
try:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

env_map = {
    'TOKEN': ('token', str),
    'CLIENT_ID': ('client_id', int),
    'DEFAULT_PREFIX': ('prefix', str),
    'EMBED_COLOR': ('embed_color', str),
    'OWNER_IDS': ('owner_ids', lambda v: [int(x.strip()) for x in v.split(',') if x.strip()]),
    'BOT_ACCESS_USER': ('bot_access_user', lambda v: [int(x.strip()) for x in v.split(',') if x.strip()]),
    'COLOR_PLAYING': ('color_playing', str),
    'COLOR_PAUSED': ('color_paused', str),
    'SPOTIFY_CLIENT_ID': ('spotify_client_id', str),
    'SPOTIFY_CLIENT_SECRET': ('spotify_client_secret', str),
    'GENIUS_TOKEN': ('genius_token', str),
    'MUSIXMATCH_TOKEN': ('musixmatch_token', str),
    'SEARCH_PLATFORM': ('default_search_platform', str),
    'LYRICS_PLATFORM': ('lyrics_platform', str),
    'IPC_ROUTES': ('ipc_routes', str),
    'VERSION': ('version', str),
}

updated = False
for env_k, (cfg_k, transform) in env_map.items():
    val = os.getenv(env_k)
    if val:
        try:
            cfg[cfg_k] = transform(val)
            updated = True
        except Exception:
            pass

mongo_url = os.getenv('MONGODB_URL') or os.getenv('MONGO_URI')
if mongo_url:
    cfg.setdefault('mongodb', {})['url'] = mongo_url
    updated = True

mongo_name = os.getenv('MONGODB_NAME')
if mongo_name:
    cfg.setdefault('mongodb', {})['db_name'] = mongo_name
    updated = True

if updated:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
"
fi

# 2. Redirect logs to host mount directory
if [ -d "${CONFIG_DIR}" ]; then
    mkdir -p "${CONFIG_DIR}/logs"
    rm -rf /src/logs
    ln -sf "${CONFIG_DIR}/logs" /src/logs
elif [ -d "/data" ]; then
    mkdir -p /data/logs
    rm -rf /src/logs
    ln -sf /data/logs /src/logs
fi

# 3. Always execute from /src
cd /src
exec python -u /src/main.py

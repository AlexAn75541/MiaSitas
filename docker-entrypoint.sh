#!/bin/sh
set -e

# Base configuration template priority: /data/settings.json -> /app/settings.json -> /app/settings Example.json
if [ -f /data/settings.json ]; then
    echo "[Entrypoint] Using settings.json from /data"
    cp /data/settings.json /app/settings.json
elif [ ! -f /app/settings.json ] && [ -f "/app/settings Example.json" ]; then
    echo "[Entrypoint] Initializing settings.json from template"
    cp "/app/settings Example.json" /app/settings.json
fi

# Hydrate environment variables into /app/settings.json
if [ -f /app/settings.json ]; then
    python3 -c "
import os, json

path = '/app/settings.json'
try:
    with open(path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
except Exception:
    cfg = {}

env_map = {
    'TOKEN': ('TOKEN', str),
    'CLIENT_ID': ('CLIENT_ID', int),
    'DEFAULT_PREFIX': ('default_prefix', str),
    'EMBED_COLOR': ('embed_color', str),
    'OWNER_IDS': ('owner_ids', lambda v: [int(x.strip()) for x in v.split(',') if x.strip()]),
    'BOT_ACCESS_USER': ('bot_access_user', lambda v: [int(x.strip()) for x in v.split(',') if x.strip()]),
    'COLOR_PLAYING': ('color_playing', str),
    'COLOR_PAUSED': ('color_paused', str),
    'SPOTIFY_CLIENT_ID': ('spotify_client_id', str),
    'SPOTIFY_CLIENT_SECRET': ('spotify_client_secret', str),
    'GENIUS_TOKEN': ('genius_token', str),
    'MUSIXMATCH_TOKEN': ('musixmatch_token', str),
    'SEARCH_PLATFORM': ('search_platform', str),
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

# Mount logs in /data/logs if /data is present
if [ -d /data ]; then
    mkdir -p /data/logs
    rm -rf /app/logs
    ln -sf /data/logs /app/logs
fi

exec python -u main.py

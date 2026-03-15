#!/bin/bash

MATOMO_URL="${MATOMO_URL:-http://matomo:80}"
MATOMO_TOKEN="${MATOMO_TOKEN:-changeme}"
MATOMO_SITE_ID="${MATOMO_SITE_ID:-1}"
LOG_FILE="/var/log/apache2/access.log"
IMPORT_SCRIPT="/var/www/html/misc/log-analytics/import_logs.py"
AUTH_FILE="/tmp/matomo-auth.cfg"

echo "[importer] Starte Matomo Log Importer..."

pip install requests --quiet --root-user-action=ignore 2>/dev/null

# Auth-Config erstellen
printf '[auth]\ntoken_auth=%s\n' "$MATOMO_TOKEN" > "$AUTH_FILE"
chmod 600 "$AUTH_FILE"

# Warte auf Matomo
echo "[importer] Warte auf Matomo..."
while true; do
    STATUS=$(python3 -c "
import urllib.request
try:
    urllib.request.urlopen('$MATOMO_URL/index.php', timeout=5)
    print('ok')
except:
    print('fail')
" 2>/dev/null)
    if [ "$STATUS" = "ok" ]; then break; fi
    sleep 5
done
echo "[importer] Matomo erreichbar."

# Warte auf Log
while [ ! -s "$LOG_FILE" ]; do
    sleep 3
done
echo "[importer] Log gefunden — starte Import..."

# Hauptloop
while true; do
    echo "[importer] Importiere $LOG_FILE ..."
    python3 "$IMPORT_SCRIPT" \
        --url="$MATOMO_URL" \
        --auth-config="$AUTH_FILE" \
        --idsite="$MATOMO_SITE_ID" \
        --enable-http-errors \
        --enable-http-redirects \
        --enable-static \
        --enable-bots \
        --recorders=2 \
        "$LOG_FILE" 2>&1 | tail -10

    # Archivierung anstoßen
    docker exec bot-lab-matomo php /var/www/html/console core:archive \
        --force-all-websites --url="$MATOMO_URL" 2>/dev/null || true

    echo "[importer] Nächster Lauf in 60s."
    sleep 60
done
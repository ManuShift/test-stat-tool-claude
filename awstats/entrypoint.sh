#!/bin/bash

WEBSERVER_LOG="/var/log/apache2/access.log"
CONF="bot-lab"
LIB_DIR="/awstats-lib"

echo "[awstats] Container startet..."
mkdir -p /var/log/awstats-apache "$LIB_DIR"

# ── Log-Datei lesbar machen (Apache schreibt als root:adm, wir laufen als root) ──
chmod o+r /var/log/apache2/access.log 2>/dev/null || true

# ── Dateien ins lokale Volume exportieren (nur wenn noch nicht vorhanden) ──
if [ ! -f "$LIB_DIR/robots.pm" ]; then
    echo "[awstats] Exportiere robots.pm → ./awstats/lib/robots.pm"
    cp /usr/share/awstats/lib/robots.pm "$LIB_DIR/robots.pm"
fi

if [ ! -f "$LIB_DIR/awstats.pl" ]; then
    echo "[awstats] Exportiere awstats.pl → ./awstats/lib/awstats.pl"
    cp /usr/lib/cgi-bin/awstats.pl "$LIB_DIR/awstats.pl"
fi

if [ ! -f "$LIB_DIR/README.txt" ]; then
    cat > "$LIB_DIR/README.txt" << 'README'
AWStats lokale Dateien
======================

robots.pm   — Bot/Crawler Datenbank
            → hier KI-Bots eintragen (RobotsSearchIDOrder_listx + RobotsHashIDLib)
            → nach Änderung: docker compose restart awstats

awstats.pl  — Hauptskript (zur Referenz, normalerweise nicht bearbeiten)

Workflow für eigene Bot-Einträge:
1. robots.pm in VS Code öffnen
2. Nach "gptbot" suchen — Struktur der bestehenden Einträge anschauen
3. Neue KI-Bots nach gleichem Muster eintragen
4. docker compose restart awstats
5. docker compose exec awstats awstats.pl -config=bot-lab -update -LogFile=/var/log/apache2/access.log
README
fi

# ── Geänderte robots.pm einspielen ──
if [ -f "$LIB_DIR/robots.pm" ]; then
    echo "[awstats] Lade robots.pm aus lokalem Volume..."
    cp "$LIB_DIR/robots.pm" /usr/share/awstats/lib/robots.pm
fi

echo "[awstats] ServerName setzen..."
echo "ServerName localhost" >> /etc/apache2/apache2.conf

# ── Warte auf Log ──
echo "[awstats] Warte auf $WEBSERVER_LOG ..."
until [ -s "$WEBSERVER_LOG" ]; do
    sleep 3
done

# Berechtigungen bei jedem Start sicherstellen
chmod o+r "$WEBSERVER_LOG" 2>/dev/null || true

echo "[awstats] Log gefunden — starte ersten Import..."
awstats.pl -config=$CONF -update 2>&1

# ── Apache starten ──
echo "[awstats] Starte Apache (Web-UI)..."
source /etc/apache2/envvars
apache2ctl start 2>&1 || true

echo "[awstats] Bereit — http://localhost:18081"

# ── Update-Loop ──
while true; do
    sleep 60
    chmod o+r "$WEBSERVER_LOG" 2>/dev/null || true
    if [ -f "$LIB_DIR/robots.pm" ]; then
        cp "$LIB_DIR/robots.pm" /usr/share/awstats/lib/robots.pm
    fi
    echo "[awstats] Update..."
    awstats.pl -config=$CONF -update 2>&1 || true
    apache2ctl status > /dev/null 2>&1 || apache2ctl start 2>&1 || true
done

#!/bin/bash
set -e

mkdir -p /var/log/matomo-apache

# Apache-Log-Pfade umleiten
sed -i \
    -e 's|ErrorLog \${APACHE_LOG_DIR}|ErrorLog /var/log/matomo-apache|g' \
    -e 's|CustomLog \${APACHE_LOG_DIR}|CustomLog /var/log/matomo-apache|g' \
    /etc/apache2/apache2.conf 2>/dev/null || true

sed -i \
    -e 's|CustomLog \${APACHE_LOG_DIR}|CustomLog /var/log/matomo-apache|g' \
    /etc/apache2/conf-enabled/other-vhosts-access-log.conf 2>/dev/null || true

echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Originalen Matomo-Entrypoint mit apache2-foreground aufrufen
exec /entrypoint.sh apache2-foreground

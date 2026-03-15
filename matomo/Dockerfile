FROM matomo:apache

# Eigenes Log-Verzeichnis damit kein Konflikt mit dem logs-Volume entsteht
RUN mkdir -p /var/log/matomo-apache && \
    sed -i \
        -e 's|ErrorLog ${APACHE_LOG_DIR}|ErrorLog /var/log/matomo-apache|g' \
        -e 's|CustomLog ${APACHE_LOG_DIR}|CustomLog /var/log/matomo-apache|g' \
        /etc/apache2/apache2.conf && \
    sed -i \
        -e 's|CustomLog ${APACHE_LOG_DIR}|CustomLog /var/log/matomo-apache|g' \
        /etc/apache2/conf-enabled/other-vhosts-access-log.conf && \
    echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Kein eigener Entrypoint nötig — Original funktioniert

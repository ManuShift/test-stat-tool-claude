FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    awstats \
    apache2 \
    libgeo-ip-perl \
    libnet-ip-perl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# awstats.pl in PATH
RUN ln -sf /usr/lib/cgi-bin/awstats.pl /usr/local/bin/awstats.pl && \
    chmod +x /usr/lib/cgi-bin/awstats.pl

# CGI-Modul, Log-Verzeichnis
RUN a2enmod cgid && \
    mkdir -p /var/lib/awstats /var/log/awstats-apache

# Alle Apache-internen Log-Pfade umleiten (kein Konflikt mit Volume)
RUN sed -i \
    -e 's|ErrorLog \${APACHE_LOG_DIR}|ErrorLog /var/log/awstats-apache|g' \
    -e 's|CustomLog \${APACHE_LOG_DIR}|CustomLog /var/log/awstats-apache|g' \
    /etc/apache2/apache2.conf && \
    sed -i \
    -e 's|CustomLog \${APACHE_LOG_DIR}|CustomLog /var/log/awstats-apache|g' \
    /etc/apache2/conf-enabled/other-vhosts-access-log.conf && \
    echo "ServerName localhost" >> /etc/apache2/apache2.conf

# AWStats-Assets verlinken
RUN ln -sf /usr/share/awstats/wwwroot /var/www/html/awstats

COPY awstats-apache.conf /etc/apache2/sites-enabled/000-default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]

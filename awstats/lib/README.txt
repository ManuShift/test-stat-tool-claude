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

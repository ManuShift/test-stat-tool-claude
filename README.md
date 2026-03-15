# Bot-Lab — KI-Bot Tracking Testumgebung (Apache)

Dockerisierte Testumgebung zum Vergleich von serverseitigen Analyse-Tools
für die Erkennung von KI-Bot-Zugriffen im Apache Access-Log.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│  Docker Network: bot-net                                │
│                                                         │
│  ┌──────────┐   HTTP-Requests   ┌─────────────────┐    │
│  │log-gene- │ ───────────────▶  │  Apache 2.4     │    │
│  │rator     │  (echte User +    │  :8080          │    │
│  │(Python)  │   KI-Bots)        └────────┬────────┘    │
│  └──────────┘                            │ access.log  │
│                                          ▼             │
│                                   ./logs/              │
│                                   access.log           │
│                                    │       │           │
│                          ┌─────────┘       └────────┐  │
│                          ▼                          ▼  │
│                  ┌──────────────┐       ┌──────────────┐│
│                  │  GoAccess    │       │   AWStats    ││
│                  │  :8888       │       │   :8081      ││
│                  │  (Realtime)  │       │  (Historisch)││
│                  └──────────────┘       └──────────────┘│
│                                                         │
│                  ┌──────────────────────────────────┐   │
│                  │  Python Analyzer (analyzer)      │   │
│                  │  UA-Matching + rDNS + Compliance │   │
│                  │  → ./scripts/output/report.txt   │   │
│                  └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Schnellstart

```bash
# 1. Umgebung starten
docker compose up -d

# 2. Log-Generator läuft automatisch (echte User + KI-Bots)
docker compose logs -f log-generator

# 3. Dashboards öffnen
open http://localhost:8888   # GoAccess (Realtime)
open http://localhost:8081   # AWStats
open http://localhost:8080   # Apache Testseite
```

## Tools im Vergleich

### GoAccess — http://localhost:8888
- **Stärke:** Realtime-Dashboard, sofort sichtbar wer gerade crawlt
- **Bot-Erkennung:** Eingebaute Crawler-DB, erkennt GPTBot/ClaudeBot automatisch
- **Schwäche:** Keine rDNS-Verifikation, nur UA-basiert
- **Für Thesis:** Gut für Live-Demos und schnelle Übersicht

### AWStats — http://localhost:8081
- **Stärke:** Historische Auswertung, Robots/Bots-Sektion eingebaut
- **Bot-Erkennung:** Interne Bot-DB + konfigurierbar
- **Schwäche:** Muss manuell aktualisiert werden, kein Realtime
- **Für Thesis:** Gut für langfristige Analysen, etablierter Standard

### Python Analyzer (scripts/analyze.py)
- **Stärke:** Vollständig anpassbar, rDNS-Verifikation, Compliance-Check
- **Bot-Erkennung:** UA-Matching + forward-confirmed rDNS
- **robots.txt Compliance:** Prüft ob Bots /private/ trotz Disallow aufrufen
- **Für Thesis:** Zeigt was eigene Implementierung leisten kann

## Einzelne Befehle

```bash
# Analyzer manuell ausführen
docker compose run --rm analyzer python3 /app/analyze.py --log /logs/access.log

# Log in Echtzeit verfolgen
tail -f ./logs/access.log

# Nur Bot-Einträge filtern
grep -iE "gptbot|claudebot|perplexitybot|anthropic|google-extended|amazonbot|ccbot" \
     ./logs/access.log

# Nur /private/-Zugriffe (Compliance-Verletzungen)
grep "/private/" ./logs/access.log

# robots.txt-Abrufe
grep "robots.txt" ./logs/access.log

# Status-Code-Verteilung
awk '{print $9}' ./logs/access.log | sort | uniq -c | sort -rn

# GoAccess direkt im Terminal (ohne Docker)
goaccess ./logs/access.log --log-format=COMBINED

# AWStats manuell aktualisieren
docker compose exec awstats awstats.pl -config=bot-lab -update

# Alle Container stoppen
docker compose down

# Mit Logs löschen
docker compose down -v
rm -f ./logs/*.log
```

## Verzeichnisstruktur

```
bot-lab/
├── docker-compose.yml
├── apache/
│   ├── conf/
│   │   └── httpd.conf          # Apache-Konfiguration (combined log format)
│   └── html/                   # Testseiten inkl. robots.txt, sitemap.xml
├── awstats/
│   ├── conf/
│   │   └── awstats.bot-lab.conf
│   └── data/                   # AWStats-Datenbank (persistent)
├── goaccess/
│   ├── goaccess.conf
│   └── html/                   # GoAccess HTML-Report
├── logs/                       # Apache access.log + error.log (geshared)
└── scripts/
    ├── generator.py            # Simuliert echte User + 9 KI-Bots
    ├── analyze.py              # UA-Matching + rDNS + Compliance
    ├── Dockerfile.generator
    ├── Dockerfile.analyzer
    └── output/
        └── report.txt          # Analyzer-Output
```

## Simulierte KI-Bots

| Bot | UA-String | robots.txt | Besonderheit |
|-----|-----------|------------|--------------|
| GPTBot | `GPTBot/1.0` | ✅ respektiert | OpenAI Crawler |
| ChatGPT-User | `ChatGPT-User/1.0` | ✅ | OpenAI User-Triggered |
| ClaudeBot | `ClaudeBot/1.0` | ✅ | Anthropic |
| anthropic-ai | `anthropic-ai/1.0` | ✅ | Anthropic (alt) |
| PerplexityBot | `PerplexityBot/1.0` | ✅ | Perplexity |
| Google-Extended | `Google-Extended` | ✅ | Google AI Training |
| Amazonbot | `Amazonbot/0.1` | ✅ | Amazon |
| CCBot | `CCBot/2.0` | ❌ ignoriert | Common Crawl — verletzt /private/ |
| Fake-Browser-Bot | Chrome UA | ❌ | Verschleierter Bot — nicht erkennbar |

Der **Fake-Browser-Bot** ist für die Thesis besonders interessant:
er verwendet einen normalen Chrome UA und ist daher per UA-Matching nicht erkennbar.
Nur über IP-Analyse / Verhaltensanomalien (kein JS, kein Referer, hohe Frequenz) detektierbar.

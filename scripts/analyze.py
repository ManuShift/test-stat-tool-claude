"""
Bot-Lab Analyzer
Liest das Apache access.log und führt durch:
  1. User-Agent-basierte Bot-Erkennung
  2. rDNS-Verifikation (forward-confirmed reverse DNS)
  3. robots.txt-Compliance-Check (/private/-Zugriffe)
  4. Tabellarischen Report nach /output/report.txt
"""

import re
import argparse
import socket
from collections import defaultdict
from datetime import datetime
from tabulate import tabulate

# ─── Bekannte KI-Bot UA-Strings (Teilstring-Match, case-insensitive) ─────────
AI_BOT_SIGNATURES = {
    "GPTBot":         "openai.com",
    "ChatGPT-User":   "openai.com",
    "ClaudeBot":      "anthropic.com",
    "anthropic-ai":   "anthropic.com",
    "PerplexityBot":  "perplexity.ai",
    "Google-Extended":"google.com",
    "Amazonbot":      "amazon.com",
    "CCBot":          "commoncrawl.org",
    "Applebot":       "apple.com",
    "Bytespider":     "bytedance.com",
}

# Apache Combined Log Pattern
LOG_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<bytes>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)


def parse_log(path: str) -> list[dict]:
    entries = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_RE.match(line.strip())
            if m:
                entries.append(m.groupdict())
    return entries


def detect_bot(ua: str) -> str | None:
    """Gibt Bot-Namen zurück wenn UA auf einen bekannten KI-Bot passt."""
    ua_lower = ua.lower()
    for bot_name in AI_BOT_SIGNATURES:
        if bot_name.lower() in ua_lower:
            return bot_name
    return None


def rdns_verify(ip: str, expected_domain: str) -> str:
    """
    Forward-confirmed reverse DNS:
    IP → rDNS-Hostname → forward-DNS → muss wieder zur IP führen
    UND Hostname muss expected_domain enthalten.
    """
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if expected_domain not in hostname:
            return f"FAIL (hostname={hostname}, expected *{expected_domain})"
        # Forward-DNS check
        resolved_ip = socket.gethostbyname(hostname)
        if resolved_ip == ip:
            return f"OK ({hostname})"
        else:
            return f"FAIL (forward={resolved_ip} ≠ {ip})"
    except socket.herror:
        return "rDNS: keine Antwort"
    except Exception as e:
        return f"ERR ({e})"


def analyze(log_path: str, output_dir: str = "/output"):
    print(f"\nAnalysiere: {log_path}")
    entries = parse_log(log_path)
    print(f"  {len(entries)} Log-Einträge gelesen\n")

    # ── Aggregation ──────────────────────────────────────────────────────────
    bot_hits   = defaultdict(lambda: {"ips": set(), "paths": [], "status": defaultdict(int)})
    humans     = 0
    unknown    = 0
    private_violations = []

    for e in entries:
        bot = detect_bot(e["ua"])
        if bot:
            bot_hits[bot]["ips"].add(e["ip"])
            bot_hits[bot]["paths"].append(e["path"])
            bot_hits[bot]["status"][e["status"]] += 1
            # Compliance-Verletzung?
            if e["path"].startswith("/private"):
                private_violations.append({
                    "bot": bot, "ip": e["ip"],
                    "path": e["path"], "status": e["status"], "ua": e["ua"]
                })
        elif any(b in e["ua"] for b in ["bot", "Bot", "crawler", "spider"]):
            unknown += 1
        else:
            humans += 1

    # ── Tabelle 1: Bot-Übersicht ──────────────────────────────────────────────
    rows = []
    for bot_name, data in sorted(bot_hits.items()):
        total_hits = len(data["paths"])
        robots_hits = data["paths"].count("/robots.txt")
        private_hits = sum(1 for p in data["paths"] if p.startswith("/private"))
        expected_domain = AI_BOT_SIGNATURES.get(bot_name, "?")
        ip_list = list(data["ips"])[:2]  # max 2 IPs anzeigen

        # rDNS nur für erste IP (simuliert — in echtem Betrieb alle prüfen)
        if ip_list and expected_domain != "?":
            rdns = rdns_verify(ip_list[0], expected_domain)
        else:
            rdns = "–"

        status_str = " ".join(f"{s}×{n}" for s, n in data["status"].items())
        rows.append([
            bot_name,
            total_hits,
            robots_hits,
            private_hits,
            ", ".join(ip_list) or "–",
            rdns,
            status_str,
        ])

    print("=" * 70)
    print("  KI-BOT ÜBERSICHT")
    print("=" * 70)
    headers = ["Bot", "Hits", "/robots.txt", "/private/ Hits", "IPs", "rDNS", "Status-Codes"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

    # ── Tabelle 2: robots.txt Compliance ─────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ROBOTS.TXT COMPLIANCE-VERLETZUNGEN (/private/-Zugriffe)")
    print("=" * 70)
    if private_violations:
        vrows = [[v["bot"], v["ip"], v["path"], v["status"]] for v in private_violations]
        print(tabulate(vrows, headers=["Bot", "IP", "Pfad", "Status"], tablefmt="rounded_outline"))
    else:
        print("  Keine Verletzungen gefunden — alle Bots respektierten robots.txt.")

    # ── Tabelle 3: Traffic-Mix ────────────────────────────────────────────────
    total_bot_hits = sum(len(d["paths"]) for d in bot_hits.values())
    print("\n" + "=" * 70)
    print("  TRAFFIC-MIX")
    print("=" * 70)
    mix = [
        ["Echte Nutzer (geschätzt)", humans],
        ["Bekannte KI-Bots", total_bot_hits],
        ["Sonstige Bots/Crawler", unknown],
        ["Gesamt", len(entries)],
    ]
    print(tabulate(mix, headers=["Kategorie", "Requests"], tablefmt="rounded_outline"))

    # ── Report in Datei schreiben ─────────────────────────────────────────────
    import os
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "report.txt")
    with open(report_path, "w") as f:
        f.write(f"Bot-Lab Analyse  —  {datetime.now().isoformat()}\n")
        f.write(f"Log: {log_path}  |  Einträge: {len(entries)}\n\n")
        f.write(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
        f.write("\n\nCompliance-Verletzungen:\n")
        if private_violations:
            f.write(tabulate(vrows, headers=["Bot", "IP", "Pfad", "Status"], tablefmt="rounded_outline"))
        else:
            f.write("  Keine.\n")

    print(f"\nReport gespeichert: {report_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot-Lab Apache Log Analyzer")
    parser.add_argument("--log", default="/logs/access.log", help="Pfad zum access.log")
    parser.add_argument("--output", default="/output", help="Ausgabe-Verzeichnis")
    args = parser.parse_args()
    analyze(args.log, args.output)

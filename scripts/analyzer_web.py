"""
Bot-Lab Analyzer — Web-Interface (Flask)
Aufrufbar unter http://localhost:18082
"""

import re
import socket
import os
from collections import defaultdict
from datetime import datetime
from flask import Flask, render_template_string, request

app = Flask(__name__)

LOG_PATH = os.getenv("LOG_FILE", "/logs/access.log")

# ─── KI-Bot Signaturen ───────────────────────────────────────────────────────
AI_BOT_SIGNATURES = {
    "GPTBot":          "openai.com",
    "ChatGPT-User":    "openai.com",
    "ClaudeBot":       "anthropic.com",
    "anthropic-ai":    "anthropic.com",
    "PerplexityBot":   "perplexity.ai",
    "Google-Extended": "google.com",
    "Amazonbot":       "amazon.com",
    "CCBot":           "commoncrawl.org",
    "Applebot":        "apple.com",
    "Bytespider":      "bytedance.com",
}

LOG_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<bytes>\S+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bot-Lab Analyzer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f1117; color: #e0e0e0; padding: 2rem; }
    h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 0.3rem; color: #fff; }
    .subtitle { color: #888; font-size: 0.85rem; margin-bottom: 2rem; }
    .controls { display: flex; gap: 1rem; align-items: center; margin-bottom: 2rem; flex-wrap: wrap; }
    .controls input { background: #1e2130; border: 1px solid #333; color: #e0e0e0;
                      padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9rem; width: 380px; }
    .controls button { background: #4f6ef7; color: #fff; border: none; padding: 0.5rem 1.5rem;
                       border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
    .controls button:hover { background: #3a56d4; }
    .rdns-toggle { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #aaa; }
    .rdns-toggle input { width: auto; }

    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
    .stat-card { background: #1e2130; border: 1px solid #2a2d3e; border-radius: 8px; padding: 1rem 1.2rem; }
    .stat-card .label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: .05em; }
    .stat-card .value { font-size: 1.8rem; font-weight: 700; margin-top: 0.2rem; }
    .stat-card.blue .value  { color: #4f9ef7; }
    .stat-card.green .value { color: #4fc97a; }
    .stat-card.red .value   { color: #f7604f; }
    .stat-card.amber .value { color: #f7b24f; }

    h2 { font-size: 1rem; font-weight: 600; margin-bottom: 0.8rem; color: #ccc; }
    .section { margin-bottom: 2rem; }

    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    thead th { background: #1e2130; color: #aaa; font-weight: 500; text-align: left;
               padding: 0.6rem 0.8rem; border-bottom: 1px solid #2a2d3e; }
    tbody tr { border-bottom: 1px solid #1a1d2a; }
    tbody tr:hover { background: #1e2130; }
    tbody td { padding: 0.55rem 0.8rem; }

    .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
             font-size: 0.75rem; font-weight: 600; }
    .badge-blue   { background: #1a2a4a; color: #4f9ef7; }
    .badge-green  { background: #1a3a2a; color: #4fc97a; }
    .badge-red    { background: #3a1a1a; color: #f7604f; }
    .badge-amber  { background: #3a2a1a; color: #f7b24f; }
    .badge-gray   { background: #2a2a2a; color: #aaa; }

    .rdns-ok   { color: #4fc97a; }
    .rdns-fail { color: #f7604f; }
    .rdns-skip { color: #666; font-style: italic; }

    .violation-row { background: #2a1a1a !important; }
    .empty { color: #555; font-style: italic; padding: 1rem; }
    .meta { color: #555; font-size: 0.78rem; margin-top: 2rem; }

    .tab-bar { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .tab { padding: 0.4rem 1rem; border-radius: 6px; font-size: 0.85rem; cursor: pointer;
           border: 1px solid #2a2d3e; background: #1e2130; color: #aaa; }
    .tab.active { background: #4f6ef7; color: #fff; border-color: #4f6ef7; }
  </style>
</head>
<body>
  <h1>Bot-Lab Analyzer</h1>
  <p class="subtitle">KI-Bot Erkennung · rDNS-Verifikation · robots.txt Compliance</p>

  <form method="POST" class="controls">
    <input name="log_path" value="{{ log_path }}" placeholder="/logs/access.log">
    <label class="rdns-toggle">
      <input type="checkbox" name="do_rdns" {% if do_rdns %}checked{% endif %}>
      rDNS-Verifikation (langsamer)
    </label>
    <button type="submit">Analysieren</button>
  </form>

  {% if result %}
  {% set r = result %}

  <!-- Stats-Karten -->
  <div class="stats-grid">
    <div class="stat-card blue">
      <div class="label">Gesamt-Requests</div>
      <div class="value">{{ r.total }}</div>
    </div>
    <div class="stat-card green">
      <div class="label">Echte Nutzer</div>
      <div class="value">{{ r.humans }}</div>
    </div>
    <div class="stat-card amber">
      <div class="label">KI-Bot Requests</div>
      <div class="value">{{ r.total_bot_hits }}</div>
    </div>
    <div class="stat-card red">
      <div class="label">Compliance-Verstöße</div>
      <div class="value">{{ r.violations|length }}</div>
    </div>
  </div>

  <!-- Bot-Übersicht -->
  <div class="section">
    <h2>KI-Bot Übersicht</h2>
    <table>
      <thead>
        <tr>
          <th>Bot</th>
          <th>Hits</th>
          <th>robots.txt</th>
          <th>/private/</th>
          <th>Status-Codes</th>
          <th>IP(s)</th>
          <th>rDNS</th>
        </tr>
      </thead>
      <tbody>
        {% for row in r.bot_rows %}
        <tr>
          <td><span class="badge badge-blue">{{ row.name }}</span></td>
          <td>{{ row.hits }}</td>
          <td>{{ row.robots_hits }}</td>
          <td>
            {% if row.private_hits > 0 %}
              <span class="badge badge-red">{{ row.private_hits }} ⚠</span>
            {% else %}
              <span class="badge badge-green">0 ✓</span>
            {% endif %}
          </td>
          <td>
            {% for code, count in row.status.items() %}
              <span class="badge {% if code == '200' %}badge-green{% elif code == '403' %}badge-red{% else %}badge-gray{% endif %}">
                {{ code }}×{{ count }}
              </span>
            {% endfor %}
          </td>
          <td><code style="font-size:0.8rem;color:#888">{{ row.ips }}</code></td>
          <td>
            {% if row.rdns.startswith('OK') %}
              <span class="rdns-ok">✓ {{ row.rdns }}</span>
            {% elif row.rdns.startswith('FAIL') %}
              <span class="rdns-fail">✗ {{ row.rdns }}</span>
            {% else %}
              <span class="rdns-skip">{{ row.rdns }}</span>
            {% endif %}
          </td>
        </tr>
        {% else %}
        <tr><td colspan="7" class="empty">Keine KI-Bots im Log gefunden.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Compliance -->
  <div class="section">
    <h2>robots.txt Compliance-Verletzungen</h2>
    {% if r.violations %}
    <table>
      <thead><tr><th>Bot</th><th>IP</th><th>Pfad</th><th>Status</th><th>Zeitpunkt</th></tr></thead>
      <tbody>
        {% for v in r.violations %}
        <tr class="violation-row">
          <td><span class="badge badge-red">{{ v.bot }}</span></td>
          <td><code style="font-size:0.8rem">{{ v.ip }}</code></td>
          <td>{{ v.path }}</td>
          <td><span class="badge badge-red">{{ v.status }}</span></td>
          <td style="color:#666;font-size:0.8rem">{{ v.time }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p class="empty">Keine Verstöße — alle Bots respektieren robots.txt.</p>
    {% endif %}
  </div>

  <!-- Traffic-Mix -->
  <div class="section">
    <h2>Traffic-Mix</h2>
    <table>
      <thead><tr><th>Kategorie</th><th>Requests</th><th>Anteil</th></tr></thead>
      <tbody>
        {% for row in r.mix %}
        <tr>
          <td>{{ row.label }}</td>
          <td>{{ row.count }}</td>
          <td>
            <div style="display:flex;align-items:center;gap:0.5rem">
              <div style="background:{{ row.color }};width:{{ row.pct * 2 }}px;height:6px;border-radius:3px"></div>
              {{ "%.1f"|format(row.pct) }}%
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <p class="meta">Analysiert: {{ log_path }} · {{ r.total }} Einträge · {{ r.timestamp }}</p>
  {% endif %}
</body>
</html>
"""

def parse_log(path):
    entries = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = LOG_RE.match(line.strip())
                if m:
                    entries.append(m.groupdict())
    except FileNotFoundError:
        pass
    return entries

def detect_bot(ua):
    ua_lower = ua.lower()
    for bot_name in AI_BOT_SIGNATURES:
        if bot_name.lower() in ua_lower:
            return bot_name
    return None

def rdns_verify(ip, expected_domain):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if expected_domain not in hostname:
            return f"FAIL (host={hostname})"
        resolved = socket.gethostbyname(hostname)
        return f"OK ({hostname})" if resolved == ip else f"FAIL (forward={resolved}≠{ip})"
    except Exception as e:
        return f"– ({e})"

def run_analysis(log_path, do_rdns=False):
    entries = parse_log(log_path)
    if not entries:
        return None

    bot_hits = defaultdict(lambda: {"ips": set(), "paths": [], "status": defaultdict(int), "times": []})
    humans = unknown = 0
    violations = []

    for e in entries:
        bot = detect_bot(e["ua"])
        if bot:
            bot_hits[bot]["ips"].add(e["ip"])
            bot_hits[bot]["paths"].append(e["path"])
            bot_hits[bot]["status"][e["status"]] += 1
            bot_hits[bot]["times"].append(e["time"])
            if e["path"].startswith("/private"):
                violations.append({**e, "bot": bot})
        elif any(b in e["ua"] for b in ["bot", "Bot", "crawler", "spider"]):
            unknown += 1
        else:
            humans += 1

    bot_rows = []
    for name, data in sorted(bot_hits.items()):
        ip_list = list(data["ips"])[:2]
        rdns = "rDNS deaktiviert"
        if do_rdns and ip_list:
            domain = AI_BOT_SIGNATURES.get(name, "?")
            rdns = rdns_verify(ip_list[0], domain) if domain != "?" else "–"
        bot_rows.append({
            "name": name,
            "hits": len(data["paths"]),
            "robots_hits": data["paths"].count("/robots.txt"),
            "private_hits": sum(1 for p in data["paths"] if p.startswith("/private")),
            "status": dict(data["status"]),
            "ips": ", ".join(ip_list) or "–",
            "rdns": rdns,
        })

    total = len(entries)
    total_bot_hits = sum(r["hits"] for r in bot_rows)

    mix_data = [
        ("Echte Nutzer",     humans,         "#4fc97a"),
        ("KI-Bots",          total_bot_hits, "#f7b24f"),
        ("Sonstige Crawler", unknown,        "#888"),
    ]
    mix = [{"label": l, "count": c, "color": col,
            "pct": (c / total * 100) if total else 0}
           for l, c, col in mix_data]

    return {
        "total": total,
        "humans": humans,
        "total_bot_hits": total_bot_hits,
        "bot_rows": bot_rows,
        "violations": violations,
        "mix": mix,
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    }

@app.route("/", methods=["GET", "POST"])
def index():
    log_path = LOG_PATH
    do_rdns = False
    result = None

    if request.method == "POST":
        log_path = request.form.get("log_path", LOG_PATH)
        do_rdns  = "do_rdns" in request.form
        result   = run_analysis(log_path, do_rdns)

    return render_template_string(HTML,
        result=result,
        log_path=log_path,
        do_rdns=do_rdns,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

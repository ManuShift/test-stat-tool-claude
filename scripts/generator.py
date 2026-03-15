"""
Bot-Lab Log Generator
Simuliert realistische Apache-Zugriffe von echten Nutzern UND KI-Bots.
Schickt echte HTTP-Requests an Apache → landet direkt im access.log.
"""

import os
import time
import random
import requests
from datetime import datetime

TARGET = f"http://{os.getenv('TARGET_HOST', 'apache')}:{os.getenv('TARGET_PORT', '80')}"

# ─── Bekannte KI-Bot User-Agents (Stand 2025) ────────────────────────────────
AI_BOTS = [
    {
        "name": "GPTBot",
        "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.0; +https://openai.com/gptbot",
        "crawl_delay": 1.0,
        "respects_robots": True,
    },
    {
        "name": "ChatGPT-User",
        "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot",
        "crawl_delay": 0.5,
        "respects_robots": True,
    },
    {
        "name": "ClaudeBot",
        "ua": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-web",
        "crawl_delay": 1.5,
        "respects_robots": True,
    },
    {
        "name": "anthropic-ai",
        "ua": "anthropic-ai/1.0 (+https://www.anthropic.com)",
        "crawl_delay": 2.0,
        "respects_robots": True,
    },
    {
        "name": "PerplexityBot",
        "ua": "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
        "crawl_delay": 0.8,
        "respects_robots": True,
    },
    {
        "name": "Google-Extended",
        "ua": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html) Google-Extended",
        "crawl_delay": 0.5,
        "respects_robots": True,
    },
    {
        "name": "Amazonbot",
        "ua": "Mozilla/5.0 (compatible; Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot)",
        "crawl_delay": 1.2,
        "respects_robots": True,
    },
    {
        "name": "CCBot",
        "ua": "CCBot/2.0 (https://commoncrawl.org/faq/)",
        "crawl_delay": 3.0,
        "respects_robots": False,  # Testet Compliance-Verletzung
    },
    {
        "name": "Fake-Browser-Bot",  # Verschleierter Bot — kein erkennbarer UA
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "crawl_delay": 0.1,
        "respects_robots": False,
        "stealth": True,
    },
]

# ─── Echte Browser User-Agents ────────────────────────────────────────────────
REAL_USERS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
]

# ─── Seiten die gecrawlt werden ───────────────────────────────────────────────
PUBLIC_PAGES  = ["/", "/index.html", "/about.html", "/blog.html", "/article.html",
                 "/robots.txt", "/sitemap.xml"]
PRIVATE_PAGES = ["/private/", "/private/index.html"]
ALL_PAGES     = PUBLIC_PAGES + PRIVATE_PAGES


def fetch(url, ua, label=""):
    """Einzelner HTTP-Request mit gegebenem User-Agent."""
    try:
        r = requests.get(url, headers={"User-Agent": ua}, timeout=5, allow_redirects=True)
        status = r.status_code
    except Exception as e:
        status = "ERR"
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {label:20s} {status}  {url}")


def simulate_real_user():
    ua = random.choice(REAL_USERS)
    pages = random.sample(PUBLIC_PAGES, k=random.randint(1, 4))
    for page in pages:
        fetch(TARGET + page, ua, "real-user")
        time.sleep(random.uniform(0.5, 3.0))


def simulate_bot(bot: dict):
    name  = bot["name"]
    ua    = bot["ua"]
    delay = bot.get("crawl_delay", 1.0)

    print(f"\n>>> Simulating {name} <<<")

    # 1. Alle Bots rufen zuerst robots.txt ab (Standard-Verhalten)
    fetch(TARGET + "/robots.txt", ua, name)
    time.sleep(delay)

    # 2. Öffentliche Seiten crawlen
    for page in PUBLIC_PAGES:
        if page == "/robots.txt":
            continue
        fetch(TARGET + page, ua, name)
        time.sleep(delay)

    # 3. Privaten Bereich — abhängig von robots.txt-Compliance
    if not bot.get("respects_robots", True):
        print(f"  [{name}] Ignoriert robots.txt — crawlt /private/")
        for page in PRIVATE_PAGES:
            fetch(TARGET + page, ua, name)
            time.sleep(delay * 0.5)
    else:
        print(f"  [{name}] Respektiert robots.txt — überspringt /private/")


# ─── Hauptschleife ────────────────────────────────────────────────────────────
def main():
    print(f"Bot-Lab Generator gestartet → {TARGET}")
    print("Warte 5s auf Apache-Start...")
    time.sleep(5)

    round_num = 0
    while True:
        round_num += 1
        print(f"\n{'='*50}")
        print(f"  Runde {round_num}  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")

        # Echte Nutzer (häufiger als Bots)
        for _ in range(random.randint(3, 8)):
            simulate_real_user()
            time.sleep(random.uniform(0.2, 1.5))

        # Zufällig 2–4 verschiedene Bots pro Runde
        bots_this_round = random.sample(AI_BOTS, k=random.randint(2, 4))
        for bot in bots_this_round:
            simulate_bot(bot)
            time.sleep(random.uniform(2, 5))

        # Pause zwischen Runden (60–120 Sekunden)
        pause = random.randint(10, 20)
        print(f"\nPause {pause}s bis zur nächsten Runde...")
        time.sleep(pause)


if __name__ == "__main__":
    main()

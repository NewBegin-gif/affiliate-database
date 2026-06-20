#!/usr/bin/env python3
"""diag_cluster_pages.py — READ-ONLY. Dump de on-page SEO van de Proton- en
Bitvavo-pagina's die net pagina 2 staan, zodat we gericht kunnen optimaliseren.

Per doelpagina: <title>, meta description, canonical, hreflang-count, h1, alle
h2's, ruwe woordtelling, en hoeveel ANDERE pagina's er intern naar linken
(inlink-count = autoriteitssignaal).

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/diagc.py
"""
import re
from pathlib import Path

REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
TARGETS = [
    "proton-pricing-en", "proton-pricing-id",
    "bitvavo-scale-up", "bitvavo-trading-bot", "bitvavo-pricing-en",
]

# inlink-index: tel per target hoeveel index.html ernaar linken
all_pages = list(REPO.rglob("index.html"))
print(f"repo: {REPO}  ({len(all_pages)} pagina's totaal)\n")

def inlinks(slug):
    needle = f"/b2b/{slug}/"
    c = 0
    for f in all_pages:
        try:
            if needle in f.read_text(encoding="utf-8", errors="ignore"):
                c += 1
        except Exception:
            pass
    return c

for slug in TARGETS:
    f = B2B / slug / "index.html"
    print("=" * 72)
    print(slug, "" if f.exists() else "  ✗ BESTAAT NIET")
    print("=" * 72)
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    title = (re.search(r"<title>(.*?)</title>", t, re.S | re.I) or [None, ""])[1].strip()
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', t, re.I)
    desc = desc.group(1).strip() if desc else "(geen)"
    canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](.*?)["\']', t, re.I)
    canon = canon.group(1) if canon else "(geen)"
    hreflang = len(re.findall(r'hreflang=', t, re.I))
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S | re.I)
    h1 = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else "(geen)"
    h2s = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<h2[^>]*>(.*?)</h2>", t, re.S | re.I)]
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", t)))
    faq = "FAQPage" in t or "faq" in t.lower()
    print(f"  TITLE  : {title}")
    print(f"  DESC   : {desc[:160]}")
    print(f"  CANON  : {canon}")
    print(f"  hreflang-tags: {hreflang} | FAQ-schema/sectie: {'ja' if faq else 'nee'} | ~woorden: {words}")
    print(f"  H1     : {h1}")
    print(f"  H2's ({len(h2s)}): " + " | ".join(h2s[:12]))
    print(f"  INLINKS van andere pagina's: {inlinks(slug)}")
    print()

print("KLAAR — plak alles terug.")

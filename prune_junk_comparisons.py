#!/usr/bin/env python3
"""prune_junk_comparisons.py — verwijder ONZINNIGE cross-categorie "X-vs-Y"
b2b-vergelijkingen (Victor-overgeneratie), bv. crypto-exchange vs caching-plugin,
AI-video vs crypto. Conservatief: alleen vs-pagina's waar de twee kanten in
INCOMPATIBELE gespecialiseerde domeinen zitten. Same-domain (bitvavo-vs-binance,
synthesia-vs-murf) en algemene B2B-vergelijkingen blijven staan.

DRY-RUN (default): toont/telt alles + schrijft volledige lijst naar
/tmp/junk_prune_list.txt. Verwijdert niets.
--apply: git rm de junk-folders, verwijder hun <url> uit sitemap.xml, strip
interne links (<li>/<a> naar die slugs) uit overige b2b-pagina's, push main+staging.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pjc.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pjc.py --apply
"""
import sys, re, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
SITEMAP = REPO / "sitemap.xml"

# Gespecialiseerde domeinen — merken die alléén binnen hun eigen domein
# zinvol te vergelijken zijn. (substring-match op de slug-helft)
DOMAINS = {
 "CRYPTO":  ["bitvavo","bybit","binance","kraken","coinbase","kucoin","mexc","okx",
             "bitget","htx","gateio","bitfinex","bitstamp","gemini-exchange"],
 "WPCACHE": ["wprocket","wp-rocket","wp rocket"],
 "MEDIA":   ["synthesia","murf","invideo","heygen","descript","elevenlabs","pictory"],
 "DEV":     ["replit"],
}
SPECIALIZED = set(DOMAINS)

# Taal-suffixen die achter een merk kunnen hangen (om af te knippen).
LANGS = {"en","fr","de","ge","es","sp","pt","po","nl","du","it","id","mx","sv","tr",
         "vi","ar","no","ja","th","zu","pl","ro","hi","ko","zh","cs","fi","el","hu",
         "sw","ha","yo","am","af","da","ru"}


def classify(half):
    h = half.lower()
    for dom, kws in DOMAINS.items():
        if any(k in h for k in kws):
            return dom
    return "GENERAL"


def split_vs(slug):
    """Geef (left, right) terug rond '-vs-' / ' vs ', anders None."""
    s = slug.lower().replace(".html", "")
    for sep in ("-vs-", " vs ", "-vs ", " vs-"):
        if sep in s:
            l, r = s.split(sep, 1)
            # knip taal-suffix van rechterkant
            parts = r.split("-")
            if len(parts) > 1 and parts[-1] in LANGS:
                r = "-".join(parts[:-1])
            return l, r
    return None


def is_junk(slug):
    sv = split_vs(slug)
    if not sv:
        return None
    l, r = sv
    dl, dr = classify(l), classify(r)
    if dl == dr:
        return None  # zelfde domein → zinvol → behouden
    # incompatibel als minstens één kant gespecialiseerd is en de domeinen verschillen
    if dl in SPECIALIZED or dr in SPECIALIZED:
        return (l, dl, r, dr)
    return None  # GENERAL × GENERAL → echte B2B-vergelijking → behouden


# ── Detectie ──
pages = sorted(p for p in B2B.iterdir() if p.is_dir())
junk = []
for p in pages:
    res = is_junk(p.name)
    if res:
        junk.append((p.name, res))

junk_slugs = {name for name, _ in junk}
print("=" * 64)
print(f"JUNK-DETECTIE  ({'APPLY' if APPLY else 'DRY-RUN'})")
print("=" * 64)
print(f"  totaal b2b-folders : {len(pages)}")
print(f"  junk-vergelijkingen: {len(junk)}")
from collections import Counter
pairc = Counter(tuple(sorted((d1, d2))) for _, (_, d1, _, d2) in junk)
print("  per domein-paar:")
for pair, c in pairc.most_common():
    print(f"    {pair[0]} × {pair[1]}: {c}")

# volledige lijst naar bestand + sample
Path("/tmp/junk_prune_list.txt").write_text("\n".join(sorted(junk_slugs)), encoding="utf-8")
print("\n  volledige lijst → /tmp/junk_prune_list.txt")
print("  --- steekproef (eerste 50) ---")
for name, (l, dl, r, dr) in sorted(junk)[:50]:
    print(f"    {name}   [{dl}×{dr}]")

# interne links + sitemap impact
if junk_slugs:
    alt = "|".join(re.escape(s) for s in junk_slugs)
    href_re = re.compile(r'href="/b2b/(?:%s)/"' % alt)
    aff_files = 0
    for p in pages:
        if p.name in junk_slugs:
            continue
        f = p / "index.html"
        if f.exists() and href_re.search(f.read_text(encoding="utf-8", errors="ignore")):
            aff_files += 1
    print(f"\n  interne-link verwijzingen op te schonen in ~{aff_files} overige pagina's")
    sm = SITEMAP.read_text(encoding="utf-8", errors="ignore") if SITEMAP.exists() else ""
    sm_hits = sum(1 for s in junk_slugs if f"/b2b/{s}/" in sm)
    print(f"  sitemap-entries te verwijderen: {sm_hits}")

if not APPLY:
    print("\nDRY-RUN — niets verwijderd. Bekijk /tmp/junk_prune_list.txt, dan --apply.")
    sys.exit(0)

if not junk_slugs:
    print("Geen junk — niets te doen."); sys.exit(0)

# ── APPLY ──
# 1) verwijder folders
for s in junk_slugs:
    d = B2B / s
    if d.exists():
        subprocess.run(["git", "-C", str(REPO), "rm", "-rq", f"b2b/{s}"], check=False)

# 2) strip interne links uit overige pagina's
alt = "|".join(re.escape(s) for s in junk_slugs)
li_re = re.compile(r'<li[^>]*>(?:(?!</li>).)*?href="/b2b/(?:%s)/"(?:(?!</li>).)*?</li>' % alt, re.S)
a_re = re.compile(r'<a [^>]*href="/b2b/(?:%s)/"[^>]*>.*?</a>' % alt, re.S)
cleaned = 0
for p in pages:
    if p.name in junk_slugs:
        continue
    f = p / "index.html"
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "/b2b/" not in t:
        continue
    nt = a_re.sub("", li_re.sub("", t))
    if nt != t:
        f.write_text(nt, encoding="utf-8"); cleaned += 1
print(f"interne links opgeschoond in {cleaned} pagina's")

# 3) sitemap opschonen
if SITEMAP.exists():
    sm = SITEMAP.read_text(encoding="utf-8", errors="ignore")
    url_re = re.compile(r'<url>(?:(?!</url>).)*?<loc>[^<]*?/b2b/(?:%s)/[^<]*?</loc>(?:(?!</url>).)*?</url>\s*' % alt, re.S)
    nsm, n = url_re.subn("", sm)
    if n:
        SITEMAP.write_text(nsm, encoding="utf-8"); print(f"sitemap: {n} entries verwijderd")

# 4) commit + push
def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "-A", "--", "b2b", "sitemap.xml")
git("commit", "-m", f"Junk-prune: verwijder {len(junk_slugs)} onzinnige cross-categorie vs-pagina's + interne links + sitemap")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-160:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-160:])
print("KLAAR — plak alles terug.")

#!/usr/bin/env python3
"""diag_junk_titles.py — READ-ONLY. Spoor de bron op van de kapotte
'... on pro platform - nb / - brand / - bra'-titels die in GSC opduiken.

Doet niets dan kijken:
  A) toont template-regels in generate_article.py die de junk produceren
     (zoektermen: 'evaluate', 'on pro', ' - nb', ' - brand', suffix-listjes,
      title-opbouw met afgekapte tokens);
  B) scant de echte b2b-pagina's op schijf en lijst <title>/<h1> die de
     verdachte patronen bevatten, met pad — zodat we precies weten welke
     pagina's herschreven/genoindexed moeten worden.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/diag.py
"""
import re
from pathlib import Path

AG = "/root/felix_hq/generate_article.py"
B2B = Path("/root/felix_hq")  # repo-root waar /b2b/ onder staat; pas aan indien anders

# ---- A) template-bron in generate_article.py ----
print("=" * 72)
print("A) Verdachte template-regels in generate_article.py")
print("=" * 72)
src = open(AG, encoding="utf-8").read().split("\n")
pat = re.compile(r"evaluate|on pro|on convert|on custody| - nb| - br\b| - brand|is it |\bsuffix\b|brand_suffix|TITLE_|title_tpl|f['\"].*\{.*brand", re.I)
ctx = set()
for i, l in enumerate(src):
    if pat.search(l):
        for j in range(max(0, i - 1), min(len(src), i + 2)):
            ctx.add(j)
for j in sorted(ctx):
    print(f"  L{j+1}: {src[j].strip()[:150]}")
if not ctx:
    print("  (geen directe template-match — junk komt mogelijk uit TOPICS-strings; zie B)")

# ---- B) echte pagina's op schijf met junk in title/h1 ----
print("\n" + "=" * 72)
print("B) Gegenereerde b2b-pagina's met verdachte title/h1")
print("=" * 72)
# vind de /b2b/-map
cands = list(Path("/root").glob("**/b2b")) + list(Path("/var/www").glob("**/b2b"))
b2b_dir = next((p for p in cands if p.is_dir()), None)
print(f"  b2b-map: {b2b_dir or 'NIET GEVONDEN — geef pad door'}")
junk_re = re.compile(r"evaluate the cryptocurrency| on pro | - nb\b| - br\b| - brand\b|is it evaluate", re.I)
found = 0
if b2b_dir:
    for f in sorted(b2b_dir.rglob("index.html")):
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        tm = re.search(r"<title>(.*?)</title>", t, re.S | re.I)
        hm = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S | re.I)
        title = (tm.group(1).strip() if tm else "")
        h1 = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else ""
        if junk_re.search(title) or junk_re.search(h1):
            found += 1
            noidx = "noindex" in t.lower()
            print(f"  {'[noindex]' if noidx else '[INDEXED]'} {f.parent.name}")
            print(f"      title: {title[:120]}")
print(f"\n  totaal verdachte pagina's: {found}")
print("\nKLAAR — plak alles terug.")

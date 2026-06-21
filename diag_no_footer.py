#!/usr/bin/env python3
"""diag_no_footer.py — READ-ONLY. Vind de b2b-pagina's zonder <footer EN </body>
(de 55 die de nieuwsbrief-backfill oversloeg) en laat zien WAT ze dan wel zijn:
grootte, of het geldige HTML is, eerste/laatste stukje, en welke kerntags er
ontbreken. Zo weten we of het kapotte/afgekapte pagina's zijn of een ander template.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/dnf.py
"""
import re
from pathlib import Path
from collections import Counter

B2B = Path("/root/felix_hq/repos/aibuildermarketplace/b2b")
hits = []
for f in sorted(B2B.glob("*/index.html")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "<footer" not in t and "</body>" not in t:
        hits.append((f.parent.name, t))

print(f"pagina's zonder <footer én </body>: {len(hits)}\n")

# patronen samenvatten
sizes = Counter()
has_html = has_head = has_h1 = has_article = empty = 0
for name, t in hits:
    n = len(t)
    bucket = "leeg/<100" if n < 100 else ("<1KB" if n < 1024 else ("1-5KB" if n < 5120 else ">5KB"))
    sizes[bucket] += 1
    if n < 100: empty += 1
    if "<html" in t.lower(): has_html += 1
    if "<head" in t.lower(): has_head += 1
    if "<h1" in t.lower(): has_h1 += 1
    if "<article" in t.lower() or "article-body" in t.lower(): has_article += 1

print("grootteverdeling:", dict(sizes))
print(f"bevat <html>:{has_html}  <head>:{has_head}  <h1>:{has_h1}  <article>:{has_article}  (van {len(hits)})")
print(f"vrijwel leeg (<100 bytes): {empty}\n")

print("=== eerste 8 voorbeelden (naam, grootte, begin + eind) ===")
for name, t in hits[:8]:
    head = re.sub(r"\s+", " ", t[:160]).strip()
    tail = re.sub(r"\s+", " ", t[-160:]).strip()
    print(f"\n• {name}  ({len(t)} bytes)")
    print(f"   begin: {head}")
    print(f"   eind : {tail}")

print(f"\n=== alle {len(hits)} namen ===")
for name, _ in hits:
    print("  " + name)
print("\nKLAAR — plak alles terug.")

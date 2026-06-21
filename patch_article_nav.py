#!/usr/bin/env python3
"""patch_article_nav.py — voeg Tool Finder + Deals toe aan de topnav van ALLE
b2b-artikelen (intern-linksignaal naar de hubs + conversie-volgendestap).

Deel A: backfill bestaande b2b/*/index.html (topnav-links uitbreiden).
Deel B: template in generate_article.py (zodat nieuwe artikelen het ook krijgen).

Veilig: dry-run by default (telt); --apply schrijft + commit + push (main+staging).
Idempotent (skip als /finder/ al in de topnav). Per-file simpele string-replace.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pan.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pan.py --apply    # schrijven + pushen
"""
import sys, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
GA = "/root/felix_hq/generate_article.py"

OLD = '<div class="topnav-links"><a href="/b2b/">All Reviews</a><a href="/">Home</a></div>'
NEW = ('<div class="topnav-links"><a href="/b2b/">All Reviews</a>'
       '<a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a>'
       '<a href="/">Home</a></div>')

# ---- Deel A: backfill artikelen ----
pages = sorted(B2B.glob("*/index.html"))
changed = already = nomatch = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if NEW in t or '/finder/">Tool Finder' in t:
        already += 1; continue
    if OLD not in t:
        nomatch += 1; continue
    if APPLY:
        f.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    changed += 1

print(f"b2b-artikelen        : {len(pages)}")
print(f"  topnav uitgebreid  : {changed}")
print(f"  al gedaan          : {already}")
print(f"  geen topnav-match  : {nomatch}")

# ---- Deel B: template ----
gsrc = open(GA, encoding="utf-8").read()
tmpl_status = "n.v.t."
if OLD in gsrc:
    tmpl_status = "wordt gepatcht" if APPLY else "matcht (apply patcht 'm)"
elif NEW in gsrc or '/finder/">Tool Finder' in gsrc:
    tmpl_status = "al gepatcht"
else:
    tmpl_status = "anchor NIET gevonden — meld dit"
print(f"  template (generate_article.py): {tmpl_status}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

# template schrijven
if OLD in gsrc:
    import shutil, datetime, py_compile
    bak = GA + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(GA, bak)
    open(GA, "w", encoding="utf-8").write(gsrc.replace(OLD, NEW, 1))
    try:
        py_compile.compile(GA, doraise=True)
        print(f"✓ template gepatcht (backup {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, GA); print(f"✗ template syntaxfout — teruggezet: {e}")

if not changed:
    print("\nGeen artikel-wijzigingen om te pushen."); sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "b2b")
git("commit", "-m", f"Topnav: Tool Finder + Deals op {changed} b2b-artikelen (intern-linksignaal naar hubs)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

#!/usr/bin/env python3
"""patch_article_build_nav.py — voeg een "Build"-link toe aan de topnav van alle
b2b-artikelen (na de Deals-link), zodat elke reviewpagina ook naar de /build/-
blueprints linkt. De Deals-link is overal identiek, dus één replace dekt alle
nav-varianten.

Deel A: backfill bestaande b2b/*/index.html. Deel B: template generate_article.py.
Dry-run by default; --apply schrijft + commit + push (main+staging). Idempotent.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pbn.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pbn.py --apply    # schrijven + pushen
"""
import sys, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
GA = "/root/felix_hq/generate_article.py"
OLD = '<a href="/deals/">Deals</a>'
NEW = '<a href="/deals/">Deals</a><a href="/build/">Build</a>'

pages = sorted(B2B.glob("*/index.html"))
changed = already = nomatch = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if '/build/">Build' in t:
        already += 1; continue
    if OLD not in t:
        nomatch += 1; continue
    if APPLY:
        f.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    changed += 1

print(f"b2b-artikelen        : {len(pages)}")
print(f"  Build-link erbij    : {changed}")
print(f"  al gedaan           : {already}")
print(f"  geen Deals-anchor   : {nomatch}")

# template
gsrc = open(GA, encoding="utf-8").read()
if '/build/">Build' in gsrc:
    print("  template: al gepatcht")
elif OLD in gsrc:
    print("  template: " + ("wordt gepatcht" if APPLY else "matcht (apply patcht 'm)"))
else:
    print("  template: anchor NIET gevonden — meld dit")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

if OLD in gsrc and '/build/">Build' not in gsrc:
    import shutil, datetime, py_compile
    bak = GA + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(GA, bak)
    open(GA, "w", encoding="utf-8").write(gsrc.replace(OLD, NEW, 1))
    try:
        py_compile.compile(GA, doraise=True); print(f"✓ template gepatcht (backup {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, GA); print(f"✗ template syntaxfout — teruggezet: {e}")

if not changed:
    print("\nGeen artikel-wijzigingen om te pushen."); sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "b2b")
git("commit", "-m", f"Topnav: Build-link op {changed} b2b-artikelen (naar /build/-blueprints)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

#!/usr/bin/env python3
"""patch_article_nav2.py — dek de resterende b2b-artikelen met een GELOKALISEERDE
topnav (Alle reviews/Alle Tests/Startseite ...). Regex negeert de link-teksten en
voegt Tool Finder + Deals in tussen de 'All Reviews'- en 'Home'-link.

Veilig: dry-run by default; --apply schrijft + commit + push (main+staging).
Idempotent (skip als /finder/">Tool Finder al aanwezig).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pan2.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pan2.py --apply    # schrijven + pushen
"""
import sys, re, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"

RE = re.compile(r'(<div class="topnav-links"><a href="/b2b/">[^<]*</a>)(<a href="/">[^<]*</a></div>)')
INS = r'\1<a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a>\2'

pages = sorted(B2B.glob("*/index.html"))
changed = already = nomatch = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if '/finder/">Tool Finder' in t:
        already += 1; continue
    new, n = RE.subn(INS, t, count=1)
    if n == 0:
        nomatch += 1; continue
    if APPLY:
        f.write_text(new, encoding="utf-8")
    changed += 1

print(f"b2b-artikelen          : {len(pages)}")
print(f"  topnav uitgebreid    : {changed}")
print(f"  al gedaan            : {already}")
print(f"  nog steeds geen match: {nomatch}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)
if not changed:
    print("\nNiets te wijzigen."); sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "b2b")
git("commit", "-m", f"Topnav (gelokaliseerd): Tool Finder + Deals op {changed} resterende b2b-artikelen")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

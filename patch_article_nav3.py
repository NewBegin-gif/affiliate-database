#!/usr/bin/env python3
"""patch_article_nav3.py — dek de laatste b2b-artikelen met een afwijkende topnav
(o.a. de variant met een extra /about/-link). Algemene regex: voeg Tool Finder +
Deals in direct NA de eerste topnav-link (All Reviews), ongeacht wat erna komt.

Veilig: dry-run by default; --apply schrijft + commit + push (main+staging).
Idempotent (skip als /finder/">Tool Finder al aanwezig).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pan3.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pan3.py --apply    # schrijven + pushen
"""
import sys, re, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"

RE = re.compile(r'(<div class="topnav-links"><a href="/b2b/">[^<]*</a>)')
INS = r'\1<a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a>'

pages = sorted(B2B.glob("*/index.html"))
changed = already = nomatch = 0
hit = []
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if '/finder/">Tool Finder' in t:
        already += 1; continue
    new, n = RE.subn(INS, t, count=1)
    if n == 0:
        nomatch += 1; continue
    if APPLY:
        f.write_text(new, encoding="utf-8")
    changed += 1; hit.append(f.parent.name)

print(f"b2b-artikelen          : {len(pages)}")
print(f"  topnav uitgebreid    : {changed}  {hit if changed <= 15 else ''}")
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
git("commit", "-m", f"Topnav: Tool Finder + Deals op laatste {changed} b2b-artikelen (afwijkende variant)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

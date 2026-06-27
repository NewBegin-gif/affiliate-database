#!/usr/bin/env python3
"""fix_ownmoney.py — verwijder de claim "tests with his own money" uit de
b2b-pagina's (nieuwsbrief-CTA) → "cuts through the hype". Eerlijkheid: Daan test
niet elke tool met eigen geld, dus die blanket-claim moet weg.
DRY-RUN default. --apply: schrijf + push main+staging.
Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/fom.py
  /root/felix_hq/venv/bin/python3 /tmp/fom.py --apply
"""
import sys, subprocess
from pathlib import Path
APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
OLD, NEW = "tests with his own money", "cuts through the hype"

pages = list(B2B.glob("*/index.html")) + list(B2B.glob("*.html"))
hits = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if OLD in t:
        hits += 1
        if APPLY:
            f.write_text(t.replace(OLD, NEW), encoding="utf-8")
print(f"b2b-pagina's met de claim: {hits} ({'aangepast' if APPLY else 'dry-run'})")

if not APPLY:
    print("DRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)
if hits:
    def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
    git("add", "-A", "--", "b2b")
    git("commit", "-m", f"Eerlijkheid: verwijder 'tests with his own money'-claim uit {hits} b2b-pagina's")
    git("pull", "--no-rebase", "-X", "ours", "origin", "main")
    p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
    p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

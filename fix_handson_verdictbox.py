#!/usr/bin/env python3
"""fix_handson_verdictbox.py — corrigeer de valse "My hands-on review →"-claim in
de verdict-box op b2b-pagina's. Behoudt 'hands-on' alleen voor de 3 tools die Daan
ÉCHT gebruikte (bitvavo/replit/hostinger); elders → neutraal "Read my review →".

DRY-RUN (default): telt. --apply: schrijft + push main+staging.
Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/fhv.py
  /root/felix_hq/venv/bin/python3 /tmp/fhv.py --apply
"""
import sys, re, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
TESTED_URLS = ("/b2b/bitvavo-trading-bot/", "/b2b/replit-trading-bot/", "/b2b/hostinger-vps-review/")

pat = re.compile(r'(<a href="([^"]*)"[^>]*>)My hands-on review →</a>')

def repl(m):
    return m.group(0) if m.group(2) in TESTED_URLS else m.group(1) + "Read my review →</a>"

pages = list(B2B.glob("*/index.html")) + list(B2B.glob("*.html"))
changed = kept = fixed_anchors = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "My hands-on review" not in t:
        continue
    nt, n = pat.subn(repl, t)
    # tel hoeveel echt gewijzigd (niet-tested) vs behouden (tested)
    fa = t.count("My hands-on review") - nt.count("My hands-on review")
    if fa:
        fixed_anchors += fa
        if nt != t:
            changed += 1
            if APPLY:
                f.write_text(nt, encoding="utf-8")
    if nt.count("My hands-on review"):
        kept += nt.count("My hands-on review")

print(f"pagina's met de claim gescand; gewijzigd: {changed} | 'hands-on'→'review' anchors: {fixed_anchors} | terecht behouden (3 echte): {kept}")

if not APPLY:
    print("DRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

if changed:
    def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
    git("add", "-A", "--", "b2b")
    git("commit", "-m", f"Eerlijkheid: verdict-box 'hands-on review' → 'Read my review' op {changed} pagina's (hands-on alleen voor echt-geteste bitvavo/replit/hostinger)")
    git("pull", "--no-rebase", "-X", "ours", "origin", "main")
    p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
    p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

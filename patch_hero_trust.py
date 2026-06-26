#!/usr/bin/env python3
"""patch_hero_trust.py — vervang de zachte/onware hero-claim op de AIBM-homepage
(VPS-kopie) door een eerlijke regel, en haal de decoratieve sterren weg.
Lokale edits werden overschreven door de VPS-cron die de homepage pusht, dus dit
fixt de bron op de VPS. Idempotent, backup, push main+staging.

  '★★★★★ Trusted by founders in 60+ countries · N expert reviews'
   → 'Shown in 60+ countries · 1,700+ honest reviews'
Plus: 'expert reviews' → 'honest reviews' (twitter-meta e.d.).

DRY-RUN (default). --apply: schrijf + push.
Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pht.py
  /root/felix_hq/venv/bin/python3 /tmp/pht.py --apply
"""
import sys, re, shutil, datetime, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
IDX = REPO / "index.html"

HONEST = '<div class="hero-stars">Shown in 60+ countries · 1,700+ honest reviews</div>'
hero_re = re.compile(r'<div class="hero-stars">.*?</div>', re.S)

src = IDX.read_text(encoding="utf-8", errors="ignore")
m = hero_re.search(src)
print("=" * 56)
print("HERO-TRUST FIX" + ("  [APPLY]" if APPLY else "  [DRY-RUN]"))
print("=" * 56)
if m:
    print("  huidige regel:", re.sub(r"\s+", " ", m.group(0))[:120])
else:
    print("  ✗ hero-stars-div niet gevonden")

new = src
if m and "Shown in 60+ countries" not in m.group(0):
    new = hero_re.sub(HONEST, new, count=1)
n_exp = new.count("expert reviews")
new = new.replace("expert reviews", "honest reviews")
print(f"  sterren/claim vervangen: {'ja' if new != src and m else 'nee/al goed'}")
print(f"  'expert reviews' → 'honest reviews': {n_exp}x")

if not APPLY:
    print("\nDRY-RUN — niets geschreven.")
    sys.exit(0)
if new == src:
    print("Niets te wijzigen (al goed)."); sys.exit(0)

bak = f"{IDX}.bak-{STAMP}"; shutil.copy2(IDX, bak)
IDX.write_text(new, encoding="utf-8")
print("✓ geschreven, backup", bak)

def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "index.html")
git("commit", "-m", "Eerlijkheid: hero-claim → 'Shown in 60+ countries · 1,700+ honest reviews' (sterren + 'trusted by/expert' weg)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

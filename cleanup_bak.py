#!/usr/bin/env python3
"""cleanup_bak.py — verwijder per ongeluk gecommite .bak-bestanden uit de live
b2b/-map (ontstaan doordat build_hreflang `git add -A -- b2b` deed na de
cluster-optimize-backups). Commit de verwijdering + push naar beide branches.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/cleanbak.py
"""
import glob, os, subprocess
from pathlib import Path

REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
baks = glob.glob(str(REPO / "b2b" / "**" / "*.bak-*"), recursive=True)
print(f"gevonden .bak-bestanden onder b2b: {len(baks)}")
for b in baks:
    print("  -", os.path.relpath(b, REPO))
    os.remove(b)

if not baks:
    print("niets op te ruimen — klaar."); raise SystemExit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)

git("add", "-A", "--", "b2b")
print(git("commit", "-m", "cleanup: verwijder per ongeluk gecommite .bak-bestanden uit b2b").stdout.strip()[-200:])
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main")
print("push main   :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging")
print("push staging:", (p2.stdout + p2.stderr).strip()[-150:])
print("\n✅ klaar.")

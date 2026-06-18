#!/usr/bin/env python3
"""Vervang alle bestaande Murf-affiliate-links in de content door de nieuwe link.

Scant álle .html in de AIBM-content-repo (artikelen, hubs, deals, …) en vervangt
elke href naar een murf.ai-URL door de nieuwe affiliate-link. Dry-run default
(toont gevonden URLs + aantal); --apply vervangt + commit/push (→ victor-staging).
"""
import argparse
import os
import re
import subprocess

REPO = "/root/felix_hq/repos/aibuildermarketplace"
NEW = "https://get.murf.ai/ym93ob513bo2"
HREF = re.compile(r'href="([^"]*murf\.ai[^"]*)"', re.I)

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
A = ap.parse_args()

seen, files_with, changed = {}, [], 0
for root, dirs, files in os.walk(REPO):
    if ".git" in dirs:
        dirs.remove(".git")
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        try:
            h = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        old = [u for u in HREF.findall(h) if u != NEW]
        if not old:
            continue
        for u in old:
            seen[u] = seen.get(u, 0) + 1
        files_with.append(p)
        if A.apply:
            h2 = HREF.sub(f'href="{NEW}"', h)
            if h2 != h:
                open(p, "w", encoding="utf-8").write(h2)
                changed += 1

print(f"Oude Murf-links gevonden: {sum(seen.values())} in {len(files_with)} bestanden")
print("Distinct oude URLs:")
for u, c in sorted(seen.items(), key=lambda x: -x[1])[:12]:
    print(f"  {c:5}  {u[:95]}")

if not A.apply:
    print(f"\nDRY-RUN — draai met --apply om alles te vervangen door {NEW} + pushen.")
else:
    def git(*a):
        return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
    git("add", "-A")
    git("commit", "-m", f"Replace Murf affiliate links with new link ({changed} files)")
    git("pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit")
    ps = git("push", "origin", "main")
    tail = (ps.stdout + ps.stderr).strip().splitlines()
    print(f"\n✓ Vervangen in {changed} bestanden → {NEW}")
    print("✓ push:", tail[-1] if tail else "(niets)")
    print("→ Victor promoot staging → live via victor_automerge.sh.")

#!/usr/bin/env python3
"""READ-ONLY diagnose stap 5 (echt de laatste): de git-flow rond rebuild_index
in generate_article.py + hoe new_folders wordt bepaald + REPO_ROOT/REPO_B2B.
Schrijft NIETS.
"""
import os
import re

AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8", errors="replace").read()
lines = src.split("\n")


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def show(a, b):
    for i in range(a - 1, min(b, len(lines))):
        print(f"  {i+1}: {lines[i]}")


hr("1. REPO_ROOT / REPO_B2B definities")
for i, l in enumerate(lines):
    if re.search(r"REPO_ROOT\s*=|REPO_B2B\s*=|REPO\s*=", l):
        print(f"  {i+1}: {l.strip()}")

hr("2. Hoe wordt de folder-lijst (new_folders / existing_folders) bepaald?")
for i, l in enumerate(lines):
    if re.search(r"new_folders|existing_folders|os\.listdir|os\.scandir|def list_folders|glob", l):
        print(f"  {i+1}: {l.strip()[:150]}")

hr("3. Git-flow rond rebuild_index (regels 1690-1770)")
show(1690, 1770)

hr("4. Alle git-commando's in het bestand (add/commit/push/pull/reset/checkout/branch)")
for i, l in enumerate(lines):
    if re.search(r"git (add|commit|push|pull|reset|checkout|fetch|merge|branch|switch)|run_command\(.*git|subprocess.*git|HEAD:|origin/", l):
        print(f"  {i+1}: {l.strip()[:160]}")

hr("KLAAR — plak alles terug")

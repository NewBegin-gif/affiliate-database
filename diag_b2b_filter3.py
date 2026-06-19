#!/usr/bin/env python3
"""READ-ONLY diagnose stap 3: filter-lijst-bron + _brand() + VAULT/_AFF.

Doel: bevestigen hoe de tool-filterknoppen ontstaan (uit gedetecteerde brands),
hoe _brand() een brand herkent, en of 'Aspire' al in VAULT/_AFF zit.
Schrijft NIETS. Draai op de VPS, plak output terug.
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


hr("1. Filter-knop-opbouw (tools_html, regels 380-410)")
show(380, 410)

hr("2. rebuild_index kop: hoe loopt het door folders -> tiles -> unique tools (730-835)")
show(730, 835)

hr("3. _brand() detector (zoek 'def _brand')")
for i, l in enumerate(lines):
    if re.search(r"def _brand\s*\(", l):
        base = len(l) - len(l.lstrip())
        print(f"  {i+1}: {l}")
        for j in range(i + 1, min(i + 40, len(lines))):
            cur = lines[j]
            if cur.strip() and (len(cur) - len(cur.lstrip())) <= base and cur.lstrip().startswith("def "):
                break
            print(f"  {j+1}: {cur}")
        break

hr("4. VAULT-definitie (zoek 'VAULT =' / hoe geladen) + bevat Aspire?")
for i, l in enumerate(lines):
    if re.search(r"^\s*VAULT\s*=|VAULT\s*=\s*\{|data\.json|affiliate-database|json\.load", l):
        print(f"  {i+1}: {l.strip()[:160]}")
# Toon het blok waar VAULT als dict-literal begint (indien hardcoded)
for i, l in enumerate(lines):
    if re.match(r"\s*VAULT\s*=\s*\{", l):
        print(f"\n  --- VAULT dict vanaf regel {i+1} (max 60 regels) ---")
        for j in range(i, min(i + 60, len(lines))):
            print(f"  {j+1}: {lines[j]}")
            if lines[j].strip() == "}" and j > i:
                break
        break
print("\n  VAULT bevat 'aspire' (case-insensitive):", "aspire" in src.lower() and bool(re.search(r"aspire", src, re.I)))
print("  voorkomens van 'aspire' in het bestand:", len(re.findall(r"aspire", src, re.I)))

hr("5. _AFF-definitie (taglines/logo's) + bevat Aspire?")
for i, l in enumerate(lines):
    if re.search(r"^\s*_AFF\s*=|_AFF\s*=\s*\{", l):
        print(f"  {i+1}: {l.strip()[:160]}")
        print(f"  --- _AFF vanaf regel {i+1} (max 40 regels) ---")
        for j in range(i, min(i + 40, len(lines))):
            print(f"  {j+1}: {lines[j]}")
        break

hr("KLAAR — plak alles terug")

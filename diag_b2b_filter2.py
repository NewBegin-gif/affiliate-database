#!/usr/bin/env python3
"""READ-ONLY diagnose stap 2: dump de ECHTE VPS rebuild_index tool-detectie.

De b2b-filter (114 knoppen) wordt dynamisch gebouwd door generate_article.py
op de VPS. We moeten zien HOE folder-namen -> tool-namen worden gemapt
(grote dict? data.json? get_tool?), zodat we Aspire er blijvend in krijgen.

Schrijft NIETS. Draai op de VPS en plak de output terug.
"""
import os
import re
import glob

# Zoek generate_article.py op de gangbare plekken
candidates = [
    "/root/felix_hq/generate_article.py",
    "/root/felix_hq/repos/aibuildermarketplace/generate_article.py",
]
candidates += glob.glob("/root/felix_hq/**/generate_article.py", recursive=True)
seen = set()
paths = [p for p in candidates if not (p in seen or seen.add(p)) and os.path.exists(p)]


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


hr("0. generate_article.py locaties + timestamps")
if not paths:
    print("GEEN generate_article.py gevonden onder /root/felix_hq/")
for p in paths:
    import datetime as dt
    mt = dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")
    print(f"  {p}  (gewijzigd {mt}, {os.path.getsize(p)} bytes)")

# Gebruik de meest recent gewijzigde
if paths:
    AG = max(paths, key=os.path.getmtime)
    src = open(AG, encoding="utf-8", errors="replace").read()
    lines = src.split("\n")
    hr(f"1. rebuild_index + get_tool functies in {AG}")

    # Toon de get_tool / tool-detectie en de filter-knop-opbouw
    def dump_func(name_rx, span=80):
        rx = re.compile(rf"def\s+{name_rx}\s*\(")
        for i, l in enumerate(lines):
            if rx.search(l):
                print(f"\n----- regel {i+1}: {l.strip()} -----")
                # toon tot de volgende top-level/def-dedent of span regels
                base_indent = len(l) - len(l.lstrip())
                for j in range(i + 1, min(i + 1 + span, len(lines))):
                    cur = lines[j]
                    if cur.strip() and (len(cur) - len(cur.lstrip())) <= base_indent and cur.lstrip().startswith("def "):
                        break
                    print(f"  {j+1}: {cur}")
                return True
        return False

    # Hoe worden de TOOL-knoppen gebouwd? Zoek de regels die de filter-btn-lijst maken
    print("\n>>> Regels die met de tool-filterknoppen / tool-lijst te maken hebben:")
    for i, l in enumerate(lines):
        if re.search(r"filterTool|filter-btn|tool_buttons|tools_set|unique.*tool|sorted\(.*tool|get_tool|TOOL_MAP|TOOL_ICONS|BRAND", l, re.I):
            print(f"  {i+1}: {l.strip()[:150]}")

    # Dump get_tool volledig (de mapping die we moeten uitbreiden)
    print("\n>>> get_tool() volledig:")
    if not dump_func(r"get_tool"):
        print("  (geen get_tool gevonden — tool-detectie zit elders)")

    # Zoek of data.json / een externe lijst gebruikt wordt voor de tools
    hr("2. Externe bronnen voor de tool-lijst?")
    for i, l in enumerate(lines):
        if re.search(r"data\.json|affiliate-database|affdb|TOOL_ICONS\s*=|TOOL_MAP\s*=|BRANDS?\s*=|KNOWN", l):
            print(f"  {i+1}: {l.strip()[:150]}")

    # Hoe wordt rebuild_index aangeroepen / wanneer?
    hr("3. Waar wordt rebuild_index aangeroepen?")
    for i, l in enumerate(lines):
        if "rebuild_index" in l:
            print(f"  {i+1}: {l.strip()[:150]}")
else:
    print("Niets te dumpen.")

hr("KLAAR — plak alles terug")

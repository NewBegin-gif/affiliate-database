#!/usr/bin/env python3
"""diag_v2_nav.py — READ-ONLY. Vind waar _v2_builder (de actieve artikel-template)
is gedefinieerd en hoe het de topnav bouwt, zodat we de basic-nav bij de bron
kunnen fixen (anders komen er nieuwe basic-nav-pagina's bij).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/dv2.py
"""
import re, glob, os

HQ = "/root/felix_hq"
# 1) welk bestand definieert _v2_builder?
print("=== bestanden met '_v2_builder' / '_USE_V2_TEMPLATE' ===")
hits = []
for f in glob.glob(HQ + "/*.py"):
    try:
        t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if "_v2_builder" in t or "_USE_V2_TEMPLATE" in t:
        defs = "def _v2_builder" in t
        print(f"  {os.path.basename(f)}  {'(DEFINIEERT _v2_builder)' if defs else ''}")
        if defs:
            hits.append(f)

# 2) toon de topnav-links in die bestand(en)
print("\n=== topnav-links / nav-markup in die bestanden ===")
for f in hits or glob.glob(HQ + "/*.py"):
    t = open(f, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'topnav-links.{0,160}', t, re.S):
        seg = re.sub(r"\s+", " ", m.group(0))[:180]
        print(f"  [{os.path.basename(f)}] {seg}")
print("\nKLAAR — plak alles terug.")

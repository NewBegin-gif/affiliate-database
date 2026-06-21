#!/usr/bin/env python3
"""diag_save_logic.py — READ-ONLY. Toont (a) de volledige add_network_footer-
functie en (b) hoe generate_article.py het artikel naar schijf schrijft, zodat
we de truncatie bij de bron kunnen voorkomen.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/dsl.py
"""
print("=" * 72); print("A) aibm_network_footer.py (volledig)"); print("=" * 72)
for i, l in enumerate(open("/root/felix_hq/aibm_network_footer.py", encoding="utf-8").read().split("\n")):
    print(f"L{i+1}: {l}")

print("\n" + "=" * 72); print("B) generate_article.py — schrijf-/save-logica (1850-1878)"); print("=" * 72)
lines = open("/root/felix_hq/generate_article.py", encoding="utf-8").read().split("\n")
for i in range(1849, min(1878, len(lines))):
    print(f"L{i+1}: {lines[i]}")

import re
print("\n" + "=" * 72); print("B2) alle .write(/open(...,'w') in generate_article.py"); print("=" * 72)
for i, l in enumerate(lines):
    if re.search(r"\.write\(|open\([^)]*['\"]w|os\.replace|os\.rename|tmp|atomic|f\.write", l):
        print(f"L{i+1}: {l.strip()[:150]}")
print("\nKLAAR — plak alles terug.")

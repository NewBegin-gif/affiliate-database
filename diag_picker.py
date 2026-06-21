#!/usr/bin/env python3
"""diag_picker.py — READ-ONLY. Dump de exacte taal-picker in generate_article.py
(rond regel 1480-1530) + de talenbron van generate_new_languages.py, zodat de
talen-curatie-patch (C) exact-matchend geschreven kan worden.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/dp.py
"""
from pathlib import Path

ga = Path("/root/felix_hq/generate_article.py").read_text(encoding="utf-8").split("\n")
print("=" * 72); print("generate_article.py — regels 1478-1530 (brand+taal-picker)"); print("=" * 72)
for i in range(1477, min(1530, len(ga))):
    print(f"L{i+1}: {ga[i]}")

print("\n" + "=" * 72); print("generate_article.py — LANG_CODES (311-320)"); print("=" * 72)
for i in range(310, 320):
    print(f"L{i+1}: {ga[i]}")

gnl = Path("/root/felix_hq/generate_new_languages.py")
print("\n" + "=" * 72); print(f"generate_new_languages.py — talenbron"); print("=" * 72)
if gnl.exists():
    import re
    lines = gnl.read_text(encoding="utf-8").split("\n")
    for i, l in enumerate(lines):
        if re.search(r"lang|LANG|NEW_|=\s*\[|=\s*\{|code", l, re.I):
            print(f"L{i+1}: {l.strip()[:140]}")
else:
    print("  bestaat niet")
print("\nKLAAR — plak alles terug.")

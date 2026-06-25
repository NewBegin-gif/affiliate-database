#!/usr/bin/env python3
"""diag_rating_blocks.py — READ-ONLY. Print de EXACTE broncode-blokken rond de
rating (zichtbaar + schema + meta + parsing) zodat de fix-patch precieze anchors
heeft. Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/drb.py
"""
def dump(path, ranges):
    print("=" * 74); print(path); print("=" * 74)
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    for a, b in ranges:
        print(f"----- L{a}-{b} " + "-" * 40)
        for i in range(a - 1, min(b, len(L))):
            print(f"{i+1}: {L[i]}")
        print()

dump("/root/felix_hq/review_template.py",
     [(3690, 3760), (3790, 3812), (3088, 3096)])
dump("/root/felix_hq/generate_article.py",
     [(815, 835), (1822, 1835)])
print("KLAAR — plak alles terug (codeblok).")

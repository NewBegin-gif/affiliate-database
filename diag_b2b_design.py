#!/usr/bin/env python3
"""READ-ONLY: dump de design-relevante delen van de b2b-index-generator
(generate_article.py): topnav, _brandlogo, kaart-template, CSS. Schrijft NIETS.
"""
import re
AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read()
lines = src.split("\n")


def hr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def show(a, b):
    for i in range(a - 1, min(b, len(lines))):
        print(f"{i+1}: {lines[i]}")


def dump_func(name, span=40):
    for i, l in enumerate(lines):
        if re.search(rf"def\s+{re.escape(name)}\s*\(", l):
            base = len(l) - len(l.lstrip())
            print(f"--- {name} @ {i+1} ---")
            for j in range(i, min(i + span, len(lines))):
                cur = lines[j]
                if j > i and cur.strip() and (len(cur) - len(cur.lstrip())) <= base and cur.lstrip().startswith("def "):
                    break
                print(f"{j+1}: {cur}")
            return True
    return False


hr("1. _brandlogo (kaart-icoon-generator)")
dump_func("_brandlogo", 30)

hr("2. _build_index_html — kaart-template + topnav (zoek 'class=\"card\"' / topnav)")
for i, l in enumerate(lines):
    if re.search(r'class=\\?"card"|class=\\?"topnav"|card-icon|<nav|B2B Knowledge|class=\\?"card-top"', l):
        print(f"{i+1}: {l.strip()[:160]}")

hr("3. CSS: .topnav / .card / .card-icon (zoek in de template-CSS)")
for i, l in enumerate(lines):
    if re.search(r'\.topnav\s*\{|\.card\s*\{|\.card-icon\s*\{|\.card-top\s*\{|\.grid\s*\{|\.card:hover', l):
        print(f"{i+1}: {l.strip()[:160]}")

hr("4. def _build_index_html signatuur + eerste 15 regels")
dump_func("_build_index_html", 15)

hr("KLAAR — plak alles terug")

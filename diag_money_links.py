#!/usr/bin/env python3
"""READ-ONLY: dump de internal-link / money-link-steering code in generate_article.py."""
import re
AG = "/root/felix_hq/generate_article.py"
lines = open(AG, encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if re.search(r'_MONEY|random_links|li_links|internal_links_html|MONEY-LINK|_picked', l):
        # print dit blok met wat context
        pass
# print elk blok met _MONEY .. internal_links_html, met 2 regels marge
idxs = [i for i, l in enumerate(lines) if "MONEY-LINK-STEERING" in l or "internal_links_html" in l or "li_links" in l]
if idxs:
    lo, hi = max(0, min(idxs) - 2), min(len(lines), max(idxs) + 3)
    for i in range(lo, hi):
        print(f"{i+1}: {lines[i]}")
else:
    print("geen money-link-blok gevonden")

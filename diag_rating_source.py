#!/usr/bin/env python3
"""diag_rating_source.py — READ-ONLY. Toon waar de (nep-4.6) rating wordt
gegenereerd in generate_article.py + review_template.py: de Review-schema
(reviewRating/ratingValue) én een eventuele ZICHTBARE rating op de pagina.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/drs.py
"""
import re
for path in ("/root/felix_hq/generate_article.py", "/root/felix_hq/review_template.py"):
    print("=" * 72); print(path); print("=" * 72)
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    pat = re.compile(r"ratingValue|reviewRating|aggregateRating|\"Review\"|'Review'|"
                     r"\[.rating.\]|\.get\(.rating|rating\"|★|verdict|star|/5|bestRating", re.I)
    for i, l in enumerate(lines):
        if pat.search(l):
            print(f"  L{i+1}: {l.strip()[:150]}")
print("\nKLAAR — plak alles terug.")

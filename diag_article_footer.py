#!/usr/bin/env python3
"""diag_article_footer.py — READ-ONLY. Vind de footer-/body-plek in de ARTIKEL-
template van generate_article.py, zodat de nieuwsbrief-template-patch exact-
matchend kan worden geschreven (zonder de index-template te raken).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/df.py
"""
import re
AG = "/root/felix_hq/generate_article.py"
lines = open(AG, encoding="utf-8").read().split("\n")
pat = re.compile(r"<footer|</body>|sister-net|footer_html|FOOTER|</main>|internal_links_html\b")
for i, l in enumerate(lines):
    if pat.search(l):
        print(f"L{i+1}: {l.rstrip()[:160]}")
print("\nKLAAR — plak alles terug.")

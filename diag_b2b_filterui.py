#!/usr/bin/env python3
"""READ-ONLY: dump de filter-template (HTML + JS) van de b2b-index-generator."""
import re
AG = "/root/felix_hq/generate_article.py"
lines = open(AG, encoding="utf-8").read().split("\n")
def hr(t): print("\n"+"="*70+f"\n{t}\n"+"="*70)

hr("1. tools_html / langs_html build (regels 385-410)")
for i in range(384, 411):
    if i < len(lines): print(f"{i+1}: {lines[i]}")

hr("2. filter-HTML in de template (filters-wrap / filter-label / {tools_html} / {langs_html} / search-box)")
for i, l in enumerate(lines):
    if re.search(r'filters-wrap|filters-inner|filter-label|\{tools_html\}|\{langs_html\}|search-box|filter-sep|filterSearch', l):
        print(f"{i+1}: {lines[i].rstrip()[:170]}")

hr("3. filter-CSS (.filter-btn / .filters-inner / .search-box)")
for i, l in enumerate(lines):
    if re.search(r'\.filter-btn\s*\{|\.filters-inner\s*\{|\.search-box\s*\{|\.filter-sep\s*\{|\.filter-label\s*\{', l):
        print(f"{i+1}: {lines[i].strip()[:170]}")

hr("KLAAR")

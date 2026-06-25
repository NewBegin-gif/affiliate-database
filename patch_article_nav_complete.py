#!/usr/bin/env python3
"""patch_article_nav_complete.py — dek ALLE resterende b2b-artikelen die Finder/
Deals/Build in de topnav missen (basic-nav-variant, hero-variant, gelokaliseerd),
en fix de tweede nav-template in generate_article.py (count=1 eerder raakte maar
één van de twee templates).

Per artikel: vul in de topnav-links de ontbrekende links aan, direct na de eerste
(/b2b/) link. Idempotent. Dry-run by default; --apply schrijft + commit + push
(main+staging).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pnc.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/pnc.py --apply
"""
import sys, re, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
GA = "/root/felix_hq/generate_article.py"
FIRST = re.compile(r'(<div class="topnav-links"><a href="/b2b/">[^<]*</a>)')


def fix_html(html):
    if '/build/">Build' in html:
        return html, False
    s = html.find('<div class="topnav-links">')
    if s == -1:
        return html, False
    e = html.find('</div>', s)
    topnav = html[s:e]
    add = ""
    if '/finder/' not in topnav:
        add += '<a href="/finder/">Tool Finder</a>'
    if '/deals/' not in topnav:
        add += '<a href="/deals/">Deals</a>'
    if '/build/' not in topnav:
        add += '<a href="/build/">Build</a>'
    if not add:
        return html, False
    m = FIRST.search(html)
    if not m:
        return html, False
    return html[:m.end()] + add + html[m.end():], True


pages = sorted(B2B.glob("*/index.html"))
changed = skip = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    nt, did = fix_html(t)
    if did:
        if APPLY:
            f.write_text(nt, encoding="utf-8")
        changed += 1
    else:
        skip += 1
print(f"b2b-artikelen: {len(pages)} | aangevuld: {changed} | al compleet/geen-nav: {skip}")

# template: vervang ALLE resterende basic-nav door volledige nav
gsrc = open(GA, encoding="utf-8").read()
BASIC = '<div class="topnav-links"><a href="/b2b/">All Reviews</a><a href="/">Home</a></div>'
FULL = ('<div class="topnav-links"><a href="/b2b/">All Reviews</a><a href="/finder/">Tool Finder</a>'
        '<a href="/deals/">Deals</a><a href="/build/">Build</a><a href="/">Home</a></div>')
n_tmpl = gsrc.count(BASIC)
print(f"template: resterende basic-nav-occurrences: {n_tmpl}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

if n_tmpl:
    import shutil, datetime, py_compile
    bak = GA + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(GA, bak)
    open(GA, "w", encoding="utf-8").write(gsrc.replace(BASIC, FULL))
    try:
        py_compile.compile(GA, doraise=True); print(f"✓ template gefixt ({n_tmpl}x) backup {bak}")
    except py_compile.PyCompileError as ex:
        shutil.copy2(bak, GA); print(f"✗ template syntaxfout — teruggezet: {ex}")

if not changed:
    print("\nGeen artikel-wijzigingen."); sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "b2b")
git("commit", "-m", f"Topnav: Finder/Deals/Build compleet op resterende {changed} b2b-artikelen + 2e template")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

#!/usr/bin/env python3
"""patch_nav_source.py — fix de nav bij de BRON in de twee actieve templates,
zodat nieuwe artikelen automatisch Finder · Deals · Build krijgen (geen
terugkerende basic-nav meer).

  1) generate_article.py: voeg Build toe aan de 'All Reviews/Finder/Deals/Home'-nav.
  2) review_template.py: voeg Finder + Deals + Build toe aan de gelokaliseerde
     '{all_reviews}/{home}'-nav.

Idempotent, per bestand backup + py_compile (auto-revert). Legacy/backup/debug-
scripts worden bewust niet aangeraakt.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pns.py
"""
import shutil, datetime, py_compile
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def patch(path, old, new, marker):
    try:
        src = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"✗ {path}: niet gevonden"); return
    if marker in src:
        print(f"= {path.split('/')[-1]}: al gepatcht"); return
    if old not in src:
        print(f"✗ {path.split('/')[-1]}: anchor niet gevonden"); return
    bak = f"{path}.bak-{STAMP}"; shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(src.replace(old, new))
    try:
        py_compile.compile(path, doraise=True)
        print(f"✓ {path.split('/')[-1]}: gepatcht ({src.count(old)}x) backup {bak}")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, path); print(f"✗ {path.split('/')[-1]}: syntaxfout — teruggezet: {e}")


# 1) generate_article.py — Build toevoegen aan de 2e nav
patch("/root/felix_hq/generate_article.py",
      '<a href="/b2b/">All Reviews</a><a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a><a href="/">Home</a>',
      '<a href="/b2b/">All Reviews</a><a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a><a href="/build/">Build</a><a href="/">Home</a>',
      marker='Deals</a><a href="/build/">Build</a><a href="/">Home</a>')

# 2) review_template.py — Finder/Deals/Build toevoegen aan de gelokaliseerde nav
patch("/root/felix_hq/review_template.py",
      '<a href="/b2b/">{L[\'all_reviews\']}</a><a href="/">{L[\'home\']}</a>',
      '<a href="/b2b/">{L[\'all_reviews\']}</a><a href="/finder/">Tool Finder</a><a href="/deals/">Deals</a><a href="/build/">Build</a><a href="/">{L[\'home\']}</a>',
      marker='/finder/">Tool Finder</a><a href="/deals/">Deals</a><a href="/build/">Build</a><a href="/">{L[\'home\']}')

print("\nKLAAR — plak alles terug.")

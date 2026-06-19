#!/usr/bin/env python3
"""patch_victor_money_links.py — stuur interne link-equity naar de money-pages.

Victor zette per artikel 3 WILLEKEURIGE interne links. Dat verspreidt autoriteit
gelijkmatig. Beter: elke pagina linkt naar 2 'money-pages' (near-page-1 winners +
key-affiliates) + 1 willekeurige (diversiteit). Zo klimmen proton-pricing-en
(pos 11,9), de Bitvavo-cluster e.d. richting pagina 1.

Idempotent (marker), backup + py_compile. Draai met venv:
  /root/felix_hq/venv/bin/python3 /tmp/patch_victor_money_links.py
"""
import shutil
import datetime
import py_compile

AG = "/root/felix_hq/generate_article.py"
MARK = "MONEY-LINK-STEERING v1"

TARGET = "            random_links = random.sample(existing_folders, 3)\n"
REPL = (
    f"            # ── {MARK}: stuur link-equity naar near-page-1 money-pages ──\n"
    "            _MONEY = ['proton-pricing-en', 'bitvavo-scale-up', 'bitvavo-pricing-en',\n"
    "                      'bitvavo-trading-bot', 'bitvavo-ultimate-review-2026',\n"
    "                      'payoneer-alternatives-en', 'chemicloud-pricing-en', 'gamma-pricing-en',\n"
    "                      'aspire-review', 'aisdr-vs-clay-en', 'replit-trading-bot']\n"
    "            _am = [m for m in _MONEY if m in existing_folders and m != slug]\n"
    "            random.shuffle(_am)\n"
    "            _picked = _am[:2]\n"
    "            _others = [f for f in existing_folders if f not in _picked and f != slug]\n"
    "            _picked += random.sample(_others, max(0, 3 - len(_picked)))\n"
    "            random_links = _picked\n"
)

src = open(AG, encoding="utf-8").read()
if MARK in src:
    print("✓ Money-link-steering staat er al — skip")
elif TARGET not in src:
    print("✗ Doel-regel niet gevonden (generate_article.py gewijzigd?). ABORT.")
    print("  Verwacht: " + TARGET.strip())
else:
    b = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(AG, b)
    open(AG, "w", encoding="utf-8").write(src.replace(TARGET, REPL, 1))
    try:
        py_compile.compile(AG, doraise=True)
        print(f"✓ Money-link-steering toegepast (backup: {b})")
        print("  → elk nieuw artikel linkt nu naar 2 money-pages + 1 willekeurige.")
    except py_compile.PyCompileError as e:
        shutil.copy2(b, AG)
        print("✗ syntaxfout — backup teruggezet:", e)

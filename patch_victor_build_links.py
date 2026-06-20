#!/usr/bin/env python3
"""patch_victor_build_links.py — laat Victors interne 'Read more'-blok ook 1
roterende /build/-gids-link bevatten (juiste /build/-pad). Raakt toekomstige
artikelen. Backup + py_compile. Draai met venv:
  /root/felix_hq/venv/bin/python3 /tmp/pvbl.py
"""
import shutil, datetime, py_compile
AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read()

if "_BUILD = [" in src:
    print("✓ build-links staan er al in — skip"); raise SystemExit(0)

anchor = ('            internal_links_html = f"<div style=\'margin-top:30px;padding-top:20px;'
          'border-top:1px solid #eee;\'><h4>Read more B2B Insights:</h4><ul>{li_links}</ul></div>"')
if anchor not in src:
    print("✗ anchor (internal_links_html) niet gevonden — ABORT"); raise SystemExit(1)

inject = (
    "            _BUILD = [('crypto-trading-bot-no-code','Build a crypto trading bot with AI'),"
    "('what-is-algorithmic-trading','What is algorithmic trading?'),"
    "('bitvavo-api-for-non-coders','The Bitvavo API for non-coders'),"
    "('cost-of-running-a-trading-bot','What it costs to run a trading bot'),"
    "('prop-firm-trading-bot','Can a bot pass a prop-firm evaluation?'),"
    "('emotionless-crypto-trading','Emotionless crypto trading'),"
    "('passive-income-crypto-systems','Passive crypto income, honestly'),"
    "('ai-agent-build-vs-buy','AI agent: build or buy?'),"
    "('ai-programmatic-seo','AI + programmatic SEO')]\n"
    "            _bg = random.choice(_BUILD)\n"
    "            li_links += \"<li><a href='/build/\" + _bg[0] + \"/'>\" + _bg[1] + \"</a></li>\"\n"
)
src = src.replace(anchor, inject + anchor, 1)

bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(AG, bak); open(AG, "w", encoding="utf-8").write(src)
try:
    py_compile.compile(AG, doraise=True)
    print("✓ build-link-steering toegevoegd + syntax OK. backup:", bak)
    print("  Toekomstige Victor-artikelen linken nu ook naar een /build/-gids.")
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG); print("✗ syntaxfout — teruggezet:", e)

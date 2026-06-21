#!/usr/bin/env python3
"""patch_victor_winner_links.py — laat Victors 'Read more B2B Insights'-blok ook
één roterende link naar een WINNER-pagina bevatten (hoog-impressie pagina's uit
GSC). Zo versterkt elk nieuw artikel automatisch je sterkste pagina's i.p.v.
willekeurige interne links (compounding autoriteit-concentratie).

Zelfde, bewezen aanpak als patch_victor_build_links.py. Idempotent, backup +
py_compile (auto-revert), abort veilig als de anchor niet matcht.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pvwl.py
"""
import shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read()

if "_WINNERS = [" in src:
    print("✓ winner-links staan er al in — skip"); raise SystemExit(0)

anchor = ('            internal_links_html = f"<div style=\'margin-top:30px;padding-top:20px;'
          'border-top:1px solid #eee;\'><h4>Read more B2B Insights:</h4><ul>{li_links}</ul></div>"')
if anchor not in src:
    print("✗ anchor (internal_links_html) niet gevonden — ABORT (niets gewijzigd)"); raise SystemExit(1)

inject = (
    "            _WINNERS = [('proton-pricing-en','How much does Proton Mail cost?'),"
    "('bitvavo-pricing-en','Bitvavo fees explained'),"
    "('bitvavo-trading-bot','Bitvavo trading bot guide'),"
    "('bitvavo-scale-up','Is Bitvavo right for your business?'),"
    "('replit-trading-bot','Build a Replit trading bot'),"
    "('aisdr-vs-clay-en','AiSDR vs Clay'),"
    "('hostinger-vps-review','Hostinger VPS review'),"
    "('beehiiv-pricing-en','Beehiiv pricing guide'),"
    "('trainual-employee-onboarding-software-en','Trainual for onboarding'),"
    "('sanebox-pricing-en','SaneBox pricing')]\n"
    "            _wn = random.choice(_WINNERS)\n"
    "            li_links += \"<li><a href='/b2b/\" + _wn[0] + \"/'>\" + _wn[1] + \"</a></li>\"\n"
)
src = src.replace(anchor, inject + anchor, 1)

bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(AG, bak); open(AG, "w", encoding="utf-8").write(src)
try:
    py_compile.compile(AG, doraise=True)
    print("✓ winner-link-steering toegevoegd + syntax OK. backup:", bak)
    print("  Elk nieuw Victor-artikel linkt nu ook naar een winner-pagina.")
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG); print("✗ syntaxfout — teruggezet:", e)

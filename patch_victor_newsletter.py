#!/usr/bin/env python3
"""patch_victor_newsletter.py — elk NIEUW Victor-artikel krijgt de native Beehiiv
nieuwsbrief-opt-in (zelfde box als de backfill van bestaande artikelen).

Template-agnostisch: voegt het formulier toe aan `internal_links_html` net vóór
het renderen, zodat het in BEIDE templates (build_article_html én _v2_builder)
terechtkomt. Idempotent, backup + py_compile (auto-revert), abort bij geen match.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pvn.py
"""
import shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read()

if "_NEWSLETTER_FORM" in src:
    print("✓ nieuwsbrief-template staat er al in — skip"); raise SystemExit(0)

anchor = ("        full_html = _v2_builder(title, content, brand, slug, schema_json, "
          "internal_links_html)")
if anchor not in src:
    print("✗ anchor (full_html = _v2_builder...) niet gevonden — ABORT (niets gewijzigd)")
    raise SystemExit(1)

# zelfde HTML als backfill_newsletter_b2b.py (marker aibm-nl-v1) — single-quoted
# Python-string; HTML gebruikt dubbele quotes, tekst bevat geen apostrofs.
form = (
    '<!-- aibm-nl-v1 -->'
    '<section style="max-width:640px;margin:48px auto;padding:28px 24px;background:#0f172a;'
    'border:1px solid #1e293b;border-radius:16px;text-align:center;font-family:system-ui,-apple-system,sans-serif">'
    '<h3 style="color:#f1f5f9;font-size:1.25rem;font-weight:800;margin:0 0 8px">'
    'Get the best AI &amp; business software, monthly</h3>'
    '<p style="color:#94a3b8;font-size:.92rem;line-height:1.5;margin:0 auto 16px;max-width:480px">'
    'Honest reviews, real pricing and time-saving workflows — from an ex-banker who tests with his own money. No spam.</p>'
    '<form action="https://aibuildermarketplace.beehiiv.com/subscribe" method="get" target="_blank" '
    'style="display:flex;gap:8px;max-width:420px;margin:0 auto;flex-wrap:wrap;justify-content:center">'
    '<input type="email" name="email" required placeholder="Enter your email" '
    'style="flex:1 1 200px;min-width:180px;padding:11px 14px;border-radius:9px;border:1px solid #334155;'
    'background:rgba(255,255,255,.06);color:#f1f5f9;font-size:.92rem">'
    '<button type="submit" style="padding:11px 22px;border-radius:9px;border:0;background:#3b82f6;'
    'color:#fff;font-weight:700;font-size:.92rem;cursor:pointer;white-space:nowrap">Subscribe &rarr;</button>'
    '</form></section>'
)

inject = (
    "        _NEWSLETTER_FORM = " + repr(form) + "\n"
    "        internal_links_html = (internal_links_html or '') + _NEWSLETTER_FORM\n"
)
src = src.replace(anchor, inject + anchor, 1)

bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(AG, bak); open(AG, "w", encoding="utf-8").write(src)
try:
    py_compile.compile(AG, doraise=True)
    print("✓ nieuwsbrief-template toegevoegd + syntax OK. backup:", bak)
    print("  Elk nieuw Victor-artikel krijgt nu de Beehiiv-opt-in (beide templates).")
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG); print("✗ syntaxfout — teruggezet:", e)

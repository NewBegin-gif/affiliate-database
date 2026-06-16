#!/usr/bin/env python3
"""Patch generate_article.py: zet per-tool og:image (de branded /og/<slug>.png)
op elke nieuw gegenereerde /b2b/-pagina, template-onafhankelijk.

Voegt een post-processing-helper toe en roept 'm aan vlak vóór het wegschrijven
(naast add_network_footer), zodat het werkt of Victor nu build_article_html of
_v2_builder gebruikt. Valt veilig terug op de bestaande default als een tool nog
geen OG-kaart heeft. Idempotent, met backup + compile-check.
"""
import py_compile
import shutil
import time

P = "/root/felix_hq/generate_article.py"

HELPER = '''

def _set_og_image(full_html, brand):
    """Zet og:image/twitter:image naar de per-tool OG-kaart als die bestaat."""
    import os as _o, re as _r
    slug = _r.sub(r"[^a-z0-9]+", "-", (brand or "").lower()).strip("-")
    if slug and _o.path.exists(_o.path.join(REPO_ROOT, "og", slug + ".png")):
        u = f"{DOMAIN}/og/{slug}.png"
        full_html = _r.sub(r'(<meta property="og:image" content=")[^"]*(")',
                           lambda m: m.group(1) + u + m.group(2), full_html)
        full_html = _r.sub(r'(<meta name="twitter:image" content=")[^"]*(")',
                           lambda m: m.group(1) + u + m.group(2), full_html)
    return full_html
'''

s = open(P, encoding="utf-8").read()
orig = s

if "_set_og_image" not in s:
    anchor = "from aibm_network_footer import add_network_footer"
    if anchor in s:
        s = s.replace(anchor, anchor + "\n" + HELPER, 1)
    else:
        print("⚠️ network-footer import niet gevonden — voeg helper toe vóór 'def main()'")
        s = s.replace("def main():", HELPER + "\n\ndef main():", 1)

call_old = "        full_html = add_network_footer(full_html)"
call_new = call_old + "\n        full_html = _set_og_image(full_html, brand)"
if "_set_og_image(full_html, brand)" not in s and call_old in s:
    s = s.replace(call_old, call_new, 1)

if s == orig:
    print("• al gepatcht of ankers niet gevonden")
else:
    bak = P + ".bak." + time.strftime("%Y%m%d%H%M%S")
    shutil.copy(P, bak)
    open(P, "w", encoding="utf-8").write(s)
    try:
        py_compile.compile(P, doraise=True)
        print(f"✓ gepatcht + compile OK (backup: {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy(bak, P)
        print(f"✗ compile-fout, teruggedraaid: {e}")

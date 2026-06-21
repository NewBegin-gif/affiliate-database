#!/usr/bin/env python3
"""patch_fix_truncation.py — STAP 3 (preventie): voorkom nieuwe afgekapte pagina's.

Fix 1 (generate_article.py): schrijf het artikel ATOMISCH (tmp + os.replace) en
  sla GEEN onvolledige HTML op (volledigheidscheck op </html>). Voorheen: directe
  open(...,"w") → onderbroken proces = half bestand.
Fix 2 (aibm_network_footer.py): de fallback plakt het netwerk-footerblok NIET meer
  op pagina's zonder sluittag (anders maskeert het afgekapte pagina's).

Idempotent, per bestand backup + py_compile (auto-revert), abort bij geen match.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pft.py
"""
import shutil, datetime, py_compile
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def patch(path, label, old, new, marker):
    src = open(path, encoding="utf-8").read()
    if marker in src:
        print(f"= {label}: al gepatcht — skip"); return
    if old not in src:
        print(f"✗ {label}: anchor niet gevonden — NIET gewijzigd"); return
    bak = f"{path}.bak-{STAMP}"; shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
    try:
        py_compile.compile(path, doraise=True)
        print(f"✓ {label}: gepatcht (backup {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, path); print(f"✗ {label}: syntaxfout — teruggezet: {e}")


# ---------- Fix 1: atomische schrijf + volledigheidscheck ----------
GA = "/root/felix_hq/generate_article.py"
old1 = ('        os.makedirs(path, exist_ok=True)\n'
        '        full_html = add_network_footer(full_html)\n'
        '        with open(f"{path}/index.html", "w") as f:\n'
        '            f.write(full_html)\n')
new1 = ('        full_html = add_network_footer(full_html)\n'
        '        if "</html>" not in full_html.lower():\n'
        '            print(f"\\u26a0\\ufe0f afgekapte HTML voor {slug} \\u2014 niet opgeslagen")\n'
        '        else:\n'
        '            os.makedirs(path, exist_ok=True)\n'
        '            _tmp = f"{path}/index.html.tmp"\n'
        '            with open(_tmp, "w", encoding="utf-8") as f:\n'
        '                f.write(full_html)\n'
        '            os.replace(_tmp, f"{path}/index.html")\n')
patch(GA, "1) atomische schrijf + volledigheidscheck", old1, new1, marker="index.html.tmp")

# ---------- Fix 2: fallback maskeert geen broken pagina's meer ----------
NF = "/root/felix_hq/aibm_network_footer.py"
old2 = '    return html.rstrip() + "\\n" + _BLOCK + "\\n"'
new2 = ('    # GEEN footer plakken op pagina zonder sluittag (afgekapt) — niet maskeren\n'
        '    return html')
patch(NF, "2) fallback maskeert geen afgekapte pagina's", old2, new2, marker="niet maskeren")

print("\nKLAAR — plak alles terug.")

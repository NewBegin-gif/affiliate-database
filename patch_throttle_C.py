#!/usr/bin/env python3
"""patch_throttle_C.py — talen cureren (35 -> 20 bewezen), de bron van dunne massa.

Keep-lijst (data-gedreven, GSC 90d: max>=20 of tot>=40 impr):
  en fr du po ge sp it pl sv da no tr id vi br mx uk   (uit generate_article.py)
  ko zh yo                                              (uit generate_new_languages.py)
Schrap: ja + alle lange-staart-talen (af am ar cs el fi ha hi hu ro ru sw th zu).

Twee edits, idempotent, backup + py_compile (auto-revert bij syntaxfout):
  1) generate_article.py — picker filtert op KEEP_CODES (LANG_CODES blijft heel,
     dus bestaande slug-parsing + brand-taal-locks blijven werken).
  2) generate_new_languages.py — default-run beperkt tot {ko, zh, yo}.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/c.py
"""
import re, shutil, datetime, py_compile
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


# ---------- 1) generate_article.py: picker filtert op KEEP_CODES ----------
GA = "/root/felix_hq/generate_article.py"
old1 = ('    lang_counts = {}\n'
        '    for lang_name, code in LANG_CODES.items():\n'
        '        lang_counts[lang_name] = len([f for f in existing_folders if f.endswith(f"-{code}")])\n')
new1 = ('    lang_counts = {}\n'
        '    KEEP_CODES = {"en", "fr", "du", "po", "ge", "sp", "it", "pl", "sv", "da",\n'
        '                  "no", "tr", "id", "vi", "br", "mx", "uk"}  # data-gedreven (GSC); ja+staart geschrapt\n'
        '    for lang_name, code in LANG_CODES.items():\n'
        '        if code not in KEEP_CODES:\n'
        '            continue\n'
        '        lang_counts[lang_name] = len([f for f in existing_folders if f.endswith(f"-{code}")])\n')
patch(GA, "1) generate_article.py talen-filter", old1, new1, marker="KEEP_CODES")

# ---------- 2) generate_new_languages.py: default-run -> {ko,zh,yo} ----------
GNL = "/root/felix_hq/generate_new_languages.py"
old2 = '_RUN_CFG = {"codes": [c for (_, c, _) in LANGUAGES]}'
new2 = '_RUN_CFG = {"codes": [c for (_, c, _) in LANGUAGES if c in {"ko", "zh", "yo"}]}'
patch(GNL, "2) generate_new_languages default-talen", old2, new2, marker='if c in {"ko"')

# ---------- verificatie: welke 'new' codes overleven ----------
try:
    txt = open(GNL, encoding="utf-8").read()
    codes = re.findall(r'\(\s*"[^"]+"\s*,\s*"([a-z]{2,3})"\s*,\s*(?:True|False)\s*\)', txt)
    keep = [c for c in codes if c in {"ko", "zh", "yo"}]
    print(f"\n  generate_new_languages.py codes gevonden: {codes}")
    print(f"  -> na filter actief: {keep}")
except Exception as e:
    print("  verificatie faalde:", e)

print("\nKLAAR — plak alles terug.")

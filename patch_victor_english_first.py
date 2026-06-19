#!/usr/bin/env python3
"""patch_victor_english_first.py — Engels-first taalstrategie in generate_article.py.

Probleem: de taal-picker weegt talen met MINDER artikelen zwaarder, waardoor
Engels (de taal van ~alle merk/keyword-queries) op ~9% dekking blijft hangen
en pagina's in willekeurige talen ranken voor Engelse queries (0 klikken).

Fix: in de else-tak van de taalkeuze wordt nu ~80% van de tijd Engels gekozen
(FORCE_LANG en BRAND_LANG_LOCK blijven leidend). Tunebaar via EN_BIAS.

Idempotent (marker), backup + py_compile. Draai met venv:
  /root/felix_hq/venv/bin/python3 /tmp/patch_victor_english_first.py
"""
import shutil
import datetime
import py_compile

AG = "/root/felix_hq/generate_article.py"
MARK = "ENGELS-FIRST v1"

TARGET = (
    "        else:\n"
    "            lang = random.choice(weighted_languages)\n"
)
REPL = (
    "        else:\n"
    f"            # ── {MARK} (SEO: Engelse dekking was ~9%; Engels = klik-taal) ──\n"
    "            EN_BIAS = 0.8\n"
    '            _en = next((n for n, c in LANG_CODES.items() if c == "en"), None)\n'
    "            if _en and random.random() < EN_BIAS:\n"
    "                lang = _en\n"
    "            else:\n"
    "                lang = random.choice(weighted_languages)\n"
)

src = open(AG, encoding="utf-8").read()
if MARK in src:
    print("✓ Engels-first patch staat er al — skip")
elif TARGET not in src:
    print("✗ Doel-blok niet gevonden (generate_article.py gewijzigd?). ABORT — niets aangepast.")
    print("  Verwacht:\n" + TARGET)
else:
    b = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(AG, b)
    open(AG, "w", encoding="utf-8").write(src.replace(TARGET, REPL, 1))
    try:
        py_compile.compile(AG, doraise=True)
        print(f"✓ Engels-first patch toegepast (backup: {b})")
        print("  → nieuwe artikelen zijn nu ~80% Engels; multilingual blijft 20%.")
    except py_compile.PyCompileError as e:
        shutil.copy2(b, AG)
        print("✗ syntaxfout — backup teruggezet:", e)

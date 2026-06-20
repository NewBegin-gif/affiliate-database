#!/usr/bin/env python3
"""patch_victor_money_links2.py — voeg de 6 nieuwe hero-reviews toe aan de
money-link-sturing (_MONEY) in generate_article.py, zodat Victors artikelen er
intern naartoe linken. Idempotent, backup + py_compile.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pm2.py
"""
import re, shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"
HEROES = ["1password-review", "payoneer-review", "nordvpn-review",
          "apollo-review", "streak-review", "aweber-review"]

src = open(AG, encoding="utf-8").read()

m = re.search(r"_MONEY\s*=\s*\[(.*?)\]", src, re.S)
if not m:
    print("✗ _MONEY-lijst niet gevonden — is de money-link-patch (v1) al gedraaid?")
    raise SystemExit(1)

body = m.group(1)
have = set(re.findall(r"['\"]([^'\"]+)['\"]", body))
missing = [h for h in HEROES if h not in have]
if not missing:
    print("✓ alle 6 hero's staan al in _MONEY — niets te doen")
    raise SystemExit(0)

add = ", " + ", ".join(f"'{h}'" for h in missing)
new_block = "_MONEY = [" + body.rstrip() + (body.rstrip().endswith(",") and " " or "") + add + "]"
new_src = src[:m.start()] + new_block + src[m.end():]

bak = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
shutil.copy2(AG, bak)
open(AG, "w", encoding="utf-8").write(new_src)
try:
    py_compile.compile(AG, doraise=True)
    print(f"✓ toegevoegd aan _MONEY: {missing}")
    print(f"  backup: {bak}")
    # verificatie
    chk = re.search(r"_MONEY\s*=\s*\[(.*?)\]", open(AG, encoding='utf-8').read(), re.S).group(1)
    allk = re.findall(r"['\"]([^'\"]+)['\"]", chk)
    print(f"  _MONEY bevat nu {len(allk)} pagina's, incl. alle hero's: {all(h in allk for h in HEROES)}")
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG)
    print("✗ syntaxfout — backup teruggezet:", e)

#!/usr/bin/env python3
"""Fix de kapotte E-E-A-T-scorer (puur cosmetisch — alleen rapportage, geen
content-herschrijving). De scorer telt ENGELSE zinsdelen ('i tested', 'according
to', ...), maar draait over alle 35 talen → niet-Engelse pagina's scoren ~0 →
kunstmatig gemiddelde van ~7/100 en vals 'X artikelen onder 40'-alarm.

Fix: score alleen Engelse pagina's (geen taalsuffix, of '-en'). Veilig:
compile-check vóór overschrijven + backup. Vereist victor-herstart.
"""
import os
import shutil
import sys
import time
import py_compile

F = "/root/felix_hq/felix_ceo_agent.py"
s = open(F, encoding="utf-8").read()

OLD = '''    files = [f"{slug}.html"] if slug else [f for f in os.listdir(articles_dir) if f.endswith('.html')]'''
NEW = (
    '    if slug:\n'
    '        files = [f"{slug}.html"]\n'
    '    else:\n'
    '        _lang = re.compile(r"-[a-z]{2}$")  # scorer is Engels-only -> vertalingen overslaan\n'
    '        files = [f for f in os.listdir(articles_dir) if f.endswith(".html")\n'
    '                 and (not _lang.search(f[:-5]) or f[:-5].endswith("-en"))]'
)

if "_lang = re.compile" in s and "Engels-only" in s:
    sys.exit("ℹ️ Al gepatcht — niets te doen.")
if OLD not in s:
    sys.exit("❌ score_eeat 'files='-regel niet gevonden (andere quotes/al gewijzigd?).")

s = s.replace(OLD, NEW, 1)

tmp = F + ".new"
open(tmp, "w", encoding="utf-8").write(s)
try:
    py_compile.compile(tmp, doraise=True)
except py_compile.PyCompileError as e:
    os.remove(tmp)
    sys.exit("❌ Gepatchte versie compileert niet — origineel ongewijzigd:\n" + str(e))

bak = F + ".bak." + str(int(time.time()))
shutil.copy(F, bak)
os.replace(tmp, F)
print("✓ E-E-A-T-scorer is nu Engels-only (geen vals 7/100-alarm meer)")
print(f"✓ backup: {bak}")
print("→ Herstart: systemctl restart victor.service")

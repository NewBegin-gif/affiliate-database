#!/usr/bin/env python3
"""Fix de duplicate-digest-spam in felix_ceo_agent.py (Victor).

Oorzaak: ~17 dagelijkse cycli delen één variabele `last_auto_improve` als
dedup-guard. Bij overlappende uur-vensters overschrijven ze elkaars token
(ping-pong) en sommige blokken zetten de guard nooit → cycli (en hun Telegram-
rapporten + LLM/git-werk) vuren elke 5 min opnieuw i.p.v. 1×/dag.

Fix: vervang de gedeelde string door een per-token `done_today`-set + een
`_once(token)`-helper die atomair checkt-en-markeert. Elk blok guardt nu zichzelf.

Veilig: schrijft alleen weg als de gepatchte versie compileert; maakt backup.
Idempotent: stopt als er al een done_today/_once aanwezig is.
"""
import os
import re
import shutil
import sys
import time
import py_compile

F = "/root/felix_hq/felix_ceo_agent.py"
s = open(F, encoding="utf-8").read()

if "def _once(" in s or "done_today = set()" in s:
    sys.exit("ℹ️ Al gepatcht (done_today/_once aanwezig) — niets te doen.")

n_before = s.count("last_auto_improve")
if n_before == 0:
    sys.exit("❌ Geen last_auto_improve gevonden — verkeerd bestand?")

# token = str(now.date())  optioneel gevolgd door  + "..."  of  + f"..."
TOK = r'(str\(now\.date\(\)\)(?:\s*\+\s*f?"[^"]*")?)'

# 1) init-regel vervangen door done_today + _once-helper (zelfde 4-spatie-indent)
init_old = "    last_auto_improve = None\n"
if init_old not in s:
    sys.exit("❌ Init-regel `    last_auto_improve = None` niet gevonden — afgebroken.")
init_new = (
    "    done_today = set()\n"
    "    def _once(_tok):\n"
    "        if _tok in done_today:\n"
    "            return False\n"
    "        done_today.add(_tok)\n"
    "        return True\n"
)
s = s.replace(init_old, init_new, 1)

# 2) checks:  last_auto_improve != TOKEN   ->   _once(TOKEN)
s, n_chk = re.subn(r'last_auto_improve\s*!=\s*' + TOK, r'_once(\1)', s)

# 3) sets:    last_auto_improve = TOKEN    ->   done_today.add(TOKEN)
s, n_set = re.subn(r'last_auto_improve\s*=\s*' + TOK, r'done_today.add(\1)', s)

leftover = [ln.strip() for ln in s.splitlines() if "last_auto_improve" in ln]
if leftover:
    sys.exit("❌ Onverwachte resterende last_auto_improve-referenties:\n  " + "\n  ".join(leftover))

# 4) compileer de nieuwe versie VOOR we het origineel overschrijven
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
print(f"✓ Gepatcht: {n_chk} checks → _once(), {n_set} sets → done_today.add()")
print(f"✓ Backup: {bak}")
print("→ Herstart nu: systemctl restart victor.service")

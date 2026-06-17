#!/usr/bin/env python3
"""#2 — Bundel de routine cyclus-rapporten in één dagelijks 'VICTOR DAGOVERZICHT'.

De 10 informatieve "— Dagelijks"-rapporten (neural/hive/skynet/quantum/omega/
growth/competitor/autopilot/titan/domination) worden niet meer los gestuurd maar
verzameld in een dag-buffer en 1× om 14:00 UTC gebundeld verstuurd (in stukken
i.v.m. Telegrams 4096-limiet). Alerts (heal/alert), de Goedemorgen-briefing en de
wekelijkse rapporten blijven real-time.

Vereist dat patch_victor_guards.py al gedraaid heeft (done_today/_once). Veilig:
compile-check vóór overschrijven + backup. Idempotent.
"""
import os
import shutil
import sys
import time
import py_compile

F = "/root/felix_hq/felix_ceo_agent.py"
s = open(F, encoding="utf-8").read()

if "done_today = set()" not in s or "_once" not in s:
    sys.exit("❌ Draai EERST patch_victor_guards.py (done_today/_once ontbreekt). "
             "Anders bundel je de duplicaten i.p.v. ze te voorkomen.")
if "_queue_report" in s or "VICTOR DAGOVERZICHT" in s:
    sys.exit("ℹ️ Al gepatcht (dagoverzicht aanwezig) — niets te doen.")

# 1) dag-buffer + helper, direct na `    done_today = set()`
anchor = "    done_today = set()\n"
inject = anchor + "    day_reports = []\n    def _queue_report(_r):\n        day_reports.append(_r)\n"
s = s.replace(anchor, inject, 1)

# 2) de 10 cyclus-sends omleiden naar de buffer
n = 0
for var in ["comp_report", "growth_report", "ap_report", "neural_report", "hive_report",
            "skynet_report", "quantum_report", "omega_report", "titan_report", "dom_report"]:
    a = f"bot.send_message(ADMIN_ID, {var})"
    n += s.count(a)
    s = s.replace(a, f"_queue_report({var})")
if n == 0:
    sys.exit("❌ Geen cyclus-sends gevonden om te bundelen — afgebroken.")

# 3) eind-van-dag-overzicht vóór `            time.sleep(300)`
sleep_anchor = "            time.sleep(300)\n"
if sleep_anchor not in s:
    sys.exit("❌ time.sleep(300)-anchor niet gevonden — afgebroken (indentatie?).")
block = (
    '            # DAGOVERZICHT: gebundelde cyclus-rapporten, 1x om 14:00 UTC\n'
    '            if hour == 14 and _once(str(now.date()) + "-dayoverview"):\n'
    '                if day_reports:\n'
    '                    try:\n'
    '                        _cnt = len(day_reports)\n'
    '                        _full = ("\\U0001F4CB VICTOR DAGOVERZICHT \\u2014 " + now.strftime("%d %b %Y")\n'
    '                                 + "\\n" + ("=" * 22) + "\\n\\n" + "\\n\\n".join(day_reports))\n'
    '                        for _i in range(0, len(_full), 3800):\n'
    '                            bot.send_message(ADMIN_ID, _full[_i:_i + 3800])\n'
    '                        day_reports.clear()\n'
    '                        log("Dagoverzicht verstuurd (%d rapporten)" % _cnt)\n'
    '                    except Exception as _e:\n'
    '                        log("Dagoverzicht error: %s" % _e)\n'
)
s = s.replace(sleep_anchor, block + sleep_anchor, 1)

# compile-check vóór schrijven
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
print(f"✓ {n} cyclus-rapporten gebundeld in dagoverzicht (14:00 UTC)")
print(f"✓ backup: {bak}")
print("→ Herstart: systemctl restart victor.service")

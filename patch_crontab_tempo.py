#!/usr/bin/env python3
"""patch_crontab_tempo.py — verlaag de generatie-frequentie in root's crontab.

Wijzigt ALLEEN het schema (eerste 5 velden) van 3 regels, op naam herkend:
  generate_article.py        0 */3  -> 0 */12   (8x/dag -> 2x/dag)
  generate_new_languages.sh  0 */6  -> 0 8      (4x/dag -> 1x/dag, 08:00)
  harvest_topics.py          0 4 *  -> 0 4 * * 1 (dagelijks -> wekelijks ma)

Veiligheid: dry-run by default (toont before/after); pas met --apply installeren.
Backup van de huidige crontab + validatie (zelfde regelaantal, niet leeg) vóór
installatie. Idempotent (al-gewijzigde regels worden overgeslagen).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/cron.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/cron.py --apply    # installeren
"""
import subprocess, sys, datetime

APPLY = "--apply" in sys.argv

# (substring in commando, nieuw 5-velden-schema)
RULES = [
    ("python3 generate_article.py", "0 */12 * * *"),
    ("generate_new_languages.sh",   "0 8 * * *"),
    ("harvest_topics.py",           "0 4 * * 1"),
]

r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
if r.returncode != 0 or not r.stdout.strip():
    print("✗ kon crontab niet lezen of crontab is leeg — ABORT (niets gewijzigd).")
    print("  stderr:", r.stderr.strip()); sys.exit(1)
cur = r.stdout
lines = cur.split("\n")

changes = []
new_lines = []
for line in lines:
    s = line.strip()
    if not s or s.startswith("#"):
        new_lines.append(line); continue
    matched = False
    for marker, sched in RULES:
        if marker in line:
            fields = line.split(None, 5)
            if len(fields) < 6:
                break
            old_sched = " ".join(fields[:5])
            cmd = fields[5]
            if old_sched == sched:
                print(f"= al ingesteld: {marker}")
            else:
                newline = f"{sched} {cmd}"
                changes.append((line, newline))
                new_lines.append(newline)
            matched = True
            break
    if not matched:
        new_lines.append(line)

if not changes:
    print("\nGeen wijzigingen nodig (alles al ingesteld of markers niet gevonden).")
    # toon welke markers gevonden zijn, ter controle
    for marker, _ in RULES:
        print(f"  marker '{marker}': {'gevonden' if marker in cur else 'NIET GEVONDEN'}")
    sys.exit(0)

print("=== voorgestelde wijzigingen ===")
for old, new in changes:
    print("  - " + old.strip())
    print("  + " + new.strip())

# validatie
new_cur = "\n".join(new_lines)
if new_cur.count("\n") != cur.count("\n"):
    print("\n✗ regelaantal veranderde — ABORT."); sys.exit(1)

if not APPLY:
    print("\nDRY-RUN — niets geïnstalleerd. Draai met --apply om te installeren.")
    sys.exit(0)

# backup + installeer
ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bak = f"/root/felix_hq/crontab.bak-{ts}"
open(bak, "w", encoding="utf-8").write(cur)
inst = subprocess.run(["crontab", "-"], input=new_cur, text=True, capture_output=True)
if inst.returncode != 0:
    print("✗ installatie faalde:", inst.stderr.strip())
    print("  herstel desnoods met: crontab", bak); sys.exit(1)
print(f"\n✓ crontab bijgewerkt ({len(changes)} regels). backup: {bak}")
print("  herstellen kan altijd met:  crontab " + bak)
print("KLAAR — plak alles terug.")

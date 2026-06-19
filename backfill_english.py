#!/usr/bin/env python3
"""backfill_english.py — genereer Engelse (-en) artikelen voor hoog-waarde merken
die te weinig Engelse dekking hebben. Gebruikt Victors eigen generator
(FORCE_BRAND + FORCE_LANG=en), dus zelfde kwaliteit/flow als de cron.

Let op: dit genereert ECHTE content via de LLM (kost een beetje + tijd, ~30-60s
per artikel) en commit/pusht elk artikel zoals de cron dat doet.

Draai met venv:
  /root/felix_hq/venv/bin/python3 /tmp/backfill_english.py            # dry-run (toont plan)
  /root/felix_hq/venv/bin/python3 /tmp/backfill_english.py --apply    # echt genereren
Tunen: --per N (Engelse artikelen per merk, default 3), --target T (min -en per merk, default 3)
"""
import os
import re
import sys
import subprocess

FELIX = "/root/felix_hq"
AG = os.path.join(FELIX, "generate_article.py")
PY = sys.executable
os.chdir(FELIX)
sys.path.insert(0, FELIX)
import generate_article as g  # voor VAULT + get_existing_folders

# Prioriteit op basis van GSC-impressies + affiliate-waarde (merknamen exact als VAULT-keys).
PRIORITY = [
    "SaneBox", "Tradify", "ChemiCloud", "Gamma", "Payoneer", "AliDrop", "Amplemarket",
    "Increff", "Unbounce", "CampaignMonitor", "Reclaim", "Trainual", "NordVPN",
    "SuccessCo", "Hostinger", "CloudTalk", "KrispCall", "Close", "GetResponse", "Proton",
]

PER = 3
TARGET = 3
APPLY = "--apply" in sys.argv
for i, a in enumerate(sys.argv):
    if a == "--per" and i + 1 < len(sys.argv):
        PER = int(sys.argv[i + 1])
    if a == "--target" and i + 1 < len(sys.argv):
        TARGET = int(sys.argv[i + 1])

vault = set(g.VAULT.keys())
folders = g.get_existing_folders()


def en_count(brand):
    bl = brand.lower()
    return sum(1 for f in folders if f.lower().startswith(bl) and f.endswith("-en"))


plan = []
for b in PRIORITY:
    if b not in vault:
        print(f"  ⚠ '{b}' niet in VAULT — overslaan (FORCE_BRAND werkt alleen voor VAULT-merken)")
        continue
    have = en_count(b)
    need = max(0, TARGET - have)
    runs = min(PER, need) if need else 0
    plan.append((b, have, runs))

print("\n=== BACKFILL-PLAN (Engelse artikelen) ===")
print(f"{'merk':<16}{'nu -en':>7}{'genereren':>11}")
for b, have, runs in plan:
    print(f"{b:<16}{have:>7}{runs:>11}")
total = sum(r for _, _, r in plan)
print(f"\nTotaal te genereren: {total} Engelse artikelen")

if not APPLY:
    print("\nDRY-RUN — niets gegenereerd. Draai met --apply om te starten.")
    sys.exit(0)

print("\n=== GENEREREN ===")
done = 0
for b, have, runs in plan:
    for k in range(runs):
        env = {**os.environ, "FORCE_BRAND": b, "FORCE_LANG": "en"}
        print(f"\n--- {b} (Engels) {k+1}/{runs} ---")
        r = subprocess.run([PY, AG], cwd=FELIX, env=env)
        done += 1 if r.returncode == 0 else 0
print(f"\n✅ KLAAR: {done}/{total} runs gelukt. Draai daarna build_hreflang.py --apply.")

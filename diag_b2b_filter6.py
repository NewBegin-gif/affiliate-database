#!/usr/bin/env python3
"""READ-ONLY diagnose stap 6: wie/wat update victor-staging + automerge-conflictresolutie.
Schrijft NIETS.
"""
import os, re, glob, subprocess

REPO = "/root/felix_hq/repos/aibuildermarketplace"


def hr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)
def sh(c):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=40).stdout.strip()
    except Exception as e: return f"(fout {e})"


hr("1. Wie commit op victor-staging? (laatste 15 commits)")
print(sh(f"git -C {REPO} log --oneline -15 origin/victor-staging 2>/dev/null"))

hr("2. Staat aspire-review op origin/victor-staging?")
print(sh(f"git -C {REPO} ls-tree -d --name-only origin/victor-staging b2b/ 2>/dev/null | grep -i aspire || echo GEEN"))

hr("3. Heeft origin/victor-staging een Aspire-knop in b2b/index.html?")
out = sh(f"git -C {REPO} show origin/victor-staging:b2b/index.html 2>/dev/null | grep -c \"filterTool(this,'Aspire')\"")
print("Aspire-knop count op staging:", out)

hr("4. Welke scripts pushen naar victor-staging?")
for base in ["/root/felix_hq"]:
    for f in glob.glob(base + "/**/*.py", recursive=True) + glob.glob(base + "/**/*.sh", recursive=True):
        try:
            s = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if "victor-staging" in s:
            hits = [ln.strip()[:140] for ln in s.split("\n") if "victor-staging" in ln]
            print(f"\n--- {f} ({len(hits)} regels) ---")
            for h in hits[:8]:
                print("   ", h)

hr("5. Volledige automerge-merge/conflict-resolutie (rest van het script)")
am = "/root/felix_hq/victor_automerge.sh"
if os.path.exists(am):
    txt = open(am, encoding="utf-8", errors="replace").read()
    # toon vanaf de merge-stap
    idx = txt.find("merge")
    print(txt[max(0, idx-200):idx+1800] if idx > 0 else txt[-2000:])

hr("KLAAR — plak alles terug")

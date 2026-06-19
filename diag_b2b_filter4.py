#!/usr/bin/env python3
"""READ-ONLY diagnose stap 4 (laatste): review_template.AFFILIATE-structuur,
automerge-gedrag en git-status van Victors repo. Schrijft NIETS.
"""
import os
import re
import glob
import subprocess


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"(fout: {e})"


# 1) review_template.py — AFFILIATE-dict structuur
hr("1. review_template.py AFFILIATE-structuur")
rt_candidates = glob.glob("/root/felix_hq/**/review_template.py", recursive=True)
rt = next((p for p in ["/root/felix_hq/review_template.py"] + rt_candidates if os.path.exists(p)), None)
print("pad:", rt)
if rt:
    s = open(rt, encoding="utf-8", errors="replace").read()
    ls = s.split("\n")
    # vind AFFILIATE = {
    for i, l in enumerate(ls):
        if re.match(r"\s*AFFILIATE\s*=\s*\{", l):
            print(f"AFFILIATE begint op regel {i+1}. Eerste ~3 entries (structuur):")
            depth = 0
            shown = 0
            for j in range(i, min(i + 50, len(ls))):
                print(f"  {j+1}: {ls[j]}")
                depth += ls[j].count("{") - ls[j].count("}")
                if "}" in ls[j] and j > i:
                    shown += 1
                if shown >= 3:
                    print("  ... (meer entries)")
                    break
            break
    print("\nAFFILIATE bevat 'aspire':", bool(re.search(r"aspire", s, re.I)))
    print("get_affiliate aanwezig:", "def get_affiliate" in s)
    # toon get_affiliate
    m = re.search(r"def get_affiliate.*?(?=\ndef |\Z)", s, re.S)
    if m:
        print("\n--- get_affiliate() ---")
        for ln in m.group(0).split("\n")[:25]:
            print("  " + ln)

# 2) automerge-script: behoudt het main-only mappen?
hr("2. victor_automerge script(s)")
for am in glob.glob("/root/felix_hq/**/victor_automerge*.sh", recursive=True):
    print(f"\n----- {am} -----")
    print(open(am, encoding="utf-8", errors="replace").read()[:2500])

# 3) git-status van Victors repo
hr("3. git-status Victor-repo (/root/felix_hq/repos/aibuildermarketplace)")
REPO = "/root/felix_hq/repos/aibuildermarketplace"
print("huidige branch:", sh(f"git -C {REPO} rev-parse --abbrev-ref HEAD"))
print("branches:", sh(f"git -C {REPO} branch -a"))
print("\naspire-review op main?:", sh(f"git -C {REPO} ls-tree -d --name-only origin/main b2b/ 2>/dev/null | grep -i aspire || echo GEEN"))
print("aspire-review op victor-staging?:", sh(f"git -C {REPO} ls-tree -d --name-only origin/victor-staging b2b/ 2>/dev/null | grep -i aspire || echo GEEN"))
print("\nlaatste 3 commits:", sh(f"git -C {REPO} log --oneline -3"))

# 4) hoe wordt rebuild_index normaal getriggerd (cron)?
hr("4. crontab (rebuild/generate triggers)")
print(sh("crontab -l 2>/dev/null | grep -iE 'generate_article|rebuild|victor' || echo '(geen match)'"))

hr("KLAAR — plak alles terug")

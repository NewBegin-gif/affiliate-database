#!/usr/bin/env python3
"""diag_sisternet.py — READ-ONLY. Spoor de oorzaak op van de afgekapte pagina's
(eindigen bij <!--sister-net-end--> zonder </footer></body></html>).

Toont:
  1) de volledige uurlijkse cron-regel(s) (promote / sister-net / aibm-promote);
  2) welke scripts 'sister-net' / footer-injectie doen;
  3) het relevante codeblok in die scripts (hoe footer/sluittags geschreven
     worden — daar zit de truncatie).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/ds.py
"""
import re, subprocess, glob, os

print("=" * 72); print("1) CRON-regels (promote / sister / aibm-promote)"); print("=" * 72)
out = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
for l in out.splitlines():
    if re.search(r"sister|promote|aibm-promote|VICTOR_WORKTREE", l, re.I):
        print("  " + l.strip())

print("\n" + "=" * 72); print("2) scripts met 'sister-net' / sister_net"); print("=" * 72)
cands = glob.glob("/root/felix_hq/*.py") + glob.glob("/root/felix_hq/*.sh")
hits = []
for f in cands:
    try:
        txt = open(f, encoding="utf-8", errors="ignore").read()
    except Exception:
        continue
    if "sister-net" in txt or "sister_net" in txt or "sister-net-end" in txt:
        hits.append(f)
        print(f"  {f}")

print("\n" + "=" * 72); print("3) footer/sluittag-logica in die scripts"); print("=" * 72)
pat = re.compile(r"sister.?net|</footer>|</body>|</html>|\.write|truncate|seek|\[:.*\]|sub\(|replace\(|footer", re.I)
for f in hits:
    print(f"\n--- {f} ---")
    lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(lines):
        if re.search(r"sister.?net|</footer>|</body>|</html>|footer_html|FOOTER|def .*footer|def .*sister", l, re.I):
            lo, hi = max(0, i - 1), min(len(lines), i + 2)
            for j in range(lo, hi):
                print(f"  L{j+1}: {lines[j].rstrip()[:150]}")
            print("  ...")
print("\nKLAAR — plak alles terug.")

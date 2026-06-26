#!/usr/bin/env python3
"""patch_disclosure_methodology.py — (1) corrigeer de valse Engelse disclosure-claim
"based on hands-on testing" → "Our reviews remain independent." en (2) voeg op ÉLKE
b2b-review een 'How we review →'-link toe aan de disclosure (E-E-A-T-signaal).
Patcht de template (review_template.py) zodat nieuwe pagina's het meteen krijgen
+ backfilt de bestaande pagina's. Alle talen voor de link; Engelse hands-on-claim
wordt gecorrigeerd.

DRY-RUN (default). --apply: schrijf + push main+staging.
Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/pdm.py
  /root/felix_hq/venv/bin/python3 /tmp/pdm.py --apply
"""
import sys, re, shutil, datetime, py_compile, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
HQ = "/root/felix_hq"
RT = HQ + "/review_template.py"
REPO = Path(HQ) / "repos" / "aibuildermarketplace"
B2B = REPO / "b2b"
LINK = '<a href="/how-we-review/" style="color:var(--accent)">How we review →</a>'

# ── 1) TEMPLATE ──
EN_OLD = "Our reviews remain independent and based on hands-on testing."
EN_NEW = "Our reviews remain independent."
REND_OLD = "  <strong>{L['disclosure_title']}.</strong> {L['disclosure']}\n</div>"
REND_NEW = "  <strong>{L['disclosure_title']}.</strong> {L['disclosure']} " + LINK + "\n</div>"

print("=" * 60)
print("1) TEMPLATE review_template.py" + ("  [APPLY]" if APPLY else "  [DRY-RUN]"))
print("=" * 60)
try:
    src = open(RT, encoding="utf-8").read()
    e1 = src.count(EN_OLD)
    e2 = src.count(REND_OLD)
    already = "/how-we-review/" in src
    print(f"  Engelse hands-on-claim gevonden: {e1}x")
    print(f"  disclosure-render-anchor gevonden: {e2}x  (al gepatcht: {already})")
    if APPLY and (e1 or (e2 and not already)):
        bak = f"{RT}.bak-{STAMP}"; shutil.copy2(RT, bak)
        new = src.replace(EN_OLD, EN_NEW)
        if not already:
            new = new.replace(REND_OLD, REND_NEW)
        open(RT, "w", encoding="utf-8").write(new)
        try:
            py_compile.compile(RT, doraise=True)
            print(f"  ✓ template gepatcht, backup {bak}")
        except py_compile.PyCompileError as ex:
            shutil.copy2(bak, RT); print(f"  ✗ syntaxfout — teruggezet: {ex}")
except FileNotFoundError:
    print("  ✗ review_template.py niet gevonden")

# ── 2) BACKFILL bestaande pagina's ──
print("\n" + "=" * 60)
print("2) BACKFILL b2b-pagina's" + ("  [APPLY]" if APPLY else "  [DRY-RUN]"))
print("=" * 60)
disc_re = re.compile(r'(<div class="disclosure"[^>]*>(?:(?!</div>).)*?)(</div>)', re.S)

def add_link(m):
    if "how-we-review" in m.group(1):
        return m.group(0)
    return m.group(1) + " " + LINK + m.group(2)

pages = list(B2B.glob("*/index.html")) + list(B2B.glob("*.html"))
linked = fixed_claim = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    o = t
    if EN_OLD in t:
        t = t.replace(EN_OLD, EN_NEW); fixed_claim += 1
    t2, n = disc_re.subn(add_link, t)
    if n and t2 != t:
        linked += 1
    t = t2
    if t != o and APPLY:
        f.write_text(t, encoding="utf-8")
print(f"  pagina's: {len(pages)} | how-we-review-link toegevoegd: {linked} | Engelse hands-on-claim gecorrigeerd: {fixed_claim}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "-A", "--", "b2b")
git("commit", "-m", "E-E-A-T + eerlijkheid: 'How we review'-link in disclosure op alle b2b-reviews + Engelse 'hands-on testing'-claim gecorrigeerd")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

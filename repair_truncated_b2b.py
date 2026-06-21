#!/usr/bin/env python3
"""repair_truncated_b2b.py — STAP 1: repareer de afgekapte b2b-pagina's
(zonder <footer én </body>).

Classificatie:
  Case A — bevat <!--sister-net-end--> : inhoud intact, alleen sluittags weg.
           Repair: nieuwsbrief-form invoegen (vóór sister-net) + </body></html>.
  Case B — geen sister-net-end : midden-in afgekapt, inhoud verloren.
           NIET aangeraakt; apart gelijst voor stap 2 (regenereren/noindex).

Veilig: dry-run by default (toont A/B-verdeling + lijsten); --apply repareert
Case A + commit + push (main+staging). Idempotent (marker aibm-nl-v1 / </body>).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/rep.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/rep.py --apply    # repareren + pushen
"""
import sys, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
SEND = "<!--sister-net-end-->"
SSTART = "<!--sister-net-start-->"

FORM = (
    '<!-- aibm-nl-v1 -->'
    '<section style="max-width:640px;margin:48px auto;padding:28px 24px;background:#0f172a;'
    'border:1px solid #1e293b;border-radius:16px;text-align:center;font-family:system-ui,-apple-system,sans-serif">'
    '<h3 style="color:#f1f5f9;font-size:1.25rem;font-weight:800;margin:0 0 8px">'
    'Get the best AI &amp; business software, monthly</h3>'
    '<p style="color:#94a3b8;font-size:.92rem;line-height:1.5;margin:0 auto 16px;max-width:480px">'
    'Honest reviews, real pricing and time-saving workflows — from an ex-banker who tests with his own money. No spam.</p>'
    '<form action="https://aibuildermarketplace.beehiiv.com/subscribe" method="get" target="_blank" '
    'style="display:flex;gap:8px;max-width:420px;margin:0 auto;flex-wrap:wrap;justify-content:center">'
    '<input type="email" name="email" required placeholder="Enter your email" '
    'style="flex:1 1 200px;min-width:180px;padding:11px 14px;border-radius:9px;border:1px solid #334155;'
    'background:rgba(255,255,255,.06);color:#f1f5f9;font-size:.92rem">'
    '<button type="submit" style="padding:11px 22px;border-radius:9px;border:0;background:#3b82f6;'
    'color:#fff;font-weight:700;font-size:.92rem;cursor:pointer;white-space:nowrap">Subscribe &rarr;</button>'
    '</form></section>'
)

caseA, caseB = [], []
for f in sorted(B2B.glob("*/index.html")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "<footer" in t or "</body>" in t:
        continue  # alleen de kapotte
    (caseA if SEND in t else caseB).append(f)

print(f"afgekapte pagina's: {len(caseA) + len(caseB)}")
print(f"  Case A (inhoud intact, repareerbaar): {len(caseA)}")
print(f"  Case B (midden-in afgekapt, regen/noindex): {len(caseB)}")
print("\n=== Case B (handmatig beslissen in stap 2) ===")
for f in caseB:
    print("  " + f.parent.name)

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply om Case A te repareren.")
    sys.exit(0)

fixed = 0
for f in caseA:
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "aibm-nl-v1" not in t and "beehiiv.com/subscribe" not in t:
        if SSTART in t:
            t = t.replace(SSTART, FORM + "\n" + SSTART, 1)
        else:
            t = t.rstrip() + "\n" + FORM
    t = t.rstrip() + "\n</body>\n</html>\n"
    f.write_text(t, encoding="utf-8")
    fixed += 1
print(f"\n✓ Case A gerepareerd: {fixed} pagina's (form + sluittags)")

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)

git("add", "--", "b2b")
git("commit", "-m", f"Repair: {fixed} afgekapte b2b-pagina's netjes afgesloten + nieuwsbrief-form")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main")
print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging")
print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

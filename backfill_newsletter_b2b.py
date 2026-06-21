#!/usr/bin/env python3
"""backfill_newsletter_b2b.py — voeg de native Beehiiv nieuwsbrief-opt-in toe aan
ALLE bestaande /b2b/-artikelen die er nog geen hebben. Elke pagina = een opt-in-
punt (compounding e-mailwaarde, ook bij weinig verkeer).

Veilig: dry-run by default (telt), --apply schrijft + commit + push (main+staging).
Skip: pagina's met al een Beehiiv-form, met de marker, of met noindex (dood).
Insertie vlak vóór <footer (anders vóór </body>). Zelf-stylende donkere box.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/nl.py            # dry-run (telt)
  /root/felix_hq/venv/bin/python3 /tmp/nl.py --apply    # schrijven + pushen
"""
import sys, subprocess, datetime
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"

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

pages = sorted(B2B.glob("*/index.html"))
changed, skipped_form, skipped_noindex, skipped_marker, no_anchor = 0, 0, 0, 0, 0
touched = []
for f in pages:
    html = f.read_text(encoding="utf-8", errors="ignore")
    if "aibm-nl-v1" in html:
        skipped_marker += 1; continue
    if "beehiiv.com/subscribe" in html:
        skipped_form += 1; continue
    if "noindex" in html.lower():
        skipped_noindex += 1; continue
    if "<footer" in html:
        new = html.replace("<footer", FORM + "\n<footer", 1)
    elif "</body>" in html:
        new = html.replace("</body>", FORM + "\n</body>", 1)
    else:
        no_anchor += 1; continue
    if APPLY:
        f.write_text(new, encoding="utf-8")
    changed += 1
    touched.append(f)

print(f"b2b-artikelen gescand : {len(pages)}")
print(f"  krijgen form        : {changed}")
print(f"  al een form          : {skipped_form}")
print(f"  al marker (gedaan)   : {skipped_marker}")
print(f"  noindex (dood, skip) : {skipped_noindex}")
print(f"  geen anchor          : {no_anchor}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply om te schrijven + pushen.")
    sys.exit(0)
if not changed:
    print("\nNiets gewijzigd."); sys.exit(0)

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)

git("add", "--", "b2b")
git("commit", "-m", f"Newsletter: native Beehiiv opt-in op {changed} b2b-artikelen (e-mail-capture)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main")
print("\npush main    :", (p1.stdout + p1.stderr).strip()[-160:])
p2 = git("push", "origin", "HEAD:victor-staging")
print("push staging :", (p2.stdout + p2.stderr).strip()[-160:])
print(f"\n✓ {changed} artikelen voorzien van nieuwsbrief-opt-in.")
print("KLAAR — plak alles terug.")

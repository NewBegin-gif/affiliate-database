#!/usr/bin/env python3
"""repair_caseb_b2b.py — STAP 1b: repareer de Case B-pagina's (midden-in afgekapt,
maar afgekapt in de trailing 'related tools'-widget — artikel intact).

Aanpak per pagina: knip terug tot de laatste SCHONE sluittag (</article> of
</section>), zodat de kapotte half-open widget weg is; voeg dan de nieuwsbrief-form
+ </body></html> toe. (Naïef </body> aanplakken zou de form in een open <img-tag
laten verdwijnen.)

Veiligheid: dry-run by default toont per pagina welke tag + hoeveel bytes worden
weggeknipt (klein = alleen de widget; groot = waarschuwing). Pagina's zonder
</article>/</section> worden OVERGESLAGEN (apart gelijst voor regen/noindex).
--apply schrijft + commit + push (main+staging).

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/rcb.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/rcb.py --apply    # repareren + pushen
"""
import sys, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
SEND = "<!--sister-net-end-->"

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

caseB = []
for f in sorted(B2B.glob("*/index.html")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    if "<footer" in t or "</body>" in t or SEND in t:
        continue
    caseB.append((f, t))

print(f"Case B pagina's: {len(caseB)}\n")
print(f"{'pagina':46} {'tag':11} {'wegknip':>8} {'%':>5}")
skipped = []
plan = []
for f, t in caseB:
    cut = -1; tag = None
    for cand in ("</article>", "</section>"):
        i = t.rfind(cand)
        if i > cut:
            cut, tag = i + len(cand), cand
    if cut == -1:
        skipped.append(f.parent.name); continue
    removed = len(t) - cut
    pct = 100 * removed / len(t)
    plan.append((f, t, cut))
    flag = "  ⚠️GROOT" if pct > 25 else ""
    print(f"{f.parent.name:46} {tag:11} {removed:8d} {pct:4.0f}%{flag}")

if skipped:
    print("\nGEEN </article>/</section> — overgeslagen (regen/noindex):")
    for s in skipped:
        print("  " + s)

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Controleer dat 'wegknip' klein is (alleen de widget).")
    print("Draai met --apply om te repareren.")
    sys.exit(0)

fixed = 0
for f, t, cut in plan:
    new = t[:cut].rstrip() + "\n" + FORM + "\n</body>\n</html>\n"
    f.write_text(new, encoding="utf-8")
    fixed += 1
print(f"\n✓ Case B gerepareerd: {fixed} pagina's (widget weg, form + sluittags)")

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)

git("add", "--", "b2b")
git("commit", "-m", f"Repair Case B: {fixed} afgekapte pagina's (kapotte widget weg) + nieuwsbrief-form")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main")
print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging")
print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

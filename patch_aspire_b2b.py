#!/usr/bin/env python3
"""patch_aspire_b2b.py — Aspire in de b2b-filter (TOOL:-lijst) + nette kaart.

Wat het doet (idempotent, met backup + syntax-check):
  1. Voegt "Aspire" toe aan review_template.AFFILIATE  -> nette kaart
     (tagline/rating/mint-logo) en betrouwbare brand-herkenning.
  2. Zet de bestaande aspire-review hero-map in Victors WERKKOPIE
     (staat al op origin/main; alleen de stale werkkopie mist 'm).
  3. Draait rebuild_index op de juiste werkkopie -> Aspire-knop + kaart,
     en /b2b/?tool=Aspire gaat werken. Daarna commit + pull + push,
     met een 2e rebuild NA de pull zodat de '-X theirs'-pull onze
     Aspire-index niet wegmerget.

Article-generatie raakt dit NIET (die gebruikt VAULT, niet AFFILIATE), dus
Victor gaat hierdoor GEEN Aspire-artikelen schrijven.

Draai op de VPS met de venv-python (voor stap 3 import):
  /root/felix_hq/venv/bin/python3 /tmp/patch_aspire_b2b.py
"""
import os
import re
import sys
import shutil
import subprocess
import datetime

RT = "/root/felix_hq/review_template.py"
FELIX = "/root/felix_hq"
REPO = "/root/felix_hq/repos/aibuildermarketplace"
B2B = os.path.join(REPO, "b2b")
HERO = os.path.join(B2B, "aspire-review")


def backup(p):
    b = f"{p}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(p, b)
    print("  backup:", b)


def git(*args, check=False):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  git", args[0], "->", out[:300])
    if check and r.returncode != 0:
        raise SystemExit(f"git {args} faalde")
    return r


# ── 1) Aspire toevoegen aan review_template.AFFILIATE ─────────────────────
print("\n[1] review_template.AFFILIATE")
src = open(RT, encoding="utf-8").read()
if re.search(r'["\']Aspire["\']\s*:\s*\{', src):
    print("  ✓ Aspire staat er al in — skip")
else:
    logo = (
        '<svg viewBox="0 0 24 24" width="1em" height="1em" '
        'xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
        '<rect width="24" height="24" rx="6" fill="#2E332F"/>'
        '<text x="12" y="17" font-size="13" font-family="Inter,Arial,sans-serif" '
        'font-weight="700" fill="#BEFFCF" text-anchor="middle">A</text></svg>'
    )
    entry = (
        '    "Aspire": {\n'
        '        "url": "https://aspire.link/sg/referwithAIBuilder",\n'
        '        "rating": "4.5",\n'
        '        "reviews": "",\n'
        '        "price": "",\n'
        '        "badge": "No minimum balance",\n'
        '        "tagline": "All-in-one finance stack: multi-currency accounts, '
        'cashback cards & AI expense automation",\n'
        '        "icon": "\U0001F4B3",\n'
        f'        "logo": {logo!r},\n'
        '        "color": "#2E332F",\n'
        '        "category": "Business Finance",\n'
        '    },\n'
    )
    new = src.replace("AFFILIATE = {\n", "AFFILIATE = {\n" + entry, 1)
    if new == src:
        print("  ✗ kon 'AFFILIATE = {' niet vinden — review_template ONGEWIJZIGD")
    else:
        backup(RT)
        open(RT, "w", encoding="utf-8").write(new)
        import py_compile
        try:
            py_compile.compile(RT, doraise=True)
            print("  ✓ Aspire toegevoegd + syntax OK")
        except py_compile.PyCompileError as e:
            print("  ✗ syntaxfout — terugzetten backup!", e)
            raise SystemExit(1)

# ── 2) aspire-review map in de werkkopie zetten ───────────────────────────
print("\n[2] aspire-review map in werkkopie")
if os.path.isdir(HERO) and os.path.exists(os.path.join(HERO, "index.html")):
    print("  ✓ al aanwezig in werkkopie")
else:
    git("fetch", "origin", "main")
    git("checkout", "origin/main", "--", "b2b/aspire-review")
    if os.path.exists(os.path.join(HERO, "index.html")):
        print("  ✓ uit origin/main in werkkopie gezet")
    else:
        print("  ✗ niet gevonden op origin/main — staat de hero daar wel? ABORT")
        raise SystemExit(1)

# ── 3) rebuild_index draaien (import is veilig: main() is guarded) ─────────
print("\n[3] rebuild_index")
os.chdir(FELIX)
sys.path.insert(0, FELIX)
try:
    import generate_article as g
except Exception as e:
    print("  ✗ kon generate_article niet importeren:", e)
    print("  Stap 1+2 zijn wel gedaan. Draai handmatig:")
    print("    cd /root/felix_hq && venv/bin/python3 generate_article.py")
    raise SystemExit(0)

folders = g.get_existing_folders()
g.rebuild_index(folders)
try:
    g.build_sitemap(folders)
except Exception as e:
    print("  (sitemap skip:", e, ")")
idx_path = os.path.join(B2B, "index.html")
has_btn = "filterTool(this,'Aspire')" in open(idx_path, encoding="utf-8").read()
print(f"  ✓ index herbouwd ({len(folders)} folders). Aspire-knop aanwezig: {has_btn}")

# ── 4) commit + pull (-X theirs) + 2e rebuild + push ──────────────────────
print("\n[4] commit + push (mirror Victor-flow, met rebuild NA de pull)")
git("add", ".")
git("commit", "-m", "Add Aspire to b2b filter (hero folder + AFFILIATE) [manual patch]")
git("pull", "--no-rebase", "-X", "theirs", "origin", "main")
# de -X theirs pull kan onze index met origin's versie hebben overschreven:
# herbouw NA de pull zodat Aspire er gegarandeerd in staat.
folders = g.get_existing_folders()
g.rebuild_index(folders)
try:
    g.build_sitemap(folders)
except Exception:
    pass
has_btn2 = "filterTool(this,'Aspire')" in open(idx_path, encoding="utf-8").read()
print("  Aspire-knop na 2e rebuild:", has_btn2)
git("add", ".")
git("commit", "-m", "Rebuild b2b index after pull — keep Aspire button")
git("push", "origin", "main")

print("\n✅ KLAAR. Check live (na ~1-2 min) op /b2b/ — de filter moet nu 'Aspire' bevatten,")
print("   en https://aibuildermarketplace.com/b2b/?tool=Aspire moet de Aspire-kaart tonen.")

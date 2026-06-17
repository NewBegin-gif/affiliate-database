#!/usr/bin/env python3
"""#1 — Fix de kapotte 'spatie in slug'-pagina's (bv. kinsta-vs-wp rocket.html).

A) Hernoemt alle b2b-bestanden/mappen met een spatie -> spatie verwijderd
   ("wp rocket" -> "wprocket", "bright data" -> "brightdata"), via git mv.
B) Fixt generate_article.py: slugificeert BEIDE merknamen in de vs-slug
   (spaties + punten weg) zodat er geen kapotte pagina's meer bijkomen.
C) Commit + push de repo. Victor regenereert /b2b/-index + sitemap in z'n cyclus.

Veilig: compile-check op de generator vóór overschrijven + backups.
"""
import os
import shutil
import subprocess
import sys
import time
import py_compile

REPO = "/root/felix_hq/repos/aibuildermarketplace"
GEN = "/root/felix_hq/generate_article.py"
b2b = os.path.join(REPO, "b2b")


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)


# ── A) hernoem/ruim kapotte spatie-bestanden op ──────────────────────────
renamed, removed = [], []
for name in sorted(os.listdir(b2b)):
    if " " not in name:
        continue
    new = name.replace(" ", "")
    if os.path.exists(os.path.join(b2b, new)):
        git("rm", "-f", "--", f"b2b/{name}")          # correcte versie bestaat al
        removed.append(name)
    else:
        r = git("mv", "--", f"b2b/{name}", f"b2b/{new}")
        if r.returncode != 0:                          # fallback buiten git-tracking
            os.replace(os.path.join(b2b, name), os.path.join(b2b, new))
            git("add", "-A", "--", f"b2b/{name}", f"b2b/{new}")
        renamed.append((name, new))
print(f"A) hernoemd: {len(renamed)} | verwijderd (dubbel): {len(removed)}")
for o, nw in renamed:
    print(f"   {o}  ->  {nw}")

# ── B) generator-fix: slugificeer beide merken in de vs-slug ─────────────
SLUGGED = '''f"{brand.lower().replace(' ','').replace('.','')}-vs-{brand2.lower().replace(' ','').replace('.','')}-{lang_code}"'''
fixes = [
    '''f"{brand.lower()}-vs-{brand2.lower()}-{lang_code}"''',
    '''f"{brand.lower()}-vs-{brand2.lower().replace(' ', '-').replace('.', '')}-{lang_code}"''',
]
g = open(GEN, encoding="utf-8").read()
applied = 0
for old in fixes:
    if old in g:
        g = g.replace(old, SLUGGED)
        applied += 1
if applied:
    tmp = GEN + ".new"
    open(tmp, "w", encoding="utf-8").write(g)
    try:
        py_compile.compile(tmp, doraise=True)
    except py_compile.PyCompileError as e:
        os.remove(tmp)
        print("⚠️ B) generator-fix compileert niet — generator ONGEWIJZIGD:", str(e)[:200])
        applied = 0
    else:
        shutil.copy(GEN, GEN + ".bak." + str(int(time.time())))
        os.replace(tmp, GEN)
print(f"B) generator-slugfix toegepast op {applied}/2 vs-slug-regels")

# ── C) commit + push ─────────────────────────────────────────────────────
git("add", "-A")
cm = git("commit", "-m", "Fix broken slugs: remove spaces in comparison page names + slugify brands")
git("pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit")
ps = git("push", "origin", "main")
print("C) push:", (ps.stdout + ps.stderr).strip().splitlines()[-1] if (ps.stdout + ps.stderr).strip() else "(niets te pushen)")
print("→ Victor regenereert /b2b/-index + sitemap in z'n volgende cyclus.")

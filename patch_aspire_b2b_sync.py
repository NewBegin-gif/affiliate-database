#!/usr/bin/env python3
"""patch_aspire_b2b_sync.py — forceer origin/main's b2b-index naar de
Aspire-versie (deterministische rebuild), zodat de '-X theirs'-deadlock
doorbroken wordt en Aspire BLIJFT staan in de b2b-filter.

Veilig: GEEN force-push. Gebruikt '-X ours' op de pull zodat onze verse
rebuild wint, daarna push naar main; staging alleen als het fast-forward kan.
Idempotent. Draai met de venv-python:
  /root/felix_hq/venv/bin/python3 /tmp/patch_aspire_b2b_sync.py
"""
import os
import sys
import subprocess

FELIX = "/root/felix_hq"
REPO = "/root/felix_hq/repos/aibuildermarketplace"
IDX = os.path.join(REPO, "b2b", "index.html")
HERO = os.path.join(REPO, "b2b", "aspire-review", "index.html")


def git(*a, check=False):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print("  git", a[0], "->", out[:260])
    if check and r.returncode != 0:
        raise SystemExit(f"git {a} faalde")
    return r


def has_aspire():
    try:
        return "filterTool(this,'Aspire')" in open(IDX, encoding="utf-8").read()
    except Exception:
        return False


os.chdir(FELIX)
sys.path.insert(0, FELIX)
import generate_article as g  # main() is guarded -> veilig

print("[0] zorg dat de hero-map in de werkkopie staat")
if not os.path.exists(HERO):
    git("fetch", "origin", "main")
    git("checkout", "origin/main", "--", "b2b/aspire-review")
print("   hero aanwezig:", os.path.exists(HERO))

print("\n[1] verse deterministische rebuild")
folders = g.get_existing_folders()
g.rebuild_index(folders)
try:
    g.build_sitemap(folders)
except Exception as e:
    print("   (sitemap skip:", e, ")")
print("   Aspire-knop in rebuild:", has_aspire())

print("\n[2] commit + pull (-X OURS: onze Aspire-index wint) + rebuild + push main")
git("add", "-A")
git("commit", "-m", "Sync b2b index with Aspire button (break -X theirs deadlock)")
git("fetch", "origin")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
# folders kunnen door de pull veranderd zijn -> herbouw, zodat de index klopt
folders = g.get_existing_folders()
g.rebuild_index(folders)
try:
    g.build_sitemap(folders)
except Exception:
    pass
print("   Aspire-knop na pull+rebuild:", has_aspire())
git("add", "-A")
git("commit", "-m", "Rebuild b2b index after pull — keep Aspire")
pr = git("push", "origin", "HEAD:main")
print("   push main exit:", pr.returncode)

print("\n[3] staging gelijktrekken (alleen als fast-forward; geen force)")
sp = git("push", "origin", "HEAD:victor-staging")
if sp.returncode != 0:
    print("   staging niet fast-forward — dat is OK; main is leidend voor live.")

print("\n[4] verificatie tegen origin")
git("fetch", "origin")
m = git("show", "origin/main:b2b/index.html")
s = git("show", "origin/victor-staging:b2b/index.html")
print("   Aspire-knop op origin/main:   ", "filterTool(this,'Aspire')" in m.stdout)
print("   Aspire-knop op origin/staging:", "filterTool(this,'Aspire')" in s.stdout)
print("\n✅ KLAAR. Check live (~1-2 min): https://aibuildermarketplace.com/b2b/?tool=Aspire")

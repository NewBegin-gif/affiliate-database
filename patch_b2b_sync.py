#!/usr/bin/env python3
"""patch_b2b_sync.py — forceer de nieuwe b2b-index (menu + logo's) schoon naar
main EN victor-staging, zodat de '-X theirs'-pull in generate_article.py 'm niet
meer terugdraait. Template is al gepatcht; dit deployt deterministisch.
Draai met venv:  /root/felix_hq/venv/bin/python3 /tmp/pbs.py
"""
import os, sys, subprocess
FELIX = "/root/felix_hq"; REPO = "/root/felix_hq/repos/aibuildermarketplace"
IDX = os.path.join(REPO, "b2b", "index.html")
os.chdir(FELIX); sys.path.insert(0, FELIX)
import generate_article as g

def git(*a):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    print("  git", a[0], "->", (r.stdout + r.stderr).strip()[:200]); return r

def has_menu():
    try: return 'class="topnav-links"' in open(IDX, encoding="utf-8").read()
    except: return False

print("[1] rebuild (nieuwe template)")
g.rebuild_index(g.get_existing_folders())
print("  menu in rebuild:", has_menu())

print("[2] commit + pull -X OURS (ons nieuwe menu wint) + rebuild + push main")
git("add", "b2b/index.html")
git("commit", "-m", "b2b index: nav menu + logos (force-sync)")
git("fetch", "origin")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
g.rebuild_index(g.get_existing_folders())
git("add", "b2b/index.html")
git("commit", "-m", "b2b index rebuild after pull (keep menu)")
print("  menu na pull+rebuild:", has_menu())
git("push", "origin", "HEAD:main")

print("[3] staging gelijktrekken (zelfde index)")
sp = git("push", "origin", "HEAD:victor-staging")
if sp.returncode != 0:
    print("  staging niet fast-forward — probeer met lease")
    git("push", "--force-with-lease", "origin", "HEAD:victor-staging")

print("[4] verificatie")
git("fetch", "origin")
m = git("show", "origin/main:b2b/index.html")
s = git("show", "origin/victor-staging:b2b/index.html")
print("  menu op origin/main:   ", 'class="topnav-links"' in m.stdout)
print("  menu op origin/staging:", 'class="topnav-links"' in s.stdout)
print("\n✅ KLAAR — check https://aibuildermarketplace.com/b2b/ (na ~1-2 min)")

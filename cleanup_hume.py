#!/usr/bin/env python3
"""Hume AI heeft z'n affiliate-programma beëindigd — haal het van de content af.

1) Verwijdert de HumeAI-entry uit COMPETITORS in generate_article.py (geen nieuwe
   Hume-vs-pagina's meer).
2) Vindt bestaande Hume-artikelen (slug bevat 'humeai') — flat .html EN
   directory/index.html — en zet ze op noindex + haalt ze uit sitemap.xml
   (--delete = git rm i.p.v. noindex).
Dry-run default; --apply voert door + commit/push (→ victor-staging).
"""
import argparse
import os
import re
import subprocess

REPO = "/root/felix_hq/repos/aibuildermarketplace"
GEN = "/root/felix_hq/generate_article.py"
B2B = os.path.join(REPO, "b2b")
SITEMAP = os.path.join(REPO, "sitemap.xml")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--delete", action="store_true", help="verwijder de pagina's i.p.v. noindex")
A = ap.parse_args()


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)


# 1) HumeAI uit COMPETITORS
src = open(GEN, encoding="utf-8").read()
comp_line = re.search(r'^[ \t]*["\']HumeAI["\']\s*:\s*\[[^\]]*\],?\n', src, re.M)
comp_status = "niet gevonden"
if comp_line:
    comp_status = "te verwijderen" if not A.apply else "verwijderd"
    if A.apply:
        src2 = src[:comp_line.start()] + src[comp_line.end():]
        import py_compile, shutil, time
        tmp = GEN + ".new"
        open(tmp, "w", encoding="utf-8").write(src2)
        try:
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            os.remove(tmp)
            print("⚠️ COMPETITORS-fix compileert niet — generator ongewijzigd:", str(e)[:150])
            comp_status = "OVERGESLAGEN (compile-fout)"
        else:
            shutil.copy(GEN, GEN + ".bak." + str(int(time.time())))
            os.replace(tmp, GEN)
print(f"1) HumeAI uit COMPETITORS: {comp_status}")

# 2) Hume-artikelen vinden (slug bevat 'humeai')
targets = []
for fn in os.listdir(B2B):
    full = os.path.join(B2B, fn)
    if os.path.isfile(full) and fn.endswith(".html") and "humeai" in fn.lower():
        targets.append((fn[:-5], full))
    elif os.path.isdir(full) and "humeai" in fn.lower():
        idx = os.path.join(full, "index.html")
        if os.path.exists(idx):
            targets.append((fn, idx))

mode = "verwijderen (git rm)" if A.delete else "noindex"
print(f"2) Hume-artikelen: {len(targets)} → {mode}")
for slug_, _ in targets[:15]:
    print(f"     - {slug_}")
if len(targets) > 15:
    print(f"     … en {len(targets) - 15} meer")

if not A.apply:
    print("\nDRY-RUN — draai met --apply (+ evt. --delete) om door te voeren + pushen.")
    raise SystemExit(0)

sitemap = open(SITEMAP, encoding="utf-8").read() if os.path.exists(SITEMAP) else ""
done = 0
for slug_, p in targets:
    if A.delete:
        d = os.path.dirname(p)
        if os.path.basename(p) == "index.html" and d != B2B:
            git("rm", "-r", "-f", "--", os.path.relpath(d, REPO))
        else:
            git("rm", "-f", "--", os.path.relpath(p, REPO))
        done += 1
    else:
        try:
            h = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if "noindex" not in h.lower():
            if re.search(r'<meta[^>]+name=["\']robots["\']', h, re.I):
                h = re.sub(r'(<meta[^>]+name=["\']robots["\'][^>]*content=["\'])[^"\']*(["\'])',
                           r"\1noindex, follow\2", h, count=1, flags=re.I)
            else:
                h = h.replace("<head>", '<head>\n<meta name="robots" content="noindex, follow">', 1)
            open(p, "w", encoding="utf-8").write(h)
            done += 1
    if sitemap:
        sitemap = re.sub(r"\s*<url>(?:(?!</url>).)*?/b2b/" + re.escape(slug_) +
                         r"[/.<](?:(?!</url>).)*?</url>", "", sitemap, flags=re.S)
if sitemap and os.path.exists(SITEMAP):
    open(SITEMAP, "w", encoding="utf-8").write(sitemap)

git("add", "-A")
git("commit", "-m", f"Hume AI affiliate program ended: {mode} {done} pages + remove from COMPETITORS")
git("pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit")
ps = git("push", "origin", "main")
tail = (ps.stdout + ps.stderr).strip().splitlines()
print(f"\n✓ {done} Hume-pagina's verwerkt ({mode})")
print("✓ push:", tail[-1] if tail else "(niets)")

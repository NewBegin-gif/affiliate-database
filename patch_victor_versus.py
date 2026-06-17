#!/usr/bin/env python3
"""Contentkwaliteit #1 — stop + ruim de onzinnige programmatische 'vs'-pagina's op.

Bug: de Versus-generator pakt 50% van de tijd een WILLEKEURIGE tool als
tegenhanger (random.choice op alle merken) i.p.v. de curated COMPETITORS-lijst,
→ pagina's als 'bitvavo-vs-kinsta', 'beehiiv-vs-wprocket' (niemand zoekt die;
Google leest het als programmatische spam → helpful-content-risico).

Dit script:
 1) fixt generate_article.py: alleen nog COMPETITORS-paren (geen curated
    concurrent → geen versus-pagina);
 2) classificeert bestaande b2b/*-vs-*.html: paren die NIET in COMPETITORS zitten
    → meta robots noindex + uit sitemap.xml;
 3) dry-run default (toont aantal + sample); --apply voert door + commit/push.

COMPETITORS wordt uit generate_article.py zelf ge-ast-parsed (volledige dict).
"""
import argparse
import ast
import os
import re
import subprocess
import sys
import time

REPO = "/root/felix_hq/repos/aibuildermarketplace"
GEN = "/root/felix_hq/generate_article.py"
B2B = os.path.join(REPO, "b2b")
SITEMAP = os.path.join(REPO, "sitemap.xml")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
A = ap.parse_args()


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)


def slug(s):
    return s.lower().replace(" ", "").replace(".", "")


# ── COMPETITORS volledig uit het bestand halen ───────────────────────────
src = open(GEN, encoding="utf-8").read()
m = re.search(r'COMPETITORS\s*=\s*\{', src)
if not m:
    sys.exit("❌ COMPETITORS-dict niet gevonden.")
i, depth = m.end() - 1, 0
for j in range(i, len(src)):
    depth += (src[j] == "{") - (src[j] == "}")
    if depth == 0:
        end = j
        break
COMPETITORS = ast.literal_eval(src[i:end + 1])
valid = set()
for k, comps in COMPETITORS.items():
    for c in comps:
        a, b = slug(k), slug(c)
        valid.add((a, b))
        valid.add((b, a))
print(f"COMPETITORS: {len(COMPETITORS)} merken, {len(valid)//2} curated paren")

# ── 1) generator-fix ─────────────────────────────────────────────────────
OLD = (
    "            if random.random() < 0.5 and brand in COMPETITORS:\n"
    "                brand2 = random.choice(COMPETITORS[brand])\n"
    "                slug = f\"{brand.lower().replace(' ','').replace('.','')}-vs-{brand2.lower().replace(' ','').replace('.','')}-{lang_code}\"\n"
    "            else:\n"
    "                brand2 = random.choice([b for b in weighted_brands if b != brand])\n"
    "                slug = f\"{brand.lower().replace(' ','').replace('.','')}-vs-{brand2.lower().replace(' ','').replace('.','')}-{lang_code}\"\n"
)
NEW = (
    "            if brand not in COMPETITORS or not COMPETITORS[brand]:\n"
    "                continue  # geen curated concurrent -> geen onzin-versus-pagina\n"
    "            brand2 = random.choice(COMPETITORS[brand])\n"
    "            slug = f\"{brand.lower().replace(' ','').replace('.','')}-vs-{brand2.lower().replace(' ','').replace('.','')}-{lang_code}\"\n"
)
gen_status = "al gefixt"
if OLD in src:
    gen_status = "FIX klaar" if not A.apply else "GEFIXT"
    if A.apply:
        import py_compile
        new_src = src.replace(OLD, NEW, 1)
        tmp = GEN + ".new"
        open(tmp, "w", encoding="utf-8").write(new_src)
        try:
            py_compile.compile(tmp, doraise=True)
        except py_compile.PyCompileError as e:
            os.remove(tmp)
            sys.exit("❌ generator-fix compileert niet — afgebroken:\n" + str(e))
        import shutil
        shutil.copy(GEN, GEN + ".bak." + str(int(time.time())))
        os.replace(tmp, GEN)
print(f"1) generator Versus-fix: {gen_status}")

# ── 2) classificeer bestaande vs-pagina's ────────────────────────────────
nonsense, ok = [], 0
for fn in os.listdir(B2B):
    if "-vs-" not in fn or not fn.endswith(".html"):
        continue
    mm = re.match(r"(.+?)-vs-(.+?)(?:-([a-z]{2}))?$", fn[:-5])
    if not mm:
        continue
    if (mm.group(1), mm.group(2)) in valid:
        ok += 1
    else:
        nonsense.append(fn)

print(f"2) vs-pagina's: {ok} zinnig (COMPETITORS) | {len(nonsense)} ONZIN → noindex")
for fn in nonsense[:15]:
    print(f"     - {fn}")
if len(nonsense) > 15:
    print(f"     … en {len(nonsense) - 15} meer")

if not A.apply:
    print("\nDRY-RUN — draai met --apply om de generator te fixen, onzin te noindexen + pushen.")
    sys.exit(0)

# ── apply: noindex + sitemap + commit ────────────────────────────────────
done = 0
sitemap = open(SITEMAP, encoding="utf-8").read() if os.path.exists(SITEMAP) else ""
for fn in nonsense:
    p = os.path.join(B2B, fn)
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
    stem = fn[:-5]
    if sitemap:
        sitemap = re.sub(r"\s*<url>(?:(?!</url>).)*?/b2b/" + re.escape(stem) +
                         r"[/.](?:(?!</url>).)*?</url>", "", sitemap, flags=re.S)
if sitemap and os.path.exists(SITEMAP):
    open(SITEMAP, "w", encoding="utf-8").write(sitemap)

git("add", "-A")
git("commit", "-m", f"Content quality: noindex {done} nonsensical programmatic vs-pages + fix versus pairing")
git("pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit")
ps = git("push", "origin", "main")
tail = (ps.stdout + ps.stderr).strip().splitlines()
print(f"\n✓ {done} pagina's op noindex gezet + uit sitemap")
print("✓ push:", tail[-1] if tail else "(niets)")
print("→ Victor promoot staging → live via victor_automerge.sh (binnen het uur).")

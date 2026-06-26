#!/usr/bin/env python3
"""fix_duplicate_titles.py — maak dubbele <title>'s uniek op de b2b-pagina's
(cannibalisatie-/duplicate-signaal). Voegt een onderscheidende suffix toe:
taal-naam voor cross-taal-botsingen, variant-woord (breakdown/competitors/…)
voor cross-type, met een gegarandeerde uniciteits-fallback. Past <title>,
og:title en twitter:title aan. Verwijdert NIETS.

DRY-RUN (default). --apply: schrijf + push main+staging.
Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/fdt.py
  /root/felix_hq/venv/bin/python3 /tmp/fdt.py --apply
"""
import sys, re, subprocess
from collections import defaultdict
from pathlib import Path

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
BRAND = " | AIBuilder Marketplace"
LANG = {"uk":"Ukrainian","da":"Danish","hi":"Hindi","tr":"Turkish","fr":"French",
 "id":"Indonesian","vi":"Vietnamese","ge":"German","de":"German","es":"Spanish",
 "sp":"Spanish","po":"Portuguese","pt":"Portuguese","it":"Italian","ja":"Japanese",
 "ko":"Korean","zh":"Chinese","ar":"Arabic","pl":"Polish","sv":"Swedish","no":"Norwegian",
 "mx":"Spanish (MX)","br":"Portuguese (BR)","fi":"Finnish","el":"Greek","sw":"Swahili",
 "ha":"Hausa","yo":"Yoruba","zu":"Zulu","am":"Amharic","af":"Afrikaans","ru":"Russian",
 "ro":"Romanian","cs":"Czech","hu":"Hungarian","th":"Thai","nl":"Dutch","du":"Dutch"}
ALLLANG = set(LANG) | {"en"}

pages = {}
for f in sorted(B2B.glob("*/index.html")):
    t = f.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>([^<]*)</title>", t)
    if m:
        pages[f.parent.name] = (f, m.group(1))

title2 = defaultdict(list)
for slug, (f, title) in pages.items():
    title2[title].append(slug)

def suffix_for(slug, title):
    toks = slug.split("-")
    tl = title.lower()
    variant = [w for w in toks if w not in ALLLANG and w.lower() not in tl]
    lang = toks[-1] if toks[-1] in LANG else None
    parts = []
    if variant:
        parts.append(" ".join(w.capitalize() for w in variant))
    if lang:
        parts.append(LANG[lang])
    return (" — " + ", ".join(parts)) if parts else ""

def build_title(title, suffix, extra=""):
    s = suffix + extra
    return title.replace(BRAND, s + BRAND) if BRAND in title else (title + s)

changes = {}
for title, slugs in title2.items():
    if len(slugs) < 2:
        continue
    slugs_sorted = sorted(slugs, key=lambda s: (len(s), s))
    used = {title}
    for s in slugs_sorted[1:]:           # eerste behoudt de titel
        nt = build_title(title, suffix_for(s, title))
        i = 2
        while nt in used:
            nt = build_title(title, suffix_for(s, title), f" ({i})")
            i += 1
        used.add(nt)
        changes[s] = (title, nt)

print("=" * 60)
print(f"DUBBELE TITELS  ({'APPLY' if APPLY else 'DRY-RUN'})")
print("=" * 60)
print(f"  b2b-pagina's gescand : {len(pages)}")
print(f"  titels uniek te maken: {len(changes)} pagina's")
print("  --- steekproef (oud → nieuw) ---")
for slug, (old, new) in list(changes.items())[:12]:
    print(f"    [{slug}]")
    print(f"      {old[:60]}")
    print(f"      → {new[:70]}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

n = 0
for slug, (old, new) in changes.items():
    f = pages[slug][0]
    t = f.read_text(encoding="utf-8", errors="ignore")
    nt = t.replace(f"<title>{old}</title>", f"<title>{new}</title>")
    nt = nt.replace(f'property="og:title" content="{old}"', f'property="og:title" content="{new}"')
    nt = nt.replace(f'name="twitter:title" content="{old}"', f'name="twitter:title" content="{new}"')
    if nt != t:
        f.write_text(nt, encoding="utf-8"); n += 1
print(f"  pagina's herschreven: {n}")

def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "-A", "--", "b2b")
git("commit", "-m", f"SEO: maak {n} dubbele b2b-titels uniek (taal/variant-suffix) — cannibalisatie-signaal weg")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-150:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-150:])
print("KLAAR — plak alles terug.")

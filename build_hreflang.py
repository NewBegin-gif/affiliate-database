#!/usr/bin/env python3
"""Bouwt complete, wederzijdse hreflang-clusters voor alle /b2b/-artikelen.

Scant b2b/<slug>/index.html, groepeert varianten per basis-slug (= slug zonder
taalsuffix), en zet in ELKE pagina een identiek hreflang-blok met alle taal-
alternatieven + x-default. Idempotent via marker <!-- hreflang-v1 --> (herschrijft
het blok bij elke run, dus self-healing). Strijkt en passant 'noindex' robots-meta
glad op artikelpagina's. Dry-run default; --apply schrijft; --commit commit+pusht.

Taal-codeerschema (VALKUIL): du=nl, ge=de, sp=es, po=pt, br=pt-BR, mx=es-MX."""
import os, re, sys, glob, subprocess

REPO = "/root/felix_hq/repos/aibuildermarketplace"
BASE = "https://aibuildermarketplace.com/b2b/"
APPLY  = "--apply"  in sys.argv
COMMIT = "--commit" in sys.argv

# suffix-code -> geldige hreflang-waarde
LANG = {
    "en":"en","fr":"fr","du":"nl","po":"pt","ge":"de","sp":"es","it":"it","pl":"pl",
    "sv":"sv","da":"da","no":"no","ja":"ja","tr":"tr","id":"id","vi":"vi","br":"pt-BR",
    "mx":"es-MX","uk":"uk","zh":"zh","ko":"ko","hi":"hi","ar":"ar","th":"th","ru":"ru",
    "cs":"cs","fi":"fi","el":"el","hu":"hu","ro":"ro","sw":"sw","ha":"ha","yo":"yo",
    "am":"am","af":"af","zu":"zu",
}

MARK_OPEN  = "<!-- hreflang-v1 -->"
MARK_CLOSE = "<!-- /hreflang-v1 -->"
BLOCK_RE   = re.compile(re.escape(MARK_OPEN) + r".*?" + re.escape(MARK_CLOSE) + r"\n?", re.S)
ROBOTS_RE  = re.compile(r'[ \t]*<meta[^>]*name=["\']robots["\'][^>]*>\s*\n?', re.I)

def split_slug(slug):
    """-> (base, code) als slug op een bekende taalsuffix eindigt, anders (slug, None)."""
    i = slug.rfind("-")
    if i == -1:
        return slug, None
    suf = slug[i+1:]
    if suf in LANG:
        return slug[:i], suf
    return slug, None

# 1) inventariseer alle artikel-dirs
dirs = sorted(glob.glob(os.path.join(REPO, "b2b", "*", "index.html")))
groups = {}          # base -> {code: slug}
slug_of = {}         # path -> slug
for path in dirs:
    slug = os.path.basename(os.path.dirname(path))
    slug_of[path] = slug
    base, code = split_slug(slug)
    if code is None:
        continue
    groups.setdefault(base, {})[code] = slug

def build_block(group):
    # x-default = Engels indien aanwezig, anders alfabetisch eerste (consistent in cluster)
    xdef = group.get("en") or sorted(group.values())[0]
    lines = [MARK_OPEN]
    for code in sorted(group, key=lambda c: LANG[c]):
        lines.append(f'<link rel="alternate" hreflang="{LANG[code]}" href="{BASE}{group[code]}/"/>')
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{xdef}/"/>')
    lines.append(MARK_CLOSE)
    return "\n    ".join(lines) + "\n"

changed = noindex_fixed = skipped = 0
for path in dirs:
    slug = slug_of[path]
    base, code = split_slug(slug)
    html = open(path, encoding="utf-8").read()
    orig = html

    # noindex weghalen (artikelen moeten indexeerbaar zijn)
    def _strip(m):
        global noindex_fixed
        if "noindex" in m.group(0).lower():
            noindex_fixed += 1
            return ""
        return m.group(0)
    html = ROBOTS_RE.sub(_strip, html)

    # oud hreflang-blok verwijderen (idempotent / self-healing)
    html = BLOCK_RE.sub("", html)

    # nieuw blok injecteren vlak voor </head>, mits we de taal kennen
    if code is not None and base in groups:
        block = "    " + build_block(groups[base])
        m = re.search(r"</head>", html, re.I)
        if m:
            html = html[:m.start()] + block + html[m.start():]
        else:
            skipped += 1

    if html != orig:
        changed += 1
        if APPLY:
            open(path, "w", encoding="utf-8").write(html)

# rapport
n_clusters = sum(1 for g in groups.values() if len(g) > 1)
print(f"artikel-dirs gescand : {len(dirs)}")
print(f"basis-slugs (clusters): {len(groups)}  (waarvan multi-taal: {n_clusters})")
print(f"pagina's gewijzigd   : {changed}")
print(f"noindex weggehaald   : {noindex_fixed}")
if skipped:
    print(f"⚠️  zonder </head>    : {skipped}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Voer uit met --apply.")
    sys.exit(0)

if COMMIT and changed:
    def git(*a):
        return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
    git("add", "-A", "--", "b2b")
    r = git("commit", "-m", "hreflang: sync taal-clusters (self-healing)")
    print(r.stdout.strip() or r.stderr.strip())
    p = git("push", "origin", "main")
    print((p.stdout + p.stderr).strip())
print("\n✅ klaar.")

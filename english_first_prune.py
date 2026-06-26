#!/usr/bin/env python3
"""english_first_prune.py — krimp de b2b-content-farm naar een Engels-eerste
kwaliteitskern. Verwijdert alle NIET-Engelse taalvarianten (de 40-talen-
explosie) + de Nederlandse legacy .html-bestanden in /b2b/. BEHOUDT: alles met
-en, hero-reviews en pagina's zonder taal-suffix (Engels/hand-gebouwd).

Ruimt mee op: hreflang-alternates (kern wordt single-language), interne links
naar verwijderde pagina's, en sitemap-entries.

DRY-RUN (default): telt + breakdown per taal + impact, schrijft volledige lijst
naar /tmp/eng_prune_list.txt. Verwijdert niets.
--apply: git rm, strip hreflang + interne links + sitemap, push main+staging.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/efp.py            # dry-run
  /root/felix_hq/venv/bin/python3 /tmp/efp.py --apply
"""
import sys, re, subprocess
from pathlib import Path
from collections import Counter

APPLY = "--apply" in sys.argv
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
SITEMAP = REPO / "sitemap.xml"

# Niet-Engelse taal-suffixen die Victor gebruikt (en algemene ISO-codes).
NON_ENG = {
 "fr","de","ge","du","nl","sp","es","po","pt","it","ja","da","vi","tr","pl","mx",
 "no","id","sv","ko","fi","ar","zh","hi","ro","cs","hu","el","sw","ha","yo","am",
 "af","ru","br","th","zu","ca","uk","he","fa","ur","bn","ta","ms","tl","ka","az",
 "uz","kk","ne","si","my","km","lo","mn","gu","mr","pa","te","kn","ml","is","sl",
 "sk","hr","sr","bg","lt","lv","et","sq","mk","be","ky","tg","tk","ps","sd","ug",
}
# Hero's / curated pagina's die ALTIJD blijven (extra vangnet).
KEEP_ALWAYS = {
 "1password-review","payoneer-review","nordvpn-review","apollo-review",
 "streak-review","aweber-review","aspire-review",
}


def prune_lang(name):
    """Geef taalcode terug als folder een niet-Engelse variant is, anders None."""
    if name in KEEP_ALWAYS:
        return None
    parts = name.rsplit("-", 1)
    if len(parts) == 2 and parts[1].lower() in NON_ENG:
        return parts[1].lower()
    return None


# ── Detectie ──
dirs = [p for p in B2B.iterdir() if p.is_dir()]
html_files = [p for p in B2B.iterdir() if p.is_file() and p.suffix == ".html"]

prune_dirs, keep_dirs, langs = [], [], Counter()
for p in dirs:
    lc = prune_lang(p.name)
    if lc:
        prune_dirs.append(p); langs[lc] += 1
    else:
        keep_dirs.append(p)

prune_slugs = {p.name for p in prune_dirs}
print("=" * 64)
print(f"ENGELS-EERST PRUNE  ({'APPLY' if APPLY else 'DRY-RUN'})")
print("=" * 64)
print(f"  totaal b2b-folders        : {len(dirs)}")
print(f"  → BEHOUDEN (Engels/hero's): {len(keep_dirs)}")
print(f"  → VERWIJDEREN (niet-Engels): {len(prune_dirs)}")
print(f"  + Nederlandse legacy .html: {len(html_files)}")
print(f"\n  per taal (top 25):")
for lc, c in langs.most_common(25):
    print(f"    -{lc}: {c}")

allnames = sorted(prune_slugs) + sorted(f.name for f in html_files)
Path("/tmp/eng_prune_list.txt").write_text("\n".join(allnames), encoding="utf-8")
print(f"\n  volledige lijst ({len(allnames)}) → /tmp/eng_prune_list.txt")
print("  --- steekproef BEHOUDEN (eerste 20) ---")
for p in sorted(n.name for n in keep_dirs)[:20]:
    print(f"    KEEP  {p}")

# impact
if prune_slugs:
    alt = "|".join(re.escape(s) for s in list(prune_slugs)[:4000])
    href_re = re.compile(r'href="/b2b/(?:%s)/"' % alt)
    hreflang_files = il_files = 0
    sample_keep = keep_dirs[:600]
    for p in sample_keep:
        f = p / "index.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        if 'rel="alternate"' in t and "hreflang" in t:
            hreflang_files += 1
        if href_re.search(t):
            il_files += 1
    print(f"\n  (steekproef {len(sample_keep)} keep-pagina's) met hreflang-alternates: {hreflang_files}, met interne links naar prune-pagina's: {il_files}")
    sm = SITEMAP.read_text(encoding="utf-8", errors="ignore") if SITEMAP.exists() else ""
    sm_hits = sum(1 for s in prune_slugs if f"/b2b/{s}/" in sm)
    print(f"  sitemap-entries te verwijderen: {sm_hits}")

if not APPLY:
    print("\nDRY-RUN — niets verwijderd. Bekijk /tmp/eng_prune_list.txt, dan --apply.")
    print("LET OP: na akkoord ook Victor op Engels-only zetten (anders vult hij bij).")
    sys.exit(0)

# ── APPLY ──
if not prune_slugs and not html_files:
    print("Niets te prunen."); sys.exit(0)

for p in prune_dirs:
    subprocess.run(["git", "-C", str(REPO), "rm", "-rq", f"b2b/{p.name}"], check=False)
for f in html_files:
    subprocess.run(["git", "-C", str(REPO), "rm", "-q", f"b2b/{f.name}"], check=False)

# strip hreflang-alternates + interne links uit de behouden pagina's
alt = "|".join(re.escape(s) for s in prune_slugs)
hreflang_re = re.compile(r'\s*<link[^>]*rel="alternate"[^>]*hreflang="[^"]*"[^>]*>', re.I)
li_re = re.compile(r'<li[^>]*>(?:(?!</li>).)*?href="/b2b/(?:%s)/"(?:(?!</li>).)*?</li>' % alt, re.S)
a_re = re.compile(r'<a [^>]*href="/b2b/(?:%s)/"[^>]*>.*?</a>' % alt, re.S)
cleaned = 0
for p in keep_dirs:
    f = p / "index.html"
    if not f.exists():
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    nt = hreflang_re.sub("", t)
    nt = a_re.sub("", li_re.sub("", nt))
    if nt != t:
        f.write_text(nt, encoding="utf-8"); cleaned += 1
print(f"hreflang + interne links opgeschoond in {cleaned} pagina's")

if SITEMAP.exists():
    sm = SITEMAP.read_text(encoding="utf-8", errors="ignore")
    url_re = re.compile(r'<url>(?:(?!</url>).)*?<loc>[^<]*?/b2b/(?:%s)/[^<]*?</loc>(?:(?!</url>).)*?</url>\s*' % alt, re.S)
    nsm, n = url_re.subn("", sm)
    if n:
        SITEMAP.write_text(nsm, encoding="utf-8"); print(f"sitemap: {n} entries verwijderd")

def git(*a): return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "-A", "--", "b2b", "sitemap.xml")
git("commit", "-m", f"Engels-eerst: verwijder {len(prune_slugs)} niet-Engelse b2b-varianten + {len(html_files)} NL-legacy + hreflang/links/sitemap")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-160:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-160:])
print("KLAAR — plak alles terug.")

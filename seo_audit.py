#!/usr/bin/env python3
"""seo_audit.py — intel voor de SEO-fixes. READ-ONLY.

1) Dumpt de topic/taal-picker van generate_article.py (om Engels-first te patchen).
2) Engelse-dekking per /b2b/-cluster: hoeveel topics missen een -en versie?
3) Lijst grootste multi-taal clusters ZONDER Engels (backfill-kandidaten).
4) Locaties van build_hreflang.py (voor de hreflang-resync).
"""
import os
import re
import glob

AG = "/root/felix_hq/generate_article.py"
REPO = "/root/felix_hq/repos/aibuildermarketplace"
B2B = os.path.join(REPO, "b2b")

# taalsuffixen (zelfde set als de generator)
SUF = ["-zh","-ko","-hi","-ar","-th","-ru","-cs","-fi","-el","-hu","-ro","-sw","-ha","-yo","-am","-af","-zu",
       "-en","-fr","-du","-po","-ge","-sp","-it","-pl","-sv","-da","-no","-ja","-tr","-id","-vi","-br","-mx",
       "-uk","-de","-nl","-es","-pt"]
SUF = sorted(SUF, key=len, reverse=True)


def hr(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def split_slug(s):
    for suf in SUF:
        if s.endswith(suf):
            return s[:-len(suf)], suf[1:]
    return s, None


# 1) topic/taal-picker
hr("1. Topic/taal-picker in generate_article.py (regels 1335-1410)")
if os.path.exists(AG):
    lines = open(AG, encoding="utf-8", errors="replace").read().split("\n")
    for i in range(1334, min(1410, len(lines))):
        print(f"  {i+1}: {lines[i]}")
else:
    print("  generate_article.py niet gevonden")

# 2+3) cluster-dekking
hr("2. Engelse-dekking per cluster")
dirs = [d for d in glob.glob(os.path.join(B2B, "*")) if os.path.isdir(d)]
clusters = {}
for d in dirs:
    slug = os.path.basename(d)
    if slug == ".git":
        continue
    base, code = split_slug(slug)
    clusters.setdefault(base, set()).add(code or "??")
total = len(clusters)
with_en = sum(1 for v in clusters.values() if "en" in v)
multi = {b: v for b, v in clusters.items() if len(v) > 1}
multi_no_en = {b: v for b, v in multi.items() if "en" not in v}
single_no_en = {b: v for b, v in clusters.items() if len(v) == 1 and "en" not in v}
print(f"  totaal clusters (basis-slugs): {total}")
print(f"  met Engelse (-en) versie:      {with_en}  ({100*with_en//max(total,1)}%)")
print(f"  ZONDER Engels:                 {total - with_en}")
print(f"  multi-taal clusters:           {len(multi)}")
print(f"  multi-taal ZONDER Engels:      {len(multi_no_en)}  <- backfill-prioriteit")
print(f"  single-taal ZONDER Engels:     {len(single_no_en)}")

hr("3. Grootste multi-taal clusters ZONDER Engels (top 30 backfill-kandidaten)")
for base, v in sorted(multi_no_en.items(), key=lambda kv: len(kv[1]), reverse=True)[:30]:
    print(f"  [{len(v):>2} talen: {','.join(sorted(v))[:50]}]  {base}")

# 4) build_hreflang locatie
hr("4. build_hreflang.py locaties")
found = glob.glob("/root/felix_hq/**/build_hreflang.py", recursive=True)
for p in found:
    print("  ", p)
if not found:
    print("  (niet gevonden onder /root/felix_hq — gebruik de affdb-kopie)")

hr("KLAAR — plak alles terug")

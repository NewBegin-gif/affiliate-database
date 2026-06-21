#!/usr/bin/env python3
"""diag_throttle_plan.py — READ-ONLY. Haalt alles op om 3 patches te schrijven:
  A) build_hreflang.py — waar het noindex strípt (moet stoppen).
  B) sync_vault_from_data.py — hoe het VAULT vult (poort erop).
  C) generate_article.py — talenbron + volume + picker (cureren).
Plus: data-gedreven TALEN-KEEP-LIJST uit GSC (welke talen leveren echt iets op).

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/tp.py
"""
import re, datetime, sys
from pathlib import Path
from collections import defaultdict

HQ = Path("/root/felix_hq")
LANG_SUF = set("en fr du po ge sp it pl sv da no ja tr id vi br mx uk zh ko hi ar th ru cs fi el hu ro sw ha yo am af zu".split())


def dump(path, label, pattern=None, full=False, head=0):
    print("\n" + "=" * 72)
    print(label, f"({path})")
    print("=" * 72)
    p = Path(path)
    if not p.exists():
        print("  ✗ bestaat niet"); return
    lines = p.read_text(encoding="utf-8", errors="ignore").split("\n")
    if full:
        for i, l in enumerate(lines):
            print(f"  L{i+1}: {l}")
    elif head:
        for i, l in enumerate(lines[:head]):
            print(f"  L{i+1}: {l}")
    elif pattern:
        rx = re.compile(pattern, re.I)
        for i, l in enumerate(lines):
            if rx.search(l):
                print(f"  L{i+1}: {l.strip()[:140]}")


# A) build_hreflang.py — noindex-strip
dump(HQ / "build_hreflang.py", "A) build_hreflang.py — noindex/robots-strip",
     pattern=r"noindex|robots|ROBOTS|_strip|\.sub\(")

# B) sync_vault_from_data.py — volledig (waarschijnlijk kort)
dump(HQ / "sync_vault_from_data.py", "B) sync_vault_from_data.py — VAULT-vulling", full=True)

# C) generate_article.py — talenbron + volume + picker
dump(HQ / "generate_article.py", "C) generate_article.py — LANG_CODES / LANGUAGES",
     pattern=r"LANG_CODES\s*=|LANGUAGES\s*=|^LANGS|LANGUAGE_LOCK|weighted_lang|weighted_brand|"
             r"num_articles|range\(|n_articles|ARTICLES|how_many|for _ in|MAX_|generate_one|main\(")

# C2) andere generatoren: lezen die dezelfde talenbron?
for f in ("generate_new_languages.sh", "pseo_engine_v2.py", "generate_alternatives.py"):
    dump(HQ / f, f"C) {f} — talen/volume", pattern=r"lang|LANG|--?batch|range\(|N=|count|talen")

# D) GSC: welke talen leveren echt iets op (keep-lijst)
print("\n" + "=" * 72)
print("D) DATA-GEDREVEN TALEN-KEEP-LIJST (GSC 90d)")
print("=" * 72)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        str(HQ / "gcp_credentials.json"),
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    end = datetime.date.today() - datetime.timedelta(days=1); start = end - datetime.timedelta(days=90)
    rows = svc.searchanalytics().query(siteUrl="sc-domain:aibuildermarketplace.com", body={
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["page"], "rowLimit": 25000}).execute().get("rows", [])
    per = defaultdict(lambda: [0, 0, 0])  # lang -> [pages_with_impr, total_impr, max_impr]
    for r in rows:
        u = r["keys"][0]
        if "/b2b/" not in u:
            continue
        slug = u.rstrip("/").rsplit("/b2b/", 1)[-1]
        i = slug.rfind("-"); suf = slug[i+1:] if i != -1 else ""
        lang = suf if suf in LANG_SUF else "en"
        im = int(r["impressions"])
        per[lang][0] += 1; per[lang][1] += im; per[lang][2] = max(per[lang][2], im)
    print(f"  {'lang':5} {'#pag>0impr':>10} {'tot impr':>9} {'max impr':>9}   keep?")
    keep = []
    for lang in sorted(per, key=lambda l: -per[l][1]):
        pg, tot, mx = per[lang]
        k = mx >= 20 or tot >= 40
        if k:
            keep.append(lang)
        print(f"  {lang:5} {pg:>10} {tot:>9} {mx:>9}   {'JA' if k else 'nee'}")
    print(f"\n  >>> KEEP-LIJST (max>=20 of tot>=40 impr): {keep}")
    print(f"  >>> SCHRAP (lange staart): {sorted(set(LANG_SUF) - set(keep))}")
except Exception as e:
    print("  GSC niet beschikbaar:", e)

print("\nKLAAR — plak alles terug.")

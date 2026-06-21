#!/usr/bin/env python3
"""diag_content_audit.py — READ-ONLY content-audit om autoriteit te concentreren.

Combineert GSC (90d, pagina-niveau: impressies/klikken/positie) met on-page-
signalen (woordtelling, noindex, taal) en deelt elke /b2b/-pagina in buckets:

  A) VERSTERKEN     — pos<=20 met echte impressies (winners; beschermen+uitbouwen)
  B) OPTIMALISEREN  — striking distance (pos 8-20, impr>=10): titel/meta/links
  C) KANNIBALISATIE — merken met veel pagina's waar impressies in 1-2 pagina's
                      zitten -> de dunne broers/zussen samenvoegen of redirecten
  D) SCHRAPPEN      — geïndexeerd maar 90d (bijna) dood + dun: noindex/verwijderen

Read-only: leest GSC + de HTML-bestanden, schrijft NIETS.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/audit.py
"""
import re
import sys
from pathlib import Path
from collections import defaultdict

KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
PROP = "sc-domain:aibuildermarketplace.com"
REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
DAYS = 90
BASE = "https://aibuildermarketplace.com/b2b/"

# ---------- GSC: pagina-niveau 90d ----------
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    import datetime
except Exception as e:
    print("libs ontbreken:", e); sys.exit(1)

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
end = datetime.date.today() - datetime.timedelta(days=1)
start = end - datetime.timedelta(days=DAYS)
rows = svc.searchanalytics().query(siteUrl=PROP, body={
    "startDate": start.isoformat(), "endDate": end.isoformat(),
    "dimensions": ["page"], "rowLimit": 25000,
}).execute().get("rows", [])

gsc = {}  # slug -> (impr, clicks, pos)
for r in rows:
    url = r["keys"][0]
    if "/b2b/" not in url:
        continue
    slug = url.rstrip("/").rsplit("/b2b/", 1)[-1]
    gsc[slug] = (int(r["impressions"]), int(r["clicks"]), r["position"])
print(f"GSC {DAYS}d: {len(rows)} pagina-rijen, waarvan {len(gsc)} /b2b/-pagina's met impressies\n")

# ---------- on-disk: woordtelling, noindex, taal ----------
LANG_SUF = set("en fr du po ge sp it pl sv da no ja tr id vi br mx uk zh ko hi ar th ru cs fi el hu ro sw ha yo am af zu".split())

def base_brand(slug):
    return slug.split("-")[0]

def split_lang(slug):
    i = slug.rfind("-")
    suf = slug[i+1:] if i != -1 else ""
    return (slug[:i], suf) if suf in LANG_SUF else (slug, "")

pages = {}  # slug -> dict(impr,clicks,pos,words,noindex,lang)
for d in sorted(B2B.iterdir()):
    if not d.is_dir():
        continue
    f = d / "index.html"
    if not f.exists():
        continue
    slug = d.name
    try:
        t = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", t)))
    noindex = "noindex" in t.lower()
    _, lang = split_lang(slug)
    impr, clicks, pos = gsc.get(slug, (0, 0, 0.0))
    pages[slug] = dict(impr=impr, clicks=clicks, pos=pos, words=words,
                       noindex=noindex, lang=lang or "en", brand=base_brand(slug))

total = len(pages)
indexed = [s for s, p in pages.items() if not p["noindex"]]
withimpr = [s for s, p in pages.items() if p["impr"] > 0]
withclicks = [s for s, p in pages.items() if p["clicks"] > 0]
print("=" * 72)
print(f"TOTAAL b2b-pagina's op schijf : {total}")
print(f"  geïndexeerd (geen noindex)  : {len(indexed)}")
print(f"  al noindex                  : {total - len(indexed)}")
print(f"  met impressies (90d)        : {len(withimpr)}")
print(f"  met klikken (90d)           : {len(withclicks)}")
print("=" * 72)

def show(slug):
    p = pages[slug]
    return f"pos {p['pos']:5.1f}  impr {p['impr']:5d}  klik {p['clicks']:2d}  {p['words']:5d}w  {slug}"

# ---------- A) VERSTERKEN ----------
strengthen = sorted([s for s in indexed if pages[s]["pos"] and pages[s]["pos"] <= 20 and pages[s]["impr"] >= 20],
                    key=lambda s: -pages[s]["impr"])
print(f"\n### A) VERSTERKEN — {len(strengthen)} winners (pos<=20, impr>=20). Top 25:")
for s in strengthen[:25]:
    print("   " + show(s))

# ---------- B) OPTIMALISEREN (striking distance) ----------
optimize = sorted([s for s in indexed if pages[s]["pos"] and 8 <= pages[s]["pos"] <= 20 and pages[s]["impr"] >= 10
                   and s not in strengthen[:25]], key=lambda s: -pages[s]["impr"])
print(f"\n### B) OPTIMALISEREN — {len(optimize)} striking-distance (pos 8-20, impr>=10). Top 20:")
for s in optimize[:20]:
    print("   " + show(s))

# ---------- C) KANNIBALISATIE / SAMENVOEGEN ----------
by_brand = defaultdict(list)
for s in indexed:
    by_brand[pages[s]["brand"]].append(s)
print("\n### C) KANNIBALISATIE — merken met >=4 geïndexeerde pagina's:")
print("    (veel pagina's, impressies geconcentreerd in 1-2 -> rest = merge/redirect-kandidaat)")
cannib = []
for brand, slugs in sorted(by_brand.items(), key=lambda kv: -len(kv[1])):
    if len(slugs) < 4:
        continue
    tot = sum(pages[s]["impr"] for s in slugs)
    top = max(slugs, key=lambda s: pages[s]["impr"])
    dead_sibs = [s for s in slugs if pages[s]["impr"] <= 1]
    cannib.append((brand, len(slugs), tot, top, len(dead_sibs)))
for brand, n, tot, top, deadn in sorted(cannib, key=lambda x: -x[1])[:25]:
    topimpr = pages[top]["impr"]
    share = f"{100*topimpr/tot:.0f}%" if tot else "—"
    print(f"   {brand:16} {n:3d} pagina's | tot impr {tot:5d} | top '{top}' ({topimpr}, {share} v/h verkeer) | {deadn} dode broers")

# ---------- D) SCHRAPPEN ----------
cut = sorted([s for s in indexed if 1 <= pages[s]["impr"] <= 3 and pages[s]["pos"] > 30 and pages[s]["words"] < 1500],
             key=lambda s: pages[s]["impr"])
zero_indexed = [s for s in indexed if pages[s]["impr"] == 0]
print(f"\n### D) SCHRAPPEN/NOINDEX — {len(cut)} dun+bijna-dood (impr 1-3, pos>30, <1500w). Voorbeeld 20:")
for s in cut[:20]:
    print("   " + show(s))
print(f"\n   + {len(zero_indexed)} geïndexeerde pagina's met 0 impressies in {DAYS}d "
      f"(kandidaat voor prune_dead_pages.py als ze >45d oud zijn)")

# ---------- samenvatting ----------
print("\n" + "=" * 72)
print("SAMENVATTING / AANBEVELING")
print("=" * 72)
print(f"  VERSTERKEN     : {len(strengthen):4d}  -> beschermen + interne links naartoe + content uitbouwen")
print(f"  OPTIMALISEREN  : {len(optimize):4d}  -> titel/meta/FAQ (zoals Proton/Bitvavo-ronde)")
print(f"  KANNIBALISATIE : {len(cannib):4d}  merken -> dunne taal/mode-varianten samenvoegen of redirecten")
print(f"  SCHRAPPEN      : {len(cut):4d}  dun+dood nu + {len(zero_indexed)} zero-impr geïndexeerd")
print("\nKLAAR — plak alles terug.")

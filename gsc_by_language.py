#!/usr/bin/env python3
"""gsc_by_language.py — READ-ONLY. Toont GSC-prestatie (28d) per TAAL (o.b.v.
de /b2b/<slug>-<lang> URL-suffix) en per LAND. Zo beslissen we op feiten welke
taalclusters tractie hebben (behouden) en welke 0 opleveren (snoeien).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/gbl.py
"""
import json, sys, re, datetime as dt
from collections import defaultdict

KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
WANT = "aibuildermarketplace"
DAYS = 28
NON_ENG = {"fr","de","ge","du","nl","sp","es","po","pt","it","ja","da","vi","tr","pl",
 "mx","no","id","sv","ko","fi","ar","zh","hi","ro","cs","hu","el","sw","ha","yo","am",
 "af","ru","br","th","zu","ca","uk","he","fa","ur","bn","ta","ms","tl","ka","az","uz",
 "kk","ne","si","my","km","lo","mn","gu","mr","pa","te","kn","ml","is","sl","sk","hr",
 "sr","bg","lt","lv","et","sq","mk","be","ky","tg","tk","ps","sd","ug"}

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except Exception as e:
    print("✗ Google-libs ontbreken:", e); sys.exit(1)

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
sites = svc.sites().list().execute().get("siteEntry", [])
cand = [s["siteUrl"] for s in sites if WANT in s.get("siteUrl", "")]
if not cand:
    print("✗ Geen AIBM-property toegankelijk."); sys.exit(0)
SITE = cand[0]
end = dt.date.today() - dt.timedelta(days=1)
start = end - dt.timedelta(days=DAYS - 1)
RANGE = dict(startDate=start.isoformat(), endDate=end.isoformat())
print(f"Property: {SITE} | periode {RANGE['startDate']}..{RANGE['endDate']} ({DAYS}d)")

def q(dims, rowLimit=25000):
    body = dict(RANGE, dimensions=dims, rowLimit=rowLimit, dataState="all")
    return svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])

def lang_of(url):
    m = re.search(r"/b2b/([^/]+)/?$", url)
    if not m:
        return "(niet-b2b)"
    slug = m.group(1)
    last = slug.rsplit("-", 1)[-1].lower()
    if last in NON_ENG:
        return last
    if last == "en":
        return "en"
    return "en/core"

# ── per taal (via page-dimensie) ──
rows = q(["page"])
agg = defaultdict(lambda: [0, 0, 0])  # clicks, impressions, pages-with-impr
for r in rows:
    lg = lang_of(r["keys"][0])
    agg[lg][0] += r.get("clicks", 0)
    agg[lg][1] += r.get("impressions", 0)
    agg[lg][2] += 1
tc = sum(v[0] for v in agg.values()); ti = sum(v[1] for v in agg.values())
print(f"\n=== PER TAAL (28d) — totaal {tc} klikken, {ti} vertoningen, {len(rows)} pagina's met data ===")
print(f"  {'taal':10} {'klikken':>8} {'verton.':>9} {'pag.':>6}")
EN = {"en", "en/core"}
eng_c = eng_i = noneng_c = noneng_i = 0
for lg, (c, i, p) in sorted(agg.items(), key=lambda x: -x[1][1]):
    print(f"  {lg:10} {c:>8} {i:>9} {p:>6}")
    if lg in EN: eng_c += c; eng_i += i
    elif lg != "(niet-b2b)": noneng_c += c; noneng_i += i
print(f"\n  ENGELS  : {eng_c} klikken / {eng_i} vertoningen")
print(f"  NIET-ENG: {noneng_c} klikken / {noneng_i} vertoningen  ← de prune-kandidaten")

# ── per land ──
crows = q(["country"])
crows.sort(key=lambda r: -r.get("impressions", 0))
print(f"\n=== TOP 15 LANDEN (28d) ===")
print(f"  {'land':6} {'klikken':>8} {'verton.':>9}")
for r in crows[:15]:
    print(f"  {r['keys'][0]:6} {r.get('clicks',0):>8} {r.get('impressions',0):>9}")
print("\nKLAAR — plak alles terug.")

#!/usr/bin/env python3
"""gsc_opportunities.py — READ-ONLY. Vind de 'near-page-1' kansen: query+pagina
rond positie 4-20 met vertoningen maar weinig klikken — daar levert een betere
titel/snippet of een klein positie-zetje direct klikken op.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/gop.py
"""
import json, sys, datetime as dt

KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
WANT = "aibuildermarketplace"
DAYS = 28

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
# liefst de domain-property (volledige dekking), anders root-prefix, anders eerste
cand.sort(key=lambda s: (not s.startswith("sc-domain:"), len(s)))
SITE = cand[0]
end = dt.date.today() - dt.timedelta(days=1)
start = end - dt.timedelta(days=DAYS - 1)
RANGE = dict(startDate=start.isoformat(), endDate=end.isoformat())
print(f"Property: {SITE} | {RANGE['startDate']}..{RANGE['endDate']} ({DAYS}d)")
if len(cand) > 1:
    print("  (andere beschikbaar:", ", ".join(cand[1:]), ")")

def q(dims, rowLimit=25000):
    body = dict(RANGE, dimensions=dims, rowLimit=rowLimit, dataState="all")
    return svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])

# ── positie-verdeling van vertoningen ──
allrows = q(["query", "page"])
buckets = {"1-3": [0, 0], "4-10": [0, 0], "11-20": [0, 0], "21+": [0, 0]}
for r in allrows:
    p = r.get("position", 99); imp = r.get("impressions", 0); cl = r.get("clicks", 0)
    k = "1-3" if p <= 3 else "4-10" if p <= 10 else "11-20" if p <= 20 else "21+"
    buckets[k][0] += imp; buckets[k][1] += cl
print("\n=== VERTONINGEN/KLIKKEN PER POSITIE-BUCKET (28d) ===")
print(f"  {'positie':8} {'verton.':>9} {'klikken':>8}")
for k in ("1-3", "4-10", "11-20", "21+"):
    print(f"  {k:8} {buckets[k][0]:>9} {buckets[k][1]:>8}")

# ── near-page-1 kansen ──
opps = [r for r in allrows if 4 <= r.get("position", 99) <= 20 and r.get("impressions", 0) >= 5]
opps.sort(key=lambda r: -r.get("impressions", 0))
print(f"\n=== TOP 35 NEAR-PAGE-1 KANSEN (pos 4-20, ≥5 vertoningen) — {len(opps)} totaal ===")
print(f"  {'pos':>4} {'verton':>7} {'klik':>4}  query  →  pagina")
for r in opps[:35]:
    qy, pg = r["keys"][0], r["keys"][1]
    pg = pg.replace("https://aibuildermarketplace.com", "").replace("/b2b/", "…/")
    print(f"  {r['position']:>4.0f} {r.get('impressions',0):>7} {r.get('clicks',0):>4}  {qy[:42]:42}  {pg[:34]}")

# ── top query's met vertoningen (vraag-zicht) ──
qrows = q(["query"])
qrows.sort(key=lambda r: -r.get("impressions", 0))
print(f"\n=== TOP 20 QUERY'S OP VERTONINGEN ===")
print(f"  {'verton':>7} {'klik':>4} {'pos':>5}  query")
for r in qrows[:20]:
    print(f"  {r.get('impressions',0):>7} {r.get('clicks',0):>4} {r.get('position',0):>5.0f}  {r['keys'][0][:50]}")
print("\nKLAAR — plak alles terug.")

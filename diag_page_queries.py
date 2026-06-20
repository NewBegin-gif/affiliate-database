#!/usr/bin/env python3
"""diag_page_queries.py — READ-ONLY GSC. Toont per doelpagina de exacte queries
waarvoor hij vertoond wordt (dimensions=page+query, 28d), zodat we titels
exact-matchend kunnen herschrijven zonder bestaande impressies te schaden.

Gebruikt /root/felix_hq/gcp_credentials.json (webmasters.readonly).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/diagq.py
"""
import sys
KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
PROP = "sc-domain:aibuildermarketplace.com"
DAYS = 28
TARGETS = [
    "proton-pricing-en", "proton-pricing-id",
    "bitvavo-scale-up", "bitvavo-trading-bot", "bitvavo-pricing-en",
]
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    import datetime
except Exception as e:
    print("✗ libs ontbreken:", e); sys.exit(1)

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
end = datetime.date.today() - datetime.timedelta(days=1)
start = end - datetime.timedelta(days=DAYS)

for slug in TARGETS:
    url = f"https://aibuildermarketplace.com/b2b/{slug}/"
    body = {
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["query"],
        "dimensionFilterGroups": [{"filters": [
            {"dimension": "page", "operator": "equals", "expression": url}]}],
        "rowLimit": 15,
    }
    try:
        rows = svc.searchanalytics().query(siteUrl=PROP, body=body).execute().get("rows", [])
    except Exception as e:
        print(f"\n{slug}: ✗ query faalde: {e}"); continue
    print("\n" + "=" * 72)
    print(f"{slug}  ({len(rows)} queries)")
    print("=" * 72)
    if not rows:
        print("  (geen query-data op page-niveau — pagina krijgt impressies via andere paden)")
    for r in rows:
        q = r["keys"][0]
        print(f"   pos {r['position']:5.1f}  impr {int(r['impressions']):5d}  klik {int(r['clicks'])}  {q}")

print("\nKLAAR — plak alles terug.")

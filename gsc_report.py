#!/usr/bin/env python3
"""gsc_report.py — Search Console-rapport voor gerichte SEO-acties.

Levert:
  - striking-distance queries (pos 8-20): grootste quick-win-potentie
  - page-2 queries (pos 11-20) los gemarkeerd
  - top-pagina's + lage-CTR-pagina's (titel/meta-kansen op pos 1-10)
  - hoeveel UNIEKE pagina's überhaupt impressies krijgen (thin-content-indicatie)

Gebruikt het GA4-service-account: /root/felix_hq/gcp_credentials.json
Vereist scope webmasters.readonly + dat het SA als gebruiker op de GSC-property staat.

Draaien (venv met google-libs):
  /root/felix_hq/venv/bin/python3 /tmp/gsc_report.py
Ontbreken de libs:
  /root/felix_hq/venv/bin/pip install google-api-python-client google-auth
"""
import json
import sys

KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
WANT = "aibuildermarketplace"  # substring om de juiste property te kiezen
DAYS = 28


def hr(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# SA-mail tonen (voor toegang verlenen in GSC indien nodig)
try:
    sa_email = json.load(open(KEY)).get("client_email", "?")
except Exception as e:
    print("Kon key niet lezen:", e)
    sys.exit(1)
print("Service-account:", sa_email)
print("→ Dit mailadres moet in Search Console als gebruiker (minstens 'Beperkt') op de property staan.")

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except Exception as e:
    print("\n✗ Google-libs ontbreken:", e)
    print("  /root/felix_hq/venv/bin/pip install google-api-python-client google-auth")
    sys.exit(1)

creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

hr("0. Toegankelijke properties voor dit service-account")
try:
    sites = svc.sites().list().execute().get("siteEntry", [])
except Exception as e:
    print("✗ sites().list() faalde:", e)
    sites = []
for s in sites:
    print(f"  {s.get('siteUrl')}  ({s.get('permissionLevel')})")
cand = [s["siteUrl"] for s in sites if WANT in s.get("siteUrl", "")]
if not cand:
    print(f"\n✗ Geen property met '{WANT}' toegankelijk voor {sa_email}.")
    print("  Voeg het SA toe in GSC: Instellingen → Gebruikers en machtigingen → Gebruiker toevoegen.")
    print("  (Domain-property 'sc-domain:aibuildermarketplace.com' of URL-prefix 'https://aibuildermarketplace.com/'.)")
    sys.exit(0)
SITE = cand[0]
print("\n✓ Gebruik property:", SITE)

import datetime as dt
end = dt.date.today() - dt.timedelta(days=1)
start = end - dt.timedelta(days=DAYS - 1)
RANGE = dict(startDate=start.isoformat(), endDate=end.isoformat())
print(f"  periode: {RANGE['startDate']} t/m {RANGE['endDate']} ({DAYS} dagen)")


def q(dimensions, rowLimit=25000):
    body = dict(RANGE, dimensions=dimensions, rowLimit=rowLimit, dataState="all")
    return svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


# ── queries ───────────────────────────────────────────────────────────────
rows = q(["query"])
for r in rows:
    r["q"] = r["keys"][0]
tot_clicks = sum(r["clicks"] for r in rows)
tot_impr = sum(r["impressions"] for r in rows)
hr(f"1. Totaal ({DAYS}d): {len(rows)} queries · {tot_clicks} klikken · {tot_impr} impressies")

striking = sorted([r for r in rows if 8 <= r["position"] <= 20 and r["impressions"] >= 3],
                  key=lambda r: r["impressions"], reverse=True)
hr(f"2. STRIKING DISTANCE (pos 8-20) — {len(striking)} queries, grootste quick-win")
print(f"  {'pos':>5}  {'impr':>5}  {'klik':>4}  query")
for r in striking[:30]:
    print(f"  {r['position']:>5.1f}  {r['impressions']:>5}  {r['clicks']:>4}  {r['q'][:70]}")

page2 = sorted([r for r in rows if 11 <= r["position"] <= 20 and r["impressions"] >= 2],
               key=lambda r: r["impressions"], reverse=True)
hr(f"3. PAGINA 2 (pos 11-20) — {len(page2)} queries (dichtst bij pagina 1)")
for r in page2[:20]:
    print(f"  {r['position']:>5.1f}  {r['impressions']:>5}  {r['q'][:70]}")

# queries die AL op pagina 1 staan maar slecht klikken = titel/meta-kans
p1lowctr = sorted([r for r in rows if r["position"] <= 10 and r["impressions"] >= 10 and r["ctr"] < 0.02],
                  key=lambda r: r["impressions"], reverse=True)
hr(f"4. PAGINA 1, lage CTR (<2%) — {len(p1lowctr)} queries (titel/meta verbeteren)")
for r in p1lowctr[:15]:
    print(f"  pos {r['position']:>4.1f}  impr {r['impressions']:>5}  CTR {r['ctr']*100:>4.1f}%  {r['q'][:60]}")

# ── pagina's ────────────────────────────────────────────────────────────────
prows = q(["page"])
hr(f"5. PAGINA'S: {len(prows)} unieke pagina's krijgen impressies")
print("   (vergelijk met ~1700 artikelen → indicatie hoeveel Google echt waardeert)")
ptop = sorted(prows, key=lambda r: r["impressions"], reverse=True)[:20]
print(f"\n  Top-20 pagina's op impressies:")
print(f"  {'impr':>5}  {'klik':>4}  {'pos':>5}  pagina")
for r in ptop:
    print(f"  {r['impressions']:>5}  {r['clicks']:>4}  {r['position']:>5.1f}  {r['keys'][0][:64]}")

hr("KLAAR — plak alles terug")

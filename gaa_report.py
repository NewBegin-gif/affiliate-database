#!/usr/bin/env python3
"""gaa_report.py — GA4-rapport (read-only) om te zien WAAR het verkeer vandaan komt.

Levert (28d):
  1) Totalen: sessions, users, new users, views, engagement, gem. duur
  2) KANAAL-verdeling (Direct/Organic/Referral/Social/…) — de hoofdvraag:
     echt publiek of bots/direct?
  3) Bron/medium (top 15)
  4) Top-pagina's op views (top 20)
  5) Landen (top 10) — diversiteit = indicatie echt vs bot

Gebruikt het service-account /root/felix_hq/gcp_credentials.json (scope
analytics.readonly). Het SA moet als 'Viewer' op de GA4-property staan
(Admin → Property Access Management) en de Data API + Admin API moeten aan staan
in het GCP-project.

Property-ID auto-detectie via Admin API; override met env GA4_PID=<nummer>.

Draaien (venv met GA4-libs):
  /root/felix_hq/venv/bin/python3 /tmp/ga.py
Ontbreken de libs:
  /root/felix_hq/venv/bin/pip install google-analytics-data google-analytics-admin
"""
import os
import sys

KEY = "/root/felix_hq/gcp_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def hr(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


try:
    from google.oauth2 import service_account
except Exception as e:
    print("✗ google-auth ontbreekt:", e); sys.exit(1)
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric, OrderBy)
except Exception as e:
    print("✗ GA4-libs ontbreken:", e)
    print("  /root/felix_hq/venv/bin/pip install google-analytics-data google-analytics-admin")
    sys.exit(1)

# ---- property-ID bepalen ----
pid = os.environ.get("GA4_PID")
if not pid:
    try:
        from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
        admin = AnalyticsAdminServiceClient(credentials=creds)
        props = []
        for s in admin.list_account_summaries():
            for p in s.property_summaries:
                props.append((p.property.split("/")[-1], p.display_name))
        print("Toegankelijke GA4-properties voor dit service-account:")
        for num, name in props:
            print(f"  {num}  {name}")
        # kies teinenjins/aibuilder indien aanwezig, anders de eerste
        pick = next((n for n, nm in props if any(k in nm.lower() for k in ("teinenjins", "aibuilder", "builder"))), None)
        pid = pick or (props[0][0] if props else None)
    except Exception as e:
        print("⚠️ kon properties niet automatisch ophalen:", e)
if not pid:
    print("\n✗ Geen property-ID. Voeg het SA toe als Viewer op de GA4-property, of geef het mee:")
    print("  GA4_PID=<nummer> /root/felix_hq/venv/bin/python3 /tmp/ga.py")
    sys.exit(1)
print(f"\n→ Gebruik property: properties/{pid}")

client = BetaAnalyticsDataClient(credentials=creds)
DR = [DateRange(start_date="28daysAgo", end_date="yesterday")]


def report(dims, mets, order_metric=None, limit=25):
    req = RunReportRequest(
        property=f"properties/{pid}", date_ranges=DR,
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        order_bys=([OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric), desc=True)]
                   if order_metric else None),
        limit=limit)
    return client.run_report(req)


try:
    # 1) totalen
    hr("1. TOTALEN (28 dagen)")
    r = report([], ["sessions", "totalUsers", "newUsers", "screenPageViews",
                    "engagementRate", "averageSessionDuration"])
    if r.rows:
        v = [m.value for m in r.rows[0].metric_values]
        print(f"  sessions:{v[0]}  users:{v[1]}  new:{v[2]}  views:{v[3]}  "
              f"engagement:{float(v[4])*100:.0f}%  gem.duur:{float(v[5]):.0f}s")

    # 2) kanaal
    hr("2. KANAAL-VERDELING (waar komt het vandaan?)")
    r = report(["sessionDefaultChannelGroup"], ["sessions", "screenPageViews", "totalUsers"],
               order_metric="sessions", limit=20)
    print(f"  {'kanaal':24} {'sessions':>9} {'views':>8} {'users':>7}")
    for row in r.rows:
        d = row.dimension_values[0].value
        m = [x.value for x in row.metric_values]
        print(f"  {d:24} {m[0]:>9} {m[1]:>8} {m[2]:>7}")

    # 3) bron/medium
    hr("3. BRON / MEDIUM (top 15)")
    r = report(["sessionSource", "sessionMedium"], ["sessions"], order_metric="sessions", limit=15)
    for row in r.rows:
        d = " / ".join(x.value for x in row.dimension_values)
        print(f"  {row.metric_values[0].value:>7}  {d}")

    # 4) top-pagina's
    hr("4. TOP-PAGINA'S op views (top 20)")
    r = report(["pagePath"], ["screenPageViews", "totalUsers"], order_metric="screenPageViews", limit=20)
    for row in r.rows:
        m = [x.value for x in row.metric_values]
        print(f"  views {m[0]:>6}  users {m[1]:>5}  {row.dimension_values[0].value[:70]}")

    # 5) landen
    hr("5. LANDEN (top 10)")
    r = report(["country"], ["sessions"], order_metric="sessions", limit=10)
    for row in r.rows:
        print(f"  {row.metric_values[0].value:>7}  {row.dimension_values[0].value}")

except Exception as e:
    msg = str(e)
    print("\n✗ rapport faalde:", msg[:300])
    if "PERMISSION" in msg.upper() or "denied" in msg.lower():
        print("→ Voeg groeipiloot-bot@… toe als 'Viewer' op de GA4-property "
              "(Admin → Property Access Management) en zet de Data API aan in het GCP-project.")
    sys.exit(1)

print("\nKLAAR — plak alles terug.")

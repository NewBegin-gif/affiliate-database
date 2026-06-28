#!/usr/bin/env python3
"""gsc_trend.py — wekelijkse GSC-trend voor AIBM (clicks / impressies / CTR / positie).

Read-only: query't de Search Console API en print een tabel. Schrijft niets,
wijzigt niets. Bedoeld om te zien of organisch zoekverkeer stijgt of daalt over
de laatste weken — i.p.v. te reageren op één ruizige week.

Draaien op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/gsc_trend.py
"""
import datetime as dt
from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY = "/root/felix_hq/gcp_credentials.json"
SITE = "sc-domain:aibuildermarketplace.com"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
WEEKS_BACK = 10


def main():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    end = dt.date.today() - dt.timedelta(days=2)        # GSC heeft ~2 dagen vertraging
    start = end - dt.timedelta(days=WEEKS_BACK * 7)

    resp = svc.searchanalytics().query(siteUrl=SITE, body={
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 1000,
    }).execute()

    rows = resp.get("rows", [])
    if not rows:
        print("Geen GSC-data terug. Heeft het service-account toegang tot", SITE, "?")
        return

    # groepeer per ISO-week
    wk = {}
    for r in rows:
        d = dt.date.fromisoformat(r["keys"][0])
        y, w, _ = d.isocalendar()
        g = wk.setdefault((y, w), {"clicks": 0.0, "impr": 0.0, "pos_w": 0.0, "first": d})
        g["clicks"] += r.get("clicks", 0)
        g["impr"] += r.get("impressions", 0)
        g["pos_w"] += r.get("position", 0) * r.get("impressions", 0)  # impressie-gewogen
        if d < g["first"]:
            g["first"] = d

    print(f"\nGSC wekelijkse trend — {SITE}")
    print(f"periode {start} t/m {end}\n")
    print(f"{'week-start':<12}{'clicks':>8}{'impressies':>12}{'CTR':>8}{'positie':>9}")
    print("-" * 49)
    prev = None
    for key in sorted(wk):
        g = wk[key]
        ctr = (g["clicks"] / g["impr"] * 100) if g["impr"] else 0
        pos = (g["pos_w"] / g["impr"]) if g["impr"] else 0
        arrow = ""
        if prev is not None:
            arrow = " ▲" if g["clicks"] > prev else (" ▼" if g["clicks"] < prev else " =")
        prev = g["clicks"]
        print(f"{g['first'].isoformat():<12}{int(g['clicks']):>8}{int(g['impr']):>12}{ctr:>7.1f}%{pos:>9.1f}{arrow}")
    print("\nLees zo: stijgen 'clicks' + 'impressies' over de weken? Dan groeit organisch,")
    print("ongeacht wat GA4's totale bezoekersaantal (alle bronnen) op één week doet.\n")


if __name__ == "__main__":
    main()

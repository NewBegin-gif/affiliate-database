#!/usr/bin/env python3
"""gsc_index.py — indexstatus van de nul-impressie /b2b/-pagina's (read-only).

Stap 1: haal alle pagina's MET impressies op (laatste 28d) — die zijn per
definitie geïndexeerd.
Stap 2: nul-impressie-pagina's = alle /b2b/-mappen in de repo MIN die set.
Stap 3: vraag de URL Inspection API per nul-impressie-pagina de coverageState op
en tel hoeveel er NIET geïndexeerd zijn.

Schrijft/wijzigt niets. Draaien op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/gsc_index.py
"""
import datetime as dt
import os
import time
from collections import Counter
from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY = "/root/felix_hq/gcp_credentials.json"
SITE = "sc-domain:aibuildermarketplace.com"
BASE = "https://aibuildermarketplace.com"
REPO_B2B = "/root/felix_hq/repos/aibuildermarketplace/b2b"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DAYS_BACK = 28
SLEEP = 0.15          # vriendelijk voor de API
MAX_INSPECT = 1300    # veiligheidscap (limiet is 2000/dag)


def main():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    end = dt.date.today() - dt.timedelta(days=2)
    start = end - dt.timedelta(days=DAYS_BACK)

    # stap 1: pagina's met impressies
    impressed, startRow = set(), 0
    while True:
        resp = svc.searchanalytics().query(siteUrl=SITE, body={
            "startDate": start.isoformat(), "endDate": end.isoformat(),
            "dimensions": ["page"], "rowLimit": 25000, "startRow": startRow,
        }).execute()
        batch = resp.get("rows", [])
        for r in batch:
            impressed.add(r["keys"][0].rstrip("/"))
        if len(batch) < 25000:
            break
        startRow += 25000

    # stap 2: alle /b2b/-mappen → nul-impressie-set
    if not os.path.isdir(REPO_B2B):
        print("Repo-pad niet gevonden:", REPO_B2B, "— pas REPO_B2B aan.")
        return
    b2b_urls = [f"{BASE}/b2b/{d}" for d in os.listdir(REPO_B2B)
                if os.path.isdir(os.path.join(REPO_B2B, d)) and d != ".git"]
    zero = [u for u in b2b_urls if u not in impressed and u.rstrip("/") not in impressed]

    print(f"\nIndexstatus nul-impressie /b2b/-pagina's — {SITE}")
    print(f"totaal /b2b/: {len(b2b_urls)} | met impressies (=geïndexeerd): "
          f"{len(b2b_urls) - len(zero)} | nul-impressie: {len(zero)}\n")
    inspect = zero[:MAX_INSPECT]
    if len(zero) > MAX_INSPECT:
        print(f"(inspecteer een cap van {MAX_INSPECT}; rest schaalt mee)\n")

    tally = Counter()
    for i, u in enumerate(inspect, 1):
        try:
            res = svc.urlInspection().index().inspect(body={
                "inspectionUrl": u + "/", "siteUrl": SITE,
            }).execute()
            state = res.get("inspectionResult", {}).get("indexStatusResult", {}) \
                       .get("coverageState", "??")
        except Exception as e:
            state = "ERR:" + str(e)[:40]
        tally[state] += 1
        if i % 100 == 0:
            print(f"  ... {i}/{len(inspect)} geïnspecteerd")
        time.sleep(SLEEP)

    print("\ncoverageState verdeling (nul-impressie-pagina's):")
    for k, v in tally.most_common():
        print(f"  {v:>5}  {k}")

    indexed = sum(v for k, v in tally.items()
                  if "indexed" in k.lower() and "not indexed" not in k.lower())
    notindexed = len(inspect) - indexed
    print(f"\n→ van de {len(inspect)} geïnspecteerde nul-impressie-pagina's: "
          f"~{notindexed} NIET geïndexeerd, ~{indexed} wél (maar zonder vertoningen).")


if __name__ == "__main__":
    main()

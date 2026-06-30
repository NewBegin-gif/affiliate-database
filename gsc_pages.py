#!/usr/bin/env python3
"""gsc_pages.py — GSC-performance per /b2b/-taal voor AIBM (laatste 28 dagen).

Read-only: query't de Search Console API op page-niveau en aggregeert per
taal-suffix (-fr, -ge, -yo, ...) plus de #daan-reviews en Engelse pagina's.
Schrijft niets. Doel: zien of de niet-Engelse Victor-massa écht impressies +
clicks oplevert, vóórdat we iets snoeien.

Draaien op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/gsc_pages.py
"""
import datetime as dt
import re
from collections import defaultdict
from google.oauth2 import service_account
from googleapiclient.discovery import build

KEY = "/root/felix_hq/gcp_credentials.json"
SITE = "sc-domain:aibuildermarketplace.com"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DAYS_BACK = 28


def bucket(url):
    """Classificeer een page-URL naar taal/groep."""
    m = re.search(r"/b2b/([^/?#]+)/?", url)
    if not m:
        return "[niet-/b2b/]"
    slug = m.group(1)
    if slug.endswith("-review"):
        return "EN  [#daan review]"
    lm = re.search(r"-([a-z]{2})$", slug)
    if lm:
        return lm.group(1)
    return "EN  [b2b, geen suffix]"


def main():
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

    end = dt.date.today() - dt.timedelta(days=2)
    start = end - dt.timedelta(days=DAYS_BACK)

    rows, startRow = [], 0
    while True:
        resp = svc.searchanalytics().query(siteUrl=SITE, body={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["page"],
            "rowLimit": 25000,
            "startRow": startRow,
        }).execute()
        batch = resp.get("rows", [])
        rows.extend(batch)
        if len(batch) < 25000:
            break
        startRow += 25000

    if not rows:
        print("Geen GSC-data terug. Service-account toegang tot", SITE, "?")
        return

    g = defaultdict(lambda: {"clicks": 0.0, "impr": 0.0, "pages": 0})
    for r in rows:
        b = bucket(r["keys"][0])
        g[b]["clicks"] += r.get("clicks", 0)
        g[b]["impr"] += r.get("impressions", 0)
        g[b]["pages"] += 1

    EN = {"EN  [#daan review]", "EN  [b2b, geen suffix]", "[niet-/b2b/]"}
    en_cl = en_im = en_pg = nx_cl = nx_im = nx_pg = 0.0
    for k, v in g.items():
        if k in EN:
            en_cl += v["clicks"]; en_im += v["impr"]; en_pg += v["pages"]
        else:
            nx_cl += v["clicks"]; nx_im += v["impr"]; nx_pg += v["pages"]

    print(f"\nGSC per /b2b/-groep — {SITE}")
    print(f"periode {start} t/m {end} ({DAYS_BACK} dagen)\n")
    print(f"{'groep/taal':<26}{'paginas':>9}{'clicks':>9}{'impressies':>12}{'CTR':>8}")
    print("-" * 64)
    for k in sorted(g, key=lambda x: -g[x]["impr"]):
        v = g[k]
        ctr = (v["clicks"] / v["impr"] * 100) if v["impr"] else 0
        print(f"{k:<26}{v['pages']:>9}{v['clicks']:>9.0f}{v['impr']:>12.0f}{ctr:>7.1f}%")
    print("-" * 64)
    print(f"{'ENGELS + reviews':<26}{en_pg:>9.0f}{en_cl:>9.0f}{en_im:>12.0f}"
          f"{(en_cl/en_im*100 if en_im else 0):>7.1f}%")
    print(f"{'NIET-ENGELS (Victor)':<26}{nx_pg:>9.0f}{nx_cl:>9.0f}{nx_im:>12.0f}"
          f"{(nx_cl/nx_im*100 if nx_im else 0):>7.1f}%")
    tot = en_cl + nx_cl
    print(f"\nAandeel clicks uit niet-Engels: {(nx_cl/tot*100 if tot else 0):.0f}%  "
          f"| uit Engels+reviews: {(en_cl/tot*100 if tot else 0):.0f}%")


if __name__ == "__main__":
    main()

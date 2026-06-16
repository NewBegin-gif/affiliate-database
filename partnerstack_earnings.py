#!/usr/bin/env python3
"""Groeipiloot — haal ECHTE commissie-data uit PartnerStack en match op data.json.

Read-only. Haalt de Rewards (commissies) uit de PartnerStack Partner-API v2,
aggregeert het verdiende bedrag per programma/vendor, en matcht dat op de tools
in de centrale data.json. Bedoeld als omzet-signaal naast de GA4-kliks: een tool
die veel oplevert hoort hoger in de homepage-grid dan een tool die alleen veel
geklikt wordt.

GEEN schrijfacties — dit script rapporteert alleen. De ranking-toepassing komt
later (in rank_by_clicks/Groeipiloot), pas als de matching klopt.

Auth: PARTNERSTACK_API_KEY (zet in /root/felix_hq/.env, net als de GA4-creds).
Gebruik:
    set -a; . /root/felix_hq/.env; set +a
    python3 partnerstack_earnings.py --data /tmp/aibm_data.json
    python3 partnerstack_earnings.py --data ... --debug      # ruwe sample tonen
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from urllib.parse import urlparse, urlencode

API = "https://api.partnerstack.com/api/v2"
PREFIX_RE = re.compile(r"^(www|try|get|go|join|start|now|refer|partners?|affiliates?|psref)\.")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def host_root(link):
    try:
        h = urlparse(link).hostname or ""
    except Exception:
        return ""
    return PREFIX_RE.sub("", h)


def api_get(path, key, params=None, retries=3):
    """Praat via curl (urllib's TLS-fingerprint wordt door Cloudflare als bot
    geblokt, error 1010). Retry op 502/503/504 (PartnerStack-backend timeouts)."""
    url = f"{API}/{path}"
    if params:
        url += "?" + urlencode(params)
    cmd = ["curl", "-sS", "--max-time", "60", "-w", "\n%{http_code}",
           "-H", f"Authorization: Bearer {key}", "-H", "Accept: application/json",
           "-H", f"User-Agent: {UA}", url]
    for attempt in range(retries):
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = p.stdout.rsplit("\n", 1)
        body, code = (out[0], out[1].strip()) if len(out) == 2 else (p.stdout, "000")
        if code == "200":
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                raise SystemExit(f"❌ Geen geldige JSON van /{path}: {body[:200]}")
        if code in ("502", "503", "504") and attempt < retries - 1:
            time.sleep(3 * (attempt + 1))
            continue
        raise SystemExit(f"❌ PartnerStack HTTP {code} op /{path} "
                         f"(poging {attempt + 1}/{retries}): {body[:200]}")


def _rows(body):
    """PartnerStack v2: {'data': {'items': [...], 'has_more': bool}}."""
    d = body.get("data", body) if isinstance(body, dict) else body
    if isinstance(d, dict):
        return d.get("items", []), bool(d.get("has_more"))
    return (d or []), False


def fetch_all(path, key, limit=100):
    """Pagineer met starting_after op de 'key' van het laatste item."""
    out, after = [], None
    while True:
        params = {"limit": limit}
        if after:
            params["starting_after"] = after
        rows, more = _rows(api_get(path, key, params))
        if not rows:
            break
        out.extend(rows)
        after = rows[-1].get("key") or rows[-1].get("id")
        if not more or not after:
            break
    return out


# velden die (mogelijk) het programma/de vendor aanduiden, in volgorde van voorkeur.
# Partnerships/rewards dragen de vendor in company.name (bv. "Aira").
PROGRAM_FIELDS = ("company_name", "group_name", "product_name", "program_name")
NESTED = {"company": ("name",), "group": ("name", "slug"), "product": ("name",),
          "program": ("name",), "partnership": ("name", "group_name")}


def program_of(reward):
    for f in PROGRAM_FIELDS:
        if reward.get(f):
            return str(reward[f])
    for parent, subs in NESTED.items():
        node = reward.get(parent)
        if isinstance(node, dict):
            for s in subs:
                if node.get(s):
                    return str(node[s])
    return "(onbekend)"


def amount_of(reward):
    """PartnerStack-bedragen zijn meestal in centen (int). Val terug op float."""
    for f in ("amount", "commission_amount", "value"):
        if f in reward and reward[f] is not None:
            v = reward[f]
            return v / 100.0 if isinstance(v, int) else float(v)
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="pad naar de centrale data.json")
    ap.add_argument("--path", default="rewards", help="API-resource (rewards/transactions)")
    ap.add_argument("--debug", action="store_true", help="toon ruwe sample + alle keys")
    a = ap.parse_args()

    key = os.environ.get("PARTNERSTACK_API_KEY")
    if not key:
        sys.exit("❌ PARTNERSTACK_API_KEY niet gezet (source /root/felix_hq/.env)")

    rows = fetch_all(a.path, key)
    print(f"PartnerStack: {len(rows)} {a.path} opgehaald.")
    if not rows:
        return
    if a.debug:
        print("\n--- keys in eerste item ---")
        print(sorted(rows[0].keys()))
        print("\n--- ruwe sample ---")
        print(json.dumps(rows[0], indent=2)[:1500])
        return

    data = json.loads(open(a.data, encoding="utf-8").read())
    # bouw matchsleutels: genormaliseerde naam + domein-root
    by_name = {norm(t["name"]): t["name"] for t in data}
    by_dom = {norm(host_root(t.get("link", "")) or t.get("domain", "")): t["name"] for t in data}

    earn = defaultdict(float)
    cnt = defaultdict(int)
    for r in rows:
        earn[program_of(r)] += amount_of(r)
        cnt[program_of(r)] += 1

    matched, unmatched = {}, {}
    for prog, total in earn.items():
        pn = norm(prog)
        tool = by_name.get(pn) or by_dom.get(pn)
        if not tool:  # losse startswith-poging
            tool = next((nm for k, nm in by_name.items() if k and (k.startswith(pn) or pn.startswith(k))), None)
        (matched if tool else unmatched)[prog] = (tool, total, cnt[prog])

    print(f"\n💰 Verdiend per tool ({a.path}) — gematcht op data.json:")
    for prog, (tool, total, n) in sorted(matched.items(), key=lambda x: -x[1][1]):
        print(f"  {total:9.2f}  {tool:22} ({n}x, programma '{prog}')")
    if unmatched:
        print(f"\n⚠️  Niet-gematchte programma's (mapping nodig):")
        for prog, (_, total, n) in sorted(unmatched.items(), key=lambda x: -x[1]):
            print(f"  {total:9.2f}  '{prog}' ({n}x)")
    print(f"\nTotaal: {sum(v[1] for v in matched.values()) + sum(v[1] for v in unmatched.values()):.2f} "
          f"over {len(matched)} gematchte + {len(unmatched)} ongematchte programma's.")


if __name__ == "__main__":
    main()

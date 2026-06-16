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
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from urllib.parse import urlparse

API = "https://api.partnerstack.com/api/v2"
PREFIX_RE = re.compile(r"^(www|try|get|go|join|start|now|refer|partners?|affiliates?|psref)\.")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def host_root(link):
    try:
        h = urlparse(link).hostname or ""
    except Exception:
        return ""
    return PREFIX_RE.sub("", h)


def api_get(path, key, params=None):
    url = f"{API}/{path}"
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        # Cloudflare (error 1010) blokkeert de default Python-urllib UA als bot
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise SystemExit(f"❌ PartnerStack {e.code} op /{path}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"❌ Verbinding mislukt: {e}")


def fetch_all(path, key, limit=100):
    """Pagineer met starting_after op de 'key' van het laatste item."""
    out, after = [], None
    while True:
        params = {"limit": limit}
        if after:
            params["starting_after"] = after
        body = api_get(path, key, params)
        rows = body.get("data") if isinstance(body, dict) else body
        if not rows:
            break
        out.extend(rows)
        if len(rows) < limit:
            break
        last = rows[-1]
        after = last.get("key") or last.get("id")
        if not after:
            break
    return out


# velden die (mogelijk) het programma/de vendor aanduiden, in volgorde van voorkeur
PROGRAM_FIELDS = ("group_name", "product_name", "program_name", "partnership_name")
NESTED = {"group": ("name", "slug"), "product": ("name",), "program": ("name",),
          "partnership": ("name", "group_name")}


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

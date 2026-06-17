#!/usr/bin/env python3
"""Groeipiloot Fase 2 — herorden de AIBM-homepage-grid op werkelijke klikdata.

Haalt affiliate_click-klikken per `partner` uit GA4 (laatste 90 dagen), mapt ze
naar tools via de affiliate-link-hostnames in data.json (zelfde opschoning als de
client-side tracker), en herordent de tool-tegels in index.html zodat de best-
klikkende tools bovenaan de grid komen. Stabiel: tools zonder klikken behouden
hun onderlinge volgorde. Fase 2 = klikken; echte EPC (omzet) komt later.

Draait op de VPS (GA4-creds: GOOGLE_APPLICATION_CREDENTIALS + GA4_PROPERTY_ID,
net als groeipiloot). DRY-RUN default — toont de voorgestelde volgorde; --apply
schrijft + commit + pusht.

Gebruik:
    set -a; . /root/felix_hq/.env; set +a
    python3 rank_by_clicks.py --repo /root/felix_hq/repos/aibuildermarketplace --data /tmp/aibm_data.json
    python3 rank_by_clicks.py --repo ... --data ... --apply
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PREFIX_RE = re.compile(r"^(www|try|get|go|join|start|now|refer|partners?|affiliates?|psref)\.")


def partner_of(link):
    """Repliceer de tracker-opschoning: hostname minus bekende subdomein-prefix."""
    try:
        host = urlparse(link).hostname or ""
    except Exception:
        return ""
    return PREFIX_RE.sub("", host)


def ga4_clicks():
    prop = os.environ.get("GA4_PROPERTY_ID")
    if not prop:
        raise SystemExit("❌ GA4_PROPERTY_ID niet gezet (source /root/felix_hq/.env)")
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (RunReportRequest, DateRange, Dimension,
                                                     Metric, FilterExpression, Filter)
    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{prop}",
        date_ranges=[DateRange(start_date="90daysAgo", end_date="yesterday")],
        dimensions=[Dimension(name="customEvent:partner")],
        metrics=[Metric(name="eventCount")],
        dimension_filter=FilterExpression(filter=Filter(
            field_name="eventName", string_filter=Filter.StringFilter(value="affiliate_click"))),
        limit=250,
    )
    resp = client.run_report(req)
    return {r.dimension_values[0].value: int(r.metric_values[0].value) for r in resp.rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--data", required=True, help="pad naar de centrale data.json")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo)
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))

    # partner-waarde -> toolnaam
    partner2tool = {}
    for t in data:
        pv = partner_of(t.get("link", ""))
        if pv:
            partner2tool.setdefault(pv, t["name"])

    clicks_by_partner = ga4_clicks()
    tool_clicks = {}
    for pv, n in clicks_by_partner.items():
        tool = partner2tool.get(pv)
        if tool:
            tool_clicks[tool] = tool_clicks.get(tool, 0) + n

    ranked = sorted(tool_clicks.items(), key=lambda x: -x[1])
    print(f"GA4: {sum(clicks_by_partner.values())} affiliate-klikken over {len(clicks_by_partner)} partners "
          f"→ {len(tool_clicks)} tools gematcht (laatste 90d)")
    print("Top klikkers:")
    for name, n in ranked[:15]:
        print(f"  {n:5}  {name}")
    if not tool_clicks:
        print("\n(Geen klikdata gematcht — custom dimension verzamelt pas sinds vandaag. "
              "Niets te herordenen; draai later opnieuw.)")
        return

    idx = repo / "index.html"
    html = idx.read_text(encoding="utf-8")
    anchor = '<div class="tools-grid" id="tools-grid">'
    if anchor not in html:
        raise SystemExit("❌ tools-grid niet gevonden in index.html")
    i = html.index(anchor) + len(anchor)
    head, rest = html[:i], html[i:]
    ms = list(re.finditer(r'<article class="tool-card.*?</article>', rest, re.S))
    if not ms:
        raise SystemExit("❌ geen tool-cards gevonden")
    head_re = re.compile(r'<div class="tools-section-head"[^>]*data-group="([a-z]+)"[^>]*>.*?</div>', re.S)
    heads = {m.group(1): m.group(0) for m in head_re.finditer(rest)}

    def name_of(card):
        h = re.search(r"<h3>([^<]+)</h3>", card)
        return (h.group(1).strip() if h else "")

    def clicks_of(card):
        return tool_clicks.get(name_of(card), 0)

    def group_of(card):
        g = re.search(r'data-group="([a-z]+)"', card)
        return g.group(1) if g else "support"

    cards = [m.group(0) for m in ms]

    # Sorteer BINNEN elke sectie-groep (ai/support) en behoud de sectiekoppen,
    # zodat de "AI Tools"/"Business Support"-indeling intact blijft.
    if "ai" in heads and "support" in heads:
        start = min(ms[0].start(), min(m.start() for m in head_re.finditer(rest)))
        end = ms[-1].end()
        pre, tail = rest[:start], rest[end:]
        groups = {"ai": [], "support": []}
        for c in cards:
            groups.get(group_of(c), groups["support"]).append(c)
        new_groups = {g: sorted(cs, key=lambda c: -clicks_of(c)) for g, cs in groups.items()}
        if all(new_groups[g] == groups[g] for g in groups):
            print("\nVolgorde is al optimaal — niets te wijzigen.")
            return
        moved = [name_of(c) for c in (new_groups["ai"] + new_groups["support"])[:8]]
        print(f"\nNieuwe top-8 (per groep gesorteerd): {moved}")
        if not a.apply:
            print("\nDRY-RUN — draai met --apply om de grid te herordenen + pushen.")
            return
        block = (heads["ai"] + "\n" + "\n".join(new_groups["ai"]) + "\n"
                 + heads["support"] + "\n" + "\n".join(new_groups["support"]))
        new_html = head + pre + block + tail
    else:
        # fallback (geen sectiekoppen): sorteer alles, oude gedrag
        new_cards = sorted(cards, key=lambda c: -clicks_of(c))
        if new_cards == cards:
            print("\nVolgorde is al optimaal — niets te wijzigen.")
            return
        print(f"\nNieuwe top-8 van de grid: {[name_of(c) for c in new_cards[:8]]}")
        if not a.apply:
            print("\nDRY-RUN — draai met --apply om de grid te herordenen + pushen.")
            return
        new_html = head + rest[:ms[0].start()] + "\n".join(new_cards) + rest[ms[-1].end():]
    idx.write_text(new_html, encoding="utf-8")

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    git("add", "index.html")
    git("commit", "-m", "Groeipiloot F2: reorder homepage grid by 90d affiliate clicks\n\n"
                        "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>")
    git("pull", "--no-rebase", "-X", "ours", "origin", "main", "--no-edit")
    p = git("push", "origin", "HEAD:main")
    print((p.stdout + p.stderr)[-300:])


if __name__ == "__main__":
    main()

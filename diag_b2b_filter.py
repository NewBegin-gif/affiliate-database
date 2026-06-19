#!/usr/bin/env python3
"""READ-ONLY diagnose: hoe genereert Victor de b2b-filter (TOOL:-knoppen)?

Doel: opsporen waar de tool-namen voor de filter-btn / data-tool vandaan komen,
zodat we Aspire er blijvend in kunnen patchen. Schrijft NIETS.

Draai op de VPS:  python3 /root/felix_hq/repos/affiliate-database/diag_b2b_filter.py
(of waar dit affdb-script ook staat). Plak de volledige output terug.
"""
import os
import re
import json

AGENT = "/root/felix_hq/felix_ceo_agent.py"
COMPETITORS = "/root/felix_hq/victor_competitors.json"
REPO = "/root/felix_hq/repos/aibuildermarketplace"
B2B = os.path.join(REPO, "b2b")
INDEX = os.path.join(B2B, "index.html")


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# 1) Bestaat de aspire-review folder in de VPS-repo?
hr("1. aspire-review folder in VPS-repo?")
if os.path.isdir(B2B):
    aspire = [f for f in os.listdir(B2B) if "aspire" in f.lower()]
    print("aspire-folders in b2b/:", aspire or "GEEN")
    print("totaal b2b-folders:", len([f for f in os.listdir(B2B) if os.path.isdir(os.path.join(B2B, f))]))
else:
    print("b2b/ niet gevonden op", B2B)

# 2) victor_competitors.json
hr("2. victor_competitors.json (merken/tools die Victor kent)")
if os.path.exists(COMPETITORS):
    try:
        data = json.load(open(COMPETITORS))
        print("type:", type(data).__name__)
        s = json.dumps(data, ensure_ascii=False, indent=1)
        print(s[:3000])
        if len(s) > 3000:
            print(f"... (+{len(s)-3000} tekens ingekort)")
        # bevat het Aspire?
        print("\nbevat 'aspire' (case-insensitive):", "aspire" in s.lower())
    except Exception as e:
        print("kon JSON niet lezen:", e)
else:
    print("bestaat niet:", COMPETITORS)

# 3) Hoe bouwt felix_ceo_agent.py de filter-knoppen / data-tool?
hr("3. Generator-logica in felix_ceo_agent.py")
if os.path.exists(AGENT):
    src = open(AGENT, encoding="utf-8", errors="replace").read()
    print("bestandsgrootte:", len(src), "tekens /", src.count("\n") + 1, "regels")
    patterns = [
        r"filter-btn",
        r"filterTool",
        r"data-tool",
        r"def\s+\w*get_tool\w*",
        r"def\s+\w*tool\w*\(",
        r"def\s+\w*b2b\w*\(",
        r"def\s+\w*index\w*\(",
        r"def\s+\w*rebuild\w*\(",
        r"COMPETITORS",
        r"victor_competitors",
        r"BRANDS|KNOWN_TOOLS|TOOL_LIST|ALL_TOOLS",
        r"b2b/index\.html",
        r"aspire",
    ]
    lines = src.split("\n")
    for pat in patterns:
        rx = re.compile(pat, re.I)
        hits = [(i + 1, l.strip()[:130]) for i, l in enumerate(lines) if rx.search(l)]
        print(f"\n--- /{pat}/  ({len(hits)} hits) ---")
        for ln, txt in hits[:12]:
            print(f"  {ln}: {txt}")
        if len(hits) > 12:
            print(f"  ... (+{len(hits)-12} meer)")
else:
    print("agent niet gevonden:", AGENT)

# 4) Welke tools staan nu in de live filter (uit index.html)?
hr("4. Huidige filter-knoppen in b2b/index.html")
if os.path.exists(INDEX):
    html = open(INDEX, encoding="utf-8", errors="replace").read()
    tools = re.findall(r"filterTool\(this,'([^']+)'\)", html)
    tools = [t for t in tools if t != "all"]
    print(f"{len(tools)} tool-knoppen. Aspire aanwezig: {'Aspire' in tools}")
    print("eerste 20:", tools[:20])
    # is er een marker/placeholder voor injectie?
    print("\n'const CARDS' aanwezig:", "const CARDS" in html)
    print("aantal <a class=\"card\">:", html.count('class="card"'))
else:
    print("index.html niet gevonden:", INDEX)

hr("KLAAR — plak alle output hierboven terug")

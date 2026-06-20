#!/usr/bin/env python3
"""diag_junk_titles2.py — READ-ONLY. Definitief vaststellen of de
'evaluate the cryptocurrency company ... on pro platform - nb/- brand'-regels
ECHTE pagina-titels zijn (onze bug) of externe zoekopdrachten (geen bug).

Scant ALLE repos onder /root/felix_hq/repos:
  - per repo: b2b-map gevonden? aantal index.html?
  - titles/h1 met het junk-patroon (per repo, met [INDEXED]/[noindex]);
  - grep pagina-BODY's op de letterlijke frase 'evaluate the cryptocurrency'
    en 'on pro platform' (komt de tekst überhaupt ergens op de site voor?).

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/diag2.py
"""
import re
from pathlib import Path

ROOT = Path("/root/felix_hq/repos")
junk_re = re.compile(r"evaluate the cryptocurrency| on pro (platform|margin|futures|product)| - nb\b| - br\b| - brand\b|is it evaluate", re.I)
body_re = re.compile(r"evaluate the cryptocurrency|on pro platform|on pro margin", re.I)

print("=" * 72)
print("Repos onder", ROOT)
print("=" * 72)
if not ROOT.exists():
    print("✗ map bestaat niet — geef het juiste repos-pad door"); raise SystemExit(0)

total_junk = 0
total_body = 0
for repo in sorted(ROOT.iterdir()):
    if not repo.is_dir():
        continue
    b2b = repo / "b2b"
    pages = list(b2b.rglob("index.html")) if b2b.is_dir() else []
    print(f"\n### {repo.name}  (b2b: {'ja' if b2b.is_dir() else 'NEE'}, {len(pages)} pagina's)")
    junk_here = []
    body_here = []
    for f in pages:
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        tm = re.search(r"<title>(.*?)</title>", t, re.S | re.I)
        hm = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S | re.I)
        title = (tm.group(1).strip() if tm else "")
        h1 = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else ""
        if junk_re.search(title) or junk_re.search(h1):
            junk_here.append((f.parent.name, "noindex" if "noindex" in t.lower() else "INDEXED", title[:110]))
        if body_re.search(t):
            body_here.append(f.parent.name)
    for name, idx, title in junk_here[:40]:
        print(f"   [{idx}] {name}: {title}")
    if junk_here:
        print(f"   → junk-titels in deze repo: {len(junk_here)}")
    if body_here:
        print(f"   → pagina's met de frase IN DE BODY: {len(body_here)} (bv. {body_here[:5]})")
    total_junk += len(junk_here)
    total_body += len(body_here)

print("\n" + "=" * 72)
print(f"TOTAAL junk-TITELS over alle repos: {total_junk}")
print(f"TOTAAL pagina's met de frase in de body: {total_body}")
print("Als beide 0 → het zijn externe zoekopdrachten, GEEN titel-bug.")
print("=" * 72)
print("KLAAR — plak alles terug.")

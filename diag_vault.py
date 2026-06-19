#!/usr/bin/env python3
"""READ-ONLY diagnose: wat zit er in Victors VAULT / TOPICS / COMPETITORS /
hero-lijst? Schrijft NIETS. Output terugplakken.
"""
import re, glob, os, importlib.util, sys

AG = "/root/felix_hq/generate_article.py"


def hr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# VAULT / TOPICS / COMPETITORS via AST-vrije import is riskant (module-side effects),
# dus we parsen de dict-keys met regex uit de broncode.
src = open(AG, encoding="utf-8").read()


def dict_keys(name):
    # vind 'NAME = {' en pak de top-level keys tot de matchende '}'
    m = re.search(rf"\n{name}\s*=\s*\{{", src)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    keys = []
    buf = src[i:]
    # scan tekens, verzamel keys op depth==1
    d = 0
    j = 0
    while j < len(buf):
        c = buf[j]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                break
        elif d == 1 and c in "\"'":
            q = c
            k = j + 1
            while k < len(buf) and buf[k] != q:
                k += 1
            key = buf[j+1:k]
            # alleen keys (gevolgd door ':'); sla waarden-strings over
            after = buf[k+1:k+40].lstrip()
            if after.startswith(":"):
                keys.append(key)
            j = k
        j += 1
    # dedup met behoud volgorde
    seen = set()
    return [x for x in keys if not (x in seen or seen.add(x))]


for nm in ["VAULT", "TOPICS", "COMPETITORS"]:
    k = dict_keys(nm)
    hr(f"{nm}: {len(k) if k else 0} keys")
    if k:
        print("  " + ", ".join(sorted(k, key=str.lower)))

# Hero / hands-on lijst: zoek inject_verdict_box.py (HEROES dict) + bestaande -review folders
hr("HERO / hands-on bronnen")
ivb = None
for p in ["/root/felix_hq/inject_verdict_box.py"] + glob.glob("/root/felix_hq/**/inject_verdict_box.py", recursive=True):
    if os.path.exists(p): ivb = p; break
print("inject_verdict_box.py:", ivb)
if ivb:
    s = open(ivb, encoding="utf-8").read()
    m = re.search(r"HEROES\s*=\s*\{(.*?)\n\}", s, re.S) or re.search(r"HEROES\s*=\s*\[(.*?)\]", s, re.S)
    if m:
        keys = re.findall(r'["\']([A-Za-z0-9 .&\-]+)["\']\s*:', m.group(1))
        print(f"HEROES ({len(keys)}):", ", ".join(sorted(set(keys), key=str.lower)))
    else:
        print("HEROES-dict niet herkend; eerste 400 tekens rond 'HEROES':")
        mm = re.search(r".{40}HEROES.{400}", s, re.S)
        print(mm.group(0) if mm else "(niet gevonden)")

# bestaande hand-built hero-pagina's (proxy: /b2b/<x>-review/ en bekende slugs)
REPO = "/root/felix_hq/repos/aibuildermarketplace/b2b"
if os.path.isdir(REPO):
    reviews = sorted(f for f in os.listdir(REPO) if f.endswith("-review") or f.endswith("-ai-review") or f.endswith("-review-2026"))
    print(f"\n/b2b/*-review folders ({len(reviews)}):")
    print("  " + ", ".join(reviews))

hr("KLAAR — plak alles terug")

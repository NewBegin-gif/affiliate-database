#!/usr/bin/env python3
"""fix_fake_rating.py — verwijder de gefabriceerde ster-rating (sync_vault-default
"4.6" + hardcoded "4.9") uit de B2B-reviews. ECHTE scores (alles ≠ 4.6/4.9 in de
review_template AFFILIATE-dict + de hand-gebouwde hero's) blijven onaangeroerd.

A) TEMPLATES (zodat nieuwe pagina's geen nep-rating meer krijgen)
   - review_template.py : gate `_genuine_rating` (rating ∉ {"", "4.6"}); rating weg
     uit meta, verdict-kaart, sticky-card, mobiel-card en Review-schema als niet-echt.
     Verdict-stats grid → auto-fit (vangt 2 stats netjes op).
   - generate_article.py: verwijder de hardcoded `"ratingValue": "4.9"` reviewRating.
   Per bestand: backup + py_compile (auto-revert bij syntaxfout).

B) BACKFILL bestaande ~1700 b2b-pagina's (regex, geankerd op 4.6/4.9 → echte
   scores blijven): Review-schema reviewRating, zichtbare verdict-stat (incl. de
   "Based on N reviews"-sub), sticky .sc-rating, mobiel .mc-rating (prijs blijft),
   meta-description "4.6★ …,", en de verdict-stats grid → auto-fit.

Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/ffr.py            # dry-run (niets schrijven)
  /root/felix_hq/venv/bin/python3 /tmp/ffr.py --apply
"""
import sys, re, shutil, datetime, py_compile, subprocess
from pathlib import Path

APPLY = "--apply" in sys.argv
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
HQ = "/root/felix_hq"
REPO = Path(HQ) / "repos" / "aibuildermarketplace"
B2B = REPO / "b2b"

# ───────────────────────── A) TEMPLATE-PATCHES ─────────────────────────
RT = HQ + "/review_template.py"
GA = HQ + "/generate_article.py"

rt_meta_old = (
    "    # Meta description\n"
    "    description = L['meta_description'].format(\n"
    "        title=title, rating=aff['rating'], price=aff['price'], tagline=aff['tagline']\n"
    "    )[:160]"
)
rt_meta_new = (
    "    # Honest-rating gate: legacy sync_vault default \"4.6\" is geen echte score.\n"
    "    _genuine_rating = str(aff.get(\"rating\", \"\")).strip() not in (\"\", \"4.6\")\n\n"
    "    # Meta description\n"
    "    description = L['meta_description'].format(\n"
    "        title=title, rating=aff['rating'], price=aff['price'], tagline=aff['tagline']\n"
    "    )[:160]\n"
    "    if not _genuine_rating:\n"
    "        import re as _re_rt\n"
    "        description = _re_rt.sub(_re_rt.escape(str(aff['rating'])) + r\"★\\s*[^,，、،\\\"<]{0,24}[,，、،]\\s*\", \"\", description)\n"
    "        description = _re_rt.sub(r\"\\s{2,}\", \" \", description).strip()"
)

rt_stars_old = (
    "    # Star rating display\n"
    "    rating_val = float(aff[\"rating\"])\n"
    "    full_stars = int(rating_val)\n"
    "    half = 1 if (rating_val - full_stars) >= 0.5 else 0\n"
    "    empty = 5 - full_stars - half\n"
    "    stars_html = \"★\" * full_stars + (\"⯨\" if half else \"\") + \"☆\" * empty"
)
rt_stars_new = rt_stars_old + (
    "\n    if _genuine_rating:\n"
    "        _vstat_rating = f'<div class=\"vstat\"><div class=\"vstat-lbl\">{L[\"rating\"]}</div>"
    "<div class=\"vstat-val\"><span class=\"stars\" aria-label=\"{aff[\"rating\"]} out of 5\">{stars_html}</span> "
    "<strong>{aff[\"rating\"]}</strong></div><div class=\"vstat-sub\">{L[\"based_on\"].format(reviews=aff[\"reviews\"])}</div></div>'\n"
    "        _sc_rating = f'<div class=\"sc-rating\"><span class=\"stars\">{stars_html}</span> {aff[\"rating\"]}/5</div>'\n"
    "        _mc_rating = f'{stars_html} {aff[\"rating\"]} · {aff[\"price\"]}'\n"
    "    else:\n"
    "        _vstat_rating = \"\"\n"
    "        _sc_rating = \"\"\n"
    "        _mc_rating = aff[\"price\"]"
)

rt_vstat_old = (
    "    <div class=\"vstat\"><div class=\"vstat-lbl\">{L['rating']}</div><div class=\"vstat-val\">"
    "<span class=\"stars\" aria-label=\"{aff['rating']} out of 5\">{stars_html}</span> "
    "<strong>{aff['rating']}</strong></div><div class=\"vstat-sub\">{L['based_on'].format(reviews=aff['reviews'])}</div></div>"
)
rt_vstat_new = "    {_vstat_rating}"

rt_sc_old = "  <div class=\"sc-rating\"><span class=\"stars\">{stars_html}</span> {aff['rating']}/5</div>"
rt_sc_new = "  {_sc_rating}"

rt_mc_old = "    <div class=\"mc-rating\">{stars_html} {aff['rating']} · {aff['price']}</div>"
rt_mc_new = "    <div class=\"mc-rating\">{_mc_rating}</div>"

rt_schema_old = (
    "    review_schema = json.dumps({\n"
    "        \"@context\": \"https://schema.org\",\n"
    "        \"@type\": \"Review\",\n"
    "        \"itemReviewed\": {\n"
    "            \"@type\": \"SoftwareApplication\",\n"
    "            \"name\": brand1,\n"
    "            \"applicationCategory\": aff[\"category\"],\n"
    "            \"offers\": {\"@type\": \"Offer\", \"price\": aff[\"price\"], \"priceCurrency\": \"USD\"},\n"
    "        },\n"
    "        \"reviewRating\": {\n"
    "            \"@type\": \"Rating\",\n"
    "            \"ratingValue\": aff[\"rating\"],\n"
    "            \"bestRating\": \"5\",\n"
    "        },"
)
rt_schema_new = (
    "    _rr = {\"reviewRating\": {\"@type\": \"Rating\", \"ratingValue\": aff[\"rating\"], \"bestRating\": \"5\"}} if _genuine_rating else {}\n"
    "    review_schema = json.dumps({\n"
    "        \"@context\": \"https://schema.org\",\n"
    "        \"@type\": \"Review\",\n"
    "        \"itemReviewed\": {\n"
    "            \"@type\": \"SoftwareApplication\",\n"
    "            \"name\": brand1,\n"
    "            \"applicationCategory\": aff[\"category\"],\n"
    "            \"offers\": {\"@type\": \"Offer\", \"price\": aff[\"price\"], \"priceCurrency\": \"USD\"},\n"
    "        },\n"
    "        **_rr,"
)

rt_css_old = ".verdict-stats{{display:grid;grid-template-columns:repeat(3,1fr)"
rt_css_new = ".verdict-stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr))"

RT_EDITS = [
    ("meta+gate", rt_meta_old, rt_meta_new),
    ("stars+helpers", rt_stars_old, rt_stars_new),
    ("verdict-stat", rt_vstat_old, rt_vstat_new),
    ("sticky-card", rt_sc_old, rt_sc_new),
    ("mobile-card", rt_mc_old, rt_mc_new),
    ("review-schema", rt_schema_old, rt_schema_new),
    ("stats-grid-css", rt_css_old, rt_css_new),
]

ga_old = "\n            \"reviewRating\": {\"@type\": \"Rating\", \"ratingValue\": \"4.9\"}"
ga_new = ""


def patch_template(path, edits):
    try:
        src = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"  ✗ {path}: niet gevonden"); return False
    new = src
    allok = True
    for name, old, repl in edits:
        if repl in new and old not in new:
            print(f"    = {name}: al gepatcht")
            continue
        c = new.count(old)
        if c == 0:
            print(f"    ✗ {name}: anchor NIET gevonden"); allok = False; continue
        print(f"    ✓ {name}: {c}x")
        new = new.replace(old, repl)
    if not allok:
        print(f"  ✗ {path.split('/')[-1]}: niet alle anchors gevonden — NIET geschreven")
        return False
    if new == src:
        print(f"  = {path.split('/')[-1]}: niets te wijzigen"); return True
    if not APPLY:
        return True
    bak = f"{path}.bak-{STAMP}"; shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(path, doraise=True)
        print(f"  ✓ {path.split('/')[-1]}: geschreven, backup {bak}")
        return True
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, path)
        print(f"  ✗ {path.split('/')[-1]}: SYNTAXFOUT — teruggezet: {e}")
        return False


print("=" * 60)
print("A) TEMPLATES" + ("  [DRY-RUN]" if not APPLY else "  [APPLY]"))
print("=" * 60)
print("  review_template.py:")
patch_template(RT, RT_EDITS)
print("  generate_article.py:")
patch_template(GA, [("hardcoded-4.9", ga_old, ga_new)])

# ───────────────────────── B) BACKFILL b2b-pagina's ─────────────────────────
print("\n" + "=" * 60)
print("B) BACKFILL b2b-pagina's" + ("  [DRY-RUN]" if not APPLY else "  [APPLY]"))
print("=" * 60)

# Regex, geankerd op 4.6/4.9 (echte scores blijven)
re_schema46 = re.compile(r',?\s*"reviewRating":\s*\{[^{}]*"ratingValue":\s*"4\.6"[^{}]*\}')
re_schema49 = re.compile(r',?\s*"reviewRating":\s*\{[^{}]*"ratingValue":\s*"4\.9"[^{}]*\}', re.S)
re_vstat = re.compile(
    r'<div class="vstat"><div class="vstat-lbl">[^<]*</div>'
    r'<div class="vstat-val"><span class="stars" aria-label="4\.6 out of 5">[^<]*</span>\s*'
    r'<strong>4\.6</strong></div><div class="vstat-sub">[^<]*</div></div>')
re_sc = re.compile(r'<div class="sc-rating"><span class="stars">[^<]*</span>\s*4\.6/5</div>')
re_mc = re.compile(r'<div class="mc-rating">[★⯨☆\s]*4\.6 · ([^<]*)</div>')
re_meta = re.compile(r'4\.6★\s*[^,，、،"<]{0,24}[,，、،]\s*')
CSS_OLD = ".verdict-stats{display:grid;grid-template-columns:repeat(3,1fr)"
CSS_NEW = ".verdict-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(88px,1fr))"

pages = sorted(B2B.glob("*/index.html"))
counts = {"schema4.6": 0, "schema4.9": 0, "vstat": 0, "sticky": 0, "mobile": 0, "meta": 0, "css": 0}
changed_files = 0
for f in pages:
    t = f.read_text(encoding="utf-8", errors="ignore")
    o = t
    t, n = re_schema46.subn("", t); counts["schema4.6"] += n
    t, n = re_schema49.subn("", t); counts["schema4.9"] += n
    t, n = re_vstat.subn("", t); counts["vstat"] += n
    t, n = re_sc.subn("", t); counts["sticky"] += n
    t, n = re_mc.subn(r'<div class="mc-rating">\1</div>', t); counts["mobile"] += n
    t, n = re_meta.subn("", t); counts["meta"] += n
    removed_vstat = re_vstat.search(o) is not None
    if removed_vstat and CSS_OLD in t:
        t = t.replace(CSS_OLD, CSS_NEW); counts["css"] += 1
    if t != o:
        changed_files += 1
        if APPLY:
            f.write_text(t, encoding="utf-8")

print(f"  pagina's gescand : {len(pages)}")
for k, v in counts.items():
    print(f"  {k:11s}: {v}")
print(f"  bestanden gewijzigd: {changed_files}")

if not APPLY:
    print("\nDRY-RUN — niets geschreven. Draai met --apply.")
    sys.exit(0)

# ───────────────────────── git push (alleen b2b-pagina's) ─────────────────────────
if changed_files:
    def git(*a):
        return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
    git("add", "--", "b2b")
    git("commit", "-m", f"Eerlijkheid: verwijder gefabriceerde 4.6/4.9 ster-rating uit {changed_files} b2b-reviews (schema+zichtbaar+meta); echte scores blijven")
    git("pull", "--no-rebase", "-X", "ours", "origin", "main")
    p1 = git("push", "origin", "HEAD:main"); print("\npush main    :", (p1.stdout + p1.stderr).strip()[-160:])
    p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-160:])
print("\nKLAAR — plak alles terug.")

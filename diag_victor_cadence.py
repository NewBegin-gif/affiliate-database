#!/usr/bin/env python3
"""diag_victor_cadence.py — READ-ONLY. Hoe snel en hoe genereert Victor?
Nodig om de generatie te temperen (de bron van dunne massa).

Rapporteert:
  1) GENERATIE-TEMPO: # b2b-pagina's aangemaakt per week (uit git-historie,
     diff-filter=A; mtimes zijn nutteloos na de hreflang-herschrijving).
  2) LEEFTIJD vs VERTONINGEN: hoeveel pagina's >45d/>90d oud zijn met 0
     vertoningen (de écht-dode set) vs recent (verdient nog tijd).
  3) TAALVERDELING van alle pagina's en van de laatste 45 dagen.
  4) CONFIG in generate_article.py: talenlijst, EN_BIAS, per-run-volume,
     modes, brand/taal-keuzelogica.
  5) CRON/cadans: hoe vaak draait de generator.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/cadence.py
"""
import re, subprocess, datetime, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
AG = "/root/felix_hq/generate_article.py"
LANG_SUF = set("en fr du po ge sp it pl sv da no ja tr id vi br mx uk zh ko hi ar th ru cs fi el hu ro sw ha yo am af zu".split())
today = datetime.date.today()


def lang_of(slug):
    i = slug.rfind("-")
    suf = slug[i+1:] if i != -1 else ""
    return suf if suf in LANG_SUF else "en"


# ---------- 1) creatie-datum per b2b/index.html uit git ----------
print("Git-historie uitlezen (creatie-datums)…", file=sys.stderr)
r = subprocess.run(
    ["git", "-C", str(REPO), "log", "--diff-filter=A", "--date=short",
     "--format=D %ad", "--name-only", "--", "b2b"],
    capture_output=True, text=True)
created = {}  # slug -> date (eerste add)
curdate = None
for line in r.stdout.splitlines():
    if line.startswith("D "):
        curdate = line[2:].strip()
    elif line.endswith("/index.html") and curdate:
        m = re.match(r"b2b/([^/]+)/index\.html$", line)
        if m and m.group(1) not in created:
            created[m.group(1)] = curdate

# ---------- 2) GSC 90d impressies per pagina ----------
impr = {}
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    creds = service_account.Credentials.from_service_account_file(
        "/root/felix_hq/gcp_credentials.json",
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    end = today - datetime.timedelta(days=1); start = end - datetime.timedelta(days=90)
    rows = svc.searchanalytics().query(siteUrl="sc-domain:aibuildermarketplace.com", body={
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": ["page"], "rowLimit": 25000}).execute().get("rows", [])
    for x in rows:
        u = x["keys"][0]
        if "/b2b/" in u:
            impr[u.rstrip("/").rsplit("/b2b/", 1)[-1]] = int(x["impressions"])
except Exception as e:
    print("GSC niet beschikbaar:", e)

# ---------- rapport ----------
all_slugs = [d.name for d in (REPO / "b2b").iterdir() if d.is_dir()]
print("\n" + "=" * 72)
print(f"b2b-pagina's: {len(all_slugs)} | met git-creatiedatum: {len(created)} | met GSC-impr(90d): {len(impr)}")
print("=" * 72)

# 1) tempo per week (laatste 16 weken)
def age_days(slug):
    d = created.get(slug)
    if not d:
        return None
    return (today - datetime.date.fromisoformat(d)).days

week_counts = Counter()
for s in all_slugs:
    a = age_days(s)
    if a is not None and a <= 16 * 7:
        week_counts[a // 7] += 1
print("\n### 1) GENERATIE-TEMPO (pagina's aangemaakt, per week terug):")
for w in range(0, 16):
    bar = "█" * (week_counts.get(w, 0) // 5)
    print(f"   {w:2d} weken geleden: {week_counts.get(w,0):4d}  {bar}")

# 2) leeftijd vs vertoningen
buckets = {"<45d": [0, 0], "45-90d": [0, 0], ">90d": [0, 0], "geen-datum": [0, 0]}
for s in all_slugs:
    a = age_days(s)
    key = "geen-datum" if a is None else ("<45d" if a < 45 else ("45-90d" if a <= 90 else ">90d"))
    buckets[key][0] += 1
    if impr.get(s, 0) == 0:
        buckets[key][1] += 1
print("\n### 2) LEEFTIJD vs 0-VERTONINGEN (de écht-dode set = oud + 0 impr):")
for k, (tot, dead) in buckets.items():
    print(f"   {k:10}: {tot:5d} pagina's, waarvan {dead:5d} met 0 vertoningen (90d)")

# 3) taalverdeling
all_lang = Counter(lang_of(s) for s in all_slugs)
recent_lang = Counter(lang_of(s) for s in all_slugs if (age_days(s) is not None and age_days(s) < 45))
print("\n### 3) TAALVERDELING (alle | laatste 45d):")
langs = sorted(all_lang, key=lambda l: -all_lang[l])
for l in langs[:14]:
    print(f"   {l:4}: {all_lang[l]:4d} totaal | {recent_lang.get(l,0):3d} laatste 45d")
print(f"   ... {len(langs)} talen totaal")

# 4) generate_article.py config
print("\n### 4) CONFIG in generate_article.py (relevante regels):")
try:
    lines = open(AG, encoding="utf-8").read().split("\n")
    pat = re.compile(r"EN_BIAS|LANG_CODES\s*=|LANGS\s*=|languages\s*=|MODES\s*=|"
                     r"random\.choice|random\.sample|for .* in range\(|num_articles|"
                     r"ARTICLES_PER|COUNT|weighted|\.shuffle", re.I)
    shown = 0
    for i, l in enumerate(lines):
        if pat.search(l) and shown < 40:
            print(f"   L{i+1}: {l.strip()[:120]}")
            shown += 1
except Exception as e:
    print("   kon generate_article.py niet lezen:", e)

# 5) cron
print("\n### 5) CRON / cadans:")
for cmd in (["crontab", "-l"], ["bash", "-lc", "ls -1 /etc/cron.d/ 2>/dev/null"]):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        for l in out.splitlines():
            if l.strip() and ("felix" in l.lower() or "generate" in l.lower() or "victor" in l.lower() or "*" in l):
                print("   " + l.strip()[:120])
    except Exception:
        pass

print("\nKLAAR — plak alles terug.")

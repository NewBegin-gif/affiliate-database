#!/usr/bin/env python3
"""prune_dead_pages.py — zet dode b2b-pagina's op noindex om autoriteit te
concentreren (Helpful-Content: massa dunne content drukt de hele site).

Een pagina is "dood" als ze in 90 dagen 0 impressies kreeg. Veiligheidsrails:
  - 90-daags venster (niet 28) → seizoens/zeldzame impressies blijven gespaard
  - recent toegevoegde folders (laatste 45 dagen, incl. de 44 nieuwe -en) BESCHERMD
  - pagina's met clicks/impressies of al-noindexed → overgeslagen
  - alleen /b2b/-folders; alternatives/best/finder etc. blijven ongemoeid

Dry-run default. Draai met venv:
  /root/felix_hq/venv/bin/python3 /tmp/prune_dead_pages.py            # rapport
  /root/felix_hq/venv/bin/python3 /tmp/prune_dead_pages.py --apply    # noindex + push
"""
import os
import re
import sys
import subprocess
import datetime as dt

KEY = "/root/felix_hq/gcp_credentials.json"
REPO = "/root/felix_hq/repos/aibuildermarketplace"
B2B = os.path.join(REPO, "b2b")
SITE = "sc-domain:aibuildermarketplace.com"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DAYS = 90
PROTECT_DAYS = 45
APPLY = "--apply" in sys.argv


def hr(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ── 1) GSC: pagina's met impressies in 90d ────────────────────────────────
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
end = dt.date.today() - dt.timedelta(days=1)
start = end - dt.timedelta(days=DAYS - 1)
rows = svc.searchanalytics().query(siteUrl=SITE, body=dict(
    startDate=start.isoformat(), endDate=end.isoformat(),
    dimensions=["page"], rowLimit=25000, dataState="all")).execute().get("rows", [])


def slug_of(url):
    m = re.search(r"/b2b/([^/]+)/?", url)
    return m.group(1) if m else None


alive = set()
for r in rows:
    s = slug_of(r["keys"][0])
    if s:
        alive.add(s)
hr(f"1. GSC {DAYS}d: {len(alive)} b2b-pagina's met impressies")

# ── 2) recent toegevoegde folders beschermen ──────────────────────────────
since = (dt.date.today() - dt.timedelta(days=PROTECT_DAYS)).isoformat()
out = subprocess.run(["git", "-C", REPO, "log", f"--since={since}", "--diff-filter=A",
                      "--name-only", "--pretty=format:"], capture_output=True, text=True).stdout
recent = set()
for line in out.splitlines():
    m = re.match(r"b2b/([^/]+)/index\.html$", line.strip())
    if m:
        recent.add(m.group(1))
print(f"   beschermd (toegevoegd < {PROTECT_DAYS}d): {len(recent)} folders")

# ── 3) alle b2b-folders → bepaal dode set ─────────────────────────────────
folders = [f for f in os.listdir(B2B) if os.path.isdir(os.path.join(B2B, f)) and f != ".git"]
NOINDEX = '<meta name="robots" content="noindex,follow">'
candidates, already, missing = [], 0, 0
for f in folders:
    if f in alive or f in recent:
        continue
    idx = os.path.join(B2B, f, "index.html")
    if not os.path.exists(idx):
        missing += 1
        continue
    html = open(idx, encoding="utf-8", errors="replace").read()
    if 'content="noindex' in html:
        already += 1
        continue
    candidates.append(f)

hr("2. RESULTAAT")
print(f"  totaal b2b-folders     : {len(folders)}")
print(f"  levend (impr 90d)      : {len(alive)}")
print(f"  beschermd (recent)     : {len(recent)}")
print(f"  al noindex             : {already}")
print(f"  >>> NOINDEX-kandidaten : {len(candidates)}")
print("\n  steekproef (20):")
for f in candidates[:20]:
    print("   ", f)

if not APPLY:
    print("\nDRY-RUN — niets gewijzigd. Draai met --apply om te noindexen + pushen.")
    sys.exit(0)

# ── 4) noindex injecteren ─────────────────────────────────────────────────
changed = 0
for f in candidates:
    idx = os.path.join(B2B, f, "index.html")
    html = open(idx, encoding="utf-8", errors="replace").read()
    if 'content="noindex' in html:
        continue
    # vervang bestaande index,follow indien aanwezig, anders injecteer in <head>
    if re.search(r'<meta name="robots"[^>]*>', html):
        html2 = re.sub(r'<meta name="robots"[^>]*>', NOINDEX, html, count=1)
    elif "<head>" in html:
        html2 = html.replace("<head>", "<head>\n" + NOINDEX, 1)
    else:
        continue
    if html2 != html:
        open(idx, "w", encoding="utf-8").write(html2)
        changed += 1

print(f"\n  noindex gezet op {changed} pagina's")


def git(*a):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
    print("  git", a[0], "->", (r.stdout + r.stderr).strip()[:200])
    return r


git("add", "-A")
git("commit", "-m", f"SEO prune: noindex {changed} zero-impression b2b pages (90d)")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
git("push", "origin", "HEAD:main")
git("push", "origin", "HEAD:victor-staging")
print("\n✅ KLAAR. Dode pagina's op noindex → autoriteit concentreert op de pagina's die ranken.")

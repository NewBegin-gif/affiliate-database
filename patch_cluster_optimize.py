#!/usr/bin/env python3
"""patch_cluster_optimize.py — on-page-optimalisatie van 5 near-page-1 pagina's
(Proton + Bitvavo) op basis van de echte GSC query->pagina-mapping.

Per pagina: <title> + meta description exact-matchend op de winnende queries;
H1 bijgewerkt waar de intentie verschoof; FAQ-sectie + FAQPage-schema toegevoegd
waar die ontbrak (eerlijke fee-info, GEEN verzonnen exacte tarieven).

Slugs bestaan al -> Victor regenereert ze niet (slug in existing_folders -> skip),
dus deze backfill blijft staan. Idempotent (marker-checks). Per bestand backup.
Daarna: git add (alleen deze 5) + commit + pull --no-rebase -X ours + push main.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/opt.py
"""
import json, re, shutil, datetime, subprocess
from pathlib import Path

REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
B2B = REPO / "b2b"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

# ---------------- per-pagina configuratie ----------------
def faq_block(pairs):
    """Zichtbare FAQ-sectie + FAQPage JSON-LD. pairs = [(vraag, antwoord), ...]."""
    items = "".join(
        f'<details style="margin:10px 0;border:1px solid #e5e7eb;border-radius:8px;padding:12px 16px">'
        f'<summary style="font-weight:700;cursor:pointer">{q}</summary>'
        f'<p style="margin:10px 0 0;color:#374151">{a}</p></details>'
        for q, a in pairs)
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}}
                         for q, a in pairs]}
    return ('<!-- aibm-faq-v1 -->'
            '<section style="max-width:820px;margin:40px auto;padding:0 16px">'
            '<h2>Frequently asked questions</h2>' + items + '</section>'
            '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')


PAGES = {
    "proton-pricing-en": {
        "title": "How Much Does Proton Mail Cost in 2026? Full Pricing Guide",
        "desc": ("How much does Proton Mail cost in 2026? Every plan priced — free tier, Mail Plus, "
                 "Unlimited, Duo and Business — plus custom-domain costs and which plan is actually "
                 "worth it. An honest founder breakdown."),
        "h1": "How Much Does Proton Mail Cost in 2026?",
        "faq": None,  # heeft al FAQ
    },
    "proton-pricing-id": {
        "title": "Proton Mail Pricing 2026: Paket, Custom Domain & Harga Lengkap",
        "desc": ("Berapa biaya Proton Mail di 2026? Harga lengkap semua paket — Plus, Unlimited, Duo "
                 "dan Business — plus biaya custom domain dan paket mana yang paling layak. Ulasan jujur."),
        "h1": None,
        "faq": None,
    },
    "bitvavo-scale-up": {
        "title": "Bitvavo for Business 2026: Fees, Safety & Full Overview",
        "desc": ("Is Bitvavo right for your business in 2026? An EU-licensed crypto exchange reviewed: "
                 "real trading fees, safety and regulation, pros and cons — from a Dutch ex-banker."),
        "h1": None,
        "faq": [
            ("Is Bitvavo safe?",
             "Bitvavo is registered with the Dutch regulator (DNB) and is one of Europe's larger "
             "EU-based exchanges. As with any exchange, enable 2FA and keep long-term holdings in your "
             "own wallet rather than on the platform."),
            ("Is Bitvavo good for businesses?",
             "Bitvavo is built mainly for individual investors; dedicated corporate/custody features are "
             "more limited than specialist B2B providers. Check current business-account availability "
             "before relying on it for company funds."),
            ("What does Bitvavo cost?",
             "Trading fees start at roughly 0.25% per trade and fall as your 30-day volume rises, with no "
             "monthly account fee. See our <a href='/b2b/bitvavo-pricing-en/'>Bitvavo fees guide</a> for "
             "the full breakdown."),
        ],
    },
    "bitvavo-trading-bot": {
        "title": "Bitvavo Trading Bot 2026: My 24/7 Automated Crypto Setup",
        "desc": ("Can you run an automated trading bot on Bitvavo? A Dutch ex-banker's hands-on guide to "
                 "the Bitvavo API, fees and a 24/7 no-code crypto setup — honest pros and cons. "
                 "Not financial advice."),
        "h1": None,
        "faq": None,  # heeft al FAQ
    },
    "bitvavo-pricing-en": {
        "title": "Bitvavo Fees 2026: Trading, Withdrawal & Hidden Costs",
        "desc": ("Bitvavo's real fees in 2026: trading fees from ~0.25%, Bitcoin and crypto withdrawal "
                 "costs, and the hidden fees founders miss. A clear breakdown of what you'll actually pay."),
        "h1": "Bitvavo Fees in 2026: Trading &amp; Withdrawal Costs",
        "faq": [
            ("What are Bitvavo's trading fees in 2026?",
             "Bitvavo uses a maker/taker model that starts at roughly 0.25% per trade and decreases as "
             "your 30-day trading volume grows. Always check Bitvavo's live fee schedule for the exact "
             "tier that applies to you."),
            ("Does Bitvavo charge withdrawal fees?",
             "Crypto withdrawals carry a network fee that varies by coin — Bitcoin withdrawals reflect "
             "on-chain costs, for example — while euro (SEPA) withdrawals are typically free. Check the "
             "current rate before withdrawing."),
            ("Are there hidden Bitvavo fees?",
             "There is no monthly account fee. The real costs are the trading fee and the network fee on "
             "crypto withdrawals; budget extra for the spread on smaller, less-liquid coins."),
        ],
    },
}

# ---------------- helpers ----------------
def set_title(html, new):
    return re.sub(r"<title>.*?</title>", f"<title>{new}</title>", html, count=1, flags=re.S)

def set_desc(html, new):
    def repl(m):
        return m.group(0)[:m.start(1) - m.start(0)] + new + m.group(0)[m.end(1) - m.start(0):]
    # vervang het content-attribuut van de description-meta
    pat = re.compile(r'(<meta[^>]+name=["\']description["\'][^>]+content=["\'])(.*?)(["\'])', re.I | re.S)
    return pat.sub(lambda m: m.group(1) + new + m.group(3), html, count=1)

def set_h1(html, new):
    return re.sub(r"(<h1[^>]*>).*?(</h1>)", lambda m: m.group(1) + new + m.group(2), html, count=1, flags=re.S)

def insert_faq(html, block):
    if "aibm-faq-v1" in html:
        return html, False
    for anchor in ("</main>", "<footer", "</body>"):
        if anchor in html:
            return html.replace(anchor, block + anchor, 1), True
    return html + block, True


# ---------------- toepassen ----------------
changed_files = []
for slug, cfg in PAGES.items():
    f = B2B / slug / "index.html"
    if not f.exists():
        print(f"✗ {slug}: bestaat niet — overgeslagen"); continue
    html = f.read_text(encoding="utf-8")
    orig = html
    acts = []
    if f"<title>{cfg['title']}</title>" not in html:
        html = set_title(html, cfg["title"]); acts.append("title")
    if cfg["desc"] not in html:
        html = set_desc(html, cfg["desc"]); acts.append("desc")
    if cfg.get("h1"):
        if f">{cfg['h1']}</h1>" not in html:
            html = set_h1(html, cfg["h1"]); acts.append("h1")
    if cfg.get("faq"):
        html, did = insert_faq(html, faq_block(cfg["faq"]))
        if did:
            acts.append("faq")
    if html != orig:
        shutil.copy2(f, str(f) + ".bak-" + STAMP)
        f.write_text(html, encoding="utf-8")
        changed_files.append(f)
        print(f"✓ {slug}: {', '.join(acts)}")
    else:
        print(f"= {slug}: al up-to-date")

if not changed_files:
    print("\nNiets gewijzigd — klaar."); raise SystemExit(0)

# ---------------- git: commit + push naar main ----------------
def git(*args, check=True):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        print("git", " ".join(args), "->", r.stderr.strip())
    return r

remote = git("remote", "get-url", "origin", check=False).stdout
if "aibuildermarketplace" not in remote:
    print("✗ remote lijkt niet de AIBM-repo — push afgebroken. remote:", remote.strip()); raise SystemExit(1)
branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
print(f"\nrepo-branch: {branch}  remote OK")

for f in changed_files:
    git("add", str(f.relative_to(REPO)))
msg = ("SEO: titel/meta/FAQ on-page-optimalisatie Proton + Bitvavo near-page-1 pagina's\n\n"
       "Exact-match op echte GSC-queries (how much does proton mail cost, bitvavo fees, "
       "bitvavo trading bot). FAQ+schema op pagina's zonder FAQ. Geen verzonnen tarieven.\n\n"
       "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
git("commit", "-m", msg)
git("pull", "--no-rebase", "-X", "ours", "origin", branch)
r = git("push", "origin", branch, check=False)
if r.returncode != 0:
    # één retry na nieuwe pull (Victor pusht vaak tegelijk)
    git("pull", "--no-rebase", "-X", "ours", "origin", branch)
    r = git("push", "origin", branch, check=False)
print("\n" + ("✓ gepusht naar origin/" + branch if r.returncode == 0 else "✗ push faalde:\n" + r.stderr))
print("Deploy-lag ~1-2 min; verifieer live met ?cb=$(date +%s).")
print("KLAAR — plak alles terug.")

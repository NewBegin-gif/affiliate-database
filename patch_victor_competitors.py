#!/usr/bin/env python3
"""patch_victor_competitors.py — voegt de COMPETITORS-lijsten alsnog correct toe
(de vorige patch zag ze door een te breed zoekvenster ten onrechte als bestaand).
Ook een re-check van VAULT. Brace-begrensde dubbelen-detectie. Backup + py_compile.

Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pc.py
"""
import re, shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"

VAULT_NEW = {
    "Clay":"https://clay.com","CallRail":"https://partners.callrail.com/nvve8beie0o6",
    "Aspire":"https://partners.aspireapp.com/AIBuilder","Checkr":"https://get.checkr.com/dlmrvlliqgxm",
    "Freshchat":"https://affiliatepartner-freshchat.freshworks.com/613iz3k6u70i","Birch":"https://join.bir.ch/aje5arihw6cw",
    "Freshservice":"https://affiliatepartner-freshservice.freshworks.com/fllek8c4eikg","AWeber":"https://www.aweber.com/easy-email.htm?id=561874",
    "InboxAlly":"https://get.inboxally.com/anvbioq7ns18","Gelato":"https://try.gelato.com/c9ioyi0ycvpz",
    "AfterSell":"https://try.aftersell.app/vv4g49ide6z2","SMTP.com":"https://pstk.smtp.com/aav1yxqg0i9h",
    "1Password":"https://1password.partnerlinks.io/jvm7u5ka0ctm","Stamped":"https://get.stamped.io/sdjq70urrlg6",
    "Streak":"https://get.streak.com/jssfh6jx2eqa",
}
COMP_NEW = {
    "Clay":["Apollo","ZoomInfo","Seamless.ai","Instantly","Smartlead"],
    "CallRail":["WhatConverts","CallTrackingMetrics","Invoca","Ringba"],
    "Aspire":["Payoneer","Wise","Airwallex","Brex","Mercury"],
    "Checkr":["Sterling","GoodHire","Certn","Accurate"],
    "Freshchat":["Intercom","Drift","Tidio","Zendesk","LiveChat"],
    "Birch":["Madgicx","Revealbot","AdEspresso","Smartly"],
    "Freshservice":["ServiceNow","Jira Service Management","Zendesk","SolarWinds"],
    "AWeber":["Mailchimp","GetResponse","ActiveCampaign","ConvertKit","Brevo"],
    "InboxAlly":["Warmbox","Mailwarm","Lemwarm","Folderly"],
    "Gelato":["Printify","Printful","Gooten","SPOD"],
    "AfterSell":["Zipify","ReConvert","CartHook","Rebuy"],
    "SMTP.com":["SMTP2GO","SendGrid","Mailgun","Postmark","Amazon SES"],
    "1Password":["LastPass","Bitwarden","Dashlane","Keeper","NordPass"],
    "Stamped":["Yotpo","Judge.me","Okendo","Loox"],
    "Streak":["HubSpot","Pipedrive","Copper","Salesflare","Close"],
}

src = open(AG, encoding="utf-8").read()
orig = src


def dict_span(name):
    """geef (start_na_accolade, eind_op_close) van NAME = { ... } via brace-matching."""
    m = re.search(rf"\n{name}\s*=\s*\{{\n", src)
    if not m:
        return None
    i = m.end()
    depth = 1
    j = i
    while j < len(src) and depth:
        ch = src[j]
        if ch == "{": depth += 1
        elif ch == "}": depth -= 1
        elif ch in "\"'":
            q = ch; j += 1
            while j < len(src) and src[j] != q:
                if src[j] == "\\": j += 1
                j += 1
        j += 1
    return i, j - 1  # j-1 = index van de matchende '}'


def keys_in(start, end):
    body = src[start:end]
    return set(re.findall(r'^\s*["\']([^"\']+)["\']\s*:', body, re.M))


def insert(name, data, fmt):
    global src
    sp = dict_span(name)
    if not sp:
        print(f"  ✗ {name} niet gevonden"); return 0
    start, end = sp
    have = keys_in(start, end)
    block = "".join(fmt(k, v) for k, v in data.items() if k not in have)
    added = sum(1 for k in data if k not in have)
    if block:
        src = src[:start] + block + src[start:]
    return added

a = insert("VAULT", VAULT_NEW, lambda k, v: f'    "{k}": "{v}",\n')
c = insert("COMPETITORS", COMP_NEW, lambda k, v: f'    "{k}": {v!r},\n')
print(f"alsnog toegevoegd → VAULT:{a}  COMPETITORS:{c}")

if src != orig:
    bak = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(AG, bak)
    open(AG, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(AG, doraise=True)
        print(f"✓ toegepast + syntax OK (backup: {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, AG); print("✗ syntaxfout — backup teruggezet:", e)
else:
    print("✓ niets te doen — alles stond er al in.")

# verificatie
for name, data in [("VAULT", VAULT_NEW), ("TOPICS", {k:1 for k in COMP_NEW}), ("COMPETITORS", COMP_NEW)]:
    sp = dict_span(name)
    if sp:
        have = keys_in(*sp)
        miss = [k for k in data if k not in have]
        print(f"  {name}: {len(data)-len(miss)}/{len(data)} aanwezig" + (f" — mist: {miss}" if miss else " ✓"))

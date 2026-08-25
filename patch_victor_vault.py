#!/usr/bin/env python3
"""patch_victor_vault.py — voeg de 15 ontbrekende affiliates toe aan Victors
VAULT + TOPICS + COMPETITORS, zodat hij er (Engels-first) artikelen over maakt.

Idempotent (slaat bestaande keys over), backup + py_compile. Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/patch_victor_vault.py
"""
import re, shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"

VAULT_NEW = {
    "Clay": "https://clay.com",
    "CallRail": "https://partners.callrail.com/nvve8beie0o6",
    "Aspire": "https://partners.aspireapp.com/AIBuilder",
    "Checkr": "https://get.checkr.com/dlmrvlliqgxm",
    "Freshchat": "https://affiliatepartner-freshchat.freshworks.com/613iz3k6u70i",
    "Birch": "https://join.bir.ch/aje5arihw6cw",
    "Freshservice": "https://affiliatepartner-freshservice.freshworks.com/fllek8c4eikg",
    "AWeber": "https://www.aweber.com/easy-email.htm?id=561874",
    "InboxAlly": "https://get.inboxally.com/anvbioq7ns18",
    "Gelato": "https://try.gelato.com/c9ioyi0ycvpz",
    "AfterSell": "https://try.aftersell.app/vv4g49ide6z2",
    "SMTP.com": "https://pstk.smtp.com/aav1yxqg0i9h",
    "1Password": "https://1password.partnerlinks.io/jvm7u5ka0ctm",
    "Stamped": "https://get.stamped.io/sdjq70urrlg6",
    "Streak": "https://get.streak.com/jssfh6jx2eqa",
}
TOPICS_NEW = {
    "Clay": ["ai-sales-prospecting","data-enrichment-tool","lead-list-building","gtm-automation","waterfall-enrichment"],
    "CallRail": ["call-tracking-software","marketing-attribution","call-analytics","lead-attribution"],
    "Aspire": ["business-finance-platform","multi-currency-account","corporate-cards-cashback","expense-management-software","startup-business-account"],
    "Checkr": ["background-check-software","employee-screening","pre-employment-screening","fcra-compliant-checks"],
    "Freshchat": ["live-chat-software","customer-messaging","chatbot-for-website","whatsapp-business-chat"],
    "Birch": ["ad-automation-tool","facebook-ads-automation","automated-ad-rules","performance-marketing-automation"],
    "Freshservice": ["it-service-management","itsm-tool","help-desk-software","asset-management"],
    "AWeber": ["email-marketing-for-small-business","email-autoresponder","newsletter-tool","landing-page-builder"],
    "InboxAlly": ["email-deliverability-tool","inbox-placement","email-warmup","sender-reputation"],
    "Gelato": ["print-on-demand","custom-products-no-inventory","print-on-demand-for-shopify","global-print-fulfillment"],
    "AfterSell": ["shopify-upsell-app","post-purchase-upsell","increase-average-order-value","checkout-upsell"],
    "SMTP.com": ["smtp-relay-service","transactional-email-api","bulk-email-sending","email-api"],
    "1Password": ["password-manager-for-business","team-password-management","passkey-manager","secrets-management"],
    "Stamped": ["product-reviews-app","loyalty-program-software","shopify-reviews-app","ugc-collection"],
    "Streak": ["gmail-crm","crm-for-google-workspace","pipeline-in-gmail","sales-crm-for-small-business"],
}
COMP_NEW = {
    "Clay": ["Apollo","ZoomInfo","Seamless.ai","Instantly","Smartlead"],
    "CallRail": ["WhatConverts","CallTrackingMetrics","Invoca","Ringba"],
    "Aspire": ["Payoneer","Wise","Airwallex","Brex","Mercury"],
    "Checkr": ["Sterling","GoodHire","Certn","Accurate"],
    "Freshchat": ["Intercom","Drift","Tidio","Zendesk","LiveChat"],
    "Birch": ["Madgicx","Revealbot","AdEspresso","Smartly"],
    "Freshservice": ["ServiceNow","Jira Service Management","Zendesk","SolarWinds"],
    "AWeber": ["Mailchimp","GetResponse","ActiveCampaign","ConvertKit","Brevo"],
    "InboxAlly": ["Warmbox","Mailwarm","Lemwarm","Folderly"],
    "Gelato": ["Printify","Printful","Gooten","SPOD"],
    "AfterSell": ["Zipify","ReConvert","CartHook","Rebuy"],
    "SMTP.com": ["SMTP2GO","SendGrid","Mailgun","Postmark","Amazon SES"],
    "1Password": ["LastPass","Bitwarden","Dashlane","Keeper","NordPass"],
    "Stamped": ["Yotpo","Judge.me","Okendo","Loox"],
    "Streak": ["HubSpot","Pipedrive","Copper","Salesflare","Close"],
}

src = open(AG, encoding="utf-8").read()
orig = src


def existing_keys(name):
    m = re.search(rf"\n{name}\s*=\s*\{{", src)
    if not m:
        return None, None
    return m.end(), set(re.findall(rf'["\']([^"\']+)["\']\s*:', src[m.end():m.end()+200000]))


def insert(name, data, fmt):
    global src
    m = re.search(rf"(\n{name}\s*=\s*\{{\n)", src)
    if not m:
        print(f"  ✗ {name} dict niet gevonden — overslaan"); return 0
    _, keys = existing_keys(name)
    block = ""
    added = 0
    for k, v in data.items():
        if k in (keys or set()):
            continue
        block += fmt(k, v); added += 1
    if block:
        src = src[:m.end()] + block + src[m.end():]
    return added

a = insert("VAULT", VAULT_NEW, lambda k, v: f'    "{k}": "{v}",\n')
b = insert("TOPICS", TOPICS_NEW, lambda k, v: f'    "{k}": {v!r},\n')
c = insert("COMPETITORS", COMP_NEW, lambda k, v: f'    "{k}": {v!r},\n')
print(f"toegevoegd → VAULT:{a}  TOPICS:{b}  COMPETITORS:{c}")

if src != orig:
    bak = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(AG, bak)
    open(AG, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(AG, doraise=True)
        print(f"✓ patch toegepast + syntax OK (backup: {bak})")
        print("  Victor genereert nu (Engels-first) artikelen voor deze merken; ze")
        print("  staan vooraan de wachtrij (minste artikelen = hoogste prioriteit).")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, AG)
        print("✗ syntaxfout — backup teruggezet:", e)
else:
    print("✓ niets te doen — alles stond er al in.")

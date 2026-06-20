#!/usr/bin/env python3
"""patch_victor_competitors_backfill.py — voeg TOPICS + COMPETITORS toe voor de
hoog-waarde VAULT-merken die ze nog misten, zodat Victor er ook vs-vergelijkings-
en topic-rijke reviews over maakt. Alleen echte, bekende concurrenten (geen gegok).

Brace-begrensde dubbelen-detectie, backup + py_compile, idempotent.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pcb.py
"""
import re, shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"

COMP = {
 "ActiveCampaign":["HubSpot","Mailchimp","Brevo","GetResponse","Klaviyo","ConvertKit"],
 "Brevo":["Mailchimp","ActiveCampaign","GetResponse","Klaviyo","MailerLite","SendGrid"],
 "Keap":["HubSpot","ActiveCampaign","GoHighLevel","Ontraport","Kartra"],
 "Kit":["Beehiiv","Substack","Mailchimp","ActiveCampaign","MailerLite"],
 "Beehiiv":["Substack","Kit","Ghost","Mailchimp","ConvertKit","MailerLite"],
 "Campaigner":["Mailchimp","Brevo","GetResponse","ActiveCampaign","Constant Contact"],
 "iContact":["Mailchimp","Constant Contact","AWeber","GetResponse","Brevo"],
 "lemlist":["Instantly","Smartlead","Apollo","Woodpecker","Mailshake","Reply"],
 "Kartra":["Kajabi","ClickFunnels","Systeme.io","Keap","Builderall"],
 "Apollo":["ZoomInfo","Clay","Seamless.ai","Lusha","Cognism","Instantly"],
 "ZoomInfo":["Apollo","Cognism","Lusha","Clearbit","Seamless.ai","LeadIQ"],
 "Salesflare":["Pipedrive","HubSpot","Close","folk","Copper","Streak"],
 "Nutshell":["Pipedrive","HubSpot","Close","Salesflare","Copper","Insightly"],
 "Capsule":["Pipedrive","HubSpot","Insightly","folk","Salesflare","Copper"],
 "folk":["HubSpot","Pipedrive","Streak","Salesflare","Capsule","Attio"],
 "Leadfeeder":["Albacross","Lead Forensics","RB2B","Visitor Queue","Clearbit"],
 "FullEnrich":["Clay","Apollo","Seamless.ai","Cognism","BetterContact"],
 "ManyChat":["Chatfuel","Tidio","Botsify","Instabot","Tars"],
 "Later":["Buffer","Hootsuite","Sprout Social","Planoly","Loomly","SocialBee"],
 "SocialBee":["Buffer","Hootsuite","Later","Loomly","Sprout Social","Publer"],
 "Shorby":["Linktree","Beacons","Taplink","Campsite","Later"],
 "Outgrow":["Typeform","Involve.me","Interact","Jotform","SurveyMonkey"],
 "VWO":["Optimizely","AB Tasty","Convert","Kameleoon","Crazy Egg"],
 "Wrike":["Asana","Monday.com","ClickUp","Smartsheet","Jira","Trello"],
 "Todoist":["TickTick","Microsoft To Do","Things","Any.do","Notion"],
 "Toggl":["Harvest","Clockify","RescueTime","Time Doctor","Hubstaff"],
 "Hive":["Asana","Monday.com","ClickUp","Wrike","Trello"],
 "SurveySparrow":["Typeform","SurveyMonkey","Qualtrics","Jotform","Google Forms"],
 "Foxit":["Adobe Acrobat","Nitro PDF","PDFelement","Smallpdf","SignNow"],
 "Tresorit":["Sync.com","pCloud","Proton Drive","Box","Dropbox","IDrive"],
 "IDrive":["Backblaze","Carbonite","Acronis","pCloud","Crashplan"],
 "Passpack":["1Password","Bitwarden","LastPass","Dashlane","Keeper","NordPass"],
 "Fastmail":["Proton Mail","Gmail","Zoho Mail","Hey","Tutanota"],
 "WPRocket":["W3 Total Cache","WP Super Cache","NitroPack","Perfmatters","LiteSpeed Cache"],
 "RankMath":["Yoast SEO","All in One SEO","SEOPress","The SEO Framework"],
 "Landingi":["Unbounce","Instapage","Leadpages","Carrd","Webflow"],
 "Leadpages":["Unbounce","Instapage","Landingi","ClickFunnels","Carrd"],
 "Aircall":["RingCentral","Dialpad","CloudTalk","JustCall","OpenPhone","Nextiva"],
 "WhatConverts":["CallRail","CallTrackingMetrics","Invoca","Ringba"],
 "Salesmessage":["SimpleTexting","TextMagic","EZ Texting","Heymarket","Textline"],
 "Printify":["Printful","Gelato","Gooten","SPOD","Teelaunch"],
 "Spocket":["DSers","Modalyst","Syncee","AliDrop","Printful"],
}

def topics_for(b):
    bl = b.lower()
    return [f"{bl}-review", f"{bl}-pricing", f"{bl}-alternatives", f"{bl}-for-small-business"]

TOPICS = {b: topics_for(b) for b in COMP}

src = open(AG, encoding="utf-8").read()
orig = src


def dict_span(name):
    m = re.search(rf"\n{name}\s*=\s*\{{\n", src)
    if not m: return None
    i = m.end(); depth = 1; j = i
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
    return i, j - 1


def keys_in(s, e):
    return set(re.findall(r'^\s*["\']([^"\']+)["\']\s*:', src[s:e], re.M))


def insert(name, data, fmt):
    global src
    sp = dict_span(name)
    if not sp: print(f"  ✗ {name} niet gevonden"); return 0
    s, e = sp; have = keys_in(s, e)
    block = "".join(fmt(k, v) for k, v in data.items() if k not in have)
    added = sum(1 for k in data if k not in have)
    if block: src = src[:s] + block + src[s:]
    return added

c = insert("COMPETITORS", COMP, lambda k, v: f'    "{k}": {v!r},\n')
t = insert("TOPICS", TOPICS, lambda k, v: f'    "{k}": {v!r},\n')
print(f"toegevoegd → COMPETITORS:{c}  TOPICS:{t}")

if src != orig:
    bak = f"{AG}.bak-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(AG, bak)
    open(AG, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(AG, doraise=True)
        print(f"✓ toegepast + syntax OK (backup: {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, AG); print("✗ syntaxfout — backup teruggezet:", e); raise SystemExit(1)
else:
    print("✓ niets te doen — alles stond er al in.")

for name in ("COMPETITORS", "TOPICS"):
    sp = dict_span(name)
    have = keys_in(*sp)
    miss = [b for b in COMP if b not in have]
    print(f"  {name}: {len(COMP)-len(miss)}/{len(COMP)} aanwezig" + (f" — mist: {miss}" if miss else " ✓"))

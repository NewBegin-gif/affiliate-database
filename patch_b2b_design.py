#!/usr/bin/env python3
"""patch_b2b_design.py — upgrade de b2b-index: echt navigatiemenu + echte logo's
op meer kaarten (vult _LOGO_DOMAIN aan met data.json-domeinen). Backup + py_compile.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/pbd.py
"""
import re, shutil, datetime, py_compile
AG = "/root/felix_hq/generate_article.py"

EXTRA = {'payoneer': 'payoneer.com', 'billcom': 'bill.com', 'tax1099': 'tax1099.com', 'flippa': 'flippa.com', 'creditrepaircloud': 'creditrepaircloud.com', 'bitvavo': 'bitvavo.com', 'bybit': 'bybit.com', 'activecampaign': 'activecampaign.com', 'close': 'close.com', 'vistasocial': 'vistasocial.com', 'replyio': 'reply.io', 'alidrop': 'alidrop.co', 'smartli': 'smartli.com', 'logomeai': 'logome.ai', 'aisdr': 'aisdr.com', 'elevateforward': 'elevateforward.ai', 'successco': 'success.co', 'getresponse': 'getresponse.com', 'campaignmonitor': 'campaignmonitor.com', 'amplemarket': 'amplemarket.com', 'omniseo': 'omniseo.com', 'seamlessai': 'seamless.ai', 'unbounce': 'unbounce.com', 'iconosquare': 'iconosquare.com', 'adwisely': 'adwisely.com', 'adcreativeai': 'adcreative.ai', 'landingi': 'landingi.com', 'aisq': 'aisq.com', 'manychat': 'manychat.com', 'printify': 'printify.com', 'frase': 'frase.io', 'clay': 'clay.com', 'rankmath': 'rankmath.com', 'atria': 'tryatria.com', 'beehiiv': 'beehiiv.com', 'clickup': 'clickup.com', 'trainual': 'trainual.com', 'beautifulai': 'beautiful.ai', 'gamma': 'gamma.app', 'databox': 'databox.com', 'tradify': 'tradifyhq.com', 'reclaimai': 'reclaim.ai', 'vea': 'vea.ai', 'sanebox': 'sanebox.com', 'assembly': 'joinassembly.com', 'increff': 'increff.com', 'quillbot': 'quillbot.com', 'lindyai': 'lindy.ai', 'typewise': 'typewise.app', 'turbotic': 'turbotic.com', 'pangram': 'pangram.com', 'synthesia': 'synthesia.io', 'invideo': 'invideo.io', 'murf': 'murf.ai', 'jotformaiagents': 'jotform.com', 'cloudtalk': 'cloudtalk.io', 'calilio': 'calilio.com', 'krispcall': 'krispcall.com', 'vidaai': 'vida.io', 'cometchat': 'cometchat.com', 'mindstudio': 'mindstudio.ai', 'consensus': 'consensus.app', 'protondrive': 'proton.me', 'idrive': 'idrive.com', 'runpod': 'runpod.io', 'bitdefender': 'bitdefender.com', 'browseai': 'browse.ai', 'plesk': 'plesk.com', 'emergent': 'emergent.sh', 'airia': 'airia.com', 'expertiseai': 'expertise.ai', 'ngram': 'ngram.com', 'replit': 'replit.com', 'nordvpn': 'nordvpn.com', 'hostinger': 'hostinger.com', 'chemicloud': 'chemicloud.com', 'kinsta': 'kinsta.com', 'wprocket': 'wp-rocket.me', 'aircall': 'aircall.io', 'katanamrp': 'katanamrp.com', 'processstreet': 'process.st', 'gusto': 'gusto.com', 'brightdata': 'brightdata.com', 'smartsuite': 'smartsuite.com', 'melio': 'meliopayments.com', 'quo': 'quo.com', 'flocksy': 'flocksy.com', 'shippo': 'goshippo.com', 'taxcycle': 'taxcycle.com', 'alohi': 'alohi.com', 'webcatalog': 'webcatalog.io', 'livestorm': 'livestorm.com', 'volza': 'volza.com', 'callhippo': 'callhippo.com', 'bokun': 'bokun.io', 'shiftie': 'shiftie.co', 'marketing360': 'marketing360.com', 'signnow': 'signnow.com', 'gravityforms': 'gravity.com', 'goflow': 'goflow.com', 'readymode': 'readymode.com', 'weave': 'getweave.com', 'navan': 'navan.com', 'softr': 'softr.io', 'marketerhire': 'marketerhire.com', 'toggl': 'toggl.com', 'voye': 'voyedatapool.com', 'jubilee': 'jubileepro.com', 'bouncer': 'usebouncer.com', 'surveysparrow': 'surveysparrow.com', 'difyai': 'dify.ai', 'doola': 'doola.com', 'stampezee': 'stampezee.com', 'wrike': 'wrike.com', 'foxit': 'foxit.com', 'contractorforeman': 'contractorforeman.com', '800com': '800.com', 'pylon': 'usepylon.com', 'salesflare': 'salesflare.com', 'dify': 'dify.ai', 'later': 'later.com', 'shorby': 'shorby.com', 'keap': 'keap.com', 'folk': 'folk.app', 'outgrow': 'outgrow.co', 'dropgenius': 'dropgenius.com', 'diginius': 'diginius.com', 'tresorit': 'tresorit.com', 'boltbusiness': 'bolt.eu', 'ueni': 'ueni.com', 'crankwheel': 'crankwheel.com', 'socialbee': 'socialbee.io', 'ownr': 'ownr.co', 'todoist': 'todoist.com', 'aira': 'aira.app', 'apollo': 'apollo.io', 'ruby': 'ruby.com', 'devsai': 'devs.ai', 'salesmessage': 'salesmessage.com', 'leadpages': 'leadpages.com', 'hive': 'hive.com', 'fastmail': 'fastmail.com', 'fullenrich': 'fullenrich.com', 'brevo': 'brevo.com', 'mrpeasy': 'mrpeasy.com', 'capsule': 'capsulecrm.com', 'trainerize': 'trainerize.com', 'pdware': 'pdware.com', 'nutshell': 'nutshell.com', 'bookyourdata': 'bookyourdata.com', 'sentaro': 'sentaro.com', 'buddypunch': 'buddypunch.com', 'leadfeeder': 'leadfeeder.com', 'lemlist': 'lemlist.com', 'atto': 'attotime.com', 'breezyhr': 'breezy.hr', 'kartra': 'kartra.com', 'barcodestalk': 'barcodestalk.com', 'nicejob': 'nicejob.com', 'smtp2go': 'smtp2go.com', 'kit': 'kit.com', 'unitelvoice': 'unitelvoice.com', 'passpack': 'passpack.com', 'zoominfo': 'zoominfo.com', 'switcherstudio': 'switcherstudio.com', 'blinq': 'blinq.me', 'vwo': 'vwo.com', 'connecteam': 'connecteam.com', 'bugherd': 'bugherd.com', 'icontact': 'icontact.com', 'campaigner': 'campaigner.com', 'learnworlds': 'learnworlds.com', 'whatconverts': 'whatconverts.com', 'hopp': 'gethopp.com', 'carbon6': 'carbon6.io', 'housecallpro': 'housecallpro.com', 'spocket': 'spocket.co', 'callrail': 'callrail.com', 'aspire': 'aspireapp.com', 'checkr': 'checkr.com', 'freshchat': 'freshchat.com', 'birch': 'bir.ch', 'freshservice': 'freshservice.com', 'aweber': 'aweber.com', 'inboxally': 'inboxally.com', 'gelato': 'gelato.com', 'aftersell': 'aftersell.app', 'smtpcom': 'smtp.com', '1password': '1password.com', 'stamped': 'stamped.io', 'streak': 'streak.com'}

src = open(AG, encoding="utf-8").read(); orig = src
done = []

# 1) _EXTRA_LOGO_DOMAINS toevoegen vlak vóór def _brandlogo
if "_EXTRA_LOGO_DOMAINS" not in src:
    anchor = "def _brandlogo(b):"
    inject = "_EXTRA_LOGO_DOMAINS = " + repr(EXTRA) + "\n\n\n"
    if anchor in src:
        src = src.replace(anchor, inject + anchor, 1); done.append("EXTRA-map toegevoegd")

# 2) dom-lookup uitbreiden met de EXTRA-map (genormaliseerd)
old_dom = "    dom = _LOGO_DOMAIN.get(b)\n"
new_dom = ("    dom = _LOGO_DOMAIN.get(b) or _EXTRA_LOGO_DOMAINS.get("
           "b.lower().replace(' ','').replace('.','').replace('-',''))\n")
if old_dom in src:
    src = src.replace(old_dom, new_dom, 1); done.append("dom-lookup uitgebreid")

# 3) breadcrumb-nav -> echt menu
old_nav = '<nav class="topnav"><a href="/">AIBuilder Marketplace</a><span class="sep">\u203a</span><span class="current">B2B Knowledge Base</span></nav>'
new_nav = ('<nav class="topnav"><div class="topnav-inner">'
           '<a href="/" class="topnav-brand">AIBuilder Marketplace</a>'
           '<span class="topnav-links"><a href="/finder/">Tool Finder</a>'
           '<a href="/best/">Best Tools</a><a href="/deals/">Deals</a>'
           '<a href="/free-stack/">Free Guide</a><a href="/">Home</a></span></div></nav>')
if old_nav in src:
    src = src.replace(old_nav, new_nav, 1); done.append("nav -> menu")
else:
    done.append("WAARSCHUWING: nav-string niet gevonden")

# 4) .topnav CSS -> echte navbalk
old_css = ".topnav{{background:#161b22;border-bottom:1px solid #30363d;padding:14px 24px;font-size:.88em}}"
new_css = (".topnav{{background:#161b22;border-bottom:1px solid #30363d;padding:0 24px}}"
           ".topnav-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;"
           "justify-content:space-between;height:54px;gap:14px;flex-wrap:wrap}}"
           ".topnav-brand{{font-weight:800;color:#f0f6fc;text-decoration:none;font-size:1.05em}}"
           ".topnav-links a{{color:#8b949e;text-decoration:none;font-size:.88em;font-weight:500;margin-left:18px}}"
           ".topnav-links a:hover{{color:#58a6ff}}")
if old_css in src:
    src = src.replace(old_css, new_css, 1); done.append("topnav CSS")
else:
    done.append("WAARSCHUWING: topnav-CSS niet gevonden")

print("stappen:", done)
if src != orig:
    bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(AG, bak)
    open(AG, "w", encoding="utf-8").write(src)
    try:
        py_compile.compile(AG, doraise=True)
        print("OK + syntax valide. backup:", bak)
        print("Draai nu 1 generatie of wacht op cron; of forceer rebuild:")
        print("  cd /root/felix_hq && venv/bin/python3 -c \"import generate_article as g; g.rebuild_index(g.get_existing_folders())\"")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, AG); print("syntaxfout - teruggezet:", e)
else:
    print("niets gewijzigd")

# ── 5) deploy: rebuild b2b/index.html uit de nieuwe template + push ──
if src != orig:
    import sys, os, subprocess
    sys.path.insert(0, "/root/felix_hq"); os.chdir("/root/felix_hq")
    REPO = "/root/felix_hq/repos/aibuildermarketplace"
    def _git(*a):
        r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
        print("  git", a[0], "->", (r.stdout + r.stderr).strip()[:200]); return r
    try:
        import generate_article as g
        g.rebuild_index(g.get_existing_folders())
        ok = 'class="topnav-links"' in open(os.path.join(REPO, "b2b", "index.html"), encoding="utf-8").read()
        print("  nieuw menu in rebuild:", ok)
        _git("add", "b2b/index.html")
        _git("commit", "-m", "b2b index: real nav menu + more real logos")
        _git("pull", "--no-rebase", "-X", "theirs", "origin", "main")
        g.rebuild_index(g.get_existing_folders())  # na pull opnieuw, zodat onze template wint
        _git("add", "b2b/index.html")
        _git("commit", "-m", "b2b index rebuild after pull")
        _git("push", "origin", "main")
        print("\n✅ KLAAR — check https://aibuildermarketplace.com/b2b/ (na ~1-2 min)")
    except Exception as e:
        print("  deploy-stap mislukt:", e)
        print("  draai handmatig: cd /root/felix_hq && venv/bin/python3 generate_article.py")

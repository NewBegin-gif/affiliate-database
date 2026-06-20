#!/usr/bin/env python3
"""patch_b2b_filterui.py — verfijn de b2b-filter: klap de TOOL- (~115) en LANG-
(~35) pill-muren standaard in achter 'Tool ▾'/'Lang ▾'-toggles. Zoekbalk + TYPE
blijven zichtbaar. Backup + py_compile + deploy (rebuild + force naar main+staging).
Draai met venv:  /root/felix_hq/venv/bin/python3 /tmp/pfu.py
"""
import os, sys, subprocess, shutil, datetime, py_compile
AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read(); orig = src
done = []

# 1) TOOL-pills inklapbaar
old1 = '        <span class="filter-label">Tool:</span>\n        {tools_html}'
new1 = ('        <button type="button" class="filter-btn pill-toggle" '
        'onclick="togglePills(\'toolpills\',this)">Tool ▾</button>\n'
        '        <span class="pill-group" id="toolpills">{tools_html}</span>')
if old1 in src: src = src.replace(old1, new1, 1); done.append("TOOL inklapbaar")
else: done.append("WAARSCHUWING: TOOL-blok niet gevonden")

# 2) LANG-pills inklapbaar
old2 = '        <span class="filter-label">Lang:</span>\n        {langs_html}'
new2 = ('        <button type="button" class="filter-btn pill-toggle" '
        'onclick="togglePills(\'langpills\',this)">Lang ▾</button>\n'
        '        <span class="pill-group" id="langpills">{langs_html}</span>')
if old2 in src: src = src.replace(old2, new2, 1); done.append("LANG inklapbaar")
else: done.append("WAARSCHUWING: LANG-blok niet gevonden")

# 3) CSS voor pill-group + toggle
old_css = "        .filter-sep{{width:1px;height:20px;background:#30363d;margin:0 4px}}"
new_css = (old_css + "\n        .pill-group{{display:none}}\n"
           "        .pill-group.open{{display:contents}}\n"
           "        .pill-toggle{{font-weight:700;color:#c9d1d9}}")
if old_css in src: src = src.replace(old_css, new_css, 1); done.append("CSS")
else: done.append("WAARSCHUWING: filter-CSS niet gevonden")

# 4) JS toggle
old_js = "        function filterSearch(q){{searchQ=q;applyFilter();}}"
new_js = (old_js + "\n        function togglePills(id,btn){{var e=document.getElementById(id);"
          'if(e){{e.classList.toggle("open");btn.classList.toggle("active");}}}}')
if old_js in src: src = src.replace(old_js, new_js, 1); done.append("JS toggle")
else: done.append("WAARSCHUWING: filterSearch-JS niet gevonden")

print("stappen:", done)
if src == orig:
    print("niets gewijzigd — ABORT"); sys.exit(1)
bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(AG, bak); open(AG, "w", encoding="utf-8").write(src)
try:
    py_compile.compile(AG, doraise=True); print("syntax OK, backup:", bak)
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG); print("syntaxfout - teruggezet:", e); sys.exit(1)

# ── deploy: rebuild + force naar main+staging (omzeilt -X theirs revert) ──
os.chdir("/root/felix_hq"); sys.path.insert(0, "/root/felix_hq")
REPO = "/root/felix_hq/repos/aibuildermarketplace"; IDX = os.path.join(REPO, "b2b", "index.html")
def _git(*a):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    print("  git", a[0], "->", (r.stdout + r.stderr).strip()[:160]); return r
import generate_article as g
g.rebuild_index(g.get_existing_folders())
ok = "pill-toggle" in open(IDX, encoding="utf-8").read()
print("  toggles in rebuild:", ok)
_git("add", "b2b/index.html"); _git("commit", "-m", "b2b filter: collapsible tool/lang pills")
_git("fetch", "origin"); _git("pull", "--no-rebase", "-X", "ours", "origin", "main")
g.rebuild_index(g.get_existing_folders())
_git("add", "b2b/index.html"); _git("commit", "-m", "b2b filter rebuild after pull")
_git("push", "origin", "HEAD:main")
sp = _git("push", "origin", "HEAD:victor-staging")
if sp.returncode != 0: _git("push", "--force-with-lease", "origin", "HEAD:victor-staging")
_git("fetch", "origin")
m = _git("show", "origin/main:b2b/index.html")
print("  toggles op origin/main:", "pill-toggle" in m.stdout)
print("\n✅ KLAAR — check https://aibuildermarketplace.com/b2b/ (na ~1-2 min)")

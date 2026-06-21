#!/usr/bin/env python3
"""patch_throttle_AB.py — twee zekere fixes:

  A) build_hreflang.py stópt met noindex strippen. De cron draait elke 6u met
     --apply en wiste tot nu toe ELKE noindex -> prune was zinloos. Hreflang
     blijft verder gewoon werken; alleen het noindex-strippen vervalt.

  B) sync_vault_from_data.py krijgt een POORT: alleen data.json-tools met
     "vault": true worden in VAULT/AFFILIATE gezet (= Victor schrijft er pas
     artikelen over als jij het markeert). Bestaande VAULT-merken blijven staan.
     Tapstitch (geen vlag) wordt dus NIET meer automatisch gegenereerd.

Idempotent, per bestand backup + py_compile (auto-revert bij syntaxfout).
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/ab.py
"""
import re, shutil, datetime, py_compile

STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def patch(path, label, apply_fn, marker):
    src = open(path, encoding="utf-8").read()
    if marker in src:
        print(f"= {label}: al gepatcht — skip"); return
    new = apply_fn(src)
    if new is None or new == src:
        print(f"✗ {label}: anchor niet gevonden — NIET gewijzigd"); return
    bak = f"{path}.bak-{STAMP}"
    shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(path, doraise=True)
        print(f"✓ {label}: gepatcht (backup {bak})")
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, path)
        print(f"✗ {label}: syntaxfout — teruggezet: {e}")


# ---------- A) build_hreflang.py: stop noindex-strip ----------
def fix_a(src):
    pat = re.compile(
        r'if "noindex" in m\.group\(0\)\.lower\(\):\s*\n'
        r'\s*noindex_fixed \+= 1\s*\n'
        r'\s*return ""\s*\n'
        r'\s*return m\.group\(0\)')
    repl = ('# noindex NIET meer strippen — prune_dead_pages.py zet die bewust (anti-conflict)\n'
            '        return m.group(0)')
    return pat.sub(repl, src, count=1)

patch("/root/felix_hq/build_hreflang.py", "A) hreflang stopt noindex-strip",
      fix_a, marker="noindex NIET meer strippen")

# ---------- B) sync_vault_from_data.py: VAULT-poort ----------
def fix_b(src):
    anchor = '        name=it.get("name","").strip(); nk=norm(name)\n        if not name: continue\n'
    if anchor not in src:
        return None
    gate = anchor + '        if not it.get("vault"): continue  # POORT: alleen tools met "vault": true\n'
    return src.replace(anchor, gate, 1)

patch("/root/felix_hq/sync_vault_from_data.py", "B) VAULT-poort (alleen vault:true)",
      fix_b, marker='it.get("vault")')

print("\nKLAAR — plak alles terug.")
print('Let op B: om voortaan een tool door Victor te laten beschrijven, zet "vault": true bij die tool in data.json.')

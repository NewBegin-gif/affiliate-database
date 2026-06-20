#!/usr/bin/env python3
"""patch_victor_dify_dedupe.py — dedupe Dify-varianten in Victors generator.

Op de site-kant hadden we 2 Dify-tegels (Dify + Dify.ai, zelfde domein/link);
dat is opgeschoond in affdb/data.json. Deze patch doet hetzelfde aan Victor-kant:
binnen de VAULT / TOPICS / COMPETITORS dict-literals in generate_article.py
worden variant-keys ("Dify.ai" / "Difyai") samengevoegd met de canonieke key
"Dify", en competitor-LIJSTwaarden "Dify.ai"/"Difyai" worden "Dify" + gededupet.

Eerst RAPPORTEERT hij elke Dify-vermelding (read-only inzicht), past daarna
alleen veilige transformaties toe. Idempotent. Backup + py_compile; bij
syntaxfout wordt automatisch teruggezet. Draai op de VPS:
  /root/felix_hq/venv/bin/python3 /tmp/dify.py
"""
import re, shutil, datetime, py_compile

AG = "/root/felix_hq/generate_article.py"
src = open(AG, encoding="utf-8").read()
orig = src

# ---------- 0) rapport: elke Dify-vermelding met regelnummer ----------
print("=== Dify-vermeldingen in generate_article.py ===")
hits = [(i + 1, l.strip()) for i, l in enumerate(src.split("\n")) if "dify" in l.lower()]
for ln, txt in hits:
    print(f"  L{ln}: {txt[:140]}")
if not hits:
    print("  (geen enkele Dify-vermelding gevonden — niets te dedupen)")
    raise SystemExit(0)
print(f"  totaal regels met 'dify': {len(hits)}\n")


def find_dict_span(text, name):
    """Geef (start,end) van de {...} na 'NAME = {' via balans-tellen, of None."""
    m = re.search(rf'\b{name}\s*=\s*\{{', text)
    if not m:
        return None
    i = text.index("{", m.start())
    depth, j = 0, i
    while j < len(text):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return (i, j + 1)
        j += 1
    return None


changes = []

# ---------- 1) variant-KEYS in VAULT / TOPICS / COMPETITORS samenvoegen ----------
for dname in ("VAULT", "TOPICS", "COMPETITORS"):
    span = find_dict_span(src, dname)
    if not span:
        continue
    a, b = span
    block = src[a:b]
    has_canon = re.search(r'["\']Dify["\']\s*:', block) is not None
    for variant in ("Dify.ai", "Difyai"):
        # match "  "Variant": <value>,"  — value is string of [ ... ]-lijst
        key_re = re.compile(
            r'[ \t]*["\']' + re.escape(variant) + r'["\']\s*:\s*'
            r'(?:"[^"]*"|\'[^\']*\'|\[[^\]]*\])\s*,?\s*\n?')
        if not key_re.search(block):
            continue
        if has_canon:
            block, n = key_re.subn("", block)
            if n:
                changes.append(f"{dname}: variant-key '{variant}' verwijderd ({n}x; 'Dify' bestaat al)")
        else:
            # geen canonieke key → hernoem de variant naar "Dify"
            block, n = re.subn(r'(["\'])' + re.escape(variant) + r'\1(\s*:)',
                               r'"Dify"\2', block, count=1)
            if n:
                has_canon = True
                changes.append(f"{dname}: variant-key '{variant}' hernoemd naar 'Dify'")
    src = src[:a] + block + src[b:]

# ---------- 2) competitor-LIJSTwaarden normaliseren naar "Dify" + dedupe ----------
span = find_dict_span(src, "COMPETITORS")
if span:
    a, b = span
    block = src[a:b]
    before = block
    block = re.sub(r'(["\'])(?:Dify\.ai|Difyai)\1', r'"Dify"', block)
    # dedupe binnen elke lijst: [..., "Dify", ..., "Dify"] -> één "Dify"
    def _dedupe_list(m):
        inner = m.group(1)
        seen, out = set(), []
        for item in re.findall(r'"[^"]*"|\'[^\']*\'', inner):
            key = item.strip("\"'")
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return "[" + ", ".join(out) + "]"
    block = re.sub(r'\[([^\]]*)\]', _dedupe_list, block)
    if block != before:
        changes.append("COMPETITORS: lijstwaarden 'Dify.ai'/'Difyai' -> 'Dify' + gededupet")
    src = src[:a] + block + src[b:]

# ---------- 3) schrijven (backup + compile-gate) ----------
print("=== wijzigingen ===")
if not changes or src == orig:
    print("  geen Dify-varianten om te dedupen — bestand ongewijzigd.")
    raise SystemExit(0)
for c in changes:
    print("  •", c)

bak = AG + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(AG, bak)
open(AG, "w", encoding="utf-8").write(src)
try:
    py_compile.compile(AG, doraise=True)
    print("\n✓ gededupet + syntax OK. backup:", bak)
except py_compile.PyCompileError as e:
    shutil.copy2(bak, AG)
    print("\n✗ syntaxfout — automatisch teruggezet:", e)

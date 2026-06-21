#!/usr/bin/env python3
"""fix_kinsta_truncated.py — de enige mid-artikel afgekapte pagina
(kinsta-woocommerce-hosting-da, inhoud verloren, zwak merk): noindex + netjes
afsluiten zodat hij valide is maar uit de index gaat. Idempotent, push main+staging.
Draai op de VPS:  /root/felix_hq/venv/bin/python3 /tmp/fk.py
"""
import subprocess
from pathlib import Path

REPO = Path("/root/felix_hq/repos/aibuildermarketplace")
f = REPO / "b2b" / "kinsta-woocommerce-hosting-da" / "index.html"
if not f.exists():
    print("✗ bestaat niet"); raise SystemExit(0)
t = f.read_text(encoding="utf-8", errors="ignore")
orig = t

if "content=\"noindex" not in t:
    if "<head>" in t:
        t = t.replace("<head>", '<head>\n<meta name="robots" content="noindex,follow">', 1)
if "</body>" not in t:
    t = t.rstrip() + "\n</body>\n</html>\n"

if t == orig:
    print("= al in orde — skip"); raise SystemExit(0)
f.write_text(t, encoding="utf-8")
print("✓ kinsta-woocommerce-hosting-da: noindex + afgesloten")

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)
git("add", "--", "b2b/kinsta-woocommerce-hosting-da/index.html")
git("commit", "-m", "Fix: noindex + sluit mid-artikel afgekapte kinsta-woocommerce-hosting-da")
git("pull", "--no-rebase", "-X", "ours", "origin", "main")
p1 = git("push", "origin", "HEAD:main"); print("push main    :", (p1.stdout + p1.stderr).strip()[-130:])
p2 = git("push", "origin", "HEAD:victor-staging"); print("push staging :", (p2.stdout + p2.stderr).strip()[-130:])
print("KLAAR — plak alles terug.")

#!/usr/bin/env python3
"""Branded OpenGraph-kaarten (1200x630) per tool, gegenereerd uit data.json.

Draait op de VPS (Pillow + een TTF-font). Voor elke tool een strakke, branded
.png in <repo>/og/<slug>.png: AIBM-stijl, tool-logo (clearbit, met letter-mark
fallback), naam, categorie en een eerlijke ondertitel. Daarna kan de og:image
van de pagina's hierheen wijzen → hogere social-CTR op LinkedIn/X/Slack.

Gebruik (op de VPS, in de repo-root):
    pip install pillow requests        # eenmalig, indien nodig
    python3 build_og_images.py --slug foxit          # 1 sample om te bekijken
    python3 build_og_images.py --limit 3             # 3 samples
    python3 build_og_images.py --all                 # alle tools

Veilig: faalt nooit hard op één tool (logo-download/teken-fouten worden
opgevangen); idempotent (overschrijft dezelfde png).
"""
import argparse
import io
import json
import re
from pathlib import Path

W, H = 1200, 630
BG = (10, 14, 23)
CARD = (26, 31, 46)
TEXT = (241, 245, 249)
MUTED = (148, 163, 184)
ACCENT = (16, 185, 129)
ACCENT_BY_CAT = {
    "Growth & Revenue": (99, 102, 241), "Operations & Workflow": (16, 185, 129),
    "Communication & Voice": (236, 72, 153), "IT & Productivity": (43, 140, 217),
    "Financial Operations": (245, 158, 11),
}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _font(size, bold=True):
    from PIL import ImageFont
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _logo(domain, size=150):
    """Clearbit-logo ophalen; None bij mislukken (dan letter-mark)."""
    try:
        import requests
        from PIL import Image
        r = requests.get(f"https://logo.clearbit.com/{domain}?size=200", timeout=10)
        if r.status_code == 200 and r.content:
            im = Image.open(io.BytesIO(r.content)).convert("RGBA")
            im.thumbnail((size, size))
            return im
    except Exception:
        pass
    return None


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(tool, out_dir):
    from PIL import Image, ImageDraw
    name, cat, dom = tool["name"], tool.get("category", ""), tool.get("domain", "")
    accent = ACCENT_BY_CAT.get(cat, ACCENT)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # accent-balk links
    d.rectangle([0, 0, 14, H], fill=accent)
    # AIBM-wordmark
    d.text((60, 54), "AIBuilder Marketplace", font=_font(30), fill=MUTED)
    # logo-tegel
    box = [60, 150, 230, 320]
    d.rounded_rectangle(box, radius=24, fill=(255, 255, 255))
    logo = _logo(dom)
    if logo:
        lx = box[0] + (170 - logo.width) // 2
        ly = box[1] + (170 - logo.height) // 2
        img.paste(logo, (lx, ly), logo)
    else:
        d.rounded_rectangle(box, radius=24, fill=accent)
        ini = (name[:1] or "?").upper()
        f = _font(96)
        tw = d.textlength(ini, font=f)
        d.text((box[0] + (170 - tw) / 2, box[1] + 30), ini, font=f, fill=(255, 255, 255))
    # naam (groot, ge-wrapt)
    nf = _font(76)
    lines = _wrap(d, name, nf, W - 290)
    y = 160
    for ln in lines[:2]:
        d.text((270, y), ln, font=nf, fill=TEXT)
        y += 88
    # categorie-pill
    if cat:
        cf = _font(28)
        cw = d.textlength(cat, font=cf)
        d.rounded_rectangle([270, y + 6, 270 + cw + 36, y + 56], radius=25, fill=accent)
        d.text((288, y + 14), cat, font=cf, fill=(8, 12, 20))
    # ondertitel onderaan
    d.text((60, H - 90), "Honest founder review · pros, cons & a clear verdict",
           font=_font(34, bold=False), fill=TEXT)
    d.text((60, H - 46), "aibuildermarketplace.com", font=_font(28, bold=False), fill=MUTED)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    out = out_dir / f"{slug}.png"
    img.save(out, "PNG")
    return out.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--data", default=None, help="pad naar data.json (default: <repo>/data.json of affdb)")
    ap.add_argument("--slug", help="één tool op naam/slug")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo)
    data_path = Path(a.data) if a.data else (repo / "data.json" if (repo / "data.json").exists()
                                             else Path("affdb/data.json"))
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    out_dir = repo / "og"
    out_dir.mkdir(exist_ok=True)
    if a.slug:
        s = a.slug.lower()
        data = [t for t in data if s in re.sub(r"[^a-z0-9]+", "-", t["name"].lower())]
    elif a.limit:
        data = data[:a.limit]
    elif not a.all:
        data = data[:3]
        print("(geen --all/--slug/--limit → 3 samples; bekijk ze eerst)")
    done = 0
    for t in data:
        try:
            n = make_card(t, out_dir)
            done += 1
            print(f"  ✓ og/{n}")
        except Exception as e:
            print(f"  ✗ {t['name']}: {e}")
    print(f"{done} OG-kaart(en) in {out_dir}")


if __name__ == "__main__":
    main()

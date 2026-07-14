"""
Crop feed images to Instagram's 4:5 (1080x1350) and write IG-ready JPEGs.

Instagram feed (incl. carousels) only accepts aspect ratios from 4:5 (0.8) to
1.91:1. Our poster masters come in 3:4 (0.747, Higgsfield) or 2:3 (0.667,
ChatGPT) — both too tall. This center-crops the excess height, resizes to
1080x1350, and writes JPEG q88 into images/.

Bias: posters carry the logo near the top and the headline/subtitle near the
bottom. A symmetric center-crop keeps both because the ChatGPT masters were
prompted with a 12% safe zone and the Higgsfield masters only lose ~3% per edge.

Usage:
    python crop_feed.py            # process the flat feed PNGs in Ready to Post
    python crop_feed.py --test     # write 2 test crops into _croptest/ only
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(__file__)
RTP = os.path.expanduser(
    "~/Desktop/JR /Bilder/JR Design/JR DESIGN/BLACKPRINT STUDIO/Claude Code/"
    "Projects/Mabuhay - Filipino Culture Festival/Marketing/Ready to Post"
)
OUT = os.path.join(HERE, "images")
TARGET_W, TARGET_H = 1080, 1350        # Instagram 4:5
TARGET_RATIO = TARGET_W / TARGET_H     # 0.8
BG = (15, 30, 61)
TOP_BIAS = 0.5   # 0.5 = symmetric; lower keeps more of the bottom


def slug(name):
    base = os.path.splitext(name)[0].lower().replace("ß", "ss")
    out = []
    for ch in base:
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_":
            out.append("-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") + ".jpg"


def _bg_color(im):
    """Sample the top-right corner (background, never the left gold border)."""
    w, h = im.size
    patch = im.crop((w - 40, 0, w, 40)).resize((1, 1), Image.LANCZOS)
    return patch.getpixel((0, 0))


def crop_to_45(im):
    """Fit to 4:5 WITHOUT clipping content: too-tall posters get matching
    side-bars in the sampled background colour (logo top + text bottom stay
    intact); too-wide images are centre-cropped on width."""
    im = im.convert("RGB")
    w, h = im.size
    ratio = w / h
    if ratio < TARGET_RATIO:            # too tall -> pad width with bg colour
        new_w = round(h * TARGET_RATIO)
        canvas = Image.new("RGB", (new_w, h), _bg_color(im))
        canvas.paste(im, ((new_w - w) // 2, 0))
        im = canvas
    elif ratio > TARGET_RATIO:          # too wide -> trim width
        new_w = round(h * TARGET_RATIO)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    return im.resize((TARGET_W, TARGET_H), Image.LANCZOS)


def process(src_path, dst_path):
    im = crop_to_45(Image.open(src_path))
    im.save(dst_path, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(dst_path)


def feed_pngs():
    # flat PNGs directly in Ready to Post (skips the Story/ subfolder)
    return sorted(
        f for f in os.listdir(RTP)
        if f.lower().endswith(".png") and os.path.isfile(os.path.join(RTP, f))
    )


def main():
    test = "--test" in sys.argv
    if test:
        out_dir = os.path.join(HERE, "_croptest")
        os.makedirs(out_dir, exist_ok=True)
        picks = [
            "P7 - Carousel Slide 4 - Geschichte.png",   # tight bottom text
            "P7 - Carousel Slide 7 - Geschichte.png",   # logo at top (ChatGPT 2:3)
            "P8 - Feed - Vendor Call.png",              # logo at top (ChatGPT 2:3)
        ]
        for f in picks:
            size = process(os.path.join(RTP, f), os.path.join(out_dir, slug(f)))
            print(f"  {f}  ->  _croptest/{slug(f)}  ({size//1024} KB)")
        return

    os.makedirs(OUT, exist_ok=True)
    for f in feed_pngs():
        size = process(os.path.join(RTP, f), os.path.join(OUT, slug(f)))
        print(f"  {f}  ->  images/{slug(f)}  ({size//1024} KB)")


if __name__ == "__main__":
    main()

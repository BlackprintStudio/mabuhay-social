"""
Image prep — converts source PNGs to Instagram-ready JPEGs.

Instagram rejects images over 8 MB and prefers JPEG. Our rendered PNGs are
6-9 MB each. This resizes to 1080px on the long-ish side (IG display size),
converts to JPEG q88 on a solid background, and writes into images/.

Run locally whenever you add/replace source cards:
    python prep_images.py "<source folder>"
Defaults to the project's "Ready to Post" folder if no argument is given.
"""
import os
import sys
from PIL import Image

DEFAULT_SRC = os.path.expanduser(
    "~/Desktop/JR /Bilder/JR Design/JR DESIGN/BLACKPRINT STUDIO/Claude Code/"
    "Projects/Mabuhay - Filipino Culture Festival/Marketing/Ready to Post"
)
OUT = os.path.join(os.path.dirname(__file__), "images")
MAX_W = 1080          # Instagram feed display width
BG = (15, 30, 61)     # --deep royal blue, for any transparency flatten


def slug(name):
    base = os.path.splitext(name)[0].lower()
    base = base.replace("ß", "ss")
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


def convert(src_path, dst_path):
    im = Image.open(src_path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, BG)
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    im.save(dst_path, "JPEG", quality=88, optimize=True, progressive=True)
    return os.path.getsize(dst_path)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for f in os.listdir(src) if f.lower().endswith((".png", ".jpg", ".jpeg")))
    if not files:
        print(f"No images in {src}")
        return
    for f in files:
        dst_name = slug(f)
        size = convert(os.path.join(src, f), os.path.join(OUT, dst_name))
        print(f"  {f}  ->  images/{dst_name}  ({size//1024} KB)")
    print(f"\n{len(files)} image(s) prepped into {OUT}")


if __name__ == "__main__":
    main()

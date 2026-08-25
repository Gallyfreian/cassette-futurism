#!/usr/bin/env python3
"""Build docs/preview-icons.jpg — a contact sheet of every generated icon."""
import glob, math, os, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "icons"
OUT = sys.argv[2] if len(sys.argv) > 2 else "docs/preview-icons.jpg"
CELL, PAD, COLS = 150, 16, 7
BG = (22, 22, 24)

files = sorted(glob.glob(os.path.join(SRC, "*.png")))
if not files:
    sys.exit(f"no PNGs in {SRC}/")

rows = math.ceil(len(files) / COLS)
sheet = Image.new("RGB", (COLS * (CELL + PAD) + PAD,
                          rows * (CELL + PAD) + PAD), BG)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGBA").resize((CELL, CELL), Image.LANCZOS)
    x = PAD + (i % COLS) * (CELL + PAD)
    y = PAD + (i // COLS) * (CELL + PAD)
    sheet.paste(im, (x, y), im)          # alpha as mask, keeps the squircle

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
sheet.save(OUT, quality=85, optimize=True)
print(f"{OUT}  {len(files)} icons  {sheet.size[0]}x{sheet.size[1]}  "
      f"{os.path.getsize(OUT)/1024:.0f} KB")
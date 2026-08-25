#!/usr/bin/env python3
"""
icon maker folder/app icons for macOS.

Requires wallgen.py alongside it (reuses the Canvas, palettes and bloom).

  python3 icongen.py --out ./icons
  python3 icongen.py --out ./icons --palette green
  python3 icongen.py --out ./icons --map "Chrome=globe,VS Code=code,dev-work=folder"
  python3 icongen.py --list
"""
import argparse, math, os, shutil, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wallgen import Canvas, PALETTES, load_font, crt_geometry, _bilinear  # noqa: E402


# ------------------------------------------------------------------ glyphs
# Each takes (canvas, box=(x,y,w,h), lw) and draws inside the box.

def g_folder(c, b, lw):
    x, y, w, h = b
    tab = w * 0.42
    c.line([(x, y + h * 0.86), (x, y + h * 0.20), (x + tab, y + h * 0.20),
            (x + tab + w * 0.09, y + h * 0.34), (x + w, y + h * 0.34),
            (x + w, y + h * 0.86), (x, y + h * 0.86)], lw)
    for i in range(1, 4):
        c.line([(x + w * 0.10, y + h * (0.46 + i * 0.12)),
                (x + w * 0.90, y + h * (0.46 + i * 0.12))], lw * 0.55, 150)


def g_terminal(c, b, lw):
    x, y, w, h = b
    c.rect(x, y + h * 0.10, x + w, y + h * 0.90, lw)
    c.line([(x, y + h * 0.26), (x + w, y + h * 0.26)], lw * 0.8, 210)
    for i, cx in enumerate((0.10, 0.19, 0.28)):
        c.circle(x + w * cx, y + h * 0.18, w * 0.022, 0, 220, fill=True)
    c.line([(x + w * 0.14, y + h * 0.44), (x + w * 0.30, y + h * 0.56),
            (x + w * 0.14, y + h * 0.68)], lw * 1.2)
    c.line([(x + w * 0.38, y + h * 0.70), (x + w * 0.74, y + h * 0.70)], lw * 1.2)


def g_globe(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    c.circle(cx, cy, r, lw)
    for k in (-0.62, -0.3, 0, 0.3, 0.62):
        rr = r * math.sqrt(max(0.02, 1 - k * k))
        c.line([(cx - rr, cy + k * r), (cx + rr, cy + k * r)], lw * 0.7, 215)
    for f in (0.34, 0.72):
        c.ellipse(cx, cy, r * f, r, lw * 0.7, 215)
    c.line([(cx, cy - r), (cx, cy + r)], lw * 0.7, 215)


def g_code(c, b, lw):
    x, y, w, h = b
    c.line([(x + w * 0.34, y + h * 0.20), (x + w * 0.06, y + h * 0.50),
            (x + w * 0.34, y + h * 0.80)], lw * 1.3)
    c.line([(x + w * 0.66, y + h * 0.20), (x + w * 0.94, y + h * 0.50),
            (x + w * 0.66, y + h * 0.80)], lw * 1.3)
    c.line([(x + w * 0.58, y + h * 0.14), (x + w * 0.42, y + h * 0.86)], lw * 1.0, 210)


def g_compass(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    c.circle(cx, cy, r, lw)
    c.circle(cx, cy, r * 0.86, lw * 0.5, 150)
    a = math.radians(-38)
    for s in (1, -1):
        tip = (cx + s * r * 0.62 * math.cos(a), cy + s * r * 0.62 * math.sin(a))
        wing = (cx - s * r * 0.20 * math.sin(a), cy + s * r * 0.20 * math.cos(a))
        wing2 = (cx + s * r * 0.20 * math.sin(a), cy - s * r * 0.20 * math.cos(a))
        c.line([tip, wing, wing2, tip], lw * (1.1 if s > 0 else 0.7),
               255 if s > 0 else 180)
    for i in range(0, 360, 30):
        aa = math.radians(i)
        t = r * (0.14 if i % 90 == 0 else 0.08)
        c.line([(cx + r * 0.94 * math.cos(aa), cy + r * 0.94 * math.sin(aa)),
                (cx + (r * 0.94 - t) * math.cos(aa),
                 cy + (r * 0.94 - t) * math.sin(aa))], lw * 0.6, 200)


def g_starburst(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    for i in range(16):
        a = 2 * math.pi * i / 16
        inner = r * (0.16 if i % 2 == 0 else 0.22)
        outer = r * (1.0 if i % 2 == 0 else 0.72)
        c.line([(cx + inner * math.cos(a), cy + inner * math.sin(a)),
                (cx + outer * math.cos(a), cy + outer * math.sin(a))], lw * 1.15)
    c.circle(cx, cy, r * 0.12, lw)


def g_disc(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    c.circle(cx, cy, r, lw)
    c.circle(cx, cy, r * 0.62, lw * 0.7, 210)
    c.circle(cx, cy, r * 0.16, 0, 255, fill=True)
    for i in range(0, 360, 24):
        a = math.radians(i)
        c.line([(cx + r * 0.70 * math.cos(a), cy + r * 0.70 * math.sin(a)),
                (cx + r * 0.94 * math.cos(a), cy + r * 0.94 * math.sin(a))],
               lw * 0.55, 170)


def g_chat(c, b, lw):
    x, y, w, h = b
    c.rect(x, y + h * 0.14, x + w * 0.72, y + h * 0.62, lw)
    c.line([(x + w * 0.18, y + h * 0.62), (x + w * 0.22, y + h * 0.80),
            (x + w * 0.40, y + h * 0.62)], lw)
    c.rect(x + w * 0.34, y + h * 0.44, x + w, y + h * 0.86, lw * 0.8, 210)
    for i in (0.28, 0.40):
        c.line([(x + w * 0.08, y + h * i), (x + w * 0.60, y + h * i)], lw * 0.55, 160)


def g_person_scan(c, b, lw):
    x, y, w, h = b
    cx = x + w / 2
    c.circle(cx, y + h * 0.20, w * 0.13, lw)
    c.line([(cx, y + h * 0.34), (cx, y + h * 0.66)], lw)
    c.line([(x + w * 0.18, y + h * 0.44), (x + w * 0.82, y + h * 0.44)], lw)
    c.line([(cx, y + h * 0.66), (x + w * 0.26, y + h * 0.90)], lw)
    c.line([(cx, y + h * 0.66), (x + w * 0.74, y + h * 0.90)], lw)
    for sx, sy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        bx = x + sx * w
        by = y + sy * h
        c.line([(bx + (1 - 2 * sx) * w * 0.20, by), (bx, by),
                (bx, by + (1 - 2 * sy) * h * 0.20)], lw * 0.9, 200)


def g_document(c, b, lw):
    x, y, w, h = b
    fold = w * 0.28
    c.line([(x + w * 0.10, y), (x + w * 0.10, y + h), (x + w * 0.90, y + h),
            (x + w * 0.90, y + fold), (x + w * 0.90 - fold, y),
            (x + w * 0.10, y)], lw)
    c.line([(x + w * 0.90 - fold, y), (x + w * 0.90 - fold, y + fold),
            (x + w * 0.90, y + fold)], lw * 0.8, 215)
    for i in range(4):
        c.line([(x + w * 0.22, y + h * (0.46 + i * 0.13)),
                (x + w * 0.78, y + h * (0.46 + i * 0.13))], lw * 0.6, 165)


def g_aperture(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    c.circle(cx, cy, r, lw)
    for i in range(6):
        a0 = 2 * math.pi * i / 6
        a1 = a0 + 2 * math.pi / 6
        c.line([(cx + r * 0.95 * math.cos(a0), cy + r * 0.95 * math.sin(a0)),
                (cx + r * 0.30 * math.cos(a1), cy + r * 0.30 * math.sin(a1))],
               lw * 0.85, 225)
    c.circle(cx, cy, r * 0.28, lw * 0.7, 200)


def g_film(c, b, lw):
    x, y, w, h = b
    c.rect(x, y + h * 0.16, x + w, y + h * 0.84, lw)
    for i in range(5):
        for sy in (0.22, 0.72):
            c.rect(x + w * (0.06 + i * 0.19), y + h * sy,
                   x + w * (0.14 + i * 0.19), y + h * (sy + 0.06), lw * 0.6, 175)
    c.line([(x + w * 0.42, y + h * 0.40), (x + w * 0.62, y + h * 0.50),
            (x + w * 0.42, y + h * 0.60), (x + w * 0.42, y + h * 0.40)], lw)


def g_bin(c, b, lw):
    x, y, w, h = b
    c.line([(x + w * 0.06, y + h * 0.22), (x + w * 0.94, y + h * 0.22)], lw)
    c.line([(x + w * 0.36, y + h * 0.22), (x + w * 0.36, y + h * 0.12),
            (x + w * 0.64, y + h * 0.12), (x + w * 0.64, y + h * 0.22)], lw * 0.8)
    c.line([(x + w * 0.16, y + h * 0.22), (x + w * 0.24, y + h * 0.92),
            (x + w * 0.76, y + h * 0.92), (x + w * 0.84, y + h * 0.22)], lw)
    for i in (0.38, 0.50, 0.62):
        c.line([(x + w * i, y + h * 0.34), (x + w * (i + 0.02), y + h * 0.82)],
               lw * 0.6, 170)


def g_gear(c, b, lw):
    x, y, w, h = b
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    teeth = 9
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        c.line([(cx + r * 0.72 * math.cos(a), cy + r * 0.72 * math.sin(a)),
                (cx + r * math.cos(a), cy + r * math.sin(a))], lw * 1.6)
    c.circle(cx, cy, r * 0.70, lw)
    c.circle(cx, cy, r * 0.26, lw * 0.8, 215)


def g_waveform(c, b, lw):
    x, y, w, h = b
    c.rect(x, y + h * 0.16, x + w, y + h * 0.84, lw * 0.8, 190)
    pts = []
    for k in range(220):
        u = k / 219
        v = (math.sin(u * 7.5) * 0.55 + math.sin(u * 21) * 0.25)
        pts.append((x + u * w, y + h * 0.50 - v * h * 0.26))
    c.line(pts, lw * 1.1)


def g_database(c, b, lw):
    x, y, w, h = b
    cx = x + w / 2
    ry = h * 0.11
    for i in range(3):
        top = y + h * (0.16 + i * 0.26)
        c.ellipse(cx, top, w * 0.42, ry, lw)
        c.line([(cx - w * 0.42, top), (cx - w * 0.42, top + h * 0.26)], lw * 0.8)
        c.line([(cx + w * 0.42, top), (cx + w * 0.42, top + h * 0.26)], lw * 0.8)


def g_chart(c, b, lw):
    x, y, w, h = b
    c.line([(x + w * 0.08, y + h * 0.10), (x + w * 0.08, y + h * 0.90),
            (x + w * 0.94, y + h * 0.90)], lw)
    vals = [0.35, 0.62, 0.28, 0.78, 0.52, 0.90]
    for i, v in enumerate(vals):
        bx = x + w * (0.20 + i * 0.13)
        c.line([(bx, y + h * 0.90), (bx, y + h * (0.90 - v * 0.72))], lw * 1.7)


def g_lock(c, b, lw):
    x, y, w, h = b
    c.rect(x + w * 0.14, y + h * 0.44, x + w * 0.86, y + h * 0.92, lw)
    c.arc(x + w / 2, y + h * 0.44, w * 0.24, 180, 360, lw, ry=h * 0.24)
    c.line([(x + w * 0.26, y + h * 0.44), (x + w * 0.26, y + h * 0.32)], lw)
    c.line([(x + w * 0.74, y + h * 0.44), (x + w * 0.74, y + h * 0.32)], lw)
    c.circle(x + w / 2, y + h * 0.64, w * 0.06, lw * 0.9, 230)
    c.line([(x + w / 2, y + h * 0.68), (x + w / 2, y + h * 0.80)], lw * 0.9, 230)


def g_network(c, b, lw):
    x, y, w, h = b
    nodes = [(0.5, 0.14), (0.14, 0.52), (0.86, 0.52), (0.32, 0.90), (0.68, 0.90)]
    for i, (a, bb) in enumerate(nodes):
        for j, (cc, dd) in enumerate(nodes):
            if j > i and (i == 0 or abs(i - j) == 1):
                c.line([(x + w * a, y + h * bb), (x + w * cc, y + h * dd)],
                       lw * 0.7, 185)
    for a, bb in nodes:
        c.circle(x + w * a, y + h * bb, w * 0.075, lw)


def g_mail(c, b, lw):
    x, y, w, h = b
    c.rect(x, y + h * 0.20, x + w, y + h * 0.80, lw)
    c.line([(x, y + h * 0.20), (x + w / 2, y + h * 0.56),
            (x + w, y + h * 0.20)], lw * 0.9, 225)


def g_grid(c, b, lw):
    x, y, w, h = b
    n = 4
    for i in range(n):
        for j in range(n):
            filled = (i + j) % 3 == 0
            gx, gy = x + i * w / n, y + j * h / n
            c.rect(gx + w * 0.03, gy + h * 0.03,
                   gx + w / n - w * 0.03, gy + h / n - h * 0.03,
                   lw * 0.8, 255)
            if filled:
                c.d.rectangle([(gx + w * 0.06) * c.ss, (gy + h * 0.06) * c.ss,
                               (gx + w / n - w * 0.06) * c.ss,
                               (gy + h / n - h * 0.06) * c.ss], fill=235)


GLYPHS = {
    "folder": g_folder, "terminal": g_terminal, "globe": g_globe, "code": g_code,
    "compass": g_compass, "starburst": g_starburst, "disc": g_disc,
    "chat": g_chat, "person": g_person_scan, "document": g_document,
    "aperture": g_aperture, "film": g_film, "bin": g_bin, "gear": g_gear,
    "waveform": g_waveform, "database": g_database, "chart": g_chart,
    "lock": g_lock, "network": g_network, "mail": g_mail, "grid": g_grid,
}

def make_icon(glyph, size=1024, palette="amber", label=None,
              inset=0.055, radius=0.2237, scan=0.30, scan_lines=34, crt=0.12,
              ca=0.008, ss=2):
    p = PALETTES[palette]
    S = size
    Sf = crt_geometry(S, S, crt)[1] if crt > 0 else 1.0
    D = int(round(S * Sf))

    c = Canvas(D, D, ss)
    pad = D * inset
    x0, y0, x1, y1 = pad, pad, D - pad, D - pad
    tw = x1 - x0
    rad = tw * radius
    lw = max(2.0, D / 150)

    shape = Image.new("L", (D * ss, D * ss), 0)
    ImageDraw.Draw(shape).rounded_rectangle(
        [x0 * ss, y0 * ss, x1 * ss, y1 * ss], radius=rad * ss, fill=255)

    c.d.rounded_rectangle([(x0 + tw * .045) * ss, (y0 + tw * .045) * ss,
                           (x1 - tw * .045) * ss, (y1 - tw * .045) * ss],
                          radius=(rad - tw * .045) * ss,
                          outline=200, width=max(1, int(lw * 0.75 * ss)))

    gbox_pad = tw * (0.30 if label else 0.24)
    gy = y0 + gbox_pad * (0.82 if label else 1.0)
    gh = tw - gbox_pad * (1.55 if label else 2.0)
    GLYPHS[glyph](c, (x0 + gbox_pad, gy, tw - 2 * gbox_pad, gh), lw)

    if label:
        c.text(D / 2, y1 - tw * 0.115, label.upper()[:9], tw * 0.085, 245,
               anchor="mm", track=tw * 0.016)

    mask = c.img.resize((D, D), Image.LANCZOS)
    alpha = np.asarray(shape.resize((D, D), Image.LANCZOS)).astype(np.float32) / 255.0
    m = np.asarray(mask).astype(np.float32) / 255.0

    img = np.zeros((D, D, 3), np.float32)
    img[:] = np.array(p["bg"], np.float32) * 1.5

    glow, core = np.array(p["glow"], np.float32), np.array(p["core"], np.float32)
    for radius_px, amount in ((max(1, D // 220), 0.80),
                              (max(3, D // 70), 0.55),
                              (max(9, D // 22), 0.30)):
        b = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius_px))
                       ).astype(np.float32) / 255.0
        img += (b ** 0.85)[..., None] * glow * amount
    img += (m ** 1.25)[..., None] * core * 1.05
    img += (m ** 3.0)[..., None] * np.float32(255) * 0.16

    # scanlines go on BEFORE the barrel, so they bow with the tube
    if scan > 0:
        period = max(3.0, D / float(max(4, scan_lines)))
        rows = np.arange(D, dtype=np.float32)
        img *= np.clip(1.0 + scan * np.cos(2 * math.pi * rows / period),
                       0.0, None)[:, None, None]

    yy = np.linspace(0, 1, D, dtype=np.float32)[:, None]
    img += (np.clip(1 - yy * 3.2, 0, 1) * 9)[..., None]
    img *= alpha[..., None]

    if crt > 0:
        u = np.linspace(-1, 1, S, dtype=np.float32)[None, :]
        v = np.linspace(-1, 1, S, dtype=np.float32)[:, None]
        qn = (u * u + v * v) / 2.0
        out = np.zeros((S, S, 3), np.float32)
        a_out = None
        for ch, tint in enumerate((1.0 + ca, 1.0, 1.0 - ca)):
            f = (1.0 + crt * tint * qn) / Sf
            xs = (u * f * 0.5 + 0.5) * (D - 1)
            ys = (v * f * 0.5 + 0.5) * (D - 1)
            xs, ys = np.broadcast_arrays(xs, ys)
            out[..., ch] = _bilinear(img[..., ch], xs, ys)
            if ch == 1:
                a_out = _bilinear(alpha, xs, ys)
        out *= (1.0 - 0.32 * np.clip(qn, 0, 1) ** 1.4)[..., None]
        img, alpha = out, a_out
    else:
        img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
                         .resize((S, S), Image.LANCZOS)).astype(np.float32)
        alpha = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8))
                           .resize((S, S), Image.LANCZOS)).astype(np.float32) / 255.0

    rgba = np.dstack([np.clip(img, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

# --------------------------------------------------------------------- icns
# Apple's iconset needs these exact filenames. Small renditions are drawn
# fresh at their target size rather than downscaled, so line weights and
# scanlines stay legible instead of turning to mush.
ICNS_SIZES = [
    (16, "icon_16x16"), (32, "icon_16x16@2x"),
    (32, "icon_32x32"), (64, "icon_32x32@2x"),
    (128, "icon_128x128"), (256, "icon_128x128@2x"),
    (256, "icon_256x256"), (512, "icon_256x256@2x"),
    (512, "icon_512x512"), (1024, "icon_512x512@2x"),
]


def _detail_for(px, scan, scan_lines, crt):
    """Dial back tube effects on renditions too small to carry them."""
    if px <= 32:
        return 0.0, scan_lines, crt * 0.35
    if px <= 64:
        return scan * 0.5, max(10, scan_lines // 3), crt * 0.6
    if px <= 128:
        return scan * 0.8, max(16, scan_lines // 2), crt * 0.85
    return scan, scan_lines, crt


def build_icns(glyph, out_path, palette="amber", label=None,
               scan=0.30, scan_lines=34, crt=0.12):
    """Render every rendition, then hand the iconset to iconutil."""
    if shutil.which("iconutil") is None:
        print(f"  skipping {out_path}: iconutil not found (macOS only)")
        return False

    stem = os.path.splitext(out_path)[0]
    iconset = stem + ".iconset"
    os.makedirs(iconset, exist_ok=True)
    try:
        for px, name in ICNS_SIZES:
            s, sl, k = _detail_for(px, scan, scan_lines, crt)
            img = make_icon(glyph, px, palette, label=label if px >= 256 else None,
                            scan=s, scan_lines=sl, crt=k)
            img.save(os.path.join(iconset, name + ".png"))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out_path],
                       check=True)
        return True
    finally:
        shutil.rmtree(iconset, ignore_errors=True)

DEFAULT_MAP = {
    "Folder": "folder", "Terminal": "terminal", "Browser": "globe",
    "Code": "code", "Safari": "compass", "Launcher": "starburst",
    "Media": "disc", "Chat": "chat", "Accessibility": "person",
    "Docs": "document", "Screenshots": "aperture", "Videos": "film",
    "Trash": "bin", "Settings": "gear", "Audio": "waveform",
    "Data": "database", "Stats": "chart", "Certs": "lock",
    "Network": "network", "Mail": "mail", "Apps": "grid",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./icons")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--palette", default="amber",
                    choices=sorted(PALETTES.keys()))
    ap.add_argument("--map", default=None,
                    help='"Name=glyph,Name=glyph" — filename=glyph pairs')
    ap.add_argument("--label", action="store_true",
                    help="print the name across the bottom of each icon")
    ap.add_argument("--crt", type=float, default=0.12,
                    help="tube bulge: 0 flat, 0.12 default, 0.25 strong")
    ap.add_argument("--scan", type=float, default=0.30,
                    help="scanline depth, 0 off .. 0.5 heavy")
    ap.add_argument("--scan-lines", type=int, default=34,
                    help="how many scanlines across the icon (fewer = chunkier, "
                         "survives Dock downscaling)")
    ap.add_argument("--icns", action="store_true",
                help="also build a multi-resolution .icns (macOS only)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        print("glyphs:", ", ".join(sorted(GLYPHS)))
        return

    pairs = DEFAULT_MAP.items()
    if a.map:
        pairs = []
        for tok in a.map.split(","):
            name, _, gl = tok.partition("=")
            gl = gl.strip() or "folder"
            if gl not in GLYPHS:
                sys.exit(f"unknown glyph {gl!r}; try --list")
            pairs.append((name.strip(), gl))

    os.makedirs(a.out, exist_ok=True)
    for name, gl in pairs:
        img = make_icon(gl, a.size, a.palette,
                        label=name if a.label else None, crt=a.crt, scan=a.scan, scan_lines=a.scan_lines)
        safe = name.replace("/", "-").replace(" ", "_")
        path = os.path.join(a.out, f"{safe}.png")
        img.save(path)
        print(path)

        if a.icns:
            if build_icns(gl, os.path.join(a.out, f"{safe}.icns"), a.palette,
                            label=name if a.label else None,
                            scan=a.scan, scan_lines=a.scan_lines, crt=a.crt):
                print(os.path.join(a.out, f"{safe}.icns"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
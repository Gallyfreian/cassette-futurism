"""
wallgen — cassette futurism / terminal-UI wallpaper generator.

Line art is drawn into a luminance mask, bloomed like a phosphor tube, then
run through a CRT stage: barrel distortion, chromatic aberration, curved
scanlines, aperture mask, vignette.

  python3 wallgen.py --size 5120x1440 --count 12 --out ./out
  python3 wallgen.py --size 3456x2234 --seed 91 --palette green --crt 0.18
  python3 wallgen.py --size 3840x2160 --flat --count 4
"""
import argparse, math, os, random, sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ------------------------------------------------------------------ fonts
_FONTS = {
    True: [("/System/Library/Fonts/Menlo.ttc", 1),
           ("/System/Library/Fonts/Supplemental/Courier New Bold.ttf", 0),
           ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 0),
           ("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 0),
           ("C:/Windows/Fonts/consolab.ttf", 0)],
    False: [("/System/Library/Fonts/Menlo.ttc", 0),
            ("/System/Library/Fonts/Supplemental/Courier New.ttf", 0),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 0),
            ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 0),
            ("C:/Windows/Fonts/consola.ttf", 0)],
}


@lru_cache(maxsize=None)
def load_font(size, bold=True):
    for path, idx in _FONTS[bool(bold)] + _FONTS[not bool(bold)]:
        if not os.path.exists(path):
            continue
        for i in (idx, 0):
            try:
                return ImageFont.truetype(path, max(1, size), index=i)
            except OSError:
                pass
    raise OSError("No monospace font found — add a path to _FONTS.")


# ---------------------------------------------------------------- palettes
PALETTES = {
    "amber": dict(bg=(11, 10, 9),  core=(255, 196, 140), glow=(255, 106, 0)),
    "green": dict(bg=(7, 11, 9),   core=(190, 255, 205), glow=(0, 220, 110)),
    "ice":   dict(bg=(8, 10, 14),  core=(200, 232, 255), glow=(0, 150, 255)),
    "blood": dict(bg=(12, 8, 8),   core=(255, 178, 170), glow=(230, 40, 40)),
    "bone":  dict(bg=(10, 10, 11), core=(255, 250, 240), glow=(190, 180, 160)),
}

STATIONS = ["ARTEMIS-IV", "KEPLER-9", "MERIDIAN-II", "TYCHO-B", "HALCYON",
            "VOSTOK-7", "ORPHEUS-1", "CALLISTO-3", "HYPERION", "ARCADIA-V"]
WORDMARKS = ["NEXUS", "VECTOR", "AXIOM", "HELIOS", "PRISM", "CIPHER",
             "LATTICE", "APEX", "QUANTA", "OBELISK", "SIGNAL", "ORACLE"]
STATES = ["STABLE", "NOMINAL", "LOCKED", "DRIFTING", "SYNCED", "STANDBY"]


# ------------------------------------------------------------------ canvas
class Canvas:
    """Vector line art into an L-mode luminance mask at ss× scale."""

    def __init__(self, w, h, ss=2):
        self.w, self.h, self.ss = w, h, ss
        self.img = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.img)

    def _w(self, width):
        return max(1, int(round(width * self.ss)))

    def line(self, pts, width=2, v=255):
        if len(pts) < 2:
            return
        self.d.line([(x * self.ss, y * self.ss) for x, y in pts],
                    fill=int(v), width=self._w(width), joint="curve")

    def rect(self, x0, y0, x1, y1, width=2, v=255):
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], width, v)

    def circle(self, cx, cy, r, width=2, v=255, fill=False):
        b = [(cx - r) * self.ss, (cy - r) * self.ss,
             (cx + r) * self.ss, (cy + r) * self.ss]
        if fill:
            self.d.ellipse(b, fill=int(v))
        else:
            self.d.ellipse(b, outline=int(v), width=self._w(width))

    def ellipse(self, cx, cy, rx, ry, width=2, v=255):
        self.d.ellipse([(cx - rx) * self.ss, (cy - ry) * self.ss,
                        (cx + rx) * self.ss, (cy + ry) * self.ss],
                       outline=int(v), width=self._w(width))

    def arc(self, cx, cy, r, a0, a1, width=2, v=255, ry=None):
        ry = r if ry is None else ry
        self.d.arc([(cx - r) * self.ss, (cy - ry) * self.ss,
                    (cx + r) * self.ss, (cy + ry) * self.ss],
                   a0, a1, fill=int(v), width=self._w(width))

    def text(self, x, y, s, size, v=255, anchor="la", track=0.0, bold=True):
        f = load_font(int(size * self.ss), bold)
        if track == 0:
            self.d.text((x * self.ss, y * self.ss), s, font=f,
                        fill=int(v), anchor=anchor)
            return
        adv = f.getlength("M") + track * self.ss
        total = adv * len(s)
        ox = -total / 2 if anchor[0] == "m" else (-total if anchor[0] == "r" else 0)
        cx = x * self.ss + ox
        for ch in s:
            self.d.text((cx, y * self.ss), ch, font=f, fill=int(v),
                        anchor="l" + anchor[1])
            cx += adv


# ------------------------------------------------------------------ heroes
def hero_globe(c, box, rng, lw):
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    R = min(w, h) / 2 * rng.uniform(0.88, 0.99)
    step = rng.choice([11, 13, 15, 18])
    tilt, spin = rng.uniform(-0.34, -0.06), rng.uniform(0, 1.2)
    ct, st = math.cos(tilt), math.sin(tilt)
    cs, sn = math.cos(spin), math.sin(spin)

    def proj(px, py, pz):
        px, pz = px * cs - pz * sn, px * sn + pz * cs
        py, pz = py * ct - pz * st, py * st + pz * ct
        return cx + px, cy - py, pz

    def poly(pts3):
        run = []
        for p in pts3:
            X, Y, Z = proj(*p)
            if Z > 0:
                run.append((X, Y))
            else:
                if len(run) > 1:
                    c.line(run, lw, 255)
                run = []
        if len(run) > 1:
            c.line(run, lw, 255)

    for lat in range(-72, 73, step):
        a = math.radians(lat)
        r, yy = R * math.cos(a), R * math.sin(a)
        poly([(r * math.cos(t), yy, r * math.sin(t))
              for t in np.linspace(0, 2 * math.pi, 300)])
    cap = math.radians(81)
    for lon in range(0, 180, step):
        a = math.radians(lon)
        for t0, t1 in ((-cap, cap), (math.pi - cap, math.pi + cap)):
            poly([(R * math.cos(t) * math.cos(a), R * math.sin(t),
                   R * math.cos(t) * math.sin(a))
                  for t in np.linspace(t0, t1, 200)])


def hero_radar(c, box, rng, lw):
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    R = min(w, h) / 2 * 0.96
    rings = rng.randint(5, 9)
    for i in range(1, rings + 1):
        c.circle(cx, cy, R * i / rings, lw * (1.0 if i == rings else 0.7),
                 255 if i == rings else 200)
    spokes = rng.choice([8, 12, 16])
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        c.line([(cx + R * 0.14 * math.cos(a), cy + R * 0.14 * math.sin(a)),
                (cx + R * math.cos(a), cy + R * math.sin(a))], lw * 0.6, 165)
    sweep = rng.uniform(0, 2 * math.pi)
    c.line([(cx, cy), (cx + R * math.cos(sweep), cy + R * math.sin(sweep))], lw * 1.3)
    for _ in range(rng.randint(3, 7)):
        a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0.2, 0.95) * R
        bx, by = cx + d * math.cos(a), cy + d * math.sin(a)
        c.circle(bx, by, R * 0.022, 0, 255, fill=True)
        c.circle(bx, by, R * 0.055, lw * 0.6, 190)
    for i in range(0, 360, 5):
        a = math.radians(i)
        t = R * (0.055 if i % 45 == 0 else 0.028)
        c.line([(cx + (R + R * 0.02) * math.cos(a), cy + (R + R * 0.02) * math.sin(a)),
                (cx + (R + R * 0.02 + t) * math.cos(a),
                 cy + (R + R * 0.02 + t) * math.sin(a))], lw * 0.6, 200)


def hero_horizon(c, box, rng, lw):
    """Perspective ground grid under a banded sun."""
    x, y, w, h = box
    hz = y + h * 0.46
    cx = x + w / 2
    sr = min(w, h) * rng.uniform(0.20, 0.30)
    c.arc(cx, hz, sr, 180, 360, lw, 255)
    for k in range(1, 6):
        yy = hz - sr * (k / 6.0)
        half = sr * math.sqrt(max(0.0, 1 - (k / 6.0) ** 2))
        c.line([(cx - half, yy), (cx + half, yy)], lw * 0.9, 235)
    c.line([(x, hz), (x + w, hz)], lw * 1.1, 255)
    rows = rng.randint(9, 14)
    for i in range(1, rows + 1):
        t = (i / rows) ** 2.3
        yy = hz + t * (y + h - hz)
        c.line([(x, yy), (x + w, yy)], lw * 0.75, int(120 + 135 * t))
    cols = rng.choice([12, 16, 20])
    for i in range(-cols, cols + 1):
        c.line([(cx + i * (w / cols) * 0.12, hz),
                (cx + i * (w / cols) * 1.9, y + h)], lw * 0.7, 190)


def hero_orbits(c, box, rng, lw):
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    R = min(w, h) / 2 * 0.95
    c.circle(cx, cy, R * 0.10, 0, 255, fill=True)
    c.circle(cx, cy, R * 0.19, lw, 230)
    for i in range(rng.randint(4, 7)):
        rx = R * rng.uniform(0.35, 1.0)
        ry = rx * rng.uniform(0.12, 0.45)
        ang = rng.uniform(0, math.pi)
        pts = []
        for t in np.linspace(0, 2 * math.pi, 260):
            px, py = rx * math.cos(t), ry * math.sin(t)
            pts.append((cx + px * math.cos(ang) - py * math.sin(ang),
                        cy + px * math.sin(ang) + py * math.cos(ang)))
        c.line(pts + [pts[0]], lw * 0.85, 225)
        t = rng.uniform(0, 2 * math.pi)
        px, py = rx * math.cos(t), ry * math.sin(t)
        c.circle(cx + px * math.cos(ang) - py * math.sin(ang),
                 cy + px * math.sin(ang) + py * math.cos(ang),
                 R * 0.035, 0, 255, fill=True)


def hero_reticle(c, box, rng, lw):
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    R = min(w, h) / 2 * 0.95
    c.circle(cx, cy, R, lw * 1.1)
    c.circle(cx, cy, R * 0.62, lw * 0.8, 215)
    c.circle(cx, cy, R * 0.08, lw * 0.8, 255)
    for a0 in (0, 90, 180, 270):
        c.arc(cx, cy, R * 0.82, a0 + 8, a0 + 82, lw * 0.9, 235)
    gap = R * 0.16
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c.line([(cx + dx * gap, cy + dy * gap),
                (cx + dx * R * 1.22, cy + dy * R * 1.22)], lw)
    for i in range(0, 360, 6):
        a = math.radians(i)
        t = R * (0.09 if i % 30 == 0 else 0.045)
        c.line([(cx + R * math.cos(a), cy + R * math.sin(a)),
                (cx + (R - t) * math.cos(a), cy + (R - t) * math.sin(a))],
               lw * 0.6, 205)
    for corner in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bx, by = cx + corner[0] * R * 1.05, cy + corner[1] * R * 1.05
        c.line([(bx - corner[0] * R * 0.22, by), (bx, by),
                (bx, by - corner[1] * R * 0.22)], lw)


def hero_waveform(c, box, rng, lw):
    x, y, w, h = box
    c.rect(x, y, x + w, y + h, lw)
    traces = rng.randint(3, 5)
    for i in range(1, 5):
        c.line([(x, y + h * i / 5), (x + w, y + h * i / 5)], lw * 0.5, 90)
    for i in range(1, 8):
        c.line([(x + w * i / 8, y), (x + w * i / 8, y + h)], lw * 0.5, 90)
    for t in range(traces):
        base = y + h * (t + 0.5) / traces
        amp = h / traces * rng.uniform(0.16, 0.40)
        f1, f2 = rng.uniform(1.5, 5), rng.uniform(6, 18)
        ph = rng.uniform(0, 6)
        pts = []
        for k in range(500):
            u = k / 499
            yy = base + amp * (math.sin(u * f1 * math.pi * 2 + ph) * 0.7 +
                               math.sin(u * f2 * math.pi * 2 + ph * 2) * 0.3)
            pts.append((x + u * w, yy))
        c.line(pts, lw * 0.9, 245)


HEROES = [hero_globe, hero_radar, hero_horizon, hero_orbits,
          hero_reticle, hero_waveform]


# ----------------------------------------------------------------- widgets
def w_dotmatrix(c, box, rng, lw):
    x, y, w, h = box
    cols, rows = rng.randint(4, 6), rng.randint(3, 4)
    pitch = min(w / cols, h / rows)
    ox, oy = x + (w - pitch * (cols - 1)) / 2, y + (h - pitch * (rows - 1)) / 2
    r = pitch * 0.30
    for i in range(cols):
        for j in range(rows):
            big = i >= cols - 2
            filled = rng.random() < 0.55
            c.circle(ox + i * pitch, oy + j * pitch,
                     r * (1.3 if big else 1.0), lw * 0.8, 255, fill=filled)


def w_ruler(c, box, rng, lw):
    x, y, w, h = box
    base = y + h * 0.75
    n = rng.choice([18, 24, 30])
    c.line([(x, base), (x + w, base)], lw)
    for i in range(n + 1):
        t = i / n
        hh = h * (0.55 if i % 12 == 0 else (0.34 if i % 5 == 0 else 0.18))
        c.line([(x + t * w, base), (x + t * w, base - hh)], lw * 0.8, 235)


def w_bars(c, box, rng, lw):
    x, y, w, h = box
    base = y + h * 0.88
    n = rng.choice([12, 16, 22])
    for i in range(n):
        bh = h * 0.8 * (0.15 + 0.85 * abs(math.sin(i * rng.uniform(0.5, 1.2)
                                                   + rng.random())))
        c.line([(x + i * w / n, base), (x + i * w / n, base - bh)], lw * 1.1)


def w_smallglobe(c, box, rng, lw):
    x, y, w, h = box
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) * 0.36
    c.circle(cx, cy, r, lw)
    if rng.random() < 0.5:
        for k in (-0.55, -0.2, 0.2, 0.55):
            rr = r * math.sqrt(max(0.02, 1 - k * k))
            c.line([(cx - rr + 0.22 * r * k, cy + k * r),
                    (cx + rr + 0.22 * r * k, cy + k * r)], lw * 0.7, 220)
    else:
        c.line([(cx - r * 1.4, cy), (cx + r * 1.4, cy)], lw * 0.7, 235)
        c.line([(cx, cy - r * 1.4), (cx, cy + r * 1.4)], lw * 0.7, 235)
        c.ellipse(cx, cy, r * 0.42, r, lw * 0.7, 210)


def w_stack(c, box, rng, lw):
    x, y, w, h = box
    n = rng.randint(3, 5)
    for i in range(n):
        f = i / (n * 2.2)
        c.rect(x + w * f, y + h * f, x + w * (1 - f), y + h * (1 - f),
               lw * 0.9, 255 - i * 22)


def w_hatch(c, box, rng, lw):
    x, y, w, h = box
    c.rect(x, y, x + w, y + h, lw)
    step = min(w, h) / rng.randint(5, 10)
    k = -w
    while k < w + h:
        x0, y0 = x + k, y
        x1, y1 = x + k + h, y + h
        x0c, y0c = max(x, min(x + w, x0)), y0
        x1c, y1c = max(x, min(x + w, x1)), y1
        if x1 > x and x0 < x + w:
            c.line([(x0c, y0c), (x1c, y1c)], lw * 0.6, 170)
        k += step


def w_keypad(c, box, rng, lw):
    x, y, w, h = box
    cols, rows = rng.randint(3, 5), rng.randint(2, 4)
    pw, ph = w / cols, h / rows
    for i in range(cols):
        for j in range(rows):
            gx, gy = x + i * pw, y + j * ph
            if rng.random() < 0.3:
                c.d.rectangle([(gx + pw * .12) * c.ss, (gy + ph * .12) * c.ss,
                               (gx + pw * .88) * c.ss, (gy + ph * .88) * c.ss],
                              fill=245)
            else:
                c.rect(gx + pw * .12, gy + ph * .12,
                       gx + pw * .88, gy + ph * .88, lw * 0.8, 225)


def w_gauge(c, box, rng, lw):
    x, y, w, h = box
    cx, cy, r = x + w / 2, y + h * 0.72, min(w, h * 1.4) * 0.42
    c.arc(cx, cy, r, 180, 360, lw)
    c.arc(cx, cy, r * 0.72, 180, 360, lw * 0.7, 200)
    for i in range(11):
        a = math.pi + math.pi * i / 10
        t = r * (0.20 if i % 5 == 0 else 0.11)
        c.line([(cx + r * math.cos(a), cy + r * math.sin(a)),
                (cx + (r - t) * math.cos(a), cy + (r - t) * math.sin(a))],
               lw * 0.7, 230)
    a = math.pi + math.pi * rng.uniform(0.1, 0.9)
    c.line([(cx, cy), (cx + r * 0.82 * math.cos(a), cy + r * 0.82 * math.sin(a))], lw * 1.2)
    c.circle(cx, cy, r * 0.07, 0, 255, fill=True)


def w_readout(c, box, rng, lw):
    x, y, w, h = box
    lines = [f"STATION  {rng.choice(STATIONS)}",
             f"SECTOR   {rng.randint(1,9)}{rng.choice('GKRT')}-{rng.choice(['ALPHA','BETA','DELTA','OMEGA'])}",
             f"ORBIT    {rng.choice(STATES)}",
             f"CREW     {rng.randint(3,48)} ACTIVE",
             f"UPTIME   {rng.randint(100,9999)}H"]
    lines = lines[:rng.randint(3, 5)]
    size = min(h / (len(lines) * 1.7), w / 19)
    lead = size * 1.85
    top = y + (h - lead * (len(lines) - 1)) / 2
    for i, s in enumerate(lines):
        c.text(x, top + i * lead, s, size, 210, anchor="lm", track=size * 0.20)


def w_blocklabel(c, box, rng, lw):
    x, y, w, h = box
    c.rect(x, y, x + w, y + h, lw)
    s = rng.choice(["SYS", "NAV", "AUX", "PWR", "COM", "DIA", "REC"])
    c.text(x + w / 2, y + h / 2, s, min(h * 0.5, w / (len(s) * 0.85)),
           255, anchor="mm", track=h * 0.06)


WIDGETS = [(w_dotmatrix, 1), (w_ruler, 2), (w_bars, 2), (w_smallglobe, 1),
           (w_stack, 1), (w_hatch, 1), (w_keypad, 1), (w_gauge, 1),
           (w_readout, 3), (w_blocklabel, 1)]


# ------------------------------------------------------------------ layout
def compose(c, W, H, rng, busy=1.0, wordmark=None):
    lw = max(1.8, min(W, H) / 430)
    wide = W / H > 2.0
    mx = int(W * (0.055 if wide else 0.075))
    my = int(H * (0.085 if wide else 0.070))
    gap = max(5, int(H * (0.010 if wide else 0.0075)))
    drop = int(H * (0.055 if wide else 0.042))

    # frame rails
    style = rng.choice(["double", "double", "bracket", "single"])
    by = H - my
    c.line([(mx, my), (W - mx, my)], lw)
    c.line([(mx, by), (W - mx, by)], lw)
    if style in ("double", "bracket"):
        c.line([(mx, my + gap), (W - mx - drop, my + gap),
                (W - mx - drop, my + gap + drop)], lw)
        c.line([(mx + drop, by - gap - drop), (mx + drop, by - gap),
                (W - mx, by - gap)], lw)
    if style == "bracket":
        c.line([(mx, my), (mx, my + drop * 1.4)], lw)
        c.line([(W - mx, by), (W - mx, by - drop * 1.4)], lw)

    # content grid
    cx0, cy0 = mx + drop * 0.6, my + gap + drop * 0.9
    cw, ch = (W - mx - drop * 0.6) - cx0, (by - gap - drop * 0.9) - cy0
    cols, rows = (10, 3) if wide else (6, 4)
    cellw, cellh = cw / cols, ch / rows
    used = [[False] * cols for _ in range(rows)]

    def cell(i, j, ci=1, ri=1, pad=0.12):
        px, py = cellw * pad, cellh * pad
        return (cx0 + i * cellw + px, cy0 + j * cellh + py,
                cellw * ci - 2 * px, cellh * ri - 2 * py)

    # hero block
    hc, hr = (3, 3) if wide else (4, 2)
    if wide:
        hi = rng.choice([0, 1, cols - hc, cols - hc - 1])
    else:
        hi = rng.choice([0, 1, cols - hc])
    hj = 0 if wide else rng.choice([0, 1])
    hero = rng.choice(HEROES)
    hero(c, cell(hi, hj, hc, hr, pad=0.02), rng, lw)
    for i in range(hi, hi + hc):
        for j in range(hj, hj + hr):
            used[j][i] = True

    # reserve the corner so no widget lands on it
    mark_left = hi >= cols / 2
    if wordmark != "none":
        for k in range(2):
            ci = k if mark_left else cols - 1 - k
            if 0 <= ci < cols:
                used[rows - 1][ci] = True

    # keep a breathing zone in the middle of ultrawides
    if wide and busy < 1.0:
        for i in range(int(cols * 0.38), int(cols * 0.62)):
            for j in range(rows):
                if rng.random() > busy:
                    used[j][i] = True

    # scatter widgets
    slots = [(i, j) for j in range(rows) for i in range(cols) if not used[j][i]]
    rng.shuffle(slots)
    target = int(len(slots) * rng.uniform(0.35, 0.60) * busy)
    placed = 0
    pool = WIDGETS[:]
    counts = {}
    for i, j in slots:
        if placed >= target:
            break
        if used[j][i]:
            continue
        fn, span = rng.choice(pool)
        if counts.get(fn, 0) >= 2:
            pool = [t for t in pool if t[0] is not fn] or WIDGETS[:]
            fn, span = rng.choice(pool)
        counts[fn] = counts.get(fn, 0) + 1
        span = min(span, cols - i)
        while span > 1 and any(used[j][i + k] for k in range(span)):
            span -= 1
        if span < 1:
            continue
        if fn is w_readout and span < 3:
            fn, span = w_dotmatrix, 1
        fn(c, cell(i, j, span, 1), rng, lw)
        for k in range(span):
            used[j][i + k] = True
        placed += 1

    # wordmark
    if wordmark != "none":
        mark = wordmark if wordmark else rng.choice(WORDMARKS)
        size = H * (0.075 if wide else 0.055)
        base = by - gap - H * 0.085
        if mark_left:
            c.text(mx + drop * 1.2, base, mark, size, 255,
                   anchor="ls", track=size * 0.27)
        else:
            c.text(W - mx, base, mark, size, 255, anchor="rs", track=size * 0.27)


# ------------------------------------------------------------------- CRT
def _bilinear(src, xs, ys):
    """src (H,W) float32; xs/ys float coord arrays. Out-of-bounds -> 0."""
    h, w = src.shape
    x0 = np.floor(xs).astype(np.int32)
    y0 = np.floor(ys).astype(np.int32)
    fx, fy = (xs - x0).astype(np.float32), (ys - y0).astype(np.float32)
    ok = (x0 >= 0) & (x0 < w - 1) & (y0 >= 0) & (y0 < h - 1)
    x0c, y0c = np.clip(x0, 0, w - 2), np.clip(y0, 0, h - 2)
    a = src[y0c, x0c]
    b = src[y0c, x0c + 1]
    cc = src[y0c + 1, x0c]
    d = src[y0c + 1, x0c + 1]
    out = (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy)
           + cc * (1 - fx) * fy + d * fx * fy)
    return out * ok


def crt_geometry(W, H, k, ax=None):
    """Returns (ax, Sx, Sy) — Sx/Sy are how much larger the source must be."""
    if ax is None:
        ax = min(1.0, max(0.30, (16.0 / 9.0) / (W / H)))
    kx, ky = k * ax, k
    Sx = 1.0 + kx * (ax / (ax + 1.0))
    Sy = 1.0 + ky * (1.0 / (ax + 1.0))
    return ax, Sx, Sy


def crt(src, W, H, k=0.14, ax=None, ca=0.006, scan=0.34, scan_px=4.0, mask=0.09,
        vignette=0.50, corner=0.035):
    """Barrel-distort src (H2,W2,3 float) down to W x H with tube effects."""
    H2, W2 = src.shape[:2]
    ax, Sx, Sy = crt_geometry(W, H, k, ax)
    kx, ky = k * ax, k

    u = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    v = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    qn = (ax * u * u + v * v) / (ax + 1.0)      # 0 centre .. 1 corners

    out = np.zeros((H, W, 3), np.float32)
    sy_mid = None
    for ch, tint in enumerate((1.0 + ca, 1.0, 1.0 - ca)):
        su = u * (1.0 + kx * tint * qn) / Sx
        sv = v * (1.0 + ky * tint * qn) / Sy
        xs = (su * 0.5 + 0.5) * (W2 - 1)
        ys = (sv * 0.5 + 0.5) * (H2 - 1)
        out[..., ch] = _bilinear(src[..., ch], xs, ys)
        if ch == 1:
            sy_mid, su_mid, sv_mid = ys, su, sv

    # scanlines phase off the source row, so they bow with the tube
    if scan > 0:
        period = max(2.5, scan_px * (H2 / float(H)))
        out *= np.clip(1.0 + scan * np.cos(2 * math.pi * sy_mid / period),
                       0.0, None)[..., None]

    # aperture-grille triads
    if mask > 0:
        cols = np.arange(W)
        m = np.ones((W, 3), np.float32)
        for ch in range(3):
            m[:, ch] = 1.0 - mask * ((cols % 3) != ch)
        out *= m[None, :, :]

    # hard tube edge, softened a touch
    inside = ((np.abs(su_mid) <= 1.0) & (np.abs(sv_mid) <= 1.0))
    inside = np.broadcast_to(inside, (H, W)).astype(np.uint8) * 255
    inside = np.asarray(Image.fromarray(inside).filter(
        ImageFilter.GaussianBlur(max(1, H // 900)))).astype(np.float32) / 255.0
    out *= inside[..., None]

    if vignette > 0:
        out *= (1.0 - vignette * np.clip(qn, 0, 1) ** 1.5)[..., None]

    if corner > 0:
        axc = np.clip((np.abs(u) - (1 - corner)) / corner, 0, 1)
        ayc = np.clip((np.abs(v) - (1 - corner)) / corner, 0, 1)
        out *= (1.0 - np.clip(np.sqrt(axc ** 2 + ayc ** 2), 0, 1) ** 2.2)[..., None]
    return out


# ---------------------------------------------------------------- renderer
def render(W, H, seed=None, palette=None, crt_k=0.14, busy=0.55,
           grain=True, wordmark=None, scan=0.34, scan_px=4.0, out="out.png"):
    rng = random.Random(seed)
    pal = palette if palette in PALETTES else rng.choice(list(PALETTES))
    p = PALETTES[pal]

    if crt_k > 0:
        _, Sx, Sy = crt_geometry(W, H, crt_k)
    else:
        Sx = Sy = 1.0
    W2, H2 = int(round(W * Sx)), int(round(H * Sy))
    ss = 2 if W2 * H2 > 8_000_000 else 3

    c = Canvas(W2, H2, ss)
    compose(c, W2, H2, rng, busy=busy, wordmark=wordmark)
    mask = c.img.resize((W2, H2), Image.LANCZOS)
    m = np.asarray(mask).astype(np.float32) / 255.0

    img = np.zeros((H2, W2, 3), np.float32)
    img[:] = np.array(p["bg"], np.float32)

    glow = np.array(p["glow"], np.float32)
    core = np.array(p["core"], np.float32)
    for radius, amount in ((max(2, H2 // 260), 0.85),
                           (max(6, H2 // 90), 0.60),
                           (max(18, H2 // 26), 0.32)):
        b = np.asarray(mask.filter(ImageFilter.GaussianBlur(radius))
                       ).astype(np.float32) / 255.0
        img += (b ** 0.85)[..., None] * glow * amount
    img += (m ** 1.25)[..., None] * core * 1.05
    img += (m ** 3.0)[..., None] * np.float32(255) * 0.18

    if crt_k > 0:
        img = crt(img, W, H, k=crt_k, scan=scan, scan_px=scan_px)
    else:
        img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
                         .resize((W, H), Image.LANCZOS)).astype(np.float32)
        if scan > 0:
            rows = np.arange(H, dtype=np.float32)
            img *= np.clip(1.0 + scan * np.cos(2 * math.pi * rows / max(2.5, scan_px)),
                           0.0, None)[:, None, None]

    if grain:
        img += np.random.default_rng(seed or 0).normal(
            0, 3.0, (H, W, 1)).astype(np.float32)

     # write to a temp name first: an interrupt mid-save would otherwise
    # leave a truncated PNG behind
    tmp = out + ".part"
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(tmp, format="PNG")
    os.replace(tmp, out)
    return pal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="5120x1440", help="WIDTHxHEIGHT")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--palette", default=None,
                    help="amber|green|ice|blood|bone (default: random per image)")
    ap.add_argument("--crt", type=float, default=0.14,
                    help="barrel strength; 0.06 subtle, 0.14 default, 0.24 heavy")
    ap.add_argument("--flat", action="store_true", help="disable the CRT stage")
    ap.add_argument("--busy", type=float, default=0.55,
                    help="0.2 sparse .. 1.0 dense instrument clutter")
    ap.add_argument("--scan", type=float, default=0.34,
                    help="scanline depth, 0 off .. 0.6 heavy")
    ap.add_argument("--scan-px", type=float, default=4.0,
                    help="scanline period in output pixels (4 at 4K, 2.5 at 1080p)")
    ap.add_argument("--wordmark", default=None,
                    help="fixed wordmark text, or 'none' to omit it")
    ap.add_argument("--out", default="./wallpapers")
    a = ap.parse_args()

    W, H = (int(t) for t in a.size.lower().split("x"))
    os.makedirs(a.out, exist_ok=True)
    base = a.seed if a.seed is not None else random.randrange(1 << 30)
    for i in range(a.count):
        seed = base + i
        name = os.path.join(a.out, f"wall_{W}x{H}_{seed}.png")
        pal = render(W, H, seed=seed, palette=a.palette,
                     crt_k=0.0 if a.flat else a.crt, busy=a.busy, wordmark=a.wordmark,
                     scan=a.scan, scan_px=a.scan_px, out=name)
        print(f"{name}  [{pal}]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
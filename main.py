#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Renders, in pure-stdlib Python, an open passport spread for the invented
Republic of Vostria: a data page (portrait, personal data, machine-readable
zone) and a facing visa page (a Dalmara tourist visa, entry/exit stamps from
neighbouring Karstovia and Dalmara, and a fee stamp). No network, no
third-party libraries, no randomness, no timestamps: the output is fully
deterministic. Writes entry.png to $MAKEFUN_OUTPUT_DIR (or /output, or the
current directory when neither exists).
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# 5x7 bitmap font (uppercase, digits, punctuation). '#' = ink, '.' = empty.
# ---------------------------------------------------------------------------
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}

CHAR_W, CHAR_H = 5, 7


def text_mask(text, spacing=1):
    """Render text to a 1-bit mask (bytes, 1 = ink). Unknown chars -> space."""
    n = len(text)
    w = n * (CHAR_W + spacing) - spacing if n else 0
    mask = bytearray(w * CHAR_H)
    for i, ch in enumerate(text):
        glyph = FONT.get(ch, FONT[' '])
        ox = i * (CHAR_W + spacing)
        for row in range(CHAR_H):
            bits = glyph[row]
            for col in range(CHAR_W):
                if bits[col] == '1':
                    mask[row * w + ox + col] = 1
    return mask, w, CHAR_H


def text_width(text, scale, spacing=1):
    if not text:
        return 0
    return int(round((len(text) * (CHAR_W + spacing) - spacing) * scale))


# ---------------------------------------------------------------------------
# Canvas: RGB buffer with drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def blend_px(self, x, y, color, alpha):
        """Alpha-blend color over the pixel (alpha 0..1)."""
        if 0 <= x < self.w and 0 <= y < self.h and alpha > 0:
            i = self._idx(x, y)
            if alpha >= 1:
                self.px[i], self.px[i + 1], self.px[i + 2] = color
            else:
                for c in range(3):
                    self.px[i + c] = int(round(
                        self.px[i + c] * (1 - alpha) + color[c] * alpha))

    def fill_rect(self, x, y, w, h, color, alpha=1.0):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                self.blend_px(xx, yy, color, alpha)

    def rect(self, x, y, w, h, color, t=1, alpha=1.0):
        for k in range(t):
            self.hline(x + k, y + k, x + w - k, color, alpha)
            self.hline(x + k, y + h - 1 - k, x + w - k, color, alpha)
            self.vline(x + k, y, y + h, color, alpha)
            self.vline(x + w - 1 - k, y, y + h, color, alpha)

    def hline(self, x0, y, x1, color, alpha=1.0):
        if x0 > x1:
            x0, x1 = x1, x0
        for x in range(max(0, x0), min(self.w, x1)):
            self.blend_px(x, y, color, alpha)

    def vline(self, x, y0, y1, color, alpha=1.0):
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(max(0, y0), min(self.h, y1)):
            self.blend_px(x, y, color, alpha)

    def line(self, x0, y0, x1, y1, color, alpha=1.0):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.blend_px(x, y, color, alpha)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, color, fill=False, alpha=1.0):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.blend_px(xx, yy, color, alpha)
                else:
                    if abs(d2 - r * r) <= r:
                        self.blend_px(xx, yy, color, alpha)

    def ellipse(self, cx, cy, rx, ry, color, fill=False, alpha=1.0):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                v = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
                if fill:
                    if v <= 1.0:
                        self.blend_px(xx, yy, color, alpha)
                else:
                    if abs(v - 1.0) <= 0.06:
                        self.blend_px(xx, yy, color, alpha)

    def polygon(self, points, color, alpha=1.0):
        """Scanline fill of a simple polygon."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.blend_px(x, y, color, alpha)

    def blit_mask(self, mask, mw, mh, x, y, scale, color, alpha=1.0):
        """Nearest-neighbour upscale of a 1-bit mask onto the canvas."""
        sw = int(round(mw * scale))
        sh = int(round(mh * scale))
        for dy in range(sh):
            sy = min(mh - 1, int(dy / scale))
            for dx in range(sw):
                sx = min(mw - 1, int(dx / scale))
                if mask[sy * mw + sx]:
                    self.blend_px(x + dx, y + dy, color, alpha)

    def blit_mask_rotated(self, mask, mw, mh, cx, cy, angle_deg, scale,
                          color, alpha=1.0):
        """Blit a mask rotated by angle_deg around (cx, cy), scaled."""
        import math
        th = math.radians(angle_deg)
        ct, st = math.cos(th), math.sin(th)
        sw = int(round(mw * scale))
        sh = int(round(mh * scale))
        hw, hh = sw / 2.0, sh / 2.0
        for dy in range(-int(hh) - 1, int(hh) + 2):
            for dx in range(-int(hw) - 1, int(hw) + 2):
                # inverse rotation into source coords
                sx = (dx * ct + dy * st) / scale + mw / 2.0
                sy = (-dx * st + dy * ct) / scale + mh / 2.0
                ix, iy = int(sx), int(sy)
                if 0 <= ix < mw and 0 <= iy < mh and mask[iy * mw + ix]:
                    self.blend_px(int(cx + dx), int(cy + dy), color, alpha)

    def paste(self, src, x, y):
        """Copy another canvas's pixels onto this one at (x, y)."""
        for yy in range(src.h):
            dy = y + yy
            if 0 <= dy < self.h:
                for xx in range(src.w):
                    dx = x + xx
                    if 0 <= dx < self.w:
                        i = self._idx(dx, dy)
                        j = (yy * src.w + xx) * 3
                        self.px[i:i + 3] = src.px[j:j + 3]

    def text(self, x, y, s, scale, color, spacing=1, alpha=1.0):
        mask, mw, mh = text_mask(s, spacing)
        self.blit_mask(mask, mw, mh, x, y, scale, color, alpha)
        return x + int(round(mw * scale))

    def text_centered(self, cx, y, s, scale, color, spacing=1, alpha=1.0):
        w = text_width(s, scale, spacing)
        self.text(cx - w // 2, y, s, scale, color, spacing, alpha)

    def text_rotated(self, cx, cy, s, scale, angle_deg, color, spacing=1,
                     alpha=1.0):
        mask, mw, mh = text_mask(s, spacing)
        self.blit_mask_rotated(mask, mw, mh, cx, cy, angle_deg, scale,
                               color, alpha)


# ---------------------------------------------------------------------------
# Minimal PNG encoder (stdlib only): 8-bit RGB, filter 0, zlib level 9.
# ---------------------------------------------------------------------------
def encode_png(canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
TABLE = (46, 50, 56)          # dark table the passport lies on
PAGE_L = (238, 240, 234)      # data page paper
PAGE_R = (244, 239, 226)      # visa page paper
INK = (28, 43, 58)            # dark navy ink
INK_SOFT = (74, 88, 102)      # secondary ink
LABEL = (110, 118, 126)       # field labels
RULE = (150, 158, 160)        # rules and borders
MRZ_BG = (214, 219, 216)      # machine-readable zone band
STAMP_BLUE = (43, 76, 155)
STAMP_RED = (163, 51, 39)
STAMP_GREEN = (46, 107, 52)
STAMP_PURPLE = (107, 63, 140)
VISA_BG = (233, 236, 203)     # visa sticker paper
GOLD = (176, 141, 63)

W, H = 1024, 640
PAGE_W, PAGE_H = 478, 580
PAGE_Y = 30
LEFT_X, RIGHT_X = 22, 524


def star_points(cx, cy, r_out, r_in, rot=-90):
    import math
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36)
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    return pts


def draw_emblem(c, cx, cy, r, color):
    """Coat of arms: double ring, five-point star over a mountain ridge."""
    c.circle(cx, cy, r, color)
    c.circle(cx, cy, r - 4, color)
    c.polygon(star_points(cx, cy - 4, r - 10, (r - 10) // 2 + 2), color)
    base = cy + r - 8
    c.polygon([(cx - r + 8, base), (cx - 12, cy + 6),
               (cx, cy + 14), (cx + 12, cy + 6), (cx + r - 8, base)],
              color)


def draw_portrait(w, h):
    """Stylised passport portrait on its own canvas: a two-tone bust
    silhouette, no face. Drawing on a separate canvas clips the
    shoulders to the photo frame instead of spilling onto the page."""
    c = Canvas(w, h, (207, 216, 222))
    # pale blue-grey backdrop with fine horizontal lines
    for yy in range(h):
        t = yy / h
        col = tuple(int(a + (b - a) * t)
                    for a, b in zip((207, 216, 222), (178, 190, 199)))
        c.hline(0, yy, w, col)
    for yy in range(5, h, 7):
        c.hline(0, yy, w, (196, 205, 212))
    cx = w // 2
    # shoulders / jacket (clipped at the frame's bottom edge)
    c.ellipse(cx, h + 22, w // 2 + 6, 52, (51, 65, 79), fill=True)
    # shirt V and collar
    c.polygon([(cx - 12, h - 34), (cx + 12, h - 34),
               (cx, h - 8)], (226, 231, 233))
    c.polygon([(cx - 22, h - 40), (cx - 8, h - 26),
               (cx - 14, h - 14), (cx - 28, h - 26)], (40, 53, 66))
    c.polygon([(cx + 22, h - 40), (cx + 8, h - 26),
               (cx + 14, h - 14), (cx + 28, h - 26)], (40, 53, 66))
    # neck
    c.fill_rect(cx - 11, 118, 22, 26, (58, 68, 80))
    # head
    c.ellipse(cx, 88, 27, 34, (58, 68, 80), fill=True)
    # hair: darker cap over the top of the head
    c.ellipse(cx, 66, 27, 22, (36, 44, 54), fill=True)
    c.polygon([(cx - 27, 66), (cx - 24, 92), (cx - 16, 72),
               (cx - 6, 58), (cx + 6, 58), (cx + 16, 72),
               (cx + 24, 92), (cx + 27, 66)], (36, 44, 54))
    # light rim on the left side of the silhouette
    c.ellipse(cx - 3, 88, 24, 31, (84, 96, 108), fill=True, alpha=0.35)
    c.ellipse(cx, 88, 27, 34, (58, 68, 80), fill=False)
    return c


def field(c, x, y, label, value, scale=1.6, label_scale=1.0, gap=11):
    c.text(x, y, label, label_scale, LABEL)
    c.text(x, y + gap, value, scale, INK)


def draw_data_page(c):
    x0, y0 = LEFT_X, PAGE_Y
    c.fill_rect(x0, y0, PAGE_W, PAGE_H, PAGE_L)
    c.rect(x0, y0, PAGE_W, PAGE_H, (120, 126, 124), t=1)
    # spine shadow on the right edge (the gutter side)
    for k in range(6):
        c.vline(x0 + PAGE_W - 1 - k, y0, y0 + PAGE_H,
                (0, 0, 0), alpha=0.05 * (6 - k) / 6)

    # --- header ---
    draw_emblem(c, x0 + 52, y0 + 42, 26, GOLD)
    c.text_centered(x0 + PAGE_W // 2 + 18, y0 + 26,
                    "REPUBLIC OF VOSTRIA", 2.2, INK)
    c.text_centered(x0 + PAGE_W // 2 + 18, y0 + 52,
                    "PASSPORT  -  PASSEPORT", 1.3, INK_SOFT)
    c.hline(x0 + 24, y0 + 76, x0 + PAGE_W - 24, RULE)
    c.hline(x0 + 24, y0 + 79, x0 + PAGE_W - 24, RULE)

    # --- portrait ---
    px, py, pw, ph = x0 + 26, y0 + 96, 140, 178
    c.paste(draw_portrait(pw, ph), px, py)
    c.rect(px, py, pw, ph, INK, t=2)
    c.text_centered(px + pw // 2, py + ph + 6, "PHOTO", 0.9, LABEL)

    # --- personal data, right of the portrait ---
    fx = x0 + 186
    field(c, fx, y0 + 96, "SURNAME / NOM", "KOVAC")
    field(c, fx, y0 + 132, "GIVEN NAMES / PRENOMS", "ELENA MARA")
    field(c, fx, y0 + 168, "NATIONALITY / NATIONALITE", "VOSTRIAN")
    field(c, fx, y0 + 204, "SEX / SEXE", "F")
    field(c, fx, y0 + 240, "DATE OF BIRTH / NEE LE", "14 MAR 1994")
    field(c, fx, y0 + 276, "PLACE OF BIRTH / LIEU", "PORT AURELIA")

    # --- document data, below the portrait ---
    dy = y0 + 300
    field(c, x0 + 26, dy, "PASSPORT NO / NO DU PASSEPORT", "VS 4839201")
    field(c, x0 + 246, dy, "TYPE / TYPE", "P")
    field(c, x0 + 26, dy + 36, "DATE OF ISSUE / DELIVRE LE", "02 JUN 2026")
    field(c, x0 + 246, dy + 36, "DATE OF EXPIRY / EXPIRE LE", "01 JUN 2036")
    field(c, x0 + 26, dy + 72, "AUTHORITY / AUTORITE",
          "MINISTRY OF THE INTERIOR", scale=1.3)
    field(c, x0 + 26, dy + 108, "PLACE OF ISSUE / LIEU DE DELIVRANCE",
          "PORT AURELIA", scale=1.3)

    # --- holder's signature ---
    sy = y0 + 452
    c.text(x0 + 26, sy, "SIGNATURE OF HOLDER / SIGNATURE", 0.9, LABEL)
    sx = x0 + 26
    c.line(sx, sy + 26, sx + 30, sy + 18, INK)
    c.line(sx + 30, sy + 18, sx + 55, sy + 28, INK)
    c.line(sx + 55, sy + 28, sx + 80, sy + 16, INK)
    c.line(sx + 80, sy + 16, sx + 105, sy + 26, INK)
    c.line(sx + 105, sy + 26, sx + 130, sy + 20, INK)
    c.hline(x0 + 26, sy + 32, x0 + 176, RULE)

    # --- machine-readable zone ---
    mz = y0 + 496
    c.fill_rect(x0 + 1, mz, PAGE_W - 2, PAGE_H - mz - 1, MRZ_BG)
    c.text_centered(x0 + PAGE_W // 2, mz + 10,
                    "P<VOSKOVAC<<ELENA<MARA<<<<<<<<<<<<<<", 1.35, INK,
                    spacing=2)
    c.text_centered(x0 + PAGE_W // 2, mz + 34,
                    "VS4839201<0VOS9403142F3606017<<<<<<<<<<<<<08", 1.35,
                    INK, spacing=2)


def draw_rect_stamp(c, cx, cy, w, h, lines, color, angle, scale=1.4):
    """A rectangular ink stamp, drawn on a temp canvas then rotated in."""
    pad = 26
    t = Canvas(w + 2 * pad, h + 2 * pad, (255, 255, 255))
    t.rect(pad, pad, w, h, color, t=3)
    t.rect(pad + 6, pad + 6, w - 12, h - 12, color, t=1)
    y = pad + 14
    for i, ln in enumerate(lines):
        t.text_centered(pad + w // 2, y, ln, scale if i == 0 else scale * 0.85,
                        color)
        y += int(13 * scale) + 4
    c.blit_mask_rotated(_canvas_mask(t), t.w, t.h, cx, cy, angle, 1.0,
                        color, alpha=0.82)


def draw_circle_stamp(c, cx, cy, r, lines, color, angle, scale=1.3):
    """Circular ink stamp: place name on top, action above the star,
    date below it. lines = [place, '', action, date]."""
    pad = 26
    d = 2 * r
    t = Canvas(d + 2 * pad, d + 2 * pad, (255, 255, 255))
    cc = pad + r
    t.circle(cc, cc, r, color)
    t.circle(cc, cc, r - 5, color)
    t.polygon(star_points(cc, cc + 2, 9, 4), color)
    t.text_centered(cc, pad + 16, lines[0], 1.0, color)
    t.text_centered(cc, cc - 34, lines[2], scale, color)
    t.text_centered(cc, cc + 22, lines[3], scale, color)
    c.blit_mask_rotated(_canvas_mask(t), t.w, t.h, cx, cy, angle, 1.0,
                        color, alpha=0.82)


def _canvas_mask(t):
    """1-bit mask of all non-white pixels of a temp canvas."""
    mask = bytearray(t.w * t.h)
    for i in range(t.w * t.h):
        if t.px[i * 3] < 250 or t.px[i * 3 + 1] < 250 or t.px[i * 3 + 2] < 250:
            mask[i] = 1
    return mask


def draw_visa_page(c):
    x0, y0 = RIGHT_X, PAGE_Y
    c.fill_rect(x0, y0, PAGE_W, PAGE_H, PAGE_R)
    c.rect(x0, y0, PAGE_W, PAGE_H, (120, 126, 124), t=1)
    # spine shadow on the left edge (the gutter side)
    for k in range(6):
        c.vline(x0 + k, y0, y0 + PAGE_H, (0, 0, 0),
                alpha=0.05 * (6 - k) / 6)

    # faint guilloche wave in the one clear lane: below the visa sticker
    # (ends y0+188) and above the top stamp row (starts ~y0+231), so it
    # never strikes through stamp text
    import math
    for xx in range(x0 + 12, x0 + PAGE_W - 12):
        yy = 210 + int(5 * math.sin((xx - x0) / 26.0))
        c.blend_px(xx, yy, (196, 182, 150), 0.5)
        c.blend_px(xx, yy + 3, (196, 182, 150), 0.35)

    # header
    c.text(x0 + 26, y0 + 22, "VISAS", 1.8, INK)
    c.text(x0 + PAGE_W - 60, y0 + 22, "12", 1.8, INK_SOFT)
    c.hline(x0 + 26, y0 + 44, x0 + PAGE_W - 26, RULE)

    # faint diagonal watermark (kept very light so stamps stay legible)
    c.text_rotated(x0 + PAGE_W // 2, y0 + 330, "VOSTRIA", 3.2, -28,
                   (196, 182, 150), spacing=6, alpha=0.28)

    # --- Dalmara tourist visa sticker ---
    vx, vy, vw, vh = x0 + 26, y0 + 60, PAGE_W - 52, 128
    c.fill_rect(vx, vy, vw, vh, VISA_BG)
    c.rect(vx, vy, vw, vh, (120, 128, 90), t=2)
    for xx in range(vx + 4, vx + vw - 4, 10):
        c.blend_px(xx, vy + 4, (120, 128, 90), 0.8)
        c.blend_px(xx, vy + vh - 5, (120, 128, 90), 0.8)
    c.text(vx + 14, vy + 12, "VISA  -  REPUBLIC OF DALMARA", 1.5, INK)
    c.text(vx + 14, vy + 36, "TYPE: TOURIST  -  SINGLE ENTRY", 1.3, INK)
    c.text(vx + 14, vy + 56, "VALID: 05 OCT 2026 - 03 NOV 2026", 1.3, INK)
    c.text(vx + 14, vy + 76, "CONDITION: NO PAID EMPLOYMENT", 1.3, INK)
    c.text(vx + 14, vy + 96, "FEE PAID: 25 DRA  -  RECEIPT 8841", 1.3, INK)
    c.text(vx + vw - 92, vy + 12, "NO 0471", 1.2, INK_SOFT)

    # --- stamps, in travel order ---
    # Vostria exit, 12 Jun 2026 (just after issue, 02 Jun 2026)
    draw_circle_stamp(c, x0 + 118, y0 + 300, 62,
                      ["PORT AURELIA", "", "DEPARTED", "12 JUN 2026"],
                      STAMP_PURPLE, -11)
    # Karstovia arrival, 18 Sep 2026
    draw_rect_stamp(c, x0 + 330, y0 + 268, 190, 74,
                    ["KARSTOVIA", "ARRIVED", "18 SEP 2026"],
                    STAMP_BLUE, 7)
    # Karstovia departure, 02 Oct 2026
    draw_rect_stamp(c, x0 + 150, y0 + 430, 190, 74,
                    ["KARSTOVIA", "DEPARTED", "02 OCT 2026"],
                    STAMP_RED, -6)
    # Dalmara arrival, 05 Oct 2026 (matches the visa validity)
    draw_circle_stamp(c, x0 + 360, y0 + 430, 62,
                      ["DALMARA", "", "ARRIVED", "05 OCT 2026"],
                      STAMP_GREEN, 9)

    # --- remarks box ---
    rx, ry, rw, rh = x0 + 26, y0 + 508, PAGE_W - 52, 56
    c.rect(rx, ry, rw, rh, RULE, t=1)
    c.text(rx + 10, ry + 8, "OBSERVATIONS / REMARKS", 1.0, LABEL)
    c.text(rx + 10, ry + 26,
           "HOLDER IS A CITIZEN OF VOSTRIA. THIS", 1.1, INK_SOFT)
    c.text(rx + 10, ry + 40,
           "PASSPORT REMAINS STATE PROPERTY.", 1.1, INK_SOFT)


def render():
    c = Canvas(W, H, TABLE)
    # soft drop shadow under the spread
    c.fill_rect(LEFT_X + 6, PAGE_Y + 8, PAGE_W * 2 + 24, PAGE_H,
                (0, 0, 0), alpha=0.25)
    draw_data_page(c)
    draw_visa_page(c)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError:
        out_dir = "."
    path = os.path.join(out_dir, "entry.png")
    png = encode_png(render())
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""news-image-20261123: one-page newspaper front page for Monday 23 Nov 2026.

Pure Python standard library. Draws a 1024x1024 PNG newspaper front page
summing up six real stories from Monday 23 November 2026 and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output). Deterministic: every run
writes byte-identical output. No network, no file reads, no randomness.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (246, 241, 229)
INK = (22, 30, 46)
NAVY = (22, 35, 63)
GOLD = (201, 162, 39)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
MUTED = (90, 96, 108)
RULE = (180, 172, 150)

# ------------------------------------------------------------- PNG encoder --
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, pixels):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            raw += bytes(pixels[y * W + x])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ------------------------------------------------------------------ canvas --
class Canvas:
    def __init__(self):
        self.px = [PAPER] * (W * H)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(W, x + w)
        y1 = min(H, y + h)
        for yy in range(y0, y1):
            base = yy * W
            for xx in range(x0, x1):
                self.px[base + xx] = color

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if 0 <= x0 < W and 0 <= y0 < H:
                self.px[y0 * W + x0] = color
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        x = r
        y = 0
        err = 0
        while x >= y:
            if fill:
                self.rect(cx - x, cy + y, 2 * x + 1, 1, color)
                self.rect(cx - x, cy - y, 2 * x + 1, 1, color)
                self.rect(cx - y, cy + x, 2 * y + 1, 1, color)
                self.rect(cx - y, cy - x, 2 * y + 1, 1, color)
            else:
                for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                               (cx - y, cy + x), (cx - x, cy + y),
                               (cx - x, cy - y), (cx - y, cy - x),
                               (cx + y, cy - x), (cx + x, cy - y)):
                    if 0 <= px < W and 0 <= py < H:
                        self.px[py * W + px] = color
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x

    def tri(self, x0, y0, x1, y1, x2, y2, color):
        # filled triangle via scanline interpolation
        pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(max(0, ay), min(H, cy + 1)):
            if y < by:
                xa = edge(ax, ay, bx, by, y)
                xb = edge(ax, ay, cx, cy, y)
            else:
                xa = edge(bx, by, cx, cy, y)
                xb = edge(ax, ay, cx, cy, y)
            if xa > xb:
                xa, xb = xb, xa
            self.rect(int(xa), y, int(xb) - int(xa) + 1, 1, color)


# ------------------------------------------------------- 5x7 bitmap font ---
# Each glyph: 7 rows, low 5 bits, top row first. Written from scratch.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color):
    for ch in text:
        glyph = FONT.get(ch, FONT.get(ch.upper(), FONT["?"]))
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    cv.rect(x + col * scale, y + row * scale,
                            scale, scale, color)
        x += 6 * scale
    return x


def wrap_text(text, scale, max_w):
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, text, scale, color, max_w, leading):
    lines = wrap_text(text, scale, max_w)
    for line in lines:
        draw_text(cv, x, y, line, scale, color)
        y += leading
    return y


# ------------------------------------------------------------------- icons --
# Simple geometric pictograms, one per story, drawn in a 116x116 box.
def icon_globe(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.circle(x + 58, y + 58, 44, fg)
    cv.circle(x + 58, y + 58, 36, fg)
    cv.hline(x + 18, y + 58, 80, fg)
    cv.line(x + 58, y + 16, x + 58, y + 100, fg)
    cv.line(x + 24, y + 34, x + 92, y + 34, fg)
    cv.line(x + 24, y + 82, x + 92, y + 82, fg)
    cv.line(x + 30, y + 96, x + 58, y + 62, RED)
    cv.line(x + 58, y + 62, x + 86, y + 96, RED)


def icon_badge(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.circle(x + 58, y + 52, 34, fg, fill=True)
    cv.circle(x + 58, y + 52, 26, bg)
    cv.circle(x + 58, y + 52, 14, fg, fill=True)
    cv.rect(x + 50, y + 84, 16, 22, fg)
    cv.rect(x + 30, y + 84, 12, 16, RED)
    cv.rect(x + 74, y + 84, 12, 16, RED)


def icon_ship_fire(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.tri(x + 34, y + 40, x + 46, y + 8, x + 58, y + 40, (255, 120, 0))
    cv.tri(x + 56, y + 42, x + 68, y + 14, x + 80, y + 42, RED)
    cv.tri(x + 44, y + 44, x + 54, y + 22, x + 64, y + 44, (255, 200, 40))
    cv.rect(x + 20, y + 66, 76, 26, fg)
    cv.tri(x + 20, y + 66, x + 96, y + 66, x + 88, y + 92, fg)
    cv.rect(x + 52, y + 44, 6, 22, fg)
    cv.hline(x + 14, y + 98, 88, fg)
    cv.hline(x + 22, y + 104, 72, fg)


def icon_factory(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.tri(x + 30, y + 42, x + 42, y + 12, x + 54, y + 42, (255, 120, 0))
    cv.tri(x + 52, y + 44, x + 64, y + 16, x + 76, y + 44, RED)
    cv.rect(x + 18, y + 60, 80, 36, fg)
    cv.rect(x + 18, y + 48, 22, 12, fg)
    cv.rect(x + 44, y + 44, 22, 16, fg)
    cv.rect(x + 70, y + 40, 22, 20, fg)
    cv.rect(x + 26, y + 72, 12, 12, bg)
    cv.rect(x + 46, y + 72, 12, 12, bg)
    cv.rect(x + 66, y + 72, 12, 12, bg)
    cv.hline(x + 14, y + 102, 88, fg)


def icon_tanker(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.rect(x + 16, y + 68, 84, 22, fg)
    cv.tri(x + 16, y + 68, x + 100, y + 68, x + 90, y + 90, fg)
    cv.rect(x + 30, y + 52, 26, 16, fg)
    cv.rect(x + 62, y + 58, 16, 10, fg)
    cv.line(x + 78, y + 20, x + 96, y + 52, RED)
    cv.tri(x + 72, y + 14, x + 84, y + 10, x + 82, y + 26, RED)
    cv.line(x + 70, y + 30, x + 58, y + 46, RED)
    cv.hline(x + 12, y + 98, 92, fg)
    cv.hline(x + 20, y + 104, 76, fg)


def icon_ballot(cv, x, y, fg, bg):
    cv.rect(x, y, 116, 116, bg)
    cv.rect(x + 26, y + 48, 64, 48, fg)
    cv.rect(x + 46, y + 40, 24, 8, fg)
    cv.rect(x + 34, y + 60, 48, 4, bg)
    cv.line(x + 34, y + 82, x + 46, y + 92, RED)
    cv.line(x + 46, y + 92, x + 78, y + 62, RED)
    cv.line(x + 34, y + 82, x + 46, y + 92, RED)
    cv.rect(x + 52, y + 12, 12, 26, RED)
    cv.tri(x + 46, y + 12, x + 70, y + 12, x + 58, y + 2, RED)


# ------------------------------------------------------------------ stories --
# Six stories that happened or were first reported on Monday 23 Nov 2026.
STORIES = [
    {
        "tag": "CLIMATE - COP31",
        "color": (46, 125, 87),
        "icon": icon_globe,
        "headline": "CLIMATE TALKS COLLAPSE",
        "body": "COP31 ends with no deal as the final draft drops any mention of fossil fuels.",
    },
    {
        "tag": "MEXICO - CARTELS",
        "color": (146, 64, 14),
        "icon": icon_badge,
        "headline": "MEXICO CAPTURES EL CHAPO ISIDRO",
        "body": "Troops seize the FBI's most-wanted cartel boss in Sinaloa after firefights kill 11.",
    },
    {
        "tag": "WAR IN UKRAINE",
        "color": (120, 40, 40),
        "icon": icon_ship_fire,
        "headline": "RUSSIAN SHIPS HIT AT SEA",
        "body": "A cargo ship burns off Finland and a warship is reported sunk in Libya after drone strikes.",
    },
    {
        "tag": "INDONESIA - DISASTER",
        "color": (178, 90, 20),
        "icon": icon_factory,
        "headline": "FACTORY FIRE: DOZENS MISSING",
        "body": "A deadly blaze at a candy factory leaves workers missing as rescuers search the ruins.",
    },
    {
        "tag": "IRAN-US WAR - THE GULF",
        "color": (90, 40, 110),
        "icon": icon_tanker,
        "headline": "WAR SPREADS ACROSS THE GULF",
        "body": "Tankers are hit in the Strait of Hormuz as missiles strike a US base in Bahrain.",
    },
    {
        "tag": "UNITED STATES - POLITICS",
        "color": (30, 80, 160),
        "icon": icon_ballot,
        "headline": "DEMOCRATS WIN RECORD HOUSE MAJORITY",
        "body": "Democrats clinch at least 258 House seats, their largest majority since 1992.",
    },
]


# ------------------------------------------------------------------ layout --
def draw_card(cv, x, y, w, h, story):
    cv.rect(x, y, w, h, CARD)
    cv.rect(x, y, w, 3, INK)
    cv.rect(x, y, w, h, INK)  # placeholder border drawn over below
    cv.rect(x + 1, y + 1, w - 2, h - 2, CARD)
    cv.rect(x, y, w, 8, story["color"])
    # icon box, left
    ix, iy = x + 18, y + 26
    story["icon"](cv, ix, iy, INK, (238, 236, 228))
    cv.rect(ix, iy, 116, 2, story["color"])
    # text column, right of icon
    tx = ix + 116 + 16
    tw = x + w - 18 - tx
    ty = y + 28
    draw_text(cv, tx, ty, story["tag"], 2, story["color"])
    ty += 26
    ty = draw_para(cv, tx, ty, story["headline"], 3, INK, tw, 26)
    ty += 6
    draw_para(cv, tx, ty, story["body"], 2, MUTED, tw, 20)


def build():
    cv = Canvas()
    # outer frame
    cv.rect(0, 0, W, 10, NAVY)
    cv.rect(0, H - 10, W, 10, NAVY)
    cv.rect(0, 0, 10, H, NAVY)
    cv.rect(W - 10, 0, 10, H, NAVY)
    # masthead
    cv.rect(10, 10, W - 20, 138, NAVY)
    title = "THE WORLD TODAY"
    tw = text_width(title, 6)
    draw_text(cv, (W - tw) // 2, 30, title, 6, WHITE)
    cv.rect((W - 420) // 2, 96, 420, 3, GOLD)
    date = "MONDAY 23 NOVEMBER 2026"
    dw = text_width(date, 3)
    draw_text(cv, (W - dw) // 2, 110, date, 3, GOLD)
    # kicker strip
    kick = "SIX STORIES THAT SHAPED THE DAY"
    kw = text_width(kick, 2)
    draw_text(cv, (W - kw) // 2, 162, kick, 2, RED)
    cv.hline(10, 186, W - 20, RULE)
    # grid: 2 columns x 3 rows
    gx, gy = 22, 200
    cw, ch = 478, 246
    gapx, gapy = 24, 14
    for i, story in enumerate(STORIES):
        cx = gx + (i % 2) * (cw + gapx)
        cy = gy + (i // 2) * (ch + gapy)
        draw_card(cv, cx, cy, cw, ch, story)
    # footer
    foot = "ALL SIX STORIES HAPPENED OR WERE FIRST REPORTED ON 23 NOVEMBER 2026"
    fw = text_width(foot, 2)
    draw_text(cv, (W - fw) // 2, 978, foot, 2, MUTED)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(os.path.join(out_dir, "entry.png"), cv.px)


if __name__ == "__main__":
    main()

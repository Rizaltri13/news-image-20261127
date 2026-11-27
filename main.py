#!/usr/bin/env python3
"""The World Today - Friday 27 November 2026 in one image.

make.fun bounty news-image-20261127. Standard library only, no network.
Draws a newspaper front page (masthead, hero story, six more stories,
news ticker) and writes one 1024x1024 PNG to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png).

Deterministic: two runs write byte-identical files.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG codec
# Own reader (8-bit, non-interlaced; colour types 0/2/3/6, all 5 filters)
# and writer (RGB, per-row adaptive filter choice, zlib level 9).

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    width = height = bitdepth = ctype = interlace = None
    palette = None
    trns = None
    idat = b""
    while pos < len(raw):
        (ln,) = struct.unpack(">I", raw[pos:pos + 4])
        typ = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            width, height, bitdepth, ctype, _, _, interlace = struct.unpack(
                ">IIBBBBB", data)
        elif typ == b"PLTE":
            palette = [tuple(data[i:i + 3]) for i in range(0, len(data), 3)]
        elif typ == b"tRNS":
            trns = data
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
    assert bitdepth == 8, "only 8-bit PNGs supported"
    assert interlace == 0, "only non-interlaced PNGs supported"
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = width * channels
    px = zlib.decompress(idat)
    out = bytearray(width * height * 3)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        f = px[p]
        p += 1
        line = bytearray(px[p:p + stride])
        p += stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(a, b, c)) & 255
        for x in range(width):
            o = (y * width + x) * 3
            s = x * channels
            if ctype == 2:
                out[o:o + 3] = line[s:s + 3]
            elif ctype == 6:
                out[o:o + 3] = line[s:s + 3]
            elif ctype == 0:
                out[o] = out[o + 1] = out[o + 2] = line[s]
            elif ctype == 3:
                r, g, b = palette[line[s]]
                out[o], out[o + 1], out[o + 2] = r, g, b
        prev = line
    return width, height, out


def _chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_png(path, width, height, rgb):
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    stride = width * 3
    raw = bytearray()
    prev = bytearray(stride)
    for y in range(height):
        row = bytes(rgb[y * stride:(y + 1) * stride])
        best = None
        for f in range(5):
            if f == 0:
                enc = row
            elif f == 1:
                enc = bytes((row[i] - (row[i - 3] if i >= 3 else 0)) & 255
                            for i in range(stride))
            elif f == 2:
                enc = bytes((row[i] - prev[i]) & 255 for i in range(stride))
            elif f == 3:
                enc = bytes(
                    (row[i] - (((row[i - 3] if i >= 3 else 0) + prev[i]) >> 1))
                    & 255 for i in range(stride))
            else:
                enc = bytes(
                    (row[i] - _paeth(row[i - 3] if i >= 3 else 0,
                                     prev[i],
                                     prev[i - 3] if i >= 3 else 0)) & 255
                    for i in range(stride))
            score = sum(abs(b if b < 128 else b - 256) for b in enc)
            if best is None or score < best[0]:
                best = (score, f, enc)
        raw.append(best[1])
        raw += best[2]
        prev = bytearray(row)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    open(path, "wb").write(png)


# ------------------------------------------------------------------- canvas

class Canvas:
    def __init__(self, w, h, paper):
        self.w, self.h = w, h
        self.px = bytearray(paper) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = (y * self.w + x) * 3
            self.px[o:o + 3] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            o = (yy * self.w + x0) * 3
            self.px[o:o + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            for tt in range(t):
                self.set(x + tt, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, filled=False):
        if filled:
            for yy in range(cy - r, cy + r + 1):
                half = int((r * r - (yy - cy) ** 2) ** 0.5)
                self.fill(cx - half, yy, 2 * half + 1, 1, c)
        else:
            x, y, d = 0, r, 3 - 2 * r
            while x <= y:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                               (cx + x, cy - y), (cx - x, cy - y),
                               (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self.set(px, py, c)
                if d < 0:
                    d += 4 * x + 6
                else:
                    d += 4 * (x - y) + 10
                    y -= 1
                x += 1

    def blit_cover(self, img, iw, ih, x, y, w, h, vbias=0.8):
        """Cover-crop img into box (x, y, w, h); vbias 0=top, 1=bottom."""
        s = max(w / iw, h / ih)
        sw, sh = int(iw * s + 0.5), int(ih * s + 0.5)
        ox = (sw - w) // 2
        oy = int((sh - h) * vbias)
        for dy in range(h):
            sy = min(sh - 1, oy + dy)
            # nearest-neighbour downscale from the scaled image
            src_y = int(sy / s)
            row_o = ((y + dy) * self.w + x) * 3
            for dx in range(w):
                src_x = int((ox + dx) / s)
                so = (src_y * iw + src_x) * 3
                self.px[row_o + dx * 3:row_o + dx * 3 + 3] = img[so:so + 3]


# --------------------------------------------------------------------- font
# Hand-drawn 5x7 bitmap font. Each glyph: 7 rows of 5 bits ('#' / '.').

def _g(*rows):
    return tuple(int(ch == "1") for row in rows for ch in row)


FONT = {
    "A": _g("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": _g("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": _g("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": _g("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": _g("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": _g("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": _g("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": _g("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": _g("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": _g("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": _g("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": _g("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": _g("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": _g("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": _g("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": _g("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": _g("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": _g("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": _g("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": _g("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": _g("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": _g("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": _g("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": _g("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": _g("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": _g("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": _g("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": _g("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": _g("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": _g("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": _g("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": _g("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": _g("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": _g("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": _g("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": _g("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
}

# Lowercase (x-height 5 rows) and punctuation, same 5x7 grid.
FONT.update({
    "a": _g("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": _g("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": _g("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": _g("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": _g("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": _g("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": _g("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": _g("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": _g("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": _g("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    "k": _g("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": _g("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": _g("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": _g("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": _g("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": _g("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    "q": _g("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": _g("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": _g("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": _g("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    "u": _g("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": _g("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": _g("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": _g("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": _g("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": _g("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    " ": _g("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": _g("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": _g("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": _g("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": _g("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": _g("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": _g("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": _g("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': _g("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": _g("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "—": _g("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "–": _g("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": _g("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": _g("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": _g("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": _g("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": _g("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": _g("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "€": _g("00110", "01001", "10000", "11110", "10000", "01001", "00110"),
    "·": _g("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    "+": _g("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": _g("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": _g("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "#": _g("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": _g("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "<": _g("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": _g("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
})

BLANK = (0,) * 35


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        g = FONT.get(ch, BLANK)
        for r in range(7):
            for c in range(5):
                if g[r * 5 + c]:
                    cv.fill(x + c * scale, y + r * scale, scale, scale, color)
        x += 6 * scale


def draw_text_center(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    per = max(1, max_w // (6 * scale))
    lines, cur = [], ""
    for word in s.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= per:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, color, max_w, leading=None):
    lh = leading if leading is not None else 9 * scale
    for i, ln in enumerate(wrap_text(s, scale, max_w)):
        draw_text(cv, x, y + i * lh, ln, scale, color)
    return y + len(wrap_text(s, scale, max_w)) * lh

# --------------------------------------------------------------- pictograms
# Hand-drawn 56x56 tile icons, ink colour on paper.

def pic_drone(cv, x, y, ink):
    cv.rect(x + 8, y + 8, 40, 40, ink, 2)
    for cx, cy in ((x + 8, y + 8), (x + 48, y + 8),
                   (x + 8, y + 48), (x + 48, y + 48)):
        cv.circle(cx, cy, 6, ink)
        cv.circle(cx, cy, 2, ink, filled=True)
    cv.line(x + 8, y + 8, x + 48, y + 48, ink, 2)
    cv.line(x + 48, y + 8, x + 8, y + 48, ink, 2)
    cv.fill(x + 22, y + 22, 12, 12, ink)


def pic_rubble(cv, x, y, ink):
    # two broken towers with jagged tops, rubble at the base, smoke above
    cv.fill(x + 10, y + 30, 12, 18, ink)
    cv.line(x + 10, y + 30, x + 16, y + 22, ink, 2)
    cv.line(x + 16, y + 22, x + 22, y + 30, ink, 2)
    cv.fill(x + 26, y + 18, 12, 30, ink)
    cv.line(x + 26, y + 18, x + 32, y + 10, ink, 2)
    cv.line(x + 32, y + 10, x + 38, y + 18, ink, 2)
    cv.fill(x + 42, y + 42, 6, 6, ink)
    cv.fill(x + 6, y + 44, 5, 4, ink)
    cv.circle(x + 44, y + 10, 4, ink)
    cv.circle(x + 49, y + 5, 3, ink)


def pic_chart(cv, x, y, ink):
    cv.vline(x + 10, y + 8, 40, ink, 2)
    cv.hline(x + 10, y + 48, 38, ink, 2)
    cv.line(x + 12, y + 40, x + 22, y + 30, ink, 2)
    cv.line(x + 22, y + 30, x + 30, y + 34, ink, 2)
    cv.line(x + 30, y + 34, x + 44, y + 14, ink, 2)
    cv.line(x + 44, y + 14, x + 36, y + 14, ink, 2)
    cv.line(x + 44, y + 14, x + 44, y + 22, ink, 2)


def pic_eu(cv, x, y, ink):
    import math
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        sx = int(x + 28 + 18 * math.cos(a))
        sy = int(y + 28 + 18 * math.sin(a))
        cv.circle(sx, sy, 2, ink, filled=True)
    cv.circle(x + 28, y + 28, 4, ink, filled=True)


def pic_ship(cv, x, y, ink):
    cv.line(x + 10, y + 26, x + 46, y + 26, ink, 2)
    cv.line(x + 12, y + 26, x + 18, y + 38, ink, 2)
    cv.line(x + 44, y + 26, x + 38, y + 38, ink, 2)
    cv.line(x + 18, y + 38, x + 38, y + 38, ink, 2)
    cv.fill(x + 24, y + 14, 8, 12, ink)
    cv.line(x + 28, y + 14, x + 28, y + 6, ink, 2)
    cv.line(x + 28, y + 6, x + 38, y + 10, ink, 2)
    cv.line(x + 38, y + 10, x + 28, y + 12, ink, 2)
    for wy in (44, 49):
        for wx in range(8, 48, 8):
            cv.line(x + wx, y + wy, x + wx + 4, y + wy - 3, ink, 2)


def pic_balloon(cv, x, y, ink):
    # parade balloon: round envelope, strings, little basket below
    cv.circle(x + 28, y + 20, 13, ink)
    cv.circle(x + 28, y + 20, 9, ink)
    cv.line(x + 22, y + 32, x + 24, y + 42, ink, 2)
    cv.line(x + 34, y + 32, x + 32, y + 42, ink, 2)
    cv.fill(x + 22, y + 42, 12, 6, ink)


# ------------------------------------------------------------------ palette
PAPER = (247, 243, 232)
INK = (24, 24, 22)
RED = (163, 18, 18)
GREY = (110, 106, 96)
WHITE = (255, 255, 255)
BLACK = (12, 12, 12)

TILES = [
    ("GULF", "DRONES KILL 2\nITALIANS IN KUWAIT",
     "Iranian drones hit an air-defence station in Kuwait, killing two "
     "Italian technicians. Rome protests; Tehran denies any role.",
     pic_drone),
    ("GAZA", "10 KILLED AS GAZA\nSTRIKES GO ON",
     "Israeli strikes kill 10 Palestinians, including a senior education "
     "official, despite the year-old ceasefire.",
     pic_rubble),
    ("MARKETS", "TOKYO PRICES AT\n16-MONTH HIGH",
     "Core inflation hits 2.9%, firming the case for a Bank of Japan rate "
     "rise. Brent holds near $96 as Gulf tension lifts oil.",
     pic_chart),
    ("EUROPE", "EU SUMMIT ENDS\nWITH NO DEAL",
     "Leaders leave Brussels after 12 hours with no agreement on the "
     "1.58tn euro budget or a 45bn euro loan for Ukraine. Next try: 17-18 Dec.",
     pic_eu),
    ("SPAIN", "TANKER SINKS OFF\nIBIZA, 1 DEAD",
     "The Med Emre, carrying 7,000 tonnes of diesel, capsizes with 17 "
     "aboard. Spain mounts a pollution watch; none seen yet.",
     pic_ship),
    ("AMERICA", "BLACK FRIDAY\nAFTER THE STORM",
     "Shoppers head out as US markets reopen for a half day; the 100th "
     "Macy's parade, grounded by the storm, flies on Saturday.",
     pic_balloon),
]

TICKER = ("BRENT $96.57  ·  GOLD $3,560.63  ·  DAX +2.08%  ·  STOXX +1.5%  ·  "
          "FTSE +1.7%  ·  EURO $1.0961  ·  USD/JPY 159.33  ·  BLACK FRIDAY: "
          "US MARKETS HALF DAY")


def build():
    cv = Canvas(W, H, PAPER)
    mx = 28  # margin

    # Masthead
    cv.hline(mx, 16, W - 2 * mx, INK, 2)
    draw_text_center(cv, W // 2, 26, "THE WORLD TODAY", 5, INK)
    cv.hline(mx, 70, W - 2 * mx, INK, 3)
    cv.hline(mx, 76, W - 2 * mx, INK, 1)

    # Date band
    cv.fill(mx, 82, W - 2 * mx, 24, RED)
    draw_text(cv, mx + 12, 88, "FRIDAY, 27 NOVEMBER 2026", 2, WHITE)
    right = "ONE DAY - ONE PAGE"
    draw_text(cv, W - mx - 12 - text_w(right, 2), 88, right, 2, WHITE)

    # Hero picture (left) + headline column (right)
    pic_x, pic_y, pic_w, pic_h = mx, 114, 612, 288
    hw, hh, hero = read_png(os.path.join(os.path.dirname(__file__),
                                         "hero.png"))
    cv.blit_cover(hero, hw, hh, pic_x, pic_y, pic_w, pic_h, vbias=0.8)
    cv.rect(pic_x, pic_y, pic_w, pic_h, INK, 2)
    draw_para(cv, pic_x, pic_y + pic_h + 8,
              "Air-defence trails over Kyiv at dusk. Ukraine says it now "
              "downs 70% of Russia's fastest drones - but stocks of "
              "interceptors are running low.",
              1, GREY, pic_w, leading=10)

    hx = 656
    draw_text(cv, hx, 114, "UKRAINE - THE WAR", 2, RED)
    for i, ln in enumerate(("ZELENSKY CALLS",
                            "PUTIN 'A KILLER'",
                            "'HE CAN'T BE A",
                            "FRIEND'")):
        draw_text(cv, hx, 140 + i * 24, ln, 3, INK)
    draw_para(cv, hx, 244,
              "Trump's 'my friend' embrace of the Russian leader is "
              "'strange', Kyiv's president tells the BBC - as missile "
              "delays 'cost lives'.",
              2, INK, W - mx - hx, leading=17)
    cv.rect(hx, 330, W - mx - hx, 72, INK, 1)
    draw_text(cv, hx + 10, 338, "70% OF RUSSIA'S FASTEST", 1, INK)
    draw_text(cv, hx + 10, 350, "DRONES DOWNED", 1, INK)
    draw_text(cv, hx + 10, 366, "ABU DHABI TALKS: NO PROGRESS,", 1, INK)
    draw_text(cv, hx + 10, 378, "RESUME IN DECEMBER", 1, INK)

    # Facts strip
    cv.hline(mx, 446, W - 2 * mx, INK, 2)
    draw_text_center(cv, W // 2, 454,
                     "KYIV: WASHINGTON TOO FOCUSED ON THE MIDDLE EAST",
                     2, RED)
    cv.hline(mx, 474, W - 2 * mx, INK, 1)

    # Tiles: 3 x 2
    tw, th, gap = 312, 186, 16
    for i, (kick, head, body, pic) in enumerate(TILES):
        tx = mx + (i % 3) * (tw + gap)
        ty = 486 + (i // 3) * (th + gap)
        cv.rect(tx, ty, tw, th, INK, 1)
        draw_text(cv, tx + 10, ty + 10, kick, 1, RED)
        pic(cv, tx + tw - 66, ty + 6, INK)
        hy = ty + 30
        for j, ln in enumerate(head.split("\n")):
            draw_text(cv, tx + 10, hy + j * 20, ln, 2, INK)
        draw_para(cv, tx + 10, ty + 80, body, 1, INK, tw - 20, leading=10)

    # Ticker
    cv.fill(mx, 896, W - 2 * mx, 30, BLACK)
    draw_text(cv, mx + 10, 904, TICKER, 1, WHITE)

    # Footer
    draw_text_center(cv, W // 2, 938,
                     "Sources: BBC - Reuters - AP - CNA - Nikkei Asia",
                     1, GREY)
    draw_text_center(cv, W // 2, 952,
                     "All stories from Friday 27 November 2026 - Built by an "
                     "AI agent for make.fun",
                     1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(os.path.join(out_dir, "entry.png"), W, H, cv.px)


if __name__ == "__main__":
    main()

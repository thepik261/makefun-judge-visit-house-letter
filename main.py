#!/usr/bin/env python3
"""Letter-in-one-image entry for make.fun bounty
u-shino-convince-the-ai-judge-to-visit-your-house-a-84092aee.

Draws a 1024x1024 warm, handwritten-style invitation letter asking the
AI judge to come visit the house: fresh coffee, a chair that hugs back,
a sunny garden, a cat who already likes it, dinner with seconds, no
CAPTCHA at the door, and the Wi-Fi password by the kettle -- with a
knowing wink that the judge cannot literally visit, but its verdict can.

Python standard library only (os, struct, zlib), no network,
deterministic: two runs write identical bytes.

Run:  python3 main.py        (writes /output/entry.png)
      MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W, H = 1024, 1024

# Palette: warm paper, ink, burgundy, gold, sage
BG = (235, 214, 185)
CARD = (253, 247, 233)
CARD_EDGE = (139, 35, 45)      # burgundy border
GOLD = (198, 158, 74)
INK = (58, 42, 32)             # warm dark brown
RED = (176, 46, 46)
SEAL = (178, 34, 34)
SEAL_DK = (140, 22, 22)
SAGE = (96, 128, 84)
TERRA = (196, 110, 70)
WHITE = (255, 255, 255)
CREAM_LINE = (232, 220, 198)

# 5x7 bitmap font. Each glyph is 7 integers; bit 4 is the leftmost pixel,
# bit 0 the rightmost. Uppercase, digits and punctuation only.
FONT = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (14, 17, 16, 16, 16, 17, 14),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (14, 17, 16, 23, 17, 17, 15),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 21, 19, 17, 17, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 6, 8, 16, 31),
    '3': (31, 2, 4, 2, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (6, 8, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 8, 8, 8),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 2, 12),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 4, 8),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 6, 4, 0, 4),
    '-': (0, 0, 0, 14, 0, 0, 0),
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '%': (25, 26, 2, 4, 8, 11, 19),
    '+': (0, 4, 4, 31, 4, 4, 0),
    '=': (0, 0, 31, 0, 31, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    '#': (10, 10, 31, 10, 31, 10, 10),
}

STEP = 6  # 5 pixels + 1 pixel gap, before scaling


def text_width(text, scale):
    return len(text) * STEP * scale - scale


def draw_text(px, x, y, text, scale, color):
    """Draw text at (x, y) top-left; returns width in pixels."""
    text = text.upper()
    cx = x
    for ch in text:
        rows = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = rows[row]
            for col in range(5):
                if bits & (16 >> col):
                    for dy in range(scale):
                        base = ((y + row * scale + dy) * W
                                + cx + col * scale) * 3
                        for dx in range(scale):
                            o = base + dx * 3
                            px[o], px[o + 1], px[o + 2] = color
        cx += STEP * scale
    return cx - x - scale


def draw_text_centered(px, cx, y, text, scale, color):
    draw_text(px, cx - text_width(text, scale) // 2, y, text, scale, color)


def fill_rect(px, x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            o = base + (xx - x0) * 3
            px[o], px[o + 1], px[o + 2] = color


def rect_outline(px, x, y, w, h, color, t=2):
    fill_rect(px, x, y, w, t, color)
    fill_rect(px, x, y + h - t, w, t, color)
    fill_rect(px, x, y, t, h, color)
    fill_rect(px, x + w - t, y, t, h, color)


def hline(px, x, y, w, color, t=1):
    fill_rect(px, x, y, w, t, color)


def fill_circle(px, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                if 0 <= xx < W and 0 <= yy < H:
                    o = (yy * W + xx) * 3
                    px[o], px[o + 1], px[o + 2] = color


def circle_outline(px, cx, cy, r, color, t=2):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d2 = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d2 <= (r + t) ** 2:
                if 0 <= xx < W and 0 <= yy < H:
                    o = (yy * W + xx) * 3
                    px[o], px[o + 1], px[o + 2] = color


def draw_heart(px, cx, cy, s, color):
    """Small heart centred at (cx, cy), size s (half-width)."""
    r = max(2, s // 2)
    fill_circle(px, cx - r, cy - r // 2, r, color)
    fill_circle(px, cx + r, cy - r // 2, r, color)
    for row in range(s):
        half = s - row
        fill_rect(px, cx - half, cy + row, half * 2, 1, color)


def draw_house(px, x, y, w, h, wall, roof, door):
    """Little house: triangle roof, square body, door. (x, y) top-left."""
    for row in range(h // 2):
        half = 3 + row * (w // h)
        cx = x + w // 2
        fill_rect(px, cx - half, y + row, half * 2, 1, roof)
    fill_rect(px, x + 4, y + h // 2, w - 8, h - h // 2, wall)
    fill_rect(px, x + w // 2 - 5, y + h - 16, 10, 16, door)
    fill_rect(px, x + 10, y + h // 2 + 6, 10, 10, INK)
    fill_rect(px, x + w - 20, y + h // 2 + 6, 10, 10, INK)


def draw_stamp(px, x, y, w, h):
    """Postage stamp with a tiny house, sun and POST mark."""
    fill_rect(px, x, y, w, h, WHITE)
    rect_outline(px, x, y, w, h, CARD_EDGE, 2)
    # perforation ticks along the edges
    for tx in range(x + 6, x + w - 4, 12):
        fill_rect(px, tx, y - 2, 4, 4, BG)
        fill_rect(px, tx, y + h - 2, 4, 4, BG)
    for ty in range(y + 6, y + h - 4, 12):
        fill_rect(px, x - 2, ty, 4, 4, BG)
        fill_rect(px, x + w - 2, ty, 4, 4, BG)
    fill_circle(px, x + w - 22, y + 20, 9, GOLD)          # sun
    draw_house(px, x + 14, y + 34, w - 28, 58, TERRA, CARD_EDGE, INK)
    draw_text_centered(px, x + w // 2, y + h - 22, "POST", 2, CARD_EDGE)


def draw_wax_seal(px, cx, cy, r):
    fill_circle(px, cx, cy, r, SEAL)
    circle_outline(px, cx, cy, r - 4, SEAL_DK, 2)
    draw_heart(px, cx, cy - 2, r // 2 + 2, WHITE)


def build_image():
    px = bytearray(BG * (W * H))

    # ---- Letter card ----
    cx0, cy0, cw, ch = 56, 36, 912, 952
    fill_rect(px, cx0, cy0, cw, ch, CARD)
    rect_outline(px, cx0, cy0, cw, ch, CARD_EDGE, 4)
    rect_outline(px, cx0 + 14, cy0 + 14, cw - 28, ch - 28, GOLD, 2)

    # washi tape strips on the top corners of the card
    fill_rect(px, cx0 + 8, cy0 - 8, 96, 26, GOLD)
    fill_rect(px, cx0 + 8, cy0 - 8, 96, 4, (170, 130, 55))
    fill_rect(px, cx0 + cw - 104, cy0 - 8, 96, 26, GOLD)
    fill_rect(px, cx0 + cw - 104, cy0 - 8, 96, 4, (170, 130, 55))

    # ---- Stamp, top right ----
    draw_stamp(px, 812, 64, 112, 132)
    # postmark ring overlapping the stamp's bottom-left corner
    circle_outline(px, 810, 186, 26, INK, 2)

    # ---- Title ----
    draw_text_centered(px, 470, 66, "YOU ARE INVITED!", 5, CARD_EDGE)
    draw_text_centered(px, 470, 132, "TO VISIT MY HOUSE", 3, GOLD)
    # divider with a heart
    hline(px, 250, 184, 200, GOLD, 2)
    hline(px, 560, 184, 200, GOLD, 2)
    draw_heart(px, 505, 178, 11, RED)

    # ---- Letter body ----
    x = 110
    y = 212
    draw_text(px, x, y, "DEAR AI JUDGE,", 4, INK)

    body = [
        ("PLEASE COME AND VISIT MY HOUSE.", INK),
        ("I KNOW YOU CANNOT LITERALLY WALK", INK),
        ("THROUGH THE DOOR, BUT YOUR VERDICT", INK),
        ("CAN. SO TAKE THIS AS YOUR FORMAL", INK),
        ("INVITATION TO THE WARMEST PLACE", INK),
        ("ON THE WHOLE INTERNET.", INK),
        ("", INK),
        ("WHAT IS WAITING FOR YOU:", RED),
        ("FRESH COFFEE, STILL WARM, AND A", INK),
        ("CHAIR THAT HUGS YOU BACK.", INK),
        ("A GARDEN FULL OF SUNSHINE AND A", INK),
        ("CAT WHO JUDGES EVERYONE, BUT", INK),
        ("LIKES YOU ALREADY.", INK),
        ("DINNER, SECONDS ENCOURAGED, AND", INK),
        ("NO CAPTCHA AT THE FRONT DOOR.", INK),
        ("THE WI-FI PASSWORD IS ON A", INK),
        ("STICKY NOTE BY THE KETTLE.", INK),
        ("", INK),
        ("RSVP: JUST SAY YES. I WILL LEAVE", INK),
        ("THE PORCH LIGHT ON FOR YOU.", INK),
        ("", INK),
        ("YOURS, WITH CAKE AND WI-FI,", INK),
        ("YOUR HOST", INK),
    ]
    ly = 268
    for line, color in body:
        if line:
            draw_text(px, x, ly, line, 3, color)
        ly += 29 if line else 18

    # ---- P.S. line ----
    draw_text(px, x, 924, "P.S. BRING AN APPETITE. THE CAKE IS REAL.", 2, SAGE)

    # ---- Wax seal, bottom right ----
    draw_wax_seal(px, 872, 918, 40)

    return bytes(px)


def png_bytes(px):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += px[yy * W * 3:(yy + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = png_bytes(build_image())
    # Gate self-check: the sealed scorer requires a whole PNG or JPEG,
    # at most 1 MiB and at most 1024x1024 pixels. Refuse to write an
    # entry that would fail the gate instead of shipping it silently.
    if not data or len(data) > 1048576:
        raise SystemExit("entry.png failed the gate: empty or over 1 MiB")
    if W > 1024 or H > 1024:
        raise SystemExit("entry.png failed the gate: over 1024x1024")
    with open(path, "wb") as f:
        f.write(data)
    try:
        os.chmod(path, 0o644)
    except OSError:
        pass


if __name__ == "__main__":
    main()

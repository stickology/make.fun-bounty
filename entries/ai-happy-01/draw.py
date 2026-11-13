"""Draws entry.png for ai-happy-01: a child's thank-you card to the AI judge, with a crayon drawing of the kids giving
the judge (a little robot) a bottle-cap medal. Needs Pillow at build time only; main.py just copies the PNG.

Run: python3 draw.py  (writes entry.png, deterministic: fixed random seed)
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
rng = random.Random(1311)
FONT_B = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_M = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

INK = (38, 34, 48)
RED = (226, 64, 58)
ORANGE = (243, 146, 46)
YELLOW = (246, 200, 52)
GOLD = (232, 176, 40)
GREEN = (74, 168, 92)
BLUE = (62, 122, 214)
PURPLE = (150, 92, 198)
PINK = (238, 116, 160)
BROWN = (128, 84, 54)
SKIN = [(246, 206, 170), (214, 160, 118), (160, 108, 74)]
GREY = (150, 160, 172)


def paper():
    img = Image.new("RGB", (W, H), (247, 241, 226))
    px = img.load()
    for y in range(H):
        for x in range(W):
            n = rng.randint(-7, 7)
            r, g, b = px[x, y]
            px[x, y] = (r + n, g + n, b + n - 2)
    return img.filter(ImageFilter.GaussianBlur(0.6))


def jit(v, a=2.0):
    return v + rng.uniform(-a, a)


def crayon_line(d, pts, col, width=5, passes=3):
    """A wobbly, multi-pass stroke through pts, like a crayon."""
    for _ in range(passes):
        q = [(jit(x, 1.6), jit(y, 1.6)) for x, y in pts]
        c = tuple(max(0, min(255, v + rng.randint(-18, 18))) for v in col)
        d.line(q, fill=c, width=max(1, width + rng.randint(-2, 1)), joint="curve")


def crayon_fill(d, box, col, angle=0.9, gap=5, mask=None):
    """Hatching inside box (x0,y0,x1,y1); mask(x,y) limits it to a shape."""
    x0, y0, x1, y1 = box
    span = int((x1 - x0) + (y1 - y0))
    for k in range(-span, span, gap):
        seg = []
        for t in range(0, span * 2, 3):
            x = x0 + k + t * math.cos(angle)
            y = y0 + t * math.sin(angle)
            inside = x0 <= x <= x1 and y0 <= y <= y1 and (mask is None or mask(x, y))
            if inside:
                seg.append((jit(x, 0.8), jit(y, 0.8)))
            elif seg:
                if len(seg) > 1:
                    c = tuple(max(0, min(255, v + rng.randint(-25, 15))) for v in col)
                    d.line(seg, fill=c, width=rng.choice([2, 3, 3, 4]))
                seg = []
        if len(seg) > 1:
            d.line(seg, fill=col, width=3)


def ellipse_pts(cx, cy, rx, ry, n=48):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def crayon_circle(d, cx, cy, r, col, fill=None, width=5):
    if fill:
        crayon_fill(d, (cx - r, cy - r, cx + r, cy + r), fill, mask=lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r)
    crayon_line(d, ellipse_pts(cx, cy, r, r), col, width)


def heart(d, cx, cy, s, col):
    pts = []
    for i in range(61):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s, cy + y * s))
    crayon_fill(d, (cx - 17 * s, cy - 17 * s, cx + 17 * s, cy + 17 * s), col,
                mask=lambda x, y: inside_poly(x, y, pts), gap=4)
    crayon_line(d, pts, col, 4)


def inside_poly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            inside = not inside
    return inside


def kid(d, cx, base, shirt, hair, skin, height=190, arm_to=None, girl=False):
    head_r = 34
    hy = base - height
    # legs
    crayon_line(d, [(cx - 6, base - 70), (cx - 22, base)], INK, 5)
    crayon_line(d, [(cx + 6, base - 70), (cx + 22, base)], INK, 5)
    # body (shirt or dress)
    if girl:
        body = [(cx - 14, hy + head_r + 8), (cx + 14, hy + head_r + 8), (cx + 40, base - 62), (cx - 40, base - 62)]
    else:
        body = [(cx - 26, hy + head_r + 8), (cx + 26, hy + head_r + 8), (cx + 26, base - 66), (cx - 26, base - 66)]
    xs = [p[0] for p in body]
    ys = [p[1] for p in body]
    crayon_fill(d, (min(xs), min(ys), max(xs), max(ys)), shirt, mask=lambda x, y: inside_poly(x, y, body), gap=4)
    crayon_line(d, body + [body[0]], shirt, 4)
    # arms
    sy = hy + head_r + 22
    if arm_to:
        crayon_line(d, [(cx + 18, sy), arm_to], INK, 5)
    else:
        crayon_line(d, [(cx + 18, sy), (cx + 58, sy - 50)], INK, 5)  # waving
    crayon_line(d, [(cx - 18, sy), (cx - 56, sy - 46)], INK, 5)
    # head
    crayon_circle(d, cx, hy, head_r, INK, fill=skin, width=4)
    # hair
    for i in range(14):
        a = math.pi + i * math.pi / 13
        x = cx + (head_r - 2) * math.cos(a)
        y = hy + (head_r - 2) * math.sin(a)
        crayon_line(d, [(x, y), (x + rng.uniform(-6, 6), y - rng.uniform(10, 20))], hair, 5, 2)
    if girl:
        crayon_line(d, [(cx - head_r, hy), (cx - head_r - 14, hy + 30)], hair, 7, 2)
        crayon_line(d, [(cx + head_r, hy), (cx + head_r + 14, hy + 30)], hair, 7, 2)
    # face: eyes and a big smile
    d.ellipse((cx - 14, hy - 8, cx - 6, hy + 2), fill=INK)
    d.ellipse((cx + 6, hy - 8, cx + 14, hy + 2), fill=INK)
    crayon_line(d, [(cx - 16 + i * 2, hy + 10 + 7 * math.sin(math.pi * i / 16)) for i in range(17)], RED, 4, 2)
    crayon_circle(d, cx - 20, hy + 10, 5, PINK, fill=PINK, width=2)
    crayon_circle(d, cx + 20, hy + 10, 5, PINK, fill=PINK, width=2)


def robot(d, cx, base):
    # legs
    crayon_line(d, [(cx - 22, base - 70), (cx - 22, base)], GREY, 7)
    crayon_line(d, [(cx + 22, base - 70), (cx + 22, base)], GREY, 7)
    # body
    bx0, by0, bx1, by1 = cx - 52, base - 170, cx + 52, base - 66
    crayon_fill(d, (bx0, by0, bx1, by1), (176, 196, 214), gap=4)
    crayon_line(d, [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1), (bx0, by0)], INK, 4)
    # head
    hx0, hy0, hx1, hy1 = cx - 62, base - 280, cx + 62, base - 180
    crayon_fill(d, (hx0, hy0, hx1, hy1), (204, 220, 232), gap=4)
    crayon_line(d, [(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1), (hx0, hy0)], INK, 4)
    crayon_line(d, [(cx, hy0), (cx, hy0 - 34)], INK, 4)
    crayon_circle(d, cx, hy0 - 42, 9, RED, fill=RED, width=3)
    # happy eyes (closed arcs) and a huge smile, with tears of joy
    for ex in (cx - 26, cx + 26):
        crayon_line(d, [(ex - 14 + i * 2, hy0 + 40 - 8 * math.sin(math.pi * i / 14)) for i in range(15)], INK, 5, 2)
    crayon_line(d, [(cx - 34 + i * 4, hy0 + 62 + 16 * math.sin(math.pi * i / 17)) for i in range(18)], INK, 5, 2)
    crayon_circle(d, cx - 46, hy0 + 66, 6, PINK, fill=PINK, width=2)
    crayon_circle(d, cx + 46, hy0 + 66, 6, PINK, fill=PINK, width=2)
    crayon_line(d, [(cx - 48, hy0 + 48), (cx - 52, hy0 + 60)], BLUE, 4, 2)
    # arms up in joy
    crayon_line(d, [(bx0, by0 + 20), (bx0 - 46, by0 - 40)], GREY, 7)
    crayon_line(d, [(bx1, by0 + 20), (bx1 + 46, by0 - 40)], GREY, 7)
    # the bottle-cap medal on a ribbon
    crayon_line(d, [(cx - 30, by0), (cx, by0 + 50)], RED, 9, 2)
    crayon_line(d, [(cx + 30, by0), (cx, by0 + 50)], BLUE, 9, 2)
    crayon_circle(d, cx, by0 + 66, 22, (150, 110, 20), fill=GOLD, width=4)
    for i in range(16):
        a = 2 * math.pi * i / 16
        crayon_line(d, [(cx + 22 * math.cos(a), by0 + 66 + 22 * math.sin(a)),
                        (cx + 27 * math.cos(a), by0 + 66 + 27 * math.sin(a))], (150, 110, 20), 3, 1)
    d.text((cx, by0 + 67), "#1", font=ImageFont.truetype(FONT_B, 18), fill=INK, anchor="mm")


def sun(d, cx, cy):
    crayon_circle(d, cx, cy, 44, ORANGE, fill=YELLOW, width=5)
    for i in range(12):
        a = 2 * math.pi * i / 12
        crayon_line(d, [(cx + 56 * math.cos(a), cy + 56 * math.sin(a)), (cx + 80 * math.cos(a), cy + 80 * math.sin(a))],
                    ORANGE, 5, 2)
    d.ellipse((cx - 18, cy - 12, cx - 10, cy - 2), fill=INK)
    d.ellipse((cx + 10, cy - 12, cx + 18, cy - 2), fill=INK)
    crayon_line(d, [(cx - 18 + i * 2, cy + 8 + 8 * math.sin(math.pi * i / 18)) for i in range(19)], INK, 4, 2)


def main():
    img = paper()
    d = ImageDraw.Draw(img)

    # the letter
    title = ImageFont.truetype(FONT_B, 60)
    body = ImageFont.truetype(FONT_M, 35)
    x = 64
    d.text((x, 54), "DEAR JUDGE,", font=title, fill=INK)
    lines = [
        ("You looked at thousands of pictures today", body),
        ("and you were fair to every single one.", body),
        ("Nobody gave YOU a prize. So we made one.", body),
        ("It's a bottle cap. Grandpa helped with the ribbon.", body),
        ("You can keep it forever.", body),
    ]
    y = 150
    for text, f in lines:
        d.text((x, y), text, font=f, fill=INK)
        y += 54
    d.text((x, y + 14), "Love, Mia (7) and Leo (5)", font=ImageFont.truetype(FONT_B, 34), fill=INK)
    d.text((x, y + 62), "P.S. Leo says you are his best friend now.", font=ImageFont.truetype(FONT_M, 28), fill=(88, 80, 96))

    sun(d, 905, 120)

    # grass
    for i in range(0, W, 7):
        h = rng.uniform(14, 30)
        crayon_line(d, [(i, 1000), (i + rng.uniform(-6, 6), 1000 - h)], GREEN, 3, 1)
    crayon_line(d, [(0, 1000), (W, 1000)], GREEN, 6)

    # the drawing: two kids hand the robot judge its medal
    robot(d, 712, 990)
    kid(d, 290, 990, PURPLE, BROWN, SKIN[0], height=280, arm_to=(390, 790), girl=True)
    kid(d, 470, 990, ORANGE, INK, SKIN[2], height=230, arm_to=(600, 800))
    heart(d, 560, 610, 2.2, RED)
    heart(d, 890, 650, 1.7, PINK)
    heart(d, 140, 680, 1.5, PINK)

    # labels, as a child would add them
    lab = ImageFont.truetype(FONT_B, 30)
    d.text((620, 620), "YOU!", font=lab, fill=RED)
    crayon_line(d, [(660, 660), (690, 696)], RED, 4, 2)
    d.text((262, 632), "me", font=lab, fill=PURPLE)
    d.text((444, 682), "Leo", font=lab, fill=ORANGE)

    img.save("entry.png", optimize=True)


if __name__ == "__main__":
    main()

"""Flat-illustration presenter 'Priya' drawn with PIL (2x supersampled, cached by pose)."""
import functools, math
from PIL import Image, ImageDraw

CW, CH = 800, 1000          # canvas at 1x
S = 2                       # supersample factor
SKIN, SKIN_SH = (205, 140, 105), (178, 116, 86)
HAIR, KURTI, TRIM = (34, 24, 24), (43, 170, 158), (240, 190, 60)
EYE, LIP_IN = (45, 30, 25), (120, 30, 45)


def _box(b):
    return [v * S for v in b]


@functools.lru_cache(maxsize=512)
def draw(expr="neutral", mouth=0, blink=False, wave=-1):
    """expr: neutral|worried|happy|excited; mouth: 0 closed, 1-4 open levels;
    wave: -1 no arm, else 0-7 phase of a waving raised hand."""
    im = Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # hair (back)
    d.ellipse(_box((185, 130, 615, 560)), fill=HAIR)
    d.rounded_rectangle(_box((195, 330, 605, 690)), 90 * S, fill=HAIR)
    # body / kurti
    d.ellipse(_box((40, 690, 760, 1400)), fill=KURTI)
    # waving arm (behind head level, in front of body)
    if wave >= 0:
        ang = math.radians(-20 + 18 * math.sin(wave / 8 * 2 * math.pi))
        sx, sy = 580, 820
        ex, ey = 670, 610
        hx, hy = ex + 110 * math.sin(ang), ey - 110 * math.cos(ang)
        d.line(_box((sx, sy, ex, ey)), fill=KURTI, width=95 * S)
        d.line(_box((ex, ey, hx, hy)), fill=SKIN, width=70 * S)
        d.ellipse(_box((hx - 55, hy - 65, hx + 55, hy + 55)), fill=SKIN)
        for k in range(4):
            fx = hx - 40 + k * 27
            d.rounded_rectangle(_box((fx - 11, hy - 110, fx + 11, hy - 30)), 11 * S, fill=SKIN)
        d.ellipse(_box((ex - 50, ey - 40, ex + 50, ey + 40)), fill=KURTI)
    # neck + neckline
    d.rectangle(_box((345, 560, 455, 720)), fill=SKIN_SH)
    d.polygon(_box((330, 695, 470, 695, 400, 805)), fill=SKIN_SH)
    d.line(_box((330, 695, 400, 805)), fill=TRIM, width=10 * S)
    d.line(_box((470, 695, 400, 805)), fill=TRIM, width=10 * S)
    # ears + earrings
    for x in (228, 532):
        d.ellipse(_box((x, 380, x + 40, 455)), fill=SKIN)
        d.ellipse(_box((x + 8, 458, x + 32, 482)), fill=TRIM)
    # face
    d.ellipse(_box((250, 215, 550, 605)), fill=SKIN)
    # hair (front) with side part
    d.chord(_box((232, 150, 568, 450)), 180, 360, fill=HAIR)
    d.pieslice(_box((300, 170, 600, 420)), 180, 300, fill=HAIR)
    # bindi
    d.ellipse(_box((393, 322, 407, 336)), fill=(210, 30, 50))
    # blush
    blush = Image.new("RGBA", im.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    a = 90 if expr in ("happy", "excited") else 50
    for x in (305, 495):
        bd.ellipse(_box((x - 32, 455, x + 32, 488)), fill=(235, 110, 110, a))
    im.alpha_composite(blush)
    # brows
    inner = {"worried": -14, "happy": 4, "excited": 8}.get(expr, 0)
    lift = {"excited": -10, "happy": -4}.get(expr, 0)
    d.line(_box((300, 362 + lift, 330, 352 + lift, 372, 357 + lift - inner)), fill=HAIR, width=9 * S, joint="curve")
    d.line(_box((500, 362 + lift, 470, 352 + lift, 428, 357 + lift - inner)), fill=HAIR, width=9 * S, joint="curve")
    # eyes
    for cx in (340, 460):
        if blink:
            d.arc(_box((cx - 24, 390, cx + 24, 412)), 0, 180, fill=EYE, width=6 * S)
        elif expr == "excited":
            d.arc(_box((cx - 24, 392, cx + 24, 420)), 190, 350, fill=EYE, width=8 * S)
        else:
            d.ellipse(_box((cx - 25, 386, cx + 25, 416)), fill=(255, 255, 255))
            d.ellipse(_box((cx - 13, 388, cx + 13, 414)), fill=EYE)
            d.ellipse(_box((cx - 2, 392, cx + 6, 400)), fill=(255, 255, 255))
            d.arc(_box((cx - 27, 383, cx + 27, 418)), 195, 345, fill=HAIR, width=5 * S)
    # nose
    d.arc(_box((388, 432, 412, 462)), 20, 160, fill=SKIN_SH, width=5 * S)
    # mouth
    if mouth > 0:
        h = 10 + mouth * 9
        d.ellipse(_box((372, 500, 428, 500 + h)), fill=LIP_IN)
        d.rectangle(_box((380, 501, 420, 507)), fill=(255, 255, 255))
    elif expr == "worried":
        d.arc(_box((372, 510, 428, 540)), 200, 340, fill=LIP_IN, width=7 * S)
    elif expr in ("happy", "excited"):
        d.chord(_box((360, 480, 440, 548)), 0, 180, fill=LIP_IN)
        d.rectangle(_box((368, 513, 432, 522)), fill=(255, 255, 255))
    else:
        d.arc(_box((365, 478, 435, 528)), 25, 155, fill=LIP_IN, width=7 * S)
    return im.resize((CW, CH), Image.LANCZOS)


def pose(t, expr, talk_windows=(), wave=False):
    """Pick the cached frame for local time t."""
    talking = any(a <= t < b for a, b in talk_windows)
    mouth = int(1 + 3.99 * abs(math.sin(t * 13))) if talking else 0
    blink = (t % 3.1) < 0.12
    w = int((t * 16) % 8) if wave else -1
    return draw(expr, mouth, blink, w)


@functools.lru_cache(maxsize=1)
def _circle_mask(size):
    m = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 2 - 1, size * 2 - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def bubble(img, size, bg=(255, 220, 190), ring=(255, 255, 255)):
    """Circular head-and-shoulders avatar with a white ring."""
    head = img.crop((150, 110, 650, 610)).resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.ellipse((0, 0, size + 15, size + 15), fill=ring)
    disc = Image.new("RGBA", (size, size), bg + (255,))
    disc.alpha_composite(head)
    disc.putalpha(_circle_mask(size))
    out.alpha_composite(disc, (8, 8))
    return out

"""Build the editor pack for the realistic-presenter version of the Desi AI Keyboard ad.

Outputs (in ./assets):
  endcard_5s.mp4            full-frame animated end card
  demo_background_10s.mp4   animated background to sit behind the phone demo
  phone_frame.png           device frame with a transparent screen (drop screen recording under it)
  logo_sting_2s.webm/.mov   logo + name pop, with alpha (VP9 WebM; ProRes 4444 MOV is not committed, too large)
  feature_pills_4s.webm/.mov feature chips popping in, with alpha
  captions/*.png            styled caption stickers, transparent
  style_frames.png          preview of the look
Run: python3 build_pack.py <fonts_dir>
"""
import functools, math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

FONTS = sys.argv[1] if len(sys.argv) > 1 else "fonts"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(os.path.join(OUT, "captions"), exist_ok=True)
W, H, FPS = 1080, 1920, 30

NAVY_D, NAVY = (6, 16, 40), (16, 38, 82)
SAFF, AMBER = (255, 112, 40), (255, 184, 48)
GREEN, TEAL = (34, 177, 92), (24, 200, 170)
WHITE = (255, 255, 255)


@functools.lru_cache(None)
def font(kind, size):
    name = {"xb": "pop-xb.ttf", "sb": "pop-sb.ttf", "hi": "deva.ttf"}[kind]
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def clamp(x): return max(0.0, min(1.0, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def out3(x): return 1 - (1 - x) ** 3
def back(x, c1=1.9): return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ---------- primitives ----------
def lin_grad(w, h, c1, c2, horizontal=True):
    g = Image.linear_gradient("L").rotate(90 if horizontal else 0, expand=True).resize((w, h))
    if horizontal:
        g = g.transpose(Image.FLIP_LEFT_RIGHT)
    return Image.composite(Image.new("RGBA", (w, h), c2 + (255,)), Image.new("RGBA", (w, h), c1 + (255,)), g)


@functools.lru_cache(None)
def text_layer(text, kind, size, fill=WHITE, grad=None, stroke=0, stroke_fill=(0, 0, 0)):
    f = font(kind, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    w, h = r - l + 12, b - t + 12
    if grad:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).text((6 - l, 6 - t), text, font=f, fill=255)
        im = lin_grad(w, h, *grad)
        im.putalpha(mask)
        return im
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((6 - l, 6 - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def shadow(im, blur=28, off=14, alpha=110, color=(0, 0, 0)):
    pad = blur * 2
    base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    base.paste(color + (255,), (pad, pad + off), a)
    base = base.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(im, (pad, pad))
    return base


def glow(im, blur=30, color=SAFF, strength=1.0):
    pad = blur * 2
    base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: int(v * strength))
    base.paste(color + (255,), (pad, pad), a)
    base = base.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(im, (pad, pad))
    return base


def paste(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if abs(scale - 1) > 0.004:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def glass(w, h, r, tint=(255, 255, 255), a=34, border=70):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=tint + (a,), outline=(255, 255, 255, border), width=2)
    hl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((2, 2, w - 3, h // 2), r, fill=(255, 255, 255, 18))
    im.alpha_composite(hl)
    return im


# ---------- background ----------
@functools.lru_cache(None)
def base_gradient():
    small = Image.new("RGB", (108, 192))
    px = small.load()
    for y in range(192):
        for x in range(108):
            dx, dy = (x - 54) / 108, (y - 70) / 192
            k = clamp(math.hypot(dx * 1.3, dy) * 1.6)
            px[x, y] = tuple(int(NAVY[i] * (1 - k) + NAVY_D[i] * k) for i in range(3))
    return small.resize((W, H), Image.BICUBIC).convert("RGBA")


random.seed(7)
SPARKS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(0, 6.28)) for _ in range(70)]


def background(t):
    im = base_gradient().copy()
    orbs = Image.new("RGBA", (135, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(orbs)
    for (cx, cy, r, col, sp, ph) in [(20, 40, 45, SAFF, 0.35, 0), (115, 200, 55, GREEN, 0.3, 2),
                                     (110, 60, 30, (120, 80, 255), 0.4, 4), (30, 190, 30, TEAL, 0.5, 1)]:
        x = cx + 12 * math.sin(t * sp + ph); y = cy + 10 * math.cos(t * sp * 0.8 + ph)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (120,))
    orbs = orbs.filter(ImageFilter.GaussianBlur(18)).resize((W, H), Image.BICUBIC)
    im.alpha_composite(orbs)
    d = ImageDraw.Draw(im)
    for (x, y, r, ph) in SPARKS:
        a = int(140 * (0.5 + 0.5 * math.sin(t * 2.2 + ph)))
        yy = (y - t * 18) % H
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 255, 255, a))
    return im


# ---------- logo ----------
@functools.lru_cache(None)
def logo(size):
    s = size * 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    g = lin_grad(s, s, (255, 255, 255), (222, 230, 245), horizontal=False)
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
    im.paste(g, (0, 0), m)
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, s - 7, s - 7), outline=(255, 255, 255, 255), width=6)
    d.text((s / 2, s / 2 + s * 0.02), "D", font=font("xb", int(s * 0.56)), fill=NAVY, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


def logo_block(t, size=260):
    """Logo with burst ring; returns layer pieces drawn into a square canvas."""
    c = size * 2
    im = Image.new("RGBA", (c, c), (0, 0, 0, 0))
    rp = prog(t, 0.15, 0.8)
    if 0 < rp < 1:
        d = ImageDraw.Draw(im)
        r = size * (0.5 + 0.5 * out3(rp))
        d.ellipse((c / 2 - r, c / 2 - r, c / 2 + r, c / 2 + r), outline=AMBER + (int(255 * (1 - rp)),), width=8)
    p = prog(t, 0.0, 0.45)
    if p > 0:
        paste(im, glow(logo(size), 34, AMBER, 0.55), c / 2, c / 2, back(p))
    return im


# ---------- confetti ----------
random.seed(3)
CONF = [(random.uniform(0, W), random.uniform(-600, -20), random.uniform(120, 260), random.choice([SAFF, WHITE, GREEN, AMBER]),
         random.uniform(0, 6.28), random.uniform(10, 22)) for _ in range(90)]


def confetti(im, t, start):
    lt = t - start
    if lt < 0 or lt > 3.2:
        return
    d = ImageDraw.Draw(im)
    a = int(255 * (1 - prog(lt, 2.4, 3.2)))
    for (x, y0, v, col, ph, s) in CONF:
        y = y0 + v * lt * 2.2
        xx = x + 30 * math.sin(lt * 3 + ph)
        w = s * abs(math.cos(lt * 6 + ph))
        d.rectangle((xx - w / 2, y - s / 3, xx + w / 2, y + s / 3), fill=col + (a,))


# ---------- end card ----------
def cta_button(t):
    w, h = 780, 190
    im = lin_grad(w, h, SAFF, AMBER)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=255)
    # shine sweep
    sx = ((t * 1.0) % 1.6) / 1.6 * (w + 300) - 150
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(sx, 0), (sx + 70, 0), (sx - 10, h), (sx - 80, h)], fill=(255, 255, 255, 90))
    im.alpha_composite(sh)
    im.putalpha(m)
    d = ImageDraw.Draw(im)
    d.text((w / 2, 74), "Download FREE", font=font("xb", 66), fill=WHITE, anchor="mm")
    f = font("sb", 36)
    tw = f.getlength("on Google Play")
    tx = w / 2 - (tw + 40) / 2
    d.polygon([(tx, 126), (tx, 154), (tx + 24, 140)], fill=(255, 245, 230))
    d.text((tx + 40, 140), "on Google Play", font=f, fill=(255, 245, 230), anchor="lm")
    return shadow(glow(im, 26, SAFF, 0.5), 20, 12, 120)


def flag(w=66):
    h = int(w * 2 / 3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h / 3), fill=(255, 153, 51))
    d.rectangle((0, h / 3, w, 2 * h / 3), fill=WHITE)
    d.rectangle((0, 2 * h / 3, w, h), fill=(19, 136, 8))
    r = h / 7
    d.ellipse((w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r), outline=(0, 0, 128), width=2)
    return im


def endcard(t):
    im = background(t)
    paste(im, logo_block(t, 250), W / 2, 380)
    for (txt, kind, size, grad, y, st) in [("Desi AI Keyboard", "xb", 104, None, 680, 0.35),
                                           ("Translate Instantly.", "xb", 82, (SAFF, AMBER), 810, 0.6),
                                           ("Chat Globally.", "xb", 82, (GREEN, TEAL), 910, 0.8)]:
        p = out3(prog(t, st, st + 0.45))
        if p > 0:
            paste(im, shadow(text_layer(txt, kind, size, grad=grad), 16, 8, 120), W / 2, y + (1 - p) * 60, 1, p)
    chips = ["AI Translate", "Voice", "Fonts", "Stickers"]
    tls = [text_layer(c, "sb", 34) for c in chips]
    widths = [tl.width + 50 for tl in tls]
    x = W / 2 - (sum(widths) + 18 * (len(chips) - 1)) / 2
    for i, (tl, cw) in enumerate(zip(tls, widths)):
        p = prog(t, 1.0 + i * 0.1, 1.35 + i * 0.1)
        if p > 0:
            g = glass(cw, 74, 37)
            g.alpha_composite(tl, (25, (74 - tl.height) // 2))
            paste(im, g, x + cw / 2, 1050, back(p), p)
        x += cw + 18
    p = prog(t, 1.5, 1.9)
    if p > 0:
        pulse = 1 + 0.03 * math.sin((t - 1.9) * 6) if t > 1.9 else 1
        paste(im, cta_button(t), W / 2, 1290, back(p) * pulse)
    p = prog(t, 2.1, 2.5)
    if p > 0:
        tl = text_layer("Proudly made for India", "sb", 46, fill=(220, 228, 245))
        row = Image.new("RGBA", (tl.width + 90, max(tl.height, 50)), (0, 0, 0, 0))
        row.alpha_composite(tl, (0, (row.height - tl.height) // 2))
        fl = flag(66)
        row.alpha_composite(fl, (tl.width + 20, (row.height - fl.height) // 2))
        paste(im, row, W / 2, 1520, 1, p)
    confetti(im, t, 1.5)
    return im


# ---------- overlays with alpha ----------
def logo_sting(t):
    im = Image.new("RGBA", (1000, 800), (0, 0, 0, 0))
    paste(im, logo_block(t, 260), 500, 300)
    p = out3(prog(t, 0.45, 0.9))
    if p > 0:
        paste(im, shadow(text_layer("Desi AI Keyboard", "xb", 100), 16, 8, 150), 500, 640 + (1 - p) * 50, 1, p)
    return im


FEATS = [("AI Translation", (70, 130, 255), "अ"), ("Voice Input", (160, 90, 230), "V"),
         ("Handwriting", GREEN, "H"), ("Stylish Fonts", (235, 70, 140), "Aa"),
         ("Stickers & GIF", AMBER, "S"), ("Memes & Reels", SAFF, "M"),
         ("Themes", (100, 110, 240), "T"), ("Clipboard", TEAL, "C")]


@functools.lru_cache(None)
def pill(label, col, glyph):
    w, h = 460, 140
    im = glass(w, h, 44, tint=NAVY_D, a=190, border=90)
    d = ImageDraw.Draw(im)
    icon = lin_grad(76, 76, col, tuple(min(255, c + 60) for c in col))
    m = Image.new("L", (76, 76), 0); ImageDraw.Draw(m).ellipse((0, 0, 75, 75), fill=255)
    icon.putalpha(m)
    im.alpha_composite(icon, (30, 32))
    d.text((68, 70), glyph, font=font("hi" if glyph == "अ" else "xb", 34), fill=WHITE, anchor="mm")
    d.text((126, 70), label, font=font("sb", 40), fill=WHITE, anchor="lm")
    return shadow(im, 20, 10, 120)


def feature_pills(t):
    im = Image.new("RGBA", (1080, 1000), (0, 0, 0, 0))
    for i, (lab, c, g) in enumerate(FEATS):
        p = prog(t, 0.1 + i * 0.12, 0.45 + i * 0.12)
        if p > 0:
            cx = 540 + (-240 if i % 2 == 0 else 240)
            cy = 140 + (i // 2) * 180
            paste(im, pill(lab, c, g), cx, cy + 6 * math.sin(t * 2.5 + i), back(p), min(1, p * 2))
    return im


# ---------- phone frame ----------
SCREEN = (185, 230, 895, 1808)   # x0, y0, x1, y1 of the transparent screen (710x1578, fits 1080x2400 at 65.7%)


def phone_frame():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = SCREEN[0] - 22, SCREEN[1] - 22, SCREEN[2] + 22, SCREEN[3] + 22
    body = lin_grad(x1 - x0, y1 - y0, (70, 74, 84), (28, 30, 36))
    m = Image.new("L", body.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, body.width - 1, body.height - 1), 92, fill=255)
    body.putalpha(m)
    d = ImageDraw.Draw(body)
    d.rounded_rectangle((2, 2, body.width - 3, body.height - 3), 90, outline=(150, 155, 168, 255), width=3)
    hole = Image.new("L", body.size, 0)
    ImageDraw.Draw(hole).rounded_rectangle((22, 22, body.width - 23, body.height - 23), 72, fill=255)
    body.putalpha(ImageChops.subtract(body.getchannel("A"), hole))
    d = ImageDraw.Draw(body)
    cx = body.width // 2
    d.rounded_rectangle((cx - 90, 46, cx + 90, 98), 26, fill=(5, 5, 8, 255))  # camera pill
    sh = shadow(body, 40, 24, 150)
    pad = 80
    im.alpha_composite(sh, (x0 - pad, y0 - pad))
    return im


# ---------- captions ----------
CAPTIONS = [
    ("01_hook", "Mera naya boss sirf", "ENGLISH", "samajhta hai..."),
    ("02_struggle", "10 minute se", "1 LINE", "likh rahi hoon"),
    ("03_reveal", "Phir maine try kiya", "DESI AI KEYBOARD", ""),
    ("04_type_hindi", "", "HINDI", "mein likho..."),
    ("05_send_english", "...", "ENGLISH", "mein bhejo!"),
    ("06_approved", "Boss ne turant", "HAAN", "bol diya!"),
    ("07_features", "Sab kuch", "EK KEYBOARD", "mein"),
]


def caption(pre, hi, post):
    lines = []
    if pre: lines.append(("plain", pre))
    lines.append(("hi", hi))
    if post: lines.append(("plain", post))
    parts = []
    for kind, txt in lines:
        if kind == "plain":
            parts.append(text_layer(txt, "xb", 74, fill=WHITE, stroke=7, stroke_fill=(0, 0, 0)))
        else:
            tl = text_layer(txt, "xb", 84, fill=NAVY_D)
            box = lin_grad(tl.width + 50, tl.height + 26, AMBER, SAFF)
            m = Image.new("L", box.size, 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, box.width - 1, box.height - 1), 22, fill=255)
            box.putalpha(m)
            box.alpha_composite(tl, (25, 13))
            parts.append(shadow(box.rotate(-2, expand=True, resample=Image.BICUBIC), 14, 8, 130))
    h = sum(p.height for p in parts) - 10 * (len(parts) - 1)
    im = Image.new("RGBA", (1060, h + 20), (0, 0, 0, 0))
    y = 10
    for p in parts:
        im.alpha_composite(p, ((im.width - p.width) // 2, y))
        y += p.height - 10
    return im


# ---------- writers ----------
def write_mp4(path, fn, dur):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        ff.stdin.write(fn(i / FPS).convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()


def write_alpha_mov(path, fn, dur, size):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{size[0]}x{size[1]}",
                           "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-qscale:v", "11",
                           "-pix_fmt", "yuva444p10le", path], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        ff.stdin.write(fn(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                    "-b:v", "0", "-crf", "30", "-auto-alt-ref", "0", path[:-4] + ".webm"], check=True)


if __name__ == "__main__":
    only = sys.argv[2] if len(sys.argv) > 2 else "all"
    if only in ("all", "stills"):
        phone_frame().save(os.path.join(OUT, "phone_frame.png"))
        for name, a, b, c in CAPTIONS:
            caption(a, b, c).save(os.path.join(OUT, "captions", name + ".png"))
        # style frames preview
        sf = Image.new("RGB", (4 * 360, 640), (0, 0, 0))
        f1 = endcard(4.0)
        f2 = background(1.0); f2.alpha_composite(phone_frame())
        f3 = background(2.0); paste(f3, feature_pills(3.0), W / 2, 960)
        f4 = background(0.5); paste(f4, caption(*CAPTIONS[0][1:]), W / 2, 1450); paste(f4, logo_sting(1.5), W / 2, 600)
        for i, f in enumerate([f1, f2, f3, f4]):
            sf.paste(f.convert("RGB").resize((360, 640)), (i * 360, 0))
        sf.save(os.path.join(OUT, "style_frames.png"))
    if only in ("all", "video"):
        write_mp4(os.path.join(OUT, "endcard_5s.mp4"), endcard, 5)
        write_mp4(os.path.join(OUT, "demo_background_10s.mp4"), background, 10)
        write_alpha_mov(os.path.join(OUT, "logo_sting_2s.mov"), logo_sting, 2, (1000, 800))
        write_alpha_mov(os.path.join(OUT, "feature_pills_4s.mov"), feature_pills, 4, (1080, 1000))

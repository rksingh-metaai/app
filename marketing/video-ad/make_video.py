"""Render a 30s 9:16 motion-graphics ad for Desi AI Keyboard -> frames piped to ffmpeg."""
import math, subprocess, sys, functools
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-user-app/917a2b34-6e03-5ca5-8c24-e1ba95ce7451"
F = D + "/scratchpad/fonts/"
W, H, FPS, DUR = 1080, 1920, 30, 30.0

NAVY, SAFF, GREEN = (15, 53, 84), (242, 106, 33), (30, 142, 62)
CREAM, WHITE, INK = (255, 247, 236), (255, 255, 255), (28, 32, 40)
GREY = (110, 116, 128)


@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype(F + {"xb": "pop-xb.ttf", "sb": "pop-sb.ttf", "hi": "deva.ttf"}[name], size)


def clamp(x):
    return max(0.0, min(1.0, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def back(x):
    c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def out(x):
    return 1 - (1 - x) ** 3


@functools.lru_cache(None)
def text_img(text, fname, size, fill, stroke=0, stroke_fill=None):
    f = font(fname, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), text, font=f, fill=fill,
                            stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def paste(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def pop_text(base, t, start, text, fname, size, fill, cx, cy, dur=0.35):
    p = prog(t, start, start + dur)
    if p > 0:
        paste(base, text_img(text, fname, size, fill), cx, cy, back(p), min(1, p * 2))


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= maxw:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def rrect(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ---------- static backgrounds ----------
def blob_bg(color, blobs):
    im = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(im)
    for (x, y, r, c) in blobs:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c[:3])
    return im.filter(ImageFilter.GaussianBlur(140)).convert("RGBA")


def tricolor_wave(im, top=1560):
    d = ImageDraw.Draw(im)
    for i, (c, off) in enumerate([(SAFF, 0), (WHITE, 55), (GREEN, 110)]):
        pts = [(x, top + off + 40 * math.sin(x / 170 + i * 0.5)) for x in range(0, W + 20, 20)]
        d.polygon(pts + [(W, H), (0, H)], fill=c)
    return im


BG_NAVY = blob_bg(NAVY, [(150, 300, 260, (40, 90, 140, 255)), (950, 1600, 320, (35, 80, 130, 255))])
lay = ImageDraw.Draw(BG_NAVY)
for i, ch in enumerate("अ क ह म र स ग ब न त प ल".split()):
    x, y = (97 * i * 7) % 1000 + 40, (173 * i * 5) % 1800 + 60
    lay.text((x, y), ch, font=font("hi", 90), fill=(40, 82, 120))
BG_CREAM = blob_bg(CREAM, [(100, 200, 300, (255, 220, 190, 255)), (1000, 1700, 350, (205, 240, 215, 255))])
BG_WAVE = tricolor_wave(BG_CREAM.copy())


def logo(size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=WHITE, outline=(225, 225, 230), width=max(2, size // 60))
    f = font("xb", int(size * 0.55))
    d.text((size / 2, size / 2 + size * 0.03), "D", font=f, fill=NAVY, anchor="mm")
    return im


LOGO = logo(340)


def shadowed(im, radius=40, off=18, opacity=90):
    pad = radius * 2
    sh = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    mask = im.getchannel("A").point(lambda v: opacity if v > 0 else 0)
    sh.paste((0, 0, 0, 255), (pad, pad + off), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    sh.alpha_composite(im, (pad, pad))
    return sh


# ---------- Scene 1: hook (0-3s) ----------
def scene1(t):
    im = BG_NAVY.copy()
    pop_text(im, t, 0.10, "Mera naya boss", "xb", 92, WHITE, W / 2, 700)
    pop_text(im, t, 0.55, "sirf ENGLISH", "xb", 140, SAFF, W / 2, 880)
    pop_text(im, t, 1.05, "samajhta hai...", "xb", 92, WHITE, W / 2, 1060)
    if t > 1.8:
        shake = math.sin(t * 40) * 6 * (1 - prog(t, 1.8, 2.6))
        pop_text(im, t, 1.8, "( aur meri English? )", "sb", 60, (170, 200, 230), W / 2 + shake, 1280)
    return im


# ---------- Scene 2: struggle (3-7s) ----------
TYPO = "Sir I am want leav tomorow"


def scene2(t):
    im = BG_CREAM.copy()
    pop_text(im, t, 0.05, "Bas theek-thaak", "xb", 100, INK, W / 2, 520)
    pop_text(im, t, 0.35, "wali English...", "xb", 100, SAFF, W / 2, 650)
    d = ImageDraw.Draw(im)
    rrect(d, (80, 960, 1000, 1110), 75, WHITE, outline=(220, 220, 225), width=3)
    if t < 2.2:
        n = int(len(TYPO) * prog(t, 0.8, 2.1))
    else:
        n = int(len(TYPO) * (1 - prog(t, 2.2, 2.75)))
    txt = TYPO[:n]
    f = font("sb", 52)
    d.text((130, 1035), txt, font=f, fill=INK, anchor="lm")
    if int(t * 3) % 2 == 0:
        x = 132 + f.getlength(txt)
        d.rectangle((x, 1000, x + 5, 1070), fill=SAFF)
    p = prog(t, 2.9, 3.2)
    if p > 0:
        st = text_img("10 MINUTE. 1 LINE.", "xb", 76, (220, 40, 40))
        box = Image.new("RGBA", (st.width + 60, st.height + 40), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 0, box.width - 1, box.height - 1), 20, outline=(220, 40, 40), width=8)
        box.alpha_composite(st, (30, 20))
        box = box.rotate(-8, expand=True, resample=Image.BICUBIC)
        paste(im, box, W / 2, 1350, 1.8 - 0.8 * out(p), p)
    return im


# ---------- Scene 3: reveal (7-10s) ----------
def scene3(t):
    im = BG_WAVE.copy()
    pop_text(im, t, 0.05, "Phir maine try kiya", "xb", 84, INK, W / 2, 360)
    p = prog(t, 0.45, 0.95)
    if p > 0:
        paste(im, shadowed(LOGO), W / 2, 830, back(p) * (1 + 0.02 * math.sin(t * 4)))
    pop_text(im, t, 1.0, "Desi AI Keyboard", "xb", 104, NAVY, W / 2, 1150)
    pop_text(im, t, 1.4, "Translate while you type", "sb", 58, GREEN, W / 2, 1280)
    return im


# ---------- Scene 4: translation demo (10-19s) ----------
PX0, PY0, PX1, PY1 = 150, 470, 930, 1880
SX0, SY0, SX1, SY1 = PX0 + 22, PY0 + 22, PX1 - 22, PY1 - 22


def build_phone():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rrect(d, (PX0, PY0, PX1, PY1), 80, (20, 20, 24))
    rrect(d, (SX0, SY0, SX1, SY1), 60, (236, 229, 221))
    # header
    d.rounded_rectangle((SX0, SY0, SX1, SY0 + 150), 60, fill=(7, 94, 84))
    d.rectangle((SX0, SY0 + 90, SX1, SY0 + 150), fill=(7, 94, 84))
    d.ellipse((SX0 + 40, SY0 + 40, SX0 + 120, SY0 + 120), fill=(200, 210, 220))
    d.text((SX0 + 80, SY0 + 80), "B", font=font("xb", 40), fill=(7, 94, 84), anchor="mm")
    d.text((SX0 + 145, SY0 + 62), "Boss", font=font("sb", 44), fill=WHITE, anchor="lm")
    d.text((SX0 + 145, SY0 + 108), "online", font=font("sb", 28), fill=(190, 230, 220), anchor="lm")
    # keyboard
    ky = 1420
    d.rectangle((SX0, ky, SX1, SY1 - 40), fill=(232, 234, 238))
    d.rounded_rectangle((SX0, SY1 - 120, SX1, SY1), 60, fill=(232, 234, 238))
    for r, n in enumerate([10, 9, 7]):
        kw = (SX1 - SX0 - 40) / 10
        x0 = SX0 + 20 + (10 - n) * kw / 2
        for k in range(n):
            y = ky + 110 + r * 95
            rrect(d, (x0 + k * kw + 5, y, x0 + (k + 1) * kw - 5, y + 80), 12, WHITE)
    rrect(d, (SX0 + 180, ky + 395, SX1 - 180, ky + 395 + 0), 12, WHITE)
    return im


PHONE = build_phone()
HI_WORDS = "कल मुझे छुट्टी चाहिए, घर पे function है".split(" ")
EN_TEXT = "I need leave tomorrow, there's a function at home."


def bubble(text, maxw, fill, fname="sb", size=36):
    f = font(fname, size)
    lines = wrap(text, f, maxw)
    lh = int(size * 1.35)
    w = int(max(f.getlength(l) for l in lines)) + 56
    h = lh * len(lines) + 36
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rrect(d, (0, 0, w - 1, h - 1), 26, fill)
    for i, l in enumerate(lines):
        d.text((28, 18 + i * lh), l, font=f, fill=INK)
    return im


B_IN1 = bubble("Are you coming to office tomorrow?", 480, WHITE)
B_OUT = bubble(EN_TEXT, 480, (220, 248, 198))
B_IN2 = bubble("Sure, no problem. Approved!", 480, WHITE)


def scene4(t):
    im = BG_CREAM.copy()
    # caption
    if t < 4.5:
        pop_text(im, t, 0.1, "Hindi mein likho...", "xb", 88, NAVY, W / 2, 270)
    elif t < 7.0:
        pop_text(im, t, 4.5, "...English mein bhejo!", "xb", 88, SAFF, W / 2, 270)
    else:
        pop_text(im, t, 7.0, "Boss ne turant", "xb", 80, NAVY, W / 2, 210)
        pop_text(im, t, 7.2, "haan bol diya!", "xb", 80, GREEN, W / 2, 320)
    slide = out(prog(t, 0.0, 0.5))
    layer = PHONE.copy()
    d = ImageDraw.Draw(layer)
    # chat bubbles
    layer.alpha_composite(B_IN1, (SX0 + 30, SY0 + 190))
    p = prog(t, 5.6, 5.95)
    if p > 0:
        b = B_OUT.resize((max(1, int(B_OUT.width * (0.6 + 0.4 * back(p)))),
                          max(1, int(B_OUT.height * (0.6 + 0.4 * back(p))))))
        layer.alpha_composite(b, (SX1 - 30 - b.width, SY0 + 340))
    if 6.4 < t < 7.0:
        dots = Image.new("RGBA", (150, 70), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dots)
        rrect(dd, (0, 0, 149, 69), 26, WHITE)
        for k in range(3):
            yy = 35 - 8 * max(0, math.sin(t * 12 - k))
            dd.ellipse((30 + k * 35 - 9, yy - 9, 30 + k * 35 + 9, yy + 9), fill=GREY)
        layer.alpha_composite(dots, (SX0 + 30, SY0 + 340 + B_OUT.height + 30))
    p = prog(t, 7.0, 7.3)
    if p > 0:
        b = B_IN2.resize((max(1, int(B_IN2.width * (0.6 + 0.4 * back(p)))),
                          max(1, int(B_IN2.height * (0.6 + 0.4 * back(p))))))
        layer.alpha_composite(b, (SX0 + 30, SY0 + 340 + B_OUT.height + 30))
    # input bar
    rrect(d, (SX0 + 20, 1250, SX1 - 120, 1400), 40, WHITE)
    d.ellipse((SX1 - 105, 1285, SX1 - 25, 1365), fill=(0, 168, 132))
    d.polygon([(SX1 - 82, 1305), (SX1 - 82, 1345), (SX1 - 45, 1325)], fill=WHITE)
    maxw = SX1 - 120 - (SX0 + 50) - 20
    if t < 4.5 or (4.5 <= t < 5.0):
        nw = int(len(HI_WORDS) * prog(t, 0.7, 3.3) + 0.999)
        txt = " ".join(HI_WORDS[:nw])
        f = font("hi", 42)
        a = 1 - prog(t, 4.5, 4.9)
        lines = wrap(txt, f, maxw) if txt else [""]
        col = tuple(int(c * a + 255 * (1 - a)) for c in INK)
        for i, l in enumerate(lines):
            d.text((SX0 + 50, 1278 + i * 52), l, font=f, fill=col)
        if t < 3.6 and int(t * 3) % 2 == 0:
            last = lines[-1]
            x = SX0 + 52 + f.getlength(last)
            yy = 1278 + (len(lines) - 1) * 52
            d.rectangle((x, yy + 4, x + 4, yy + 48), fill=SAFF)
    if 4.5 <= t < 5.6:
        f = font("sb", 34)
        a = prog(t, 4.6, 5.0)
        col = tuple(int(c * a + 255 * (1 - a)) for c in INK)
        for i, l in enumerate(wrap(EN_TEXT, f, maxw)):
            d.text((SX0 + 50, 1282 + i * 48), l, font=f, fill=col)
    # toolbar with translate chip
    ky = 1420
    pulse = 1 + 0.06 * math.sin(t * 10) if 3.4 < t < 4.6 else 1
    chip_on = t >= 4.0
    cw, ch = 300 * pulse, 70 * pulse
    cx, cy = SX0 + 40 + 150, ky + 52
    rrect(d, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), 35,
          SAFF if chip_on else WHITE, outline=SAFF, width=4)
    d.text((cx, cy), "अA  Translate", font=font("hi", 34), fill=WHITE if chip_on else SAFF, anchor="mm")
    for i, lab in enumerate(["Voice", "GIF", "Fonts"]):
        d.text((SX0 + 400 + i * 130, cy), lab, font=font("sb", 30), fill=GREY, anchor="mm")
    # tap ripple
    tp = prog(t, 3.8, 4.4)
    if 0 < tp < 1:
        r = 30 + 70 * tp
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255), width=int(10 * (1 - tp)) + 1)
        d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=(255, 255, 255, int(160 * (1 - tp))))
    # send tap
    sp = prog(t, 5.3, 5.7)
    if 0 < sp < 1:
        sx, sy = SX1 - 65, 1325
        r = 30 + 60 * sp
        d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=(0, 168, 132), width=int(10 * (1 - sp)) + 1)
    im.alpha_composite(layer, (0, int((1 - slide) * 900)))
    return im


# ---------- Scene 5: features (19-25s) ----------
def load_shot():
    s = Image.open(D + "/images/2.webp").convert("RGBA")
    s = s.crop((0, 60, s.width, s.height - 80))
    h = 1240
    s = s.resize((int(s.width * h / s.height), h), Image.LANCZOS)
    mask = Image.new("L", s.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s.width - 1, s.height - 1), 50, fill=255)
    s.putalpha(mask)
    fr = Image.new("RGBA", (s.width + 36, s.height + 36), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle((0, 0, fr.width - 1, fr.height - 1), 66, fill=(20, 20, 24))
    fr.alpha_composite(s, (18, 18))
    return shadowed(fr)


SHOT = load_shot()
FEATS = [("AI Translation", (60, 120, 220)), ("Voice Input", (140, 80, 200)),
         ("Handwriting", GREEN), ("Stylish Fonts", (220, 60, 120)),
         ("Stickers & GIF", (240, 160, 20)), ("Memes & Reels", SAFF),
         ("Themes", (90, 90, 200)), ("Clipboard", (0, 150, 150))]


@functools.lru_cache(None)
def pill(label, color):
    im = Image.new("RGBA", (450, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rrect(d, (0, 0, 449, 149), 40, WHITE, outline=(230, 230, 235), width=3)
    d.ellipse((30, 45, 90, 105), fill=color)
    d.text((60, 75), label[0], font=font("xb", 34), fill=WHITE, anchor="mm")
    d.text((112, 75), label, font=font("sb", 40), fill=INK, anchor="lm")
    return im


def scene5(t):
    im = BG_CREAM.copy()
    if t < 2.8:
        pop_text(im, t, 0.05, "Aur bhi bahut kuch!", "xb", 92, NAVY, W / 2, 250)
        p = out(prog(t, 0.0, 0.6))
        paste(im, SHOT, W / 2, 1130 + (1 - p) * 800, 1.0 + 0.04 * prog(t, 0.6, 2.8))
    else:
        lt = t - 2.8
        pop_text(im, lt, 0.0, "Sab kuch", "xb", 96, NAVY, W / 2, 330)
        pop_text(im, lt, 0.2, "ek keyboard mein", "xb", 96, SAFF, W / 2, 460)
        for i, (lab, c) in enumerate(FEATS):
            p = prog(lt, 0.35 + i * 0.13, 0.7 + i * 0.13)
            cx = W / 2 + (-245 if i % 2 == 0 else 245)
            cy = 700 + (i // 2) * 200
            paste(im, pill(lab, c), cx, cy, back(p), min(1, p * 2))
        pop_text(im, lt, 1.8, "Bolo, likho, style karo", "sb", 60, GREEN, W / 2, 1560)
    return im


# ---------- Scene 6: end card (25-30s) ----------
def scene6(t):
    im = BG_WAVE.copy()
    p = prog(t, 0.1, 0.55)
    if p > 0:
        paste(im, shadowed(logo(260)), W / 2, 380, back(p))
    pop_text(im, t, 0.4, "Desi AI Keyboard", "xb", 100, NAVY, W / 2, 640)
    pop_text(im, t, 0.7, "Translate Instantly.", "xb", 76, SAFF, W / 2, 790)
    pop_text(im, t, 0.9, "Chat Globally.", "xb", 76, GREEN, W / 2, 890)
    p = prog(t, 1.4, 1.8)
    if p > 0:
        btn = Image.new("RGBA", (760, 170), (0, 0, 0, 0))
        bd = ImageDraw.Draw(btn)
        rrect(bd, (0, 0, 759, 169), 85, NAVY)
        bd.text((380, 62), "Download FREE", font=font("xb", 62), fill=WHITE, anchor="mm")
        bd.text((380, 125), "on Google Play", font=font("sb", 34), fill=(190, 210, 235), anchor="mm")
        pulse = 1 + 0.035 * math.sin((t - 1.8) * 6) if t > 1.8 else 1
        paste(im, shadowed(btn, 30, 12, 70), W / 2, 1140, back(p) * pulse)
    pop_text(im, t, 2.0, "Proudly made for India", "sb", 52, INK, W / 2, 1360)
    return im


SCENES = [(0, 3, scene1), (3, 7, scene2), (7, 10, scene3), (10, 19, scene4), (19, 25, scene5), (25, 30, scene6)]


def frame(gt):
    for a, b, fn in SCENES:
        if a <= gt < b:
            im = fn(gt - a)
            # quick flash-fade in on each cut
            fp = prog(gt, a, a + 0.12)
            if fp < 1 and a > 0:
                im = Image.blend(Image.new("RGBA", (W, H), WHITE), im, fp)
            return im.convert("RGB")
    return scene6(4.99).convert("RGB")


if __name__ == "__main__":
    outp = sys.argv[1]
    if len(sys.argv) > 2:  # preview stills
        for s in sys.argv[2:]:
            frame(float(s)).save(f"{outp}_{s}.png")
        sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", outp],
                          stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()

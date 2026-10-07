"""Complete 30s premium-style ad (v3): pack look + animated presenter Priya + chat demo.
Run from this folder: python3 render_v3.py <fonts_dir> <out.mp4> [audio.wav] [--stills t1 t2 ...]"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack"))
import build_pack as bp
import priya

bp.FONTS = sys.argv[1]
W, H, FPS, DUR = 1080, 1920, 30, 30.0
prog, back, out3, paste = bp.prog, bp.back, bp.out3, bp.paste
CAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack", "assets", "captions")
CAPS = {n: Image.open(os.path.join(CAP, n + ".png")).convert("RGBA") for n, *_ in
        [(c[0],) for c in bp.CAPTIONS]}
INK, GREY = (28, 32, 40), (110, 116, 128)


def pop_img(base, t, start, im, cx, cy, scale=1.0, dur=0.35):
    p = prog(t, start, start + dur)
    if p > 0:
        paste(base, im, cx, cy, back(p) * scale, min(1, p * 2))


def presenter(base, t, expr, talks, scale, top, cx=W / 2, wave=False, enter=0.0):
    p = out3(prog(t, enter, enter + 0.45))
    if p <= 0:
        return
    fig = priya.pose(t, expr, talks, wave)
    fig = fig.resize((int(fig.width * scale), int(fig.height * scale)), Image.LANCZOS)
    paste(base, bp.glow(fig, 40, bp.AMBER, 0.35), cx, top + fig.height / 2 + (1 - p) * 500 + 6 * math.sin(t * 3.2))


def avatar(base, t, expr, talks, cx, cy, size=230, enter=0.0):
    p = prog(t, enter, enter + 0.35)
    if p > 0:
        b = priya.bubble(priya.pose(t, expr, talks), size, bg=(255, 214, 170), ring=bp.AMBER)
        paste(base, bp.glow(b, 26, bp.SAFF, 0.6), cx, cy, back(p))


# ---------- chat screen (710 x 1578, drawn inside the phone frame) ----------
SW, SH = bp.SCREEN[2] - bp.SCREEN[0], bp.SCREEN[3] - bp.SCREEN[1]
HI_WORDS = "कल मुझे छुट्टी चाहिए, घर पे function है".split(" ")
EN_TEXT = "I need leave tomorrow, there's a function at home."


def bubble(text, maxw, fill, size=34, tick=False):
    f = bp.font("sb", size)
    lines = wrap(text, f, maxw)
    lh = int(size * 1.35)
    w = int(max(f.getlength(l) for l in lines)) + 60
    h = lh * len(lines) + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 24, fill=fill)
    for i, l in enumerate(lines):
        d.text((28, 18 + i * lh), l, font=f, fill=INK)
    if tick:
        for k in (0, 12):
            d.line([(w - 50 + k, h - 22), (w - 43 + k, h - 15), (w - 30 + k, h - 30)], fill=(52, 183, 241), width=3)
    return bp.shadow(im, 6, 3, 40)


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split(" "):
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= maxw:
            cur = trial
        else:
            lines.append(cur); cur = w
    return lines + ([cur] if cur else [])


def static_screen():
    im = Image.new("RGBA", (SW, SH), (236, 229, 221, 255))
    d = ImageDraw.Draw(im)
    for y in range(0, SH, 70):  # subtle wallpaper dots
        for x in range((y // 70) % 2 * 35, SW, 70):
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(226, 218, 208))
    d.rectangle((0, 0, SW, 190), fill=(7, 94, 84))
    d.ellipse((30, 95, 110, 175), fill=(210, 220, 230))
    d.text((70, 135), "B", font=bp.font("xb", 38), fill=(7, 94, 84), anchor="mm")
    d.text((130, 115), "Boss", font=bp.font("sb", 42), fill=(255, 255, 255), anchor="lm")
    d.text((130, 158), "online", font=bp.font("sb", 26), fill=(190, 230, 220), anchor="lm")
    # keyboard
    ky = SH - 560
    d.rectangle((0, ky, SW, SH), fill=(228, 230, 236))
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    kw = (SW - 24) / 10
    for r, keys in enumerate(rows):
        x0 = 12 + (10 - len(keys)) * kw / 2
        y = ky + 110 + r * 100
        for k, ch in enumerate(keys):
            d.rounded_rectangle((x0 + k * kw + 5, y, x0 + (k + 1) * kw - 5, y + 84), 12, fill=(255, 255, 255))
            d.text((x0 + k * kw + kw / 2, y + 42), ch, font=bp.font("sb", 34), fill=INK, anchor="mm")
    y = ky + 410
    d.rounded_rectangle((12 + kw * 2 + 5, y, SW - 12 - kw * 2 - 5, y + 84), 12, fill=(255, 255, 255))
    d.text((SW / 2, y + 42), "Desi AI Keyboard", font=bp.font("sb", 26), fill=GREY, anchor="mm")
    return im, ky


STATIC, KY = static_screen()
B_IN1 = bubble("Are you coming to office tomorrow?", 440, (255, 255, 255))
B_OUT = bubble(EN_TEXT, 440, (217, 253, 211), tick=True)
B_IN2 = bubble("Sure, no problem. Approved! 👍".replace(" 👍", ""), 440, (255, 255, 255))


def chat_screen(t):
    im = STATIC.copy()
    d = ImageDraw.Draw(im)
    im.alpha_composite(B_IN1, (10, 220))
    p = prog(t, 5.6, 5.95)
    oy = 220 + B_IN1.height
    if p > 0:
        paste(im, B_OUT, SW - 20 - B_OUT.width / 2, oy + B_OUT.height / 2, 0.6 + 0.4 * back(p))
    ry = oy + B_OUT.height
    if 6.3 < t < 7.0:
        dots = Image.new("RGBA", (140, 70), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dots)
        dd.rounded_rectangle((0, 0, 139, 69), 24, fill=(255, 255, 255))
        for k in range(3):
            yy = 35 - 8 * max(0, math.sin(t * 12 - k))
            dd.ellipse((35 + k * 35 - 9, yy - 9, 35 + k * 35 + 9, yy + 9), fill=GREY)
        im.alpha_composite(dots, (30, ry + 20))
    p = prog(t, 7.0, 7.3)
    if p > 0:
        paste(im, B_IN2, 10 + B_IN2.width / 2, ry + B_IN2.height / 2, 0.6 + 0.4 * back(p))
    # input bar
    iy0, iy1 = KY - 170, KY - 20
    d.rounded_rectangle((16, iy0, SW - 120, iy1), 40, fill=(255, 255, 255))
    d.ellipse((SW - 105, iy0 + 35, SW - 25, iy0 + 115), fill=(0, 168, 132))
    d.polygon([(SW - 80, iy0 + 55), (SW - 80, iy0 + 95), (SW - 43, iy0 + 75)], fill=(255, 255, 255))
    maxw = SW - 120 - 60 - 20
    if t < 5.0:
        nw = int(len(HI_WORDS) * prog(t, 0.7, 3.3) + 0.999)
        txt = " ".join(HI_WORDS[:nw])
        f = bp.font("hi", 40)
        a = 1 - prog(t, 4.5, 4.9)
        col = tuple(int(c * a + 255 * (1 - a)) for c in INK)
        lines = wrap(txt, f, maxw) or [""]
        for i, l in enumerate(lines):
            d.text((48, iy0 + 22 + i * 52), l, font=f, fill=col)
        if t < 3.6 and int(t * 3) % 2 == 0:
            x = 50 + f.getlength(lines[-1])
            yy = iy0 + 22 + (len(lines) - 1) * 52
            d.rectangle((x, yy + 6, x + 4, yy + 50), fill=bp.SAFF)
    if 4.5 <= t < 5.6:
        f = bp.font("sb", 32)
        a = prog(t, 4.6, 5.0)
        col = tuple(int(c * a + 255 * (1 - a)) for c in INK)
        for i, l in enumerate(wrap(EN_TEXT, f, maxw)):
            d.text((48, iy0 + 28 + i * 46), l, font=f, fill=col)
    # toolbar
    cy = KY + 52
    pulse = 1 + 0.07 * math.sin(t * 10) if 3.3 < t < 4.6 else 1
    on = t >= 4.0
    cw, ch = 290 * pulse, 72 * pulse
    cx = 30 + 145
    d.rounded_rectangle((cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), 36,
                        fill=bp.SAFF if on else (255, 255, 255), outline=bp.SAFF, width=4)
    d.text((cx, cy), "अA  Translate", font=bp.font("hi", 32), fill=(255, 255, 255) if on else bp.SAFF, anchor="mm")
    for i, lab in enumerate(["Voice", "GIF", "Fonts"]):
        d.text((385 + i * 115, cy), lab, font=bp.font("sb", 28), fill=GREY, anchor="mm")
    tp = prog(t, 3.8, 4.4)
    if 0 < tp < 1:
        r = 30 + 80 * tp
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255), width=int(10 * (1 - tp)) + 1)
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=(255, 255, 255, int(170 * (1 - tp))))
    sp = prog(t, 5.3, 5.7)
    if 0 < sp < 1:
        sx, sy = SW - 65, iy0 + 75
        r = 30 + 60 * sp
        d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=(0, 168, 132), width=int(10 * (1 - sp)) + 1)
    m = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, SW - 1, SH - 1), 72, fill=255)
    im.putalpha(m)
    return im


PHONE = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pack", "assets", "phone_frame.png")).convert("RGBA")


def phone_with(screen):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.alpha_composite(screen, (bp.SCREEN[0], bp.SCREEN[1]))
    im.alpha_composite(PHONE)
    return im


# ---------- scenes ----------
TYPO = "Sir I am want leav tomorow"


def s1(t):
    im = bp.background(t)
    pop_img(im, t, 0.1, CAPS["01_hook"], W / 2, 400)
    presenter(im, t, "worried", [(0.1, 1.5), (1.8, 2.7)], 1.1, 820)
    return im


def s2(t):
    im = bp.background(t + 3)
    g = bp.glass(920, 150, 75, a=230, border=120)
    d = ImageDraw.Draw(g)
    n = int(len(TYPO) * prog(t, 0.6, 1.9)) if t < 2.1 else int(len(TYPO) * (1 - prog(t, 2.1, 2.6)))
    f = bp.font("sb", 50)
    d.text((50, 75), TYPO[:n], font=f, fill=INK, anchor="lm")
    if int(t * 3) % 2 == 0:
        x = 52 + f.getlength(TYPO[:n]); d.rectangle((x, 42, x + 5, 108), fill=bp.SAFF)
    paste(im, bp.shadow(g, 24, 12, 120), W / 2, 330)
    presenter(im, t, "worried", [(0.05, 1.0), (2.8, 3.6)], 1.0, 960)
    p = prog(t, 2.7, 3.0)
    if p > 0:
        paste(im, CAPS["02_struggle"], W / 2, 700, 1.7 - 0.7 * out3(p), p)
    return im


def s3(t):
    im = bp.background(t + 7)
    paste(im, bp.logo_sting(t), W / 2, 420)
    p = out3(prog(t, 0.9, 1.3))
    if p > 0:
        paste(im, bp.text_layer("Translate while you type", "xb", 60, grad=(bp.SAFF, bp.AMBER)), W / 2, 830 + (1 - p) * 40, 1, p)
    presenter(im, t, "excited" if t < 1.6 else "happy", [(0.05, 1.0)], 1.0, 960)
    return im


def s4(t):
    im = bp.background(t + 10)
    slide = out3(prog(t, 0.0, 0.5))
    ph = phone_with(chat_screen(t))
    ph = ph.resize((int(W * 0.8), int(H * 0.8)), Image.LANCZOS)
    im.alpha_composite(ph, (int(W * 0.1), int(320 + (1 - slide) * 1200)))
    if t < 4.5:
        pop_img(im, t, 0.2, CAPS["04_type_hindi"], W / 2, 200, 0.85)
    elif t < 7.0:
        pop_img(im, t, 4.5, CAPS["05_send_english"], W / 2, 200, 0.85)
    else:
        pop_img(im, t, 7.0, CAPS["06_approved"], W / 2, 220, 0.85)
    expr = "neutral" if t < 4.5 else ("happy" if t < 7.0 else "excited")
    avatar(im, t, expr, [(0.2, 1.4), (4.5, 5.6), (7.0, 8.4)], 905, 1690, 230, enter=0.5)
    return im


def s5(t):
    im = bp.background(t + 19)
    pop_img(im, t, 0.05, CAPS["07_features"], W / 2, 300)
    paste(im, bp.feature_pills(t - 0.3), W / 2, 1060)
    avatar(im, t, "happy", [(0.1, 1.0), (2.0, 3.0), (4.0, 5.0)], W / 2, 1700, 260, enter=0.3)
    return im


def s6(t):
    im = bp.endcard(t)
    presenter(im, t, "excited" if t < 1.5 else "happy", [(0.3, 1.3), (2.0, 3.0)], 0.5, 1580, wave=True, enter=0.6)
    return im


SCENES = [(0, 3, s1), (3, 7, s2), (7, 10, s3), (10, 19, s4), (19, 25, s5), (25, 30, s6)]


def frame(gt):
    for a, b, fn in SCENES:
        if a <= gt < b or (b == 30 and gt >= a):
            lt = gt - a
            im = fn(lt)
            # punch-in transition + light flash on each cut
            z = 1 + 0.08 * (1 - out3(prog(lt, 0, 0.25))) if a > 0 else 1 + 0.03 * prog(lt, 0, 3)
            if z > 1.001:
                zw, zh = int(W * z), int(H * z)
                im = im.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
            fl = 1 - prog(lt, 0, 0.12)
            if fl > 0 and a > 0:
                im = Image.blend(im, Image.new("RGBA", (W, H), (255, 255, 255, 255)), fl * 0.6)
            if gt > DUR - 0.4:
                im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)), prog(gt, DUR - 0.4, DUR))
            return im.convert("RGB")


if __name__ == "__main__":
    outp = sys.argv[2]
    if "--stills" in sys.argv:
        for s in sys.argv[sys.argv.index("--stills") + 1:]:
            frame(float(s)).save(f"{outp}_{s}.png")
        sys.exit()
    tmp = outp + ".tmp.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait()
    if len(sys.argv) > 3:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", sys.argv[3], "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", outp], check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, outp)

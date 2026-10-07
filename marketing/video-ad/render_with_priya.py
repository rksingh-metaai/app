"""Re-render the ad with the illustrated presenter 'Priya' in every scene.
Run from this folder: python3 render_with_priya.py out.mp4 [--audio audio.wav]"""
import math, sys, subprocess
from PIL import Image, ImageDraw
import make_video as mv
import priya

W, H = mv.W, mv.H


def put_priya(im, t, expr, talks, scale, top, cx=W / 2, wave=False, enter=0.0):
    p = mv.out(mv.prog(t, enter, enter + 0.45))
    if p <= 0:
        return
    fig = priya.pose(t, expr, talks, wave)
    fig = fig.resize((int(fig.width * scale), int(fig.height * scale)), Image.LANCZOS)
    bob = 6 * math.sin(t * 3.2)
    y = top + (1 - p) * 500 + bob
    im.alpha_composite(fig, (int(cx - fig.width / 2), int(y)))


def put_bubble(im, t, expr, talks, cx, cy, size=240, enter=0.0):
    p = mv.prog(t, enter, enter + 0.35)
    if p > 0:
        mv.paste(im, priya.bubble(priya.pose(t, expr, talks), size), cx, cy, mv.back(p))


def scene1(t):
    im = mv.BG_NAVY.copy()
    mv.pop_text(im, t, 0.10, "Mera naya boss", "xb", 92, mv.WHITE, W / 2, 300)
    mv.pop_text(im, t, 0.55, "sirf ENGLISH", "xb", 140, mv.SAFF, W / 2, 470)
    mv.pop_text(im, t, 1.05, "samajhta hai...", "xb", 92, mv.WHITE, W / 2, 630)
    if t > 1.8:
        shake = math.sin(t * 40) * 6 * (1 - mv.prog(t, 1.8, 2.6))
        mv.pop_text(im, t, 1.8, "( aur meri English? )", "sb", 60, (170, 200, 230), W / 2 + shake, 770)
    put_priya(im, t, "worried", [(0.1, 1.5), (1.8, 2.6)], 1.1, 840)
    return im


TYPO = mv.TYPO


def scene2(t):
    im = mv.BG_CREAM.copy()
    mv.pop_text(im, t, 0.05, "Bas theek-thaak", "xb", 100, mv.INK, W / 2, 260)
    mv.pop_text(im, t, 0.35, "wali English...", "xb", 100, mv.SAFF, W / 2, 390)
    d = ImageDraw.Draw(im)
    mv.rrect(d, (80, 520, 1000, 670), 75, mv.WHITE, outline=(220, 220, 225), width=3)
    n = int(len(TYPO) * mv.prog(t, 0.8, 2.1)) if t < 2.2 else int(len(TYPO) * (1 - mv.prog(t, 2.2, 2.75)))
    txt = TYPO[:n]
    f = mv.font("sb", 52)
    d.text((130, 595), txt, font=f, fill=mv.INK, anchor="lm")
    if int(t * 3) % 2 == 0:
        x = 132 + f.getlength(txt)
        d.rectangle((x, 560, x + 5, 630), fill=mv.SAFF)
    put_priya(im, t, "worried", [(0.05, 0.9)], 1.0, 960)
    p = mv.prog(t, 2.9, 3.2)
    if p > 0:
        st = mv.text_img("10 MINUTE. 1 LINE.", "xb", 76, (220, 40, 40))
        box = Image.new("RGBA", (st.width + 60, st.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), 20,
                                              fill=(255, 255, 255), outline=(220, 40, 40), width=8)
        box.alpha_composite(st, (30, 20))
        box = box.rotate(-8, expand=True, resample=Image.BICUBIC)
        mv.paste(im, box, W / 2, 830, 1.8 - 0.8 * mv.out(p), p)
    return im


def scene3(t):
    im = mv.BG_WAVE.copy()
    mv.pop_text(im, t, 0.05, "Phir maine try kiya", "xb", 84, mv.INK, W / 2, 220)
    p = mv.prog(t, 0.45, 0.95)
    if p > 0:
        mv.paste(im, mv.shadowed(mv.logo(250)), W / 2, 500, mv.back(p))
    mv.pop_text(im, t, 1.0, "Desi AI Keyboard", "xb", 104, mv.NAVY, W / 2, 750)
    mv.pop_text(im, t, 1.4, "Translate while you type", "sb", 58, mv.GREEN, W / 2, 860)
    put_priya(im, t, "excited" if t < 1.6 else "happy", [(0.05, 0.9)], 1.0, 960)
    return im


def scene4(t):
    im = mv.scene4(t)
    expr = "neutral" if t < 4.5 else ("happy" if t < 7.0 else "excited")
    put_bubble(im, t, expr, [(0.1, 1.2), (4.5, 5.5), (7.0, 8.2)], 915, 1735, 230, enter=0.4)
    return im


def scene5(t):
    im = mv.scene5(t)
    put_bubble(im, t, "happy", [(0.05, 0.9), (2.8, 3.8), (4.6, 5.4)], 150, 1760, 210, enter=0.2)
    return im


def scene6(t):
    im = mv.BG_WAVE.copy()
    p = mv.prog(t, 0.1, 0.55)
    if p > 0:
        mv.paste(im, mv.shadowed(mv.logo(220)), W / 2, 250, mv.back(p))
    mv.pop_text(im, t, 0.4, "Desi AI Keyboard", "xb", 100, mv.NAVY, W / 2, 470)
    mv.pop_text(im, t, 0.7, "Translate Instantly.", "xb", 76, mv.SAFF, W / 2, 610)
    mv.pop_text(im, t, 0.9, "Chat Globally.", "xb", 76, mv.GREEN, W / 2, 705)
    p = mv.prog(t, 1.4, 1.8)
    if p > 0:
        btn = Image.new("RGBA", (760, 170), (0, 0, 0, 0))
        bd = ImageDraw.Draw(btn)
        mv.rrect(bd, (0, 0, 759, 169), 85, mv.NAVY)
        bd.text((380, 62), "Download FREE", font=mv.font("xb", 62), fill=mv.WHITE, anchor="mm")
        bd.text((380, 125), "on Google Play", font=mv.font("sb", 34), fill=(190, 210, 235), anchor="mm")
        pulse = 1 + 0.035 * math.sin((t - 1.8) * 6) if t > 1.8 else 1
        mv.paste(im, mv.shadowed(btn, 30, 12, 70), W / 2, 900, mv.back(p) * pulse)
    mv.pop_text(im, t, 2.0, "Proudly made for India", "sb", 50, mv.INK, W / 2, 1060)
    put_priya(im, t, "excited" if t < 1.5 else "happy", [(0.4, 1.4), (2.0, 2.8)], 0.85, 1080,
              wave=True, enter=0.2)
    return im


mv.SCENES = [(0, 3, scene1), (3, 7, scene2), (7, 10, scene3), (10, 19, scene4), (19, 25, scene5), (25, 30, scene6)]

if __name__ == "__main__":
    outp = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] != "--audio":
        for s in sys.argv[2:]:
            mv.frame(float(s)).save(f"{outp}_{s}.png")
        sys.exit()
    tmp = outp + ".noaudio.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(mv.FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(mv.DUR * mv.FPS)):
        ff.stdin.write(mv.frame(i / mv.FPS).tobytes())
    ff.stdin.close(); ff.wait()
    audio = sys.argv[3] if len(sys.argv) > 3 else None
    if audio:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", audio, "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", outp], check=True)
        subprocess.run(["rm", "-f", tmp])

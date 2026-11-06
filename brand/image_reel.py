"""Turn one still image into a short branded vertical reel (Ken Burns + text cards).
usage: image_reel.py SRC LOGO OUT spec.json
spec: {"tag": str, "cards": [[line1, line2, color("w"|"r")], ...], "end": [line, line], "seconds": float}
"""
import sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SRC, LOGO, OUT, SPEC = sys.argv[1:5]
spec = json.load(open(SPEC))
W, H, FPS = 1080, 1920, 30
RED = (165, 29, 29); RED2 = (226, 72, 72); DARK = (17, 17, 19); WHITE = (255, 255, 255); PINK = (245, 190, 180)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FBC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
F = lambda p, s: ImageFont.truetype(p, s)
src = Image.open(SRC).convert('RGB')
logo = Image.open(LOGO).convert('RGBA')
ease = lambda t: t * t * (3 - 2 * t)
clamp = lambda x: max(0.0, min(1.0, x))

# base: fill 9:16 by cropping center of source (scaled up a bit for zoom headroom)
sw, sh = src.size
scale = max(W / sw, H / sh) * 1.12
base = src.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
BW, BH = base.size

TOTAL = spec.get('seconds', 10.0)
cards = spec['cards']
END = 2.4
seg = (TOTAL - END) / len(cards)


GRAD = Image.new('RGBA', (W, H), (0, 0, 0, 0))
_gd = ImageDraw.Draw(GRAD)
for _y in range(0, 700, 4):
    _gd.rectangle((0, _y, W, _y + 4), fill=DARK + (int(210 * (1 - _y / 700) ** 1.2),))


def frame(t):
    z = 1.0 + 0.10 * (t / TOTAL)
    cw, ch = W / z * (BW / (W * 1.12)) * 1.0, H / z * (BH / (H * 1.12))
    cw, ch = min(BW, W * (BW / W) / 1.12 / z * 1.12 / (BW / W) * (BW / W)), None
    # simpler: crop window of size (W*1.12/z, H*1.12/z) in base coords scaled
    k = 1.12 / z
    ww, hh = BW / 1.12 * k, BH / 1.12 * k
    x0 = (BW - ww) / 2 + 30 * (t / TOTAL); y0 = (BH - hh) / 2
    im = base.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + ww, y0 + hh)).convert('RGBA')
    # top gradient (alpha-composited; drawing RGBA fills directly on an RGBA image replaces pixels)
    im.alpha_composite(GRAD)
    d = ImageDraw.Draw(im, 'RGBA')
    l = logo.resize((120, 120), Image.LANCZOS)
    im.alpha_composite(l, (W - 175, 90))
    f = F(FB, 30); tag = spec['tag']; tw = d.textlength(tag, font=f); h = 58
    d.rounded_rectangle((60, 100, 60 + tw + 66, 100 + h), radius=29, fill=RED)
    d.ellipse((82, 100 + h // 2 - 7, 96, 100 + h // 2 + 7), fill=WHITE)
    d.text((108, 112), tag, font=f, fill=WHITE)
    if t < TOTAL - END:
        i = min(len(cards) - 1, int(t // seg)); lt = (t - i * seg) / seg
        a = clamp(lt * 5) * clamp((1 - lt) * 6) if i < len(cards) - 1 else clamp(lt * 5)
        l1, l2, col = cards[i]
        dy = int(30 * (1 - ease(clamp(lt * 5))))
        c1 = WHITE; c2 = RED2 if col == 'r' else PINK
        d.text((60, 210 + dy), l1, font=F(FB, 76), fill=c1 + (int(255 * a),))
        if l2:
            d.text((60, 305 + dy), l2, font=F(FBC, 58), fill=c2 + (int(255 * a),))
        im2 = im
    else:
        a = clamp((t - (TOTAL - END)) * 3)
        ov = Image.new('RGBA', (W, H), DARK + (int(225 * a),))
        im.alpha_composite(ov)
        d = ImageDraw.Draw(im, 'RGBA')
        s = 300; l = logo.resize((s, s), Image.LANCZOS)
        l.putalpha(l.getchannel('A').point(lambda v: int(v * a)))
        im.alpha_composite(l, ((W - s) // 2, 640))
        y = 1020
        for txt, f, col in [(spec['end'][0], F(FBC, 52), PINK), (spec['end'][1], F(FB, 78), WHITE)]:
            tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, y), txt, font=f, fill=col + (int(255 * a),)); y += f.size + 40
    return im.convert('RGB')


ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                       '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                       '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(int(TOTAL * FPS)):
    ff.stdin.write(frame(i / FPS).tobytes())
ff.stdin.close(); ff.wait()
print('ok')

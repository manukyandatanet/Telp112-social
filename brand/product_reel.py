"""Product photos (white background) -> branded 1080x1920 "product of the day" reel.
usage: product_reel.py OUT LOGO spec.json
spec: {"tag": str, "photos": [path,...], "cards": [[line1, line2], ...], "end": [line, line], "seconds": float}
Photos cycle with crossfade inside a white rounded card; text cards change above it.
"""
import sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont

OUT, LOGO, SPEC = sys.argv[1:4]
spec = json.load(open(SPEC))
W, H, FPS = 1080, 1920, 30
RED = (165, 29, 29); RED2 = (226, 72, 72); DARK = (17, 17, 19); WHITE = (255, 255, 255); PINK = (245, 190, 180)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FBC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
F = lambda p, s: ImageFont.truetype(p, s)
ease = lambda t: t * t * (3 - 2 * t)
clamp = lambda x: max(0.0, min(1.0, x))
logo = Image.open(LOGO).convert('RGBA')
TOTAL = spec.get('seconds', 12.0); END = 2.6
cards = spec['cards']; seg = (TOTAL - END) / len(cards)
CARD = (90, 560, 990, 1460)  # white photo card
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
photos = []
for p in spec['photos']:
    im = Image.open(p).convert('RGB'); s = min((CW - 60) / im.width, (CH - 60) / im.height)
    photos.append(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))
pseg = (TOTAL - END) / len(photos)

bg = Image.new('RGBA', (W, H), DARK + (255,)); d = ImageDraw.Draw(bg)
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
for y in range(1100, H):  # subtle red glow at bottom
    gd.line((0, y, W, y), fill=RED + (int(90 * clamp((y - 1100) / 820)),))
bg.alpha_composite(glow); d = ImageDraw.Draw(bg)
l = logo.resize((120, 120), Image.LANCZOS); bg.alpha_composite(l, (W - 175, 90))
f = F(FB, 30); tag = spec['tag']; tw = d.textlength(tag, font=f)
d.rounded_rectangle((60, 100, 60 + tw + 66, 158), radius=29, fill=RED)
d.ellipse((82, 122, 96, 136), fill=WHITE); d.text((108, 112), tag, font=f, fill=WHITE)
d.rounded_rectangle(CARD, radius=40, fill=WHITE)
f3 = F(FBC, 36); s = 'Անվճար խորհրդատվություն'; d.text(((W - d.textlength(s, font=f3)) / 2, 1560), s, font=f3, fill=PINK)
f2 = F(FB, 56); ph = '+374 96 112141'; d.text(((W - d.textlength(ph, font=f2)) / 2, 1615), ph, font=f2, fill=WHITE)


def photo_at(k, lt):
    p = photos[k]; z = 1.0 + 0.05 * lt
    q = p.resize((int(p.width * z), int(p.height * z)), Image.LANCZOS)
    c = Image.new('RGB', (CW, CH), WHITE); c.paste(q, ((CW - q.width) // 2, (CH - q.height) // 2)); return c


def frame(t):
    im = bg.copy()
    tt = min(t, TOTAL - END - 0.001)
    k = min(len(photos) - 1, int(tt // pseg)); lt = (tt - k * pseg) / pseg
    c = photo_at(k, lt)
    if k > 0 and lt < 0.12:
        c = Image.blend(photo_at(k - 1, 1.0), c, ease(lt / 0.12))
    m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, CW, CH), radius=40, fill=255)
    im.paste(c, CARD[:2], m)
    d = ImageDraw.Draw(im, 'RGBA')
    if t < TOTAL - END:
        i = min(len(cards) - 1, int(t // seg)); lt = (t - i * seg) / seg
        a = (1.0 if i == 0 and t < 0.2 else clamp(lt * 6)) * (clamp((1 - lt) * 7) if i < len(cards) - 1 else 1)
        dy = int(26 * (1 - ease(clamp(lt * 6)))) if i > 0 else 0
        l1, l2 = cards[i]
        d.text((60, 225 + dy), l1, font=F(FB, 70), fill=WHITE + (int(255 * a),))
        if l2: d.text((60, 320 + dy), l2, font=F(FBC, 54), fill=RED2 + (int(255 * a),))
    else:
        a = clamp((t - (TOTAL - END)) * 3)
        im.alpha_composite(Image.new('RGBA', (W, H), DARK + (int(230 * a),)))
        d = ImageDraw.Draw(im, 'RGBA')
        s = 300; l = logo.resize((s, s), Image.LANCZOS)
        l.putalpha(l.getchannel('A').point(lambda v: int(v * a)))
        im.alpha_composite(l, ((W - s) // 2, 600))
        y = 990
        for txt, f, col in [(spec['end'][0], F(FBC, 44), PINK), (spec['end'][1], F(FB, 78), WHITE)]:
            tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, y), txt, font=f, fill=col + (int(255 * a),)); y += f.size + 40
    return im.convert('RGB')


ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(int(TOTAL * FPS)):
    ff.stdin.write(frame(n / FPS).tobytes())
ff.stdin.close(); ff.wait(); print('ok', TOTAL)

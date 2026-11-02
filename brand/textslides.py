import sys, os, json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps, ImageFilter

SPEC, LOGO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1350
RED = (165, 29, 29); RED2 = (226, 72, 72); DARK = (17, 17, 19); WHITE = (255, 255, 255)
GREY = (190, 190, 196); PINK = (235, 170, 170)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FBC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F = lambda p, s: ImageFont.truetype(p, s)
logo = Image.open(LOGO).convert('RGBA')
spec = json.load(open(SPEC))
TOTAL = len(spec['slides'])


def wrap(d, text, f, maxw):
    out = []
    for para in text.split('\n'):
        cur = ''
        for w in para.split():
            t = (cur + ' ' + w).strip()
            if d.textlength(t, font=f) <= maxw: cur = t
            else: out.append(cur); cur = w
        out.append(cur)
    return out


def photo_bg(path, bright=1.3):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    im = ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.45))
    im = ImageOps.autocontrast(im, cutoff=1)
    return ImageEnhance.Brightness(im).enhance(bright)


def grad(im, start, amax=240):
    g = Image.new('L', (1, H))
    for y in range(H):
        g.putpixel((0, y), int(amax * min(1, max(0, (y - start) / (H - start)) ** 0.9)))
    return Image.composite(Image.new('RGB', (W, H), DARK), im, g.resize((W, H)))


def chrome(im, d, n, logo_size=110):
    l = logo.resize((logo_size, logo_size), Image.LANCZOS)
    im.paste(l, (60, 60), l)
    f = F(FB, 26); s = f'{n:02d} / {TOTAL:02d}'
    tw = d.textlength(s, font=f)
    d.rounded_rectangle((W - 84 - tw, 72, W - 36, 122), radius=25, fill=(40, 40, 44))
    d.text((W - 60 - tw, 82), s, font=f, fill=WHITE)
    d.text((60, H - 62), 'TELP112  ·  Engineering & Safety Systems', font=F(FR, 24), fill=(150, 150, 156))


def pill(d, x, y, text, f, fill=RED):
    tw = d.textlength(text, font=f); h = f.size + 26
    d.rounded_rectangle((x, y, x + tw + 64, y + h), radius=h // 2, fill=fill)
    d.ellipse((x + 22, y + h // 2 - 7, x + 36, y + h // 2 + 7), fill=WHITE)
    d.text((x + 46, y + 12), text, font=f, fill=WHITE)
    return y + h


for n, s in enumerate(spec['slides'], start=1):
    kind = s['kind']
    if kind == 'cover':
        im = grad(photo_bg(s['photo']), 480) if s.get('photo') else Image.new('RGB', (W, H), DARK)
        d = ImageDraw.Draw(im)
        chrome(im, d, n, 150)
        y = pill(d, 60, 760, s['tag'], F(FB, 30))
        y += 24
        for line in wrap(d, s['title'], F(FB, 92), W - 120):
            d.text((56, y), line, font=F(FB, 92), fill=WHITE); y += 108
        y += 10
        for line in wrap(d, s['sub'], F(FBC, 44), W - 120):
            d.text((60, y), line, font=F(FBC, 44), fill=PINK); y += 56
    elif kind == 'step':
        if s.get('photo'):
            im = grad(photo_bg(s['photo'], 1.25), 300, 250)
        else:
            im = Image.new('RGB', (W, H), DARK)
            dd = ImageDraw.Draw(im)
            for i in range(0, W + H, 60):
                dd.line((i, 0, i - H, H), fill=(24, 24, 27), width=2)
        d = ImageDraw.Draw(im)
        chrome(im, d, n)
        y = 640
        if s.get('num'):
            d.text((54, y - 250), s['num'], font=F(FB, 240), fill=RED2)
        if s.get('tag'):
            y = pill(d, 60, y, s['tag'], F(FB, 28), fill=tuple(s.get('tagcolor', RED))) + 26
        for line in wrap(d, s['title'], F(FB, 70), W - 120):
            d.text((58, y), line, font=F(FB, 70), fill=WHITE); y += 84
        y += 18
        d.rectangle((60, y, 140, y + 6), fill=RED); y += 34
        for line in wrap(d, s['text'], F(FBC, 44), W - 120):
            d.text((60, y), line, font=F(FBC, 44), fill=GREY); y += 58
    elif kind == 'cta':
        im = Image.new('RGB', (W, H), DARK)
        d = ImageDraw.Draw(im)
        chrome(im, d, n, 0) if False else None
        f = F(FB, 26); st = f'{n:02d} / {TOTAL:02d}'
        tw = d.textlength(st, font=f)
        d.rounded_rectangle((W - 84 - tw, 72, W - 36, 122), radius=25, fill=(40, 40, 44))
        d.text((W - 60 - tw, 82), st, font=f, fill=WHITE)
        l = logo.resize((260, 260), Image.LANCZOS); im.paste(l, ((W - 260) // 2, 170), l)
        y = 500
        for line in wrap(d, s['title'], F(FB, 56), W - 160):
            tw = d.textlength(line, font=F(FB, 56)); d.text(((W - tw) / 2, y), line, font=F(FB, 56), fill=WHITE); y += 74
        y += 40
        for line in s['lines']:
            tw = d.textlength(line, font=F(FBC, 42)); d.text(((W - tw) / 2, y), line, font=F(FBC, 42), fill=(225, 225, 225)); y += 58
        y += 60
        btn = 'Անվճար խորհրդատվություն'; f = F(FB, 44); tw = d.textlength(btn, font=f)
        d.rounded_rectangle(((W - tw) / 2 - 50, y, (W + tw) / 2 + 50, y + 100), radius=50, fill=RED)
        d.text(((W - tw) / 2, y + 24), btn, font=f, fill=WHITE); y += 150
        for line, sz in [('+374 96 112141', 52), ('www.telp112.am', 36)]:
            f = F(FB, sz); tw = d.textlength(line, font=f); d.text(((W - tw) / 2, y), line, font=f, fill=WHITE); y += sz + 26
    im.save(os.path.join(OUT, f"{spec['prefix']}_{n:02d}.jpg"), quality=92)
print('ok', TOTAL)

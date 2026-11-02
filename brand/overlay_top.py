import sys
from PIL import Image, ImageDraw, ImageFont

SRC, LOGO, OUT, TAG, L1, L2, SUB = sys.argv[1:8]
W, H = 1080, 1350
RED = (165, 29, 29); DARK = (17, 17, 19); WHITE = (255, 255, 255); PINK = (245, 190, 180)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FBC = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F = lambda p, s: ImageFont.truetype(p, s)

im = Image.open(SRC).convert('RGB').resize((W, H), Image.LANCZOS)
g = Image.new('L', (1, H))
for y in range(H):
    top = max(0, 1 - y / 520) ** 1.1 * 225
    bot = max(0, (y - 1180) / (H - 1180)) * 230
    g.putpixel((0, y), int(max(top, bot)))
im = Image.composite(Image.new('RGB', (W, H), DARK), im, g.resize((W, H)))
d = ImageDraw.Draw(im)
l = Image.open(LOGO).convert('RGBA').resize((110, 110), Image.LANCZOS)
im.paste(l, (W - 170, 50), l)
f = F(FB, 28); tw = d.textlength(TAG, font=f); h = 54
d.rounded_rectangle((60, 60, 60 + tw + 64, 60 + h), radius=27, fill=RED)
d.ellipse((82, 60 + h // 2 - 7, 96, 60 + h // 2 + 7), fill=WHITE)
d.text((106, 71), TAG, font=f, fill=WHITE)
d.text((58, 145), L1, font=F(FB, 68), fill=WHITE)
d.text((58, 225), L2, font=F(FB, 68), fill=WHITE)
d.text((60, 318), SUB, font=F(FBC, 42), fill=PINK)
d.text((60, H - 70), 'TELP112  ·  +374 96 112141', font=F(FB, 32), fill=WHITE)
s = 'www.telp112.am'; f = F(FR, 28)
d.text((W - 60 - d.textlength(s, font=f), H - 66), s, font=f, fill=(210, 210, 210))
im.save(OUT, quality=92)
print('ok')

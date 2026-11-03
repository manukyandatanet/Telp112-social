"""Carousel slides (1080x1350) -> branded 1080x1920 reel with progress bar.
usage: slides_reel.py OUT TAG HEADLINE SLIDE1.jpg SLIDE2.jpg ...
"""
import sys, subprocess
from PIL import Image, ImageDraw, ImageFont
W,H,FPS=1080,1920,30
RED=(165,29,29);RED2=(226,72,72);DARK=(17,17,19);WHITE=(255,255,255);PINK=(245,190,180)
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';FBC='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
F=lambda p,s:ImageFont.truetype(p,s)
OUT,TAG,HEAD=sys.argv[1:4]
slides=[Image.open(f).convert('RGB') for f in sys.argv[4:]]
durs=[2.6]*(len(slides)-1)+[3.2]; XF=0.35
starts=[sum(durs[:i]) for i in range(len(durs))]; TOTAL=sum(durs)
bg=Image.new('RGBA',(W,H),DARK+(255,)); d=ImageDraw.Draw(bg)
# top header
f=F(FB,32); tag=TAG; tw=d.textlength(tag,font=f)
d.rounded_rectangle((60,110,60+tw+70,170),radius=30,fill=RED); d.ellipse((84,133,98,147),fill=WHITE); d.text((110,121),tag,font=f,fill=WHITE)
d.text((60,195),HEAD,font=F(FB,52),fill=WHITE)
# bottom
ph='+374 96 112141'; f2=F(FB,50); d.text(((W-d.textlength(ph,font=f2))/2,1730),ph,font=f2,fill=WHITE)
f3=F(FBC,34); s='Անվճար խորհրդատվություն'; d.text(((W-d.textlength(s,font=f3))/2,1675),s,font=f3,fill=PINK)
Y0=290
def frame(t):
    im=bg.copy(); dd=ImageDraw.Draw(im)
    i=max(k for k in range(len(starts)) if starts[k]<=t)
    def sl(k,tt):
        z=1.0+0.04*min(1,tt/durs[k]); w,h=int(1080*z),int(1350*z)
        x=slides[k].resize((w,h),Image.LANCZOS).crop(((w-1080)//2,(h-1350)//2,(w-1080)//2+1080,(h-1350)//2+1350))
        return x
    cur=sl(i,t-starts[i])
    if i>0 and t-starts[i]<XF:
        prev=sl(i-1,durs[i-1]); a=(t-starts[i])/XF; cur=Image.blend(prev,cur,a*a*(3-2*a))
    im.paste(cur,(0,Y0))
    # progress bar
    n=len(slides); gw=(W-120-(n-1)*10)/n
    for k in range(n):
        x0=60+k*(gw+10); dd.rounded_rectangle((x0,1655-25,x0+gw,1655-17),radius=4,fill=(70,70,75))
        p=1 if k<i else (min(1,(t-starts[i])/durs[i]) if k==i else 0)
        if p>0: dd.rounded_rectangle((x0,1630,x0+max(8,gw*p),1638),radius=4,fill=RED2)
    return im.convert('RGB')
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
 '-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
for k in range(int(TOTAL*FPS)): ff.stdin.write(frame(k/FPS).tobytes())
ff.stdin.close(); ff.wait(); print('ok',TOTAL)

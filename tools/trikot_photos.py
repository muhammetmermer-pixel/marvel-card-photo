"""Trikot-Fotos (Stand 24.10.2026, an 2 Curry-Trikots getestet):
Freistellung per Lab-Schwellen (Boden beige b>=135/L>=170; Trikot blau, gelbe Borte b>168, weisse Seitenstreifen b<135),
Clip auf Trikotkoerper (+-18 px bei 1000 px), dann Komposition 1600x1600 weiss, Schatten rechts/unten.
Aufruf: python3 tools/trikot_photos.py OUTDIR SKU front.jpg back.jpg sig.jpg num.jpg label.jpg neck.jpg
Ausgabe: SKU_01 (Vorderseite) .. SKU_06; Kontrollmontage vor Upload ansehen (Reste vom Boden am Saum)."""
import sys
import cv2, numpy as np, os
def cutout(path,out):
    img=cv2.imread(path);h,w=img.shape[:2]
    s=1000/max(h,w);sm=cv2.resize(img,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    lab=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB)
    L,a,b=[lab[...,i].astype(int) for i in range(3)]
    fg=((L<170)|(b<135)|(a<115)|(b>168)).astype(np.uint8)
    blue=((L<150)&(b<125)).astype(np.uint8)
    blue=cv2.morphologyEx(blue,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
    ys,xs=np.where(blue>0);x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
    nb,lb,stb,_=cv2.connectedComponentsWithStats(blue);kb=1+np.argmax(stb[1:,4]);blue=(lb==kb).astype(np.uint8)
    clip=cv2.dilate(blue,np.ones((1,37),np.uint8))
    clip=cv2.dilate(clip,np.ones((13,1),np.uint8))
    fg=fg*clip
    fg=cv2.GaussianBlur(fg*255,(5,5),0)>127
    fg=fg.astype(np.uint8)
    fg=cv2.morphologyEx(fg,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    fg=cv2.morphologyEx(fg,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
    n,lbl,st,_=cv2.connectedComponentsWithStats(fg)
    k=1+np.argmax(st[1:,4]);m=(lbl==k).astype(np.uint8)
    inv=1-m;n,lbl,st,_=cv2.connectedComponentsWithStats(inv)
    for i in range(1,n):
        x,y,ww,hh,ar=st[i]
        if x>0 and y>0 and x+ww<m.shape[1] and y+hh<m.shape[0]: m[lbl==i]=1
    top=m.copy(); top[int(m.shape[0]*0.3):]=0
    cl=cv2.morphologyEx(m,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(45,45)))
    cl[int(m.shape[0]*0.3):]=m[int(m.shape[0]*0.3):]
    m=cl
    m=cv2.resize(m*255,(w,h),interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(out,m)

import cv2, numpy as np, os
from PIL import Image, ImageFilter, ImageOps
def jersey(src,mask,out):
    im=Image.open(src).convert('RGB'); m=Image.open(mask).convert('L')
    bb=m.point(lambda v:255 if v>127 else 0).getbbox(); im=im.crop(bb); m=m.crop(bb)
    m=m.filter(ImageFilter.GaussianBlur(1.2))
    S=1600; H=int(S*0.86); sc=H/im.height
    if im.width*sc>S*0.80: sc=S*0.80/im.width
    w,h=int(im.width*sc),int(im.height*sc)
    im=im.resize((w,h),Image.LANCZOS); m=m.resize((w,h),Image.LANCZOS)
    m=m.point(lambda v:0 if v<20 else (255 if v>235 else v))
    cv=Image.new('RGB',(S,S),'white')
    x=(S-w)//2-8; y=(S-h)//2-8
    sh=Image.new('L',(S,S),0); sh.paste(m,(x+22,y+26)); sh=sh.filter(ImageFilter.GaussianBlur(22)).point(lambda v:int(v*0.42))
    cv.paste((0,0,0),(0,0),sh)
    cv.paste(im,(x,y),m)
    cv.save(out,quality=95,subsampling=0)
def close(src,out,yoff=0.5):
    im=Image.open(src).convert('RGB'); w,h=im.size
    y=int((h-w)*yoff); im=im.crop((0,y,w,y+w)).resize((1600,1600),Image.LANCZOS); im.save(out,quality=95,subsampling=0)

if __name__=='__main__':
    out,sku,front,back,sig,num,lab,neck=sys.argv[1:9]
    os.makedirs(out,exist_ok=True); R=out
    for src,name,o in [(front,'f','01'),(back,'b','02')]:
        cutout(src,f'/tmp/{sku}_{name}_mask.png'); jersey(src,f'/tmp/{sku}_{name}_mask.png',f'{R}/{sku}_{o}.jpg')
    for i,(s,y) in enumerate([(sig,.72),(num,.55),(lab,.8),(neck,.3)],3): close(s,f'{R}/{sku}_0{i}.jpg',y)

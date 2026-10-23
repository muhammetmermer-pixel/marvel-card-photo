#!/usr/bin/env python3
"""Freistellen + Ausrichten + weisser Hintergrund + Schatten + 4 Eckzooms.
Aufruf: cardshots.py INPUT.jpg OUTPREFIX  -> OUTPREFIX_front.jpg (1600x1600)
        optional: --corners schreibt OUTPREFIX_c1..c4.jpg"""
import sys, cv2, numpy as np
S=1600
def find_card(img):
    h,w=img.shape[:2]
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # nur der helle Papierbereich oben (unterer dunkler Balken/Stoff ausschliessen)
    dark=np.where(g.mean(axis=1)<120)[0]
    dark=dark[dark>h*0.4]
    ymax=int(dark.min())-30 if len(dark) else h
    top=np.where(g.mean(axis=1)<120)[0];top=top[top<h*0.2]
    ymin=int(top.max())+30 if len(top) else 0
    reg=img[ymin:ymax]
    gb=cv2.GaussianBlur(cv2.cvtColor(reg,cv2.COLOR_BGR2GRAY),(0,0),2).astype(np.float32)
    H0,W0=gb.shape
    yy,xx=np.mgrid[0:H0,0:W0]
    edge=((xx<W0*0.12)|(xx>W0*0.88)|(yy<H0*0.12))
    A=np.c_[xx[edge],yy[edge],np.ones(edge.sum())].astype(np.float64)
    co=np.linalg.lstsq(A,gb[edge].astype(np.float64),rcond=None)[0]
    bg=(co[0]*xx+co[1]*yy+co[2]).astype(np.float32)
    d=np.abs(gb-bg)
    hsv=cv2.cvtColor(reg,cv2.COLOR_BGR2HSV)
    sat=cv2.GaussianBlur(hsv[:,:,1],(0,0),3).astype(np.float32)
    H,W=d.shape;good=[]
    for th in (16,12,9,7):
        m=((d>th)|(sat>70)).astype(np.uint8)*255
        m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
        m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
        cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        good=[]
        for c in cs:
            a=cv2.contourArea(c)
            if a<300000: continue
            x,y,bw,bh=cv2.boundingRect(c)
            if x<5 or y<5 or x+bw>W-5 or y+bh>H-5: continue
            r=cv2.minAreaRect(c);rw,rh=r[1]
            if rw*rh==0 or cv2.contourArea(cv2.convexHull(c))/(rw*rh)<0.88: continue
            if not (0.6<min(rw,rh)/max(rw,rh)<0.8): continue
            good.append((a,r))
        if good: break
    r=max(good,key=lambda t:t[0])[1]
    return ((r[0][0],r[0][1]+ymin),r[1],r[2])
def find_back(img):
    h,w=img.shape[:2]
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    dark=np.where(g.mean(axis=1)<120)[0];dark=dark[dark>h*0.4]
    ymax=int(dark.min())-30 if len(dark) else h
    reg=img[:ymax]
    sat=cv2.GaussianBlur(cv2.cvtColor(reg,cv2.COLOR_BGR2HSV)[:,:,1],(0,0),2)
    m=(sat>24).astype(np.uint8)*255
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(cs,key=cv2.contourArea)
    return cv2.minAreaRect(c)
def warp(img,rect):
    (cx,cy),(rw,rh),ang=rect
    box=cv2.boxPoints(rect)
    # Ecken ordnen: tl,tr,br,bl
    s=box.sum(1); dd=np.diff(box,axis=1).ravel()
    tl=box[s.argmin()];br=box[s.argmax()];tr=box[dd.argmin()];bl=box[dd.argmax()]
    W=int(round(np.linalg.norm(tr-tl)));H=int(round(np.linalg.norm(bl-tl)))
    dst=np.array([[0,0],[W-1,0],[W-1,H-1],[0,H-1]],np.float32)
    M=cv2.getPerspectiveTransform(np.array([tl,tr,br,bl],np.float32),dst)
    return cv2.warpPerspective(img,M,(W,H),flags=cv2.INTER_CUBIC)
def compose(card,frac=0.89):
    """Referenz des Nutzers (Okt 2026): Karte 89% der Hoehe, exakt mittig, weisser Hintergrund,
    Schatten nur rechts/unten: Versatz (97,155) px, sigma 28, Staerke 0.265 (Grau ~188), vom Bildrand beschnitten."""
    t=3  # Randsaum der Freistellung abschneiden
    card=card[t:-t,t:-t]
    h,w=card.shape[:2]
    sc=min(S*frac/w,S*frac/h)
    c=cv2.resize(card,(int(w*sc),int(h*sc)),interpolation=cv2.INTER_AREA)
    ch,cw=c.shape[:2]
    can=np.full((S,S,3),255,np.uint8)
    x=(S-cw)//2;y=(S-ch)//2
    dx,dy=97,155
    sh=np.zeros((S,S),np.float32)
    sh[max(0,y+dy):min(S,y+ch+dy),max(0,x+dx):min(S,x+cw+dx)]=1
    sh=cv2.GaussianBlur(sh,(0,0),28)*0.265
    can=(can*(1-sh[...,None])).astype(np.uint8)
    can[y:y+ch,x:x+cw]=c
    return can

def corners(card,n=0.40):
    m=int(card.shape[1]*0.06);card=cv2.copyMakeBorder(card,m,m,m,m,cv2.BORDER_CONSTANT,value=(255,255,255))
    h,w=card.shape[:2];a=int(w*n*1.0);b=int(w*n*1.0)
    out=[]
    for ys,xs in [(slice(0,b),slice(0,a)),(slice(0,b),slice(w-a,w)),(slice(h-b,h),slice(w-a,w)),(slice(h-b,h),slice(0,a))]:
        piece=card[ys,xs]
        can=np.full((S,S,3),255,np.uint8)
        # Ecke mit etwas weissem Rand zeigen
        p=cv2.resize(piece,(int(S*0.8),int(S*0.8)),interpolation=cv2.INTER_CUBIC)
        pad=(S-p.shape[0])//2
        can[pad:pad+p.shape[0],pad:pad+p.shape[1]]=p
        out.append(can)
    return out
if __name__=="__main__":
    src,pre=sys.argv[1],sys.argv[2]
    img=cv2.imread(src)
    card=warp(img,find_back(img) if '--back' in sys.argv else find_card(img))
    if card.shape[1]>card.shape[0]:
        card=cv2.rotate(card,cv2.ROTATE_90_CLOCKWISE) if False else card  # Querformat bleibt
    # Hochformat-Karten: Ausgabe immer in 'aufrechter' Lage der Aufnahme
    cv2.imwrite(pre+"_front.jpg",compose(card),[cv2.IMWRITE_JPEG_QUALITY,93])
    if "--corners" in sys.argv:
        for i,cc in enumerate(corners(card),1): cv2.imwrite(f"{pre}_c{i}.jpg",cc,[cv2.IMWRITE_JPEG_QUALITY,93])

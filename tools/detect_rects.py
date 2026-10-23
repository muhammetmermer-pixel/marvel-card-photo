#!/usr/bin/env python3
"""Kartenrechteck je Originalfoto finden (Aufnahmen: Karte auf hellem Papier, Kamera fest).
Aufruf: python3 tools/detect_rects.py <foto> ...   -> JSON {foto: [x0,y0,x1,y1] | null}
Als Modul: detect(path) -> [x0,y0,x1,y1] oder None. Verfahren: Hintergrundfarbe aus den oberen Zeilen der Region,
Abstand im Lab-Raum, groesste Komponente mit Seitenverhaeltnis 0.66..0.76 (Karte 63x88). Weisse Rueckseiten auf
weissem Papier liefern oft nur ein Teilstueck -> dann None (Aufrufer nimmt Standardrechteck + Kontrolle)."""
import sys,json,cv2,numpy as np
def detect(path):
    for roi in((.40,.08,.95,.60),(.12,.05,.95,.72)):
        r=_detect(path,roi)
        if r:return r
    return None
def _detect(path,roi):
    im=cv2.imread(path);h,w=im.shape[:2]
    x0,y0,x1,y1=int(roi[0]*w),int(roi[1]*h),int(roi[2]*w),int(roi[3]*h)
    lab=cv2.cvtColor(cv2.GaussianBlur(im[y0:y1,x0:x1],(7,7),0),cv2.COLOR_BGR2LAB).astype(float)
    d=np.linalg.norm(lab-np.median(lab[:40].reshape(-1,3),0),axis=2);best=None
    for th in(22,16,12):
        m=(d>th).astype(np.uint8)
        m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((9,9),np.uint8))
        n,_,st,_=cv2.connectedComponentsWithStats(m)
        for i in range(1,n):
            x,y,ww,hh,a=[int(v) for v in st[i]]
            if (x<=2 or y+hh>=y1-y0-2) and roi[0]<.3: continue
            if a>20000 and .66<ww/hh<.76 and a>.6*ww*hh and (best is None or a>best[0]):best=(a,[x0+x,y0+y,x0+x+ww,y0+y+hh])
        if best:break
    return best[1] if best else None
DEFAULT=[750,326,1244,1009]   # Standardlage der Karte in 1512x2016-Aufnahmen (Median aus Lauf 23.10.2026)
def main(cfgp,overlay):
    """Schreibt rf/rb in cards.json (erkannt oder DEFAULT) und optional eine Kontrollmontage aller Rechtecke."""
    cfg=json.load(open(cfgp));U=f"{cfg['uploads']}/{cfg.get('prefix','IMG_')}%s.{cfg.get('ext','jpeg')}";tiles=[];dflt=[]
    for c in cfg['cards']:
        for k,key in(('front','rf'),('back','rb')):
            src=U%c[k];r=detect(src);
            if r is None:r=DEFAULT;dflt.append(c['sku']+key)
            c[key]=','.join(map(str,r))
            if overlay:
                im=cv2.imread(src);cv2.rectangle(im,tuple(r[:2]),tuple(r[2:]),(0,0,255),6)
                t=cv2.resize(im[250:1150,550:1450],(180,180));cv2.putText(t,c['sku']+key[1],(3,18),0,.6,(255,0,0),2);tiles.append(t)
    json.dump(cfg,open(cfgp,'w'),ensure_ascii=False,indent=1)
    if overlay:
        while len(tiles)%14:tiles.append(np.zeros((180,180,3),np.uint8))
        cv2.imwrite(overlay,np.vstack([np.hstack(tiles[i:i+14]) for i in range(0,len(tiles),14)]))
    print('Standardrechteck (Erkennung fehlgeschlagen):',dflt or 'keine','| Kontrollmontage:',overlay,'(PFLICHT: ansehen, rotes Rechteck muss die Karte exakt fassen; sonst rf/rb in cards.json korrigieren)')
if __name__=="__main__":
    if sys.argv[1]=='--cards':main(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None)
    else:print(json.dumps({p:detect(p) for p in sys.argv[1:]}))

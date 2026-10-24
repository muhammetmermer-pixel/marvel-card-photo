import json,cv2,numpy as np,sys
cfg=json.load(open('/tmp/w/cards.json'));U=cfg['uploads']+'/%s.jpg'
ids=json.loads(sys.argv[1]);tag=sys.argv[2];S=1.5
rows=[]
for idx in ids:
    c=cfg['cards'][idx-1];x0,y0,x1,y1=map(int,c['rf'].split(','))
    im=cv2.imread(U%c['front'])[y0:y1,x0:x1];h,w=im.shape[:2]
    def prep(cr):
        cr=cv2.resize(cr,None,fx=S,fy=S,interpolation=cv2.INTER_LANCZOS4)
        lab=cv2.cvtColor(cr,cv2.COLOR_BGR2LAB);lab[:,:,0]=cv2.createCLAHE(2.0,(8,8)).apply(lab[:,:,0]);return cv2.cvtColor(lab,cv2.COLOR_LAB2BGR)
    a=prep(im[:int(.20*h)]);b=prep(im[int(.72*h):])
    H=max(a.shape[0],b.shape[0]);pad=lambda z:cv2.copyMakeBorder(z,0,H-z.shape[0],0,0,cv2.BORDER_CONSTANT,value=(255,255,255))
    r=np.hstack([pad(a),pad(b)]);cv2.putText(r,f'#{idx}',(3,22),0,.8,(0,0,255),2);rows.append(cv2.copyMakeBorder(r,0,5,0,0,cv2.BORDER_CONSTANT,value=(255,0,255)))
W=max(r.shape[1] for r in rows);rows=[cv2.copyMakeBorder(r,0,0,0,W-r.shape[1],cv2.BORDER_CONSTANT,value=(255,255,255)) for r in rows];cv2.imwrite(f'/tmp/w/{tag}.jpg',np.vstack(rows))

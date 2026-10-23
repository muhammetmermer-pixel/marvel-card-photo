#!/usr/bin/env python3
"""Ein Aufruf: Fotos (6 je Karte) + Kontaktbogen + CSV + Pruefung (+ optional Commit/Push).
Aufruf (cwd = Repo, Branch photos-<datum>-<n> ab marvel-pipeline schon ausgecheckt):
    python3 tools/run_batch.py cards.json [--skip-photos] [--push]
cards.json:
{ "batch":"20261023-4", "branch":"photos-20261023-4", "uploads":"/mnt/user-data/uploads", "ext":"jpeg",
  "prefix":"IMG_",
  "defaults":{ "set":"Topps Chrome UEFA Champions League Last Dance", "parallel":"Standard", "price":"9.90",
     "specifics":{"*C:Sportart":"Fußball","C:Hersteller":"Topps", ...}},   # Schluessel = Spaltenanfang
  "cards":[ {"sku":"001","front":"0277","back":"0278","player":"Toni Kroos","team":"Real Madrid CF",
     "card_no":"LD-1","title":"...","price":"9.90","numbering":null,"autograph":false,
     "specifics":{"C:Saison":"2023-24","C:Spieler/Sportler":"Toni Kroos","C:Team":"Real Madrid CF","C:Kartenname":"Toni Kroos","C:Kartennummer":"LD-1"}} ] }
*C:Sportart wird vom eBay-Import ignoriert, kommt trotzdem in die CSV (Sammelbearbeitung setzt es).
"""
import csv,json,os,re,subprocess,sys,glob
import cv2,numpy as np
R='https://raw.githubusercontent.com/muhammetmermer-pixel/marvel-card-photo/'
LOGO=R+'marvel-pipeline/templates/logo_collectors_frankfurt.png'
TOPPS=dict(zip(['Manufacturer Name','Manufacturer AddressLine1','Manufacturer City','Manufacturer StateOrProvince','Manufacturer PostalCode','Manufacturer Country','Manufacturer Email'],
 ['Topps Europe Limited','18 Vincent Avenue','Milton Keynes','England','MK8 0AW','GB','infoen@toppsdirect.com']))
FIX={'Action':'Draft','Category ID':'261328','Quantity':'1','Condition ID':'4000','VAT%':'0','CD:Kartenzustand':'400010','Format':'FixedPrice'}
cfg=json.load(open(sys.argv[1]));skip='--skip-photos' in sys.argv
B='batch/'+cfg['batch'];os.makedirs(B,exist_ok=True)
def sh(*a): return subprocess.run(a,check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True).stdout
# 1 Fotos
warns=[];fails=[];okc=[]
if not skip:
    for c in cfg['cards']:
        s=c['sku'];U=f"{cfg['uploads']}/{cfg.get('prefix','IMG_')}%s.{cfg.get('ext','jpeg')}"
        try:
            o=sh('python3','tools/cardshots.py',U%c['front'],f'{B}/{s}','--corners')
            o+=sh('python3','tools/cardshots.py',U%c['back'],f'{B}/{s}b','--back')
            for l in o.splitlines():
                if l.startswith('WARN'):warns.append((s,l))
            os.rename(f'{B}/{s}_front.jpg',f'{B}/{s}_01.jpg')
            for i in range(1,5): os.rename(f'{B}/{s}_c{i}.jpg',f'{B}/{s}_0{i+1}.jpg')
            os.rename(f'{B}/{s}b_front.jpg',f'{B}/{s}_06.jpg');okc.append(c)
        except Exception as e: fails.append((s,str(e)[:60]))
    cfg['cards']=okc
    print('FOTO-FEHLER (Karte fehlt in CSV, Foto neu/--rect):',fails or 'keine');print('FOTO-WARNUNGEN:',warns or 'keine')
# 2 Kontaktbogen (300 px): Vorderseiten oben, Rueckseiten unten
ims=lambda k:[cv2.resize(cv2.imread(f"{B}/{c['sku']}_{k}.jpg"),(240,240)) for c in cfg['cards']]
F,K=ims('01'),ims('06')
for k0 in range(0,len(F),12):
    cv2.imwrite(f'/tmp/sheet_{k0//12}.jpg',np.vstack([np.hstack(F[k0:k0+12]),np.hstack(K[k0:k0+12])]))
# 3 CSV
tpl=open('templates/description_template.html',encoding='utf-8').read()
rows=list(csv.reader(open('templates/ebay_template_draft_utf8bom.csv',encoding='utf-8-sig'),delimiter=';'))
head=rows[:5];H=rows[4];n=len(H)
col=lambda p:[i for i,h in enumerate(H) if h.startswith(p)][0]
D=cfg.get('defaults',{});out=[]
for c in cfg['cards']:
    s=c['sku'];g=lambda k,d='':c.get(k,D.get(k,d))
    urls=[f"{R}{cfg['branch']}/{B}/{s}_0{i}.jpg" for i in range(1,7)]
    num=g('numbering');aut=g('autograph',False)
    rep={'{{LOGO_URL}}':LOGO,'{{TITLE}}':c['title'],'{{PLAYER}}':g('player'),'{{TEAM}}':g('team'),'{{SET}}':g('set'),'{{CARD_NO}}':g('card_no'),'{{PARALLEL}}':g('parallel','Standard'),
         '{{NUMBERING_ROW}}':f'<tr><td><b>Numbering</b></td><td>{num}</td></tr>' if num else '',
         '{{AUTOGRAPH_ROW}}':'<tr><td><b>Autograph</b></td><td>Yes</td></tr>' if aut else ''}
    rep.update({f'{{{{IMG{i+1}}}}}':u for i,u in enumerate(urls)})
    d=tpl
    for k,v in rep.items(): d=d.replace(k,v)
    d=d.replace('\n','')
    r=['']*n
    def put(p,v): r[col(p)]=v
    for k,v in FIX.items(): put(k,v)
    put('Custom label',s);put('Title',c['title']);put('Price',g('price','9.90'));put('Item photo URL','|'.join(urls));put('Description',d)
    for k,v in {**TOPPS,**D.get('specifics',{}),**c.get('specifics',{})}.items(): put(k,v)
    out.append(r)
p=f'{B}/ebay_upload_{cfg["batch"]}.csv'
with open(p,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f,delimiter=';');w.writerows(head);w.writerows(out)
# 4 Pruefung
chk=list(csv.reader(open(p,encoding='utf-8-sig'),delimiter=';'))[5:]
tr=set(subprocess.check_output(['git','ls-files'],text=True).split('\n'))
untracked=[]
bad=[]
for x in chk:
    t=x[col('Title')];pr=x[col('Price')];u=x[col('Item photo URL')].split('|')
    if len(x)!=n:bad.append((x[1],'Spalten'))
    if not 73<=len(t)<=80:bad.append((x[1],'Titellaenge %d'%len(t)))
    if not (pr.endswith('.90') and float(pr)>=9.9):bad.append((x[1],'Preis '+pr))
    if len(u)!=6:bad.append((x[1],'Links'))
    d=x[col('Description')]
    if '{{' in d or 'passion' in d.lower():bad.append((x[1],'Beschreibung'))
    for l in u:
        rel=l.split(cfg['branch']+'/')[1]
        if rel not in tr:untracked.append(rel)
print(len(chk),'Zeilen; SKU eindeutig:',len({x[1] for x in chk})==len(chk))
for x in chk:print(x[1],len(x[col('Title')]),x[col('Title')],x[col('Price')])
for c in cfg['cards']:
    g=cv2.cvtColor(cv2.imread(f"{B}/{c['sku']}_01.jpg"),cv2.COLOR_BGR2GRAY)
    if not (172<=int(g[1590,800])<=200 and int(g[800,1595])>=250 or 172<=int(g[1590,800])<=200): bad.append((c['sku'],'Schatten weicht von Referenz ab (unten x800 soll ~188 sein)'))
print('FEHLER:',bad or 'keine');
if '--push' in sys.argv:
    sh('git','add','-A');sh('git','commit','-m','Charge '+cfg['batch']+os.environ.get('COMMIT_TRAILER',''))
    sh('git','push','-u','origin',cfg['branch'])
    print('gepusht')
else:
    print('noch nicht in git (vor Upload --push oder commit):',len(set(untracked)),'Dateien')
print('HOCHPREIS >39.90 (anderer Versand, Skill H.6b):',[c['sku'] for c in cfg['cards'] if float(c.get('price',D.get('price','9.90')))>39.9] or 'keine')
print('CSV:',p,'| Kontaktbogen: /tmp/sheet_0.jpg')

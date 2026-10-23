import csv,subprocess
R='https://raw.githubusercontent.com/muhammetmermer-pixel/marvel-card-photo/'
BR='photos-20261023-3'; BD='batch/20261023-3'
LOGO=R+'marvel-pipeline/templates/logo_collectors_frankfurt.png'
tpl=open('templates/description_template.html',encoding='utf-8').read()
rows=list(csv.reader(open('templates/ebay_template_draft_utf8bom.csv',encoding='utf-8-sig'),delimiter=';'))
head=rows[:5]; ncol=len(rows[4])
SET='Topps Chrome UEFA Champions League Last Dance'
cards=[
 ('001','2023-24','Toni Kroos','Real Madrid CF','Germany','LD-1',"Toni Kroos Last Dance Topps Chrome Real Madrid CF Germany UCL Insert No Auto"),
 ('003','2014-15','Xavi Hernández','FC Barcelona','Spain','LD-2',"Xavi Hernández Last Dance Topps Chrome FC Barcelona Spain UCL Insert No Auto"),
 ('005','1990-91','Diego Maradona','SSC Napoli','Argentina','LD-10',"Diego Maradona Last Dance Topps Chrome SSC Napoli Argentina UCL Insert No Auto"),
 ('007','2005-06','Dennis Bergkamp','Arsenal FC','Netherlands','LD-7',"Dennis Bergkamp Last Dance Topps Chrome Arsenal Netherlands UCL Insert No Auto"),
 ('009','2011-12','Javier Zanetti','FC Internazionale Milano','Argentina','LD-14',"Javier Zanetti Last Dance Topps Chrome Inter Milan Argentina UCL Insert No Auto"),
]
H=rows[4]; idx={h:i for i,h in enumerate(H)}
out=[]
for sku,sea,pl,team,land,no,title in cards:
    urls=[f"{R}{BR}/{BD}/{sku}_0{i}.jpg" for i in range(1,7)]
    d=tpl
    for k,v in {'{{LOGO_URL}}':LOGO,'{{FRONT_URL}}':urls[0],'{{PLAYER}}':pl,'{{TEAM}}':team,'{{SET}}':SET,'{{CARD_NO}}':no,'{{PARALLEL}}':'Standard','{{NUMBERING_ROW}}':'','{{AUTOGRAPH_ROW}}':''}.items(): d=d.replace(k,v)
    d=d.replace('\n','')
    r=['']*ncol
    def s(h,v):
        key=[k for k in idx if k.startswith(h)][0]; r[idx[key]]=v
    s('Action','Draft');s('Custom label',sku);s('Category ID','261328');s('Title',title);s('Price','9.90');s('Quantity','1')
    s('Item photo URL','|'.join(urls));s('Condition ID','4000');s('VAT%','0');s('CD:Kartenzustand','400010');s('Description',d);s('Format','FixedPrice')
    s('*C:Sportart','Fußball');s('C:Hersteller','Topps');s('C:Spieler/Sportler',pl);s('C:Parallel/Variante','Standard');s('C:Liga','UEFA Champions League')
    s('C:Team',team);s('C:Besonderheiten','Insert');s('C:Edition','Topps Chrome UEFA Champions League');s('C:Mit Autogramm','Nein');s('C:Kartenname',pl)
    s('C:Kartennummer',no);s('C:Produktart','Einzelkarte');s('C:Ursprungsland','Großbritannien');s('C:Kartengröße','Standard');s('C:Vintage','Nein')
    s('C:Sprache','Englisch');s('C:Veranstaltung/Turnier','UEFA Champions League');s('C:Original/Lizenzierter','Original');s('C:Material','Pappe');s('C:Insert Set','Last Dance');s('C:Maßgefertigt','Nein');s('C:Saison',sea);s('C:Herstellungsjahr','2025')
    s('Manufacturer Name','Topps Europe Limited');s('Manufacturer AddressLine1','18 Vincent Avenue');s('Manufacturer City','Milton Keynes');s('Manufacturer StateOrProvince','England');s('Manufacturer PostalCode','MK8 0AW');s('Manufacturer Country','GB');s('Manufacturer Email','infoen@toppsdirect.com')
    out.append(r)
p='/mnt/user-data/outputs/ebay_upload_20261023_v3.csv'
with open(p,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f,delimiter=';');w.writerows(head);w.writerows(out)
# Prüfung
chk=list(csv.reader(open(p,encoding='utf-8-sig'),delimiter=';'))
data=chk[5:];tracked=set(subprocess.check_output(['git','ls-files'],text=True).split('\n'))
ok=True
print(len(data),'Zeilen; SKU eindeutig:',len({x[1] for x in data})==len(data))
for x in data:
    t=x[3];u=x[7].split('|')
    local=[l.split(BR+'/')[1] for l in u]
    print(x[1],len(x),len(t),t,x[5],len(u),all(l in tracked for l in local))

#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

W,H=2400,1350; C={'w':'#FFFFFF','b':'#4285F4','r':'#EA4335','y':'#FBBC04','g':'#34A853','k':'#202124','m':'#5F6368','z':'#F8F9FA'}
OUT=Path(__file__).with_name('arch-1-operator-estate.png')
def F(n,b=False):
    paths=(['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if b else ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])+['/System/Library/Fonts/HelveticaNeue.ttc','/System/Library/Fonts/Helvetica.ttc','/Library/Fonts/Arial.ttf']
    for p in paths:
        try:return ImageFont.truetype(p,n,index=1 if b and p.endswith('.ttc') else 0)
        except OSError:pass
    return ImageFont.load_default()
FT,FN,FS,FZ=F(44,1),F(24,1),F(20),F(24,1)
im=Image.new('RGB',(W,H),C['w']); d=ImageDraw.Draw(im)
def dashbox(b,r,fill,col):
    d.rounded_rectangle(b,r,fill=fill)
    x1,y1,x2,y2=b
    for x in range(x1+r,x2-r,24):
        d.line((x,y1,min(x+14,x2-r),y1),fill=col,width=3);d.line((x,y2,min(x+14,x2-r),y2),fill=col,width=3)
    for y in range(y1+r,y2-r,24):
        d.line((x1,y,x1,min(y+14,y2-r)),fill=col,width=3);d.line((x2,y,x2,min(y+14,y2-r)),fill=col,width=3)
    d.arc((x1,y1,x1+2*r,y1+2*r),180,270,fill=col,width=3);d.arc((x2-2*r,y1,x2,y1+2*r),270,360,fill=col,width=3)
    d.arc((x1,y2-2*r,x1+2*r,y2),90,180,fill=col,width=3);d.arc((x2-2*r,y2-2*r,x2,y2),0,90,fill=col,width=3)
def wrap(text,font,maxw):
    lines=[]; cur=''
    for w in text.split():
        t=(cur+' '+w).strip()
        if d.textbbox((0,0),t,font=font)[2]<=maxw:cur=t
        else:
            if cur:lines.append(cur)
            cur=w
    if cur:lines.append(cur)
    return lines
def center(b,text,font=FN,col=None):
    lines=wrap(text,font,b[2]-b[0]-30); hs=[d.textbbox((0,0),s,font=font)[3] for s in lines]; y=b[1]+(b[3]-b[1]-sum(hs)-5*(len(lines)-1))/2
    for s,h in zip(lines,hs):
        tw=d.textbbox((0,0),s,font=font)[2]; d.text((b[0]+(b[2]-b[0]-tw)/2,y),s,font=font,fill=col or C['k']); y+=h+5
def node(b,text,col,font=FN,fill=None,r=18,w=3):
    d.rounded_rectangle(b,r,fill=fill or C['w'],outline=col,width=w);center(b,text,font)
def chip(xy,text):
    bb=d.textbbox((0,0),text,font=FS); tw,th=bb[2],bb[3];x,y=xy
    d.rounded_rectangle((x-tw/2-9,y-th/2-5,x+tw/2+9,y+th/2+5),5,fill=C['w']);d.text((x-tw/2,y-th/2-1),text,font=FS,fill=C['m'])
def arrow(pts,text,at,dotted=False):
    if dotted:
        for a,b in zip(pts,pts[1:]):
            L=abs(b[0]-a[0])+abs(b[1]-a[1]); n=max(1,L//12)
            for i in range(0,n,2):
                t=i/n;u=min(1,(i+1)/n);d.line((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u),fill=C['m'],width=2)
    else:d.line(pts,fill=C['m'],width=3,joint='curve')
    a,b=pts[-2],pts[-1]; dx,dy=b[0]-a[0],b[1]-a[1]
    if dx>0:t=[b,(b[0]-11,b[1]-7),(b[0]-11,b[1]+7)]
    elif dx<0:t=[b,(b[0]+11,b[1]-7),(b[0]+11,b[1]+7)]
    elif dy>0:t=[b,(b[0]-7,b[1]-11),(b[0]+7,b[1]-11)]
    else:t=[b,(b[0]-7,b[1]+11),(b[0]+7,b[1]+11)]
    d.polygon(t,fill=C['m']);chip(at,text)

d.text((70,48),'Phase E — AICB Operator Estate on GCP (now → 20 Sep gate)',font=FT,fill=C['k'])
dashbox((430,145,2330,1255),28,C['z'],C['b']);d.text((465,165),'GCP · europe-west2 (London)',font=FZ,fill=C['b'])
node((60,200,340,285),'Visitors / prospects',C['y']);node((60,540,340,635),"Ram's Mac",C['k'])
node((610,220,1700,315),'Firebase Hosting — aicb.cloud (edge CDN, Google-managed SSL)',C['b'])
d.rounded_rectangle((570,390,1120,850),24,fill=C['w'],outline=C['b'],width=3);d.text((600,410),'Cloud Run services — scale-to-zero',font=FZ,fill=C['b'])
for b,t in [((610,470,1080,535),'aicb-contact-api'),((610,550,1080,625),'aicb-cockpit (/q phone queue)'),((610,640,1080,705),'aicb-sentinel-ui'),((610,720,1080,785),'aicb-oscan-api')]:node(b,t,C['b'],w=2)
node((1780,235,2225,340),'Cloud Trace + token budgets + canary rollbacks',C['y'],F(20,1))
node((470,925,870,1015),'dev-gcp VM (e2-medium, Ubuntu 24.04)',C['g'],F(20,1))
node((955,900,1195,980),'Cloud Scheduler',C['y'],F(20,1));node((1280,900,1550,980),'Cloud Tasks (rate-limited)',C['y'],F(20,1));node((1640,885,1995,995),'Cloud Workflows (approval gates)',C['b'],F(20,1))
node((1770,475,2240,585),'Cloud SQL Postgres + pgvector (outreach.* system of record)',C['g'],F(20,1));node((1770,650,2240,755),'BigQuery — analytical corpus, VECTOR_SEARCH',C['b'],F(20,1))
dashbox((1145,380,1695,790),22,'#FDF6F5',C['r']);d.text((1175,400),'VPC perimeter (VPC-SC)',font=FZ,fill=C['r']);node((1200,505,1640,650),'Vertex AI — Gemini 2.5/3.x + implicit context caching',C['b'],F(20,1))
d.rounded_rectangle((100,920,380,1100),38,fill=C['w'],outline=C['r'],width=3);d.rounded_rectangle((195,935,285,941),3,fill=C['r']);center((120,955,360,1080),"Ram's phone — /q approval",F(20,1))
d.rounded_rectangle((470,1135,2285,1215),14,fill='#EEF0F1',outline=C['m'],width=2);center((470,1135,2285,1215),'Workload Identity Federation · per-service least-privilege SAs · Cloud Audit Logs',F(20,1))
arrow([(340,242),(500,242),(500,267),(610,267)],'https',(475,220));arrow([(1155,315),(1155,350),(845,350),(845,390)],'path rewrites',(995,350))
arrow([(340,587),(400,587),(400,970),(470,970)],'Tailscale / IAP tunnel (no public IPs)',(490,866))
arrow([(1120,520),(1170,520),(1170,475),(1420,475),(1420,505)],'ADC via metadata server — zero API keys',(1295,475));arrow([(870,970),(900,970),(900,870),(1560,870),(1560,650)],'ADC via metadata server — zero API keys',(1230,870))
arrow([(1120,700),(1720,700),(1720,702),(1770,702)],'stream events',(1450,700));arrow([(1120,470),(1500,470),(1500,290),(1780,290)],'traces',(1510,445),True)
arrow([(1195,940),(1280,940)],'enqueue',(1238,916));arrow([(1550,940),(1640,940)],'dispatch',(1595,916));arrow([(1820,885),(1820,820),(2250,820),(2250,530),(2240,530)],'write-ahead outbox row',(2050,820));arrow([(1640,965),(1540,965),(1540,1070),(380,1070)],'callback resume on approval',(1100,1070))
d.rectangle((0,1290,W,H),fill=C['k']);d.text((70,1305),'Phase E · operator estate · AICB · Aug 2026',font=F(20,1),fill=C['w'])
im.save(OUT,'PNG',optimize=True)
with Image.open(OUT) as q:assert q.size==(W,H) and q.mode=='RGB'
print(f'{OUT} — {OUT.stat().st_size:,} bytes')

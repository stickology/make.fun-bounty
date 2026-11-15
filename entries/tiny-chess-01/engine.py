import json,os,urllib.request as U
E=os.environ['MAKEFUN_ENV_URL']
def post(p,b):
 r=U.Request(E+p,json.dumps(b).encode(),{'content-type':'application/json'})
 with U.urlopen(r) as f:return json.load(f)
# Board: 120-cell mailbox, A8=21..H8=28, A1=91..H1=98. The side to move is always upper case at the bottom:
# after every move the board is mirrored top to bottom (F) and its case swapped. Values and piece-square
# tables are Michniewski's simplified evaluation.
V={'P':100,'N':320,'B':330,'R':500,'Q':900,'K':20000}
T={'P':'0 0 0 0 0 0 0 0 50 50 50 50 50 50 50 50 10 10 20 30 30 20 10 10 5 5 10 25 25 10 5 5 0 0 0 20 20 0 0 0 5 -5 -10 0 0 -10 -5 5 5 10 10 -20 -20 10 10 5 0 0 0 0 0 0 0 0',
'N':'-50 -40 -30 -30 -30 -30 -40 -50 -40 -20 0 0 0 0 -20 -40 -30 0 10 15 15 10 0 -30 -30 5 15 20 20 15 5 -30 -30 0 15 20 20 15 0 -30 -30 5 10 15 15 10 5 -30 -40 -20 0 5 5 0 -20 -40 -50 -40 -30 -30 -30 -30 -40 -50',
'B':'-20 -10 -10 -10 -10 -10 -10 -20 -10 0 0 0 0 0 0 -10 -10 0 5 10 10 5 0 -10 -10 5 5 10 10 5 5 -10 -10 0 10 10 10 10 0 -10 -10 10 10 10 10 10 10 -10 -10 5 0 0 0 0 5 -10 -20 -10 -10 -10 -10 -10 -10 -20',
'R':'0 0 0 0 0 0 0 0 5 10 10 10 10 10 10 5 -5 0 0 0 0 0 0 -5 -5 0 0 0 0 0 0 -5 -5 0 0 0 0 0 0 -5 -5 0 0 0 0 0 0 -5 -5 0 0 0 0 0 0 -5 0 0 0 5 5 0 0 0',
'Q':'-20 -10 -10 -5 -5 -10 -10 -20 -10 0 0 0 0 0 0 -10 -10 0 5 5 5 5 0 -10 -5 0 5 5 5 5 0 -5 0 0 5 5 5 5 0 -5 -10 5 5 5 5 5 0 -10 -10 0 5 0 0 0 0 -10 -20 -10 -10 -5 -5 -10 -10 -20',
'K':'-30 -40 -40 -50 -50 -40 -40 -30 -30 -40 -40 -50 -50 -40 -40 -30 -30 -40 -40 -50 -50 -40 -40 -30 -30 -40 -40 -50 -50 -40 -40 -30 -20 -30 -30 -40 -40 -30 -30 -20 -10 -20 -20 -20 -20 -20 -20 -10 20 20 0 0 0 0 20 20 20 30 10 0 0 10 30 20'}
T['E']='-50 -40 -30 -20 -20 -30 -40 -50 -30 -20 -10 0 0 -10 -20 -30 -30 -10 20 30 30 20 -10 -30 -30 -10 30 40 40 30 -10 -30 -30 -10 30 40 40 30 -10 -30 -30 -10 20 30 30 20 -10 -30 -30 -30 0 0 0 0 -30 -30 -50 -30 -30 -30 -30 -30 -30 -50'
V['E']=V['K']
P={}
for k,s in T.items():
 a=[0]*120;v=list(map(int,s.split()))
 for r in range(8):
  for c in range(8):a[21+10*r+c]=v[8*r+c]+V[k]
 P[k]=a
def F(i):return(11-i//10)*10+i%10
N,S=-10,10
D={'N':(-21,-19,-12,-8,8,12,19,21),'B':(-11,-9,9,11),'R':(-10,-1,1,10)}
D['Q']=D['K']=D['B']+D['R']
MATE=50000
class Stop(Exception):pass
def gen(b,ep,cr):
 # pseudo-legal moves (i,j) of the upper-case side; cr=(long,short) castling rights
 for i in range(21,99):
  p=b[i]
  if not p.isupper():continue
  if p=='P':
   if b[i+N]=='.':
    yield i,i+N
    if i>80 and b[i+2*N]=='.':yield i,i+2*N
   for j in(i+N-1,i+N+1):
    if b[j].islower() or j==ep:yield i,j
   continue
  for d in D[p]:
   j=i+d
   while 1:
    q=b[j]
    if q==' ' or q.isupper():break
    yield i,j
    if q!='.' or p in'NK':break
    j+=d
  if p=='K' and i==95:
   if cr[1] and b[96]==b[97]=='.' and b[98]=='R':yield i,97
   if cr[0] and b[94]==b[93]==b[92]=='.' and b[91]=='R':yield i,93
def att(b,s):
 # is square s attacked by a lower-case piece?
 for d in D['Q']:
  j=s+d;n=1
  while 1:
   q=b[j]
   if q==' ' or q.isupper():break
   if q!='.':
    u=q.upper()
    if u=='Q' or(u=='B' and d in D['B'])or(u=='R' and d in D['R'])or(u=='K' and n==1)or(q=='p' and d in(-11,-9) and n==1):return 1
    break
   j+=d;n+=1
 for d in D['N']:
  if b[s+d]=='n':return 1
 return 0
def turn(b):return''.join(b[r*10:r*10+10]for r in range(11,-1,-1)).swapcase()
def make(pos,m,pr='Q'):
 # play move m on pos=(board,score,ep,cr,ocr); return the position from the opponent's side
 b,sc,ep,cr,ocr=pos;i,j=m;b=list(b);p=b[i];q=b[j]
 sc+=P[p][j]-P[p][i]
 if q.islower():sc+=P[q.upper()][F(j)]
 b[j]=p;b[i]='.';nep=0
 if i==91 or j==91:cr=(0,cr[1])
 if i==98 or j==98:cr=(cr[0],0)
 if j==21:ocr=(0,ocr[1])
 if j==28:ocr=(ocr[0],0)
 if p=='K':
  cr=(0,0)
  if abs(j-i)==2:
   r,t=(98,96)if j>i else(91,94)
   b[r]='.';b[t]='R';sc+=P['R'][t]-P['R'][r]
 if p=='P':
  if j<29:b[j]=pr;sc+=P[pr][j]-P['P'][j]
  if j-i==2*N:nep=F(i+N)
  if j==ep:b[j+S]='.';sc+=P['P'][F(j+S)]
 return(turn(''.join(b)),-sc,nep,ocr,cr)
def board(fen):
 f=fen.split();b=[' ']*120
 for r,row in enumerate(f[0].split('/')):
  c=0
  for ch in row:
   if ch.isdigit():
    for _ in range(int(ch)):b[21+10*r+c]='.';c+=1
   else:b[21+10*r+c]=ch;c+=1
 b=''.join(b);cs=f[2];ep=0
 if f[3]!='-':ep=21+(ord(f[3][0])-97)+10*(8-int(f[3][1]))
 wc=('Q'in cs,'K'in cs);bc=('q'in cs,'k'in cs)
 sc=sum(P[p][i]if p.isupper()else-P[p.upper()][F(i)]for i,p in enumerate(b)if p.isalpha())
 if f[1]=='b':return(turn(b),-sc,F(ep)if ep else 0,bc,wc),1
 return(b,sc,ep,wc,bc),0
def sq(i,bl):
 if bl:i=F(i)
 return'abcdefgh'[i%10-1]+str(10-i//10)
class Search:
 def __init__(s,hist,lim,tt):s.tt=tt;s.hist=hist;s.n=0;s.kill={};s.lim=lim;s.h={}
 def moves(s,pos,tm,ply):
  b=pos[0];ms=list(gen(b,pos[2],pos[3]));k=s.kill.get(ply);h=s.h
  def key(m):
   if m==tm:return-1e9
   q=b[m[1]]
   if q.islower():return-1e6-10*V[q.upper()]+V[b[m[0]]]/100
   if m==k:return-9e5
   return-h.get((b[m[0]],m[1]),0)
  ms.sort(key=key);return ms
 def q(s,pos,a,be):
  s.n+=1;b=pos[0];sc=pos[1]
  if sc>=be:return sc
  a=max(a,sc)
  cs=[m for m in gen(b,pos[2],pos[3])if b[m[1]].islower()]
  cs.sort(key=lambda m:-10*V[b[m[1]].upper()]+V[b[m[0]]]/100)
  for m in cs:
   if b[m[1]]=='k':return MATE
   v=-s.q(make(pos,m),-be,-a)
   if v>=be:return v
   a=max(a,v)
  return a
 def ab(s,pos,d,a,be,ply,null=1):
  if d<=0:return s.q(pos,a,be)
  s.n+=1;b=pos[0]
  if s.n>s.lim:raise Stop
  if b in s.hist:return 0
  key=(b,pos[2],pos[3],pos[4]);e=s.tt.get(key);tm=None
  if e:
   ed,ev,ef,tm=e
   if ed>=d:
    if ef==0 or(ef==1 and ev>=be)or(ef==2 and ev<=a):return ev
  chk=att(b,b.index('K'))
  if chk:d+=1
  elif null and d>=3 and pos[1]>=be:
   v=-s.ab((turn(b),-pos[1],0,pos[4],pos[3]),d-3,-be,-be+1,ply+1,0)
   if v>=be:return v
  a0=a;best=-MATE-1;bm=None
  for n,m in enumerate(s.moves(pos,tm,ply)):
   if b[m[1]]=='k':return MATE
   c=make(pos,m);quiet=b[m[1]]=='.'
   if n==0:v=-s.ab(c,d-1,-be,-a,ply+1)
   else:
    r=1 if quiet and not chk and d>=3 and n>=4 else 0
    v=-s.ab(c,d-1-r,-a-1,-a,ply+1)
    if v>a and(r or v<be):v=-s.ab(c,d-1,-be,-a,ply+1)
   if v>best:best=v;bm=m
   if v>a:a=v
   if a>=be:
    if quiet:s.kill[ply]=m;k=(b[m[0]],m[1]);s.h[k]=s.h.get(k,0)+d*d
    break
  if best<-MATE+999:best=-MATE+ply if chk else 0
  s.tt[key]=(d,best,1 if best>=be else 2 if best<=a0 else 0,bm)
  return best
KM=P['K']
def choose(fen,legal,hist,budget):
 # endgame (little material besides kings and pawns): the king heads for the centre
 P['K']=P['E']if sum(V[c.upper()]for c in fen.split()[0]if c.upper()in'NBRQ')<=2600 else KM
 TT.clear()
 pos,bl=board(fen);s=Search(hist,budget*6//5,TT);ok={}
 for m in gen(pos[0],pos[2],pos[3]):
  for u in legal:
   if sq(m[0],bl)+sq(m[1],bl)==u[:4]and(m not in ok or u[4:]=='q'):ok[m]=u
 best=legal[0];bm=None;d=1
 try:
  while s.n<budget and d<40:
   a=-MATE-1
   for m in sorted(ok,key=lambda m:m!=bm):
    u=ok[m]
    v=-s.ab(make(pos,m,u[4:].upper()or'Q'),d-1,-MATE-1,-a,1)
    if v>a:a=v;best=u;bm=m
   if a>MATE-999:break
   d+=1
 except Stop:pass
 return best
B=int(os.environ.get('NODES','70000'));TT={}
while 1:
 g=post('/game',{})
 if g['status']=='done':break
 h=set();TT.clear()
 while g['status']=='your_move':
  p,bl=board(g['fen']);h.add(p[0])
  g=post('/move',{'game':g['game'],'move':choose(g['fen'],g['legal_moves'],h,B)})

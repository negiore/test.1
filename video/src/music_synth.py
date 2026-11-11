import json,numpy as np,wave
from scipy.signal import butter,sosfilt
SR=44100
T=json.load(open("timeline.json"));M=T["marks"];total=T["total"];N=int(total*SR)
L=np.zeros(N);R=np.zeros(N)
rng=np.random.default_rng(7)
BPM=128;beat=60/BPM;bar=beat*4
drop=M["drop"];org=drop%bar
brk=M["break"];endc=M["end_card"];bstart=M["build_start"]-1.3
def lp(x,f,o=2): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x)
def hp(x,f,o=2): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x)
def bp(x,lo,hi): return sosfilt(butter(2,[lo,hi],'band',fs=SR,output='sos'),x)
def add(t,x,g=1.0,pan=0.0):
  i=int(t*SR)
  if i>=N or i+len(x)<0: return
  if i<0: x=x[-i:];i=0
  x=x[:N-i]; L[i:i+len(x)]+=x*g*(1-pan)**0.5*1.0; R[i:i+len(x)]+=x*g*(1+pan)**0.5*1.0
def tt(d): return np.arange(int(d*SR))/SR
def env_ad(d,a=0.005,dec=0.2):
  t=tt(d);return np.minimum(1,t/a)*np.exp(-t/dec)
def kick(d=0.45,hard=1.0):
  t=tt(d);f=45+120*np.exp(-t*30)*hard;ph=2*np.pi*np.cumsum(f)/SR
  return np.sin(ph)*np.exp(-t*7)+0.3*np.exp(-t*200)*rng.standard_normal(len(t))*0.3
def snare(d=0.25):
  t=tt(d);n=bp(rng.standard_normal(len(t)),900,7000)*np.exp(-t*18);b=np.sin(2*np.pi*190*t)*np.exp(-t*25)
  return n*0.8+b*0.5
def clap(d=0.3):
  t=tt(d);n=bp(rng.standard_normal(len(t)),1000,5000);e=np.exp(-t*20)
  for k in (0.01,0.02): e+=np.where(t>k,np.exp(-(t-k)*60),0)*0.6
  return n*e*0.8
def hat(d=0.06,open_=False):
  t=tt(0.25 if open_ else d);return lp(hp(rng.standard_normal(len(t)),7000),11000)*np.exp(-t*(14 if open_ else 80))*0.3
def saw(f,t,det=0): 
  ph=(f*t+rng.random())%1;return 2*ph-1
def supersaw(freqs,d,cut=4000):
  t=tt(d);x=np.zeros(len(t))
  for f in freqs:
    for dt in (-0.12,-0.06,-0.02,0.02,0.06,0.12): x+=saw(f*(1+dt/12),t)
  x=lp(x,cut);return x/ (len(freqs)*6)
def pad(freqs,d,cut=900):
  t=tt(d);x=np.zeros(len(t))
  for f in freqs:
    for dt in (-0.08,0,0.08): x+=saw(f*(1+dt/12),t)
  x=lp(x,cut);a=np.minimum(1,t/0.4)*np.minimum(1,(d-t)/0.4).clip(0,1)
  return x*a/(len(freqs)*3)
def piano(f,d=2.5):
  t=tt(d);x=sum(np.sin(2*np.pi*f*k*t)*np.exp(-t*(1.2+k*0.8))/k**1.3 for k in range(1,7))
  return x*np.minimum(1,t/0.004)
def pluck(f,d=0.3):
  t=tt(d);return lp(saw(f,t),1800)*np.exp(-t*12)
def nt(n): return 440*2**((n-69)/12)
CH=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]  # Am F C G
BASS=[45,41,36,43]
def bars(t0,t1):
  k=int(np.ceil((t0-org)/bar));t=org+k*bar
  while t<t1-1e-6: yield k,t; t+=bar
# ---------- INTRO: pad + heartbeat ----------
for k,t in bars(0,bstart):
  c=CH[k%4]
  add(t,pad([nt(n-12) for n in c]+[nt(c[0]-24)],bar+0.4,cut=600+400*min(1,t/20)),0.35)
  add(t,kick(0.4,0.6),0.55); add(t+beat*0.6,kick(0.4,0.5),0.35)
  add(t+beat*2,kick(0.4,0.6),0.5); add(t+beat*2.6,kick(0.4,0.5),0.3)
  if t>5:
    for s in range(8):
      n=c[[0,1,2,1][s%4]]+12+(12 if s>=4 else 0)
      add(t+s*beat/2,pluck(nt(n)),0.10,pan=0.4 if s%2 else -0.4)
  if t>17:
    for s in range(8): add(t+s*beat/2+beat/4,hat(),0.18)
# ---------- BUILD ----------
b0=bstart;bd=drop-b0
t=tt(bd);nz=rng.standard_normal(len(t))
cut=np.linspace(300,9000,len(t))**1
seg=[];sz=2048
y=np.zeros(len(t))
for i in range(0,len(t),sz):
  c=cut[i];y[i:i+sz]=bp(nz[i:i+sz+0],max(100,c*0.5),min(18000,c*1.5))[:len(y[i:i+sz])]
add(b0,y*np.linspace(0.05,0.6,len(t)),0.8)
tr=2*np.pi*np.cumsum(np.linspace(110,880,len(t)))/SR
add(b0,(np.sin(tr)+0.4*np.sign(np.sin(tr)))*np.linspace(0,0.25,len(t)),0.6)
# snare roll accelerating
tk=b0
while tk<drop-0.12:
  p=(tk-b0)/bd; add(tk,snare(),0.25+0.5*p); tk+=beat*(1 if p<0.3 else 0.5 if p<0.6 else 0.25 if p<0.85 else 0.125)
# ---------- DROP ----------
for k,t in bars(drop,brk):
  c=CH[k%4];bn=BASS[k%4]
  for q in range(4):
    add(t+q*beat,kick(0.45,1.2),0.9)
    add(t+q*beat+beat/2,hat(open_=True),0.12)
    for s in (0,1): add(t+q*beat+s*beat/2+beat/4,hat(),0.07)
  add(t+beat,clap(),0.55);add(t+beat*3,clap(),0.55)
  # sidechained chords: 8th stabs pumping
  ch=supersaw([nt(n) for n in c]+[nt(c[0]+12)],bar,cut=3200)
  tc=tt(bar);pump=np.minimum(1,((tc%beat)/beat)*2.2)**1.5
  add(t,ch*pump,0.45,pan=-0.3)
  ch2=supersaw([nt(n) for n in c],bar,cut=3000);add(t,ch2*pump,0.35,pan=0.3)
  tsb=tt(bar);add(t,np.sin(2*np.pi*nt(bn-24)*tsb)*pump*np.minimum(1,(bar-tsb)/0.02),0.5)
  # bass offbeat
  for q in range(4):
    tb=tt(beat/2);bs=lp(saw(nt(bn-12),tb),600)*np.minimum(1,tb/0.005)*np.exp(-tb*4)
    sub=np.sin(2*np.pi*nt(bn-12)*tb)*np.minimum(1,tb/0.01)*np.exp(-tb*3)
    add(t+q*beat+beat/2,bs*0.6+sub*0.8,0.5)
  # arp
  for s in range(16):
    n=c[[0,1,2,1][s%4]]+24 + (12 if (s//4)%2 else 0)
    add(t+s*beat/4,pluck(nt(n),0.18),0.05,pan=0.5 if s%2 else -0.5)
# crash on drop
tcr=tt(2.5);add(drop,lp(hp(rng.standard_normal(len(tcr)),5000),10000)*np.exp(-tcr*1.8)*0.5,0.45)
# ---------- BREAK ----------
for k,t in bars(brk,endc):
  c=CH[k%4]
  for j,n in enumerate(c): add(t+j*0.03,piano(nt(n)),0.16); add(t+j*0.03,piano(nt(n)*1.003),0.06)
  add(t,piano(nt(c[0]-12),3.0),0.2)
  add(t+beat*2,piano(nt(c[2]+12),1.5),0.1)
  add(t,pad([nt(n) for n in c],bar+0.4,cut=1500),0.22)
  add(t,kick(0.4,0.5),0.3);add(t+beat*0.6,kick(0.4,0.4),0.2)
# ---------- END CARD ----------
fin=[nt(n) for n in (45,57,60,64,69,72,76)]
add(endc,kick(0.9,1.5)*1.2,1.0)
td=tt(total-endc);ch=supersaw(fin,total-endc,cut=3000)*np.exp(-td*0.5)
add(endc,ch,0.5)
for f in fin[1:5]: add(endc+0.02,piano(f,4.0),0.2)
add(endc,hp(rng.standard_normal(len(td)),4000)*np.exp(-td*1.2)*0.4,0.7)
# ---------- SFX on phrases ----------
def whoosh(d=0.35):
  t=tt(d);x=bp(rng.standard_normal(len(t)),800,6000);return x*np.sin(np.pi*t/d)**2*0.5
def impact():
  t=tt(1.2);return kick(1.2,2.0)*0.9+lp(rng.standard_normal(len(t)),1500)*np.exp(-t*6)*0.5
def glitch():
  out=np.zeros(int(0.4*SR))
  for _ in range(7):
    i=rng.integers(0,len(out)-3000);l=rng.integers(300,2500);f=rng.choice([800,1600,2400,3200,4800])
    out[i:i+l]+=np.sign(np.sin(2*np.pi*f*np.arange(l)/SR))*0.3
  return out
for p in T["phrases"]:
  s=p["style"];t=p["start"]
  inDrop=drop<=t<brk
  if s in("slam","stamp","final") or (s=="drop"): add(t-0.02,impact(),0.6 if not inDrop else 0.35)
  elif s in("glitch","shatter"): add(t,glitch(),0.45)
  elif s in("type","counter"):
    for j in range(6): add(t+j*0.05,hat(0.02),0.12)
  else: add(t-0.15,whoosh(),0.35)
# boot glitch at start
add(0.05,glitch(),0.5);add(0.4,glitch(),0.4)
L=lp(L,13000);R=lp(R,13000)
for A in (L,R): A/=np.percentile(np.abs(A),99.9)
L=np.tanh(L*0.9);R=np.tanh(R*0.9)
mx=max(np.abs(L).max(),np.abs(R).max());L/=mx;R/=mx
# fades
f=np.minimum(1,np.arange(N)/(0.05*SR));fo=np.minimum(1,(N-np.arange(N))/(1.5*SR));L*=f*fo;R*=f*fo
st=np.stack([L,R],1)*0.95
w=wave.open("music.wav","wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype(np.int16).tobytes());w.close()
print("ok",total)

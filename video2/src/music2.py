import json,numpy as np,wave
from scipy.signal import butter,sosfilt
SR=44100;T=json.load(open("timeline.json"));M=T["marks"];total=T["total"];N=int(total*SR)
L=np.zeros(N);R=np.zeros(N);rng=np.random.default_rng(3)
def lp(x,f,o=2):return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x)
def hp(x,f,o=2):return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x)
def bp(x,a,b):return sosfilt(butter(2,[a,b],'band',fs=SR,output='sos'),x)
def tt(d):return np.arange(int(d*SR))/SR
def add(t,x,g=1.0,pan=0.0):
  i=int(t*SR)
  if i>=N:return
  if i<0:x=x[-i:];i=0
  x=x[:N-i];L[i:i+len(x)]+=x*g*np.sqrt(1-pan);R[i:i+len(x)]+=x*g*np.sqrt(1+pan)
def nt(n):return 440*2**((n-69)/12)
def saw(f,t):return 2*((f*t+rng.random())%1)-1
def kick(d=0.45,h=1.0):
  t=tt(d);ph=2*np.pi*np.cumsum(45+120*np.exp(-t*30)*h)/SR;return np.sin(ph)*np.exp(-t*7)
def clap():t=tt(0.3);return bp(rng.standard_normal(len(t)),1000,5000)*np.exp(-t*22)*0.8
def hat(d=0.05,o=False):t=tt(0.22 if o else d);return lp(hp(rng.standard_normal(len(t)),7000),11000)*np.exp(-t*(14 if o else 80))*0.3
def piano(f,d=1.6):
  t=tt(d);return sum(np.sin(2*np.pi*f*k*t)*np.exp(-t*(1.5+k*0.9))/k**1.3 for k in range(1,7))*np.minimum(1,t/0.004)
def bell(f,d=1.8):
  t=tt(d);return (np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*4)+0.25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*8))*np.exp(-t*2.2)*np.minimum(1,t/0.002)
def pad(fs,d,cut=900):
  t=tt(d);x=sum(saw(f*(1+dt/12),t) for f in fs for dt in(-0.08,0,0.08));x=lp(x,cut)
  return x*np.clip(np.minimum(t/0.5,(d-t)/0.5),0,1)/(len(fs)*3)
def supersaw(fs,d,cut=3200):
  t=tt(d);x=sum(saw(f*(1+dt/12),t) for f in fs for dt in(-0.12,-0.05,0.05,0.12));return lp(x,cut)/(len(fs)*4)
def bass(f,d):t=tt(d);return (lp(saw(f,t),500)*0.6+np.sin(2*np.pi*f*t))*np.exp(-t*3)*np.minimum(1,t/0.005)
def noise_sweep(d,a,b):
  t=tt(d);n=rng.standard_normal(len(t));y=np.zeros(len(t));sz=2048
  for i in range(0,len(t),sz):
    c=a+(b-a)*i/len(t);y[i:i+sz]=bp(n[i:i+sz],max(80,c*0.6),min(18000,c*1.4))[:len(y[i:i+sz])]
  return y
A,B,C,D,E,F,G,H=[M[k] for k in "ABCDEFGH"];DROP=M["drop"]
# ---- A: dark drone + clock ----
dur=B-0.3
add(0,pad([nt(45),nt(52),nt(57)],dur,cut=500),0.5)
add(0,lp(rng.standard_normal(int(dur*SR)),200)*0.15,0.6)
tk=0.0
while tk<B-0.4:
  t=tt(0.04);add(tk,bp(rng.standard_normal(len(t)),2000,6000)*np.exp(-t*120),0.35 if int(tk*2)%2==0 else 0.2);tk+=0.5
for it in T["items"]:
  if it["sc"]=="A":
    for j in range(5):t=tt(0.03);add(it["start"]-0.25+j*0.045,bp(rng.standard_normal(len(t)),1500,5000)*np.exp(-t*150),0.4)
    if it.get("big"):add(it["start"]+0.1,kick(1.2,2)*1.0+lp(rng.standard_normal(int(1.2*SR)),300)*np.exp(-tt(1.2)*4)*0.4,0.7)
# record scratch + glass at B
t=tt(0.35);sc=np.sin(2*np.pi*np.cumsum(np.linspace(900,120,len(t)))/SR)*np.exp(-t*4)*0.5+bp(rng.standard_normal(len(t)),500,3000)*np.exp(-t*6)*0.4
add(B-0.38,sc,0.8)
t=tt(1.0);add(B,hp(rng.standard_normal(len(t)),3000)*np.exp(-t*5)*0.6+kick(1.0,1.8),0.6)
# ---- B..E: swing groove (BPM 132, swung 8ths) ----
bpm=132;bt=60/bpm;sw=0.62
prog=[[50,53,57,60],[43,47,50,53],[48,52,55,59],[45,49,52,55]] # Dm7 G7 Cmaj7 A7
walk=[[38,41,45,48],[43,47,50,41],[36,40,43,47],[45,44,43,42]]
t0=B+0.05;k=0
while t0<F-0.3:
  bar=k//4;q=k%4;tb=t0
  c=prog[bar%4];wn=walk[bar%4][q]
  add(tb,bass(nt(wn-12),bt*0.95),0.55)
  add(tb,kick(0.3,0.8),0.45 if q in(0,2) else 0.0)
  if q in(1,3):add(tb,clap(),0.4)
  add(tb,hat(),0.12);add(tb+bt*sw,hat(),0.09)
  if q in(1,3):
    for j,n in enumerate(c):add(tb+bt*sw+j*0.008,piano(nt(n+12),0.35)*np.exp(-tt(0.35)*6),0.07)
  if q==0 and bar%2==0:add(tb,supersaw([nt(n+12) for n in c],0.25,2800)*np.exp(-tt(0.25)*10),0.35)
  t0+=bt;k+=1
# SFX for C (chat pop), D (step), E (counter)
for it in T["items"]:
  s=it["start"]
  if it["k"]=="u" and it["sc"]=="C":
    add(s,bell(nt(84),0.4)*0.6+bell(nt(91),0.4)*0.4,0.35)
  if it.get("step"):
    for j,n in enumerate([72,76,79,84]):add(s+j*0.05,bell(nt(n+it["step"]*2),0.5),0.18)
    t=tt(0.25);add(s-0.1,bp(rng.standard_normal(len(t)),800,5000)*np.sin(np.pi*t/0.25)**2,0.4)
  if it.get("count"):
    dd=min(1.6,it["end"]-it["start"])
    for j in range(16):t=tt(0.03);add(s+0.4+j*dd/16,bp(rng.standard_normal(len(t)),3000,7000)*np.exp(-t*100),0.25)
  if it.get("big")=="こわ" or it.get("big")=="しばかないで！" or it.get("big")=="重っ！？":
    add(s,kick(0.8,1.6),0.5)
# ---- F: piano + bells ----
chF=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]];barF=2.2;tf=F-0.2;i=0
while tf<G-0.3:
  c=chF[i%4]
  for j,n in enumerate(c+[c[0]+12,c[1]+12]):add(tf+j*barF/6,piano(nt(n),2.0),0.12,pan=-0.3+0.15*j)
  add(tf,piano(nt(c[0]-12),2.5),0.18);add(tf,pad([nt(n) for n in c],barF+0.4,1200),0.15)
  tf+=barF;i+=1
# ---- G: heartbeat riser to drop ----
g0=G;add(g0,noise_sweep(DROP-g0,200,9000)*np.linspace(0.05,0.5,int((DROP-g0)*SR)),0.6)
hb=g0
while hb<DROP-0.3:add(hb,kick(0.4,0.5),0.5);add(hb+0.22,kick(0.4,0.4),0.3);hb+=0.8
bpm2=128;b2=60/bpm2;bar2=b2*4;prog2=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]];bs2=[45,41,36,43]
t=tt(2.5);add(DROP,lp(hp(rng.standard_normal(len(t)),5000),10000)*np.exp(-t*1.8)*0.5,0.5)
add(DROP,kick(1.0,2.0),0.9)
td=DROP;k=0
while td<H-0.2:
  c=prog2[k%4]
  for q in range(4):
    add(td+q*b2,kick(0.45,1.2),0.85);add(td+q*b2+b2/2,hat(o=True),0.12)
  add(td+b2,clap(),0.5);add(td+3*b2,clap(),0.5)
  tc=tt(bar2);pump=np.minimum(1,((tc%b2)/b2)*2.2)**1.5
  add(td,supersaw([nt(n) for n in c]+[nt(c[0]+12)],bar2)*pump,0.45,pan=-0.3);add(td,supersaw([nt(n) for n in c],bar2,3000)*pump,0.35,pan=0.3)
  add(td,np.sin(2*np.pi*nt(bs2[k%4]-24)*tc)*pump*np.minimum(1,(bar2-tc)/0.02),0.5)
  for s in range(8):add(td+s*b2/2,bell(nt(c[s%3]+24),0.3),0.06,pan=0.5 if s%2 else -0.5)
  td+=bar2;k+=1
add(H-0.2,kick(1.2,2.0),0.8)
# ---- H: music box credits ----
mel=[72,76,79,76,74,77,81,77,72,76,79,84,83,79,76,72];th=H+0.2;j=0
while th<total-1.0:
  add(th,bell(nt(mel[j%16]),1.6),0.22,pan=0.2*np.sin(j));
  if j%4==0:add(th,pad([nt(n) for n in prog2[(j//4)%4]],1.9*1.0,1000),0.12);add(th,piano(nt(prog2[(j//4)%4][0]-12),2.0),0.12)
  th+=0.48;j+=1
L=lp(L,13000);R=lp(R,13000)
for X in(L,R):X/=np.percentile(np.abs(X),99.9)
L=np.tanh(L*0.9);R=np.tanh(R*0.9);mx=max(np.abs(L).max(),np.abs(R).max());L/=mx;R/=mx
fo=np.minimum(1,(N-np.arange(N))/(1.8*SR));L*=fo;R*=fo
st=(np.stack([L,R],1)*0.95*32767).astype(np.int16)
w=wave.open("music.wav","wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(st.tobytes());w.close();print("ok")

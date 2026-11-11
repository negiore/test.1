import json,numpy as np,soundfile as sf
SR=44100;FPS=30
S=json.load(open("script2.json"))
t=0.6;items=[];chunks=[];marks={}
for i,s in enumerate(S):
  t+=s.get("gap",0.25)
  if s["k"]=="v":
    a,sr=sf.read(f"proc/l{i:02d}.wav");
    if a.ndim>1:a=a.mean(1)
    a=np.interp(np.arange(0,len(a)/sr,1/SR),np.arange(len(a))/sr,a)
    # trim silence
    e=np.abs(a)>0.01;nz=np.nonzero(e)[0];a=a[max(0,nz[0]-400):nz[-1]+2000]
    d=len(a)/SR;chunks.append((t,a))
    items.append(dict(s,i=i,start=round(t,3),end=round(t+d,3)));t+=d
  else:
    d=1.6+0.06*len(s["t"])
    items.append(dict(s,i=i,start=round(t,3),end=round(t+d,3)));t+=d
  if s.get("drop"):marks["drop"]=items[-1]["start"]
for sc in "ABCDEFGH":
  marks[sc]=min(x["start"] for x in items if x["sc"]==sc)
# extend each voice item display until next item start
for a,b in zip(items,items[1:]): a["hold"]=round(b["start"],3)
items[-1]["hold"]=round(items[-1]["end"]+0.6,3)
marks["H"]=items[-2]["start"]-4.2  # credits start before last lines
total=items[-1]["end"]+2.5;marks["total"]=round(total,3)
v=np.zeros(int(total*SR)+SR)
for st,c in chunks:i=int(st*SR);v[i:i+len(c)]+=c
v=v[:int(total*SR)];v=v/np.abs(v).max()*0.9
sf.write("voice.wav",v,SR,subtype="PCM_16")
h=SR//FPS;env=[float(np.sqrt((v[k*h:(k+1)*h]**2).mean())) for k in range(int(total*FPS))]
m=max(env);env=[round(min(1,e/m*1.5),3) for e in env]
json.dump(dict(items=items,marks=marks,env=env,fps=FPS,total=total),open("timeline.json","w"),ensure_ascii=False)
print(marks)
for x in items:print(x["sc"],x["start"],x["end"],x["k"],x.get("sub",x["t"]))

import wave,numpy as np,json
out={}
for i in range(6):
  w=wave.open(f"orig/sec{i}.wav");a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float);sr=w.getframerate()
  h=sr//100;e=np.array([20*np.log10(np.sqrt((a[k:k+h]**2).mean())+1) for k in range(0,len(a)-h,h)])
  sp=e>45;segs=[];k=0;n=len(sp)
  while k<n:
    if sp[k]:
      j=k
      while j<n and (sp[j] or (j+25<n and sp[j:j+25].any())): j+=1
      segs.append([round(k/100,2),round(j/100,2)]);k=j
    else:k+=1
  R=1.12;segs=[[round(x/R,3),round(y/R,3)] for x,y in segs];out[i]={"dur":len(a)/sr/R,"segs":segs};print(i,round(len(a)/sr,2),segs)
json.dump(out,open("segs.json","w"))

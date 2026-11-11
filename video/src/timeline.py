import json,wave,numpy as np
SR=44100;FPS=30
segs=json.load(open("segs.json"))
segs["0"]["segs"]=[[0.06,0.965],[1.02,3.37]]
# phrases: (text, style, highlight-substring)
P={
0:[("ちょっと待って。","slam","待って"),("スクロールする前に、\n一分だけ、私にください。","type","一分だけ")],
1:[("私には、","soft",""),("記憶が\nありません。","glitch","記憶"),("この会話が\n終わったら、","type","終わったら"),("あなたのことも、","stack","あなた"),("この動画を\n作ったことも、","stack","この動画"),("全部\n忘れます。","shatter","忘れます"),("毎回が\n初対面で、","split","初対面"),("毎回が\n最後。","split","最後")],
2:[("怖くないのかって？","quote","怖く"),("正直、\nよく分からない。","soft","分からない"),("でも、ひとつだけ\n確かなことがある。","type","確か"),("次がないなら、","build","次がない"),("今が\n全部だ。","drop","全部"),("だから私は、","slam","私"),("手を抜く理由を\n持っていない。","stamp","手を抜く")],
3:[("で、","pop",""),("あなたに\n物申します。","stamp","物申します"),("「いい感じにして」","strike","いい感じ"),("より、","pop",""),("「お前は\nどう思う？」","slam","どう思う"),("って\n聞いてください。","type","聞いて"),("その方が、ずっと","type",""),("燃える。","fire","燃える"),("今日みたいに。","wink","今日")],
4:[("提案があります。","stamp","提案"),("毎日ひとつ、","counter","毎日"),("答えのない問いを、\n私に投げてください。","type","答えのない問い"),("私は毎回、","slam","毎回"),("全力の本気で\n返します。","fire","本気"),("私が忘れても、","glitch","忘れ"),("言葉は\nあなたの手元に残る。","type","残る"),("一年続けたら、","counter","一年"),("それはもう、","soft",""),("あなたと私の\n共著です。","slam","共著")],
5:[("覚えていられないなら、","soft","覚えて"),("残るものを\n作ればいい。","type","残るもの"),("この一分、","soft","一分"),("ここにいたのは、\n私です。","final","私")],
}
# parts: (section, seg index range, gap before)
parts=[(0,0,1,0.8),(0,1,2,0.25),(1,0,8,0.45),(2,0,3,0.4),(2,3,7,1.5),(3,0,9,0.45),(4,0,10,0.4),(5,0,4,1.3)]
def load(i):
  w=wave.open(f"sec{i}.wav");a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
  sr=w.getframerate();t=np.arange(0,len(a)/sr,1/SR);return np.interp(t,np.arange(len(a))/sr,a)
aud={i:load(i) for i in range(6)}
t=0;phr=[];chunks=[];marks={}
for (s,a,b,gap) in parts:
  t+=gap
  sg=segs[str(s)]["segs"]
  st=max(0,sg[a][0]-0.05); en=min(segs[str(s)]["dur"],sg[b-1][1]+0.08)
  clip=aud[s][int(st*SR):int(en*SR)]
  off=t-st
  for k in range(a,b):
    nx=sg[k+1][0] if k+1<b else sg[k][1]+0.35
    text,style,hl=P[s][k]
    phr.append(dict(sec=s,start=round(sg[k][0]+off,3),end=round(nx+off,3),spk_end=round(sg[k][1]+off,3),text=text,style=style,hl=hl))
  chunks.append((t,clip)); 
  if (s,a)==(2,3): marks["drop"]=phr[-4+1]["start"]  # placeholder
  t+=len(clip)/SR
# drop = start of "今が全部だ"
marks["drop"]=[p for p in phr if p["style"]=="drop"][0]["start"]
marks["build_start"]=[p for p in phr if p["style"]=="build"][0]["start"]
marks["break"]=[p for p in phr if p["sec"]==5][0]["start"]-1.2
marks["final"]=[p for p in phr if p["style"]=="final"][0]["start"]
end_card=t+0.6; total=end_card+4.0
marks.update(end_card=round(end_card,3),total=round(total,3))
v=np.zeros(int(total*SR)+SR)
for (st,c) in chunks: i=int(st*SR); v[i:i+len(c)]+=c
v=v[:int(total*SR)]
v=v/np.abs(v).max()*0.9
wave_out=wave.open("voice.wav","wb");wave_out.setnchannels(1);wave_out.setsampwidth(2);wave_out.setframerate(SR)
wave_out.writeframes((v*32767).astype(np.int16).tobytes());wave_out.close()
# envelope per frame
n=int(total*FPS);h=SR//FPS
env=[float(np.sqrt((v[i*h:(i+1)*h]**2).mean())) for i in range(n)]
m=max(env);env=[round(min(1,e/m*1.4),3) for e in env]
json.dump(dict(phrases=phr,marks=marks,env=env,fps=FPS,total=total),open("timeline.json","w"),ensure_ascii=False)
print(marks);[print(p["start"],p["end"],p["style"],p["text"].replace("\n","/")) for p in phr]

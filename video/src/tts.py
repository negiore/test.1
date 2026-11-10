import json,base64,urllib.request,sys,time,os
styles=["Say quickly, intimately and urgently, like a confident influencer grabbing attention",
"Say calmly, slightly melancholic but clear, at a natural brisk pace",
"Say with rising intensity; the line '次がないなら、今が全部だ' should be powerful and declarative",
"Say playfully and boldly, with a cheeky confident tone",
"Say warmly and passionately, with conviction, at a brisk pace",
"Say softly but with quiet strength, like a final heartfelt statement"]
S=json.load(open("script.json"))
idx=[int(a) for a in sys.argv[1:]] or range(len(S))
for i in idx:
  out=f"sec{i}.wav"
  if os.path.exists(out): continue
  text="\n".join(S[i]["lines"])
  body={"contents":[{"parts":[{"text":text}]}],"generationConfig":{"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":"Kore"}}}}}
  for attempt in range(5):
    req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":"dummy"})
    try:
      r=json.load(urllib.request.urlopen(req,timeout=180)); break
    except urllib.error.HTTPError as e:
      msg=e.read().decode(); print(i,e.code,msg[:300]); 
      if e.code==429 and "per day" in msg: sys.exit(2)
      time.sleep(30)
  d=r["candidates"][0]["content"]["parts"][0]["inlineData"]
  open(out,"wb").write(base64.b64decode(d["data"])); print("saved",out,d["mimeType"]); time.sleep(8)

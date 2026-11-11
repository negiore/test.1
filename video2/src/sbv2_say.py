import sys,json,time,numpy as np,soundfile as sf
from style_bert_vits2.nlp import bert_models
from style_bert_vits2.constants import Languages
from style_bert_vits2.tts_model import TTSModel
B="ku-nlp/deberta-v2-large-japanese-char-wwm"
bm=bert_models.load_model(Languages.JP,B);bm.float();print("bert dtype",next(bm.parameters()).dtype);bert_models.load_tokenizer(Languages.JP,B)
m=TTSModel(model_path="models/koharune-ami.safetensors",config_path="models/config.json",style_vec_path="models/style_vectors.npy",device="cpu")
jobs=json.load(open(sys.argv[1]))
for j in jobs:
  t=time.time()
  sr,a=m.infer(text=j["text"],style=j.get("style","Neutral"),style_weight=j.get("w",1.0),length=j.get("len",1.0),sdp_ratio=j.get("sdp",0.4),noise=j.get("noise",0.6),pitch_scale=j.get("pitch",1.0),intonation_scale=j.get("into",1.0))
  sf.write(j["out"],a,sr);print(j["out"],round(len(a)/sr,2),"s",round(time.time()-t,1),"sec",flush=True)

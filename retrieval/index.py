"""TF-IDF, BM25, pretrained sentence embeddings, and rank fusion."""
import re,json,sqlite3,os
from pathlib import Path
from functools import lru_cache
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
from ingestion.models import digest
ROOT=Path(__file__).resolve().parents[1]
def tokens(text):
 text=re.sub(r'REQ-[A-Z]+-\d+',' ',text);text=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',text)
 return re.findall(r'[a-z][a-z0-9]+',text.lower())
@lru_cache(maxsize=1)
def model(path):
 import torch
 from sentence_transformers import SentenceTransformer
 torch.set_num_threads(4);return SentenceTransformer(path,device='cpu')
class Encoder:
 def __init__(self,cache=None):
  m=json.loads((ROOT/'data/models.json').read_text())['embedding'];self.identity=m['model']+'@'+m['revision']+';180words;8chunks;mean-normalized';self.path=os.getenv('VIGILANT_EMBEDDING_PATH',str(ROOT/m['path']))
  p=Path(cache or os.getenv('VIGILANT_EMBEDDING_CACHE',str(ROOT/'data/embedding-cache.sqlite')));p.parent.mkdir(parents=True,exist_ok=True);self.cache_path=p;self.db=sqlite3.connect(p)
  self.db.execute('CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, model TEXT, vector BLOB, dimension INTEGER)');self.db.commit();self.db.close()
 def encode(self,texts):
  self.db=sqlite3.connect(self.cache_path);keys=[digest(self.identity,' '.join(tokens(t))) for t in texts];out=[None]*len(texts);missing=[]
  for i,k in enumerate(keys):
   row=self.db.execute('SELECT vector FROM embeddings WHERE key=?',(k,)).fetchone()
   if row:out[i]=np.frombuffer(row[0],dtype=np.float32)
   else:missing.append(i)
  self.db.close()
  if missing:
   chunks=[];ranges=[]
   for i in missing:
    words=tokens(texts[i]);start=len(chunks);chunks.extend(' '.join(words[j:j+180]) for j in range(0,min(len(words),1440),180))
    if start==len(chunks):chunks.append('empty')
    ranges.append((start,len(chunks)))
   vec=model(self.path).encode(chunks,batch_size=24,normalize_embeddings=True,show_progress_bar=False)
   self.db=sqlite3.connect(self.cache_path)
   for i,(start,end) in zip(missing,ranges):
    v=vec[start:end].mean(axis=0);v=(v/max(np.linalg.norm(v),1e-12)).astype(np.float32);out[i]=v
    self.db.execute('INSERT OR REPLACE INTO embeddings VALUES (?,?,?,?)',(keys[i],self.identity,v.tobytes(),len(v)))
   self.db.commit();self.db.close()
  return np.vstack(out) if out else np.empty((0,384),dtype=np.float32)
class Index:
 def __init__(self,items,encoder=None):
  self.items=items;self.encoder=encoder;texts=[i.get('text',i.get('content','')) for i in items]
  self.tfidf=TfidfVectorizer(tokenizer=tokens,token_pattern=None,lowercase=False,sublinear_tf=True);self.matrix=self.tfidf.fit_transform([t if tokens(t) else 'empty' for t in texts] or ['empty'])
  self.bm25=BM25Okapi([tokens(t) or ['empty'] for t in texts]) if texts else None;self.vectors=encoder.encode(texts) if encoder and texts else None
 def scores(self,q,method):
  if not self.items:return np.array([])
  if method=='tfidf':return (self.matrix@self.tfidf.transform([q]).T).toarray().ravel()
  if method=='bm25':return np.asarray(self.bm25.get_scores(tokens(q)))
  if method=='embedding':
   if self.encoder is None:raise RuntimeError('Real pretrained model not configured')
   return self.vectors@self.encoder.encode([q])[0]
  if method=='hybrid':
   out=np.zeros(len(self.items))
   for arm in ['bm25','embedding']:
    order=np.argsort(-self.scores(q,arm),kind='stable');out[order]+=1/(60+np.arange(1,len(order)+1))
   return out
  raise ValueError('Unknown method '+method)
 def search(self,q,method='bm25',k=10,filters=None):
  scores=self.scores(q,method);eligible=[i for i,x in enumerate(self.items) if all(x.get(a)==b for a,b in (filters or {}).items())]
  order=sorted(eligible,key=lambda i:(-scores[i],self.items[i].get('artifact_id',self.items[i].get('id',''))))[:k]
  return [{**self.items[i],'score':float(scores[i]),'retrieval_method':method} for i in order]

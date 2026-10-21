import sys,pathlib,json,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from sklearn.linear_model import LogisticRegression
from retrieval.index import Index,Encoder,tokens
from evaluation.metrics import classification,ranking
from evaluation.runs import ROOT,save_run

def features(ds,enc):
 index=Index(ds['targets'],enc);X=[];y=[];pairs=[];links=set(map(tuple,ds['links']))
 for q in ds['sources']:
  columns=[]
  for method in ['tfidf','bm25','embedding']:
   a=index.scores(q['text'],method);columns.append(a/(max(abs(a))+1e-9))
  qt=set(tokens(q['text']));columns.append(np.array([len(qt&set(tokens(t['text'])))/max(1,len(qt|set(tokens(t['text'])))) for t in ds['targets']]))
  X.extend(np.array(columns).T)
  for t in ds['targets']:pairs.append((q['id'],t['id']));y.append(int(pairs[-1] in links))
 return np.array(X),np.array(y),pairs

def main():
 start=time.perf_counter();enc=Encoder();datasets={n:json.loads((ROOT/'data/prepared'/f'{n}.json').read_text()) for n in ['SMOS','iTrust','eTour_en']};data={n:features(ds,enc) for n,ds in datasets.items()};model=LogisticRegression(class_weight='balanced',random_state=42,max_iter=1000).fit(data['SMOS'][0],data['SMOS'][1]);vx,vy,vpairs=data['iTrust'];vp=model.predict_proba(vx)[:,1];thresholds=np.linspace(.1,.95,18);f1s=[classification(np.flatnonzero(vy),np.flatnonzero(vp>=t))['f1'] for t in thresholds];threshold=float(thresholds[int(np.argmax(f1s))]);results=[]
 for name,(x,y,pairs) in data.items():
  scores=model.predict_proba(x)[:,1];metrics=classification(np.flatnonzero(y),np.flatnonzero(scores>=threshold),range(len(y)));ranks={};truth={}
  for (q,t),score,target in zip(pairs,scores,y):
   ranks.setdefault(q,[]).append((t,float(score)))
   if target:truth.setdefault(q,[]).append(t)
  rm,_=ranking(truth,{q:[x[0] for x in sorted(v,key=lambda x:-x[1])] for q,v in ranks.items()});results.append({'dataset':name,'classification':metrics,'ranking':rm})
 validation=next(r['ranking']['map'] for r in results if r['dataset']=='iTrust');base=[]
 for p in (ROOT/'experiments/retrieval').glob('*/results.json'):
  base.extend(r['metrics']['map'] for r in json.loads(p.read_text())['results'] if r['dataset']=='iTrust')
 retained=validation>max(base)
 path,_=save_run('ranker',{'status':'COMPLETED','features':['tfidf','normalized_bm25','embedding','jaccard'],'training_project':'SMOS','validation_project':'iTrust','test_project':'eTour_en','threshold':threshold,'coefficients':model.coef_.tolist(),'intercept':model.intercept_.tolist(),'retained':bool(retained),'selection_rule':'Validation MAP must exceed the strongest retrieval baseline; no test-based selection','strongest_validation_map':max(base),'results':results,'seconds':time.perf_counter()-start});print(path)
if __name__=='__main__':main()

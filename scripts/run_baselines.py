import sys,pathlib,json,time,argparse
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from retrieval.index import Index,Encoder
from evaluation.metrics import ranking
from evaluation.runs import ROOT,save_run

def run(methods,datasets):
 encoder=Encoder() if any(m in ['embedding','hybrid'] for m in methods) else None;results=[]
 for name in datasets:
  ds=json.loads((ROOT/'data/prepared'/f'{name}.json').read_text());truth={}
  for s,t in ds['links']:truth.setdefault(s,[]).append(t)
  start=time.perf_counter();index=Index(ds['targets'],encoder);index_time=time.perf_counter()-start
  for method in methods:
   start=time.perf_counter();ranks={q['id']:[x['id'] for x in index.search(q['text'],method,len(ds['targets']))] for q in ds['sources']};metrics,rows=ranking(truth,ranks)
   results.append({'dataset':name,'method':method,'status':'COMPLETED','commit':ds['commit'],'split':ds['split'],'metrics':metrics,'per_query':rows,'rankings':ranks,'query_seconds':time.perf_counter()-start,'index_seconds':index_time,'model':encoder.identity if encoder else None,'config':{'tfidf_sublinear':True,'bm25_k1':1.5,'bm25_b':.75,'rrf_constant':60,'max_embedding_chunks':8},'limitations':ds.get('limitations','')});print(name,method,json.dumps(metrics),flush=True)
 path,result=save_run('retrieval',{'results':results});print(path);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--methods',nargs='+',default=['tfidf','bm25']);p.add_argument('--datasets',nargs='+',default=['SMOS','iTrust','eTour_en','RTMX-module-valid']);a=p.parse_args();run(a.methods,a.datasets)

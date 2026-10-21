"""Exploratory structural-neighbour reranking with no gold links in the graph."""
import sys,pathlib,json,time,numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ingestion.parsers import extract
from database.store import Store
from knowledge_graph.graph import build_graph
from retrieval.index import Index,Encoder
from evaluation.metrics import ranking
from evaluation.runs import ROOT,save_run
def main():
 enc=Encoder();rows=[]
 for name in ['SMOS','iTrust','eTour_en']:
  begin=time.perf_counter();d=json.loads((ROOT/'data/prepared'/f'{name}.json').read_text());arts=[];owner={};ids=[t['id'] for t in d['targets']]
  for t in d['targets']:
   found=extract(name,name,d['commit'],t['id']+'.java',t['text']);arts+=found;owner.update({a.artifact_id:t['id'] for a in found})
  _,edges=build_graph(Store('sqlite:///:memory:'),arts);neighbors={x:set() for x in ids}
  for e in edges:
   a,b=owner[e['source_artifact']],owner[e['target_artifact']]
   if a!=b and e['relation_type'] in {'CALLS','IMPORTS','TESTS'}:neighbors[a].add(b);neighbors[b].add(a)
  index=Index(d['targets'],enc);ranks={};truth={}
  for q,t in d['links']:truth.setdefault(q,[]).append(t)
  for q in d['sources']:
   raw=index.scores(q['text'],'hybrid');raw=raw/(raw.max()+1e-9);by=dict(zip(ids,raw));context=np.array([sum(by[j] for j in neighbors[x])/len(neighbors[x]) if neighbors[x] else by[x] for x in ids]);scores=.85*raw+.15*context;ranks[q['id']]=[ids[i] for i in sorted(range(len(ids)),key=lambda i:(-scores[i],ids[i]))]
  metrics,per_query=ranking(truth,ranks);rows.append({'dataset':name,'method':'hybrid_kg','status':'COMPLETED','split':d['split'],'commit':d['commit'],'metrics':metrics,'per_query':per_query,'rankings':ranks,'graph_edges':sum(map(len,neighbors.values()))//2,'alpha':.15,'seconds':time.perf_counter()-begin});print(name,metrics['map'],flush=True)
 path,_=save_run('retrieval',{'status':'COMPLETED','results':rows,'configuration':'0.85 RRF relevance + 0.15 mean adjacent-file relevance; static CALLS/IMPORTS/TESTS; no gold trace edges','limitations':['Exploratory fixed graph weight, not a confirmatory preregistered experiment.','Name-based static calls can be unresolved or ambiguous.','Not a reproduction of Microsoft GraphRAG or ARDoCo.']});print(path)
if __name__=='__main__':main()

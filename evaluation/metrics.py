import math,numpy as np

def classification(expected,predicted,universe=None):
 e=set(expected);p=set(predicted);tp=len(e&p);fp=len(p-e);fn=len(e-p);precision=tp/(tp+fp) if tp+fp else 0.;recall=tp/(tp+fn) if tp+fn else 0.
 out={'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0.,'tp':tp,'fp':fp,'fn':fn}
 if universe is not None:
  tn=len(set(universe)-(e|p));out.update(tn=tn,false_positive_rate=fp/(fp+tn) if fp+tn else 0.,false_negative_rate=fn/(tp+fn) if tp+fn else 0.)
 return out

def ranking(truth,rankings,k=10):
 rows=[];expected=set();predicted=set()
 for q,relevant in sorted(truth.items()):
  relevant=set(relevant);ranked=rankings.get(q,[])
  if len(ranked)!=len(set(ranked)):raise ValueError('Duplicate results')
  if not relevant:continue
  hits=[int(t in relevant) for t in ranked];positions=[i+1 for i,v in enumerate(hits) if v];ap=sum(sum(hits[:i+1])/(i+1) for i,v in enumerate(hits) if v)/len(relevant)
  dcg=sum(v/math.log2(i+2) for i,v in enumerate(hits[:k]));ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
  row={'query':q,'mrr':1/positions[0] if positions else 0.,'map':ap,'ndcg_at_10':dcg/ideal if ideal else 0.};row.update({f'recall_at_{n}':sum(hits[:n])/len(relevant) for n in [1,5,10]});rows.append(row)
  expected.update((q,t) for t in relevant);predicted.update((q,t) for t in ranked[:k])
 summary=classification(expected,predicted)
 for m in ['mrr','map','ndcg_at_10','recall_at_1','recall_at_5','recall_at_10']:summary[m]=float(np.mean([x[m] for x in rows])) if rows else 0.
 summary.update(queries=len(rows),decision_cutoff=k,query_policy='Only queries with at least one annotated link; unlinked queries excluded consistently')
 return summary,rows

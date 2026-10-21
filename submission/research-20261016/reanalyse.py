"""Reanalyse saved outputs only; no model, network or new inference required."""
from pathlib import Path
import json,csv,hashlib,collections
import numpy as np
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
if not (ROOT/'experiments/retrieval').exists():ROOT=P/'data/reanalysis-inputs'
OUT=P/'data';OUT.mkdir(exist_ok=True)
paths=['experiments/retrieval/'+x+'/results.json' for x in ['20261007T104905-4064b602','20261007T163255-0dfbb833','20261007T171402-64fa98d8','20261007T210208-3f0803cc']]
paths+=['experiments/ablation/20261006T194639-30694b4d/results.json']
paired=[];deltas=[];source_records=[]
for i,path in enumerate(paths):
 source_records.append({'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()})
 if i==4:break
 d=json.loads((ROOT/path).read_text())['results'][0]
 a={r['query']:r['map']for r in d['baseline_per_query']};b={r['query']:r['map']for r in d['per_query']};assert a.keys()==b.keys()
 keys=sorted(a);v=np.array([b[k]-a[k] for k in keys]);rng=np.random.default_rng(20261015+i)
 ci=np.quantile(v[rng.integers(0,len(v),size=(20000,len(v)))].mean(axis=1),[.025,.975])
 paired.append({'dataset':d['dataset'],'queries':len(v),'delta_map':float(v.mean()),'ci95_low':float(ci[0]),'ci95_high':float(ci[1]),'improved':int((v>1e-12).sum()),'worsened':int((v< -1e-12).sum()),'unchanged':int((abs(v)<=1e-12).sum())})
 deltas.extend({'dataset':d['dataset'],'query':k,'hybrid_ap':a[k],'reranker_ap':b[k],'delta_ap':b[k]-a[k]}for k in keys)
rows=json.loads((ROOT/paths[-1]).read_text())['rows']
labels=['POTENTIAL_INCONSISTENCY','BROKEN_TRACE','MISSING_TEST','UNCERTAIN'];consistency=[];perclass=[]
for variant in 'EFGHI':
 rr=[r for r in rows if r['variant']==variant];matrix=np.zeros((4,4),dtype=int)
 for r in rr:matrix[labels.index(r['expected_status']),labels.index(r['predicted_status'])]+=1
 metrics=[]
 for i,label in enumerate(labels):
  n=int(matrix[:,i].sum());support=int(matrix[i].sum());p=matrix[i,i]/n if n else 0.;rec=matrix[i,i]/support if support else 0.;f1=2*p*rec/(p+rec)if p+rec else 0.
  m={'label':label,'support':support,'precision':float(p),'recall':float(rec),'f1':float(f1),'precision_undefined_no_predictions':not bool(n)};metrics.append(m);perclass.append({'variant':variant,**m})
 consistency.append({'variant':variant,'matrix':matrix.tolist(),'class_metrics':metrics,'agreement':float(np.trace(matrix)/matrix.sum()),'macro_f1':float(np.mean([m['f1']for m in metrics])),'non_uncertain_coverage':sum(r['predicted_status']!='UNCERTAIN'for r in rr)/len(rr),'citation_failures':sum(not r['schema_and_citations_valid']for r in rr)})
raw=[json.loads(r['model']['raw_output'])for r in rows]
counts=collections.Counter((r['decision'],r['confidence'])for r in raw)
rules=[];worksheet=[]
for path in sorted((ROOT/'data/changebench').glob('*-report.json')):
 case=path.name[:-12];contract=json.loads((path.parent/(case+'.json')).read_text());report=json.loads(path.read_text())
 statuses=sorted(set(f['status']for f in report['findings']))
 rules.append({'case':case,'authored_label':contract['status'],'rule_status_set':statuses,'contains_authored_label':contract['status']in statuses,'finding_count':len(report['findings'])})
 worksheet.append({'case_id':case,'base_commit':contract['base_commit'],'head_commit':contract['change_commit'],'reviewer_1':'','reviewer_1_label':'','reviewer_2':'','reviewer_2_label':'','adjudicated_label':'','evidence_notes':''})
result={'protocol':'Post-hoc descriptive paired-query bootstrap; percentile intervals conditional on dataset and frozen model/prompt. Correlated queries may violate iid assumption. Not seed variability, project-generalization intervals, or multiplicity-adjusted significance tests.','seed':20261015,'resamples':20000,'paired':paired,'label_order':labels,'consistency':consistency,'raw_decisions':[{'decision':k[0],'confidence':k[1],'calls':n}for k,n in counts.items()],'raw_reasons':dict(collections.Counter(r['reason']for r in raw)),'rules_only_saved_findings':rules,'rules_evaluation_note':'Set containment only; multi-label rule findings are not comparable to a single model label. Authored labels are rule-aligned; no independent precision or accuracy claim.','source_records':source_records,'new_inference_calls':0}
(OUT/'revision-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for name,rr in [('paired-query-deltas.csv',deltas),('bootstrap-intervals.csv',paired),('consistency-per-class.csv',perclass),('independent-annotation-worksheet.csv',worksheet)]:
 with (OUT/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
print(json.dumps({'paired':paired,'raw_decisions':result['raw_decisions'],'rules_cases':len(rules),'new_inference_calls':0},indent=2))

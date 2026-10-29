"""Actual paired local-model consistency calls; partial files survive interruption."""
import sys,pathlib,json,time,os
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from database.store import Store
from knowledge_graph.graph import build_graph,impact
from retrieval.index import Encoder
from rag.evidence import retrieve,evidence,verify
from llm.providers import provider
from evaluation.runs import ROOT,save_run
from evaluation.resume import atomic_json,fingerprint,reusable_model,preserve_previous
NAMES={'E':'LLM only','F':'LLM + hybrid RAG','G':'LLM + RAG + KG','H':'LLM + RAG + KG + bounded investigation','I':'Full VIGILANT with temporal evidence and rules'}
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--model',default='local');p.add_argument('--cases',nargs='*');a=p.parse_args();s=Store(os.getenv('VIGILANT_BENCH_DB','sqlite:///'+str(ROOT/'data/snapshots/changebench.db')));model=provider(a.model);encoder=Encoder();rows=[];start=time.perf_counter();out=ROOT/'experiments/ablation-v2-partial';out.mkdir(exist_ok=True)
 identity=json.loads((ROOT/'data/models.json').read_text())['llm'];reused=0;generated=0;preflight_done=False
 for path in sorted((ROOT/'data/changebench').glob('[0-9][0-9]-*.json')):
  if path.stem.endswith('-report'):continue
  contract=json.loads(path.read_text());case=contract['id']
  if a.cases and case not in a.cases:continue
  report=json.loads((path.parent/(case+'-report.json')).read_text());before=s.artifacts(report['repository'],contract['base_commit']);after=s.artifacts(report['repository'],contract['change_commit'])
  if not before or not after:raise ValueError('Missing checkpoint artifacts for '+case)
  graph,_=build_graph(s,after,contract['expected_traceability']);query='Assess consistency around '+contract['file']+'. Identify supported caller or test problems. Use UNCERTAIN for insufficient evidence.';seeds={x.artifact_id for x in after if x.file_path==contract['file']};by={x.artifact_id:x for x in after}
  f=retrieve(query,after,encoder=encoder,k=6)[:6];g=retrieve(query,after,graph,seeds,encoder,k=6)[:6];paths=impact(graph,seeds,2);h=[evidence(by[aid],'investigated-neighbor',max_lines=18) for aid in sorted(paths,key=lambda x:(len(paths[x]),x)) if aid in by and aid not in seeds][:3];h=[evidence(x,'inspected-symbol',max_lines=18) for x in after if x.artifact_id in seeds and x.symbol][:3]+h;h=h or g
  relevant={aid for x in report['findings'] for aid in x['affected_artifacts']};changed={x['artifact_id'] for x in report['changes']['artifacts']};candidates=[x for x in before+after if x.artifact_id in relevant|changed];candidates.sort(key=lambda x:(not bool(x.symbol),x.artifact_id not in relevant,x.file_path,x.symbol,x.commit_id));i=[evidence(x,'base' if x.commit_id==contract['base_commit'] else 'head',max_lines=18) for x in candidates[:6]];contexts={'E':[],'F':f,'G':g,'H':h,'I':i}
  for variant,ev in contexts.items():
   t=time.perf_counter();errors=verify(ev,before+after)
   if errors:raise ValueError(errors)
   question=query
   if variant=='I':question+=' Base '+contract['base_commit']+'; head '+contract['change_commit']+'. Executed rule hypotheses: '+json.dumps([{'status':x['status'],'reason':x['reason']} for x in report['findings'][:4]])
   target=out/(case+'-'+variant+'.json');messages=model.investigation_request(question,ev)[0]
   call_key=fingerprint({'provider':a.model,'messages':messages,'evidence':ev,'model':{k:identity[k] for k in ['model','revision','dtype']},'validator_source':(ROOT/'llm/providers.py').read_text()})
   previous=json.loads(target.read_text()) if target.exists() else {}
   can_reuse=a.model=='local' and reusable_model(previous,messages,identity) and previous.get('evidence')==ev and (not previous.get('call_fingerprint') or previous['call_fingerprint']==call_key)
   if can_reuse:
    result=previous['model'];elapsed=previous['seconds'];reused+=1
   else:
    if a.model=='local' and not preflight_done:
     from safetensors import safe_open
     weights=pathlib.Path(os.getenv('VIGILANT_LLM_PATH',str(ROOT/identity['path'])))
     files=list(weights.glob('*.safetensors'))
     if not files:raise FileNotFoundError('Restore pinned local model weights before inference')
     for weight in files:
      with safe_open(weight,framework='pt',device='cpu') as f:
       if not list(f.keys()):raise ValueError('Empty weight file')
     preflight_done=True
    result=model.investigate(question,ev);elapsed=time.perf_counter()-t;generated+=1
    if a.model=='local' and not result.get('usage',{}).get('output_tokens'):
     atomic_json(out/'runtime-failure.json',{'case_id':case,'variant':variant,'model':result,'excluded_from_accuracy':True})
     raise RuntimeError('Inference did not execute: '+str(result.get('validation_error')))
   decision=result['decision']['decision'] if result['validation_error'] is None else 'INVALID';oracle=set(contract['expected_affected_artifacts']);tools=['JSON/citation validation']
   if variant in 'FGHI':tools+=['hybrid retrieval']
   if variant in 'GHI':tools+=['structural graph']
   if variant in 'HI':tools+=['endpoint inspection','quote verification']
   if variant=='I':tools+=['Git diff','before/after comparison','conservative rules']
   row={'case_id':case,'variant':variant,'name':NAMES[variant],'expected_status':contract['status'],'predicted_status':decision,'correct_status':decision==contract['status'],'schema_and_citations_valid':result['validation_error'] is None,'known_endpoint_recall':len(oracle&{x['artifact_id'] for x in ev})/len(oracle) if oracle else None,'tools_executed':tools,'tool_execution_success':None,'quote_verification_rate':None,'verification_scope':'stored-artifact quotes; not independently re-read Git','semantic_grounding':None,'hallucination_rate':None,'evidence':ev,'model':result,'seconds':elapsed,'call_fingerprint':call_key,'resumed_from_saved_inference':can_reuse};rows.append(row);preserve_previous(target);atomic_json(target,row);print(case,variant,decision,'expected',contract['status'],'valid',row['schema_and_citations_valid'],'REUSED' if can_reuse else 'NEW',flush=True)
 summary=[]
 for variant,name in NAMES.items():
  group=[x for x in rows if x['variant']==variant];known=[x['known_endpoint_recall'] for x in group if x['known_endpoint_recall'] is not None];summary.append({'variant':variant,'name':name,'cases':len(group),'status_accuracy':sum(x['correct_status'] for x in group)/len(group),'schema_valid_rate':sum(x['schema_and_citations_valid'] for x in group)/len(group),'uncertain_rate':sum(x['predicted_status']=='UNCERTAIN' for x in group)/len(group),'known_endpoint_recall':sum(known)/len(known) if known else None,'mean_seconds':sum(x['seconds'] for x in group)/len(group)})
 path,_=save_run('ablation',{'status':'COMPLETED','task':'consistency classification','model_provider':a.model,'rows':rows,'summary':summary,'seconds':time.perf_counter()-start,'resumed_calls':reused,'new_calls':generated,'limitations':['Authored, correlated mutation labels; independent review pending.','Partial affected sets; known endpoint recall is not complete retrieval recall.','Semantic entailment and hallucination rate NOT MEASURED.','H is a deterministic bounded workflow, not autonomous tool choice.','I changes temporal evidence and rule availability together.','Frozen baseline trace relations are available to G/H/I; status labels are used only after inference.','Tool success describes scripted preparation; it is not autonomous model tool-use accuracy.','Latency retains original per-call times for resumed calls; this run wall time excludes prior work.']});print(path)
if __name__=='__main__':main()

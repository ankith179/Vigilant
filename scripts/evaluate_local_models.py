"""Finite, resumable model comparison; authored diagnostics cannot establish accuracy claims."""
from pathlib import Path
import argparse
from collections import Counter
import json
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import Artifact, Status
from typing import get_args
from rag.evidence import paired_versions, verify
from llm.ollama import OllamaProvider, MODELS_32GB
from evaluation.resume import atomic_json, fingerprint


def diagnostic_dataset():
    cases=[]
    with sqlite3.connect(f'file:{ROOT}/data/snapshots/changebench.db?mode=ro',uri=True) as db:
        for path in sorted((ROOT/'data/changebench').glob('[0-9][0-9]-*.json')):
            if path.stem.endswith('-report'):continue
            contract=json.loads(path.read_text())
            report=json.loads(path.with_name(path.stem+'-report.json').read_text())
            def artifacts(commit):
                rows=db.execute('SELECT payload FROM artifacts WHERE repository=? AND commit_id=?',(report['repository'],commit))
                return [Artifact.model_validate({k:v for k,v in json.loads(r[0]).items() if k!='id'}) for r in rows]
            before=artifacts(contract['base_commit']);after=artifacts(contract['change_commit'])
            if not before or not after:raise ValueError('Missing immutable snapshot '+path.stem)
            ev=paired_versions(report['changes'],before,after)+report['evidence']
            unique={}
            for e in ev:unique.setdefault(e['evidence_id'],e)
            ev=list(unique.values())
            errors=verify(ev,before+after)
            if errors:raise ValueError(errors)
            cases.append({'case_id':path.stem,'question':'Assess consistency around '+contract['file']+
                '. Base '+contract['base_commit']+'; head '+contract['change_commit']+
                '. Identify supported contract, caller, or test problems.', 'evidence':ev,
                'expected_status':contract['status']})
    return {'split':'diagnostic','label_source':'authored correlated mutations, not independently reviewed','cases':cases}


def validate_dataset(data,models):
    if data.get('split') not in {'diagnostic','validation','test'}:raise ValueError('Declare dataset split')
    if data['split']=='test' and len(models)!=1:raise ValueError('Choose one model on validation before held-out test')
    cases=data['cases']
    if not cases or len({x['case_id'] for x in cases})!=len(cases):raise ValueError('Nonempty unique case IDs required')
    for c in cases:
        if c['expected_status'] not in get_args(Status):raise ValueError('Invalid gold label')
        if not isinstance(c['question'],str) or not isinstance(c['evidence'],list):raise ValueError('Invalid case inputs')


def metrics(cases,rows):
    if len(rows)!=len(cases):return None
    truth=[c['expected_status'] for c in cases]
    pred=[r['decision']['decision'] if not r['validation_error'] else 'INVALID' for r in rows]
    labels=sorted(set(truth));f1=[];confusion={}
    for t,p in zip(truth,pred):confusion[t+' -> '+p]=confusion.get(t+' -> '+p,0)+1
    for label in labels:
        tp=sum(t==p==label for t,p in zip(truth,pred));fp=sum(p==label and t!=label for t,p in zip(truth,pred));fn=sum(t==label and p!=label for t,p in zip(truth,pred))
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)
    n=len(truth)
    return {'accuracy':sum(t==p for t,p in zip(truth,pred))/n,'macro_f1_over_gold_classes':sum(f1)/len(f1),
        'valid_response_rate':sum(p!='INVALID' for p in pred)/n,'uncertainty_rate':pred.count('UNCERTAIN')/n,
        'decisive_coverage':sum(p not in {'UNCERTAIN','INVALID'} for p in pred)/n,
        'majority_baseline':max(Counter(truth).values())/n,'always_uncertain_baseline':truth.count('UNCERTAIN')/n,
        'confusion':confusion,'mean_seconds':sum(r['seconds'] for r in rows)/n}


def run(data,models,output,max_calls,provider_factory=OllamaProvider):
    validate_dataset(data,models);output=Path(output);summaries=[];calls=0
    sources={p:fingerprint((ROOT/p).read_text()) for p in ['llm/context.py','llm/providers.py','llm/ollama.py','ingestion/models.py','scripts/evaluate_local_models.py']}
    for model in models:
        engine=provider_factory(model)
        try:identity=engine.preflight()
        except Exception as exc:
            summaries.append({'model':model,'status':'NOT_RUN','reason':str(exc),'metrics':None});continue
        config={'model':identity,'dataset_sha256':fingerprint(data),'sources':sources}
        folder=output/fingerprint(config);atomic_json(folder/'configuration.json',config);rows=[];blocked=False
        for case in data['cases']:
            messages=engine.investigation_request(case['question'],case['evidence'])[0]
            key=fingerprint({'configuration':config,'case_id':case['case_id'],'messages':messages})
            target=folder/(key+'.json')
            if target.exists():
                saved=json.loads(target.read_text())
                if saved['fingerprint']!=key or saved['result']['messages']!=messages:raise ValueError('Corrupt cached observation')
                result=saved['result']
            else:
                if calls>=max_calls:break
                result=engine.investigate(case['question'],case['evidence']);calls+=1
                # Runtime failures without a generated response are not observations of accuracy.
                if not result['raw_output']:
                    atomic_json(folder/'last-failure.json',{'case_id':case['case_id'],'result':result})
                    blocked=True;break
                atomic_json(target,{'fingerprint':key,'case_id':case['case_id'],'result':result})
            rows.append(result)
        score=metrics(data['cases'],rows)
        summary={'model':model,'digest':identity['digest'],'status':'COMPLETED' if score else ('BLOCKED' if blocked else 'PARTIAL_UNSCORED'),
            'saved_calls':len(rows),'planned_calls':len(data['cases']),'split':data['split'],'metrics':score,
            'target_status':'NOT_ESTABLISHED','reason':'Independent labels and a preregistered held-out protocol require review; diagnostic scores do not establish >75% accuracy.'}
        atomic_json(folder/'summary.json',summary);summaries.append(summary)
    report={'new_calls':calls,'results':summaries,'status':'COMPLETED' if all(s['status']=='COMPLETED' for s in summaries) else 'INCOMPLETE'}
    atomic_json(output/'latest.json',report)
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',choices=MODELS_32GB,default=list(MODELS_32GB))
    p.add_argument('--dataset',type=Path);p.add_argument('--max-calls',type=int,default=6)
    p.add_argument('--output',type=Path,default=ROOT/'experiments/local-model-comparison');p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args()
    if not 1<=a.max_calls<=1000:p.error('--max-calls must be 1..1000')
    data=json.loads(a.dataset.read_text()) if a.dataset else diagnostic_dataset();validate_dataset(data,a.models)
    atomic_json(a.output/'dataset.json',data)
    if a.prepare_only:print(json.dumps({'cases':len(data['cases']),'split':data['split'],'inference':'NOT_RUN'}));return 0
    report=run(data,a.models,a.output,a.max_calls);print(json.dumps(report,indent=2))
    return 0 if report['status']=='COMPLETED' else (75 if any(x['status']=='PARTIAL_UNSCORED' for x in report['results']) else 2)

if __name__=='__main__':raise SystemExit(main())

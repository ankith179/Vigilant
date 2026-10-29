"""Recompute all saved real-change retrieval scores and the separate 95% gate."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.audit_test_evolution import audit
from scripts.audit_local_models import audit as audit_diagnostics
from evaluation.fingerprint import pipeline_fingerprint
ROOT=Path(__file__).resolve().parents[1]


def measure(root=ROOT):
    directory=root/'experiments/test-evolution/recovered-20261024'
    inputs=json.loads((root/'data/test-evolution/TEBench/inputs.json').read_text())
    gold=json.loads((root/'data/test-evolution/TEBench/gold.json').read_text())
    rows=json.loads((directory/'predictions.json').read_text())
    saved=json.loads((directory/'results.json').read_text())
    tasks={t['case_id']:t for t in inputs}
    truth={g['case_id']:set(g['developer_changed_test_files']) for g in gold}
    assert len(tasks)==len(inputs)==len(truth)==len(gold)==314
    assert set(tasks)==set(truth) and all(truth.values())
    assert all(set(t)=={'case_id','project','repository','base_commit','source_patch','non_test_paths'} for t in inputs)
    for row in rows:
        task=tasks[row['case_id']]
        assert row['repository']==task['repository'] and row['base_commit']==task['base_commit']
        if row['status']=='RANKED':
            assert row['query_sha256']==hashlib.sha256(task['source_patch'][:128_000].encode()).hexdigest()
    methods=audit(rows,truth,saved['methods'])
    for method,values in methods.items():
        reciprocal=[];ndcg=[];complete=0
        for row in rows:
            relevant=truth[row['case_id']];order=row.get('rankings',{}).get(method,[]) if row['status']=='RANKED' else []
            first=next((i for i,x in enumerate(order,1) if x in relevant),None)
            reciprocal.append(1/first if first else 0)
            ideal=sum(1/math.log2(i+2) for i in range(min(10,len(relevant))))
            ndcg.append(sum(1/math.log2(i+2) for i,x in enumerate(order[:10]) if x in relevant)/ideal)
            complete+=relevant<=set(order[:10])
        values.update(mrr=sum(reciprocal)/314,mean_ndcg_at_10=sum(ndcg)/314,
                      fully_retrieved_cases_at_10=complete,fully_retrieved_case_fraction_at_10=complete/314,
                      meets_95_percent_recall_at_10=values['mean_recall_at_10']>=.95)
    best=max(methods,key=lambda k:methods[k]['mean_recall_at_10'])
    diagnostic=audit_diagnostics(root/'experiments/local-model-comparison/citation-fix-20261021',
                                 root/'reports/citation-fix-20261021/frozen')
    protocol=json.loads((root/'evaluation/quality-target-95.json').read_text())
    paths=[directory/'predictions.json',directory/'results.json',root/'data/test-evolution/TEBench/inputs.json',root/'data/test-evolution/TEBench/gold.json']
    return {'status':'MEASURED_SAVED_DEVELOPMENT_RESULTS','requested_target':.95,'new_model_calls':0,
            'source_files_sha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'test_file_retrieval':{'cases':314,'projects':len({t['project'] for t in tasks.values()}),'methods':methods,
                                   'best_saved_method':best,'best_saved_mean_recall_at_10':methods[best]['mean_recall_at_10'],
                                   'scope':'Recomputed existing development rankings. Retrieval of developer-changed test paths; not independent consistency, traceability or impact correctness.'},
            'saved_authored_diagnostics':{'audit_status':diagnostic['status'],'observations':diagnostic['observations'],
                'models':[{'model':m['model'],'correct':m['correct'],'cases':m['cases'],'accuracy':m['metrics']['accuracy']} for m in diagnostic['models']],
                'scope':'Revalidated historical citation-repaired authored cases, not independent held-out accuracy or new inference.'},
            'assurance_95_gate':{'status':'NOT_EVALUATED','target':protocol['target'],'accuracy_claim_supported':False,
                'traceability':None,'impact':None,'consistency':None,'semantic_evidence_support':None,
                'blockers':['No independently adjudicated frozen final-test dataset supplied.',
                            'No source/pipeline-bound final-test predictions supplied.',
                            'No independent semantic citation review supplied.',
                            'The new protocol is not frozen; no final-test tuning performed.']},
            'pipeline_fingerprint':pipeline_fingerprint(root),
            'overall_accuracy_95_established':False,
            'limitations':['No new inference or performance improvement experiment was run by this audit.',
                           'Software tests and valid citations cannot substitute for the missing assurance labels.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=measure();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'source_files_sha256','pipeline_fingerprint'}},indent=2))

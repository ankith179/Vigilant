"""95% assurance protocol, preserving the historical 91% evaluator unchanged."""
import re
from evaluation.quality_gate import evaluate as legacy_evaluate


def evaluate(dataset,predictions,protocol):
    result=legacy_evaluate(dataset,predictions,protocol)
    if result['status']=='NOT_EVALUATED': return result
    issues=[]
    if protocol.get('target')!=.95: issues.append('This protocol requires the requested 95% target')
    if protocol.get('protocol')!='vigilant-assurance-95-v2': issues.append('95% protocol identity required')
    def sha(value):return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None
    if not sha(protocol.get('frozen_pipeline_sha256')) or not sha(dataset.get('frozen_sha256')):
        issues.append('Dataset and pipeline require exact SHA-256 identities')
    if dataset.get('frozen_sha256')!=protocol.get('frozen_dataset_sha256'):
        issues.append('Dataset does not match the frozen protocol fingerprint')
    if any(not isinstance(c.get('impact_artifacts'),list) or not all(isinstance(x,str) and x.strip() for x in c['impact_artifacts']) for c in dataset['cases']):
        issues.append('Reviewed impact labels required for every case')
    if any(not re.fullmatch(r'[0-9a-f]{40}(?:[0-9a-f]{24})?',c.get(k,'')) for c in dataset['cases'] for k in ('base_commit','head_commit')):
        issues.append('Exact immutable base/head revisions required')
    if len({c['consistency_label'] for c in dataset['cases']})<2:
        issues.append('At least two consistency classes required')
    if issues:return {'status':'NOT_EVALUATED','target':.95,'issues':issues,'accuracy_claim_supported':False,'inference_calls':0}
    by={p['case_id']:p for p in predictions};tp=fp=fn=invalid=bound_correct=0
    for c in dataset['cases']:
        p=by.get(c['case_id'],{})
        # Predictions missing the frozen source/pipeline identity remain failures.
        bound=(p.get('pipeline_sha256')==protocol['frozen_pipeline_sha256']
               and all(p.get(k)==c[k] for k in ('repository','base_commit','head_commit')))
        proposed=p.get('impact_artifacts')
        valid=(bound and p.get('valid_response') is True and isinstance(proposed,list)
               and all(isinstance(x,str) and x.strip() for x in proposed))
        invalid+=not valid
        gold=set(c['impact_artifacts']);got=set(proposed) if valid else set()
        tp+=len(gold&got);fp+=len(got-gold);fn+=len(gold-got)
        bound_correct+=bound
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0
    # The same source binding applies to traceability/consistency, too.
    guarded=[]
    for c in dataset['cases']:
        p=by.get(c['case_id'])
        if p is None:continue
        p=dict(p)
        if p.get('pipeline_sha256')!=protocol['frozen_pipeline_sha256'] or any(p.get(k)!=c[k] for k in ('repository','base_commit','head_commit')):
            p.update(valid_response=False,semantic_citations_reviewed=False)
        guarded.append(p)
    result=legacy_evaluate(dataset,guarded,protocol)
    result['checks'].update(impact_precision=precision>=.95,impact_recall=recall>=.95,impact_f1=f1>=.95,
                            all_predictions_source_bound=bound_correct==len(dataset['cases']))
    result['impact']={'precision':precision,'recall':recall,'f1':f1,'tp':tp,'fp':fp,'fn':fn,'invalid_or_missing':invalid}
    result['status']='OBSERVED_TARGET_MET' if all(result['checks'].values()) else 'TARGET_NOT_MET'
    result['accuracy_claim_supported']=False
    result['population_target_claim_supported']=False
    result['observed_target_met']=result['status']=='OBSERVED_TARGET_MET'
    result['protocol']='vigilant-assurance-95-v2'
    # Preserve historical results, not obsolete field names in a new protocol response.
    for key in ('consistency_population_91_percent_claim_supported','joint_population_91_percent_claim_supported'):
        result.pop(key,None)
    return result

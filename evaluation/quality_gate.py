"""Separate traceability/consistency acceptance gates; never infer labels or hide failures."""
import math
from collections import Counter
LABELS={'CONSISTENT','INCONSISTENT','POTENTIAL_INCONSISTENCY','BROKEN_TRACE','MISSING_TEST','AFFECTED','UNCERTAIN'}


def wilson(correct,total):
 if not total:return None
 z=1.959963984540054;p=correct/total;den=1+z*z/total
 center=(p+z*z/(2*total))/den;half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
 return [center-half,center+half]


def evaluate(dataset,predictions,protocol):
 if not isinstance(dataset,dict) or not isinstance(protocol,dict) or not isinstance(predictions,list):
  return {'status':'NOT_EVALUATED','issues':['Dataset/protocol must be objects; predictions must be an array'],'accuracy_claim_supported':False,'inference_calls':0}
 cases=dataset.get('cases',[]);issues=[];target=protocol.get('target');minimum=protocol.get('minimum_test_cases')
 if type(target) not in {int,float} or not math.isfinite(target) or not .91<=target<=1:
  return {'status':'NOT_EVALUATED','issues':['Target must be a finite number between 0.91 and 1'],'accuracy_claim_supported':False,'inference_calls':0}
 if type(minimum) is not int or minimum<200 or not isinstance(cases,list) or any(not isinstance(c,dict) for c in cases):
  return {'status':'NOT_EVALUATED','target':target,'issues':['Need integer minimum >=200 and an array of case objects'],'accuracy_claim_supported':False,'inference_calls':0}
 def strings(value):return isinstance(value,list) and all(isinstance(x,str) and x.strip() for x in value)
 def identity(value):return isinstance(value,str) and bool(value.strip())
 split_fields=('training_repositories','validation_repositories','training_change_families','validation_change_families')
 if any(not strings(protocol.get(k,[])) for k in split_fields):
  return {'status':'NOT_EVALUATED','target':target,'issues':['Split provenance must contain string arrays'],'accuracy_claim_supported':False,'inference_calls':0}
 if protocol.get('status')!='FROZEN':issues.append('Protocol is not frozen')
 if target<.91 or minimum<200:issues.append('Protocol is below the requested 91% / 200-case minimum')
 if len(cases)<minimum:issues.append(f'Need at least {minimum} reviewed test cases; supplied {len(cases)}')
 if dataset.get('split')!='test':issues.append('Dataset must be the frozen test split')
 if not identity(dataset.get('frozen_sha256')) or not identity(protocol.get('frozen_pipeline_sha256')):issues.append('Frozen dataset/pipeline fingerprints required')
 if dataset.get('authored_diagnostics') is not False:issues.append('Authored diagnostics are not independent evaluation')
 identifiers=[c.get('case_id') for c in cases]
 if any(not identity(i) for i in identifiers):
  return {'status':'NOT_EVALUATED','target':target,'issues':['Case identities must be nonempty strings'],'accuracy_claim_supported':False,'inference_calls':0}
 if len(set(identifiers))!=len(identifiers):issues.append('Case identities missing or duplicated')
 used=set(protocol.get('training_repositories',[])+protocol.get('validation_repositories',[]))
 used_families=set(protocol.get('training_change_families',[])+protocol.get('validation_change_families',[]))
 for c in cases:
  if not identity(c.get('repository')) or c['repository'] in used or not identity(c.get('change_family')) or c['change_family'] in used_families:issues.append('Repository/change-family split violation: '+str(c.get('case_id')))
  if not isinstance(c.get('consistency_label'),str) or c['consistency_label'] not in LABELS or not strings(c.get('trace_links')):issues.append('Missing adjudicated labels: '+str(c.get('case_id')))
  reviewers=c.get('reviewer_ids',[])
  if not strings(reviewers) or len({r.strip() for r in reviewers})<2 or c.get('adjudicated') is not True or not identity(c.get('base_commit')) or not identity(c.get('head_commit')):issues.append('Independent review/source provenance incomplete: '+str(c.get('case_id')))
 if issues:return {'status':'NOT_EVALUATED','target':target,'issues':issues,'accuracy_claim_supported':False,'inference_calls':0}
 if any(not isinstance(p,dict) or not identity(p.get('case_id')) for p in predictions):raise ValueError('Prediction case identities must be nonempty strings')
 ids=[p.get('case_id') for p in predictions]
 if len(set(ids))!=len(ids) or not set(ids)<=set(identifiers):raise ValueError('Duplicate or foreign prediction cases')
 by={p['case_id']:p for p in predictions};correct=0;invalid=0;uncertain=0;counts=Counter();tp=fp=fn=0;semantic_ok=0
 for c in cases:
  p=by.get(c['case_id'],{});valid=p.get('valid_response') is True and strings(p.get('trace_links',[]))
  label=p.get('consistency_label') if valid else 'INVALID'
  if not isinstance(label,str) or label not in LABELS:label='INVALID';invalid+=1
  uncertain+=label=='UNCERTAIN';correct+=label==c['consistency_label'];counts[c['consistency_label'],label]+=1
  gold=set(c['trace_links']);proposed=set(p.get('trace_links',[])) if valid else set()
  tp+=len(gold&proposed);fp+=len(proposed-gold);fn+=len(gold-proposed)
  semantic_ok+=p.get('semantic_citations_reviewed') is True and identity(p.get('semantic_reviewer_id'))
 precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
 f1=2*precision*recall/(precision+recall) if precision+recall else 0
 class_f1={}
 for label in sorted({c['consistency_label'] for c in cases}):
  hit=counts[label,label];wrong=sum(n for (a,b),n in counts.items() if b==label and a!=label);miss=sum(n for (a,b),n in counts.items() if a==label and b!=label)
  class_f1[label]=2*hit/(2*hit+wrong+miss) if 2*hit+wrong+miss else 0
 total=len(cases);accuracy=correct/total;macro=sum(class_f1.values())/len(class_f1)
 checks={'trace_precision':precision>=target,'trace_recall':recall>=target,'trace_f1':f1>=target,'consistency_accuracy':accuracy>=target,'consistency_macro_f1':macro>=target,
         'all_semantic_citations_reviewed':semantic_ok==total,'operational_checks':protocol.get('operational_checks_passed') is True}
 return {'status':'OBSERVED_TARGET_MET' if all(checks.values()) else 'TARGET_NOT_MET','target':target,'cases':total,'checks':checks,
         'traceability':{'precision':precision,'recall':recall,'f1':f1,'tp':tp,'fp':fp,'fn':fn},
         'consistency':{'accuracy':accuracy,'macro_f1':macro,'per_class_f1':class_f1,'invalid_responses':invalid,'uncertainty_rate':uncertain/total,'correct':correct,'confusion_matrix':{label:{pred:counts[label,pred] for pred in sorted(LABELS|{'INVALID'})} for label in sorted({c['consistency_label'] for c in cases})},'wilson_95_interval':wilson(correct,total)},
         'consistency_population_91_percent_claim_supported':False,
         'joint_population_91_percent_claim_supported':False,
         'limitations':['Gate consumes recorded reviewer attestations, not independent authentication of reviewers.','Wilson interval is descriptive only; this gate does not establish population accuracy or cluster-aware uncertainty.','Passing operational tests is not evidence of semantic correctness.'], 'inference_calls':0}

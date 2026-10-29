"""Typed, read-only intents over a scoped saved report. No model calls."""
import re
from typing import Literal
from urllib.parse import urlencode
from pydantic import BaseModel,ConfigDict,Field
from fastapi import HTTPException
from ingestion.models import Artifact,digest
from rag.evidence import verify

Intent=Literal['CHANGES','FINDING','IMPACT','REQUIREMENT_TRACE','API_CONTRACT','TEST_OBLIGATIONS','EVIDENCE','LIMITATIONS','UNSUPPORTED']


class ReportContext(BaseModel):
 model_config=ConfigDict(extra='forbid')
 run_id:str;repository:str;base_commit:str;head_commit:str
 finding_id:str|None=None
 artifact_id:str|None=None
 intent:Intent|None=None


class ReportChatInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 project_id:str;repository:str;run_id:str;base_commit:str;head_commit:str
 question:str=Field(min_length=1,max_length=1200)
 finding_id:str|None=None
 artifact_id:str|None=None
 intent:Intent|None=None
 context:ReportContext|None=None


def resolve_intent(body):
 if body.intent:return body.intent,'explicit'
 q=body.question.casefold()
 for intent,pattern in [('EVIDENCE',r'\b(evidence|sources?|citations?|lines?)\b'),
                        ('LIMITATIONS',r'\b(limitations?|coverage|unknown|unsupported|gaps?)\b'),
                        ('REQUIREMENT_TRACE',r'\b(requirements?|traceability|traces?)\b'),
                        ('API_CONTRACT',r'\b(api|endpoints?|routes?)\b'),
                        ('IMPACT',r'\b(impact|affected|dependenc(?:y|ies)|callers?|paths?|chains?)\b'),
                        ('TEST_OBLIGATIONS',r'\b(tests?|obligations?)\b'),
                        ('CHANGES',r'\b(changes?|changed|compare|summari[sz]e)\b'),
                        ('FINDING',r'\b(findings?|why|explain|contradiction)\b')]:
  if re.search(pattern,q):return intent,'keyword'
 if body.context and re.fullmatch(r'\s*(?:and )?(?:what about|show|explain) (?:it|that|this)[?.! ]*',q):
  return body.context.intent or 'UNSUPPORTED','context'
 return 'UNSUPPORTED','keyword'


def verified_paths(store,report,artifact_id=None):
 """Return frozen paths only after checking revision and endpoint provenance."""
 result=[]
 for candidate in report.get('affected_artifacts',[]):
  if artifact_id and candidate['artifact_id']!=artifact_id:continue
  for detail in candidate.get('path_details',[]):
   role=detail['revision_role'];commit=report['base_commit'] if role=='base' else report['commit_id']
   path=detail['path'];steps=detail['steps']
   if role not in {'base','head'} or len(path)<2 or len(steps)!=len(path)-1 or path[-1]!=candidate['artifact_id']:raise ValueError('Invalid recorded graph path')
   for index,step in enumerate(steps):
    if (step['from_artifact'],step['to_artifact'])!=(path[index],path[index+1]) or not step['edge_options']:raise ValueError('Incomplete graph path')
    for edge in step['edge_options']:
     if edge['commit_id']!=commit or edge['repository']!=report['repository'] or edge['project_id']!=report['project_id'] or (edge['source_artifact'],edge['target_artifact'])!=(path[index+1],path[index]):raise ValueError('Graph scope mismatch')
     spans=edge.get('evidence_spans',[])
     if {s['artifact_id'] for s in spans}!={edge['source_artifact'],edge['target_artifact']}:raise ValueError('Graph endpoint provenance absent')
     for span in spans:
      row=store.get('artifacts',digest(span['artifact_id'],commit))
      if not row or row['repository']!=report['repository'] or row['project_id']!=report['project_id'] or span['commit']!=commit or any(span[k]!=row[field] for k,field in [('file','file_path'),('content_hash','content_hash'),('start_line','start_line'),('end_line','end_line')]):raise ValueError('Graph span mismatch')
   result.append({'artifact_id':candidate['artifact_id'],**detail})
 return result


def explain(store,body):
 report=store.get('analysis_runs',body.run_id)
 if not report or report.get('status')!='COMPLETED' or not report.get('changes'):raise HTTPException(404,'Completed investigation not found')
 if any(report.get(k)!=getattr(body,k) for k in ('project_id','repository')):raise HTTPException(404,'Investigation outside selected scope')
 if report.get('base_commit')!=body.base_commit or report.get('commit_id')!=body.head_commit:raise HTTPException(409,'Revision scope changed; select investigation again')
 if body.context and any(getattr(body.context,k)!=getattr(body,k) for k in ('run_id','repository','base_commit','head_commit')):raise HTTPException(409,'Conversation context belongs to another scope')
 evidence=report.get('evidence',[])
 try:
  if any(e['commit'] not in {body.base_commit,body.head_commit} for e in evidence):raise ValueError('Revision mismatch')
  rows=store.get_many('artifacts',[digest(e['artifact_id'],e['commit']) for e in evidence])
  artifacts=[Artifact.model_validate({k:v for k,v in row.items() if k!='id'}) for row in rows]
  if any(a.project_id!=body.project_id or a.repository!=body.repository for a in artifacts) or verify(evidence,artifacts):raise ValueError('Evidence mismatch')
 except (ValueError,KeyError,TypeError):raise HTTPException(409,'Saved evidence failed source verification')
 finding_id=body.finding_id or (body.context.finding_id if body.context else None)
 artifact_id=body.artifact_id or (body.context.artifact_id if body.context else None)
 findings=report.get('findings',[]);chosen=next((f for f in findings if f['finding_id']==finding_id),None)
 if finding_id and chosen is None:raise HTTPException(404,'Finding is not in this investigation')
 if artifact_id:
  versions=[store.get('artifacts',digest(artifact_id,c)) for c in {body.base_commit,body.head_commit}]
  if not any(a and a['repository']==body.repository and a['project_id']==body.project_id for a in versions):raise HTTPException(404,'Artifact is outside selected scope')
 intent,route=resolve_intent(body);state='ANSWERED';selected=[];claims=[];paths=[];test_candidates=[];test_suggestions=[]
 def claim(text,basis,items=(),support='UNREVIEWED'):
  ids=[e['evidence_id'] for e in items]
  claims.append({'text':text,'basis':basis,'support_level':support,'evidence_ids':ids,
                 'record_reference':{'run_id':body.run_id,'base_commit':body.base_commit,'head_commit':body.head_commit}})
 if intent=='EVIDENCE':
  ids=set(chosen['evidence_ids']) if chosen else None
  selected=[e for e in evidence if (ids is None or e['evidence_id'] in ids) and (not artifact_id or e['artifact_id']==artifact_id)][:8]
  claim('These excerpts match stored artifact versions. Semantic support still requires review.','SOURCE_RECORD',selected,'SOURCE_MATCH_ONLY')
 elif intent=='CHANGES':
  files=report['changes']['files'];selected=evidence[:6]
  claim(f'Git recorded {len(files)} changed files between these revisions.','SAVED_GIT_DIFF',selected,'RECORDED_FACT')
  for f in files[:10]:claim(f"{f['status']}: {f['old_path']} → {f['new_path']}",'SAVED_GIT_DIFF',support='RECORDED_FACT')
 elif intent=='FINDING':
  if not chosen and re.search(r'\b(it|that|this|why)\b',body.question,re.I) and len(findings)>1:
   state='NEEDS_CLARIFICATION';claim('Select the finding you want explained.','SCOPE_CLARIFICATION',support='NOT_ESTABLISHED')
  else:
   selected_findings=[chosen] if chosen else findings[:5]
   ids={e for f in selected_findings for e in f.get('evidence_ids',[])};selected=[e for e in evidence if e['evidence_id'] in ids][:8]
   for f in selected_findings:claim(f"Recorded {f['status']} ({f['rule']}): {f['reason']}",'RECORDED_FINDING',[e for e in selected if e['evidence_id'] in f.get('evidence_ids',[])])
   model=report.get('model',{});proposal=model.get('decision',{}).get('decision')
   if not model.get('validation_error') and any(f['status'] in {'CONSISTENT','INCONSISTENT'} and proposal in {'CONSISTENT','INCONSISTENT'} and f['status']!=proposal for f in selected_findings):
    state='CONFLICTING_EVIDENCE';claim('Rule and advisory model verdict conflict; independent review is required.','REVIEW_REQUIRED',selected)
 elif intent=='IMPACT':
  try:paths=verified_paths(store,report,artifact_id)
  except (ValueError,KeyError,TypeError):raise HTTPException(409,'Saved graph path failed provenance verification')
  ids={aid for p in paths for aid in p['path']};selected=[e for e in evidence if e['artifact_id'] in ids][:8]
  if paths:
   claim(f'{len(paths)} saved revision-specific dependency paths are available. They identify review candidates; behavioral impact remains unverified.','SAVED_GRAPH_PATH',selected,'STRUCTURAL_CANDIDATE')
   for p in paths[:8]:
    for step in p['steps']:
     labels=', '.join(f"{e['relation_type']} / {e.get('provenance_type','UNRECORDED')} / {e.get('resolution_status','UNRECORDED')}" for e in step['edge_options'])
     claim(f"{p['revision_role']}: {step['from_artifact']} → {step['to_artifact']} ({labels})",'SAVED_GRAPH_PATH',support='STRUCTURAL_CANDIDATE')
  else:
   state='NOT_ESTABLISHED';claim('No complete revision-specific path provenance was recorded for this selection. Historical hop counts cannot establish a dependency chain.','MISSING_PATH_PROVENANCE',support='NOT_ESTABLISHED')
 elif intent=='TEST_OBLIGATIONS':
  selected=[e for e in evidence if any(a.artifact_id==e['artifact_id'] and a.artifact_type in {'test','test_method'} for a in artifacts)][:8]
  test_candidates=[{'artifact_id':e['artifact_id'],'evidence_id':e['evidence_id'],'commit':e['commit'],'file':e['file'],
                    'reason':'Test excerpt recorded in this investigation; relevance requires review.','executed':False,'coverage_complete':False} for e in selected]
  state='NOT_ESTABLISHED'
  if not report.get('obligation_review'):claim('No complete verification-obligation registry or test coverage proof is recorded. These tests are review candidates; missing tests and successful execution are not established.','TEST_REVIEW_CANDIDATES',selected,'NOT_ESTABLISHED')
  review=report.get('obligation_review')
  if review:
   claim('A source-verified development registry is recorded. Search completeness and obligation judgments are reviewer attestations, not independent coverage or accuracy proof. No tests were executed by attaching it.','RECORDED_OBLIGATION_REVIEW',support='RECORDED_FACT')
   for row in review.get('assessments',[]):
    if artifact_id and artifact_id not in next((r[-1]['obligation']['applicable_artifact_ids'] for r in report.get('obligation_registry',{}).get('histories',[]) if r[-1]['obligation']['obligation_id']==row['obligation_id']),[]):continue
    items=[e for e in evidence if e['evidence_id'] in row.get('evidence_ids',[])]
    selected=list({e['evidence_id']:e for e in selected+items}.values())
    claim(f"Obligation {row['obligation_id']}: recorded {row['status']}; blockers: {', '.join(row['blockers']) or 'none within reviewed boundary'}.",'RECORDED_OBLIGATION_REVIEW',items,'REVIEWER_ATTESTED')
  changed_ids={c.get('new_artifact_id') or c.get('artifact_id') for c in report['changes'].get('artifacts',[])}
  seeds=[e for e in evidence if e['artifact_id'] in changed_ids and e['commit']==body.head_commit][:6]
  for e in seeds:
   test_suggestions.append({'file':e['file'],'start_line':e['start_line'],'artifact_id':e['artifact_id'],
                            'evidence_id':e['evidence_id'],'status':'REVIEW_SUGGESTION',
                            'question':'Review assertions for this changed source contract, including boundary and error cases supported by its requirements.',
                            'expected_behavior':'REQUIRES_CONTRACT_REVIEW','test_execution':'NOT_RUN'})
  selected=list({e['evidence_id']:e for e in selected+seeds}.values())
 elif intent in {'REQUIREMENT_TRACE','API_CONTRACT'}:
  kinds={'requirement'} if intent=='REQUIREMENT_TRACE' else {'api','api_caller'}
  selected=[e for e in evidence if any(a.artifact_id==e['artifact_id'] and a.artifact_type in kinds for a in artifacts) and (not artifact_id or e['artifact_id']==artifact_id)][:8]
  state='NOT_ESTABLISHED';claim('Recorded excerpts are available for review. Contract satisfaction and complete trace coverage are not established.','RECORDED_CONTRACT_CANDIDATES',selected,'NOT_ESTABLISHED')
 elif intent=='LIMITATIONS':
  for text in report.get('limitations',[])+report.get('analysis_contract',{}).get('evidence_gaps',[]):claim(text,'RECORDED_LIMITATION',support='RECORDED_FACT')
  if not report.get('coverage'):claim('This historical report has no full Git inventory coverage record.','MISSING_COVERAGE',support='NOT_ESTABLISHED')
 else:
  state='INSUFFICIENT_EVIDENCE';claim('Ask about recorded changes, findings, impact paths, requirement/API evidence, test obligations or limitations.','UNSUPPORTED_REQUEST',support='NOT_ESTABLISHED')
 if not claims:state='NOT_ESTABLISHED';claim('No saved records establish an answer for this selection.','MISSING_EVIDENCE',support='NOT_ESTABLISHED')
 if not selected and intent in {'EVIDENCE','FINDING'} and state=='ANSWERED':state='INSUFFICIENT_EVIDENCE'
 role_by_key={(a.artifact_id,a.commit_id):a.artifact_type for a in artifacts}
 citations=[{**e,'artifact_role':role_by_key.get((e['artifact_id'],e['commit']),'UNRECORDED'),
             'support_level':'SOURCE_MATCH_ONLY','provenance_type':'STORED_ARTIFACT_EXCERPT',
             'revision_role':'base-and-head' if body.base_commit==body.head_commit else ('head' if e['commit']==body.head_commit else 'base'),
             'source_url':'/api/artifacts/'+e['artifact_id']+'?'+urlencode({'repository':body.repository,'commit_id':e['commit']})} for e in selected]
 scope={k:getattr(body,k) for k in ('project_id','repository','run_id','base_commit','head_commit')}
 return {'state':state,'intent':intent,'intent_resolution':route,'answer':'\n'.join(c['text'] for c in claims),
         'claims':claims,'impact_paths':paths,'test_candidates':test_candidates,'test_suggestions':test_suggestions,'coverage':report.get('coverage'),
         'citations':citations,'retrieved_evidence':[],'decision':{'decision':state},'validation_error':None,
         'confidence_note':'Recorded facts/findings; no new model inference.','source_verified':True,
         'verification_scope':'quoted excerpts and path endpoints against stored artifact versions; semantic support unreviewed',
         'semantic_entailment_verified':False,'inference_calls':0,'scope':scope,
         'context':{k:v for k,v in {**scope,'finding_id':finding_id,'artifact_id':artifact_id,'intent':intent}.items() if k!='project_id'},
         'finding_ids':[chosen['finding_id']] if chosen else []}

"""Bounded VIGILANT investigation with persisted tool outcomes and verified quotes."""
import time,uuid
from collections import Counter
from ingestion.models import digest,now
from ingestion.git import revision
from ingestion.service import import_repository
from knowledge_graph.graph import build_graph,impact_snapshots
from ingestion.coverage import coverage
from rag.evidence import retrieve,evidence,verify_git,paired_versions
from change_analysis.diff import detect,format_change_facts
from consistency.rules import check
from traceability.recovery import recover
from retrieval.index import Encoder,tokens,RETRIEVAL_POLICY
from llm.providers import provider
from agents.evidence_first import analysis_packet
from agents.control import RunControl,InvestigationStopped

def analyze(store,repo,base,head='HEAD',project='vigilant',model='none',semantic=False,declared_links=(),ollama_model=None,control=None,run_id=None):
 # Existing direct/CLI callers keep their prior budget unless they opt in.
 control=control or RunControl(float('inf'))
 rid=run_id or uuid.uuid4().hex;trajectory=[];quote_counts={"attempted":0,"verified":0};start=time.perf_counter();store.put('analysis_runs',rid,{'run_id':rid,'project_id':project,'status':'RUNNING'})
 scope={'run_id':rid,'project_id':project}
 def stage(role,tool,fn):
  t=time.perf_counter();started=False
  try:
   control.check();started=True;value=fn();control.check()
   trajectory.append({'role':role,'tool':tool,'status':'SUCCESS','seconds':time.perf_counter()-t});return value
  except InvestigationStopped as e:
   trajectory.append({'role':role,'tool':tool,'status':e.status,'operation_started':started,'seconds':time.perf_counter()-t});raise
  except Exception as e:trajectory.append({'role':role,'tool':tool,'status':'FAILED','error':str(e),'seconds':time.perf_counter()-t});raise
 try:
  plan=stage('Planner','resolve-commits',lambda:{'base':revision(repo,base),'head':revision(repo,head)})
  imports=stage('Artifact Investigator','import-snapshots',lambda:[import_repository(store,repo,project,plan['base']),import_repository(store,repo,project,plan['head'])]);repository=imports[0]['repository']
  before=store.artifacts(repository,plan['base']);after=store.artifacts(repository,plan['head']);scope={'run_id':rid,'project_id':project,'repository':repository,'commit_id':plan['head']}
  changes=stage('Change Investigator','git-diff-symbol-hashes',lambda:detect(repo,plan['base'],plan['head'],before,after));bg,be=stage('Traceability Investigator','base-graph',lambda:build_graph(store,before,declared_links));hg,he=stage('Traceability Investigator','head-graph',lambda:build_graph(store,after,declared_links))
  seeds={x['artifact_id'] for x in changes['artifacts']}|{x['new_artifact_id'] for x in changes['artifacts'] if x.get('new_artifact_id')};paths=stage('Change Investigator','two-snapshot-impact',lambda:impact_snapshots([('base',bg),('head',hg)],seeds))
  coverage_report=stage('Verifier','inventory-extraction-coverage',lambda:{'base':coverage(repo,plan['base'],before,bg),'head':coverage(repo,plan['head'],after,hg)})
  encoder=stage('Evidence Investigator','prepare-encoder',Encoder) if semantic else None
  candidates=stage('Traceability Investigator','bounded-trace-recovery',lambda:recover(store,after,encoder))
  findings=stage('Consistency Investigator','deterministic-rules',lambda:check(changes['artifacts'],before,after,be,changes['files']))
  packet=stage('Verifier','establish-source-change-facts',lambda:analysis_packet(changes,before,after,findings,paths))
  terms=Counter(tokens(' '.join(line[1:] for f in changes['files'] for line in f.get('patch','').splitlines() if line.startswith(('+','-')) and not line.startswith(('+++','---')))))
  query=' '.join((x['symbol'] or x['file']) for x in changes['artifacts'][:8])+' '+' '.join(word for word,_ in terms.most_common(32))
  ev=stage('Evidence Investigator','retrieve-grounded-context',lambda:retrieve(query,after,hg,seeds,encoder))
  ev=paired_versions(changes,before,after)+ev
  for a in before:
   if a.artifact_id in seeds and a.artifact_type in {'api','requirement','test_method'}:ev.append(evidence(a,'base-version',max_lines=12))
   if len(ev)>=20:break
  # Findings receive exact endpoint evidence even when retrieval budgets omit that endpoint.
  for f in findings:
   for aid in f['affected_artifacts']:
    if not any(e['artifact_id']==aid for e in ev):
     a=next((a for a in after+before if a.artifact_id==aid),None)
     if a:ev.append(evidence(a,'rule-endpoint',max_lines=30))
   f['evidence_ids']=sorted({e['evidence_id'] for e in ev if e['artifact_id'] in f['affected_artifacts']})
  unique={}
  for e in ev:unique.setdefault(e['evidence_id'],e)
  ev=list(unique.values())
  def verify_sources():
   quote_counts['attempted']=len(ev);errors=verify_git(ev,before+after,repo)
   failed={e['evidence_id'] for e in ev if any(e['evidence_id'] in err for err in errors)};quote_counts['verified']=len(ev)-len(failed)
   if errors:raise ValueError(str(errors))
  stage('Verifier','validate-git-blobs-quotes-ranges-hashes',verify_sources)
  for e in ev:e['revision_role']='base-and-head' if plan['base']==plan['head'] else ('head' if e['commit']==plan['head'] else 'base')
  from agents.assurance import assess_changes
  assurance=stage('Verifier','facts-rules-semantic-residue-v3',lambda:assess_changes(
   changes,before,after,repo,model=model,ollama_model=ollama_model,declared_links=declared_links,
   control=control,retrieved_evidence=(ev if model != "none" else ())))
  for e in assurance['evidence']:
   if not any(x['evidence_id']==e['evidence_id'] for x in ev):ev.append(e)
  # Retain the v2 envelope for old readers; scoped V3 assessments are explicit below.
  reasoning={'provider':'none','decision':None,'raw_output':'','usage':{'api_cost_usd':0.0},
   'validation_error':None,'authority':'LEGACY_COMPATIBILITY_ENVELOPE',
   'confidence_calibrated':False,'inference_requested':False,'promoted_to_finding':False,
   'v3_assessments_available':True,'context_policy':{'version':'evidence-first-v3','included':len(ev)}}
  report={**scope,'status':'COMPLETED','created_at':now(),'base_commit':plan['base'],'config':{'model':model,'semantic':semantic,'impact_hops':2,'ollama_model':ollama_model},'changes':changes,'affected_artifacts':paths,'coverage':coverage_report,'trace_candidates':candidates,'findings':findings,'evidence':ev,'model':reasoning,'trajectory':trajectory,'metrics':{**measured_metrics(trajectory,quote_counts),'model_schema_valid':(reasoning['validation_error'] is None) if reasoning['inference_requested'] else None,'semantic_grounding_rate':None,'seconds':time.perf_counter()-start},'limitations':['Static graph neighbourhood is an impact candidate set, not a causal proof.','Citation validity does not prove semantic entailment.','Unchanged tests signal review, not definite defects.']}
  report['assurance_v3']=assurance;report['analysis_contract']=packet;report['config'].update(analysis_policy='facts-rules-semantic-residue-v3',retrieval_policy=RETRIEVAL_POLICY)
  for item in report['affected_artifacts']:item.update(classification='IMPACT_CANDIDATE',causal_impact_verified=False,path_basis='revision-isolated-reverse-dependency-path-v3')
  publish_started=time.perf_counter();publish_step={'role':'Explanation Generator','tool':'persist-report','status':'SUCCESS','seconds':0.0}
  def persist():
   cid=digest(repository,plan['head'])
   with store.connection(write=True) as connection:
    for table,rows,key in [('evidence',ev,'evidence_id'),('findings',findings,'finding_id')]:
     store.put_many(table,[(digest(rid,row[key]),{**row,**scope}) for row in rows],connection=connection)
    store.put_many('graph_nodes',[(cid,{'artifact_id':cid,'artifact_type':'commit','repository':repository,'commit_id':plan['head'],'project_id':project})],connection=connection)
    store.put_many('changes',[(digest(rid,str(i)),{**c,**scope}) for i,c in enumerate(changes['artifacts'])],connection=connection)
    store.put_many('graph_edges',[(digest(rid,'commit',str(i)),{'source_artifact':cid,'target_artifact':c.get('new_artifact_id') or c['artifact_id'],'relation_type':'MODIFIES','method':'git-diff','evidence':[c],**scope}) for i,c in enumerate(changes['artifacts'])],connection=connection)
    publish_step['seconds']=time.perf_counter()-publish_started
    final_trajectory=[*trajectory,publish_step]
    report['trajectory']=final_trajectory
    report['metrics'].update(measured_metrics(final_trajectory,quote_counts));report['metrics']['seconds']=time.perf_counter()-start
    store.put_many('agent_runs',[(rid,{**scope,'status':'COMPLETED','trajectory':final_trajectory})],replace=True,connection=connection)
    store.put_many('analysis_runs',[(rid,report)],replace=True,connection=connection)
  control.begin_publication()
  try:persist()
  except Exception as e:
   trajectory.append({'role':'Explanation Generator','tool':'persist-report','status':'FAILED','error':str(e),'seconds':time.perf_counter()-publish_started});raise
  trajectory.append(publish_step);return report
 except InvestigationStopped as e:
  e.run_id=rid
  stopped={**scope,'status':e.status,'trajectory':trajectory,'error':str(e),'finished_at':now(),'partial_results':True,'metrics':measured_metrics(trajectory,quote_counts),'stop_mode':'COOPERATIVE_STAGE_BOUNDARY'}
  store.put('agent_runs',rid,stopped);store.put('analysis_runs',rid,stopped,replace=True);raise
 except Exception as e:
  store.put('agent_runs',rid,{'run_id':rid,'status':'FAILED','trajectory':trajectory,'error':str(e)});store.put('analysis_runs',rid,{'run_id':rid,'status':'FAILED','trajectory':trajectory,'error':str(e),'metrics':measured_metrics(trajectory,quote_counts)},replace=True);raise


def measured_metrics(trajectory,quotes):
 total=len(trajectory);successful=sum(s['status']=='SUCCESS' for s in trajectory)
 return {'tool_execution_success':successful/total if total else None,'tool_stages_attempted':total,'tool_stages_succeeded':successful,
         'quote_verification_rate':quotes['verified']/quotes['attempted'] if quotes['attempted'] else None,'quotes_attempted':quotes['attempted'],'quotes_verified':quotes['verified'],'quote_verification_basis':'independent-git-blob-read'}

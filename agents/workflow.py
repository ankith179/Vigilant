"""Bounded VIGILANT investigation with persisted tool outcomes and verified quotes."""
import time,uuid,networkx as nx
from ingestion.models import digest,now
from ingestion.git import revision
from ingestion.service import import_repository
from knowledge_graph.graph import build_graph,impact
from rag.evidence import retrieve,evidence,verify,paired_versions
from change_analysis.diff import detect,format_change_facts
from consistency.rules import check
from traceability.recovery import recover
from retrieval.index import Encoder
from llm.providers import provider

def analyze(store,repo,base,head='HEAD',project='vigilant',model='none',semantic=False,declared_links=(),ollama_model=None):
 rid=uuid.uuid4().hex;trajectory=[];start=time.perf_counter();store.put('analysis_runs',rid,{'run_id':rid,'project_id':project,'status':'RUNNING'})
 def stage(role,tool,fn):
  t=time.perf_counter()
  try:value=fn();trajectory.append({'role':role,'tool':tool,'status':'SUCCESS','seconds':time.perf_counter()-t});return value
  except Exception as e:trajectory.append({'role':role,'tool':tool,'status':'FAILED','error':str(e),'seconds':time.perf_counter()-t});raise
 try:
  plan=stage('Planner','resolve-commits',lambda:{'base':revision(repo,base),'head':revision(repo,head)})
  imports=stage('Artifact Investigator','import-snapshots',lambda:[import_repository(store,repo,project,plan['base']),import_repository(store,repo,project,plan['head'])]);repository=imports[0]['repository']
  before=store.artifacts(repository,plan['base']);after=store.artifacts(repository,plan['head']);scope={'run_id':rid,'project_id':project,'repository':repository,'commit_id':plan['head']}
  changes=stage('Change Investigator','git-diff-symbol-hashes',lambda:detect(repo,plan['base'],plan['head'],before,after));bg,be=stage('Traceability Investigator','base-graph',lambda:build_graph(store,before,declared_links));hg,he=stage('Traceability Investigator','head-graph',lambda:build_graph(store,after,declared_links))
  seeds={x['artifact_id'] for x in changes['artifacts']}|{x['new_artifact_id'] for x in changes['artifacts'] if x.get('new_artifact_id')};paths=stage('Change Investigator','two-snapshot-impact',lambda:impact(nx.compose(bg,hg),seeds))
  encoder=Encoder() if semantic else None
  candidates=stage('Traceability Investigator','bounded-trace-recovery',lambda:recover(store,after,encoder))
  query='Assess changes to '+', '.join((x['symbol'] or x['file']) for x in changes['artifacts'][:8])+'. Does existing caller/test evidence need review?\nGit-derived change facts (not findings):\n'+format_change_facts(changes)
  ev=stage('Evidence Investigator','retrieve-grounded-context',lambda:retrieve(query,after,hg,seeds,encoder))
  ev=paired_versions(changes,before,after)+ev
  for a in before:
   if a.artifact_id in seeds and a.artifact_type in {'api','requirement','test_method'}:ev.append(evidence(a,'base-version',max_lines=12))
   if len(ev)>=20:break
  findings=stage('Consistency Investigator','deterministic-rules',lambda:check(changes['artifacts'],before,after,be))
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
  errors=stage('Verifier','validate-quotes-ranges-hashes',lambda:verify(ev,before+after))
  if errors:raise ValueError(str(errors))
  engine=provider(model)
  if model=='ollama' and ollama_model:
   from llm.ollama import OllamaProvider
   engine=OllamaProvider(ollama_model)
  reasoning=stage('Traceability Investigator','structured-model-call',lambda:engine.investigate(query,ev))
  report={**scope,'status':'COMPLETED','created_at':now(),'base_commit':plan['base'],'config':{'model':model,'semantic':semantic,'impact_hops':2,'ollama_model':ollama_model},'changes':changes,'affected_artifacts':[{'artifact_id':a,'path':p} for a,p in paths.items()],'trace_candidates':candidates,'findings':findings,'evidence':ev,'model':reasoning,'trajectory':trajectory,'metrics':{'tool_execution_success':1.,'quote_verification_rate':1.,'model_schema_valid':reasoning['validation_error'] is None,'semantic_grounding_rate':None,'seconds':time.perf_counter()-start},'limitations':['Static graph neighbourhood is an impact candidate set, not a causal proof.','Citation validity does not prove semantic entailment.','Unchanged tests signal review, not definite defects.']}
  def persist():
   for table,rows,key in [('evidence',ev,'evidence_id'),('findings',findings,'finding_id')]:
    for row in rows:store.put(table,digest(rid,row[key]),{**row,**scope})
   cid=digest(repository,plan['head']);store.put('graph_nodes',cid,{'artifact_id':cid,'artifact_type':'commit','repository':repository,'commit_id':plan['head'],'project_id':project})
   for i,c in enumerate(changes['artifacts']):
    store.put('changes',digest(rid,str(i)),{**c,**scope});store.put('graph_edges',digest(rid,'commit',str(i)),{'source_artifact':cid,'target_artifact':c.get('new_artifact_id') or c['artifact_id'],'relation_type':'MODIFIES','method':'git-diff','evidence':[c],**scope})
  stage('Explanation Generator','persist-report',persist);report['trajectory']=trajectory;store.put('agent_runs',rid,{**scope,'status':'COMPLETED','trajectory':trajectory});store.put('analysis_runs',rid,report,replace=True);return report
 except Exception as e:
  store.put('agent_runs',rid,{'run_id':rid,'status':'FAILED','trajectory':trajectory,'error':str(e)});store.put('analysis_runs',rid,{'run_id':rid,'status':'FAILED','trajectory':trajectory,'error':str(e)},replace=True);raise

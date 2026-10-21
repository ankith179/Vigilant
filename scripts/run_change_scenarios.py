"""Twelve authored controlled changes on pinned real repositories, never upstream writes."""
import sys,pathlib,subprocess,ast,os,json,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from ingestion.git import git,revision
from ingestion.service import import_repository
from agents.workflow import analyze
from database.store import Store
from evaluation.metrics import classification
from evaluation.runs import ROOT,save_run

def specs():
 req='.rtmx/requirements/HARNESS/REQ-HARNESS-001.md';helper='src/flask/helpers.py';test='tests/test_helpers.py';api='backend/app/api/routes/items.py';client='frontend/src/client/sdk.gen.ts'
 return [
 {'id':'01-requirement-changed','repo':'rtmx','file':req,'mode':'append','new':'Controlled benchmark change: include failed sessions in completed-run accounting.','status':'POTENTIAL_INCONSISTENCY','target':'tests/test_harness.sh'},
 {'id':'02-requirement-added','repo':'rtmx','file':'.rtmx/requirements/REQ-VIGILANT-ADDED.md','mode':'add','new':'# Controlled benchmark requirement\nThe runner shall record a machine-readable timeout reason.','status':'UNCERTAIN'},
 {'id':'03-code-changed','repo':'flask','file':helper,'mode':'replace','old':'code: int = 303','new':'code: int = 307','status':'POTENTIAL_INCONSISTENCY','target':test,'target_symbol':'test_redirect_no_app'},
 {'id':'04-code-deleted','repo':'flask','file':helper,'mode':'remove_function','old':'redirect','status':'BROKEN_TRACE','target':test,'target_symbol':'test_redirect_no_app'},
 {'id':'05-test-changed','repo':'flask','file':test,'mode':'replace','old':'def test_redirect_no_app():','new':'def test_redirect_no_app():\n    # Controlled benchmark: comment-only review','status':'UNCERTAIN','target':helper,'target_symbol':'redirect'},
 {'id':'06-test-deleted','repo':'flask','file':test,'mode':'remove_function','old':'test_redirect_no_app','status':'MISSING_TEST','target':helper,'target_symbol':'redirect'},
 {'id':'07-frontend-changed','repo':'fullstack','file':'frontend/src/routes/_layout/items.tsx','mode':'append','new':'// Controlled benchmark: display-only wording review.','status':'UNCERTAIN'},
 {'id':'08-api-changed','repo':'fullstack','file':api,'mode':'replace','old':'prefix="/items"','new':'prefix="/catalog"','status':'POTENTIAL_INCONSISTENCY','target':client},
 {'id':'09-backend-changed','repo':'fullstack','file':api,'mode':'replace','old':'limit: int = 100','new':'limit: int = 50','status':'POTENTIAL_INCONSISTENCY','target':'backend/tests/api/routes/test_items.py'},
 {'id':'10-consumer-changed','repo':'fullstack','file':client,'mode':'replace','old':"url: '/api/v1/items/'",'new':"url: '/api/v1/obsolete-items/'",'status':'BROKEN_TRACE','target':api},
 {'id':'11-implementation-test-drift','repo':'flask','file':helper,'mode':'replace','old':'code: int = 303','new':'code: int = 308','status':'POTENTIAL_INCONSISTENCY','target':test,'target_symbol':'test_redirect_no_app'},
 {'id':'12-requirement-test-drift','repo':'rtmx','file':req,'mode':'append','new':'Controlled benchmark change: verify zero shared process state across consecutive runs.','status':'POTENTIAL_INCONSISTENCY','target':'tests/test_harness.sh'}]

def mutate(p,case):
 mode=case['mode'];old=case.get('old','');new=case.get('new','')
 if mode=='add':p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new);return
 text=p.read_text()
 if mode=='remove_function':
  node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==old);lines=text.splitlines(True);start=min([node.lineno]+[d.lineno for d in node.decorator_list])-1;text=''.join(lines[:start]+lines[node.end_lineno:])
 elif mode=='append':text+='\n'+new+'\n'
 else:
  if old not in text:raise ValueError('Mutation text absent: '+str(p))
  text=text.replace(old,new,1)
 p.write_text(text)

def main():
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--case');parser.add_argument('--model',default='none');parser.add_argument('--semantic',action='store_true');args=parser.parse_args()
 folder=ROOT/'data/changebench';folder.mkdir(exist_ok=True);store=Store(os.getenv('VIGILANT_DB','sqlite:///'+str(ROOT/'data/changebench.db')));results=[];start=time.perf_counter()
 for case in specs():
  if args.case and args.case!=case['id']:continue
  source=ROOT/('data/raw/rtmx' if case['repo']=='rtmx' else 'data/repos/'+case['repo']);dest=folder/case['id'];base=revision(source);origin=git(source,'remote','get-url','origin');project='changebench/'+case['id']
  if not dest.exists():git(source,'worktree','add','--detach',str(dest),base)
  if revision(dest)==base:
   git(dest,'checkout','--detach',base);mutate(dest/case['file'],case);git(dest,'add','--all');env={**os.environ,'GIT_AUTHOR_NAME':'VIGILANT ChangeBench','GIT_AUTHOR_EMAIL':'vigilant@example.invalid','GIT_COMMITTER_NAME':'VIGILANT ChangeBench','GIT_COMMITTER_EMAIL':'vigilant@example.invalid','GIT_AUTHOR_DATE':'2026-10-05T00:00:00Z','GIT_COMMITTER_DATE':'2026-10-05T00:00:00Z'}
   subprocess.run(['git','-c','core.hooksPath=/dev/null','-C',str(dest),'commit','-m',case['id']],env=env,check=True,capture_output=True)
  head=revision(dest);initial=import_repository(store,dest,project,base);arts=store.artifacts(initial['repository'],base)
  def locate(path,symbol=''):return next(a for a in arts if a.file_path==path and a.symbol==symbol)
  links=[]
  if case['repo']=='flask':links=[{'source_artifact':locate('tests/test_helpers.py','test_redirect_no_app').artifact_id,'target_artifact':locate('src/flask/helpers.py','redirect').artifact_id,'relation_type':'TESTS','method':'reviewed-baseline-call-trace'}]
  if case['repo']=='rtmx' and case.get('target'):links=[{'source_artifact':locate(case['file']).artifact_id,'target_artifact':locate(case['target']).artifact_id,'relation_type':'VALIDATES','method':'upstream-rtmx-module-declaration'}]
  if case['id']=='09-backend-changed':
   tests=[a for a in arts if a.file_path==case['target'] and a.artifact_type=='test_method' and 'read_items' in a.symbol]
   if not tests:raise ValueError('Actual read_items test not found')
   case['target_symbol']=tests[0].symbol;links=[{'source_artifact':tests[0].artifact_id,'target_artifact':locate(case['file'],'read_items').artifact_id,'relation_type':'TESTS','method':'reviewed-api-test-trace'}]
  expected=[a.artifact_id for a in arts if a.file_path==case.get('target') and (a.symbol==case['target_symbol'] if case.get('target_symbol') else not a.symbol)]
  if case['id'] in ['08-api-changed','10-consumer-changed']:expected=[a.artifact_id for a in arts if a.file_path==case['target'] and a.artifact_type==('api_caller' if case['id']=='08-api-changed' else 'api') and '/items' in a.metadata.get('route','')]
  contract={**case,'base_commit':base,'change_commit':head,'origin':origin,'expected_affected_artifacts':expected,'expected_traceability':links,'oracle':'Authored expectations; partial affected set; not independently reviewed','scope':'Known-trace maintenance on real structures; changes are explicitly controlled mutations'}
  (folder/(case['id']+'.json')).write_text(json.dumps(contract,indent=2))
  report=analyze(store,dest,base,head,project,model=args.model,semantic=args.semantic,declared_links=links);(folder/(case['id']+'-report.json')).write_text(json.dumps(report,indent=2))
  predicted={a['artifact_id'] for a in report['affected_artifacts']};statuses={f['status'] for f in report['findings']};metric=classification(expected,predicted)
  row={'case':contract,'run_id':report['run_id'],'status_match':case['status'] in statuses,'predicted_statuses':sorted(statuses),'affected_metrics':metric,'uncertain':statuses=={'UNCERTAIN'},'model_error':report['model']['validation_error'],'seconds':report['metrics']['seconds']};results.append(row);print(case['id'],row['status_match'],metric,flush=True)
 path,_=save_run('changebench',{'status':'COMPLETED','cases':results,'status_accuracy':sum(r['status_match'] for r in results)/len(results),'uncertain_rate':sum(r['uncertain'] for r in results)/len(results),'seconds':time.perf_counter()-start,'limitations':['Partial affected oracles: apparent false positives require human review.','Seeded relations test trace maintenance, not link recovery.','Repeated artifacts/cases are not independent statistical samples.']});print(path)
if __name__=='__main__':main()

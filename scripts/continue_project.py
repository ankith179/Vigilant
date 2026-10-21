"""Resume executable project stages from a durable, atomic task ledger.

This runner executes existing scripts. It does not independently write research
code, perform human review, or bypass account/model limits.
"""
from pathlib import Path
import argparse,datetime,json,os,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'PROJECT_STATE.json'

def now():return datetime.datetime.now(datetime.timezone.utc)
def save(state):
 state['updated_at']=now().isoformat();temporary=STATE.with_suffix('.pending');temporary.write_text(json.dumps(state,indent=2));os.replace(temporary,STATE)
def main():
 p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');p.add_argument('--retry-failed',action='store_true');p.add_argument('--task');p.add_argument('--status',action='store_true');p.add_argument('--release-lease',action='store_true');a=p.parse_args();state=json.loads(STATE.read_text())
 if a.status:
  for task in state['tasks']:print(f"{task['id']:20} {task['status']:12} {task['title']}")
  return
 if a.release_lease:state['active_lease']=None;save(state);return
 lease=state.get('active_lease')
 if lease and datetime.datetime.fromisoformat(lease['expires_at'])>now():raise SystemExit('Another worker has an active lease. Check it before releasing the lease.')
 owner='runner-'+uuid.uuid4().hex;state['active_lease']={'owner':owner,'expires_at':(now()+datetime.timedelta(hours=6)).isoformat()};save(state)
 try:
  for task in state['tasks']:
   if a.task and task['id']!=a.task:continue
   if task['status']=='COMPLETED':continue
   if not task.get('command'):continue
   if task['status']=='FAILED' and not a.retry_failed:continue
   dependencies=[x for x in state['tasks'] if x['id'] in task.get('depends_on',[])]
   if any(x['status']!='COMPLETED' for x in dependencies):continue
   args=[sys.executable if x=='{python}' else ('npm.cmd' if os.name=='nt' and x=='npm' else x) for x in task['command']]
   task['status']='RUNNING';task['started_at']=now().isoformat();save(state);log=ROOT/'reports'/('resume-'+task['id']+'.log');log.parent.mkdir(exist_ok=True)
   print('Running',task['id'],flush=True)
   with log.open('a',encoding='utf-8') as out:result=subprocess.run(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
   task['finished_at']=now().isoformat();task['status']='COMPLETED' if result.returncode==0 else 'FAILED';task['exit_code']=result.returncode;task['log']=str(log.relative_to(ROOT));save(state)
   if result.returncode:raise SystemExit('Stage failed; preserved progress and log: '+str(log))
   if not a.all:break
 finally:state['active_lease']=None;save(state)
if __name__=='__main__':main()

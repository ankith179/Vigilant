"""Fetch pinned upstream data; preserve existing checkouts and verify versions."""
from pathlib import Path
import subprocess,json,datetime,argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
'lissa':('https://github.com/ardoco/Replication-Package-ICSE25_LiSSA-Toward-Generic-Traceability-Link-Recovery-through-RAG.git','a8e652f29bbdcc4bdcd3d98cd85aa4a37cb65480',['LiSSA-RATLR-V2/lissa/datasets/req2code']),
'rtmx':('https://github.com/rtmx-ai/rtmx-bench.git','c2ced5349577a1df6987130961cadc94834ca70c',[]),
'safa':('https://github.com/SAREC-Lab/SAFA-Artifacts.git','ac201a4a7364cf91110c33a9f5b41df9ffbfe709',[])}
REPOS={
'flask':('https://github.com/pallets/flask.git','d73fa1cdcbd8b1465c151db8924ba58b1dd14e35'),
'petclinic':('https://github.com/spring-projects/spring-petclinic.git','500158f732419217507c7656904b8e6aa1bcc0d6'),
'express':('https://github.com/expressjs/express.git','7ef98448f8b38099ab1ded55e458538ad47a51e7'),
'fullstack':('https://github.com/fastapi/full-stack-fastapi-template.git','1762adac607a1b29cfc4da129557780beea71616')}
def git(*args,cwd=None):return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=cwd,check=True,capture_output=True,text=True,timeout=300).stdout.strip()
def fetch(name,url,commit,sparse,folder,depth=1):
 dest=ROOT/'data'/folder/name;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  git('clone','--filter=blob:none','--no-checkout','--depth',str(depth),url,str(dest))
  if sparse:git('sparse-checkout','set',*sparse,cwd=dest)
  git('fetch','--depth',str(depth),'origin',commit,cwd=dest);git('checkout','--detach',commit,cwd=dest)
 if git('rev-parse','HEAD',cwd=dest)!=commit:raise ValueError('Existing checkout mismatch '+name)
 return {'name':name,'url':url,'commit':commit,'downloaded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(dest.relative_to(ROOT)),'licenses':[x.name for x in dest.iterdir() if 'license' in x.name.lower()]}
def main(repositories=False):
 records={};source=REPOS if repositories else SOURCES
 for name,values in source.items():
  records[name]=fetch(name,values[0],values[1],[] if repositories else values[2],'repos' if repositories else 'raw',40 if repositories else 1)
  if repositories:records[name]['base_commit']=git('rev-parse','HEAD~1',cwd=ROOT/records[name]['path'])
  print(name,values[1],flush=True)
  (ROOT/'data'/('repositories.json' if repositories else 'source-manifest.json')).write_text(json.dumps(records,indent=2))
if __name__=='__main__':main()

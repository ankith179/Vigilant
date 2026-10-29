"""Check a generated VIGILANT release, optionally restore and smoke-test a fresh copy."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,stat,subprocess,sys,tempfile,zipfile


def verify(archive,restore=False):
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            path=PurePosixPath(item.filename)
            if '\\' in item.filename or path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='VIGILANT' or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Unsafe archive member')
        if sum(item.file_size for item in z.infolist())>2_000_000_000:raise ValueError('Release exceeds validation extraction budget')
        if z.testzip() is not None:raise ValueError('ZIP integrity failure')
        manifest=json.loads(z.read('VIGILANT/PACKAGE-MANIFEST.json'))
        expected={r['path'] for r in manifest}|{'VIGILANT/PACKAGE-MANIFEST.json'}
        if {i.filename for i in z.infolist() if not i.is_dir()}!=expected:raise ValueError('Manifest/member set mismatch')
        for row in manifest:
            data=z.read(row['path'])
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Manifest byte/hash mismatch: '+row['path'])
        preserved=json.loads(z.read('VIGILANT/reports/audit-v2-20261023/preserved-before.json'))
        for path,digest in preserved.items():
            if hashlib.sha256(z.read('VIGILANT/'+path)).hexdigest()!=digest:raise ValueError('Historical file changed: '+path)
        if any(any(p in {'.venv','node_modules','.runtime','.uv-cache','__pycache__'} for p in PurePosixPath(name).parts) for name in z.namelist()):raise ValueError('Reproducible dependencies were packaged')
        if any(name.startswith('VIGILANT/tmp/release-debug-restore/') for name in z.namelist()):raise ValueError('Temporary restored project was packaged')
        result={'status':'PASS','manifest_files_verified':len(manifest),'historical_files_verified':len(preserved),'new_model_calls':0}
        if restore:
            with tempfile.TemporaryDirectory(prefix='vigilant-release-check-') as tmp:
                z.extractall(tmp);root=Path(tmp)/'VIGILANT'
                subprocess.run([sys.executable,'scripts/restore_checkpoint.py'],cwd=root,check=True,capture_output=True,text=True)
                code="""
import json,sqlite3
from pathlib import Path
from contextlib import closing
from database.store import Store
from backend.app import create_app
from fastapi.testclient import TestClient
checks={}
for p in Path('data/snapshots').glob('*'):
 if p.suffix in {'.db','.sqlite'}:
  with closing(sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)) as db:checks[p.name]=db.execute('pragma integrity_check').fetchone()[0]
assert all(v=='ok' for v in checks.values())
store=Store()
assert not any(r.get('kind')=='job' and r.get('status')=='QUEUED' for r in store.jobs()), 'Do not resume queued inference during validation'
with TestClient(create_app(store)) as client:
 health=client.get('/api/health');assert health.status_code==200 and health.json()['status']=='ok'
 home=client.get('/');assert home.status_code==200 and 'assets/index-' in home.text
 stats=client.get('/api/stats');assert stats.status_code==200 and stats.json()['artifacts']>0
 print(json.dumps({'health':health.json(),'frontend_http':home.status_code,'artifact_count':stats.json()['artifacts'],'database_integrity':checks}))
store.engine.dispose()
"""
                env={**os.environ,'VIGILANT_DB':'sqlite:///'+str(root/'data/vigilant.db'),'VIGILANT_ACCESS_TOKEN':''}
                checked=subprocess.run([sys.executable,'-c',code],cwd=root,env=env,check=True,capture_output=True,text=True)
                result['fresh_restore_application']=json.loads(checked.stdout)
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--restore-smoke',action='store_true');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=verify(args.archive,args.restore_smoke)
    result['archive_sha256']=hashlib.sha256(args.archive.read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

"""Verify staged recovered sources and blank packets; never supply review labels."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import create_app
from database.store import Store
from fastapi.testclient import TestClient
from ingestion.models import Artifact,digest


def audit(baseline):
    report=ROOT/'reports/recovered-review-20261024';packets=report/'packets'
    database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    staging=json.loads((report/'STAGING.json').read_text());before=hashlib.sha256(database.read_bytes()).hexdigest()
    assert before==staging['database_sha256']
    index_path=ROOT/'reports/verified-cache-maps-20261024/maps/index.json';index=json.loads(index_path.read_text())
    assert staging['source_index_sha256']==hashlib.sha256(index_path.read_bytes()).hexdigest()
    samples=[];count=0;api_count=0;references=0;statuses=Counter()
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
        assert db.execute('select count(*) from projects').fetchone()[0]==1
        assert db.execute('select count(*) from repositories').fetchone()[0]==4
        assert db.execute('select count(*) from commits').fetchone()[0]==53
        assert db.execute('select count(*) from artifacts').fetchone()[0]==29647
        for key,s in index['snapshots'].items():
            raw=(index_path.parent/s['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']
            m=json.loads(raw)
            stored={a['artifact_id']:a for (r,) in db.execute('select payload from artifacts where repository=? and commit_id=?',(m['repository'],m['commit_id'])) for a in [json.loads(r)]}
            assert len(stored)==len(m['artifacts'])
            for a in m['artifacts']:
                item=stored[a['artifact_id']];assert {k:v for k,v in item.items() if k!='id'}==a
                assert Artifact.model_validate(a).content_hash==digest(a['content']);count+=1
            commit=json.loads(db.execute('select payload from commits where id=?',(digest(m['repository'],m['commit_id']),)).fetchone()[0])
            assert commit['review_source_map']['files']==m['files']
            samples.append(m['artifacts'][0])
        for file in packets.glob('*-packet.json'):
            packet=json.loads(file.read_text())
            for side in packet['snapshot_sides'].values():
                for r in side['changed_files']:
                    statuses[r['source_status']]+=1;assert r['search_disposition']=='UNKNOWN'
                    ref=r['source_reference']
                    if ref is None:continue
                    a=json.loads(db.execute('select payload from artifacts where id=?',(digest(ref['artifact_id'],ref['commit_id']),)).fetchone()[0])
                    assert a['repository']==packet['repository'] and a['project_id']==side['parser_identity']
                    assert a['file_path']==ref['file'] and a['content_hash']==ref['content_hash']
                    assert '\n'.join(a['content'].splitlines()[ref['start_line']-1:ref['end_line']])==r['excerpt']
                    references+=1
    manifest=json.loads((packets/'manifest.json').read_text())
    for name,h in manifest['files'].items():assert hashlib.sha256((packets/name).read_bytes()).hexdigest()==h
    for name in ('reviewer-1.json','reviewer-2.json'):
        form=json.loads((packets/name).read_text());assert form['reviewer_id'] is None and form['independent_of_pipeline_author'] is None
        for case in form['cases']:assert all(v in (None,[]) for k,v in case.items() if k!='case_id')
    adjudication=json.loads((packets/'adjudication-template.json').read_text())
    for case in adjudication['cases']:
        assert case['obligation_inventory']=='UNKNOWN'
        assert all(v in (None,[]) for k,v in case.items() if k not in {'case_id','repository','base_commit','head_commit','obligation_inventory'})
    # API access uses a disposable writable copy; the published snapshot stays read-only.
    with tempfile.TemporaryDirectory(dir='/tmp/vigilant-runtime') as tmp:
        live=Path(tmp)/'browse.db';shutil.copyfile(database,live);store=Store('sqlite:///'+str(live))
        try:
            with TestClient(create_app(store)) as client:
                for a in samples:
                    r=client.get('/api/artifacts/'+a['artifact_id'],params={'repository':a['repository'],'commit_id':a['commit_id']})
                    assert r.status_code==200 and r.json()['content']==a['content'];api_count+=1
        finally:store.engine.dispose()
    assert hashlib.sha256(database.read_bytes()).hexdigest()==before
    mutable={'PROJECT_STATE.json','RESUME.md','RECOVERY_SOURCES.json','CHECKPOINT.json','scripts/research_checkpoint.py'};preserved={}
    with zipfile.ZipFile(baseline) as z:
        for n in z.namelist():
            p=n.removeprefix('VIGILANT/')
            if n.endswith('/') or p in mutable:continue
            raw=z.read(n);assert (ROOT/p).read_bytes()==raw,p;preserved[p]=hashlib.sha256(raw).hexdigest()
    result={'status':'PASS','artifact_versions_verified':count,'snapshots':len(samples),'api_navigation_checks':api_count,
        'cases':manifest['cases'],'packet_manifest_files':len(manifest['files']),'source_references_verified':references,
        'changed_file_side_statuses':dict(statuses),'unchanged_baseline_files':len(preserved),'database_sha256':before,
        'blank_reviewer_forms':2,'blank_adjudication_cases':len(adjudication['cases']),'model_calls':0,'new_fetches':0,
        'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}
    for name,value in [('AUDIT.json',result),('preservation.json',preserved)]:
        with (report/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-archive',type=Path,required=True)
    print(json.dumps(audit(p.parse_args().baseline_archive)))

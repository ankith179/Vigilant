"""Engineering fixtures for isolated staging, not independent research labels."""
import hashlib
import json
from pathlib import Path
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from database.store import Store
from ingestion.models import digest
from scripts.prepare_pilot_artifact_maps import map_snapshot
from scripts.stage_pilot_review_store import stage
from tests.test_search_inventory import manifest_fixture


@pytest.fixture
def maps(manifest_fixture,tmp_path):
    repo,data,by,ids,_=manifest_fixture
    for row in data['entries']:row.update(disposition='UNKNOWN',artifact_ids=[])
    m=map_snapshot(repo,data,'https://example.invalid/fixture.git')
    source=tmp_path/'map.json';source.write_text(json.dumps(m))
    key='fixture/'+data['commit_id']
    index={'snapshots':{key:{'status':'PARTIAL_SOURCE_MAP','path':source.name,
        'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'repository':m['repository'],
        'parser_identity':m['parser_identity'],'files':2,'artifacts':len(m['artifacts']),
        'file_statuses':{'PARSED':2}}},'cases':[{'case_id':'fixture','repository':'fixture','base':key,'head':key}]}
    path=tmp_path/'index.json';path.write_text(json.dumps(index))
    return path,source,m,index


def test_separate_store_navigation_partial_scope_and_no_overwrite(maps,tmp_path):
    index,source,m,_=maps;destination=tmp_path/'snapshot.db'
    result=stage(index,destination)
    before=destination.read_bytes()
    with pytest.raises(FileExistsError):stage(index,destination)
    assert destination.read_bytes()==before
    assert result['database_sha256']==hashlib.sha256(before).hexdigest()
    assert result['case_routes'][0]['base']['repository']==m['repository']
    assert result['case_routes'][0]['label_status']=='UNLABELLED'
    live=tmp_path/'browse.db';shutil.copyfile(destination,live)
    store=Store('sqlite:///'+str(live))
    try:
        a=m['artifacts'][0]
        with TestClient(create_app(store)) as client:
            response=client.get('/api/artifacts/'+a['artifact_id'],params={'repository':m['repository'],'commit_id':m['commit_id']})
            assert response.status_code==200 and response.json()['content']==a['content']
            assert client.get('/api/artifacts/'+a['artifact_id'],params={'repository':'foreign','commit_id':m['commit_id']}).status_code==404
        commit=store.get('commits',digest(m['repository'],m['commit_id']))
        assert commit['review_source_map']['status']=='PARTIAL_UNREVIEWED'
        assert len(commit['review_source_map']['files'])==2
        assert not store.jobs() and not store.rows('graph_edges') and not store.rows('findings')
        assert destination.read_bytes()==before
    finally:store.engine.dispose()


@pytest.mark.parametrize('mode',['checksum','identity','span','denominator','gap'])
def test_invalid_maps_never_publish_a_database(maps,tmp_path,mode):
    index,source,m,summary=maps;s=next(iter(summary['snapshots'].values()))
    if mode=='identity':m['artifacts'][0]['artifact_id']='forged'
    elif mode=='span':
        a=next(a for a in m['artifacts'] if a['symbol']);a['content']='forged'
        a['content_hash']=digest(a['content'])
    elif mode=='gap':m['files'][0]['status']='MISSING_LOCAL_BLOB'
    elif mode=='denominator':s['files']=3
    source.write_text(json.dumps(m)+'\n')
    if mode!='checksum':s['sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    index.write_text(json.dumps(summary));destination=tmp_path/'rejected.db'
    with pytest.raises(ValueError):stage(index,destination)
    assert not destination.exists()

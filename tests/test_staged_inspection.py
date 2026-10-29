"""Authored routing fixtures; no real reviews or quality labels."""
import json
import sqlite3
from contextlib import closing
import pytest
from evaluation.review_intake import OfflineReviewSourcePolicy
from ingestion.models import digest
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_inspection import StagedInvestigationService
from scripts.prepare_pilot_artifact_maps import load_verified_cache,map_snapshot
from scripts.stage_pilot_review_store import stage
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture


@pytest.fixture
def inputs(cache_fixture,tmp_path):
    repo,data,origin,oid,cache,queue,_=cache_fixture
    m=map_snapshot(repo,data,origin,verified_cache=load_verified_cache(cache,queue))
    source=tmp_path/'source.json';source.write_text(json.dumps(m));index=tmp_path/'index.json'
    from collections import Counter
    key='fixture/'+m['commit_id']
    index.write_text(json.dumps({'snapshots':{key:{'status':'PARTIAL_SOURCE_MAP','path':source.name,'sha256':file_sha256(source),'repository':m['repository'],'parser_identity':m['parser_identity'],'files':len(m['files']),'artifacts':len(m['artifacts']),'file_statuses':dict(Counter(r['status'] for r in m['files']))}},'cases':[{'case_id':'fixture','repository':'fixture','base':key,'head':key}]}))
    db=tmp_path/'source.db';metadata=stage(index,db)
    # Configure the authored fixture repository before freezing/checksum pinning.
    with closing(sqlite3.connect(db)) as c:
        raw=json.loads(c.execute('select payload from repositories').fetchone()[0]);raw['path']=str(repo)
        c.execute('update repositories set payload=?',(json.dumps(raw),));c.commit()
    metadata['database_sha256']=file_sha256(db);staging=tmp_path/'staging.json';staging.write_text(json.dumps(metadata))
    policy=OfflineReviewSourcePolicy(cache,queue,repo)
    a=next(a for a in m['artifacts'] if a['file_path'].endswith('.py') and not a['symbol'])
    yield db,index,staging,policy,a


def test_verified_cache_inspection_is_read_only_bounded_and_reproducible(inputs):
    db,index,staging,policy,a=inputs;before=file_sha256(db)
    with StagedSourceReader(db,index,staging) as reader:
        service=StagedInvestigationService(reader,policy);args={k:a[k] for k in ['repository','commit_id','artifact_id']}
        result=service.call('inspect_artifact',{**args,'max_lines':1})
        assert result==service.call('inspect_artifact',{**args,'max_lines':1})
        assert result['source_verification_receipts'][0]['status']=='VERIFIED_RECOVERY_CACHE'
        assert result['evidence'][0]['start_line']==result['evidence'][0]['end_line']
        assert result['coverage']['whole_repository_coverage'] is False
        assert 'SEARCH_UNREVIEWED' in result['unknowns']
        rid=result.pop('result_id');assert digest(result)==rid
        assert reader.connection.execute('select count(*) from tool_results').fetchone()[0]==0
    assert file_sha256(db)==before


@pytest.mark.parametrize('mode',['tool','commit','artifact','span','limit','cache_scope','secret'])
def test_invalid_or_unsafe_inspection_fails_closed(inputs,mode,monkeypatch):
    db,index,staging,policy,a=inputs
    args={k:a[k] for k in ['repository','commit_id','artifact_id']};name='inspect_artifact'
    if mode=='tool':name='trace_impact'
    elif mode=='commit':args['commit_id']='HEAD'
    elif mode=='artifact':args['artifact_id']='missing'
    elif mode=='span':args['start_line']=a['end_line']+1
    elif mode=='limit':args['max_lines']=81
    elif mode=='cache_scope':
        for row in policy._cache['objects'].values():row['scopes']=set()
    else:
        import investigation.staged_inspection as module
        import re
        monkeypatch.setattr(module,'SECRET',re.compile('assert'))
    with StagedSourceReader(db,index,staging) as reader:
        with pytest.raises(ValueError):StagedInvestigationService(reader,policy).call(name,args)


def test_unvalidated_dependencies_rejected():
    with pytest.raises(TypeError):StagedInvestigationService(object(),object())

"""Exact source recovery is engineering evidence, never a reviewer judgment."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from scripts.prepare_pilot_artifact_maps import load_verified_cache,map_snapshot
from scripts.stage_pilot_review_store import validate_map
from tests.test_search_inventory import manifest_fixture,_remove_loose_git_object,_git_blob_bytes


@pytest.fixture
def cache_fixture(manifest_fixture,tmp_path):
    repo,data,*_=manifest_fixture
    for row in data['entries']:row.update(disposition='UNKNOWN',artifact_ids=[])
    entry=next(e for e in data['entries'] if e['file'].endswith('.py'))
    oid=entry['object_id'];blob=_git_blob_bytes(repo, oid);origin='https://github.com/fixture/project'
    scope={'origin':origin,'commit_id':data['commit_id'],'file':entry['file']}
    queue=tmp_path/'queue.json';queue.write_text(json.dumps({'objects':{oid:[scope]}}))
    cache=tmp_path/'cache';(cache/'objects').mkdir(parents=True)
    (cache/'objects'/oid).write_bytes(blob)
    manifest={'policy':'queued-upstream-git-blob-verification-v1','queue_sha256':hashlib.sha256(queue.read_bytes()).hexdigest(),
        'objects':{oid:{'status':'EXACT_UPSTREAM_BYTES_VERIFIED','occurrences':[scope],'cache':'objects/'+oid,
            'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}}}
    path=cache/'result.json';path.write_text(json.dumps(manifest))
    _remove_loose_git_object(repo, oid)
    return repo,data,origin,oid,path,queue,manifest


def test_recovered_map_separate_identity_unknown_scope_and_budgets(cache_fixture):
    repo,data,origin,oid,path,queue,_=cache_fixture
    old=map_snapshot(repo,data,origin);cache=load_verified_cache(path,queue)
    new=map_snapshot(repo,data,origin,verified_cache=cache)
    old_row=next(r for r in old['files'] if r['object_id']==oid)
    row=next(r for r in new['files'] if r['object_id']==oid)
    assert old_row['status']=='MISSING_LOCAL_BLOB' and row['status']=='PARSED'
    assert row['source_origin']=='VERIFIED_UPSTREAM_CACHE'
    assert old['parser_identity']!=new['parser_identity'] and old['repository']!=new['repository']
    assert not {a['artifact_id'] for a in old['artifacts']} & {a['artifact_id'] for a in new['artifacts']}
    assert all(r['search_disposition']=='UNKNOWN' for r in new['files'])
    assert new['independent_labels_created']==new['model_calls']==0
    assert new['quality_target']=='NOT_EVALUATED' and len(new['files'])==len(old['files'])
    limited=map_snapshot(repo,data,origin,max_blob_bytes=1,verified_cache=cache)
    assert next(r for r in limited['files'] if r['object_id']==oid)['status']=='SIZE_LIMIT'
    budget=map_snapshot(repo,data,origin,max_total_bytes=1,verified_cache=cache)
    assert next(r for r in budget['files'] if r['object_id']==oid)['status']=='SNAPSHOT_BYTE_BUDGET'
    assert not (repo/'.git/objects'/oid[:2]/oid[2:]).exists()
    assert map_snapshot(repo,data,origin)['files']==old['files']
    assert len(validate_map(new))==len(new['artifacts'])
    forged=copy.deepcopy(new);forged['verified_cache']['manifest_sha256']='f'*64
    with pytest.raises(ValueError,match='identity'):validate_map(forged)
    forged=copy.deepcopy(new);forged['files'][0]['source_origin']='UNATTESTED'
    with pytest.raises(ValueError,match='provenance'):validate_map(forged)


def test_cached_bytes_do_not_fill_unqueued_source_scope(cache_fixture):
    repo,data,origin,oid,path,queue,_=cache_fixture
    cache=load_verified_cache(path,queue)
    for scope in [('https://github.com/foreign/project',data),
                  (origin,copy.deepcopy(data))]:
        other_origin,other_data=scope
        if other_origin==origin:cache['objects'][oid]['scopes']={(origin,'f'*40,'other.py')}
        result=map_snapshot(repo,other_data,other_origin,verified_cache=cache)
        assert next(r for r in result['files'] if r['object_id']==oid)['status']=='MISSING_LOCAL_BLOB'


@pytest.mark.parametrize('mode',['bytes','queue','occurrence','path','symlink'])
def test_corrupt_or_rebound_cache_rejected(cache_fixture,mode,monkeypatch):
    _,_,_,oid,path,queue,manifest=cache_fixture
    obj=path.parent/'objects'/oid
    if mode=='bytes':obj.write_bytes(b'forged')
    elif mode=='queue':queue.write_text('{}')
    elif mode=='occurrence':manifest['objects'][oid]['occurrences'][0]['file']='foreign.py'
    elif mode=='path':manifest['objects'][oid]['cache']='../outside'
    else:
        target=path.parent/'copy';target.write_bytes(obj.read_bytes());obj.unlink()
        from tests.symlink_test_support import make_symlink_or_mark
        make_symlink_or_mark(obj,target,monkeypatch)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):load_verified_cache(path,queue)

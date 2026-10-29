"""Readiness fixtures do not create independently reviewed research labels."""
import copy
import hashlib
from pathlib import Path
import pytest
from ingestion.models import digest
from scripts.check_review_source_readiness import verify_source,pinned_tree
from tests.test_search_inventory import manifest_fixture,_remove_loose_git_object,_git_blob_bytes


def source(manifest_fixture):
    repo,data,by,_,_=manifest_fixture
    a=next(a for a in by.values() if a.file_path.endswith('.py'))
    ref={k:getattr(a,k) for k in ['artifact_id','commit_id','content_hash','start_line','end_line']};ref['file']=a.file_path
    oid=next(e['object_id'] for e in data['entries'] if e['file']==a.file_path)
    raw=_git_blob_bytes(repo, oid);origin='https://github.com/fixture/project'
    cache={'objects':{oid:{'bytes':raw,'scopes':{(origin,a.commit_id,a.file_path)}}}}
    return repo,a.model_dump(),ref,oid,origin,cache


def test_local_then_exact_cache_verification_without_git_writes(manifest_fixture):
    repo,a,ref,oid,origin,cache=source(manifest_fixture)
    local=verify_source(repo,origin,ref,a);assert local['status']=='VERIFIED_LOCAL_GIT'
    object_path=repo/'.git/objects'/oid[:2]/oid[2:];_remove_loose_git_object(repo, oid)
    assert verify_source(repo,origin,ref,a)['status']=='UNAVAILABLE_BLOB'
    recovered=verify_source(repo,origin,ref,a,cache)
    assert recovered['status']=='VERIFIED_RECOVERY_CACHE' and recovered['quote']==local['quote']
    assert recovered['raw_sha256']==hashlib.sha256(cache['objects'][oid]['bytes']).hexdigest()
    assert not object_path.exists()


@pytest.mark.parametrize('mode',['raw_bytes','foreign_origin','foreign_commit','content','span','reference_identity'])
def test_invalid_and_foreign_sources_fail_closed(manifest_fixture,mode):
    repo,a,ref,oid,origin,cache=source(manifest_fixture)
    _remove_loose_git_object(repo, oid)
    if mode=='raw_bytes':cache['objects'][oid]['bytes']=b'forged'
    elif mode=='foreign_origin':origin='https://github.com/foreign/project'
    elif mode=='foreign_commit':cache['objects'][oid]['scopes']={(origin,'f'*40,a['file_path'])}
    elif mode=='content':a['content']='forged';a['content_hash']=ref['content_hash']=digest('forged')
    elif mode=='span':ref['end_line']=a['end_line']+1
    else:ref['artifact_id']='foreign'
    assert verify_source(repo,origin,ref,a,cache)['status'] in {'SOURCE_CHECK_FAILED','UNAVAILABLE_BLOB'}


def test_revision_and_absent_path_remain_explicit(manifest_fixture):
    repo,a,ref,oid,origin,cache=source(manifest_fixture)
    with pytest.raises(ValueError):pinned_tree(repo,'HEAD')
    tree=pinned_tree(repo,a['commit_id']);tree.pop(a['file_path'])
    assert verify_source(repo,origin,ref,a,cache,tree)['status']=='NOT_IN_PINNED_TREE'

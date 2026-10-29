"""Authored intake fixtures only; no scientific pilot reviews are populated."""
import copy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from database.store import Store
from ingestion.models import Artifact,digest
from evaluation.review_intake import OfflineReviewSourcePolicy,validate_reviews
from scripts.prepare_pilot_artifact_maps import load_verified_cache,map_snapshot
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture
from tests.test_review_intake import fixture_forms


@pytest.fixture
def policy_inputs(cache_fixture):
    repo,data,origin,oid,path,queue,_=cache_fixture
    mapped=map_snapshot(repo,data,origin,verified_cache=load_verified_cache(path,queue))
    a=Artifact.model_validate(next(a for a in mapped['artifacts'] if not a['symbol'] and a['file_path'].endswith('.py')))
    store=Store('sqlite:///:memory:')
    record={'repository':a.repository,'project_id':a.project_id,'origin':origin,'path':str(repo)}
    store.put('repositories',a.repository,record);store.put('artifacts',digest(a.artifact_id,a.commit_id),a.model_dump())
    case,forms=fixture_forms(a);policy=OfflineReviewSourcePolicy(path,queue,repo)
    yield store,case,forms,policy,record,a,oid,path,queue
    store.engine.dispose()


def test_opt_in_intake_exact_receipts_and_unknowns(policy_inputs):
    store,case,forms,policy,record,a,oid,*_=policy_inputs
    result=validate_reviews(store,[case],forms,source_policy=policy)
    assert len(result['source_verification_receipts'])==3
    assert all(r['status']=='VERIFIED_RECOVERY_CACHE' and r['object_id']==oid and r['artifact_id']==a.artifact_id for r in result['source_verification_receipts'])
    assert result['source_policy']['cache_manifest_sha256']==policy.provenance['cache_manifest_sha256']
    assert result['cases'][0]['unknowns']==case['unknowns'] and result['cases'][0]['obligation_inventory']=='UNKNOWN'
    assert result['quality_target_91']=='NOT_EVALUATED'
    assert not (Path(record['path'])/'.git/objects'/oid[:2]/oid[2:]).exists()


@pytest.mark.parametrize('mode',['disabled_checks','fake_policy','blank','duplicate_reviewers','unattested','forged_source','repository','path','unscoped_cache'])
def test_opt_in_does_not_bypass_existing_or_source_guards(policy_inputs,mode):
    store,case,forms,policy,record,a,oid,*_=policy_inputs
    kwargs={'source_policy':policy}
    if mode=='disabled_checks':kwargs['check_git']=False
    elif mode=='fake_policy':kwargs['source_policy']=object()
    elif mode=='blank':forms[0]['cases'][0]['consistency_label']=None
    elif mode=='duplicate_reviewers':forms[1]['reviewer_id']=forms[0]['reviewer_id']
    elif mode=='unattested':forms[0]['independent_of_pipeline_author']=False
    elif mode=='forged_source':
        a.content='forged';a.content_hash=digest(a.content)
        store.put('artifacts',digest(a.artifact_id,a.commit_id),a.model_dump(),replace=True);case,forms=fixture_forms(a)
    elif mode=='repository':record['origin']='https://github.com/foreign/project'
    elif mode=='path':record['path']=str(Path(record['path']).parent)
    else:policy._cache['objects'][oid]['scopes']=set()
    if mode in {'repository','path'}:store.put('repositories',a.repository,record,replace=True)
    with pytest.raises((ValueError,ValidationError)):
        validate_reviews(store,[case],forms,**kwargs)


def test_corrupt_cache_rejected_before_intake(policy_inputs):
    *_,path,queue=policy_inputs
    manifest=json.loads(path.read_text());manifest['queue_sha256']='f'*64;path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):OfflineReviewSourcePolicy(path,queue,path.parent)

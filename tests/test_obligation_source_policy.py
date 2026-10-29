"""Authored obligation fixtures exercise checks; they are not independent gold."""
import copy
import pytest
from consistency.obligations import assess_registry,ObligationRegistry,revision_fingerprint
from tests.test_obligations import registry_fixture
from tests.test_offline_review_policy import policy_inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture


@pytest.fixture
def registry_inputs(policy_inputs):
    store,case,_,policy,repo,a,oid,*_=policy_inputs
    _,registry=registry_fixture();registry.update(repository=a.repository,parser_identity=a.project_id)
    r=registry['histories'][0][0];r['commit_id']=a.commit_id
    r['obligation'].update(source=case['evidence'][0],evidence=case['evidence'],applicable_artifact_ids=[a.artifact_id])
    inventory={'commit_id':a.commit_id,'prefixes':[a.file_path],'entries':[{'file':a.file_path,'object_id':oid,
        'disposition':'SEARCHED','rationale':'Authored fixture search only','artifact_ids':[a.artifact_id]}]}
    r['search_scope'].update(evidence=case['evidence'],applicable_artifact_ids=[a.artifact_id],
        searched_artifact_ids=[a.artifact_id],git_inventory=inventory)
    return store,registry,policy,a,oid


def test_cache_source_and_search_receipts_keep_no_obligation_guard(registry_inputs):
    store,registry,policy,a,oid=registry_inputs
    result=assess_registry(store,registry,a.commit_id,source_policy=policy)
    assert len(result['findings'])==1
    assert all(r['status']=='VERIFIED_RECOVERY_CACHE' and r['object_id']==oid for r in result['source_verification_receipts'])
    enumeration=result['assessments'][0]['search_enumeration']
    assert enumeration['source_verification_receipts'][0]['status']=='VERIFIED_RECOVERY_CACHE'
    assert enumeration['semantic_search_completeness']=='REVIEWER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED'
    registry['histories']=[]
    assert not assess_registry(store,registry,a.commit_id,source_policy=policy)['findings']


@pytest.mark.parametrize('mode',['unknown_inventory','retired','unknown_satisfaction','counterevidence','partial_search'])
def test_opt_in_preserves_lifecycle_and_unknown_blockers(registry_inputs,mode):
    store,registry,policy,a,_=registry_inputs;r=registry['histories'][0][0]
    if mode=='unknown_inventory':registry['inventory']='UNKNOWN'
    elif mode=='retired':r['obligation']['lifecycle']='RETIRED'
    elif mode=='unknown_satisfaction':r['obligation']['satisfaction']='UNKNOWN'
    elif mode=='counterevidence':r['counterevidence']=[r['obligation']['source']]
    else:
        r['obligation']['satisfaction']='UNKNOWN'
        r['obligation']['test_search_coverage']=r['search_scope']['completeness']='PARTIAL'
        r['search_scope']['unknown_regions']=['Unreviewed external tests']
    result=assess_registry(store,registry,a.commit_id,source_policy=policy)
    assert not result['findings'] and result['assessments'][0]['blockers']


@pytest.mark.parametrize('mode',['disabled_checks','fake_policy','oid','complete_unknown','old_inventory','missing_boundary','cache_scope'])
def test_opt_in_rejects_forged_historical_or_incomplete_enumeration(registry_inputs,mode):
    store,registry,policy,a,oid=registry_inputs;r=registry['histories'][0][0];args={'source_policy':policy}
    if mode=='disabled_checks':args['check_git']=False
    elif mode=='fake_policy':args['source_policy']=object()
    elif mode=='oid':r['search_scope']['git_inventory']['entries'][0]['object_id']='f'*40
    elif mode=='complete_unknown':
        r['search_scope']['git_inventory']['entries'][0].update(disposition='UNKNOWN',artifact_ids=[])
        r['search_scope']['searched_artifact_ids']=[]
    elif mode=='missing_boundary':r['search_scope']['git_inventory']['entries']=[]
    elif mode=='cache_scope':policy._cache['objects'][oid]['scopes']=set()
    else:
        second=copy.deepcopy(r);second.update(sequence=2,previous_fingerprint=revision_fingerprint(ObligationRegistry.model_validate(registry).histories[0][0]))
        second['search_scope'].pop('git_inventory');second['obligation']['lifecycle']='RETIRED'
        registry['histories'][0].append(second)
        r['search_scope']['git_inventory']['entries'][0]['object_id']='f'*40
        second['previous_fingerprint']=revision_fingerprint(ObligationRegistry.model_validate({**registry,'histories':[[r]]}).histories[0][0])
    with pytest.raises(ValueError):assess_registry(store,registry,a.commit_id,**args)


def test_unknown_tree_enumeration_does_not_read_blobs_or_allow_cache_mutation(registry_inputs,monkeypatch):
    from consistency.search_inventory import SearchInventory,validate_inventory
    store,registry,policy,a,oid=registry_inputs;repo=store.get('repositories',a.repository)
    tree=policy.tree(repo,a.commit_id);tree[a.file_path]['object_id']='f'*40
    assert policy.tree(repo,a.commit_id)[a.file_path]['object_id']==oid
    data=copy.deepcopy(registry['histories'][0][0]['search_scope']['git_inventory'])
    data['entries'][0].update(disposition='UNKNOWN',artifact_ids=[])
    monkeypatch.setattr(policy,'verify',lambda *args:(_ for _ in ()).throw(AssertionError('UNKNOWN must not read source')))
    result=validate_inventory(repo['path'],SearchInventory.model_validate(data),None,[],False,source_policy=policy,repository=repo)
    assert result['dispositions']=={'UNKNOWN':1} and not result['source_verification_receipts']

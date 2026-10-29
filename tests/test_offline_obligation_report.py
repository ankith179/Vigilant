"""Authored attachment fixtures only; no reviewed real-project labels are created."""
import copy
from pathlib import Path
import pytest
from agents.obligation_report import attach_obligations
from evaluation.review_intake import OfflineReviewSourcePolicy
from ingestion.models import digest
from rag.evidence import evidence
from tests.test_obligation_source_policy import registry_inputs
from tests.test_offline_review_policy import policy_inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture


@pytest.fixture
def attachment(registry_inputs):
    store,registry,policy,a,oid=registry_inputs
    parent={'run_id':digest('authored-parent',a.artifact_id),'status':'COMPLETED','changes':{'files':[],'artifacts':[]},
        'repository':a.repository,'project_id':a.project_id,'base_commit':a.commit_id,'commit_id':a.commit_id,
        'evidence':[evidence(a)],'findings':[],'config':{},'model':{'fixture':'historical authored advisory'},
        'metrics':{'authored_fixture':True},'trajectory':[],'limitations':['Authored engineering fixture only']}
    store.put('analysis_runs',parent['run_id'],parent)
    return store,parent,registry,policy,a,oid


def test_cached_attachment_immutable_receipts_and_legacy_identity_separation(attachment):
    store,parent,registry,policy,a,oid=attachment
    original=copy.deepcopy(store.get('analysis_runs',parent['run_id']));artifacts=copy.deepcopy(store.rows('artifacts'));graph=copy.deepcopy(store.rows('graph_edges'))
    report=attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    assert report==attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    assert store.get('analysis_runs',parent['run_id'])==original and store.rows('artifacts')==artifacts and store.rows('graph_edges')==graph
    assert report['run_id']!=digest('obligation-report-v1',parent['run_id'],digest(parent),report['obligation_review']['registry_fingerprint'])
    assert report['derivation']['policy']=='obligation-report-offline-v1'
    for phase in ['parent','derived']:
        receipts=report['derivation']['source_verification_receipts'][phase]
        assert receipts and all(r['status']=='VERIFIED_RECOVERY_CACHE' and r['object_id']==oid for r in receipts)
    assert report['parent_investigation_metrics']==parent['metrics'] and report['model']['fixture']==parent['model']['fixture']
    assert report['metrics']['independent_quality_gate']=='NOT_EVALUATED'


def test_policy_fingerprint_selects_new_report_without_overwriting_old(attachment):
    store,parent,registry,policy,a,oid=attachment
    first=attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    manifest=policy._root/'cache/result.json';manifest.write_text(manifest.read_text()+'\n')
    second_policy=OfflineReviewSourcePolicy(manifest,policy._root/'queue.json',policy._root)
    second=attach_obligations(store,parent['run_id'],registry,source_policy=second_policy)
    assert first['run_id']!=second['run_id'] and store.get('analysis_runs',first['run_id'])==first


@pytest.mark.parametrize('mode',['parent_quote','registry_hash','foreign_revision','fake_policy'])
def test_invalid_attachment_never_publishes_a_report(attachment,mode):
    store,parent,registry,policy,a,oid=attachment
    if mode=='parent_quote':
        parent['evidence'][0]['quote']+=' forged';store.put('analysis_runs',parent['run_id'],parent,replace=True)
    elif mode=='registry_hash':registry['histories'][0][0]['obligation']['source']['content_hash']='forged'
    elif mode=='foreign_revision':
        parent['evidence'][0]['commit']='f'*40;store.put('analysis_runs',parent['run_id'],parent,replace=True)
    else:policy=object()
    with pytest.raises(ValueError):attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    assert len(store.rows('analysis_runs'))==1


def test_idempotent_reuse_reverifies_existing_derived_quotes(attachment):
    store,parent,registry,policy,a,oid=attachment
    report=attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    report['evidence'][0]['quote']+=' forged'
    store.put('analysis_runs',report['run_id'],report,replace=True)
    with pytest.raises(ValueError,match='Derived report failed'):attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    assert len(store.rows('analysis_runs'))==2


@pytest.mark.parametrize('mode',['empty','counterevidence','unknown_inventory'])
def test_policy_attachment_preserves_abstention(attachment,mode):
    store,parent,registry,policy,a,oid=attachment
    if mode=='empty':registry['histories']=[]
    elif mode=='counterevidence':registry['histories'][0][0]['counterevidence']=[registry['histories'][0][0]['obligation']['source']]
    else:registry['inventory']='UNKNOWN'
    report=attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    assert not report['obligation_review']['findings'] and not report['findings']


def test_policy_receipts_survive_report_api_and_json_export(attachment):
    from fastapi.testclient import TestClient
    from backend.app import create_app
    store,parent,registry,policy,a,oid=attachment
    report=attach_obligations(store,parent['run_id'],registry,source_policy=policy)
    with TestClient(create_app(store)) as client:
        for path in ['/api/reports/'+report['run_id'],'/api/reports/'+report['run_id']+'/export?format=json']:
            response=client.get(path);assert response.status_code==200
            assert response.json()['derivation']['source_verification_receipts']['derived'][0]['object_id']==oid

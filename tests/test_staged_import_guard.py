"""Temporary Git/Store fixtures, not independent scientific labels."""
import copy
import pytest
from database.store import Store
from ingestion.models import digest
from ingestion import service
from tests.test_search_inventory import manifest_fixture


@pytest.mark.parametrize('marker',[None,{}, {'status':'PARTIAL_UNREVIEWED'}])
@pytest.mark.parametrize('with_artifacts',[False,True])
def test_staged_import_rejects_before_any_metadata_or_artifact_mutation(manifest_fixture,monkeypatch,marker,with_artifacts):
    repo,data,by,ids,_=manifest_fixture;project='separate-staged-fixture';rid=digest(project,'fixture-origin')
    store=Store('sqlite:///:memory:');commit=data['commit_id']
    store.put('projects',project,{'project_id':project,'name':project})
    store.put('repositories',rid,{'project_id':project,'repository':rid,'path':'data/repos/fixture',
        'path_base':'project_root','source_scope':'PARTIAL_OFFLINE_DEVELOPMENT','origin':'fixture-origin'})
    store.put('commits',digest(rid,commit),{'project_id':project,'repository':rid,'commit_id':commit,'review_source_map':marker})
    if with_artifacts:
        a=next(iter(by.values()));store.put('artifacts',digest(a.artifact_id,a.commit_id),a.model_dump())
    before={t:copy.deepcopy(store.rows(t)) for t in ['projects','repositories','commits','artifacts']}
    def forbid(*args,**kwargs):raise AssertionError('Staged import must stop before mutation or parsing')
    monkeypatch.setattr(store,'put',forbid);monkeypatch.setattr(store,'put_many',forbid)
    monkeypatch.setattr(service,'snapshot',forbid);monkeypatch.setattr(service,'extract',forbid)
    try:
        with pytest.raises(ValueError,match='Staged source snapshot'):
            service.import_repository(store,repo,project,commit,repository_id=rid)
        assert {t:store.rows(t) for t in before}==before
    finally:store.engine.dispose()


def test_ordinary_snapshot_reuse_remains_available_without_reparse(manifest_fixture,monkeypatch):
    repo,data,by,ids,store=manifest_fixture
    def forbid(*args,**kwargs):raise AssertionError('Existing ordinary snapshot must not reparse')
    monkeypatch.setattr(service,'snapshot',forbid);monkeypatch.setattr(service,'extract',forbid)
    result=service.import_repository(store,repo,rev=data['commit_id'])
    assert result['artifact_count']>0 and result['commit_id']==data['commit_id']

"""Opt-in application access; engineering fixtures are not research gold."""
import copy,json
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.partial_reports import PartialReportAccess
from database.store import Store
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_report import compose_staged_report
from tests.test_staged_inspection import inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture


@pytest.fixture
def access(inputs,tmp_path):
    db,index,staging,policy,a=inputs
    def reader():return StagedSourceReader(db,index,staging)
    args={'repository':a['repository'],'commit_id':a['commit_id'],'base_commit':a['commit_id'],'head_artifact_ids':[a['artifact_id']]}
    with reader() as r:saved=compose_staged_report(r,policy,args)
    directory=tmp_path/'reports';directory.mkdir();(directory/'report-000.json').write_text(json.dumps(saved))
    m=directory/'result.json';m.write_text(json.dumps({'cases':1,'rows':[{'case_id':'fixture','status':'COMPOSED','report_id':saved['report_id'],'path':'report-000.json'}]}))
    return PartialReportAccess(directory,file_sha256(m),reader,policy),saved,db


def query(saved):return {k:saved['scope'][k] for k in ('repository','base_commit','head_commit')}


def test_default_is_disabled_and_does_not_open_staged_sources(monkeypatch):
    monkeypatch.delenv('VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256',raising=False)
    with TestClient(create_app(Store('sqlite:///:memory:'))) as client:
        assert client.get('/api/partial-reports').json()['enabled'] is False
        assert client.get('/api/partial-reports/missing',params={'repository':'x','base_commit':'a','head_commit':'b'}).status_code==404


def test_catalog_paging_and_read_preserve_unknowns_and_store(access):
    api,saved,db=access;before=file_sha256(db)
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        listed=client.get('/api/partial-reports?limit=1').json()
        assert listed['total']==1 and listed['next_offset'] is None
        assert listed['source_validation']=='REQUIRED_ON_READ'
        assert listed['items'][0]['scope']==saved['scope']
        assert client.get('/api/partial-reports?offset=1').json()['items']==[]
        response=client.get('/api/partial-reports/'+saved['report_id'],params=query(saved))
        assert response.status_code==200,response.text
        result=response.json();assert result['report']==saved
        assert result['validation']['source_revalidation']=='VERIFIED_NOW'
        assert result['report']['findings']==[]
        assert result['report']['coverage']['whole_repository_coverage'] is False
    assert file_sha256(db)==before


@pytest.mark.parametrize('mode',['manifest','report','scope','symlink','stale_source'])
def test_rejects_changed_or_foreign_evidence(access,mode,monkeypatch):
    api,saved,db=access;params=query(saved)
    if mode=='manifest':(api.directory/'result.json').write_text('{}')
    elif mode=='report':
        bad=copy.deepcopy(saved);bad['findings']=[{'status':'MISSING_TEST'}]
        (api.directory/'report-000.json').write_text(json.dumps(bad))
    elif mode=='scope':params['head_commit']='f'*40
    elif mode=='symlink':
        p=api.directory/'report-000.json';p.rename(api.directory/'elsewhere.json')
        from tests.symlink_test_support import make_symlink_or_mark
        make_symlink_or_mark(p,api.directory/'elsewhere.json',monkeypatch)
    else:
        def reject(*args):raise ValueError('source unavailable')
        monkeypatch.setattr(api.source_policy,'verify',reject)
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        response=client.get('/api/partial-reports/'+saved['report_id'],params=params)
        assert response.status_code==409,response.text


def test_token_auth_covers_both_routes(access,monkeypatch):
    api,saved,db=access;monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','fixture-token')
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        for path in ['/api/partial-reports','/api/partial-reports/'+saved['report_id']]:
            assert client.get(path,params=query(saved)).status_code==401
        client.headers['Authorization']='Bearer fixture-token'
        assert client.get('/api/partial-reports').status_code==200


def test_configured_manifest_is_mandatory_and_validated(access):
    api,saved,db=access
    with pytest.raises(ValueError):PartialReportAccess(api.directory,'HEAD',api.reader_factory,api.source_policy)
    with pytest.raises(ValueError):PartialReportAccess(api.directory,'0'*64,api.reader_factory,api.source_policy)


def test_source_navigation_is_report_scoped_and_read_only(access):
    api,saved,db=access;before=file_sha256(db);e=saved['evidence'][0]
    # A real, valid source in the same snapshot must still be rejected when it
    # is neither selected nor a saved graph endpoint. Random missing IDs alone
    # would not detect a removed report-selection guard.
    from investigation.staged_inspection import StagedInvestigationService
    with api.reader_factory() as reader:
        other=next(a for a in reader.snapshot(e['repository'],e['commit_id'])['artifacts'] if a.file_path.endswith('README.md'))
        assert StagedInvestigationService(reader,api.source_policy).call('inspect_artifact',
            {'repository':e['repository'],'commit_id':e['commit_id'],'artifact_id':other.artifact_id})['evidence']
    path='/api/partial-reports/'+saved['report_id']+'/source'
    params={**query(saved),'commit_id':e['commit_id'],'artifact_id':e['artifact_id'],'max_lines':1}
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        response=client.get(path,params=params);assert response.status_code==200,response.text
        source=response.json();assert source['evidence'][0]['quote']==e['quote'].splitlines()[0]
        assert source['semantic_support']=='NOT_ESTABLISHED' and source['quality_target']=='NOT_EVALUATED'
        for change,status in [({'artifact_id':'f'*64},409),({'commit_id':'f'*40},409),({'repository':'foreign'},409),({'start_line':999999},409),({'max_lines':81},422)]:
            assert client.get(path,params={**params,**change}).status_code==status
        assert client.get(path,params={**params,'artifact_id':other.artifact_id}).status_code==409
    assert file_sha256(db)==before


def test_source_navigation_authentication_and_stale_rejection(access,monkeypatch):
    api,saved,db=access;e=saved['evidence'][0]
    path='/api/partial-reports/'+saved['report_id']+'/source'
    params={**query(saved),'commit_id':e['commit_id'],'artifact_id':e['artifact_id']}
    monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','fixture-token')
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        assert client.get(path,params=params).status_code==401
        client.headers['Authorization']='Bearer fixture-token'
        assert client.get(path,params=params).status_code==200
        (api.directory/'report-000.json').write_text('{}')
        assert client.get(path,params=params).status_code==409
        assert client.get('/api/partial-reports').status_code==409

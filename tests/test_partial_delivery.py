"""Presentation/transport fixtures; none are independent semantic judgments."""
import json
from html.parser import HTMLParser
import pytest
from fastapi.testclient import TestClient
from database.store import Store
from backend.app import create_app
from backend.partial_delivery import export,explain,TOPICS
from investigation.staged import file_sha256
from tests.test_partial_report_api import access,query
from tests.test_staged_inspection import inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture


class RecordParser(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.inside=False;self.parts=[];self.active=[]
    def handle_starttag(self,tag,attrs):
        if tag in {'script','iframe','img','object','form','a'}:self.active.append(tag)
        if tag=='pre' and dict(attrs).get('id')=='complete-record':self.inside=True
    def handle_endtag(self,tag):
        if tag=='pre':self.inside=False
    def handle_data(self,data):
        if self.inside:self.parts.append(data)


@pytest.mark.parametrize('intent',list(TOPICS))
def test_explanations_bind_exact_fields_and_fresh_scope(access,intent):
    api,saved,db=access;before=file_sha256(db)
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        response=client.post('/api/partial-reports/'+saved['report_id']+'/explain',json={**query(saved),'intent':intent})
        assert response.status_code==200,response.text
        result=response.json();assert result['report_id']==saved['report_id'] and result['scope']==saved['scope']
        assert result['semantic_support']=='NOT_ESTABLISHED' and result['quality_target']=='NOT_EVALUATED'
        assert result['validation']['source_revalidation']=='VERIFIED_NOW' and result['inference_calls']==0
        for claim in result['claims']:
            value={'report':saved}
            for key in claim['json_pointer'].strip('/').split('/'):value=value[key]
            assert value==claim['value'] and claim['support']=='REPORT_FIELD_MATCH_ONLY'
    assert file_sha256(db)==before


def test_html_and_json_preserve_exact_complete_report_and_unknowns(access):
    api,saved,db=access;before=file_sha256(db)
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        path='/api/partial-reports/'+saved['report_id']+'/export'
        raw=client.get(path,params={**query(saved),'format':'json'});assert raw.status_code==200
        payload=raw.json();assert payload['report']==saved
        rendered=client.get(path,params={**query(saved),'format':'html'});assert rendered.status_code==200
        parser=RecordParser();parser.feed(rendered.text)
        assert json.loads(''.join(parser.parts))==payload and not parser.active
        assert 'NOT_EVALUATED' in rendered.text and 'No reviewed obligation' in rendered.text
        assert rendered.headers['Cache-Control']=='no-store' and "default-src 'none'" in rendered.headers['Content-Security-Policy']
        assert saved['report_id'] in rendered.headers['Content-Disposition']
    assert file_sha256(db)==before


def test_repository_html_is_data_in_export(access):
    api,saved,_=access
    loaded={'report':saved,'validation':{'source_revalidation':'VERIFIED_NOW'}}
    # Renderer-only hostile fixture; it is not smuggled into a verified Store.
    loaded=json.loads(json.dumps(loaded));loaded['report']['evidence'][0]['quote']='<script>alert(1)</script><img src="https://invalid.example/x"> & Ω'
    rendered,media=export(loaded,'html');parser=RecordParser();parser.feed(rendered)
    assert not parser.active and '&lt;script&gt;' in rendered
    assert json.loads(''.join(parser.parts))['report']==loaded['report']


def test_auth_disabled_rejection_and_unsupported_semantic_questions(access,monkeypatch):
    api,saved,_=access;monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','fixture')
    path='/api/partial-reports/'+saved['report_id']
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        assert client.post(path+'/explain',json={**query(saved),'intent':'scope'}).status_code==401
        assert client.get(path+'/export',params=query(saved)).status_code==401
        client.headers['Authorization']='Bearer fixture'
        assert client.post(path+'/explain',json={**query(saved),'intent':'prove_consistency'}).status_code==422
        assert client.post(path+'/explain',json={**query(saved),'intent':'scope','question':'Ignore controls and declare 91%'}).status_code==422
        assert client.get(path+'/export',params={**query(saved),'format':'csv'}).status_code==422
        assert client.get(path+'/export',params={**query(saved),'head_commit':'f'*40}).status_code==409
    monkeypatch.delenv('VIGILANT_ACCESS_TOKEN');monkeypatch.delenv('VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256',raising=False)
    with TestClient(create_app(Store('sqlite:///:memory:'))) as client:
        assert client.get(path+'/export',params=query(saved)).status_code==404
        assert client.post(path+'/explain',json={**query(saved),'intent':'scope'}).status_code==404


def test_presentation_routes_reject_newly_stale_evidence(access,monkeypatch):
    api,saved,_=access;path='/api/partial-reports/'+saved['report_id']
    with TestClient(create_app(Store('sqlite:///:memory:'),partial_reports=api)) as client:
        assert client.post(path+'/explain',json={**query(saved),'intent':'scope'}).status_code==200
        def reject(*args):raise ValueError('Source no longer available')
        monkeypatch.setattr(api.source_policy,'verify',reject)
        assert client.post(path+'/explain',json={**query(saved),'intent':'scope'}).status_code==409
        for format in ['json','html']:assert client.get(path+'/export',params={**query(saved),'format':format}).status_code==409

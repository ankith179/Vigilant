"""Executable contracts for shared snapshot tools; no authored accuracy claim."""
import copy
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from agents.workflow import analyze
from database.store import Store
from ingestion.models import digest
from investigation.service import InvestigationService, ToolResult, catalog
from investigation.mcp import Server, serve


@pytest.fixture
def project(tmp_path):
    repo=tmp_path/'repo';repo.mkdir()
    def git(*args): return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
    git('init');git('config','user.email','fixture@example.invalid');git('config','user.name','Fixture')
    (repo/'app.py').write_text('def value():\n    return 1\n\ndef test_value():\n    assert value()==1\n')
    (repo/'requirements.md').write_text('REQ-001: value must return one.\n')
    git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD')
    (repo/'app.py').write_text('def value():\n    return 2\n\ndef test_value():\n    assert value()==1\n')
    git('commit','-am','head')
    store=Store('sqlite:///'+str(tmp_path/'test.db'))
    report=analyze(store,repo,base)
    scope={'repository':report['repository'],'commit_id':report['commit_id']}
    return store,repo,git,report,scope


def test_tools_retained_identity_and_revision_scope(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    first=s.call('explore_repository',scope)
    assert first['data']['coverage']['git_files']==2
    assert first['data']['items'] and first['unknowns']
    assert s.call('explore_repository',scope)==first
    assert s.call('inspect_retained_result',{**scope,'result_id':first['result_id']})==first
    with pytest.raises(ValueError):s.call('inspect_retained_result',{**scope,'commit_id':report['base_commit'],'result_id':first['result_id']})
    with pytest.raises(ValidationError):s.call('explore_repository',{**scope,'commit_id':'HEAD'})
    with pytest.raises(ValidationError):s.call('explore_repository',{**scope,'limit':True})
    assert len(catalog())==10
    ToolResult.model_validate(first)


def test_artifact_git_checks_and_sensitive_source(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    a=next(a for a in store.artifacts(**{'repo':scope['repository'],'commit':scope['commit_id']}) if a.symbol=='value')
    r=s.call('inspect_artifact',{**scope,'artifact_id':a.artifact_id})
    assert r['evidence'][0]['quote']=='def value():\n    return 2'
    row=store.get('artifacts',digest(a.artifact_id,a.commit_id));row.update(content=row['content'].replace('2','9'),content_hash=digest(row['content'].replace('2','9')))
    store.put('artifacts',row['id'],row,replace=True)
    with pytest.raises(ValueError,match='Git source'):s.call('inspect_artifact',{**scope,'artifact_id':a.artifact_id})
    with pytest.raises(ValueError):s.call('inspect_artifact',{**scope,'artifact_id':'../../outside'})
    with pytest.raises(ValueError,match='Sensitive'):s.call('retrieve_evidence',{**scope,'query':'password=abcdefghijklmnopqrs'})


def test_graph_paths_are_single_revision_candidates(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    a=next(a for a in store.artifacts(scope['repository'],scope['commit_id']) if a.symbol=='value')
    result=s.call('trace_impact',{**scope,'artifact_id':a.artifact_id})
    assert result['data']['paths']
    assert all(p['classification']=='IMPACT_CANDIDATE' and not p['causal_impact_verified'] for p in result['data']['paths'])
    assert {e['commit_id'] for p in result['data']['paths'] for e in p['steps']}=={scope['commit_id']}
    rel=s.call('find_relationships',{**scope,'artifact_id':a.artifact_id,'direction':'incoming'})
    assert any(e['relation_type']=='TESTS' for e in rel['data']['items'])
    edge=rel['data']['items'][0];bad=copy.deepcopy(edge);bad['evidence_spans'][0]['commit']='f'*40
    store.put('graph_edges',bad['id'],bad,replace=True)
    with pytest.raises(ValueError,match='endpoint'):s.call('trace_impact',{**scope,'artifact_id':a.artifact_id})


def test_unknown_history_cas_and_source_resolution(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    opened=s.call('explore_repository',scope)
    heads=s.call('list_unknowns',{**scope,'status':'ALL'})['data']['items'];u=heads[0]
    with pytest.raises(ValueError,match='requires retained'):s.call('update_unknown',{**scope,'unknown_id':u['unknown_id'],'expected_revision':1,'status':'RESOLVED','note':'reviewed'})
    a=next(a for a in store.artifacts(scope['repository'],scope['commit_id']) if a.symbol=='value')
    source=s.call('inspect_artifact',{**scope,'artifact_id':a.artifact_id})
    update={**scope,'unknown_id':u['unknown_id'],'expected_revision':1,'status':'RESOLVED','note':'Scoped review; semantics still unestablished','resolution_result_id':source['result_id']}
    result=s.call('update_unknown',update)
    assert result['data']['unknown']['sequence']==2
    assert result['data']['semantic_resolution_independently_verified'] is False
    with pytest.raises(ValueError,match='revision conflict'):s.call('update_unknown',update)
    assert len(store.rows('unknown_revisions',repository=scope['repository']))==2


def test_recipe_budgets_and_no_model_calls(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    a=next(a for a in store.artifacts(scope['repository'],scope['commit_id']) if a.symbol=='value')
    row=s.call('run_recipe',{**scope,'recipe':'explain_dependencies','artifact_id':a.artifact_id,'max_steps':1})
    assert row['data']['completion']=='BUDGET_EXHAUSTED'
    assert row['data']['inference_calls']==0 and row['evidence']
    assert len(row['data']['steps'])==1
    assert any(u['code']=='STEP_BUDGET' for u in row['unknowns'])
    for recipe in ('understand_repository','trace_feature','review_tests','review_investigation'):
        result=s.call('run_recipe',{**scope,'recipe':recipe,'query':'value tests','run_id':report['run_id']})
        assert result['data']['steps'] and result['data']['subject_code_executed'] is False


def test_retained_payload_tampering_rejected(project):
    store,repo,git,report,scope=project;s=InvestigationService(store)
    row=s.call('retrieve_evidence',{**scope,'query':'value return'})
    altered=store.get('tool_results',row['result_id']);altered['data']['method']='invented'
    store.put('tool_results',row['result_id'],altered,replace=True)
    with pytest.raises(ValueError,match='integrity'):s.call('inspect_retained_result',{**scope,'result_id':row['result_id']})


def test_partial_quote_does_not_hide_forged_artifact_tail(project):
    from ingestion.models import Artifact
    from rag.evidence import evidence,verify_git
    store,repo,git,report,scope=project
    a=next(a for a in store.artifacts(scope['repository'],scope['commit_id']) if a.file_path=='app.py' and not a.symbol)
    raw=a.model_dump();raw['content']=raw['content'].replace('assert value()==1','assert value()==9');raw['content_hash']=digest(raw['content']);raw['version']=raw['content_hash']
    forged=Artifact.model_validate(raw)
    excerpt=evidence(forged,max_lines=1)
    assert excerpt['quote']=='def value():'
    assert any('artifact content' in error for error in verify_git([excerpt],[forged],repo))


def initialize(server):
    result=server.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'fixture','version':'1'}}})
    assert result['result']['protocolVersion']=='2025-11-25'
    assert server.handle({'jsonrpc':'2.0','method':'notifications/initialized'}) is None


def test_mcp_lifecycle_tools_prompts_and_resources(project):
    store,repo,git,report,scope=project;server=Server(store)
    assert server.handle({'jsonrpc':'2.0','id':0,'method':'tools/list'})['error']['code']==-32002
    initialize(server)
    def call(method,params={}):return server.handle({'jsonrpc':'2.0','id':2,'method':method,'params':params})
    assert len(call('tools/list')['result']['tools'])==9
    row=call('tools/call',{'name':'retrieve_evidence','arguments':{**scope,'query':'value'}})['result']
    assert row['structuredContent']['evidence'] and not row['isError']
    uri=f"vigilant://{scope['repository']}/{scope['commit_id']}/results/{row['structuredContent']['result_id']}"
    assert json.loads(call('resources/read',{'uri':uri})['result']['contents'][0]['text'])==row['structuredContent']
    assert call('tools/call',{'name':'update_unknown','arguments':scope})['error']['code']==-32602
    bad=call('tools/call',{'name':'explore_repository','arguments':{**scope,'limit':'bad'}})['result']
    assert bad['isError'] and 'structuredContent' not in bad
    assert len(call('prompts/list')['result']['prompts'])==5
    assert call('prompts/get',{'name':'trace_feature','arguments':scope})['result']['messages']
    assert 'error' in call('prompts/get',{'name':'trace_feature','arguments':{}})


def test_stdio_framing_and_invalid_messages(project):
    store,repo,git,report,scope=project
    source=io.StringIO('invalid\n'+json.dumps({'jsonrpc':'2.0','id':1,'method':'ping'})+'\n');output=io.StringIO()
    serve(store,stdin=source,stdout=output)
    rows=[json.loads(line) for line in output.getvalue().splitlines()]
    assert rows[0]['error']['code']==-32700 and rows[1]['result']=={}


def test_actual_mcp_subprocess_discovery():
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'smoke','version':'1'}}},
              {'jsonrpc':'2.0','method':'notifications/initialized'},
              {'jsonrpc':'2.0','id':2,'method':'tools/list'},
              {'jsonrpc':'2.0','id':3,'method':'prompts/list'}]
    run=subprocess.run([sys.executable,'vigilant.py','--database','sqlite:///:memory:','mcp'],
        input=''.join(json.dumps(m)+'\n' for m in messages),capture_output=True,text=True,timeout=20,check=True)
    replies=[json.loads(line) for line in run.stdout.splitlines()]
    assert [r['id'] for r in replies]==[1,2,3]
    assert len(replies[1]['result']['tools'])==9 and len(replies[2]['result']['prompts'])==5


def test_api_cli_mcp_share_exact_results(project,tmp_path):
    from backend.app import create_app
    store,repo,git,report,scope=project
    with TestClient(create_app(store)) as client:
        assert len(client.get('/api/investigation/tools').json()['tools'])==9
        response=client.post('/api/investigation/call',json={'name':'explore_repository','arguments':scope})
        assert response.status_code==200,response.text
        api=response.json()
        assert client.post('/api/investigation/call',json={'name':'update_unknown','arguments':scope}).status_code==403
    args=tmp_path/'args.json';args.write_text(json.dumps(scope))
    result=subprocess.run([sys.executable,'vigilant.py','--database',str(store.engine.url),'call','explore_repository','--arguments',str(args)],capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)['result_id']==api['result_id']
    server=Server(store);initialize(server)
    result=server.handle({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'explore_repository','arguments':scope}})['result']
    assert result['structuredContent']['result_id']==api['result_id']


def test_api_tool_routes_require_existing_auth(project,monkeypatch):
    from backend.app import create_app
    monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','test-token')
    store,repo,git,report,scope=project
    with TestClient(create_app(store)) as client:
        assert client.get('/api/investigation/tools').status_code==401
        assert client.get('/api/investigation/tools',headers={'Authorization':'Bearer test-token'}).status_code==200

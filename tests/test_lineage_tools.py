"""Actual shared transport acceptance; authored fixtures are not accuracy labels."""
import copy
import json
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from database.store import Store
from ingestion.git import git
from ingestion.models import digest
from ingestion.service import import_repository
from investigation.service import InvestigationService, catalog, result_identity
from investigation.mcp import Server
from scripts.audit_artifact_lineage import fixture


@pytest.fixture
def indexed(tmp_path):
    f=fixture(tmp_path/'rename','rename');store=Store('sqlite:///'+str(tmp_path/'lineage.db'))
    for commit in (f['base'],f['head']):r=import_repository(store,f['path'],rev=commit)
    args={'repository':r['repository'],'commit_id':f['head'],'base_commit':f['base'],'paths':['a.py','moved/a.py']}
    yield store,f,args
    store.engine.dispose()


def mcp_call(server,method,params=None):
    return server.handle({'jsonrpc':'2.0','id':3,'method':method,'params':params or {}})


def initialized(store):
    server=Server(store)
    mcp_call(server,'initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'fixture','version':'1'}})
    server.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
    return server


def test_default_off_and_retained_gate(indexed,monkeypatch):
    store,f,args=indexed;s=InvestigationService(store)
    assert 'inspect_lineage' not in {t['name'] for t in catalog()}
    with pytest.raises(ValueError,match='not enabled'):s.call('inspect_lineage',args)
    assert not store.rows('tool_results')
    monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');r=s.call('inspect_lineage',args)
    monkeypatch.delenv('VIGILANT_LINEAGE_TOOLS')
    with pytest.raises(ValueError,match='not enabled'):
        s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':r['result_id']})


def test_paired_source_retention_and_no_graph_transfer(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');s=InvestigationService(store)
    before={table:store.rows(table) for table in ['artifacts','commits','graph_edges','graph_nodes','analysis_runs']}
    r=s.call('inspect_lineage',args);rec=r['data']['lineage_record']
    assert {e['commit'] for e in r['evidence']}=={f['base'],f['head']}
    assert rec['denominators']['candidate_pairs']==2
    assert all(x['lifecycle']=='UNREVIEWED' and not x['relationship_transfer_allowed'] for x in rec['observations'])
    assert r['unknowns'] and not r['data']['canonical_relationships_transferred']
    assert s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':r['result_id']})==r
    assert s.call('inspect_lineage',args)==r
    assert before=={table:store.rows(table) for table in before}


def test_actual_api_cli_mcp_and_resource_share_result(indexed,tmp_path,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');monkeypatch.setenv('VIGILANT_ACCESS_TOKEN','fixture-token')
    with TestClient(create_app(store)) as c:
        assert c.post('/api/investigation/call',json={'name':'inspect_lineage','arguments':args}).status_code==401
        headers={'Authorization':'Bearer fixture-token'}
        assert 'inspect_lineage' in {x['name'] for x in c.get('/api/investigation/tools',headers=headers).json()['tools']}
        response=c.post('/api/investigation/call',headers=headers,json={'name':'inspect_lineage','arguments':args})
        assert response.status_code==200,response.text
        api=response.json()
    path=tmp_path/'args.json';path.write_text(json.dumps(args))
    cli=subprocess.run([sys.executable,'vigilant.py','--database',str(store.engine.url),'call','inspect_lineage','--arguments',str(path)],capture_output=True,text=True,check=True)
    assert json.loads(cli.stdout)==api
    server=initialized(store)
    assert 'inspect_lineage' in {t['name'] for t in mcp_call(server,'tools/list')['result']['tools']}
    result=mcp_call(server,'tools/call',{'name':'inspect_lineage','arguments':args})['result']
    assert not result['isError'] and result['structuredContent']==api
    uri=f"vigilant://{args['repository']}/{args['commit_id']}/results/{api['result_id']}"
    assert json.loads(mcp_call(server,'resources/read',{'uri':uri})['result']['contents'][0]['text'])==api


def test_base_forgery_rejected_on_call_and_retained_read(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');s=InvestigationService(store);r=s.call('inspect_lineage',args)
    a=next(a for a in store.artifacts(args['repository'],f['base']) if not a.symbol)
    row=store.get('artifacts',digest(a.artifact_id,a.commit_id));row['content']='def value():\n    return 9\n';row['content_hash']=row['version']=digest(row['content']);store.put('artifacts',row['id'],row,replace=True)
    with pytest.raises(ValueError):s.call('inspect_lineage',args)
    with pytest.raises(ValueError):s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':r['result_id']})
    assert len(store.rows('tool_results'))==1


def test_rehashed_inner_tamper_and_policy_drift_reject(indexed,monkeypatch):
    from change_analysis import lineage
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');s=InvestigationService(store);r=s.call('inspect_lineage',args)
    bad=copy.deepcopy(r);bad['data']['lineage_record']['observations'][0]['logical_continuity']='CONFIRMED'
    bad['result_id']=result_identity(bad);store.put('tool_results',bad['result_id'],{**bad,**bad['scope']})
    with pytest.raises(ValueError,match='revalidation'):s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':bad['result_id']})
    monkeypatch.setattr(lineage,'MODULES',(*lineage.MODULES,'README.md'))
    with pytest.raises(ValueError,match='revalidation'):s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':r['result_id']})


def test_partial_staged_missing_and_wrong_project_scopes_reject(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');s=InvestigationService(store)
    key=digest(args['repository'],f['base']);row=store.get('commits',key);row['review_source_map']={'partial':True};store.put('commits',key,row,replace=True)
    with pytest.raises(ValueError,match='partial staged'):s.call('inspect_lineage',args)
    row.pop('review_source_map');store.put('commits',key,row,replace=True)
    with pytest.raises(ValueError):s.call('inspect_lineage',{**args,'base_commit':'f'*40})
    with pytest.raises(ValueError):s.call('inspect_lineage',{**args,'paths':['../a.py']})
    with pytest.raises(ValueError):s.call('inspect_lineage',{**args,'paths':['a.py']*17})
    repository=store.get('repositories',args['repository']);repository['project_id']='foreign';store.put('repositories',args['repository'],repository,replace=True)
    with pytest.raises(ValueError,match='project'):s.call('inspect_lineage',args)
    assert not store.rows('tool_results')


def test_same_revision_retention_and_worktree_isolation(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1');s=InvestigationService(store)
    args={**args,'base_commit':f['head'],'paths':['moved/a.py']};r=s.call('inspect_lineage',args)
    (f['path']/'moved/a.py').write_text('uncommitted changes')
    assert s.call('inspect_retained_result',{'repository':args['repository'],'commit_id':args['commit_id'],'result_id':r['result_id']})==r
    assert len(r['evidence'])==1


def test_full_source_secret_is_withheld_before_persistence(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1')
    p=f['path']/'moved/a.py';p.write_text(p.read_text()+'# safe padding\n'*20+'password="abcdefghijklmnopqrstuv"\n')
    git(f['path'],'add','.');git(f['path'],'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','authored sensitive fixture')
    r=import_repository(store,f['path']);args={**args,'commit_id':r['commit_id']}
    with pytest.raises(ValueError,match='Sensitive'):InvestigationService(store).call('inspect_lineage',args)
    assert not store.rows('tool_results') and not store.rows('unknown_revisions')


def test_forged_parent_identity_does_not_gain_canonical_citations(indexed,monkeypatch):
    store,f,args=indexed;monkeypatch.setenv('VIGILANT_LINEAGE_TOOLS','1')
    a=next(a for a in store.artifacts(args['repository'],f['base']) if not a.symbol)
    row=store.get('artifacts',digest(a.artifact_id,a.commit_id));row['artifact_id']='f'*64
    store.put('artifacts',row['id'],row,replace=True)
    with pytest.raises(ValueError,match='identity mismatch'):InvestigationService(store).call('inspect_lineage',args)
    assert not store.rows('tool_results')

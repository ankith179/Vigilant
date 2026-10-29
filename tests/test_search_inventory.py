"""Pinned file-enumeration checks; reviewer semantics are still attestations."""
import copy
import subprocess
import sys
import json
from pathlib import Path
import pytest
from database.store import Store
from ingestion.service import import_repository
from ingestion.git import inventory
from consistency.search_inventory import SearchInventory,validate_inventory

import stat

def _remove_loose_git_object(repo, oid):
    path = Path(repo) / '.git' / 'objects' / oid[:2] / oid[2:]
    path.chmod(path.stat().st_mode | stat.S_IWRITE)
    path.unlink()

def _git_blob_bytes(repo, oid):
    return subprocess.run(['git', '-C', str(repo), 'cat-file', 'blob', oid], check=True, capture_output=True).stdout


@pytest.fixture
def manifest_fixture(tmp_path):
    def git(*args):return subprocess.run(['git','-C',str(tmp_path),*args],check=True,capture_output=True,text=True).stdout.strip()
    git('init');git('config','user.email','review@example.invalid');git('config','user.name','Review')
    (tmp_path/'tests').mkdir();(tmp_path/'tests/test_value.py').write_text('def test_value():\n    assert 1==1\n')
    (tmp_path/'tests/README.md').write_text('Test setup notes\n')
    git('add','.');git('commit','-m','base')
    s=Store('sqlite:///:memory:');r=import_repository(s,tmp_path);artifacts=s.artifacts(r['repository'],r['commit_id'])
    files={a.file_path:a for a in artifacts if not a.symbol};by={a.artifact_id:a for a in artifacts}
    rows=inventory(tmp_path,r['commit_id'])
    data={'commit_id':r['commit_id'],'prefixes':['tests'],'entries':[{'file':row['file'],'object_id':row['object_id'],
          'disposition':'SEARCHED','rationale':'Authored fixture inspection','artifact_ids':[files[row['file']].artifact_id]} for row in rows]}
    return tmp_path,data,by,[a.artifact_id for a in files.values()],s


def test_exact_pinned_boundary_and_unknowns(manifest_fixture):
    repo,data,by,ids,_=manifest_fixture
    lookup=lambda aid,commit:by[aid]
    result=validate_inventory(repo,SearchInventory.model_validate(data),lookup,ids,True)
    assert result['files']==2 and not result['whole_repository_coverage']
    unknown=copy.deepcopy(data);unknown['entries'][0].update(disposition='UNKNOWN',artifact_ids=[])
    with pytest.raises(ValueError,match='Unknown'):validate_inventory(repo,SearchInventory.model_validate(unknown),lookup,ids,True)
    remaining=[aid for e in unknown['entries'] for aid in e['artifact_ids']]
    partial=validate_inventory(repo,SearchInventory.model_validate(unknown),lookup,remaining,False)
    assert partial['status']=='MACHINE_ENUMERATED_PARTIAL_BOUNDARY'


@pytest.mark.parametrize('mode',['missing','hash','file','duplicate','outside','searched_identity'])
def test_invalid_search_inventory_rejected(manifest_fixture,mode):
    repo,data,by,ids,_=manifest_fixture;lookup=lambda aid,commit:by[aid]
    if mode=='missing':data['entries'].pop()
    elif mode=='hash':data['entries'][0]['object_id']='f'*40
    elif mode=='file':data['entries'][0]['artifact_ids']=data['entries'][1]['artifact_ids']
    elif mode=='duplicate':data['entries'].append(copy.deepcopy(data['entries'][0]))
    elif mode=='outside':data['prefixes']=['../outside']
    elif mode=='searched_identity':ids=[]
    with pytest.raises(ValueError):validate_inventory(repo,SearchInventory.model_validate(data),lookup,ids,True)


@pytest.mark.parametrize('field',['artifact_id','commit_id'])
def test_inventory_rejects_rebound_artifact_identity(manifest_fixture,field):
    repo,data,by,ids,_=manifest_fixture
    # The text is still genuine; only the identity/revision is rebound.
    a=by[ids[0]]
    setattr(a,field,'f'*40)
    with pytest.raises(ValueError,match='identity/revision'):
        validate_inventory(repo,SearchInventory.model_validate(data),lambda aid,commit:by[aid],ids,True)


def test_historical_inventory_is_checked_even_when_latest_has_none(manifest_fixture):
    from consistency.obligations import assess_registry,ObligationRegistry,revision_fingerprint
    from tests.test_obligations import registry_fixture
    repo,data,by,ids,store=manifest_fixture
    _,registry=registry_fixture();a=by[ids[0]]
    ref={k:getattr(a,k) for k in ('artifact_id','commit_id','content_hash','start_line','end_line')}
    ref['file']=a.file_path
    registry.update(repository=a.repository,parser_identity=a.project_id)
    r=registry['histories'][0][0];r['commit_id']=a.commit_id
    r['obligation'].update(source=ref,evidence=[ref],applicable_artifact_ids=[a.artifact_id])
    r['search_scope'].update(evidence=[ref],applicable_artifact_ids=[a.artifact_id],searched_artifact_ids=ids,git_inventory=data)
    second=copy.deepcopy(r);second['sequence']=2
    second['search_scope'].pop('git_inventory');second['obligation']['lifecycle']='RETIRED'
    second['previous_fingerprint']=revision_fingerprint(ObligationRegistry.model_validate(registry).histories[0][0])
    registry['histories'][0].append(second)
    assert not assess_registry(store,registry,a.commit_id)['findings']
    # Rehashing the lifecycle chain cannot legitimize a forged old Git object.
    r['search_scope']['git_inventory']['entries'][0]['object_id']='f'*40
    registry['histories'][0].pop()
    second['previous_fingerprint']=revision_fingerprint(ObligationRegistry.model_validate(registry).histories[0][0])
    registry['histories'][0].append(second)
    with pytest.raises(ValueError,match='Git object mismatch'):
        assess_registry(store,registry,a.commit_id)


def test_draft_cli_keeps_unknowns_and_refuses_review_overwrite_or_empty_boundary(manifest_fixture,tmp_path):
    repo,data,by,ids,_=manifest_fixture
    script=Path(__file__).resolve().parents[1]/'scripts/build_search_inventory.py'
    output=tmp_path/'draft.json'
    command=[sys.executable,str(script),str(repo),'--commit',data['commit_id'],'--prefix','tests','--output',str(output)]
    subprocess.run(command,check=True,capture_output=True,text=True)
    result=json.loads(output.read_text())
    assert len(result['entries'])==2
    assert all(e['disposition']=='UNKNOWN' and not e['artifact_ids'] for e in result['entries'])
    assert validate_inventory(repo,SearchInventory.model_validate(result),lambda aid,commit:None,[],False)['dispositions']=={'UNKNOWN':2}
    with pytest.raises(ValueError,match='Unknown'):
        validate_inventory(repo,SearchInventory.model_validate(result),lambda aid,commit:None,[],True)
    output.write_text('Reviewer work must survive\n')
    assert subprocess.run(command,capture_output=True).returncode!=0
    assert output.read_text()=='Reviewer work must survive\n'
    empty=tmp_path/'empty.json';command[-1]=str(empty);command[command.index('--prefix')+1]='absent'
    assert subprocess.run(command,capture_output=True).returncode!=0
    assert not empty.exists()
    # A tree-only UNKNOWN draft must not need blob contents or blob sizes.
    oid=data['entries'][0]['object_id']
    _remove_loose_git_object(repo, oid)
    command[command.index('--prefix')+1]='tests';command[-1]=str(tmp_path/'tree-only.json')
    subprocess.run(command,check=True,capture_output=True,text=True)
    assert len(json.loads((tmp_path/'tree-only.json').read_text())['entries'])==2


def test_offline_artifact_map_preserves_missing_sources_budgets_and_identity(manifest_fixture):
    from scripts.prepare_pilot_artifact_maps import map_snapshot
    from ingestion.models import digest
    repo,data,by,ids,_=manifest_fixture
    for e in data['entries']:e.update(disposition='UNKNOWN',artifact_ids=[])
    origin='https://example.invalid/review-fixture.git'
    result=map_snapshot(repo,data,origin)
    assert result['repository']==digest(result['parser_identity'],origin)
    assert result['repository']!=by[ids[0]].repository
    assert all(a['project_id']==result['parser_identity'] for a in result['artifacts'])
    assert all(r['status']=='PARSED' and r['search_disposition']=='UNKNOWN' for r in result['files'])
    assert result['independent_labels_created']==0 and 'findings' not in result
    limited=map_snapshot(repo,data,origin,max_total_bytes=1)
    assert not limited['artifacts'] and all(r['status']=='SNAPSHOT_BYTE_BUDGET' for r in limited['files'])
    small=map_snapshot(repo,data,origin,max_blob_bytes=1)
    assert not small['artifacts'] and all(r['status']=='SIZE_LIMIT' for r in small['files'])
    oid=data['entries'][0]['object_id'];_remove_loose_git_object(repo, oid)
    missing=map_snapshot(repo,data,origin)
    assert len(missing['files'])==2
    assert sum(r['status']=='MISSING_LOCAL_BLOB' for r in missing['files'])==1
    assert sum(r['status']=='PARSED' for r in missing['files'])==1


def test_offline_artifact_map_rejects_tampering_or_reviewed_input(manifest_fixture):
    from scripts.prepare_pilot_artifact_maps import map_snapshot
    repo,data,by,ids,_=manifest_fixture
    with pytest.raises(ValueError,match='UNKNOWN-only'):map_snapshot(repo,data,'fixture')
    for e in data['entries']:e.update(disposition='UNKNOWN',artifact_ids=[])
    data['entries'][0]['object_id']='f'*40
    with pytest.raises(ValueError,match='pinned Git tree'):map_snapshot(repo,data,'fixture')

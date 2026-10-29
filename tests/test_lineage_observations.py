import copy
import subprocess
import sys
import pytest
from ingestion.git import git, revision, snapshot
from ingestion.parsers import extract
from scripts.audit_artifact_lineage import fixture, CASES
from change_analysis import lineage


def scope(f):return dict(project='authored',repository='authored-upstream',base=f['base'],head=f['head'])


@pytest.mark.parametrize('name',CASES[:-1])
def test_source_observations_retain_known_ambiguities(tmp_path,name):
    f=fixture(tmp_path/name,name);args=scope(f)
    result=lineage.observe(f['path'],**args)
    assert lineage.verify(f['path'],result,**args)==result
    rows=result['observations'];d=result['denominators']
    base=[r['base']['observer_artifact_id'] for r in rows if r['base']]
    head=[r['head']['observer_artifact_id'] for r in rows if r['head']]
    assert len(base)==len(set(base))==d['base_artifacts']
    assert len(head)==len(set(head))==d['head_artifacts']
    assert all(r['logical_continuity']=='UNKNOWN' and r['lifecycle']=='UNREVIEWED' and
               not r['relationship_transfer_allowed'] for r in rows)
    canonical=[a for path,text in snapshot(f['path'],f['base'])
               for a in extract(args['project'],args['repository'],f['base'],path,text)]
    assert set(base).isdisjoint({a.artifact_id for a in canonical})
    functions=[r for r in rows if (r['base'] or r['head'])['artifact_type']=='function']
    paired=[r for r in functions if r['base'] and r['head']]
    if name in {'rename','modified_rename'}:
        assert len(paired)==1 and paired[0]['status']=='GIT_RENAME_CANDIDATE'
        assert paired[0]['base']['observer_artifact_id']!=paired[0]['head']['observer_artifact_id']
    elif name=='copy':
        assert len(paired)==1 and len(functions)==2
        assert any(r['head'] and r['head']['path']=='copy.py' and r['status']=='UNKNOWN' for r in functions)
    elif name=='cross_file_symbol_move':
        assert not [r for r in paired if r['base']['symbol']=='value']
    elif name=='duplicate_ordinal_shift':
        assert not paired
        assert all(r['reason']=='DUPLICATE_SYMBOL_GROUP' for r in functions)
    elif name=='divergent_branches':
        assert not paired and result['history']['relation']=='DIVERGED'
        assert all(r['reason']=='NONLINEAR_REVISION_SCOPE' for r in rows)
    elif name=='delete_recreate':
        assert not paired and result['history']['file_deletions']
        assert all(r['reason']=='FILE_DELETION_HISTORY' for r in rows)
    elif name=='renamed_symbol':assert not paired


def test_tampering_scope_and_selected_paths_fail_closed(tmp_path):
    f=fixture(tmp_path/'copy','copy');args=scope(f);r=lineage.observe(f['path'],**args)
    forged=copy.deepcopy(r);forged['observations'][0]['base']['content_hash']='0'*64
    with pytest.raises(ValueError):lineage.verify(f['path'],forged,**args)
    with pytest.raises(ValueError):lineage.verify(f['path'],r,**{**args,'repository':'foreign'})
    subset=lineage.observe(f['path'],**args,paths=['a.py'])
    with pytest.raises(ValueError):lineage.verify(f['path'],subset,**args)
    assert lineage.verify(f['path'],subset,**args,paths=['a.py'])==subset


def test_missing_or_mutable_revision_and_bad_paths_reject(tmp_path):
    f=fixture(tmp_path/'missing','missing_revision');args=scope(f)
    with pytest.raises(subprocess.CalledProcessError):lineage.observe(f['path'],**args)
    args['head']=args['base']
    with pytest.raises(ValueError):lineage.observe(f['path'],**{**args,'head':'HEAD'})
    for paths in [[],['../a.py'],['a\\b.py'],['./a.py'],['missing.py'],['/a.py']]:
        with pytest.raises(ValueError):lineage.observe(f['path'],**args,paths=paths)


def test_history_limit_parse_errors_and_partial_selection_remain_unknown(tmp_path,monkeypatch):
    f=fixture(tmp_path/'history','delete_recreate');args=scope(f)
    monkeypatch.setattr(lineage,'HISTORY_LIMIT',1)
    r=lineage.observe(f['path'],**args)
    assert r['history']['status']=='INCOMPLETE_COMMIT_LIMIT'
    assert all(x['status']=='UNKNOWN' for x in r['observations'])
    monkeypatch.undo()
    (f['path']/'a.py').write_text('def :\n')
    git(f['path'],'add','a.py');git(f['path'],'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','parse error')
    r=lineage.observe(f['path'],**{**args,'head':revision(f['path'])})
    assert any(x['reason']=='PARSE_ERROR_UNKNOWN' for x in r['observations'])


def test_duplicate_content_rename_is_not_arbitrarily_linked(tmp_path):
    f=fixture(tmp_path/'duplicate','copy');p=f['path'];base=f['head']
    (p/'moved').mkdir();git(p,'mv','a.py','moved/a.py');git(p,'mv','copy.py','moved/copy.py')
    git(p,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','duplicate renames')
    r=lineage.observe(p,**{**scope(f),'base':base,'head':revision(p)})
    assert not r['denominators']['candidate_pairs']
    assert any(x['reason']=='DUPLICATED_CONTENT_RENAME' for x in r['observations'])


def test_cli_is_opt_in_and_preserves_existing_output(tmp_path):
    f=fixture(tmp_path/'rename','rename');out=tmp_path/'lineage.json'
    cmd=[sys.executable,'scripts/observe_artifact_lineage.py','--repository-path',str(f['path']),
         '--project','authored','--repository-id','authored-upstream','--base',f['base'],
         '--head',f['head'],'--output',str(out)]
    result=subprocess.run(cmd,capture_output=True,text=True);assert result.returncode==0,result.stderr
    original=out.read_bytes()
    assert subprocess.run(cmd,capture_output=True).returncode!=0
    assert out.read_bytes()==original


def test_binary_side_and_absent_path_remain_in_file_denominator(tmp_path):
    f=fixture(tmp_path/'copy','copy');p=f['path']
    (p/'copy.py').write_bytes(b'\0binary')
    git(p,'add','copy.py');git(p,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','binary')
    r=lineage.observe(p,**{**scope(f),'head':revision(p)},paths=['copy.py'])
    assert r['denominators']['selected_files']==1
    assert r['denominators']['unavailable_file_sides']==2
    assert r['sources']['base']['selected_sources']['copy.py']['status']=='ABSENT_AT_THIS_REVISION'
    assert r['sources']['head']['selected_sources']['copy.py']['status']=='UNAVAILABLE_BINARY'
    assert not r['observations']


def test_pinned_sources_ignore_worktree_and_detect_policy_drift(tmp_path,monkeypatch):
    f=fixture(tmp_path/'rename','rename');args=scope(f);p=f['path']
    r=lineage.observe(p,**args)
    (p/'moved/a.py').write_text('uncommitted unrelated replacement')
    assert lineage.verify(p,r,**args)==r
    monkeypatch.setattr(lineage,'MODULES',(*lineage.MODULES,'README.md'))
    with pytest.raises(ValueError):lineage.verify(p,r,**args)

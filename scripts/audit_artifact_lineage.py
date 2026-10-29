"""Authored Git-fixture audit, not a logical-identity migration or research gold.

Only disposable fixture repositories are written. Existing artifact IDs, parser,
production delta behavior and saved project evidence are never modified.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.git import git, inventory, revision, snapshot
from ingestion.models import digest
from ingestion.parsers import extract, PARSER_POLICY
from change_analysis.diff import detect

POLICY = 'authored-artifact-lineage-audit-v1'
CASES = ('rename', 'modified_rename', 'copy', 'cross_file_symbol_move',
         'duplicate_ordinal_shift', 'divergent_branches', 'delete_recreate',
         'renamed_symbol', 'missing_revision')
BODY = 'def value():\n    return 1\n'
PADDING = ''.join(f'# stable context {i}\n' for i in range(30))


def fixture(path, name):
    path.mkdir()
    def g(*args):
        # Fixed fixture timestamps and no hooks/signing; these are not project commits.
        env = {**os.environ, 'GIT_AUTHOR_DATE': '2026-01-01T00:00:00+00:00',
               'GIT_COMMITTER_DATE': '2026-01-01T00:00:00+00:00',
               'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
        return subprocess.run(['git', '-c', 'core.hooksPath='+os.devnull,
                               '-c', 'commit.gpgsign=false', '-C', str(path), *args],
                              env=env, check=True, capture_output=True, text=True,
                              timeout=30).stdout.strip()
    def write(file, text):
        target=path/file; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    def commit(message):
        g('add', '-A'); g('commit', '-m', message); return revision(path)
    g('init', '-b', 'main'); g('config', 'user.name', 'Authored fixture')
    g('config', 'user.email', 'fixture@example.invalid')
    initial = BODY+PADDING if name in {'modified_rename','renamed_symbol'} else BODY
    if name=='duplicate_ordinal_shift': initial=BODY+'\ndef value():\n    return 2\n'
    write('a.py', initial)
    if name=='cross_file_symbol_move':write('b.py', 'def other():\n    return 0\n')
    common=commit('authored base'); base=common; intermediate=[]
    if name in {'rename','modified_rename','renamed_symbol'}:
        (path/'moved').mkdir();g('mv','a.py','moved/a.py')
        if name=='modified_rename':write('moved/a.py',initial.replace('return 1','return 2'))
        if name=='renamed_symbol':write('moved/a.py',initial.replace('value()', 'renamed()'))
    elif name=='copy':write('copy.py',initial)
    elif name=='cross_file_symbol_move':
        write('a.py','# function moved elsewhere\n')
        write('b.py','def other():\n    return 0\n\n'+BODY)
    elif name=='duplicate_ordinal_shift':write('a.py','def value():\n    return 2\n')
    elif name=='divergent_branches':
        g('checkout','-b','left');write('a.py',BODY.replace('1','2'));base=commit('left')
        g('checkout','-b','right',common);write('a.py',BODY.replace('1','3'))
    elif name=='delete_recreate':
        g('rm','a.py');intermediate.append(commit('deleted'));write('a.py',initial)
    elif name=='missing_revision':return {'path':path,'base':base,'head':'f'*40,'common':common,'intermediate':[]}
    head=commit('authored '+name)
    return {'path':path,'base':base,'head':head,'common':common,'intermediate':intermediate}


def extracted(repo, commit, rid):
    texts=dict(snapshot(repo,commit));items=[]
    for path,text in texts.items():items.extend(extract('lineage-audit',rid,commit,path,text,source_files=texts))
    return items


def audit_case(parent, name):
    if name not in CASES:raise ValueError('Unsupported fixture')
    f=fixture(parent/name,name);repo=f.pop('path');rid=digest(POLICY,name)
    row={'case':name,'scope':'AUTHORED_DEVELOPMENT_FIXTURE_ONLY', 'repository':rid,
         'base_commit':f['base'],'head_commit':f['head'],'common_commit':f['common'],
         'intermediate_commits':f['intermediate'], 'logical_continuity':'UNKNOWN',
         'semantic_correctness':'NOT_ESTABLISHED','production_behavior_changed':False}
    if name=='missing_revision':
        try:revision(repo,f['head'])
        except subprocess.CalledProcessError as exc:
            row.update(outcome='REJECTED_MISSING_REVISION',git_exit_code=exc.returncode,
                       assertion='Unresolvable revision fails before comparison',verified=True)
            row['observation_id']=digest(POLICY,row)
            return row
        raise AssertionError('Missing revision was accepted')
    before=extracted(repo,f['base'],rid);after=extracted(repo,f['head'],rid)
    delta=detect(repo,f['base'],f['head'],before,after)
    funcs=lambda items:[a for a in items if a.artifact_type=='function']
    old,new=funcs(before),funcs(after)
    function_changes=[c for c in delta['artifacts'] if c['artifact_type']=='function']
    kinds=sorted(c['kind'] for c in function_changes)
    same_ids=bool({a.artifact_id for a in old}&{a.artifact_id for a in new})
    expectations={
        'rename':(['renamed'],'GIT_RENAME_CANDIDATE','Git rename pairs exact symbol/type, with a new path-bound ID'),
        'modified_rename':(['renamed'],'GIT_RENAME_CANDIDATE','Rename pairing is not a claim of unchanged content'),
        'copy':(['added'],'COPY_NOT_LINKED','Surviving source and copy keep distinct path-bound IDs'),
        'cross_file_symbol_move':(['added','deleted'],'UNRESOLVED_SYMBOL_MOVE','Move across retained files is represented as endpoint add/delete'),
        'duplicate_ordinal_shift':(['deleted','modified'],'AMBIGUOUS_ORDINAL_REUSE','Ordinal shift reuses first identity and loses second pairing'),
        'divergent_branches':(['modified'],'DIVERGENT_ENDPOINT_COMPARISON','Same path/symbol ID does not establish linear ancestry'),
        'delete_recreate':([],'ENDPOINT_IDENTICAL_HISTORY_GAP','Endpoint equality hides intervening deletion/recreation'),
        'renamed_symbol':(['added','deleted'],'UNRESOLVED_SYMBOL_RENAME','File rename alone does not pair a renamed symbol')}
    expected,outcome,assertion=expectations[name]
    assert kinds==expected,(name,kinds,expected)
    if name in {'rename','modified_rename'}:
        assert not same_ids and any(x['status'].startswith('R') for x in delta['files'])
        assert all(x['new_artifact_id'] and x['new_artifact_id']!=x['artifact_id'] for x in function_changes)
    if name=='modified_rename':assert old[0].content_hash!=new[0].content_hash
    if name=='copy':assert len(new)==2 and new[0].content_hash==new[1].content_hash
    if name=='duplicate_ordinal_shift':
        assert old[0].artifact_id==new[0].artifact_id and old[1].content_hash==new[0].content_hash
        assert old[1].metadata.get('identity_ambiguity') and not old[0].metadata.get('identity_ambiguity')
    merge_base=git(repo,'merge-base',f['base'],f['head'])
    if name=='divergent_branches':assert merge_base not in {f['base'],f['head']} and same_ids
    if name=='delete_recreate':assert not delta['artifacts'] and same_ids and f['intermediate']
    refs={}
    for role,commit,items in [('base',f['base'],before),('head',f['head'],after)]:
        refs[role]={'commit':commit,'tree':git(repo,'rev-parse',commit+'^{tree}'),
                    'inventory':inventory(repo,commit),
                    'artifacts':[a.model_dump(exclude={'created_at','updated_at'}) for a in items]}
    row.update(outcome=outcome,assertion=assertion,verified=True,
               merge_base=merge_base,scope_source=refs,delta=delta,
               intermediate_source=[{'commit':c,'tree':git(repo,'rev-parse',c+'^{tree}'),
                                     'inventory':inventory(repo,c)} for c in f['intermediate']],
               function_change_kinds=kinds,shared_function_ids=same_ids)
    row['observation_id']=digest(POLICY,row)
    return row


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vigilant-lineage-fixtures-') as tmp:
        rows=[audit_case(Path(tmp),name) for name in CASES]
    modules=['ingestion/models.py','ingestion/parsers.py','ingestion/git.py',
             'change_analysis/diff.py','scripts/audit_artifact_lineage.py']
    result={'policy':POLICY,'status':'AUTHORED_BEHAVIOR_AUDIT_VERIFIED',
            'parser_policy':PARSER_POLICY,'git_version':subprocess.run(['git','--version'],check=True,capture_output=True,text=True).stdout.strip(),
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in modules},
            'case_denominator':len(CASES),'cases_verified':sum(r['verified'] for r in rows),
            'model_calls':0,'independent_labels_created':0,'canonical_writes':0,
            'fixture_provenance':'Locally authored synthetic source; no external project or benchmark labels',
            'production_lineage_implemented':False,'quality_target_91':'NOT_EVALUATED',
            'limitations':['Authored Python fixtures, not independent accuracy evidence',
                           'Git similarity is heuristic and configuration/version dependent',
                           'No global identity, semantic equivalence or complete project history is established',
                           'Partial staged maps and historical frozen IDs are unchanged'],
            'cases':rows}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'reports/lineage-audit-20261025/observations')
    result=run(p.parse_args().output)
    print(json.dumps({k:v for k,v in result.items() if k!='cases'}))

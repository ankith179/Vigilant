"""Exact local recovery fixtures; no independent labels or network requests."""
import hashlib
import json
from pathlib import Path
import subprocess
import pytest
from database.store import Store
from ingestion.models import artifact,digest
from scripts.recover_local_pilot_blobs import recover


def oid(raw):
    return subprocess.run(['git','hash-object','--stdin'],input=raw,check=True,capture_output=True).stdout.decode().strip()


def queue_file(path,items):
    entries=[dict(case_id=str(i),side='base',repository='fixture',original_alias='demo',origin='fixture',
        commit_id='f'*40,file=file,object_id=oid(raw)) for i,(file,raw) in enumerate(items)]
    objects={e['object_id']:[{k:v for k,v in e.items() if k!='object_id'}] for e in entries}
    path.write_text(json.dumps({'missing_file_side_entries':entries,'objects':objects,
        'unique_missing_blob_ids':len(objects),'absent_pinned_tree_paths':[{'file':'not-in-tree.py'}]}))
    return entries


def test_exact_worktree_and_stored_bytes_preserve_mismatches_and_denominator(tmp_path):
    root=tmp_path/'repos';(root/'demo/src').mkdir(parents=True)
    (root/'demo/src/value.py').write_bytes(b'first\n')
    queue=tmp_path/'queue.json';entries=queue_file(queue,[('src/value.py',b'first\n'),('src/value.py',b'old\n'),
        ('docs/contract.txt',b'contract\n'),('docs/contract.txt',b'contract\r\n')])
    snapshot=tmp_path/'source.db';store=Store('sqlite:///'+str(snapshot))
    a=artifact('fixture','r','f'*40,'docs/contract.txt','documentation','', 'contract\n')
    store.put('artifacts',digest(a.artifact_id,a.commit_id),a.model_dump());store.engine.dispose()
    before=snapshot.read_bytes();output=tmp_path/'recovery';result=recover(queue,root,[snapshot],output)
    assert result['unique_objects']==4 and result['original_missing_entries']==4
    assert result['recovered_objects']==2 and result['unresolved_entry_occurrences']==2
    assert (output/'objects'/entries[0]['object_id']).read_bytes()==b'first\n'
    assert (output/'objects'/entries[2]['object_id']).read_bytes()==b'contract\n'
    assert result['objects'][entries[3]['object_id']]['status']=='UNRESOLVED'
    assert any(a['status']=='BYTE_MISMATCH' for a in result['objects'][entries[1]['object_id']]['attempts'])
    assert snapshot.read_bytes()==before and result['absent_pinned_tree_paths']==[{'file':'not-in-tree.py'}]
    assert result['new_fetches']==0 and result['independent_labels_created']==0
    saved={p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
    with pytest.raises(FileExistsError):recover(queue,root,[snapshot],output)
    assert all(p.read_bytes()==b for p,b in saved.items())


def test_recovery_rejects_traversal_and_does_not_follow_source_symlinks(tmp_path,monkeypatch):
    root=tmp_path/'repos';(root/'demo').mkdir(parents=True);queue=tmp_path/'queue.json'
    queue_file(queue,[('../private.py',b'secret')])
    with pytest.raises(ValueError,match='Unsafe'):recover(queue,root,[],tmp_path/'rejected')
    assert not (tmp_path/'rejected').exists()
    outside=tmp_path/'private.py';outside.write_bytes(b'secret')
    from tests.symlink_test_support import make_symlink_or_mark
    make_symlink_or_mark(root/'demo/source.py',outside,monkeypatch)
    queue_file(queue,[('source.py',b'secret')]);result=recover(queue,root,[],tmp_path/'symlink')
    assert result['recovered_objects']==0
    assert any(a['status']=='UNSAFE_SYMLINK' for r in result['objects'].values() for a in r['attempts'])


def test_size_limit_keeps_missing_objects_in_denominator(tmp_path):
    root=tmp_path/'repos';(root/'demo').mkdir(parents=True)
    (root/'demo/large.py').write_bytes(b'large')
    queue=tmp_path/'queue.json';queue_file(queue,[('large.py',b'large')])
    result=recover(queue,root,[],tmp_path/'bounded',max_bytes=1)
    assert result['unique_objects']==1 and result['recovered_objects']==0 and result['unresolved_objects']==1
    assert any(a['status']=='SIZE_LIMIT' for r in result['objects'].values() for a in r['attempts'])


def test_upstream_bytes_require_exact_hash_and_expected_source(tmp_path):
    from scripts.verify_upstream_pilot_blobs import verify
    queue=tmp_path/'queue.json';entries=queue_file(queue,[('source.py',b'correct\n'),('other.py',b'other\n')])
    q=json.loads(queue.read_text())
    for values in q['objects'].values():
        for v in values:v['origin']='https://github.com/example/project.git'
    for e in q['missing_file_side_entries']:e['origin']='https://github.com/example/project.git'
    queue.write_text(json.dumps(q));responses=tmp_path/'responses';responses.mkdir()
    for i,e in enumerate(entries):
        oid=e['object_id'];v={'object_id':oid,'origin':'https://github.com/example/project.git',
            'url':'https://api.github.com/repos/example/project/git/blobs/'+oid,'status':'RETURNED',
            'text':'correct\n' if i==0 else 'changed\n'}
        (responses/(oid+'.json')).write_text(json.dumps(v))
    output=tmp_path/'verified';r=verify(queue,responses,output)
    assert r['verified_objects']==1 and r['unresolved_entry_occurrences']==1
    assert (output/'objects'/entries[0]['object_id']).read_bytes()==b'correct\n'
    assert not (output/'objects'/entries[1]['object_id']).exists()
    with pytest.raises(FileExistsError):verify(queue,responses,output)
    p=responses/(entries[0]['object_id']+'.json');v=json.loads(p.read_text());v['url']='https://example.invalid/foreign';p.write_text(json.dumps(v))
    assert verify(queue,responses,tmp_path/'foreign')['verified_objects']==0

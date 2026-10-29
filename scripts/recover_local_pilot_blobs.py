"""Recover exact queued Git blobs from local candidates into a separate cache."""
import argparse
from collections import defaultdict
from contextlib import closing
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_pilot_artifact_maps import local_git


def blob_id(raw,expected):
    algorithm=hashlib.sha1 if len(expected)==40 else hashlib.sha256
    return algorithm(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def recover(queue_path,repo_root,snapshots,output,max_bytes=2_000_000):
    queue_path,repo_root,output=map(Path,(queue_path,repo_root,output))
    if output.exists():raise FileExistsError('Refusing to overwrite recovery work')
    queue=json.loads(queue_path.read_text());entries=queue['missing_file_side_entries'];objects=queue['objects']
    if len(objects)!=queue['unique_missing_blob_ids'] or set(objects)!={e['object_id'] for e in entries}:
        raise ValueError('Recovery queue denominator mismatch')
    by_path=defaultdict(set);by_alias=defaultdict(set)
    for e in entries:
        path=e['file'];p=PurePosixPath(path)
        if (not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',e['object_id']) or
            not re.fullmatch(r'[A-Za-z0-9_-]+',e['original_alias']) or p.is_absolute() or
            '..' in p.parts or '\\' in path or str(p)!=path):raise ValueError('Unsafe recovery identity/path')
        by_path[path].add(e['object_id']);by_alias[e['original_alias']].add(e['object_id'])
    output.mkdir(parents=True,exist_ok=False);(output/'objects').mkdir()
    results={oid:{'status':'UNRESOLVED','attempts':[],'occurrences':objects[oid]} for oid in objects};scan_errors=[]
    def candidate(oid,raw,source,encoding='RAW_BYTES'):
        actual=blob_id(raw,oid);match=actual==oid
        results[oid]['attempts'].append({'source':source,'encoding':encoding,'bytes':len(raw),
            'actual_object_id':actual,'status':'MATCH' if match else 'BYTE_MISMATCH'})
        if match and results[oid]['status']!='RECOVERED_EXACT_BYTES':
            with (output/'objects'/oid).open('xb') as stream:stream.write(raw)
            results[oid].update(status='RECOVERED_EXACT_BYTES',cache='objects/'+oid,
                sha256=hashlib.sha256(raw).hexdigest())
    # All Git operations are local-only; the existing helper disables lazy fetch/transports.
    for alias,oids in sorted(by_alias.items()):
        repo=repo_root/alias;ordered=sorted(oids)
        try:
            rows=local_git(repo,'cat-file','--batch-check',data=('\n'.join(ordered)+'\n').encode()).splitlines()
            for oid,line in zip(ordered,rows,strict=True):
                fields=line.decode().split();source='git-cache:'+alias
                if fields[-1]=='missing':results[oid]['attempts'].append({'source':source,'status':'MISSING'});continue
                if fields[1]!='blob' or int(fields[2])>max_bytes:
                    results[oid]['attempts'].append({'source':source,'status':'TYPE_OR_SIZE_LIMIT'});continue
                candidate(oid,local_git(repo,'cat-file','blob',oid),source)
        except Exception as exc:scan_errors.append({'source':'git-cache:'+alias,'error':type(exc).__name__})
    seen=set()
    for e in entries:
        key=e['original_alias'],e['file']
        if key in seen:continue
        seen.add(key);base=(repo_root/e['original_alias']).resolve();path=base/e['file']
        source='worktree:'+e['original_alias']+'/'+e['file']
        targets={v['object_id'] for v in entries if (v['original_alias'],v['file'])==key}
        if not path.resolve().is_relative_to(base) or any(p.is_symlink() for p in [path,*path.parents] if p!=base):
            for oid in targets:results[oid]['attempts'].append({'source':source,'status':'UNSAFE_SYMLINK'})
            continue
        try:
            with path.open('rb') as stream:raw=stream.read(max_bytes+1)
            for oid in targets:
                if len(raw)>max_bytes:results[oid]['attempts'].append({'source':source,'status':'SIZE_LIMIT'})
                else:candidate(oid,raw,source)
        except OSError as exc:
            for oid in targets:results[oid]['attempts'].append({'source':source,'status':'UNAVAILABLE','error':type(exc).__name__})
    # Stored text is only a candidate reconstruction. No encoding/line-ending guess is accepted without the exact blob hash.
    for snapshot in sorted(map(Path,snapshots)):
        try:
            with closing(sqlite3.connect(snapshot.resolve().as_uri()+'?mode=ro',uri=True)) as db:
                placeholders=','.join('?' for _ in by_path)
                query="SELECT payload FROM artifacts WHERE json_extract(payload,'$.symbol')='' AND json_extract(payload,'$.file_path') IN ("+placeholders+")"
                for (payload,) in db.execute(query,list(by_path)):
                    a=json.loads(payload);raw=a['content'].encode('utf-8')
                    source='stored-text:'+snapshot.name+'/'+a['artifact_id']+'@'+a['commit_id']
                    for oid in by_path[a['file_path']]:
                        if len(raw)>max_bytes:results[oid]['attempts'].append({'source':source,'status':'SIZE_LIMIT'})
                        else:candidate(oid,raw,source,'STORED_TEXT_UTF8_REENCODED')
        except Exception as exc:scan_errors.append({'source':'stored-text:'+snapshot.name,'error':type(exc).__name__})
    recovered={oid for oid,r in results.items() if r['status']=='RECOVERED_EXACT_BYTES'}
    result={'policy':'exact-local-pilot-blob-recovery-v1','queue_sha256':hashlib.sha256(queue_path.read_bytes()).hexdigest(),
        'objects':results,'unique_objects':len(objects),'recovered_objects':len(recovered),'unresolved_objects':len(objects)-len(recovered),
        'original_missing_entries':len(entries),'recovered_entry_occurrences':sum(e['object_id'] in recovered for e in entries),
        'unresolved_entry_occurrences':sum(e['object_id'] not in recovered for e in entries),
        'absent_pinned_tree_paths':queue['absent_pinned_tree_paths'],'scan_errors':scan_errors,
        'new_fetches':0,'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED',
        'scope':'Separate exact-byte cache only; frozen maps, packets, inventories and source databases are unchanged'}
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--queue',type=Path,default=ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json')
    p.add_argument('--repo-root',type=Path,default=ROOT/'data/repos');p.add_argument('--snapshot',type=Path,action='append')
    a=p.parse_args();r=recover(a.queue,a.repo_root,a.snapshot or list((ROOT/'data/snapshots').glob('*.db')),a.output)
    print(json.dumps({k:v for k,v in r.items() if k not in {'objects','absent_pinned_tree_paths'}}))

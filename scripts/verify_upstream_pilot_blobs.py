"""Validate saved read-only GitHub responses; never fetch or execute subject code."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.recover_local_pilot_blobs import blob_id


def verify(queue_path,responses,output):
    queue_path,responses,output=map(Path,(queue_path,responses,output))
    if output.exists():raise FileExistsError('Refusing to overwrite upstream verification')
    queue=json.loads(queue_path.read_text());results={};valid={}
    for oid,occurrences in queue['objects'].items():
        if not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',oid):raise ValueError('Invalid object identity')
        origin=occurrences[0]['origin']
        if not re.fullmatch(r'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',origin):raise ValueError('Unexpected upstream origin')
        repo=origin.removeprefix('https://github.com/').removesuffix('.git')
        url='https://api.github.com/repos/'+repo+'/git/blobs/'+oid
        p=responses/(oid+'.json');row={'status':'UNRESOLVED','occurrences':occurrences,'source_url':url}
        try:
            saved=p.read_bytes();r=json.loads(saved);row['response_sha256']=hashlib.sha256(saved).hexdigest()
            if r['object_id']!=oid or r['origin']!=origin or r['url']!=url:raise ValueError('Response source scope mismatch')
            if r['status']!='RETURNED' or not isinstance(r['text'],str):raise ValueError('Upstream content unavailable')
            raw=r['text'].encode('utf-8')
            if len(raw)>2_000_000:raise ValueError('Upstream blob size limit')
            actual=blob_id(raw,oid);row['actual_object_id']=actual
            if actual!=oid:raise ValueError('Upstream bytes differ from queued Git object')
            valid[oid]=raw;row.update(status='EXACT_UPSTREAM_BYTES_VERIFIED',bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),cache='objects/'+oid)
        except Exception as exc:row['error']=str(exc)[:500]
        results[oid]=row
    output.mkdir(parents=True,exist_ok=False);(output/'objects').mkdir()
    for oid,raw in valid.items():
        with (output/'objects'/oid).open('xb') as stream:stream.write(raw)
    entries=queue['missing_file_side_entries']
    result={'policy':'queued-upstream-git-blob-verification-v1','queue_sha256':hashlib.sha256(queue_path.read_bytes()).hexdigest(),
        'objects':results,'unique_objects':len(results),'verified_objects':len(valid),'unresolved_objects':len(results)-len(valid),
        'original_missing_entries':len(entries),'verified_entry_occurrences':sum(e['object_id'] in valid for e in entries),
        'unresolved_entry_occurrences':sum(e['object_id'] not in valid for e in entries),
        'absent_pinned_tree_paths':queue['absent_pinned_tree_paths'],'model_calls':0,'independent_labels_created':0,
        'quality_target':'NOT_EVALUATED','scope':'Separate exact source-byte cache; frozen artifacts/maps/packets and review labels unchanged'}
    with (output/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--queue',type=Path,default=ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json')
    p.add_argument('--responses',type=Path,default=ROOT/'reports/local-source-recovery-20261024/upstream-responses')
    a=p.parse_args();r=verify(a.queue,a.responses,a.output);print(json.dumps({k:v for k,v in r.items() if k not in {'objects','absent_pinned_tree_paths'}}))

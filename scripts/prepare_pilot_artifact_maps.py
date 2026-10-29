"""Parse available local pilot blobs into a separate identity; preserve every gap."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from consistency.search_inventory import SearchInventory, in_boundary
from ingestion.git import INCLUDED_SUFFIXES, IGNORED_PARTS
from ingestion.models import digest
from ingestion.parsers import PARSER_POLICY, extract


def local_git(repo, *args, data=None):
    # Disable lazy fetching and all transports, including configured remote helpers.
    return subprocess.run(['git', '--no-pager', '-c', 'core.hooksPath='+os.devnull,
        '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', '-C', str(repo), *args],
        input=data, capture_output=True, check=True, timeout=60,
        env={**os.environ, 'GIT_NO_LAZY_FETCH': '1'}).stdout


def load_verified_cache(manifest_path, queue_path):
    """Accept only exact, scoped bytes from the saved upstream verification pass."""
    manifest_path,queue_path=map(Path,(manifest_path,queue_path))
    raw=manifest_path.read_bytes();manifest=json.loads(raw);queue_raw=queue_path.read_bytes()
    queue=json.loads(queue_raw)
    if (manifest['policy']!='queued-upstream-git-blob-verification-v1' or
        manifest['queue_sha256']!=hashlib.sha256(queue_raw).hexdigest() or
        set(manifest['objects'])!=set(queue['objects'])):
        raise ValueError('Verified cache/queue mismatch')
    objects={}
    for oid,row in manifest['objects'].items():
        if not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',oid):raise ValueError('Invalid cache object identity')
        if row['occurrences']!=queue['objects'][oid]:raise ValueError('Cache occurrence scope mismatch')
        if row['status']!='EXACT_UPSTREAM_BYTES_VERIFIED':continue
        expected='objects/'+oid;path=manifest_path.parent/expected
        if row['cache']!=expected or path.is_symlink() or not path.resolve().is_relative_to(manifest_path.parent.resolve()):
            raise ValueError('Unsafe verified cache path')
        if path.stat().st_size>2_000_000:raise ValueError('Verified cache size limit')
        blob=path.read_bytes();algorithm=hashlib.sha1 if len(oid)==40 else hashlib.sha256
        if (len(blob)!=row['bytes'] or hashlib.sha256(blob).hexdigest()!=row['sha256'] or
            algorithm(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()!=oid):
            raise ValueError('Verified cache bytes mismatch')
        scopes={(o['origin'],o['commit_id'],o['file']) for o in row['occurrences']}
        objects[oid]={'bytes':blob,'scopes':scopes}
    return {'manifest_sha256':hashlib.sha256(raw).hexdigest(),'queue_sha256':manifest['queue_sha256'],
            'objects':objects}


def map_snapshot(repo, payload, origin, max_blob_bytes=2_000_000, max_total_bytes=20_000_000, verified_cache=None):
    manifest = SearchInventory.model_validate(payload)
    if any(e.disposition!='UNKNOWN' or e.artifact_ids for e in manifest.entries):
        raise ValueError('Preparation requires UNKNOWN-only drafts, not reviewer judgments')
    sha = manifest.commit_id
    if local_git(repo, 'rev-parse', '--verify', '--end-of-options', sha+'^{commit}').decode().strip()!=sha:
        raise ValueError('Expected pinned commit')
    tree = {}
    for entry in local_git(repo, 'ls-tree', '-rz', sha).split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t',1);mode,kind,oid=meta.split()
            file=path.decode('utf-8',errors='replace')
            if in_boundary(file,manifest.prefixes):tree[file]=(mode,kind,oid.decode())
    if not tree or {e.file:e.object_id for e in manifest.entries}!={p:v[2] for p,v in tree.items()}:
        raise ValueError('Draft differs from pinned Git tree boundary')
    oids=sorted({v[2] for v in tree.values()})
    checked=local_git(repo,'cat-file','--batch-check',data=('\n'.join(oids)+'\n').encode()).splitlines()
    availability={}
    for oid,line in zip(oids,checked,strict=True):
        fields=line.decode().split()
        availability[oid]=None if fields[-1]=='missing' else (fields[1],int(fields[2]))
    rows=[];selected=[];used=0
    for path,(mode,kind,oid) in sorted(tree.items()):
        obj=availability[oid];size=obj[1] if obj else None
        recovered=verified_cache['objects'].get(oid) if verified_cache else None
        cached=obj is None and recovered is not None and (origin,sha,path) in recovered['scopes']
        if cached:obj=('blob',len(recovered['bytes']));size=obj[1]
        reason=('NON_REGULAR_FILE' if mode not in {b'100644',b'100755'} else
            'EXCLUDED_DIRECTORY' if any(p in IGNORED_PARTS for p in Path(path).parts) else
            'UNSUPPORTED_SUFFIX' if Path(path).suffix.lower() not in INCLUDED_SUFFIXES else
            'MISSING_LOCAL_BLOB' if obj is None else
            'NON_BLOB_OBJECT' if obj[0]!='blob' else
            'SIZE_LIMIT' if size>max_blob_bytes else
            'SNAPSHOT_BYTE_BUDGET' if used+size>max_total_bytes else None)
        rows.append({'file':path,'object_id':oid,'size_bytes':size,'status':reason or 'SELECTED',
                     'artifact_ids':[],'search_disposition':'UNKNOWN'})
        if verified_cache:
            rows[-1]['source_origin']='VERIFIED_UPSTREAM_CACHE' if cached else 'LOCAL_GIT' if availability[oid] else 'UNAVAILABLE'
        if reason is None:
            if not cached:selected.append(oid)
            used+=size
    texts={};blob_data={}
    if selected:
        raw=local_git(repo,'cat-file','--batch',data=('\n'.join(selected)+'\n').encode());offset=0
        for oid in selected:
            end=raw.index(b'\n',offset);header=raw[offset:end].split();size=int(header[2])
            blob=raw[end+1:end+1+size];offset=end+size+2
            algorithm=hashlib.sha1 if len(oid)==40 else hashlib.sha256
            if (header[:2]!=[oid.encode(),b'blob'] or len(blob)!=size or
                algorithm(b'blob '+str(size).encode()+b'\0'+blob).hexdigest()!=oid):
                raise ValueError('Local Git blob identity mismatch')
            blob_data[oid]=blob
        if offset!=len(raw):raise ValueError('Unexpected batch data')
    if verified_cache:
        for row in rows:
            if row['status']=='SELECTED' and row['source_origin']=='VERIFIED_UPSTREAM_CACHE':
                blob_data[row['object_id']]=verified_cache['objects'][row['object_id']]['bytes']
    for row in rows:
        if row['status']!='SELECTED':continue
        blob=blob_data[row['object_id']]
        if b'\0' in blob:row['status']='BINARY_CONTENT';continue
        try:texts[row['file']]=blob.decode('utf-8-sig')
        except UnicodeDecodeError:texts[row['file']]=blob.decode('cp1252',errors='replace')
    parser_hash=digest([(p.name,hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'ingestion').glob('*.py'))])
    project='review-development-offline::'+PARSER_POLICY+'::local-blobs-v1::'+parser_hash[:16]
    policy_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if verified_cache:
        project='review-development-offline::'+PARSER_POLICY+'::verified-cache-v1::'+parser_hash[:16]+'::'+policy_hash[:16]+'::'+verified_cache['manifest_sha256'][:16]
    repository=digest(project,origin);artifacts=[]
    for row in rows:
        if row['status']!='SELECTED':continue
        try:
            items=extract(project,repository,sha,row['file'],texts[row['file']],source_files=texts)
            artifacts.extend(a.model_dump() for a in items);row['artifact_ids']=[a.artifact_id for a in items]
            row['status']='PARSED_WITH_ERRORS' if any(a.metadata.get('parse_error') or a.metadata.get('parse_has_error') for a in items) else 'PARSED'
        except Exception as exc:row.update(status='PARSER_FAILURE',error=type(exc).__name__)
    result={'policy':'available-local-pilot-artifacts-v1','parser_identity':project,'repository':repository,
        'origin':origin,'commit_id':sha,'draft_fingerprint':digest(payload),'parser_source_sha256':parser_hash,
        'limits':{'max_blob_bytes':max_blob_bytes,'max_total_bytes':max_total_bytes},
        'files':rows,'artifacts':artifacts,'independent_labels_created':0,'model_calls':0,
        'scope':'Partial development source map; no review judgments, graph, complete semantics or negative labels',
        'quality_target':'NOT_EVALUATED'}
    if verified_cache:
        result.update(policy='available-local-plus-verified-pilot-artifacts-v1',source_policy_sha256=policy_hash,
            verified_cache={k:verified_cache[k] for k in ('manifest_sha256','queue_sha256')})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index',type=Path,default=ROOT/'reports/search-drafts-20261024/prepared/index.json')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verified-cache',type=Path)
    p.add_argument('--queue',type=Path,default=ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json');a=p.parse_args()
    cache=load_verified_cache(a.verified_cache,a.queue) if a.verified_cache else None
    index=json.loads(a.index.read_text());a.output.mkdir(parents=True,exist_ok=False);results={}
    for key,snapshot in index['snapshots'].items():
        try:
            draft=a.index.parent/snapshot['draft']
            if hashlib.sha256(draft.read_bytes()).hexdigest()!=snapshot['sha256']:raise ValueError('Draft checksum mismatch')
            result=map_snapshot(ROOT/'data/repos'/snapshot['repository'],json.loads(draft.read_text()),snapshot['origin'],verified_cache=cache)
            destination=a.output/(key.replace('/','-')+'.json')
            with destination.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
            from collections import Counter
            results[key]={'status':'PARTIAL_SOURCE_MAP','path':destination.name,
                'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'parser_identity':result['parser_identity'],
                'repository':result['repository'],'files':len(result['files']),'artifacts':len(result['artifacts']),
                'file_statuses':dict(Counter(r['status'] for r in result['files']))}
        except Exception as exc:results[key]={'status':'FAILED_RETAINED','error':type(exc).__name__}
    summary={'input_sha256':hashlib.sha256(a.index.read_bytes()).hexdigest(),'cases':index['cases'],
        'snapshots':results,'new_labels':0,'model_calls':0,'quality_target':'NOT_EVALUATED'}
    with (a.output/'index.json').open('x') as stream:json.dump(summary,stream,indent=2);stream.write('\n')
    print(json.dumps({'snapshots':len(results),'failed':sum(r['status']=='FAILED_RETAINED' for r in results.values()),
        'files':sum(r.get('files',0) for r in results.values()),'artifacts':sum(r.get('artifacts',0) for r in results.values())}))


if __name__=='__main__':main()

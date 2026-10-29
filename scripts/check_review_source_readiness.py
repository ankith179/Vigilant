"""Offline source-readiness probe; never validate or manufacture review judgments."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion.models import Artifact,digest
from scripts.prepare_pilot_artifact_maps import local_git,load_verified_cache


def pinned_tree(repo,commit):
    if not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',commit):raise ValueError('Expected pinned commit')
    if local_git(repo,'rev-parse','--verify','--end-of-options',commit+'^{commit}').decode().strip()!=commit:
        raise ValueError('Commit identity mismatch')
    tree={}
    for entry in local_git(repo,'ls-tree','-rz',commit).split(b'\0'):
        if not entry:continue
        meta,path=entry.split(b'\t',1);mode,kind,oid=meta.split()
        tree[path.decode('utf-8')]={'mode':mode.decode(),'kind':kind.decode(),'object_id':oid.decode()}
    return tree


def verify_source(repo,origin,reference,artifact,cache=None,tree=None):
    """Require an exact tree binding, raw blob identity, stored span and reference."""
    try:
        ref=reference;a=Artifact.model_validate(artifact)
        if (ref['artifact_id']!=a.artifact_id or ref['commit_id']!=a.commit_id or ref['file']!=a.file_path or
            ref['content_hash']!=a.content_hash or a.content_hash!=digest(a.content) or
            a.artifact_id!=digest(a.project_id,a.repository,a.file_path,a.artifact_type,a.symbol) or
            ref['start_line']<a.start_line or ref['end_line']>a.end_line or ref['end_line']<ref['start_line']):
            raise ValueError('Reference/artifact mismatch')
        tree=pinned_tree(repo,a.commit_id) if tree is None else tree
        entry=tree.get(a.file_path)
        if entry is None:return {'status':'NOT_IN_PINNED_TREE'}
        if entry['mode'] not in {'100644','100755'} or entry['kind']!='blob':raise ValueError('Nonregular source')
        oid=entry['object_id'];checked=local_git(repo,'cat-file','--batch-check',data=(oid+'\n').encode()).decode().split()
        if checked==[oid,'missing']:
            saved=cache['objects'].get(oid) if cache else None
            if saved is None or (origin,a.commit_id,a.file_path) not in saved['scopes']:
                return {'status':'UNAVAILABLE_BLOB','object_id':oid}
            raw=saved['bytes'];source='VERIFIED_RECOVERY_CACHE'
        else:
            if checked[:2]!=[oid,'blob'] or int(checked[2])>2_000_000:raise ValueError('Unexpected source size/type')
            raw=local_git(repo,'cat-file','blob',oid);source='VERIFIED_LOCAL_GIT'
        if len(raw)>2_000_000:raise ValueError('Source size limit')
        algorithm=hashlib.sha1 if len(oid)==40 else hashlib.sha256
        if algorithm(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=oid:raise ValueError('Git blob identity mismatch')
        try:text=raw.decode('utf-8-sig')
        except UnicodeDecodeError:text=raw.decode('cp1252',errors='replace')
        lines=text.splitlines()
        if a.content.splitlines()!=lines[a.start_line-1:a.end_line]:raise ValueError('Stored artifact differs from pinned blob')
        if ref['start_line']<1 or ref['end_line']>max(1,len(lines)):raise ValueError('Reference outside blob')
        return {'status':source,'object_id':oid,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                'quote':'\n'.join(lines[ref['start_line']-1:ref['end_line']])}
    except Exception as exc:return {'status':'SOURCE_CHECK_FAILED','error':type(exc).__name__+': '+str(exc)[:200]}


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite readiness results')
    source=ROOT/'reports/recovered-review-20261024';packets=source/'packets'
    staging=json.loads((source/'STAGING.json').read_text());database=ROOT/'data/snapshots/pilot-review-recovered-20261024.db'
    before=hashlib.sha256(database.read_bytes()).hexdigest()
    if before!=staging['database_sha256']:raise ValueError('Source Store checksum mismatch')
    manifest_path=packets/'manifest.json';manifest=json.loads(manifest_path.read_text())
    for file,h in manifest['files'].items():
        if hashlib.sha256((packets/file).read_bytes()).hexdigest()!=h:raise ValueError('Packet checksum mismatch')
    queue=ROOT/'reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json'
    cache_path=ROOT/'reports/local-source-recovery-20261024/upstream-verified/result.json'
    cache=load_verified_cache(cache_path,queue);trees={};rows=[]
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        for file in sorted(packets.glob('*-packet.json')):
            packet=json.loads(file.read_text());repo=ROOT/'data/repos'/packet['original_repository_alias']
            for side,snapshot in packet['snapshot_sides'].items():
                key=str(repo),snapshot['commit_id']
                if key not in trees:trees[key]=pinned_tree(repo,key[1])
                for item in snapshot['changed_files']:
                    row={'case_id':packet['case_id'],'side':side,'file':item['file'],'repository':packet['repository'],
                         'commit_id':snapshot['commit_id'],'search_disposition':item['search_disposition']}
                    ref=item['source_reference']
                    if ref is None:
                        status='MISSING_SOURCE_REFERENCE' if item['file'] in trees[key] else 'NOT_IN_PINNED_TREE'
                        row.update(local={'status':status},with_cache={'status':status})
                    else:
                        raw=db.execute('select payload from artifacts where id=?',(digest(ref['artifact_id'],ref['commit_id']),)).fetchone()
                        if raw is None:raise ValueError('Unavailable stored source')
                        artifact={k:v for k,v in json.loads(raw[0]).items() if k!='id'}
                        if artifact['repository']!=packet['repository'] or artifact['project_id']!=snapshot['parser_identity']:
                            raise ValueError('Foreign canonical source')
                        row['local']=verify_source(repo,packet['origin'],ref,artifact,tree=trees[key])
                        row['with_cache']=verify_source(repo,packet['origin'],ref,artifact,cache,trees[key])
                        if row['with_cache']['status'].startswith('VERIFIED_') and row['with_cache'].get('quote')!=item['excerpt']:
                            row['with_cache']={'status':'SOURCE_CHECK_FAILED','error':'Pinned-source excerpt mismatch'}
                    rows.append(row)
    if hashlib.sha256(database.read_bytes()).hexdigest()!=before:raise ValueError('Frozen Store changed')
    result={'policy':'offline-review-source-readiness-v1','rows':rows,'denominator':len(rows),'cases':manifest['cases'],
        'local_statuses':dict(Counter(r['local']['status'] for r in rows)),
        'with_cache_statuses':dict(Counter(r['with_cache']['status'] for r in rows)),
        'database_sha256':before,'packet_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'cache_manifest_sha256':cache['manifest_sha256'],'queue_sha256':cache['queue_sha256'],
        'default_review_intake':'NOT_RUN_WITH_BLANK_FORMS; cache policy not connected to validate_reviews',
        'semantic_support':'NOT_REVIEWED','independent_labels_created':0,'model_calls':0,'new_fetches':0,
        'quality_target_91':'NOT_EVALUATED','quality_target_95':'NOT_EVALUATED'}
    output.mkdir(parents=True,exist_ok=False)
    with (output/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='rows'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(p.parse_args().output)))

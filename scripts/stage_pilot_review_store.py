"""Stage checksummed partial source maps in a new, isolated development Store."""
import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database.store import Store
from ingestion.models import Artifact,digest


def validate_map(payload):
    project=payload['parser_identity'];repo=payload['repository'];commit=payload['commit_id']
    expected='review-development-offline::native-compiler-coverage-v4::local-blobs-v1::'+payload['parser_source_sha256'][:16]
    if payload['policy']=='available-local-plus-verified-pilot-artifacts-v1':
        cache=payload['verified_cache']
        if any(not re.fullmatch(r'[a-f0-9]{64}',value) for value in
               (payload['parser_source_sha256'],payload['source_policy_sha256'],cache['manifest_sha256'],cache['queue_sha256'])):
            raise ValueError('Invalid verified-cache provenance')
        expected='review-development-offline::native-compiler-coverage-v4::verified-cache-v1::'+payload['parser_source_sha256'][:16]+'::'+payload['source_policy_sha256'][:16]+'::'+cache['manifest_sha256'][:16]
    if project!=expected or repo!=digest(project,payload['origin']):raise ValueError('Map identity mismatch')
    if payload['policy'] not in {'available-local-pilot-artifacts-v1','available-local-plus-verified-pilot-artifacts-v1'} or payload['independent_labels_created']!=0 or payload['model_calls']!=0:
        raise ValueError('Expected unlabelled offline source map')
    rows={r['file']:r for r in payload['files']}
    if len(rows)!=len(payload['files']):raise ValueError('Duplicate file entries')
    allowed={'PARSED','PARSED_WITH_ERRORS','MISSING_LOCAL_BLOB','NON_REGULAR_FILE',
             'UNSUPPORTED_SUFFIX','EXCLUDED_DIRECTORY','SIZE_LIMIT','SNAPSHOT_BYTE_BUDGET','BINARY_CONTENT','PARSER_FAILURE'}
    if any(r['search_disposition']!='UNKNOWN' or r['status'] not in allowed for r in rows.values()):
        raise ValueError('Review dispositions or unsupported file status in source map')
    if payload['policy']=='available-local-plus-verified-pilot-artifacts-v1' and any(
        r.get('source_origin') not in {'LOCAL_GIT','VERIFIED_UPSTREAM_CACHE','UNAVAILABLE'} for r in rows.values()):
        raise ValueError('Missing source provenance')
    items=[Artifact.model_validate(a) for a in payload['artifacts']]
    if len({a.artifact_id for a in items})!=len(items):raise ValueError('Duplicate artifact identities')
    parents={a.file_path:a for a in items if not a.symbol};by_file={p:[] for p in rows}
    for a in items:
        if (a.project_id!=project or a.repository!=repo or a.commit_id!=commit or a.file_path not in rows or
            a.artifact_id!=digest(project,repo,a.file_path,a.artifact_type,a.symbol)):
            raise ValueError('Artifact scope/identity mismatch')
        parent=parents.get(a.file_path)
        if parent is None:raise ValueError('Missing parent source artifact')
        if a.symbol and a.content!='\n'.join(parent.content.splitlines()[a.start_line-1:a.end_line]):
            raise ValueError('Artifact source span mismatch')
        by_file[a.file_path].append(a.artifact_id)
    for path,r in rows.items():
        if len(r['artifact_ids'])!=len(set(r['artifact_ids'])) or set(r['artifact_ids'])!=set(by_file[path]):
            raise ValueError('File/artifact inventory mismatch')
        if bool(by_file[path])!=(r['status'] in {'PARSED','PARSED_WITH_ERRORS'}):
            raise ValueError('File coverage status differs from stored sources')
    return items


def stage(index_path,destination):
    index_path=Path(index_path);destination=Path(destination)
    if destination.exists():raise FileExistsError('Refusing to overwrite a database')
    index=json.loads(index_path.read_text());routes={};statuses=Counter();artifact_count=0
    runtime=Path(tempfile.gettempdir())/'vigilant-runtime';runtime.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pilot-review-',dir=runtime) as temporary:
        live=Path(temporary)/'live.db';store=Store('sqlite:///'+str(live))
        try:
            for key,s in index['snapshots'].items():
                alias,commit=key.split('/')
                if not re.fullmatch(r'[A-Za-z0-9_-]+',alias) or not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',commit):
                    raise ValueError('Invalid snapshot route')
                if s['status']!='PARTIAL_SOURCE_MAP':raise ValueError('Unavailable snapshot cannot be silently omitted')
                path=(index_path.parent/s['path']).resolve()
                if not path.is_relative_to(index_path.parent.resolve()):raise ValueError('Map path outside source directory')
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Source map checksum mismatch')
                m=json.loads(raw);items=validate_map(m)
                if m['commit_id']!=commit or m['repository']!=s['repository'] or m['parser_identity']!=s['parser_identity']:
                    raise ValueError('Map/index snapshot mismatch')
                project=m['parser_identity'];repo=m['repository'];counts=Counter(r['status'] for r in m['files'])
                if dict(counts)!=s['file_statuses'] or len(m['files'])!=s['files'] or len(items)!=s['artifacts']:
                    raise ValueError('Map/index denominator mismatch')
                store.put('projects',project,{'project_id':project,'name':'Pilot review sources (partial, unreviewed)',
                    'development_only':True,'independent_labels':0})
                store.put('repositories',repo,{'project_id':project,'repository':repo,'name':alias,
                    'path':'data/repos/'+alias,'path_base':'project_root','origin':m['origin'],
                    'source_scope':'PARTIAL_OFFLINE_DEVELOPMENT','whole_project_semantics':False})
                store.put('commits',digest(repo,commit),{'project_id':project,'repository':repo,'commit_id':commit,
                    'review_source_map':{'status':'PARTIAL_UNREVIEWED','sha256':s['sha256'],
                        'verification':'SAVED_MAP_CHECKSUM_AND_ARTIFACT_IDENTITIES_SPANS; not new Git/semantic review',
                        'file_statuses':dict(counts),'files':m['files'],'independent_labels':0}})
                store.put_many('artifacts',[(digest(a.artifact_id,commit),a.model_dump()) for a in items])
                routes[key]={'repository':repo,'commit_id':commit,'parser_identity':project}
                statuses.update(counts);artifact_count+=len(items)
            cases=[{'case_id':c['case_id'],'original_repository_alias':c['repository'],
                'base':routes[c['base']],'head':routes[c['head']],
                'label_status':'UNLABELLED','search_coverage':'UNKNOWN'} for c in index['cases']]
        finally:store.engine.dispose()
        portable=Path(temporary)/'portable.db'
        with closing(sqlite3.connect(live.resolve().as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(portable)) as dst:
            src.backup(dst);dst.execute('PRAGMA journal_mode=DELETE')
            if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Review store integrity failure')
        destination.parent.mkdir(parents=True,exist_ok=True)
        # Publish a finished file atomically without replacing a pre-existing DB.
        with tempfile.NamedTemporaryFile(dir=destination.parent,suffix='.pending',delete=False) as stream:
            pending=Path(stream.name)
        try:
            shutil.copyfile(portable,pending);os.link(pending,destination)
        finally:pending.unlink(missing_ok=True)
    return {'policy':'isolated-pilot-review-store-v1','database_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
        'source_index_sha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),'snapshots':len(routes),
        'artifacts':artifact_count,'files':sum(statuses.values()),'file_statuses':dict(statuses),'case_routes':cases,
        'graph_or_investigation_created':False,'independent_labels':0,'model_calls':0,'quality_target':'NOT_EVALUATED'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index',type=Path,default=ROOT/'reports/pilot-artifacts-20261024/maps/index.json')
    p.add_argument('--database',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.report.exists():raise FileExistsError('Refusing to overwrite staging report')
    result=stage(a.index,a.database);a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='case_routes'}))

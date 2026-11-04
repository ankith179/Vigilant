"""Read validated partial snapshots without Store writes, Git, import or reparse."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from ingestion.models import digest
from scripts.stage_pilot_review_store import validate_map


def file_sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1_048_576),b''):h.update(block)
    return h.hexdigest()


def read_json(path,maximum=80_000_000):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>maximum:
        raise ValueError('Invalid or oversized staged source file')
    raw=path.read_bytes()
    if len(raw)>maximum:raise ValueError('Staged source file exceeds budget')
    return raw,json.loads(raw)


class StagedSourceReader:
    """Only checksum-pinned frozen Stores; this does not verify raw Git or semantics."""
    def __init__(self,database,index,staging):
        if Path(database).is_symlink():raise ValueError('Expected regular frozen database')
        self.database=Path(database).resolve();self.index_path=Path(index).resolve()
        index_raw,self.index=read_json(index,5_000_000);staging_raw,metadata=read_json(staging,5_000_000)
        if self.database.is_symlink() or not self.database.is_file():raise ValueError('Expected regular frozen database')
        self.binding={'policy':'validated-staged-source-reader-v1','database_sha256':file_sha256(database),
            'source_index_sha256':hashlib.sha256(index_raw).hexdigest(),'staging_sha256':hashlib.sha256(staging_raw).hexdigest()}
        if (self.binding['database_sha256']!=metadata['database_sha256'] or
            self.binding['source_index_sha256']!=metadata['source_index_sha256']):
            raise ValueError('Staged database/index checksum mismatch')
        self.routes={}
        for key,row in self.index['snapshots'].items():
            alias,commit=key.split('/');route=row['repository'],commit
            if not re.fullmatch(r'[A-Za-z0-9_-]+',alias) or not re.fullmatch(r'[a-f0-9]{40}(?:[a-f0-9]{24})?',commit):
                raise ValueError('Expected canonical alias and pinned commit')
            if row['status']!='PARTIAL_SOURCE_MAP' or route in self.routes:raise ValueError('Unavailable or duplicate staged route')
            self.routes[route]=row
        if len(self.routes)!=metadata['snapshots']:raise ValueError('Snapshot denominator mismatch')
        # The verified main file is an immutable checkpoint, never a live WAL view.
        self.connection=sqlite3.connect(self.database.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        self.connection.execute('PRAGMA query_only=ON')

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):
        if self.connection is not None:
            self.connection.close();self.connection=None
            if file_sha256(self.database)!=self.binding['database_sha256']:raise ValueError('Frozen database changed during read')

    def _row(self,table,key):
        if table not in {'repositories','commits'}:raise ValueError('Unsupported staged table')
        row=self.connection.execute('select payload from '+table+' where id=?',(key,)).fetchone()
        if row is None:raise ValueError('Unavailable staged record')
        return json.loads(row[0])

    def snapshot(self,repository,commit_id):
        if self.connection is None:raise ValueError('Staged reader is closed')
        s=self.routes.get((repository,commit_id))
        if s is None:raise ValueError('Snapshot outside pinned staged index')
        relative=Path(s['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Map path outside staged scope')
        candidate=self.index_path.parent/relative;path=candidate.resolve()
        if candidate.is_symlink() or not path.is_relative_to(self.index_path.parent.resolve()):raise ValueError('Map path outside staged scope')
        raw,m=read_json(path)
        if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Source map checksum mismatch')
        items=validate_map(m)
        if len(items)>20_000 or sum(len(a.content) for a in items)>20_000_000:
            raise ValueError('Staged snapshot exceeds investigation artifact/text budget')
        counts=dict(Counter(r['status'] for r in m['files']))
        if (m['repository']!=repository or m['commit_id']!=commit_id or m['parser_identity']!=s['parser_identity'] or
            len(items)!=s['artifacts'] or len(m['files'])!=s['files'] or counts!=s['file_statuses']):
            raise ValueError('Map/index identity or denominator mismatch')
        if any(a.content_hash!=digest(a.content) for a in items):raise ValueError('Map artifact content hash mismatch')
        repo=self._row('repositories',repository);commit=self._row('commits',digest(repository,commit_id))
        if (repo.get('project_id')!=m['parser_identity'] or repo.get('repository')!=repository or repo.get('origin')!=m['origin'] or
            repo.get('source_scope')!='PARTIAL_OFFLINE_DEVELOPMENT' or commit.get('project_id')!=m['parser_identity'] or
            commit.get('repository')!=repository or commit.get('commit_id')!=commit_id):raise ValueError('Stored staged scope mismatch')
        coverage=commit['review_source_map']
        if (coverage['status']!='PARTIAL_UNREVIEWED' or coverage['sha256']!=s['sha256'] or coverage['files']!=m['files'] or
            coverage['file_statuses']!=counts or coverage['independent_labels']!=0):raise ValueError('Stored staged coverage mismatch')
        stored={}
        count=self.connection.execute('select count(*) from artifacts where repository=? and commit_id=?',(repository,commit_id)).fetchone()[0]
        if count!=len(items):raise ValueError('Stored artifact denominator differs from pinned map')
        for (payload,) in self.connection.execute('select payload from artifacts where repository=? and commit_id=?',(repository,commit_id)):
            a=json.loads(payload);key=a.pop('id')
            if key!=digest(a['artifact_id'],commit_id) or a['artifact_id'] in stored:raise ValueError('Stored artifact key mismatch')
            stored[a['artifact_id']]=a
        if stored!={a['artifact_id']:a for a in m['artifacts']}:raise ValueError('Stored artifacts differ from pinned source map')
        return {'repository':repository,'commit_id':commit_id,'project_id':m['parser_identity'],'origin':m['origin'],
            'artifacts':items,'files':deepcopy(m['files']),
            'coverage':{'status':'PARTIAL_UNREVIEWED','files':len(m['files']),'artifact_versions':len(items),
                'file_statuses':counts,'search_dispositions':dict(Counter(r['search_disposition'] for r in m['files'])),
                'whole_repository_coverage':False,'semantic_support':'NOT_ESTABLISHED','complete_test_coverage':'NOT_ESTABLISHED'},
            'provenance':{**self.binding,'source_map_sha256':s['sha256'],'parser_identity':m['parser_identity'],
                'verified_cache':deepcopy(m.get('verified_cache')),
                'source_verification':'CHECKSUM_PINNED_MAP_AND_STORED_ARTIFACTS_ONLY','raw_git_verification':'NOT_PERFORMED_BY_READER'},
            'model_calls':0,'independent_labels_created':0,'quality_target':'NOT_EVALUATED'}

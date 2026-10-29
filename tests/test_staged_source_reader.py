"""Checksum/read-only engineering fixtures; these are not independent labels."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import pytest
from ingestion.models import digest
from investigation.staged import StagedSourceReader,file_sha256
from scripts.stage_pilot_review_store import stage
from tests.test_pilot_review_store import maps,manifest_fixture


@pytest.fixture
def staged_inputs(maps,tmp_path):
    index,source,m,summary=maps;database=tmp_path/'frozen.db';metadata=tmp_path/'staging.json'
    metadata.write_text(json.dumps(stage(index,database)))
    return database,index,metadata,source,m,summary


def test_read_only_reader_preserves_identity_statuses_and_snapshot(staged_inputs):
    database,index,metadata,source,m,_=staged_inputs;before=file_sha256(database)
    with StagedSourceReader(database,index,metadata) as reader:
        snapshot=reader.snapshot(m['repository'],m['commit_id'])
        assert {a.artifact_id for a in snapshot['artifacts']}=={a['artifact_id'] for a in m['artifacts']}
        assert snapshot['coverage']['search_dispositions']=={'UNKNOWN':2}
        assert snapshot['coverage']['whole_repository_coverage'] is False
        assert snapshot['provenance']['raw_git_verification']=='NOT_PERFORMED_BY_READER'
        assert snapshot['model_calls']==snapshot['independent_labels_created']==0
        with pytest.raises(sqlite3.OperationalError):reader.connection.execute('delete from artifacts')
        snapshot['files'].clear();snapshot['artifacts'][0].content='caller mutation'
        assert len(reader.snapshot(m['repository'],m['commit_id'])['files'])==2
    assert file_sha256(database)==before and not Path(str(database)+'-wal').exists() and not Path(str(database)+'-shm').exists()
    with pytest.raises(ValueError,match='closed'):reader.snapshot(m['repository'],m['commit_id'])


@pytest.mark.parametrize('mode',['database','index','map','route','map_path','stored_artifact','stored_coverage','staging_count','extra_artifact'])
def test_reader_rejects_corrupt_or_rebound_sources(staged_inputs,mode):
    database,index,metadata,source,m,summary=staged_inputs
    staging=json.loads(metadata.read_text());route=next(iter(summary['snapshots'].values()))
    if mode=='database':
        with database.open('ab') as stream:stream.write(b'changed')
    elif mode=='index':index.write_text(index.read_text()+'\n')
    elif mode=='map':source.write_text(source.read_text()+'\n')
    elif mode=='route':
        route['parser_identity']='foreign';index.write_text(json.dumps(summary));staging['source_index_sha256']=file_sha256(index)
    elif mode=='map_path':
        route['path']='../'+source.parent.name+'/'+source.name;index.write_text(json.dumps(summary));staging['source_index_sha256']=file_sha256(index)
    elif mode=='staging_count':staging['snapshots']+=1
    else:
        with closing(sqlite3.connect(database)) as db:
            table='artifacts' if mode in {'stored_artifact','extra_artifact'} else 'commits'
            key,raw=db.execute('select id,payload from '+table+' limit 1').fetchone();data=json.loads(raw)
            if mode=='extra_artifact':
                db.execute('insert into artifacts select ?,project_id,repository,commit_id,run_id,payload from artifacts limit 1',('extra-artifact',))
            else:
                if mode=='stored_artifact':data.update(content='forged',content_hash=digest('forged'))
                else:data['review_source_map']['files'][0]['status']='MISSING_LOCAL_BLOB'
                db.execute('update '+table+' set payload=? where id=?',(json.dumps(data),key))
            db.commit()
        staging['database_sha256']=file_sha256(database)
    metadata.write_text(json.dumps(staging))
    with pytest.raises(ValueError):
        with StagedSourceReader(database,index,metadata) as reader:reader.snapshot(m['repository'],m['commit_id'])


def test_reader_rejects_foreign_and_unpinned_requests(staged_inputs):
    database,index,metadata,source,m,_=staged_inputs
    with StagedSourceReader(database,index,metadata) as reader:
        for repo,commit in [('foreign',m['commit_id']),(m['repository'],'HEAD')]:
            with pytest.raises(ValueError,match='outside pinned'):reader.snapshot(repo,commit)

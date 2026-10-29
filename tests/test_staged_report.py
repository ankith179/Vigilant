"""Composition acceptance over authored fixtures, never independent accuracy."""
import pytest
from tests.test_staged_inspection import inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_report import compose_staged_report
from ingestion.models import digest


def test_report_links_revision_scoped_sources_without_findings(inputs):
    db,index,staging,policy,a=inputs;before=file_sha256(db)
    args={'repository':a['repository'],'commit_id':a['commit_id'],'base_commit':a['commit_id'],
          'base_artifact_ids':[a['artifact_id']],'head_artifact_ids':[a['artifact_id']]}
    with StagedSourceReader(db,index,staging) as reader:
        report=compose_staged_report(reader,policy,args)
        assert report==compose_staged_report(reader,policy,args)
        assert len(report['evidence'])==2
        assert report['findings']==[] and not report['obligation_assessment']['reviewed_registry_supplied']
        assert report['coverage']['whole_repository_coverage'] is False
        for role in ('base','head'):
            assert report['roles'][role]['graph']['scope']['commit_id']==a['commit_id']
        rid=report.pop('report_id');assert digest(report)==rid
        assert reader.connection.execute('select count(*) from analysis_runs').fetchone()[0]==0
    assert file_sha256(db)==before


@pytest.mark.parametrize('mode',['foreign','mutable_base','duplicate'])
def test_report_rejects_invalid_scope(inputs,mode):
    db,index,staging,policy,a=inputs
    args={'repository':a['repository'],'commit_id':a['commit_id'],'base_commit':a['commit_id'],'base_artifact_ids':[a['artifact_id']]}
    if mode=='foreign':args['base_artifact_ids']=['missing']
    elif mode=='mutable_base':args['base_commit']='HEAD'
    else:args['base_artifact_ids']*=2
    with StagedSourceReader(db,index,staging) as reader:
        with pytest.raises(ValueError):compose_staged_report(reader,policy,args)


def test_report_retains_failed_source_as_unknown(inputs,monkeypatch):
    db,index,staging,policy,a=inputs
    def reject(*args):raise ValueError('unavailable')
    monkeypatch.setattr(policy,'verify',reject)
    with StagedSourceReader(db,index,staging) as reader:
        report=compose_staged_report(reader,policy,{'repository':a['repository'],'commit_id':a['commit_id'],'base_commit':a['commit_id'],'head_artifact_ids':[a['artifact_id']]})
        assert len(report['source_unknowns'])==1 and report['evidence']==[] and report['findings']==[]
        assert report['roles']['head']['graph']['withheld_edges']

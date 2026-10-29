"""Graph adapter engineering checks; no research labels."""
import json
import pytest
from tests.test_staged_inspection import inputs
from tests.test_verified_cache_maps import cache_fixture,manifest_fixture
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_graph import project_staged_graph
from ingestion.models import digest


def test_projection_retains_coverage_provenance_and_frozen_store(inputs):
    db,index,staging,policy,a=inputs;before=file_sha256(db)
    with StagedSourceReader(db,index,staging) as reader:
        args={'repository':a['repository'],'commit_id':a['commit_id'],'artifact_ids':[a['artifact_id']]}
        result=project_staged_graph(reader,policy,args)
        assert result==project_staged_graph(reader,policy,args)
        assert result['coverage']['whole_repository_coverage'] is False
        assert result['findings']==[] and result['consistency']=='NOT_ESTABLISHED'
        d=result['denominators'];assert d['page_candidate_edges']==d['source_verified_edges']+d['withheld_edges']
        for edge in result['edges']:
            assert edge['source_edge']['commit_id']==a['commit_id']
            assert all(r['status']=='VERIFIED' for r in edge['endpoint_source_receipts'])
            assert not edge['causal_impact_verified']
        rid=result.pop('result_id');assert digest(result)==rid
        assert reader.connection.execute('select count(*) from graph_edges').fetchone()[0]==0
    assert file_sha256(db)==before


@pytest.mark.parametrize('mode',['foreign','duplicate','limit','revision'])
def test_invalid_graph_selection_rejected(inputs,mode):
    db,index,staging,policy,a=inputs
    args={'repository':a['repository'],'commit_id':a['commit_id'],'artifact_ids':[a['artifact_id']]}
    if mode=='foreign':args['artifact_ids']=['missing']
    elif mode=='duplicate':args['artifact_ids']*=2
    elif mode=='limit':args['limit']=True
    else:args['commit_id']='HEAD'
    with StagedSourceReader(db,index,staging) as reader:
        with pytest.raises(ValueError):project_staged_graph(reader,policy,args)


def test_unavailable_source_stays_unknown(inputs,monkeypatch):
    db,index,staging,policy,a=inputs
    def reject(*args):raise ValueError('source unavailable')
    monkeypatch.setattr(policy,'verify',reject)
    with StagedSourceReader(db,index,staging) as reader:
        result=project_staged_graph(reader,policy,{'repository':a['repository'],'commit_id':a['commit_id'],'artifact_ids':[a['artifact_id']]})
        assert result['denominators']['incident_candidate_edges']>0
        assert not result['edges'] and result['withheld_edges']
        assert result['findings']==[]

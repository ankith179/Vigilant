"""Authored partial-source engineering fixtures, never independent labels."""
from copy import deepcopy
import json
import pytest
from ingestion.models import digest
from investigation.staged import StagedSourceReader,file_sha256
from investigation.staged_comparison import compare_staged
from scripts.stage_pilot_review_store import stage
from tests.test_pilot_review_store import maps,manifest_fixture


@pytest.fixture
def comparison_inputs(maps,tmp_path):
    index,source,m,summary=maps
    return index,source,m,summary,tmp_path


def run_pair(inputs,head):
    index,source,base,summary,root=inputs
    oldkey=next(iter(summary['snapshots']));headkey='fixture/'+head['commit_id']
    destination=root/'head.json';destination.write_text(json.dumps(head))
    row=deepcopy(summary['snapshots'][oldkey])
    row.update(path=destination.name,sha256=file_sha256(destination),files=len(head['files']),artifacts=len(head['artifacts']))
    from collections import Counter
    row['file_statuses']=dict(Counter(r['status'] for r in head['files']))
    summary['snapshots'][headkey]=row;summary['cases'][0]['head']=headkey
    index.write_text(json.dumps(summary));db=root/'comparison.db';metadata=root/'comparison-staging.json'
    metadata.write_text(json.dumps(stage(index,db)));before=file_sha256(db)
    with StagedSourceReader(db,index,metadata) as reader:
        result=compare_staged(reader,base['repository'],base['commit_id'],head['commit_id'])
        assert compare_staged(reader,base['repository'],base['commit_id'],head['commit_id'])==result
    assert file_sha256(db)==before
    return result


def next_snapshot(inputs):
    head=deepcopy(inputs[2]);head['commit_id']='b'*40
    for a in head['artifacts']:a['commit_id']=head['commit_id']
    return head


def test_equal_observations_keep_all_unchanged_rows_and_unknown_search(comparison_inputs):
    result=run_pair(comparison_inputs,next_snapshot(comparison_inputs))
    assert result['outcomes']['files']=={'SAME_OBJECT_ID':2}
    assert result['outcomes']['artifacts']=={'SAME_EXTRACTED_CONTENT':len(comparison_inputs[2]['artifacts'])}
    assert result['denominators']['artifact_versions_unavailable']==0
    assert result['coverage']['base']['search_dispositions']=={'UNKNOWN':2}
    assert result['coverage']['whole_repository_coverage'] is False
    assert result['coverage']['consistency']=='NOT_ESTABLISHED'
    assert result['model_calls']==result['independent_labels_created']==0


def test_observed_content_change_is_not_semantic_change(comparison_inputs):
    head=next_snapshot(comparison_inputs)
    row=next(r for r in head['files'] if r['file'].endswith('.py'))
    path=row['file'];row['object_id']='c'*40
    for a in head['artifacts']:
        if a['file_path']==path:
            a['content']=a['content'].replace('1','2');a['content_hash']=digest(a['content']);a['version']=a['content_hash']
    result=run_pair(comparison_inputs,head)
    assert result['outcomes']['files']['DIFFERENT_OBJECT_ID']==1
    assert result['outcomes']['artifacts']['DIFFERENT_EXTRACTED_CONTENT']>=1
    assert result['coverage']['semantic_equivalence']=='NOT_ESTABLISHED'


@pytest.mark.parametrize('status',['PARSED_WITH_ERRORS','MISSING_LOCAL_BLOB','UNSUPPORTED_SUFFIX','NON_REGULAR_FILE','PARSER_FAILURE','SIZE_LIMIT','SNAPSHOT_BYTE_BUDGET','BINARY_CONTENT','EXCLUDED_DIRECTORY'])
def test_extraction_gaps_remain_unknown_in_denominators(comparison_inputs,status):
    head=next_snapshot(comparison_inputs);row=head['files'][0];row['status']=status
    ids=set(row['artifact_ids'])
    if status!='PARSED_WITH_ERRORS':
        head['artifacts']=[a for a in head['artifacts'] if a['artifact_id'] not in ids];row['artifact_ids']=[]
    result=run_pair(comparison_inputs,head)
    affected=[a for a in result['artifacts'] if a['artifact_id'] in ids]
    assert len(affected)==len(ids) and all(a['outcome']=='UNKNOWN' for a in affected)
    assert all('HEAD_'+status in a['uncertainty'] for a in affected)
    assert sum(result['outcomes']['artifacts'].values())==result['denominators']['artifact_union']
    assert result['denominators']['artifact_union']==len(comparison_inputs[2]['artifacts'])
    if status=='PARSED_WITH_ERRORS':assert all(a['observed_content_relation']=='SAME_EXTRACTED_CONTENT' for a in affected)
    else:assert result['denominators']['artifact_versions_unavailable']==len(ids)


@pytest.mark.parametrize('mode',['removed_file','new_file','removed_symbol','new_symbol'])
def test_unpaired_entries_never_become_additions_or_deletions(comparison_inputs,mode):
    head=next_snapshot(comparison_inputs);row=head['files'][0]
    if mode=='removed_file':
        head['files'].remove(row);head['artifacts']=[a for a in head['artifacts'] if a['file_path']!=row['file']]
    elif mode=='new_file':
        row=deepcopy(row);row['file']='new.py';head['files'].append(row)
        additions=[]
        for a in head['artifacts']:
            if a['file_path']==head['files'][0]['file']:
                a=deepcopy(a);a['file_path']='new.py';a['artifact_id']=digest(a['project_id'],a['repository'],a['file_path'],a['artifact_type'],a['symbol']);additions.append(a)
        row['artifact_ids']=[a['artifact_id'] for a in additions];head['artifacts'].extend(additions)
    else:
        a=next(a for a in head['artifacts'] if a['symbol']);row=next(r for r in head['files'] if r['file']==a['file_path'])
        if mode=='removed_symbol':head['artifacts'].remove(a);row['artifact_ids'].remove(a['artifact_id'])
        else:
            a=deepcopy(a);a['symbol']+='::another';a['artifact_id']=digest(a['project_id'],a['repository'],a['file_path'],a['artifact_type'],a['symbol']);head['artifacts'].append(a);row['artifact_ids'].append(a['artifact_id'])
    result=run_pair(comparison_inputs,head)
    assert result['outcomes']['artifacts']['UNKNOWN']>0
    assert result['denominators']['artifact_versions_unavailable']>0
    assert all(a['outcome']=='UNKNOWN' for a in result['artifacts'] if a['base'] is None or a['head'] is None)
    if mode in {'removed_file','new_file'}:
        assert result['outcomes']['files']['UNKNOWN']==1 and result['denominators']['file_rows_unavailable']==1
    assert result['coverage']['absent_side_means_deleted_or_added'] is False


def test_invalid_reader_not_accepted():
    with pytest.raises(TypeError):compare_staged(object(),'repo','a'*40,'b'*40)

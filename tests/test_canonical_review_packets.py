"""Blind-packet tests use authored fixtures only, never independent gold."""
import hashlib
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from scripts.stage_pilot_review_store import stage
from scripts.prepare_canonical_review_packets import prepare
from evaluation.review_intake import ReviewerForm
from evaluation.change_cases import ReviewedChangeCase
from tests.test_pilot_review_store import maps,manifest_fixture


@pytest.fixture
def packet_inputs(maps,tmp_path):
    index,source,m,_=maps;database=tmp_path/'review.db';staging=tmp_path/'staging.json'
    r=stage(index,database);staging.write_text(json.dumps(r));sha=m['commit_id']
    pilot=tmp_path/'pilot';pilot.mkdir();handoff=tmp_path/'handoff';handoff.mkdir()
    case=dict(case_id='fixture',repository='fixture',base_commit=sha,head_commit=sha,
        change_family=None,change_intent=None,consistency_label=None,affected_artifact_ids=None,
        trace_links=None,reviewed_negative_links=None,obligations=[],obligation_inventory='UNKNOWN',
        unknowns=[],evidence=[],reviewer_ids=[],adjudicator_id=None,adjudication_rationale=None,
        semantic_support=None,semantic_reviewer_id=None)
    (pilot/'unlabelled-cases.json').write_text(json.dumps({'split':'pilot','held_out':False,'label_status':'UNLABELLED','cases':[case]}))
    original=dict(case_id='fixture',repository='fixture',origin=m['origin'],base_commit=sha,head_commit=sha,
        changed_files=['tests/test_value.py','missing.py'],patch='Authored fixture patch')
    (pilot/'fixture-packet.json').write_text(json.dumps(original))
    form=dict(reviewer_id=None,independent_of_pipeline_author=None,cases=[dict(case_id='fixture',
        consistency_label=None,trace_links=None,affected_artifact_ids=None,rationale=None,evidence=[])])
    for name in ['reviewer-1.json','reviewer-2.json']:(handoff/name).write_text(json.dumps(form))
    (handoff/'reviewer-schema.json').write_text(json.dumps(ReviewerForm.model_json_schema()))
    (handoff/'adjudication-schema.json').write_text(json.dumps(ReviewedChangeCase.model_json_schema()))
    return database,staging,pilot,handoff,m


def test_canonical_packets_keep_gaps_null_judgments_and_frozen_inputs(packet_inputs,tmp_path):
    database,staging,pilot,handoff,m=packet_inputs
    before={p:p.read_bytes() for p in [database,staging,*pilot.iterdir(),*handoff.iterdir()]}
    output=tmp_path/'packets';summary=prepare(database,staging,pilot,handoff,output)
    packet=json.loads((output/'fixture-packet.json').read_text());assert packet['repository']==m['repository']
    for side in ['base','head']:
        rows=packet['snapshot_sides'][side]['changed_files']
        assert rows[0]['source_reference']['commit_id']==m['commit_id'] and rows[0]['excerpt'].startswith('def test_value')
        assert rows[1]['source_status']=='NOT_IN_PINNED_TREE' and rows[1]['source_reference'] is None
        assert all(r['search_disposition']=='UNKNOWN' for r in rows)
    form=json.loads((output/'reviewer-1.json').read_text())
    assert form['reviewer_id'] is None and form['cases'][0]['consistency_label'] is None
    with pytest.raises(ValidationError):ReviewerForm.model_validate(form)
    case=json.loads((output/'adjudication-template.json').read_text())['cases'][0]
    assert case['repository']==m['repository'] and case['consistency_label'] is None
    with pytest.raises(ValidationError):ReviewedChangeCase.model_validate(case)
    for name,h in summary['files'].items():assert hashlib.sha256((output/name).read_bytes()).hexdigest()==h
    assert all(p.read_bytes()==b for p,b in before.items())
    saved={p:p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):prepare(database,staging,pilot,handoff,output)
    assert all(p.read_bytes()==b for p,b in saved.items())


@pytest.mark.parametrize('mode',['checksum','revision','judgment'])
def test_invalid_or_judgment_contaminated_packets_are_not_published(packet_inputs,tmp_path,mode):
    database,staging,pilot,handoff,m=packet_inputs
    if mode=='checksum':database.write_bytes(database.read_bytes()+b'altered')
    elif mode=='revision':
        p=pilot/'fixture-packet.json';v=json.loads(p.read_text());v['head_commit']='f'*40;p.write_text(json.dumps(v))
    else:
        p=handoff/'reviewer-1.json';v=json.loads(p.read_text());v['cases'][0]['consistency_label']='CONSISTENT';p.write_text(json.dumps(v))
    output=tmp_path/'bad'
    with pytest.raises(ValueError):prepare(database,staging,pilot,handoff,output)
    assert not output.exists()

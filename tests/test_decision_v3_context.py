import json
import pytest
from agents.decision_rules import decide
from ingestion.models import DecisionV3, FactSource, FactsV3, SourcedFact
from llm.context_v3 import request_v3
from llm.providers import LLMProvider
from rag.evidence import evidence
from ingestion.models import artifact

def src(name,revision,role,start=1,end=2):
    return {'evidence_id':name,'artifact_id':'artifact-'+name,'repository':'r','project_id':'p',
        'file':'src/'+name+'.py','path':'src/'+name+'.py','start_line':start,'end_line':end,
        'commit':revision,'commit_id':revision,'revision':revision,'revision_role':role,
        'content_hash':'a'*64,'quote':'one\ntwo','score':1.0,'retrieval_method':'fixture',
        'extraction_method':'fixture-parser'}

def facts():
    src0=FactSource(revision='HEAD',commit_id='h',path='facts.py',start_line=1,end_line=1,content_hash='b'*64,
        extraction_method='parser',artifact_role='implementation',evidence_id='fact-e')
    return FactsV3(evidence_sufficient=SourcedFact(value=True,sources=[src0]))

def test_v3_packet_requires_revision_provenance_and_keeps_base_separate():
    with pytest.raises(ValueError,match='missing revision'):
        request_v3('inspect',[{'evidence_id':'e'}],facts(),head_revision='h')
    rows=[src('base','b','BASE'),src('head','h','HEAD')]
    messages,selected,aliases,_,audit=request_v3('inspect',rows,facts(),head_revision='h')
    payload=json.loads(messages[-1]['content'])
    assert [x['evidence_id'] for x in payload['head_evidence']]==['E1']
    assert [x['evidence_id'] for x in payload['historical_base_evidence']]==['E2']
    assert payload['historical_base_label']=='historical, not current implementation'
    assert selected[0]['revision']=='h' and aliases['E2']['revision']=='b'
    assert audit['base_and_head_deduplicated_separately']

def test_v3_deduplicates_overlaps_only_within_same_revision():
    rows=[src('head-a','h','HEAD',1,3),src('head-b','h','HEAD',2,4),src('base','b','BASE',1,3)]
    rows[1]['path']=rows[1]['file']=rows[0]['path']
    _,selected,_,_,audit=request_v3('inspect',rows,facts(),head_revision='h')
    assert [x['evidence_id'] for x in selected]==['head-a','base']
    assert audit['dropped'][0]['reason']=='overlap-within-same-revision'

def test_v3_packet_caps_at_six_without_cross_revision_dedup():
    rows=[src('h'+str(i),'h','HEAD',i*3+1,i*3+2) for i in range(7)]
    rows += [src('b','b','BASE',1,2)]
    _,selected,_,_,audit=request_v3('inspect',rows,facts(),head_revision='h')
    assert len(selected)==6 and audit['dropped'][-1]['reason']=='six-excerpt-cap'

def test_v3_packet_reserves_two_ranked_retrieval_excerpts_and_keeps_provenance():
    rows=[src("r1","h","HEAD"),src("r2","h","HEAD"),src("r3","h","HEAD")]
    for i,row in enumerate(rows):
        row.update(selection_arm="retrieval",artifact_role="test",score=3-i)
    rows += [src("f"+str(i),"h","HEAD") for i in range(4)]
    messages,selected,_,_,audit=request_v3("inspect",rows,facts(),head_revision="h")
    payload=json.loads(messages[-1]["content"])
    assert audit["retrieval_selected"]==2
    assert len([x for x in selected if x.get("selection_arm")=="retrieval"])==2
    assert any(x["selection_arm"]=="retrieval" and x["artifact_role"]=="test"
               for x in payload["head_evidence"])
    assert any(x["reason"]=="retrieval-candidate-cap" for x in audit["dropped"])


class Stub(LLMProvider):
    name='mock-v3'
    def __init__(self,values):self.values=iter(values);self.calls=0
    def complete(self,messages):
        self.calls+=1
        value=next(self.values)
        return json.dumps(value),{'elapsed_seconds':0.01,'output_tokens':5}

def response(cons='POTENTIAL_INCONSISTENCY',confidence=.95):
    return DecisionV3(consistency=cons,evidence_ids=['E1'],rationale='proposal',
        raw_confidence=confidence).model_dump()

def test_v3_provider_preserves_raw_outputs_and_requires_three_matching_samples():
    engine=Stub([response(),response(),response(),{'supported':True,'reason':'excerpt supports claim'}])
    row=src('head','h','HEAD')
    result=engine.investigate_v3('semantic question',[row],facts(),head_revision='h')
    assert engine.calls==4 and result['vote_agreement'] is True
    assert result['decision']['consistency']=='POTENTIAL_INCONSISTENCY'
    assert result['raw_confidences']==[.95,.95,.95]
    assert len(result['raw_outputs'])==3 and result['semantic_entailment']=='MODEL_CHECKED_NOT_INDEPENDENT'
    assert result['head_citations']==['head']
    assert result['unsupported_claim_rate_model_judged']==0.0

def test_v3_provider_abstains_when_samples_disagree():
    engine=Stub([response('INCONSISTENT'),response('POTENTIAL_INCONSISTENCY'),response('INCONSISTENT')])
    result=engine.investigate_v3('semantic question',[src('head','h','HEAD')],facts(),head_revision='h')
    assert engine.calls==3
    assert result['vote_agreement'] is False
    assert result['decision']['consistency']=='UNCERTAIN'
    assert 'samples or citation checks' in result['decision']['rationale']

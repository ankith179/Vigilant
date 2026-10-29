"""Evaluator contract fixtures, deliberately not research evaluation data."""
import copy
import pytest
from evaluation.assurance_gate import evaluate


@pytest.fixture
def reviewed_fixture():
    pipeline='a'*64;dataset_hash='b'*64
    protocol={'protocol':'vigilant-assurance-95-v2','status':'FROZEN','target':.95,'minimum_test_cases':200,
              'frozen_pipeline_sha256':pipeline,'frozen_dataset_sha256':dataset_hash,'operational_checks_passed':True}
    cases=[{'case_id':str(i),'repository':'unseen','change_family':'held','base_commit':'c'*40,'head_commit':'d'*40,
            'reviewer_ids':['reviewer-one','reviewer-two'],'adjudicated':True,
            'consistency_label':'CONSISTENT' if i%2 else 'INCONSISTENT','trace_links':['requirement->code'],
            'impact_artifacts':['code']} for i in range(200)]
    predictions=[{'case_id':c['case_id'],'repository':c['repository'],'base_commit':c['base_commit'],'head_commit':c['head_commit'],
                  'consistency_label':c['consistency_label'],'trace_links':c['trace_links'],'impact_artifacts':c['impact_artifacts'],
                  'pipeline_sha256':pipeline,'valid_response':True,'semantic_citations_reviewed':True,'semantic_reviewer_id':'reviewer-three'} for c in cases]
    return {'cases':cases,'split':'test','authored_diagnostics':False,'frozen_sha256':dataset_hash},predictions,protocol


def test_95_protocol_separate_tasks_and_missing_denominator(reviewed_fixture):
    data,pred,protocol=reviewed_fixture
    result=evaluate(data,pred,protocol)
    assert result['status']=='OBSERVED_TARGET_MET' and not result['population_target_claim_supported']
    pred=pred[:180]
    result=evaluate(data,pred,protocol)
    assert result['status']=='TARGET_NOT_MET'
    assert result['impact']['recall']==.9 and result['consistency']['accuracy']==.9
    assert result['consistency']['invalid_responses']==20 and result['impact']['invalid_or_missing']==20


def test_95_refuses_stale_predictions_and_incomplete_labels(reviewed_fixture):
    data,pred,protocol=reviewed_fixture
    pred[0]['head_commit']='e'*40
    result=evaluate(data,pred,protocol)
    assert result['consistency']['invalid_responses']==1 and result['impact']['invalid_or_missing']==1
    assert result['checks']['all_predictions_source_bound'] is False
    del data['cases'][0]['impact_artifacts']
    assert evaluate(data,pred,protocol)['status']=='NOT_EVALUATED'


def test_95_rejects_false_review_string_and_foreign_pipeline(reviewed_fixture):
    data,pred,protocol=reviewed_fixture
    data['cases'][0]['adjudicated']='false'
    assert evaluate(data,pred,protocol)['status']=='NOT_EVALUATED'
    data['cases'][0]['adjudicated']=True
    pred[0]['pipeline_sha256']='f'*64
    assert evaluate(data,pred,protocol)['consistency']['invalid_responses']==1


def test_95_refuses_unfrozen_and_wrong_dataset_hash(reviewed_fixture):
    data,pred,protocol=reviewed_fixture
    protocol['frozen_dataset_sha256']='e'*64
    assert evaluate(data,pred,protocol)['status']=='NOT_EVALUATED'
    protocol['status']='DRAFT_NOT_FROZEN'
    assert evaluate(data,pred,protocol)['status']=='NOT_EVALUATED'

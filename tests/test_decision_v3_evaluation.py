import pytest
from evaluation.decision_v3 import evaluate, mcnemar_exact, score_axis
from evaluation.case_validation import validate_case

def test_axis_scoring_counts_abstentions_as_incorrect_and_reports_coverage():
    rows=[{'case_id':'a','truth':{'consistency':'CONSISTENT'},'predictions':{'rules':{'consistency':'UNCERTAIN','format_valid':True}}},
          {'case_id':'b','truth':{'consistency':'INCONSISTENT'},'predictions':{'rules':{'consistency':'INCONSISTENT','format_valid':False}}}]
    m=score_axis(rows,'consistency','rules')
    assert m['n_labeled']==2 and m['correct_including_abstentions']==1
    assert m['decisive_coverage']==0.5 and m['selective_risk']==0.0
    assert m['majority_baseline']==0.5 and m['wilson_95'] is not None

def test_authority_missing_invalid_and_reviewed_uncertainty_are_counted():
    rows=[{'truth':{'authority':'NORMATIVE'},'predictions':{'rules':{}}},
          {'truth':{'authority':'INFORMATIONAL'},'predictions':{'rules':{'authority':'BAD'}}},
          {'truth':{'authority':'NOT_ESTABLISHED'},'predictions':{'rules':{'authority':'NOT_ESTABLISHED'}}}]
    m=score_axis(rows,'authority','rules')
    assert m['n_labeled']==3 and m['correct_including_abstentions']==1
    assert m['confusion_matrix']['NORMATIVE']['<MISSING>']==1
    assert m['confusion_matrix']['INFORMATIONAL']['<INVALID>']==1
    assert m['confusion_matrix']['NOT_ESTABLISHED']['NOT_ESTABLISHED']==1
    assert m['decisive_coverage']==0 and m['selective_risk'] is None

def test_missing_and_uncertain_consistency_remain_in_denominator():
    rows=[{'truth':{'consistency':'CONSISTENT'},'predictions':{}},
          {'truth':{'consistency':'UNCERTAIN'},'predictions':{'rules':{'consistency':'UNCERTAIN'}}}]
    m=score_axis(rows,'consistency','rules')
    assert m['accuracy_all_labeled']==0.5
    assert m['confusion_matrix']['CONSISTENT']['<MISSING>']==1
    assert m['confusion_matrix']['UNCERTAIN']['UNCERTAIN']==1

def test_paired_exact_mcnemar_reports_discordant_counts():
    assert mcnemar_exact(1,1)==1.0
    result=evaluate({'schema_version':1,'cohort':'authored','split':'development','cases':[
      {'case_id':'a','truth':{'trace':'LINKED','consistency':'CONSISTENT','test_obligation':'SATISFIED'},
       'predictions':{'a':{'trace':'LINKED','consistency':'CONSISTENT','test_obligation':'SATISFIED'},
                      'b':{'trace':'UNCERTAIN','consistency':'CONSISTENT','test_obligation':'SATISFIED'}}}]})
    assert result['conditions']['a']['axes']['trace']['accuracy_all_labeled']==1.0
    paired=result['paired_comparisons']['a_vs_b']['per_axis']
    assert paired['trace']['n']==1 and paired['trace']['a_correct_b_wrong']==1
    assert paired['authority']['n']==0 and paired['authority']['mcnemar_exact_two_sided'] is None

def test_paired_axes_count_missing_as_wrong_and_matching_uncertainty_as_correct():
    cases=[{'case_id':'1','truth':{'consistency':'CONSISTENT'},'predictions':{'a':{},'b':{'consistency':'CONSISTENT'}}},
           {'case_id':'2','truth':{'consistency':'UNCERTAIN'},'predictions':{'a':{'consistency':'UNCERTAIN'},'b':{'consistency':'CONSISTENT'}}}]
    paired=evaluate({'cases':cases})['paired_comparisons']['a_vs_b']['per_axis']['consistency']
    assert paired['n']==2 and paired['a_correct_b_wrong']==1 and paired['a_wrong_b_correct']==1
    assert paired['mcnemar_exact_two_sided']==1.0

def test_case_template_validator_rejects_invalid_hash_and_axis():
    case={'case_id':'x','repository_id':'r','base_revision':'b','head_revision':'h',
      'artifact_hashes':['not-hash'],'evidence_packet':'e',
      'labels':{'trace':'LINKED','consistency':'PASS','test_obligation':None},
      'review':{'reviewer_id':None,'rationale':None,'timestamp':None},
      'adjudication_status':'PENDING','split':'development'}
    errors=validate_case(case)
    assert any('SHA-256' in e for e in errors) and any('consistency' in e for e in errors)

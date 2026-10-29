import copy
import unittest
from tools.coverage_report import summarize

CARD = {'case_id':'id1', 'd_ids':['D01','D14'], 'priority_tier':'P1', 'origin':'MINED',
        'source_id':'source', 'family':'family', 'split':'dev', 'history_source':'A',
        'base_revision':'base', 'head_revision':'head',
        'artifacts':{'requirement':[], 'code':[{'path':'a.py','revision':'base','content_hash':'a'*64}], 'test':[]},
        'change_facts':{}, 'requirement_source':None, 'expected_trace':None, 'expected_consistency':None,
        'expected_test_obligation':None, 'expected_authority':None, 'impact_ground_truth':None,
        'supporting_evidence_ids':[], 'adjudication':{'status':'PENDING','reviewer_ids':[],'rationale':None},
        'notes':'', 'label_status':'UNREVIEWED_SILVER'}

class CoverageTests(unittest.TestCase):
    def test_missing_split_and_source_share(self):
        result = summarize([CARD], [{'id':'workspace','history_source':'NO_HISTORY'}])
        self.assertEqual(result['d_id_counts']['D1'], 1)
        self.assertEqual(len(result['missing_by_split']['test']), 36)
        self.assertIn('D13', result['curated_only_missing'])
        self.assertEqual(result['source_over_25_percent']['dev']['source'], 1)
        self.assertEqual(result['no_history_sources'], ['workspace'])
        self.assertEqual(result['adjudicated_axis_labels']['consistency'], {})

    def test_duplicate_rejected_and_review_counts(self):
        with self.assertRaises(ValueError):
            summarize([CARD, CARD], [])
        reviewed = copy.deepcopy(CARD)
        reviewed['expected_consistency'] = 'UNCERTAIN'
        reviewed['adjudication'] = {'status':'ADJUDICATED','reviewer_ids':['r1'], 'rationale':'reviewed'}
        reviewed['label_status'] = 'ADJUDICATED'
        self.assertEqual(summarize([reviewed], [])['adjudicated_axis_labels']['consistency'], {'UNCERTAIN':1})

if __name__ == '__main__':
    unittest.main()

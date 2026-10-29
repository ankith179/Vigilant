import copy
import unittest
from tools.blind_review import FIELDS, prepare

CARD = {'case_id':'id1', 'd_ids':['D14'], 'priority_tier':'P1', 'origin':'MINED',
        'source_id':'source', 'family':'family', 'split':'dev', 'history_source':'A',
        'base_revision':'a'*40, 'head_revision':'b'*40,
        'artifacts':{'requirement':[], 'code':[{'path':'a.py','revision':'a'*40,'content_hash':'c'*64}], 'test':[]},
        'change_facts':{'path':'a.py', 'symbol':'function', 'candidate_category':'SECRET_HINT'},
        'requirement_source':None, 'expected_trace':None, 'expected_consistency':None,
        'expected_test_obligation':None, 'expected_authority':None, 'impact_ground_truth':None,
        'supporting_evidence_ids':[], 'adjudication':{'status':'PENDING','reviewer_ids':[],'rationale':None},
        'notes':'do not expose notes', 'label_status':'UNREVIEWED_SILVER'}

class ReviewTests(unittest.TestCase):
    def test_blinded_and_deterministic(self):
        rows = prepare([CARD], {'source':'data/repos/source'})
        self.assertEqual(rows, prepare([CARD], {'source':'data/repos/source'}))
        self.assertEqual(tuple(rows[0]), FIELDS)
        self.assertNotIn('SECRET_HINT', str(rows))
        self.assertNotIn('D14', str(rows))
        self.assertEqual(rows[0]['reviewer_consistency'], '')
        self.assertEqual(rows[0]['reviewer_id'], '')
        self.assertEqual(rows[0]['reviewed_at_utc'], '')
        self.assertEqual(rows[0]['reviewer_rationale'], '')
        self.assertEqual(rows[0]['uncertainty_reason'], '')
        self.assertEqual(rows[0]['adjudication_status'], 'PENDING')

    def test_rejects_duplicate_and_unsafe_content(self):
        with self.assertRaises(ValueError):
            prepare([CARD, CARD], {'source':'data/repos/source'})
        bad = copy.deepcopy(CARD)
        bad['change_facts']['path'] = '=formula'
        with self.assertRaises(ValueError):
            prepare([bad], {'source':'data/repos/source'})

if __name__ == '__main__':
    unittest.main()

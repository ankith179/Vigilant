import copy
import unittest
from tools.candidates_to_cards import convert

ROW = {'case_id':'case1', 'd_ids':['D14'], 'origin':'MINED', 'label_status':'UNREVIEWED_SILVER',
       'repository_id':'repo', 'family':'family', 'split':'dev', 'base_revision':'base', 'head_revision':'head',
       'path':'src/a.py', 'symbol':'f', 'candidate_category':'CODE_CHANGED_DOC_UNCHANGED',
       'facts':{'evidence':[{'presence':'PRESENT','path':'src/a.py','revision':'BASE','content_hash':'a'*64},
                            {'presence':'PRESENT','path':'src/a.py','revision':'HEAD','content_hash':'b'*64}]}}

class CandidateCardTests(unittest.TestCase):
    def test_revision_and_label_integrity(self):
        card = convert(ROW)
        self.assertEqual([x['revision'] for x in card['artifacts']['code']], ['base', 'head'])
        self.assertEqual(card['priority_tier'], 'P1')
        self.assertIsNone(card['expected_consistency'])
        self.assertEqual(card['label_status'], 'UNREVIEWED_SILVER')

    def test_rejects_labels_missing_priority_and_bad_hash(self):
        for change in (lambda x:x.update(expected_trace='LINKED'), lambda x:x.update(d_ids=[]),
                       lambda x:x['facts']['evidence'][0].update(content_hash='invalid')):
            row = copy.deepcopy(ROW)
            change(row)
            with self.assertRaises(ValueError):
                convert(row)



    def test_accepts_exact_revision_hash_and_rejects_unbound_revision(self):
        row = copy.deepcopy(ROW)
        row['base_revision'], row['head_revision'] = 'a' * 40, 'b' * 40
        row['facts']['evidence'][0]['revision'] = row['base_revision']
        row['facts']['evidence'][1]['revision'] = row['head_revision']
        card = convert(row)
        self.assertEqual([x['revision'] for x in card['artifacts']['code']], ['a' * 40, 'b' * 40])

        row['facts']['evidence'][1]['revision'] = 'c' * 40
        with self.assertRaises(ValueError):
            convert(row)

if __name__ == '__main__':
    unittest.main()

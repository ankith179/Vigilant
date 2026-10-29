import copy
import unittest
from tools.agreement import agreement

def row(cid, label):
    return {'case_id':cid, 'source_id':'repo', 'base':'a', 'head':'b', 'path':'x.py', 'symbol':'f',
            'diff_command':'git diff', 'reviewer_trace':'', 'reviewer_consistency':label,
            'reviewer_test_obligation':'', 'reviewer_authority':''}

class AgreementTests(unittest.TestCase):
    def test_hand_computed_kappa_and_missing_axes(self):
        left = {str(i):row(str(i), v) for i, v in enumerate(['CONSISTENT','CONSISTENT','INCONSISTENT','INCONSISTENT'])}
        right = copy.deepcopy(left)
        right['3']['reviewer_consistency'] = 'CONSISTENT'
        result = agreement(left, right, 'inter-rater')['axes']
        self.assertEqual(result['consistency']['agreement'], .75)
        self.assertEqual(result['consistency']['cohen_kappa'], .5)
        self.assertEqual(result['consistency']['disagreements'], ['3'])
        self.assertEqual(result['trace']['incomplete'], 4)
        self.assertIsNone(result['trace']['cohen_kappa'])

    def test_degenerate_and_mismatched_cases(self):
        left = {'1': row('1', 'UNCERTAIN')}
        self.assertIsNone(agreement(left, copy.deepcopy(left), 'intra-rater')['axes']['consistency']['cohen_kappa'])
        right = copy.deepcopy(left)
        right['1']['head'] = 'different'
        with self.assertRaises(ValueError):
            agreement(left, right, 'inter-rater')

if __name__ == '__main__':
    unittest.main()

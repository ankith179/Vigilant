import hashlib
import unittest
from math import isclose
from scripts.analyze_test_evolution_misses import analyze


def check_loss_accounting():
    tasks = [{'case_id': str(i), 'project': 'p', 'base_commit': 'b', 'repository': 'r', 'source_patch': 's'} for i in range(4)]
    gold = [{'case_id': str(i), 'developer_changed_test_files': ['a.java', 'b.java', 'c.bin']} for i in range(4)]
    base = {'status': 'RANKED', 'base_commit': 'b', 'repository': 'r',
            'query_sha256': hashlib.sha256(b's').hexdigest(), 'candidate_files': ['x.java', 'a.java', 'b.java']}
    rows = [{**base, 'case_id': '0', 'rankings': {'rank_rrf': ['x.java', 'a.java', 'b.java']}},
            {**base, 'case_id': '1', 'rankings': {'rank_rrf': ['a.java', 'a.java', 'b.java']}},
            {**base, 'case_id': '2', 'base_commit': 'wrong', 'rankings': {'rank_rrf': ['a.java', 'b.java', 'x.java']}}]
    r = analyze(tasks, gold, rows, k=1)
    assert r['overall']['cases'] == 4 and r['overall']['invalid_or_missing'] == 3
    assert r['overall']['mean_recall'] == 0
    assert isclose(sum(r['overall']['mean_loss'].values()), 1)
    assert r['cases'][0]['losses'] == {'invalid_or_missing': 0, 'outside_inventory': 1/3, 'top_k_capacity': 1/3, 'ranking': 1/3}
    assert r['cases'][0]['outside_inventory'][0]['scope'] == 'NON_JAVA_EXCLUDED_BY_CANDIDATE_RULE'
    with unittest.TestCase().assertRaisesRegex(ValueError, 'Duplicate'):
        analyze(tasks, gold, rows + [rows[0]])
    with unittest.TestCase().assertRaisesRegex(ValueError, 'Unexpected'):
        analyze(tasks, gold, rows + [{**base, 'case_id': 'foreign'}])


class MissAccountingTest(unittest.TestCase):
    def test_denominators(self):
        check_loss_accounting()


if __name__ == '__main__':
    unittest.main()

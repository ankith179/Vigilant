"""Recompute test-file recall and verify recorded input/split provenance offline."""
from pathlib import Path
import argparse
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def audit(rows, truth, saved):
    by = {r['case_id']: r for r in rows}
    assert len(by) == len(rows) and set(by) == set(truth), 'Prediction case set differs'
    summaries = {}
    for method, measured in saved.items():
        sums = {k: 0.0 for k in (1, 5, 10)}; invalid = 0
        for cid, relevant in truth.items():
            row = by[cid]; candidates = row.get('candidate_files', [])
            order = row.get('rankings', {}).get(method, [])
            valid = (row['status'] == 'RANKED' and bool(candidates) and len(set(candidates)) == len(candidates)
                     and len(set(order)) == len(order) and set(order) == set(candidates))
            invalid += not valid
            if not valid:
                order = []
            for k in sums:
                sums[k] += sum(file in relevant for file in order[:k]) / len(relevant)
        assert measured['cases'] == len(truth) and measured['invalid_or_missing'] == invalid
        values = {f'mean_recall_at_{k}': value / len(truth) for k, value in sums.items()}
        for key, value in values.items():
            assert math.isclose(measured[key], value, rel_tol=1e-12, abs_tol=1e-12), (method, key)
        summaries[method] = {**values, 'cases': len(truth), 'invalid_or_missing': invalid}
    return summaries


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--policy', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    inputs = json.loads((ROOT / 'data/test-evolution/TEBench/inputs.json').read_text())
    gold = json.loads((ROOT / 'data/test-evolution/TEBench/gold.json').read_text())
    tasks = {r['case_id']: r for r in inputs}
    truth = {r['case_id']: set(r['developer_changed_test_files']) for r in gold}
    assert len(tasks) == len(inputs) == len(gold) == len(truth) == 314
    assert set(tasks) == set(truth) and all(truth.values())
    assert all(set(t) == {'case_id', 'project', 'repository', 'base_commit', 'source_patch', 'non_test_paths'} for t in inputs)
    rows = json.loads((a.baseline / 'predictions.json').read_text())
    report = json.loads((a.baseline / 'results.json').read_text())
    for row in rows:
        if row['status'] != 'RANKED':
            continue
        task = tasks[row['case_id']]
        assert row['repository'] == task['repository'] and row['base_commit'] == task['base_commit']
        assert row['query_sha256'] == hashlib.sha256(task['source_patch'][:128_000].encode()).hexdigest()
    result = {'status': 'PASS', 'baseline': audit(rows, truth, report['methods']),
              'provenance': '314 case identities, base revisions, source-only input fields, query hashes and score arithmetic',
              'quality_target_91': 'NOT_EVALUATED', 'new_llm_calls': 0,
              'limitations': 'Arithmetic and recorded provenance only; no independent semantic correctness or complete behavioral-impact review'}
    if a.policy:
        policy = json.loads((a.policy / 'results.json').read_text())
        selected = json.loads((a.policy / 'predictions.json').read_text())
        trace = json.loads((a.policy / 'training-trace.json').read_text())
        train_projects = set(policy['training_projects'])
        held_projects = set(policy['held_development_projects'])
        assert not train_projects & held_projects
        train_ids = {cid for cid, t in tasks.items() if t['project'] in train_projects}
        held_ids = {cid for cid, t in tasks.items() if t['project'] in held_projects}
        assert train_ids | held_ids == set(tasks) and not train_ids & held_ids
        assert all(r['case_id'] in train_ids for r in trace) and len(trace) == len(train_ids) * 3
        expected_hash = hashlib.sha256(json.dumps(policy['policy'], sort_keys=True).encode()).hexdigest()
        assert expected_hash == policy['frozen_policy_sha256']
        old = {r['case_id']: r for r in rows}
        assert {r['case_id'] for r in selected} == held_ids
        for row in selected:
            assert row['rankings']['bandit'] == old[row['case_id']].get('rankings', {}).get(row['chosen_arm'], [])
        held_truth = {cid: truth[cid] for cid in held_ids}
        result['policy'] = audit(selected, held_truth, {'bandit': policy['methods']['bandit']})
        result['training_events_checked'] = len(trace)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

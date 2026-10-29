"""Offline loss decomposition on exposed development rankings; never a gold oracle."""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def analyze(tasks, gold, predictions, method='rank_rrf', k=10):
    if k < 1:
        raise ValueError('k must be positive')
    def unique(rows):
        result = {r['case_id']: r for r in rows}
        if len(result) != len(rows):
            raise ValueError('Duplicate case identity')
        return result
    tasks, gold, predictions = map(unique, (tasks, gold, predictions))
    if set(tasks) != set(gold) or set(predictions) - set(tasks):
        raise ValueError('Unexpected case identities')
    details = []
    for cid, task in sorted(tasks.items()):
        relevant = set(gold[cid]['developer_changed_test_files'])
        if not relevant:
            raise ValueError('Empty reference set')
        row = predictions.get(cid, {})
        candidates = row.get('candidate_files', [])
        order = row.get('rankings', {}).get(method, [])
        valid = (row.get('status') == 'RANKED' and bool(candidates)
                 and len(set(candidates)) == len(candidates)
                 and len(set(order)) == len(order) and set(order) == set(candidates)
                 and row.get('base_commit') == task['base_commit']
                 and row.get('repository') == task['repository']
                 and row.get('query_sha256') == hashlib.sha256(task['source_patch'][:128_000].encode()).hexdigest())
        n = len(relevant)
        outside = relevant - set(candidates) if valid else set()
        present = n - len(outside) if valid else 0
        hits = len(relevant & set(order[:k])) if valid else 0
        capacity = min(k, present)
        # Four disjoint losses sum to 1-recall. Invalid rows receive no inferred coverage.
        losses = {'invalid_or_missing': float(not valid),
                  'outside_inventory': len(outside) / n,
                  'top_k_capacity': (present - capacity) / n,
                  'ranking': (capacity - hits) / n}
        recall = hits / n
        if not math.isclose(recall + sum(losses.values()), 1.0, abs_tol=1e-12):
            raise ValueError('Loss decomposition does not reconcile')
        details.append({'case_id': cid, 'project': task['project'], 'valid': valid,
                        'references': n, 'hits': hits, 'recall': recall, 'losses': losses,
                        'inventory_ceiling': present / n, 'top_k_oracle_ceiling': capacity / n,
                        'outside_inventory': [{'path': p, 'scope': 'JAVA_ABSENCE_UNRESOLVED' if p.endswith('.java')
                                               else 'NON_JAVA_EXCLUDED_BY_CANDIDATE_RULE'} for p in sorted(outside)]})
    groups = defaultdict(list)
    for row in details:
        groups[row['project']].append(row)
    def summary(rows):
        n = len(rows)
        return {'cases': n, 'invalid_or_missing': sum(not r['valid'] for r in rows),
                'reference_files': sum(r['references'] for r in rows),
                'mean_recall': sum(r['recall'] for r in rows) / n,
                'mean_inventory_ceiling': sum(r['inventory_ceiling'] for r in rows) / n,
                'mean_top_k_oracle_ceiling': sum(r['top_k_oracle_ceiling'] for r in rows) / n,
                'mean_loss': {key: sum(r['losses'][key] for r in rows) / n for key in details[0]['losses']},
                'outside_inventory_counts': dict(Counter(p['scope'] for r in rows for p in r['outside_inventory']))}
    if not details:
        raise ValueError('No cases')
    return {'scope': 'EXPOSED_DEVELOPMENT_TEST_FILE_RETRIEVAL', 'method': method, 'k': k,
            'overall': summary(details), 'projects': {p: summary(rows) for p, rows in sorted(groups.items())},
            'cases': details, 'quality_target_91': 'NOT_EVALUATED', 'new_llm_calls': 0,
            'limitations': ['Oracle ceilings are descriptive uses of exposed references, never predictions.',
                           'Absent Java references require pinned base-tree review; absence does not prove a new file.',
                           'Non-Java exclusions describe the candidate rule, not whether a file exists at base.',
                           'Unchanged or unlinked files have no inferred negative labels.',
                           'No independent traceability, impact, consistency or semantic-support labels created.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    files = {'inputs': ROOT / 'data/test-evolution/TEBench/inputs.json',
             'gold': ROOT / 'data/test-evolution/TEBench/gold.json',
             'predictions': a.baseline / 'predictions.json',
             'source': ROOT / 'data/test-evolution/TEBench/source.json'}
    data = {key: json.loads(path.read_text(encoding='utf-8')) for key, path in files.items()}
    result = analyze(data['inputs'], data['gold'], data['predictions'])
    result['input_sha256'] = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in files.items()}
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['benchmark_provenance'] = data['source']
    a.output.parent.mkdir(parents=True, exist_ok=True)
    pending = a.output.with_suffix('.pending')
    pending.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    pending.replace(a.output)
    print(json.dumps(result['overall'], indent=2))


if __name__ == '__main__':
    main()

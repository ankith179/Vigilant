"""Independently recompute saved retrieval metrics without rerunning models."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[1]


def recompute(data, ranks):
    truth = {}
    for query, target in data['links']:
        truth.setdefault(query, set()).add(target)
    universe = {target['id'] for target in data['targets']}
    rows = []
    total_hits = total_predictions = total_links = 0
    for query, relevant in sorted(truth.items()):
        order = ranks[query]
        assert len(order) == len(set(order)), (query, 'duplicate ranking')
        assert set(order) == universe, (query, 'incomplete target ranking')
        assert relevant <= universe, (query, 'unresolved gold target')
        hits = [position for position, target in enumerate(order, 1) if target in relevant]
        top_hits = sum(position <= 10 for position in hits)
        total_hits += top_hits
        total_predictions += min(10, len(order))
        total_links += len(relevant)
        ideal = sum(1 / math.log2(position + 1) for position in range(1, min(10, len(relevant)) + 1))
        row = {
            'query': query,
            'map': sum(number / position for number, position in enumerate(hits, 1)) / len(relevant),
            'mrr': 1 / hits[0] if hits else 0,
            'ndcg_at_10': sum(1 / math.log2(position + 1) for position in hits if position <= 10) / ideal,
        }
        row.update({f'recall_at_{k}': sum(position <= k for position in hits) / len(relevant) for k in (1, 5, 10)})
        rows.append(row)
    precision = total_hits / total_predictions if total_predictions else 0
    recall = total_hits / total_links if total_links else 0
    summary = {'precision': precision, 'recall': recall,
               'f1': 2 * precision * recall / (precision + recall) if precision + recall else 0,
               'tp': total_hits, 'fp': total_predictions - total_hits, 'fn': total_links - total_hits,
               'queries': len(rows), 'decision_cutoff': 10}
    for metric in ('map', 'mrr', 'ndcg_at_10', 'recall_at_1', 'recall_at_5', 'recall_at_10'):
        summary[metric] = statistics.mean(row[metric] for row in rows) if rows else 0
    return summary, rows


def audit():
    verified = []
    for path in sorted((ROOT / 'experiments/retrieval').glob('*/results.json')):
        run = json.loads(path.read_text())
        for result in run['results']:
            dataset = result['dataset']
            data_path = ROOT / 'data/prepared' / (dataset + '.json')
            data = json.loads(data_path.read_text())
            assert result['commit'] == data['commit'], (path, 'dataset commit differs')
            calculated, rows = recompute(data, result['rankings'])
            for key, value in calculated.items():
                assert math.isclose(value, result['metrics'][key], rel_tol=1e-10, abs_tol=1e-12), (path, dataset, key)
            saved_rows = {row['query']: row for row in result['per_query']}
            assert set(saved_rows) == {row['query'] for row in rows}
            for row in rows:
                for key, value in row.items():
                    if key != 'query':
                        assert math.isclose(value, saved_rows[row['query']][key], rel_tol=1e-10, abs_tol=1e-12), (path, row['query'], key)
            if result['method'] == 'hybrid_rag_top5':
                calls = result['calls']
                assert len(calls) == len(rows)
                assert {row['query_id'] for row in calls} == set(saved_rows)
                assert all(row['inference_executed'] and row['raw_output'] and row['usage']['output_tokens'] > 0 for row in calls)
                assert all(row['dataset_fingerprint'] == result['dataset_fingerprint'] for row in calls)
                baseline_path = ROOT / 'experiments/retrieval/20261006T021326-432d54b3/results.json'
                baseline = next(r for r in json.loads(baseline_path.read_text())['results']
                                if r['dataset'] == dataset and r['method'] == 'hybrid')
                baseline_metrics, baseline_rows = recompute(data, baseline['rankings'])
                for key, value in baseline_metrics.items():
                    assert math.isclose(value, result['baseline_metrics'][key], rel_tol=1e-10, abs_tol=1e-12), (path, 'baseline', key)
                baseline_queries = {r['query']: r for r in baseline_rows}
                changed = 0
                statuses = {}
                for call in calls:
                    query = call['query_id']
                    order = baseline['rankings'][query]
                    aliases = {f'A{i + 1}': target for i, target in enumerate(order[:5])}
                    assert call['aliases'] == aliases, (path, query, 'candidate aliases')
                    supported = [target for alias, target in aliases.items()
                                 if call['decision']['statuses'][alias] == 'SUPPORTED']
                    expected = supported + [target for target in order if target not in supported]
                    assert result['rankings'][query] == expected, (path, query, 'reranking policy')
                    changed += expected != order
                    for status in call['decision']['statuses'].values():
                        statuses[status] = statuses.get(status, 0) + 1
                    for metric in ('recall_at_5', 'recall_at_10'):
                        assert saved_rows[query][metric] == baseline_queries[query][metric], (path, query, 'top-five recall invariant')
                assert result['changed_query_rankings'] == changed
                assert result['candidate_status_counts'] == statuses
                assert result['schema_valid_rate'] == sum(c['validation_error'] is None for c in calls) / len(calls)
            verified.append({'run': str(path.relative_to(ROOT)), 'run_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                             'prepared_sha256': hashlib.sha256(data_path.read_bytes()).hexdigest(),
                             'dataset': dataset, 'method': result['method'], 'metrics': calculated,
                             'linked_queries_checked': len(rows)})
    return {'status': 'PASS', 'method_rows_verified': len(verified),
            'per_query_metric_rows_verified': sum(row['linked_queries_checked'] for row in verified),
            'verification': 'Independent Python formulas over immutable saved rankings; no inference rerun.',
            'scope': 'Arithmetic, complete target rankings, dataset commit, per-query values, actual RAG generation records, paired baseline metrics and frozen reranking policy. Does not independently validate gold labels or semantic entailment.',
            'rows': verified}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='reports/verification/metrics-audit.json')
    args = parser.parse_args()
    report = audit()
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'method_rows_verified', 'per_query_metric_rows_verified')}))


if __name__ == '__main__':
    main()

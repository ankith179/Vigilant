"""Retry failed infrastructure rows once without rewriting the original run."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.test_evolution import ROOT, TEST_CANDIDATE_POLICY, ranks, save, score, sha


def merge_predictions(original, recovered):
    original_ids = [row.get('case_id') for row in original]
    recovered_ids = [row.get('case_id') for row in recovered]
    if len(set(original_ids)) != len(original_ids) or len(set(recovered_ids)) != len(recovered_ids):
        raise ValueError('Duplicate case identity')
    by_id = {row['case_id']: row for row in recovered}
    if not set(by_id) <= set(original_ids):
        raise ValueError('Recovery contains a foreign case')
    merged = []
    for row in original:
        retry = by_id.get(row['case_id'])
        if retry and retry.get('status') == 'RANKED':
            if retry.get('candidate_policy') != TEST_CANDIDATE_POLICY:
                raise ValueError('Recovered candidate policy mismatch')
            merged.append(retry)
        else:
            merged.append(row)
    return merged


def recover(baseline, dataset, output):
    if output.exists():
        raise ValueError('Preserve existing recovery output; choose a new path')
    baseline = Path(baseline)
    dataset = Path(dataset)
    original = json.loads((baseline / 'predictions.json').read_text(encoding='utf-8'))
    fingerprint = json.loads((baseline / 'fingerprint.json').read_text(encoding='utf-8'))
    if fingerprint.get('candidate_policy') != TEST_CANDIDATE_POLICY:
        raise ValueError('Baseline candidate policy mismatch')
    inputs = json.loads((dataset / 'inputs.json').read_text(encoding='utf-8'))
    gold = json.loads((dataset / 'gold.json').read_text(encoding='utf-8'))
    tasks = {row['case_id']: row for row in inputs}
    failures = [row for row in original if row.get('status') != 'RANKED']
    if not failures or set(tasks) != {row['case_id'] for row in original}:
        raise ValueError('Expected failed rows and a complete matching input set')
    recovered = []
    for row in failures:
        try:
            attempt = ranks(tasks[row['case_id']], ROOT / '.runtime/tebench')
        except Exception as exc:
            attempt = {'case_id': row['case_id'], 'status': 'FAILED', 'error': str(exc)[:1000]}
        recovered.append(attempt)
    merged = merge_predictions(original, recovered)
    output = Path(output)
    output.mkdir(parents=True)
    save(output / 'initial-failures.json', failures)
    save(output / 'recovery-attempts.json', recovered)
    save(output / 'predictions.json', merged)
    result = {
        'status': 'COMPLETED_DEVELOPMENT_INFRASTRUCTURE_RECOVERY',
        'candidate_policy': TEST_CANDIDATE_POLICY,
        'baseline': str(baseline),
        'baseline_predictions_sha256': sha(baseline / 'predictions.json'),
        'inputs_sha256': sha(dataset / 'inputs.json'),
        'initial_failures': len(failures),
        'recovered_cases': sum(row.get('status') == 'RANKED' for row in recovered),
        'remaining_failures': sum(row.get('status') != 'RANKED' for row in recovered),
        'methods': {method: score(gold, merged, method) for method in ('tfidf', 'bm25', 'rank_rrf')},
        'new_llm_calls': 0,
        'limitations': [
            'Each failed infrastructure row received one retry; original failures remain in the baseline and this report.',
            'Results are exposed development test-file retrieval only, not traceability, consistency or independent performance.',
        ],
    }
    save(output / 'results.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/test-evolution/TEBench')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = recover(args.baseline, args.dataset, args.output)
    print(json.dumps({key: value for key, value in result.items() if key != 'methods'}, indent=2))
    print(json.dumps({method: {key: value for key, value in metrics.items() if key != 'case_metrics'}
                      for method, metrics in result['methods'].items()}, indent=2))


if __name__ == '__main__':
    main()

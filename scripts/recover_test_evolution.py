"""Recover recorded infrastructure failures without rewriting the original run."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.test_evolution import ARMS, ranks, save, score, sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path, default=ROOT / '.runtime/tebench-recovery')
    p.add_argument('--resume', action='store_true')
    a = p.parse_args()
    source = a.baseline / 'predictions.json'
    originals = json.loads(source.read_text())
    inputs = json.loads((ROOT / 'data/test-evolution/TEBench/inputs.json').read_text())
    by = {r['case_id']: r for r in originals}
    if len(by) != len(originals) or set(by) != {r['case_id'] for r in inputs}:
        raise ValueError('Baseline is incomplete or has duplicate cases')
    if a.output.exists() and not a.resume:
        p.error('Preserve existing recovery output or use matching --resume')
    a.output.mkdir(parents=True, exist_ok=a.resume)
    fingerprint = {'baseline_predictions_sha256': sha(source),
                   'inputs_sha256': sha(ROOT / 'data/test-evolution/TEBench/inputs.json'),
                   'source_sha256': {name: sha(ROOT / name) for name in
                                     ('scripts/test_evolution.py', 'scripts/recover_test_evolution.py', 'retrieval/index.py', 'ingestion/git.py')}}
    meta = a.output / 'fingerprint.json'
    if meta.exists():
        if json.loads(meta.read_text()) != fingerprint:
            raise ValueError('Recovery resume fingerprint differs')
    else:
        if a.resume:
            p.error('Missing recovery fingerprint')
        save(meta, fingerprint)
    groups = defaultdict(list)
    for task in inputs:
        groups[task['repository']].append(task)
    def project(tasks):
        result = []
        for task in tasks:
            cid = task['case_id']; original = by[cid]
            path = a.output / 'cases' / (hashlib.sha256(cid.encode()).hexdigest() + '.json')
            if path.exists():
                row = json.loads(path.read_text())
                if row.get('case_id') != cid:
                    raise ValueError('Saved recovery case differs')
            elif original['status'] == 'RANKED':
                row = original
                save(path, row)
            else:
                try:
                    row = ranks(task, a.runtime)
                except Exception as exc:
                    row = {'case_id': cid, 'status': 'FAILED', 'error': str(exc)[:1000]}
                row = {**row, 'recovery_attempt': {'original_status': original['status'],
                       'original_error': original.get('error'), 'reason': 'Separate pre-fetched cache after stale shallow-lock failures'}}
                save(path, row)
                print(cid, row['status'], flush=True)
            result.append(row)
        return result
    with ThreadPoolExecutor(max_workers=3) as executor:
        predictions = [r for rows in executor.map(project, [groups[k] for k in sorted(groups)]) for r in rows]
    save(a.output / 'predictions.json', predictions)
    gold = json.loads((ROOT / 'data/test-evolution/TEBench/gold.json').read_text())
    result = {'status': 'COMPLETED_INFRASTRUCTURE_RECOVERY',
              'original_failed_cases': sum(r['status'] != 'RANKED' for r in originals),
              'remaining_failed_cases': sum(r['status'] != 'RANKED' for r in predictions),
              'successful_originals_reused_without_rerun': sum(r['status'] == 'RANKED' for r in originals),
              'methods': {m: score(gold, predictions, m) for m in ARMS}, 'original_run_preserved': True,
              'new_llm_calls': 0, 'subject_code_executed': False, 'quality_target_91': 'NOT_EVALUATED',
              'scope': 'Same source-only retrieval algorithm and task denominator; only infrastructure failures retried in separate caches'}
    save(a.output / 'results.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'methods'}, indent=2))


if __name__ == '__main__':
    main()

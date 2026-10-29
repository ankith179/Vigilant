"""Inspect exposed reference absences at pinned base trees without changing rankings."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.git import inventory, revision


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, default=ROOT / '.runtime/tebench-recovery')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Preserve existing diagnostic output')
    source = ROOT / 'reports/realworld-20261024/miss-decomposition-20261024.json'
    inputs = ROOT / 'data/test-evolution/TEBench/inputs.json'
    diagnostic = json.loads(source.read_text())
    tasks = {r['case_id']: r for r in json.loads(inputs.read_text())}
    result = []
    for row in diagnostic['cases']:
        absent = row['outside_inventory']
        if not absent:
            continue
        task = tasks[row['case_id']]
        repo = a.cache / task['repository'].replace('/', '__')
        if revision(repo, task['base_commit']) != task['base_commit']:
            raise ValueError('Pinned base mismatch')
        tree = {f['file']: f for f in inventory(repo, task['base_commit'])}
        for ref in absent:
            entry = tree.get(ref['path'])
            # Only the base is available here. Absence is not proof of a new file:
            # a rename or reference-path convention may explain it.
            reason = ('ABSENT_AT_PINNED_BASE_PATH' if entry is None else
                      'PRESENT_NON_JAVA_EXCLUDED' if not ref['path'].endswith('.java') else
                      'PRESENT_INELIGIBLE_' + entry['exclusion_reason'] if not entry['eligible'] else
                      'PRESENT_JAVA_OUTSIDE_TEST_DIRECTORY' if not any(x in {'test', 'tests'} for x in Path(ref['path']).parts) else
                      'PRESENT_ELIGIBLE_JAVA_REQUIRES_INVENTORY_RECONCILIATION')
            result.append({'case_id': row['case_id'], 'repository': task['repository'],
                           'base_commit': task['base_commit'], 'path': ref['path'],
                           'prior_scope': ref['scope'], 'diagnosis': reason,
                           'base_tree_entry': entry})
    output = {'status': 'PINNED_BASE_PATH_AUDIT_COMPLETE', 'scope': 'EXPOSED_DEVELOPMENT_DIAGNOSTIC',
              'counts': dict(Counter(r['diagnosis'] for r in result)),
              'java_counts': dict(Counter(r['diagnosis'] for r in result if r['path'].endswith('.java'))),
              'rows': result, 'new_predictions': 0, 'new_llm_calls': 0,
              'quality_target_91': 'NOT_EVALUATED',
              'limitations': ['Exact paths at base only; no rename/new-file inference or full impact judgment.',
                              'No cutoff, inventory, model or ranking changed. All 314 case denominators retained.'],
              'input_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in (source, inputs)},
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'counts', 'java_counts')}))


if __name__ == '__main__':
    main()

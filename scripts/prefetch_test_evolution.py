"""Fetch all pinned base commits once into separate caches; preserve failed caches."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.git import git, revision
from scripts.test_evolution import save


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, default=ROOT / '.runtime/tebench-recovery')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Preserve existing fetch report')
    inputs = json.loads((ROOT / 'data/test-evolution/TEBench/inputs.json').read_text())
    groups = defaultdict(set)
    for row in inputs:
        groups[row['repository']].add(row['base_commit'])
    def fetch(pair):
        slug, commits = pair
        repo = a.runtime / slug.replace('/', '__')
        repo.mkdir(parents=True, exist_ok=True)
        if not (repo / 'HEAD').exists():
            git(repo, 'init', '--bare')
        status, error = 'FETCHED', None
        try:
            # One fetch per independent repository avoids repeatedly rewriting shallow roots.
            git(repo, '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'fetch',
                '--depth=1', '--no-write-fetch-head', 'https://github.com/' + slug + '.git', *sorted(commits))
        except subprocess.CalledProcessError as exc:
            status, error = 'FETCH_FAILED', exc.stderr.decode(errors='replace')[-3000:]
        except Exception as exc:
            status, error = 'FETCH_FAILED', str(exc)
        present, missing = [], []
        for sha in sorted(commits):
            try:
                assert revision(repo, sha) == sha
                present.append(sha)
            except Exception:
                missing.append(sha)
        row = {'repository': slug, 'status': status, 'error': error,
               'present': present, 'missing': missing}
        save(a.output.parent / 'prefetch-repositories' / (slug.replace('/', '__') + '.json'), row)
        print(slug, len(present), '/', len(commits), flush=True)
        return row
    with ThreadPoolExecutor(max_workers=3) as executor:
        rows = list(executor.map(fetch, sorted(groups.items())))
    save(a.output, {'repositories': rows, 'runtime': str(a.runtime), 'subject_code_executed': False,
                    'new_llm_calls': 0, 'original_caches_preserved': True})


if __name__ == '__main__':
    main()

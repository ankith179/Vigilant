"""Pinned real-project test-file retrieval and training-only policy comparison.

TEBench answers describe developer test evolution. They are not VIGILANT
consistency labels, complete impact sets, or reviewed negative trace links.
"""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ingestion.git import git, revision, inventory
from retrieval.index import Index, RETRIEVAL_POLICY

REVISION = 'eaed7337a15d8db78d0ff3240e39a933784e8088'
PARQUET_SHA = '64eff60fb61779fac101d7063d0970dd4690bb583c7faa0fb3e673e539ddba85'
ARMS = ('tfidf', 'bm25', 'rank_rrf')
TEST_CANDIDATE_POLICY = 'test-tree-and-resource-v2'
TEST_PATH_PARTS = {'test', 'tests', 'testresources', 'test-resources', 'fixtures', 'fuzztests'}
RESOURCE_PATH_PARTS = {'resource', 'resources', 'fixture', 'fixtures', 'fuzztests'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix('.pending')
    pending.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    pending.replace(path)


def paths(patch):
    result = set()
    for line in patch.splitlines():
        if not line.startswith('diff --git '):
            continue
        fields = shlex.split(line)
        if len(fields) != 4:
            raise ValueError('Unsupported patch header')
        for field, prefix in zip(fields[2:], ('a/', 'b/')):
            path = PurePosixPath(field[2:])
            if not field.startswith(prefix) or path.is_absolute() or '..' in path.parts or '\\' in str(path):
                raise ValueError('Unsafe patch path')
            result.add(str(path))
    if not result:
        raise ValueError('Patch has no file headers')
    return sorted(result)


def prepare(rows):
    inputs, gold, ids = [], [], set()
    for r in rows:
        cid = r['instance_id']
        if not isinstance(cid, str) or not cid or cid in ids:
            raise ValueError('Missing or duplicate identity')
        ids.add(cid)
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', r['repo']):
            raise ValueError('Expected GitHub repository slug')
        if any(not re.fullmatch('[0-9a-f]{40}', r[k]) for k in ('v_minus_1_commit', 'v0_commit')):
            raise ValueError('Expected immutable commits')
        if not isinstance(r['labels'], list) or not r['labels'] or not set(r['labels']) <= {'breaking', 'stale', 'missing'}:
            raise ValueError('Invalid published evolution labels')
        # Full V0, commit message, labels, test names and test patch stay out of inputs.
        inputs.append({'case_id': cid, 'project': r['project'], 'repository': r['repo'],
                       'base_commit': r['v_minus_1_commit'], 'source_patch': r['source_patch'],
                       'non_test_paths': paths(r['source_patch'])})
        gold.append({'case_id': cid, 'full_answer_commit': r['v0_commit'], 'evolution_labels': r['labels'],
                     'developer_changed_test_files': paths(r['test_patch']),
                     'developer_changed_test_methods': r['changed_test_methods'],
                     'test_patch_sha256': hashlib.sha256(r['test_patch'].encode()).hexdigest()})
    return inputs, gold


def read_blobs(repo, ids):
    ids = list(dict.fromkeys(ids))
    if not ids:
        return {}
    if any(not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', oid) for oid in ids):
        raise ValueError('Expected immutable object IDs')
    # One subprocess for all eligible test files; never execute a subject script.
    import os
    raw = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'core.fsmonitor=false',
                          '-C', str(repo), 'cat-file', '--batch'],
                         input=('\n'.join(ids) + '\n').encode(), capture_output=True, check=True, timeout=180).stdout
    offset, result = 0, {}
    for oid in ids:
        end = raw.find(b'\n', offset)
        if end < 0:
            raise ValueError('Truncated batch header')
        header = raw[offset:end].split()
        if len(header) != 3 or header[0].decode() != oid or header[1] != b'blob':
            raise ValueError('Expected Git blob')
        size = int(header[2]); start = end + 1; offset = start + size + 1
        if size < 0 or raw[offset - 1:offset] != b'\n':
            raise ValueError('Truncated blob')
        result[oid] = raw[start:start + size]
    if offset != len(raw):
        raise ValueError('Unexpected batch data')
    return result


def candidate_kind(row):
    """Classify base-tree test artifacts without treating arbitrary files as tests.

    Supported source/text files under an explicit test tree are indexed by path
    and content. Unsupported-suffix fixtures under a resource tree are retained
    as path-only candidates; large files and ignored directories remain excluded
    by ``inventory``.
    """
    path = PurePosixPath(row['file'])
    parts = {part.casefold() for part in path.parts}
    if not parts.intersection(TEST_PATH_PARTS):
        return None
    if row.get('eligible'):
        return 'indexed_test_artifact'
    if (row.get('exclusion_reason') == 'unsupported-suffix'
            and parts.intersection(RESOURCE_PATH_PARTS)):
        return 'path_only_test_resource'
    return None


def candidate_items(rows, blobs):
    items = []
    for row in rows:
        kind = candidate_kind(row)
        if kind is None:
            continue
        path = row['file']
        text = path
        raw = blobs.get(row['object_id'])
        if kind == 'indexed_test_artifact' and raw is not None and b'\0' not in raw:
            text += '\n' + raw.decode('utf-8', errors='replace')
        items.append({'id': path, 'text': text})
    return items


def ranks(task, runtime):
    slug, base = task['repository'], task['base_commit']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', slug) or not re.fullmatch('[0-9a-f]{40}', base):
        raise ValueError('Invalid repository/commit')
    repo = runtime / slug.replace('/', '__')
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / 'HEAD').exists():
        git(repo, 'init', '--bare')
    try:
        revision(repo, base)
    except subprocess.CalledProcessError:
        git(repo, 'fetch', '--depth=1', 'https://github.com/' + slug + '.git', base)
    if revision(repo, base) != base:
        raise ValueError('Commit mismatch')
    files = inventory(repo, base)
    selected = [f for f in files if candidate_kind(f) is not None]
    blobs = read_blobs(repo, [f['object_id'] for f in selected if f['eligible']])
    items = candidate_items(selected, blobs)
    if not items:
        raise ValueError('No eligible base tests')
    query = task['source_patch'][:128_000]
    index = Index(items)
    orders = {m: [h['id'] for h in index.search(query, m, len(items))] for m in ('tfidf', 'bm25')}
    fusion = defaultdict(float)
    for order in orders.values():
        for rank, file in enumerate(order, 1):
            fusion[file] += 1 / (60 + rank)
    orders['rank_rrf'] = sorted(fusion, key=lambda p: (-fusion[p], p))
    return {'case_id': task['case_id'], 'status': 'RANKED', 'candidate_policy': TEST_CANDIDATE_POLICY,
            'rankings': orders,
            'base_commit': base, 'repository': slug, 'candidate_files': [i['id'] for i in items],
            'query_sha256': hashlib.sha256(query.encode()).hexdigest(),
            'query_characters_omitted': max(0, len(task['source_patch']) - len(query)),
            'candidate_sha256': hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()}


def score(gold, predictions, method):
    ids = [r.get('case_id') for r in predictions]
    gids = [r['case_id'] for r in gold]
    if len(set(gids)) != len(gids) or len(set(ids)) != len(ids) or not set(ids) <= set(gids):
        raise ValueError('Duplicate or foreign case')
    by = {r['case_id']: r for r in predictions}; rows = []
    for g in gold:
        relevant = set(g['developer_changed_test_files'])
        if not relevant:
            raise ValueError('Empty published reference')
        p = by.get(g['case_id'], {}); candidates = p.get('candidate_files', [])
        if not isinstance(candidates, list) or not all(isinstance(x, str) for x in candidates):
            candidates = []
        order = p.get('rankings', {}).get(method, [])
        valid = (p.get('status') == 'RANKED' and bool(candidates) and isinstance(order, list)
                 and all(isinstance(x, str) for x in order) and len(set(order)) == len(order)
                 and len(set(candidates)) == len(candidates) and set(order) == set(candidates))
        if not valid:
            order = []
        rows.append({'case_id': g['case_id'], 'valid': valid, 'unavailable_in_base': sorted(relevant - set(candidates)),
                     **{f'recall_at_{k}': len(set(order[:k]) & relevant) / len(relevant) for k in (1, 5, 10)}})
    return {'cases': len(rows), 'invalid_or_missing': sum(not r['valid'] for r in rows),
            **{f'mean_recall_at_{k}': sum(r[f'recall_at_{k}'] for r in rows) / len(rows) if rows else 0 for k in (1, 5, 10)},
            'case_metrics': rows}


def run(args):
    inputs = json.loads((args.dataset / 'inputs.json').read_text())
    groups = defaultdict(list)
    for task in inputs:
        groups[task['repository']].append(task)
    if args.output.exists() and not args.resume:
        raise ValueError('Output exists; use exact --resume or another output')
    args.output.mkdir(parents=True, exist_ok=args.resume)
    fingerprint = {'inputs_sha256': sha(args.dataset / 'inputs.json'), 'retrieval_policy': RETRIEVAL_POLICY,
                   'candidate_policy': TEST_CANDIDATE_POLICY,
                   'sources': {name: sha(ROOT / name) for name in ('scripts/test_evolution.py', 'retrieval/index.py', 'ingestion/git.py')}}
    meta = args.output / 'fingerprint.json'
    if meta.exists():
        if json.loads(meta.read_text()) != fingerprint:
            raise ValueError('Resume fingerprint mismatch')
    else:
        if args.resume:
            raise ValueError('No saved fingerprint')
        save(meta, fingerprint)
        for name in fingerprint['sources']:
            target = args.output / 'frozen' / (name.replace('/', '__') + '.txt')
            target.parent.mkdir(exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
    def project(tasks):
        # One thread per repository group: no concurrent Git fetches into one repository.
        result = []
        for task in tasks:
            saved = args.output / 'cases' / (hashlib.sha256(task['case_id'].encode()).hexdigest() + '.json')
            if saved.exists():
                row = json.loads(saved.read_text())
                if row.get('case_id') != task['case_id']:
                    raise ValueError('Saved case identity mismatch')
            else:
                try:
                    row = ranks(task, ROOT / '.runtime/tebench')
                except Exception as exc:
                    row = {'case_id': task['case_id'], 'status': 'FAILED', 'error': str(exc)[:1000]}
                save(saved, row)
                print(task['case_id'], row['status'], flush=True)
            result.append(row)
        return result
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        predictions = [r for project_rows in executor.map(project, [groups[k] for k in sorted(groups)]) for r in project_rows]
    save(args.output / 'predictions.json', predictions)
    # Gold opens after rankings have been persisted. Full V0 never enters retrieval.
    gold = json.loads((args.dataset / 'gold.json').read_text())
    result = {'status': 'COMPLETED_DEVELOPMENT_RETRIEVAL', 'dataset_sha256': PARQUET_SHA,
              'methods': {m: score(gold, predictions, m) for m in ARMS},
              'new_llm_calls': 0, 'subject_code_executed': False, 'quality_target_91': 'NOT_EVALUATED',
              'scope': 'Developer-changed test-file recall from base test-source and test-resource candidates; files absent at base remain misses. No precision/consistency claim.'}
    save(args.output / 'results.json', result)
    print(json.dumps({m: {k: v for k, v in s.items() if k != 'case_metrics'} for m, s in result['methods'].items()}, indent=2))


def policy(args):
    import numpy as np
    from scripts.run_contextual_bandit import LinUCB, query_features, fit_scaler, scale_feature
    if args.output.exists():
        raise ValueError('Preserve existing output')
    inputs = json.loads((args.dataset / 'inputs.json').read_text())
    gold = {r['case_id']: r for r in json.loads((args.dataset / 'gold.json').read_text())}
    predictions = {r['case_id']: r for r in json.loads((args.baseline / 'predictions.json').read_text())}
    if set(predictions) != {r['case_id'] for r in inputs}:
        raise ValueError('Incomplete baseline')
    projects = sorted({r['project'] for r in inputs})
    training = set(projects[:5])  # Fixed before training; all data remains exposed development material.
    train = [r for r in inputs if r['project'] in training]
    held = [r for r in inputs if r['project'] not in training]
    mean, scale = fit_scaler([query_features(r['source_patch']) for r in train])
    learner = LinUCB(ARMS, 4, alpha=0.5); trace = []
    for epoch in range(3):
        for r in train:
            x = scale_feature(query_features(r['source_patch']), mean, scale)
            arm = learner.choose(x, explore=True)
            reward = score([gold[r['case_id']]], [predictions[r['case_id']]], arm)['mean_recall_at_5']
            learner.update(arm, x, reward)
            trace.append({'epoch': epoch, 'case_id': r['case_id'], 'arm': arm, 'reward': reward})
    frozen = {'parameters': learner.parameters(), 'mean': mean.tolist(), 'scale': scale.tolist()}
    frozen_sha = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    selected = []
    for r in held:
        x = scale_feature(query_features(r['source_patch']), mean, scale)
        arm = learner.choose(x, explore=False)
        original = predictions[r['case_id']]
        selected.append({**original, 'chosen_arm': arm, 'rankings': {'bandit': original.get('rankings', {}).get(arm, [])}})
    assert frozen_sha == hashlib.sha256(json.dumps({'parameters': learner.parameters(), 'mean': mean.tolist(), 'scale': scale.tolist()}, sort_keys=True).encode()).hexdigest()
    truth = [gold[r['case_id']] for r in held]
    methods = {m: score(truth, [predictions[r['case_id']] for r in held], m) for m in ARMS}
    methods['bandit'] = score(truth, selected, 'bandit')
    result = {'status': 'COMPLETED_DEVELOPMENT_POLICY', 'training_projects': sorted(training),
              'held_development_projects': [p for p in projects if p not in training], 'training_events': len(trace),
              'frozen_policy_sha256': frozen_sha, 'policy': frozen, 'methods': methods,
              'new_llm_calls': 0, 'full_weight_rl': 'NOT_RUN', 'production_policy_promoted': False,
              'quality_target_91': 'NOT_EVALUATED',
              'limitations': ['All benchmark metadata is exposed development material; repository families can overlap.',
                             'Reward is published test-edit Recall@5, not independent semantic/consistency correctness.',
                             'Three fixed epochs, training-only scaling/rewards, no held-project policy updates.',
                             'Each fixed baseline and every invalid/missing outcome are retained.']}
    save(args.output / 'results.json', result); save(args.output / 'training-trace.json', trace)
    save(args.output / 'predictions.json', selected)
    print(json.dumps({m: {k: v for k, v in s.items() if k != 'case_metrics'} for m, s in methods.items()}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'run', 'policy'))
    p.add_argument('--dataset', type=Path, default=ROOT / 'data/test-evolution/TEBench')
    p.add_argument('--parquet', type=Path, default=ROOT / 'data/raw/TEBench/test.parquet')
    p.add_argument('--output', type=Path)
    p.add_argument('--baseline', type=Path)
    p.add_argument('--workers', type=int, default=3, choices=range(1, 5))
    p.add_argument('--resume', action='store_true')
    args = p.parse_args()
    if args.action == 'prepare':
        if args.dataset.exists(): p.error('Preserve the existing prepared dataset')
        if sha(args.parquet) != PARQUET_SHA: p.error('Pinned dataset checksum mismatch')
        import pyarrow.parquet as pq  # Benchmark-only optional dependency.
        inputs, gold = prepare(pq.read_table(args.parquet).to_pylist())
        if len(inputs) != 314 or len({r['project'] for r in inputs}) != 10: p.error('Pinned dataset count mismatch')
        save(args.dataset / 'inputs.json', inputs); save(args.dataset / 'gold.json', gold)
        save(args.dataset / 'source.json', {'repository': 'https://huggingface.co/datasets/iSEngLab/TEBench',
             'revision': REVISION, 'sha256': PARQUET_SHA, 'licence': 'CC-BY-4.0 dataset; subject code terms remain applicable',
             'cases': 314, 'exposure': 'DEVELOPMENT_ONLY', 'input_state': 'base plus source_patch, original tests unchanged',
             'scope': 'Published test evolution only; not VIGILANT consistency ground truth'})
    elif args.action == 'run':
        if not args.output: p.error('--output required')
        run(args)
    else:
        if not args.output or not args.baseline: p.error('--output and --baseline required')
        policy(args)


if __name__ == '__main__':
    main()

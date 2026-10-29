"""Create two identical blank review sheets from unreviewed Git case cards."""
import argparse
import csv
import json
import random
import re
import subprocess
from collections import defaultdict
from pathlib import Path

try:
    from .case_card_v1 import CaseCard
except ImportError:
    from case_card_v1 import CaseCard

FIELDS = ('case_id', 'source_id', 'base', 'head', 'path', 'symbol', 'diff_command',
          'reviewer_trace', 'reviewer_consistency', 'reviewer_test_obligation',
          'reviewer_authority', 'evidence_notes', 'reviewer_id', 'reviewed_at_utc',
          'reviewer_rationale', 'uncertainty_reason', 'adjudication_status')


def prepare(cards, source_paths, limit=30, seed=104729):
    if limit < 1:
        raise ValueError('limit must be positive')
    groups, seen = defaultdict(list), set()
    for raw in cards:
        card = CaseCard.model_validate(raw)
        if card.case_id in seen:
            raise ValueError('duplicate case ID')
        seen.add(card.case_id)
        if card.adjudication.status != 'PENDING' or card.label_status != 'UNREVIEWED_SILVER':
            raise ValueError('review input must be unreviewed')
        if card.history_source != 'A':
            raise ValueError('only Git review commands are currently supported')
        if not all(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', rev) for rev in (card.base_revision, card.head_revision)):
            raise ValueError('Git revisions must be full hexadecimal commit IDs')
        if card.source_id not in source_paths:
            raise ValueError('source path missing from manifest')
        path, symbol = card.change_facts.get('path'), card.change_facts.get('symbol', '')
        if not isinstance(path, str) or not path or not isinstance(symbol, str):
            raise ValueError('case path and symbol required')
        values = [card.case_id, card.source_id, card.base_revision, card.head_revision, path, symbol, source_paths[card.source_id]]
        if any(not isinstance(v, str) or '\n' in v or '\r' in v or v.lstrip().startswith(('=', '+', '-', '@')) for v in values):
            raise ValueError('unsafe spreadsheet value')
        cmd = subprocess.list2cmdline(['git', '-C', source_paths[card.source_id], 'diff', card.base_revision, card.head_revision, '--', path])
        row = dict(zip(FIELDS, values[:2] + values[2:6] + [cmd] + [''] * (len(FIELDS) - 7)))
        row['adjudication_status'] = 'PENDING'
        groups[(card.priority_tier, card.source_id)].append(row)
    rng = random.Random(seed)
    for rows in groups.values():
        rng.shuffle(rows)
    selected = []
    keys = sorted(groups)
    while len(selected) < limit and keys:
        for key in keys[:]:
            selected.append(groups[key].pop())
            if not groups[key]:
                keys.remove(key)
            if len(selected) == limit:
                break
    rng.shuffle(selected)
    return selected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cards', type=Path)
    p.add_argument('--repos-json', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--limit', type=int, default=30)
    p.add_argument('--seed', type=int, default=104729)
    args = p.parse_args()
    with args.cards.open(encoding='utf-8') as src:
        cards = [json.loads(line) for line in src if line.strip()]
    manifest = json.loads(args.repos_json.read_text(encoding='utf-8'))
    paths = {r['id']: r['clone_path'] for r in manifest['repositories']}
    rows = prepare(cards, paths, args.limit, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    for name in ('reviewer-1.csv', 'reviewer-2.csv'):
        with (args.output_dir / name).open('x', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({'case_count': len(rows), 'seed': args.seed, 'labels_created': 0}))


if __name__ == '__main__':
    main()

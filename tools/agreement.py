"""Describe agreement between two completed review sheets; no gold labels are created."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

AXES = {
    'trace': {'LINKED', 'BROKEN_TRACE', 'MISSING_TRACE', 'UNCERTAIN'},
    'consistency': {'CONSISTENT', 'INCONSISTENT', 'POTENTIAL_INCONSISTENCY', 'NO_ASSURANCE_IMPACT', 'UNCERTAIN'},
    'test_obligation': {'SATISFIED', 'UNSATISFIED', 'UNVERIFIED', 'NOT_APPLICABLE'},
    'authority': {'NORMATIVE', 'INFORMATIONAL', 'NOT_ESTABLISHED'},
}
IDENTITY = ('case_id', 'source_id', 'base', 'head', 'path', 'symbol', 'diff_command')


def load(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = set(IDENTITY) | {'reviewer_' + axis for axis in AXES}
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not required.issubset(reader.fieldnames):
            raise ValueError('review sheet fields missing or duplicated')
        rows = {}
        for row in reader:
            cid = row['case_id']
            if not cid or cid in rows:
                raise ValueError('empty or duplicate case ID')
            for axis, labels in AXES.items():
                label = row['reviewer_' + axis]
                if label and label not in labels:
                    raise ValueError(f'invalid {axis} label in {cid}')
            rows[cid] = row
    return rows


def agreement(left, right, mode):
    if mode not in ('inter-rater', 'intra-rater'):
        raise ValueError('invalid agreement mode')
    if not left or set(left) != set(right):
        raise ValueError('review sheets must contain the same nonempty case set')
    for cid in left:
        if any(left[cid][field] != right[cid][field] for field in IDENTITY):
            raise ValueError(f'case identity differs: {cid}')
    results = {}
    for axis, allowed in AXES.items():
        field = 'reviewer_' + axis
        paired = [(cid, left[cid][field], right[cid][field]) for cid in sorted(left)
                  if left[cid][field] and right[cid][field]]
        n = len(paired)
        ca, cb = Counter(a for _, a, _ in paired), Counter(b for _, _, b in paired)
        observed = sum(a == b for _, a, b in paired) / n if n else None
        expected = sum(ca[k] * cb[k] for k in allowed) / (n * n) if n else None
        kappa = (observed - expected) / (1 - expected) if n and expected < 1 else None
        results[axis] = {'paired': n, 'incomplete': len(left) - n, 'agreement': observed,
                         'cohen_kappa': kappa, 'kappa_status': 'DEFINED' if kappa is not None else 'UNDEFINED',
                         'confusion_matrix': {a: {b: sum(x == a and y == b for _, x, y in paired)
                                                  for b in sorted(allowed)} for a in sorted(allowed)},
                         'disagreements': [cid for cid, a, b in paired if a != b]}
    return {'mode': mode, 'case_count': len(left), 'axes': results,
            'independence': 'NOT_VERIFIED', 'interpretation': 'Agreement is not accuracy or adjudication.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('first', type=Path)
    p.add_argument('second', type=Path)
    p.add_argument('--mode', choices=('inter-rater', 'intra-rater'), required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = agreement(load(args.first), load(args.second), args.mode)
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2)
        out.write('\n')
    print(json.dumps({'mode': args.mode, 'cases': result['case_count'], 'labels_created': 0}))


if __name__ == '__main__':
    main()

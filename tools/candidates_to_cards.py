"""Convert priority-tagged Git miner candidates into validated case cards."""
import argparse
import json
from pathlib import Path

try:
    from .case_card_v1 import CaseCard
except ImportError:
    from case_card_v1 import CaseCard

TIERS = {
    'P1': {'D13', 'D14', 'D15', 'D16', 'D19'},
    'P2': {'D18', 'D25', 'D26', 'D30', 'D31'},
    'P3': {'D17', 'D20', 'D21', 'D22', 'D23', 'D27'},
    'P4': {'D24', 'D28', 'D29', 'D32', 'D33', 'D34', 'D35', 'D36'},
}


def convert(row):
    if row.get('origin') != 'MINED' or row.get('label_status') != 'UNREVIEWED_SILVER':
        raise ValueError('expected an unreviewed mined candidate')
    if any(row.get(key) is not None for key in ('expected_trace', 'expected_consistency',
           'expected_test_obligation', 'expected_authority', 'impact_ground_truth')):
        raise ValueError('candidate contains labels')
    tiers = [tier for tier, ids in TIERS.items() if ids.intersection(row.get('d_ids', []))]
    if not tiers:
        raise ValueError('candidate has no target priority assignment')
    base_revision, head_revision = row['base_revision'], row['head_revision']
    revisions = {'BASE': base_revision, 'HEAD': head_revision,
                 base_revision: base_revision, head_revision: head_revision}
    artifacts = {'requirement': [], 'code': [], 'test': []}
    for evidence in row['facts']['evidence']:
        if evidence.get('presence') != 'PRESENT':
            continue
        path = evidence['path']
        evidence_revision = revisions.get(evidence.get('revision'))
        if evidence_revision is None:
            raise ValueError('evidence revision is not bound to the case BASE or HEAD')
        parts = path.lower().replace('\\', '/').split('/')
        kind = 'test' if 'tests' in parts or 'test' in parts or parts[-1].startswith('test_') else 'code'
        artifacts[kind].append({'path': path, 'revision': evidence_revision,
                                'content_hash': evidence['content_hash']})
    card = {'case_id': row['case_id'], 'd_ids': row['d_ids'], 'priority_tier': tiers[0],
            'origin': 'MINED', 'source_id': row['repository_id'], 'family': row['family'],
            'split': row['split'], 'history_source': 'A', 'base_revision': row['base_revision'],
            'head_revision': row['head_revision'], 'artifacts': artifacts,
            'change_facts': {'candidate_category': row['candidate_category'], 'path': row['path'],
                             'symbol': row['symbol'], 'facts': row['facts']},
            'requirement_source': None, 'expected_trace': None, 'expected_consistency': None,
            'expected_test_obligation': None, 'expected_authority': None, 'impact_ground_truth': None,
            'supporting_evidence_ids': [], 'adjudication': {'status': 'PENDING', 'reviewer_ids': [], 'rationale': None},
            'notes': 'Candidate only; absent revision observations remain in change_facts.',
            'label_status': 'UNREVIEWED_SILVER'}
    return CaseCard.model_validate(card).model_dump()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    seen, cards = set(), []
    with args.input.open(encoding='utf-8') as src:
        for number, line in enumerate(src, 1):
            if not line.strip():
                continue
            try:
                card = convert(json.loads(line))
                if card['case_id'] in seen:
                    raise ValueError('duplicate case_id')
                seen.add(card['case_id'])
                cards.append(card)
            except (ValueError, KeyError, TypeError) as exc:
                p.error(f'line {number}: {exc}; no output written')
    with args.output.open('x', encoding='utf-8', newline='\n') as dst:
        for card in cards:
            dst.write(json.dumps(card, ensure_ascii=False) + '\n')
    print(json.dumps({'cards': len(cards), 'labels_created': 0}))


if __name__ == '__main__':
    main()

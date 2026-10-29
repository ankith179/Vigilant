"""Coverage is not accuracy. Summarize validated case-card inventory."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .case_card_v1 import CaseCard
except ImportError:
    from case_card_v1 import CaseCard

TARGET = {f'D{i}' for i in range(1, 37)}
CURATED = {'D13', 'D15', 'D16', 'D18', 'D21', 'D24', 'D29', 'D34', 'D35'}
AXES = ('trace', 'consistency', 'test_obligation', 'authority')


def summarize(raw_cards, sources):
    cards, ids = [], set()
    for raw in raw_cards:
        card = CaseCard.model_validate(raw)
        if card.case_id in ids:
            raise ValueError('duplicate case ID')
        ids.add(card.case_id)
        dids = set()
        for value in card.d_ids:
            if not isinstance(value, str) or not value.startswith('D') or not value[1:].isdigit():
                raise ValueError('invalid D-ID')
            did = f'D{int(value[1:])}'
            if did not in TARGET:
                raise ValueError('D-ID outside target')
            dids.add(did)
        cards.append((card, dids))
    counts = {field: Counter(getattr(card, field) for card, _ in cards)
              for field in ('priority_tier', 'source_id', 'family', 'split', 'origin', 'history_source')}
    did_counts = Counter(d for _, dids in cards for d in dids)
    by_split = defaultdict(Counter)
    source_split = defaultdict(Counter)
    labels = {axis: Counter() for axis in AXES}
    for card, dids in cards:
        by_split[card.split].update(dids)
        source_split[card.split][card.source_id] += 1
        if card.adjudication.status == 'ADJUDICATED':
            for axis in AXES:
                value = getattr(card, 'expected_' + axis)
                if value is not None:
                    labels[axis][value] += 1
    no_history = [s['id'] for s in sources if s.get('history_source') == 'NO_HISTORY']
    return {'notice': 'Coverage is not accuracy.', 'case_count': len(cards),
            'd_id_counts': {d: did_counts[d] for d in sorted(TARGET, key=lambda x:int(x[1:]))},
            'counts': {key:dict(value) for key, value in counts.items()},
            'adjudicated_axis_labels': {key:dict(value) for key, value in labels.items()},
            'missing_d_ids': sorted(TARGET - set(did_counts), key=lambda x:int(x[1:])),
            'missing_by_split': {split:sorted(TARGET - set(by_split[split]), key=lambda x:int(x[1:])) for split in ('dev', 'test')},
            'curated_only_missing': sorted(CURATED - set(did_counts), key=lambda x:int(x[1:])),
            'source_over_25_percent': {split:{source:n for source,n in c.items() if n * 4 > sum(c.values())}
                                       for split,c in source_split.items()},
            'no_history_sources': no_history}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cards', type=Path)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    with args.cards.open(encoding='utf-8') as stream:
        cards = [json.loads(line) for line in stream if line.strip()]
    manifest = json.loads(args.sources.read_text(encoding='utf-8'))
    result = summarize(cards, manifest['sources'])
    with args.output.open('x', encoding='utf-8') as out:
        out.write('Coverage is not accuracy.\n')
        json.dump(result, out, indent=2)
        out.write('\n')
    print('Coverage is not accuracy.')
    print(json.dumps({'case_count': result['case_count'], 'missing_d_ids': len(result['missing_d_ids'])}))


if __name__ == '__main__':
    main()

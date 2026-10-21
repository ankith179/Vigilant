"""Create tables and a scientific plot from a complete real-inference ablation."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.resume import atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path)
    args = parser.parse_args()
    candidates = [p for p in sorted((ROOT/'experiments/ablation').glob('*/results.json'))
                  if not (p.parent/'EXCLUDED.json').exists()]
    path = args.run or (candidates[-1] if candidates else None)
    if path is None:
        raise SystemExit('No non-excluded completed ablation exists yet.')
    run = json.loads(path.read_text())
    rows = run['rows']
    if run['status'] != 'COMPLETED' or len(rows) != 60:
        raise ValueError('Expected the complete 12-case, 5-variant study.')
    contracts = {}
    for p in (ROOT/'data/changebench').glob('[0-9][0-9]-*.json'):
        if not p.stem.endswith('-report'):
            c = json.loads(p.read_text())
            contracts[c['id']] = c
    actual = {(r['case_id'], r['variant']) for r in rows}
    expected = {(c, v) for c in contracts for v in 'EFGHI'}
    if actual != expected or len(actual) != len(rows):
        raise ValueError('Missing, duplicate or unexpected study pair.')
    for r in rows:
        if not r['model'].get('usage', {}).get('output_tokens'):
            raise ValueError('No-inference failure cannot be summarized as model accuracy.')
        if r['expected_status'] != contracts[r['case_id']]['status']:
            raise ValueError('Expected label does not match preserved scenario contract.')
    summaries = []
    for variant in 'EFGHI':
        group = [r for r in rows if r['variant'] == variant]
        recalled = [r['known_endpoint_recall'] for r in group if r['known_endpoint_recall'] is not None]
        summaries.append({
            'variant': variant, 'name': group[0]['name'], 'cases': len(group),
            'correct': sum(r['predicted_status'] == r['expected_status'] for r in group),
            'status_agreement': sum(r['predicted_status'] == r['expected_status'] for r in group)/len(group),
            'schema_citation_validity': sum(r['model']['validation_error'] is None for r in group)/len(group),
            'uncertainty_rate': sum(r['predicted_status'] == 'UNCERTAIN' for r in group)/len(group),
            'known_endpoint_recall': sum(recalled)/len(recalled) if recalled else None,
            'mean_seconds': sum(r['seconds'] for r in group)/len(group),
            'prediction_counts': dict(Counter(r['predicted_status'] for r in group)),
            'validation_errors': dict(Counter((r['model']['validation_error'] or '').split(':', 1)[0]
                                              for r in group if r['model']['validation_error'])),
            'semantic_grounding': None, 'hallucination_rate': None,
        })
    output = ROOT/'reports/ablation'
    output.mkdir(parents=True, exist_ok=True)
    record = {'source_run': str(path.relative_to(ROOT)),
              'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'inference_calls': len(rows), 'resumed_calls': run.get('resumed_calls', 0),
              'new_calls': run.get('new_calls', len(rows)),
              'expected_statuses': dict(Counter(c['status'] for c in contracts.values())),
              'summary': summaries, 'limitations': run['limitations']}
    atomic_json(output/'summary.json', record)
    packets = []
    key = []
    for r in rows:
        review_id = hashlib.sha256((run['run_id']+'|'+r['case_id']+'|'+r['variant']).encode()).hexdigest()[:16]
        packets.append({'review_id': review_id, 'messages': r['model']['messages'],
                        'evidence': r['evidence'], 'raw_model_output': r['model']['raw_output'],
                        'validated_decision': r['model']['decision'],
                        'validation_error': r['model']['validation_error'],
                        'review': {'reviewer_id': None, 'evidence_sufficient': None,
                                   'decision_entailed': None, 'unsupported_claim_present': None,
                                   'reviewer_status': None, 'rationale': None}})
        key.append({'review_id': review_id, 'case_id': r['case_id'], 'variant': r['variant'],
                    'authored_expected_status': r['expected_status']})
    atomic_json(output/'review-packets.json', sorted(packets, key=lambda x: x['review_id']))
    atomic_json(output/'review-key.json', key)
    fields = ['variant', 'name', 'cases', 'correct', 'status_agreement',
              'schema_citation_validity', 'uncertainty_rate', 'known_endpoint_recall', 'mean_seconds']
    with (output/'summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(summaries)
    lines = ['# Local model consistency ablation', '',
             'This table reports actual generated responses from the pinned Qwen 1.5B model. '
             'It measures agreement with authored scenario labels, not independent accuracy.', '',
             f"Source: `{record['source_run']}`. Calls: {len(rows)}; reused exact saved inference: {record['resumed_calls']}; newly generated: {record['new_calls']}.", '',
             '| Variant | Cases | Correct | Status agreement | Schema/citation valid | UNCERTAIN | Known endpoint recall | Mean seconds |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in summaries:
        recall = 'N/A' if r['known_endpoint_recall'] is None else f"{r['known_endpoint_recall']:.3f}"
        lines.append(f"| {r['variant']} | {r['cases']} | {r['correct']} | {r['status_agreement']:.3f} | {r['schema_citation_validity']:.3f} | {r['uncertainty_rate']:.3f} | {recall} | {r['mean_seconds']:.2f} |")
    lines += ['', 'Variant definitions:']
    lines += [f"- {r['variant']}: {r['name']}." for r in summaries]
    uncertainty_only = sum(c['status'] == 'UNCERTAIN' for c in contracts.values())/len(contracts)
    best = max(r['status_agreement'] for r in summaries)
    lines += ['', f'An always-UNCERTAIN comparator agrees with {uncertainty_only:.1%} of these authored labels. '
              f'The best observed variant agrees with {best:.1%}.']
    if best <= uncertainty_only:
        lines += ['', '**This pilot does not demonstrate improved consistency classification from the local model or richer evidence.** '
                  'The deterministic rule findings must remain separate from model effectiveness claims.']
    lines += ['', 'Exact evidence quotes and identifiers were checked. Semantic entailment and hallucination '
              'rate have not been independently measured. Validation failures are retained as UNCERTAIN. '
              'Loading-only failures are excluded, including the historical run marked EXCLUDED.json.', '',
              'The cases are correlated, the endpoint labels are incomplete, and the graph contains declared '
              'baseline traces. H is scripted investigation. I changes temporal context and rules together. '
              'Per-call timings retain their original measurements for reused calls; cold-load cost is not '
              'balanced between arms. No statistical significance claim is made.', '',
              'See `docs/ABLATION_PROTOCOL.md` and the raw rows for prompts, evidence, full responses, '
              'validation errors, tokens, model revision and per-call timing. '
              '`review-packets.json` contains unfilled review fields and omits variant names and '
              'authored expected labels; `review-key.json` preserves the mapping separately. '
              'These are annotation materials, not completed independent validation.', '']
    (output/'RESULTS.md').write_text('\n'.join(lines))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    x = np.arange(len(summaries))
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, field, label, color in [(-.24, 'status_agreement', 'Status agreement', '#28685D'),
                                       (0, 'schema_citation_validity', 'Schema/citation validity', '#5979AA'),
                                       (.24, 'uncertainty_rate', 'UNCERTAIN rate', '#C19B54')]:
        ax.bar(x+offset, [r[field] for r in summaries], width=.23, label=label, color=color)
    ax.set(xticks=x, xticklabels=list('EFGHI'), ylim=(0, 1.10), ylabel='Fraction of 12 authored cases',
           xlabel='Variant (see protocol)', title='Pinned Qwen consistency pilot: actual 60-call results')
    ax.axhline(uncertainty_only, color='#555555', linewidth=.8, linestyle='--')
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(output/'comparison.png', dpi=180, bbox_inches='tight')
    fig.savefig(output/'comparison.pdf', bbox_inches='tight')
    plt.close(fig)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()

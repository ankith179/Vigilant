"""Build auditable tables and scientific figures from saved experiments only.

Default execution requires all four frozen RAG datasets. --allow-partial makes
an explicitly incomplete report and never substitutes a score for missing work.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_results import audit

RUNS = {
    'lexical': 'experiments/retrieval/20261006T020645-ee4c5e32/results.json',
    'semantic': 'experiments/retrieval/20261006T021326-432d54b3/results.json',
    'graph': 'experiments/retrieval/20261006T142659-bc349a3f/results.json',
    'ranker': 'experiments/ranker/20261006T142709-dea10c63/results.json',
    'changebench': 'experiments/changebench/20261006T143016-f81c6507/results.json',
    'ablation': 'experiments/ablation/20261006T194639-30694b4d/results.json',
    'pipeline': 'experiments/pipeline/20261006T195007-e56e6b8d/results.json',
    'safa': 'experiments/safa/20261006T142403-c681a243/results.json',
}
DATASETS = ['SMOS', 'iTrust', 'eTour_en', 'RTMX-module-valid']
LABELS = {'tfidf': 'TF-IDF', 'bm25': 'BM25', 'embedding': 'MiniLM', 'hybrid': 'Hybrid',
          'hybrid_kg': 'Hybrid + KG', 'hybrid_rag_top5': 'Hybrid + RAG'}
METRICS = ['precision', 'recall', 'f1', 'mrr', 'map', 'recall_at_1', 'recall_at_5', 'recall_at_10', 'ndcg_at_10']


def read(path):
    return json.loads((ROOT / path).read_text())


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(value) for value in row) + ' |' for row in rows])


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def collect(allow_partial=False):
    verified = audit()
    selected = dict(RUNS)
    results = []
    for key in ('lexical', 'semantic', 'graph'):
        for row in read(RUNS[key])['results']:
            results.append({**row, 'source_run': RUNS[key]})
    missing = []
    rag = []
    observation_audit_path = ROOT / 'reports/verification/rag-observations-audit.json'
    observation_audits = {d['dataset']: d for d in json.loads(observation_audit_path.read_text())['datasets']} if observation_audit_path.exists() else {}
    for name in DATASETS:
        pointer = ROOT / 'experiments/rag-trace-partial' / (name + '-complete.json')
        if not pointer.exists():
            missing.append(name)
            continue
        completion = json.loads(pointer.read_text())
        path = completion['result_path']
        result = read(path)['results'][0]
        assert result['dataset'] == name and result['status'] == 'COMPLETED'
        assert result['dataset_fingerprint'] == completion['dataset_fingerprint']
        assert result['protocol_version'] == 'rag-trace-v2-frozen-2026-10-06'
        assert len(result['calls']) == completion['linked_queries']
        results.append({**result, 'source_run': path})
        selected['rag_' + name] = path
        counts = result['candidate_status_counts']
        observation_audit = observation_audits.get(name, {})
        strict_rate = (observation_audit.get('strict_schema_valid_rate')
                       if observation_audit.get('verified_observations') == result['linked_queries']
                       and observation_audit.get('dataset_fingerprint') == result['dataset_fingerprint'] else None)
        rag.append({'dataset': name, 'queries': result['linked_queries'],
                    'schema_valid_rate': result['schema_valid_rate'],
                    'strict_schema_valid_rate': strict_rate,
                    'changed_rankings': result['changed_query_rankings'],
                    'supported': counts.get('SUPPORTED', 0), 'unsupported': counts.get('UNSUPPORTED', 0),
                    'uncertain': counts.get('UNCERTAIN', 0),
                    'mean_generation_seconds': statistics.mean(c['seconds'] for c in result['calls']),
                    'semantic_grounding': None, 'hallucination_rate': None,
                    'source_run': path})
    if missing and not allow_partial:
        raise RuntimeError('RAG evaluation incomplete: ' + ', '.join(missing))
    stats = []
    for name in DATASETS:
        data = read('data/prepared/' + name + '.json')
        linked = len({q for q, _ in data['links']})
        stats.append({'dataset': name, 'split': data['split'], 'requirements': len(data['sources']),
                      'linked_queries': linked, 'unlinked_excluded': len(data['sources']) - linked,
                      'targets': len(data['targets']), 'links': len(data['links']), 'commit': data['commit']})
    traces = [{'dataset': row['dataset'], 'method': row['method'], 'split': row['split'],
               'queries': row['metrics']['queries'], **{m: row['metrics'][m] for m in METRICS},
               'tp': row['metrics']['tp'], 'fp': row['metrics']['fp'], 'fn': row['metrics']['fn'],
               'source_run': row['source_run']} for row in results]
    bench = read(RUNS['changebench'])
    changes = [{'case': row['case']['id'], 'repository': row['case']['repo'],
                'expected_status': row['case']['status'], 'expected_status_present': row['status_match'],
                'known_affected_recovered': row['affected_metrics']['tp'],
                'known_affected_missed': row['affected_metrics']['fn'],
                'outside_partial_oracle': row['affected_metrics']['fp'],
                'known_affected_recall': row['affected_metrics']['recall'],
                'seconds': row['seconds'], 'base_commit': row['case']['base_commit'],
                'change_commit': row['case']['change_commit']} for row in bench['cases']]
    ablation = read('reports/ablation/summary.json')
    assert ablation['source_sha256'] == hashlib.sha256((ROOT / RUNS['ablation']).read_bytes()).hexdigest()
    pipeline = read(RUNS['pipeline'])
    provenance = {key: {'path': path, 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for key, path in selected.items()}
    return {'status': 'INCOMPLETE_RAG' if missing else 'COMPLETED', 'missing_rag_datasets': missing,
            'datasets': stats, 'traceability': traces, 'rag': rag, 'changebench': changes,
            'ablation': ablation, 'ranker': read(RUNS['ranker']), 'safa': read(RUNS['safa'])['counts'],
            'pipeline': {'tool_stages': len(pipeline['trajectory']),
                         'changed_artifact_records': len(pipeline['changes']['artifacts']),
                         'impact_candidates': len(pipeline['affected_artifacts']),
                         'verified_excerpts': len(pipeline['evidence']), 'rule_findings': len(pipeline['findings']),
                         'model_status': pipeline['model']['decision']['decision'],
                         'model_seconds': pipeline['model']['seconds'], 'metrics': pipeline['metrics']},
            'metric_audit': verified, 'provenance': provenance}


def figures(data, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                         'figure.dpi': 150, 'savefig.dpi': 180})
    methods = list(LABELS)
    colors = ['#718096', '#394b66', '#419b92', '#236d97', '#9e6b35', '#a44258']
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for ax, name in zip(axes.flat, DATASETS):
        rows = {r['method']: r for r in data['traceability'] if r['dataset'] == name}
        present = [method for method in methods if method in rows]
        values = [rows[method]['map'] for method in present]
        bars = ax.bar(range(len(present)), values, color=[colors[methods.index(m)] for m in present], width=.7)
        ax.set_xticks(range(len(present)), [LABELS[m].replace(' + ', '\n+ ') for m in present], fontsize=8)
        ax.set_ylim(0, 1); ax.set_ylabel('MAP'); ax.set_title(name.replace('_en', ' English'))
        ax.bar_label(bars, fmt='%.3f', fontsize=8, padding=3)
        ax.grid(axis='y', alpha=.15); ax.set_axisbelow(True)
    fig.suptitle('Traceability ranking across datasets', fontsize=16)
    for ext in ('png', 'pdf'): fig.savefig(output / ('traceability-map.' + ext))
    plt.close(fig)
    rows = [r for r in data['traceability'] if r['dataset'] == 'eTour_en']
    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    x = np.arange(len(rows))
    for offset, key, label, color in [(-.24, 'precision', 'Precision at 10', '#394b66'),
                                     (0, 'recall', 'Recall at 10', '#419b92'),
                                     (.24, 'f1', 'F1 at 10', '#9e6b35')]:
        ax.bar(x + offset, [r[key] for r in rows], .23, label=label, color=color)
    ax.set_xticks(x, [LABELS[r['method']] for r in rows], fontsize=9)
    ax.set_ylim(0, 1); ax.set_ylabel('Micro-averaged link metric'); ax.legend(frameon=False, ncols=3)
    ax.set_title('eTour English traceability at a fixed cutoff'); ax.grid(axis='y', alpha=.15);ax.set_axisbelow(True)
    for ext in ('png', 'pdf'): fig.savefig(output / ('etour-precision-recall-f1.' + ext))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--allow-partial', action='store_true'); args = parser.parse_args()
    data = collect(args.allow_partial)
    out = ROOT / 'reports/results'; out.mkdir(parents=True, exist_ok=True)
    (out / 'summary.json').write_text(json.dumps(data, indent=2) + '\n')
    for key in ('datasets', 'traceability', 'rag', 'changebench'): write_csv(out / (key + '.csv'), data[key])
    figure_text = ' Figures use completed runs only. Missing methods have no bar.'
    sections = ['# VIGILANT measured results',
                'Status: ' + data['status'] + '. Missing complete RAG datasets: ' + (', '.join(data['missing_rag_datasets']) or 'none') + '.',
                '## Dataset statistics', table(['Dataset', 'Split', 'Requirements', 'Linked queries', 'Targets', 'Links'],
                    [[r[k] for k in ('dataset','split','requirements','linked_queries','targets','links')] for r in data['datasets']]),
                'Only queries with an annotated link contribute to ranking metrics. RTMX uses seven existing test modules and 22 requirements; two missing modules and unresolved function labels prevent a comparable 24-function evaluation.',
                '## Traceability performance', table(['Dataset', 'Method', 'P@10', 'R@10', 'F1@10', 'MRR', 'MAP', 'Macro R@1', 'Macro R@5', 'Macro R@10', 'nDCG@10'],
                    [[r['dataset'], LABELS[r['method']]] + [f'{r[k]:.4f}' for k in METRICS] for r in data['traceability']]),
                'P@10, R@10 and F1@10 are micro-averaged over predicted links. The three Macro R columns average each query\'s recall, and can differ from micro recall. MRR and MAP use the full target ranking. RTMX R@10 is necessarily 1.0 because there are only seven candidates. No cross-dataset pooled superiority claim is made.' + figure_text,
                '## RAG scope',
                table(['Dataset', 'Queries', 'Changed rankings', 'Runtime validation', 'Full schema validation', 'Uncertain candidate judgments', 'Mean generation seconds'],
                    [[r['dataset'], r['queries'], r['changed_rankings'], f"{r['schema_valid_rate']:.4f}",
                      'NOT CHECKED' if r['strict_schema_valid_rate'] is None else f"{r['strict_schema_valid_rate']:.4f}",
                      r['uncertain'], f"{r['mean_generation_seconds']:.2f}"] for r in data['rag']]),
                'The frozen RAG method reviews only five candidates from hybrid retrieval. Only SUPPORTED candidates move forward. Recall at 5 and 10 cannot change from reranking within the first five positions. Prefix excerpts can omit relevant implementations. Valid JSON and known citation IDs do not establish semantic entailment. Partial generation files are not completed dataset evaluations.',
                'Runtime validation is the runner\'s recorded decision check. Full schema validation is a separate audit of every required property, enum and length bound. Neither is a semantic grounding or hallucination score. Generation times retain their original observations across resumes and include cold-load effects where applicable.',
                '## Controlled change analysis', table(['Case','Expected label','Label present','Known hits','Known misses','Outside partial oracle'],
                    [[r[k] for k in ('case','expected_status','expected_status_present','known_affected_recovered','known_affected_missed','outside_partial_oracle')] for r in data['changebench']]),
                'All labels are authored and the affected sets are partial. Outside-oracle predictions are not verified false positives. Expected-status presence is a regression check, not independent classification accuracy. Seeded trace relations evaluate maintenance rather than initial recovery.',
                '## Local model ablation', table(['Variant','Calls','Agreement','Uncertainty','Citation validity','Known endpoint recall','Mean seconds'],
                    [[r['variant'],r['cases']] + [f'{r[k]:.4f}' for k in ('status_agreement','uncertainty_rate','schema_citation_validity','known_endpoint_recall','mean_seconds')] for r in data['ablation']['summary']]),
                'All five variants produce UNCERTAIN for every case. The 0.25 agreement equals always-UNCERTAIN. There is no demonstrated gain in model consistency classification. Five generated responses fail citation validation and become UNCERTAIN. Known endpoint recall describes the partial authored oracle. Independent semantic grounding and hallucination rate remain unmeasured. Cold model loading and resumed calls make these times unsuitable for a causal speed comparison.',
                '## Ranker selection',
                'The trained ranker was rejected by its validation rule: its iTrust MAP did not exceed BM25 MAP 0.3787. eTour test performance was not used to retain it. The fixed 0.15 graph weight is exploratory, not a preregistered confirmatory result.',
                '## Full pipeline and SAFA', json.dumps(data['pipeline'],indent=2),
                'The full API-change pipeline generates 15 rule findings concerning a shared route-renaming cause, not 15 independent confirmed defects. The final local-model decision is UNCERTAIN. SAFA compares artifact-tree versions; it supplies no independent code-consistency accuracy labels.',
                '## Verification and provenance',
                f"Independent recomputation checked {data['metric_audit']['method_rows_verified']} method rows and {data['metric_audit']['per_query_metric_rows_verified']} query metric rows. Original experiment files remain unchanged.",
                table(['Record', 'Immutable input'], [[key, value['path']] for key,value in data['provenance'].items()]),
                'SHA-256 values, raw ranks, exact input populations and unrounded metrics are in summary.json. Historical user-reported results use different policies and are excluded from these comparisons.']
    (out / 'RESULTS.md').write_text('\n\n'.join(sections) + '\n')
    figures(data, out)
    print(data['status'], len(data['traceability']), 'method rows;', len(data['rag']), 'complete RAG datasets')


if __name__ == '__main__': main()

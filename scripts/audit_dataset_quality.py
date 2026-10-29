"""Read-only dataset diagnostics and descriptive ranking intervals; no new inference."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
LATEST = 'experiments/retrieval/20261022T134925-e5822b09/results.json'


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def interval(values):
    rng = random.Random(42)
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(2000))
    return [means[49], means[1949]]


def audit():
    datasets = []; cross = defaultdict(list); comparisons = []
    latest = json.loads((ROOT/LATEST).read_text())
    previous = {}
    for path in sorted((ROOT/'experiments/retrieval').glob('*/results.json')):
        if path.parent.name >= Path(LATEST).parent.name:
            continue
        for row in json.loads(path.read_text()).get('results', []):
            previous[row['dataset'], row['method']] = (path, row)
    for path in sorted((ROOT/'data/prepared').glob('*.json')):
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or 'sources' not in data:
            continue
        gold = defaultdict(set); degrees = Counter(); groups = defaultdict(list)
        for source, target in data['links']:
            gold[source].add(target); degrees[target] += 1
        checked = 0; errors = []; encodings = Counter()
        for side in ('sources', 'targets'):
            for row in data[side]:
                encodings[row.get('encoding', 'unspecified')] += 1
                if row.get('sha256'):
                    raw = ROOT/row['path']
                    if not raw.is_file() or hashlib.sha256(raw.read_bytes()).hexdigest() != row['sha256']:
                        errors.append(row['path'])
                    else:
                        checked += 1
                if side == 'sources':
                    key = normalized(row['text']); groups[key].append(row['id']); cross[key].append([data['name'], row['id']])
        duplicates = [{'ids': ids, 'label_sets_disagree': len({tuple(sorted(gold[i])) for i in ids}) > 1}
                      for text, ids in groups.items() if text and len(ids) > 1]
        sizes = [len(gold[row['id']]) for row in data['sources'] if gold[row['id']]]
        sources = {r['id'] for r in data['sources']}; targets = {r['id'] for r in data['targets']}
        datasets.append({'dataset': data['name'], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_count': len(sources), 'target_count': len(targets), 'links': len(data['links']),
            'duplicate_source_ids': len(data['sources'])-len(sources), 'duplicate_target_ids': len(data['targets'])-len(targets),
            'duplicate_links': len(data['links'])-len(set(map(tuple,data['links']))),
            'dangling_links': [pair for pair in data['links'] if pair[0] not in sources or pair[1] not in targets],
            'duplicate_source_text_groups': duplicates, 'unlinked_sources': sum(not gold[source] for source in sources),
            'orphan_target_fraction': len(targets-set(degrees))/len(targets),
            'link_density': len(data['links'])/(len(sources)*len(targets)), 'largest_target_degrees': degrees.most_common(5),
            'mean_recall_at_10_ceiling': statistics.mean(min(10,n)/n for n in sizes),
            'mean_precision_at_effective_10_ceiling': statistics.mean(min(10,n)/min(10,len(targets)) for n in sizes),
            'raw_hashes_checked': checked, 'raw_hash_errors': errors, 'encodings': dict(encodings),
            'source_text_lengths': {'minimum': min(len(r['text']) for r in data['sources']),
                                    'maximum': max(len(r['text']) for r in data['sources'])}})
        for row in latest['results']:
            if row['dataset'] != data['name']:
                continue
            per = {q['query']: q for q in row['per_query']}
            rprecision = []
            for q, ranking in row['rankings'].items():
                if gold[q]:
                    rprecision.append(len(set(ranking[:len(gold[q])]) & gold[q])/len(gold[q]))
            record = {'dataset':data['name'], 'method':row['method'], 'run':LATEST,
                      'map':row['metrics']['map'], 'r_precision':statistics.mean(rprecision),
                      'map_query_bootstrap_95_interval':interval([q['map'] for q in per.values()])}
            prior = previous.get((data['name'],row['method']))
            if prior:
                old = {q['query']:q for q in prior[1]['per_query']}
                if set(old) == set(per):
                    deltas = [per[q]['map']-old[q]['map'] for q in sorted(per)]
                    record.update({'prior_run':str(prior[0].relative_to(ROOT)), 'paired_map_delta':statistics.mean(deltas),
                                   'paired_map_delta_query_bootstrap_95_interval':interval(deltas)})
            comparisons.append(record)
    ablation = json.loads((ROOT/'experiments/ablation/20261006T194639-30694b4d/results.json').read_text())
    rescored = []
    for variant in sorted({r['variant'] for r in ablation['rows']}):
        rows = [r for r in ablation['rows'] if r['variant'] == variant]
        predictions = [r['predicted_status'] if r['schema_and_citations_valid'] else 'INVALID' for r in rows]
        rescored.append({'variant':variant, 'cases':len(rows), 'invalid':predictions.count('INVALID'),
            'accuracy':sum(p==r['expected_status'] for p,r in zip(predictions,rows))/len(rows),
            'valid_uncertainty_rate':predictions.count('UNCERTAIN')/len(rows)})
    return {'status':'COMPLETED', 'new_inference_calls':0, 'datasets':datasets, 'lexical_comparison':comparisons,
        'cross_dataset_identical_source_text': [ids for text,ids in cross.items() if text and len({i[0] for i in ids})>1],
        'legacy_ablation_rescore':rescored, 'historical_files_modified':False,
        'limitations':['Duplicate text and differing labels require review; neither proves mislabelling.',
            'Unlinked targets and incomplete annotations are not verified negatives.',
            'Query bootstrap intervals (2000 resamples, seed 42) are descriptive; correlated queries violate independence.',
            'Retrieval MAP and R-precision are not consistency or operation accuracy.',
            'No semantic annotation, license determination, or independent held-out evaluation performed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); result = audit()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'datasets':len(result['datasets']),'comparisons':len(result['lexical_comparison'])}))

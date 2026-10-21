"""Check RAG evidence provenance and saved observations without model inference."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.resume import fingerprint, reusable_completion
from run_rag_trace import DATASETS, PROTOCOL_VERSION, SYSTEM_PROMPT, output_schema, validate_response

BASELINE = 'experiments/retrieval/20261006T021326-432d54b3/results.json'


def strict_schema_issues(raw, aliases):
    """Independently check every constraint in this protocol's small schema."""
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return ['invalid JSON']
    if not isinstance(value, dict):
        return ['root must be object']
    issues = []
    if set(value) != {'statuses', 'evidence_ids', 'reason'}:
        issues.append('missing or additional root properties')
    statuses = value.get('statuses')
    if not isinstance(statuses, dict) or set(statuses) != set(aliases):
        issues.append('missing or additional status properties')
    elif any(v not in ('SUPPORTED', 'UNSUPPORTED', 'UNCERTAIN') for v in statuses.values()):
        issues.append('status outside enum')
    evidence = value.get('evidence_ids')
    if not isinstance(evidence, list):
        issues.append('evidence_ids must be array')
    elif len(evidence) > 6 or any(not isinstance(v, str) or v not in {'E0', *aliases} for v in evidence):
        issues.append('invalid evidence identifier or more than six identifiers')
    if not isinstance(value.get('reason'), str) or len(value['reason']) > 140:
        issues.append('reason must be string of at most 140 characters')
    return issues


def audit(provider_source=None):
    provider_source = Path(provider_source) if provider_source else ROOT / 'llm/providers.py'
    manifest = json.loads((ROOT / 'data/models.json').read_text())
    model, embedding = manifest['llm'], manifest['embedding']
    encoder_id = embedding['model'] + '@' + embedding['revision'] + ';180words;8chunks;mean-normalized'
    baseline = {r['dataset']: r for r in json.loads((ROOT / BASELINE).read_text())['results'] if r['method'] == 'hybrid'}
    datasets = []
    for name in DATASETS:
        prepared = ROOT / 'data/prepared' / (name + '.json')
        data = json.loads(prepared.read_text())
        queries = {q['id']: q for q in data['sources']}
        targets = {t['id']: t for t in data['targets']}
        truth = {q for q, _ in data['links']}
        dataset_fp = fingerprint({
            'protocol': PROTOCOL_VERSION, 'dataset': name,
            'prepared_sha256': hashlib.sha256(prepared.read_bytes()).hexdigest(),
            'model': {k: model[k] for k in ('model', 'revision', 'dtype')},
            'embedding': encoder_id,
            'provider_source_sha256': hashlib.sha256(provider_source.read_bytes()).hexdigest(),
            'retrieval': 'hybrid RRF(k=60)', 'candidate_count': 5,
            'requirement_prefix_chars': 900, 'candidate_prefix_chars': 1100,
            'system_prompt': SYSTEM_PROMPT,
            'rerank_policy': 'SUPPORTED first; all others preserve full hybrid order',
            'temperature': 0, 'max_new_tokens': 220,
        })
        checked, generated_invalid, excluded_runtime, schema_errors = [], [], [], []
        for qid in sorted(truth):
            path = ROOT / 'experiments/rag-trace-partial' / (name + '-' + hashlib.sha256(qid.encode()).hexdigest()[:14] + '.json')
            if not path.exists():
                continue
            row = json.loads(path.read_text())
            if not row.get('inference_executed'):
                excluded_runtime.append(qid)
                continue
            aliases = {f'A{i+1}': tid for i, tid in enumerate(baseline[name]['rankings'][qid][:5])}
            evidence = [{'id': 'E0', 'type': 'requirement', 'text': queries[qid]['text'][:900]}] + [
                {'id': a, 'type': 'source', 'path': targets[t]['path'], 'text': targets[t]['text'][:1100]}
                for a, t in aliases.items()]
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': json.dumps(evidence, ensure_ascii=False)}]
            call_fp = fingerprint({'dataset_fingerprint': dataset_fp, 'query_id': qid,
                                   'aliases': aliases, 'schema': output_schema(aliases), 'messages': messages})
            assert row['dataset'] == name and row['query_id'] == qid, (name, qid, 'identity')
            assert row['aliases'] == aliases, (name, qid, 'candidate ranking differs from saved hybrid baseline')
            assert row['dataset_fingerprint'] == dataset_fp, (name, qid, 'dataset configuration')
            assert row['protocol_version'] == PROTOCOL_VERSION, (name, qid, 'protocol')
            assert reusable_completion(row, messages, model, call_fp), (name, qid, 'evidence/model/fingerprint mismatch')
            issues = strict_schema_issues(row['raw_output'], aliases)
            if issues:
                schema_errors.append({'query_id': qid, 'issues': issues})
            try:
                parsed = validate_response(row['raw_output'], aliases)
            except (ValueError, TypeError, KeyError):
                assert row['validation_error'], (name, qid, 'unrecorded response error')
                assert all(x == 'UNCERTAIN' for x in row['decision']['statuses'].values())
                generated_invalid.append(qid)
            else:
                assert row['validation_error'] is None and row['decision'] == parsed, (name, qid, 'decision/raw output mismatch')
            checked.append({'query_id': qid, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'raw_output_sha256': hashlib.sha256(row['raw_output'].encode()).hexdigest(),
                            'decision_sha256': fingerprint(row['decision'])})
        completion = ROOT / 'experiments/rag-trace-partial' / (name + '-complete.json')
        if completion.exists():
            pointer = json.loads(completion.read_text())
            final = json.loads((ROOT / pointer['result_path']).read_text())['results'][0]
            assert final['dataset_fingerprint'] == dataset_fp
            records = {r['query_id']: r for r in checked}
            assert set(records) == truth and len(final['calls']) == len(truth)
            assert {c['query_id'] for c in final['calls']} == truth
            for call in final['calls']:
                record = records[call['query_id']]
                assert hashlib.sha256(call['raw_output'].encode()).hexdigest() == record['raw_output_sha256']
                assert fingerprint(call['decision']) == record['decision_sha256']
        datasets.append({'dataset': name, 'expected_queries': len(truth), 'verified_observations': len(checked),
                         'generated_invalid_queries': generated_invalid, 'excluded_runtime_queries': excluded_runtime,
                         'strict_schema_errors': schema_errors,
                         'strict_schema_valid_rate': 1 - len(schema_errors) / len(checked) if checked else None,
                         'dataset_fingerprint': dataset_fp, 'observations': checked})
    return {'status': 'PASS', 'protocol': PROTOCOL_VERSION,
            'provider_source': str(provider_source),
            'provider_source_sha256': hashlib.sha256(provider_source.read_bytes()).hexdigest(),
            'verified_observations': sum(d['verified_observations'] for d in datasets),
            'scope': 'Saved hybrid top-five candidates, exact prepared evidence prefixes, prompt/schema/configuration fingerprints, raw output and decision agreement. Does not establish semantic entailment or final accuracy for incomplete datasets.',
            'datasets': datasets}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', default='reports/verification/rag-observations-audit.json')
    parser.add_argument('--provider-source', type=Path, help='Exact archived provider source used for the saved run; mismatches still fail.')
    args = parser.parse_args()
    report = audit(args.provider_source); path = ROOT / args.output; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'], report['verified_observations'], 'verified actual generations')

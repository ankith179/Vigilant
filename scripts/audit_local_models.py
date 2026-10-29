"""Audit saved local decisions without an Ollama server or new inference."""
from pathlib import Path
import argparse
import json
import math
import sys
import importlib.util
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.resume import fingerprint


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(directory, sources):
    # Validate the archive before loading its trusted project code. Replaying with
    # today's prompt would incorrectly reject an unchanged historical observation.
    for config_path in Path(directory).glob('*/configuration.json'):
        config = json.loads(config_path.read_text(encoding='utf-8'))
        for name, expected in config['sources'].items():
            path = Path(name)
            require(not path.is_absolute() and '..' not in path.parts, 'Unsafe source path')
            require(fingerprint((Path(sources)/path).read_text(encoding='utf-8')) == expected,
                    'Frozen source mismatch: '+name)
    with frozen_contract(Path(sources)) as modules:
        return audit_observations(directory, sources, modules)


@contextmanager
def frozen_contract(sources):
    names = ['ingestion.models', 'llm.context', 'llm.providers', 'llm.ollama',
             'scripts.evaluate_local_models']
    original = {name: sys.modules.get(name) for name in names}
    original_path = sys.path[:]
    loaded = {}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, sources/(name.replace('.', '/')+'.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
        yield loaded
    finally:
        sys.path[:] = original_path
        for name, module in original.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def audit_observations(directory, sources, modules):
    LLMProvider = modules['llm.providers'].LLMProvider
    OllamaProvider = modules['llm.ollama'].OllamaProvider
    metrics = modules['scripts.evaluate_local_models'].metrics
    validate_dataset = modules['scripts.evaluate_local_models'].validate_dataset
    directory, sources = Path(directory), Path(sources)
    data = json.loads((directory/'dataset.json').read_text(encoding='utf-8'))
    cases = {c['case_id']: c for c in data['cases']}
    models = []
    for config_path in sorted(directory.glob('*/configuration.json')):
        folder = config_path.parent
        config = json.loads(config_path.read_text(encoding='utf-8'))
        validate_dataset(data, [config['model']['model']])
        require(folder.name == fingerprint(config), 'Configuration fingerprint mismatch')
        require(config['dataset_sha256'] == fingerprint(data), 'Dataset fingerprint mismatch')
        for name, expected in config['sources'].items():
            path = Path(name)
            require(not path.is_absolute() and '..' not in path.parts, 'Unsafe source path')
            require(fingerprint((sources/path).read_text(encoding='utf-8')) == expected,
                    'Frozen source mismatch: '+name)
        observed = {}
        for path in sorted(folder.glob('*.json')):
            if path.name in {'configuration.json', 'summary.json', 'last-failure.json'}:
                continue
            row = json.loads(path.read_text(encoding='utf-8'))
            case_id = row['case_id']
            require(case_id in cases and case_id not in observed, 'Unknown or duplicate case')
            case, result = cases[case_id], row['result']
            key = fingerprint({'configuration': config, 'case_id': case_id, 'messages': result['messages']})
            require(row['fingerprint'] == key == path.stem, 'Observation fingerprint mismatch')
            require(bool(result['raw_output']) and result['usage'].get('output_tokens', 0) > 0,
                    'Missing generation output/token record')
            require(result['usage']['local_model'] == config['model'], 'Model identity mismatch')
            require(result['usage'].get('api_cost_usd') == 0, 'Unexpected API cost')

            # Replay only the stored response through the unchanged strict validator.
            class Replay(LLMProvider):
                evidence_budget = 18000
                evidence_limit = 24

                def complete(self, messages):
                    require(messages == result['messages'], 'Saved prompt differs from dataset/context')
                    return result['raw_output'], result['usage']

            replayed = Replay().investigate(case['question'], case['evidence'])
            require(replayed['messages'] == result['messages'], 'Prompt mismatch')
            require(replayed['decision'] == result['decision'], 'Stored decision differs from raw response')
            require(replayed['validation_error'] == result['validation_error'], 'Validation result mismatch')
            if result['usage'].get('citation_policy') == 'selected-alias-enums-v1':
                require(result['usage']['output_schema'] == OllamaProvider.citation_schema(result['messages']),
                        'Citation schema differs from selected evidence')
            observed[case_id] = result
        require(set(observed) == set(cases), 'Incomplete run: no full-dataset accuracy accepted')
        rows = [observed[c['case_id']] for c in data['cases']]
        recomputed = metrics(data['cases'], rows)
        summary = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
        require(summary['status'] == 'COMPLETED', 'Saved run is not completed')
        require(set(summary['metrics']) == set(recomputed), 'Metric fields differ')
        for key, value in recomputed.items():
            saved = summary['metrics'][key]
            equal = math.isclose(saved, value, rel_tol=1e-12, abs_tol=1e-12) if isinstance(value, float) else saved == value
            require(equal, 'Metric mismatch: '+key)
        correct = sum(not r['validation_error'] and r['decision']['decision'] == c['expected_status']
                      for c, r in zip(data['cases'], rows))
        models.append({'model': config['model']['model'], 'digest': config['model']['digest'],
                       'cases': len(rows), 'correct': correct,
                       'valid': sum(not r['validation_error'] for r in rows), 'metrics': recomputed})
    require(bool(models), 'No saved configurations found')
    return {'status': 'PASS', 'new_inference_calls': 0, 'observations': sum(m['cases'] for m in models),
            'models': models, 'scope': 'Saved source/data/prompt fingerprints, raw-response validation and score arithmetic. '
            'No independent semantic review, new inference or held-out accuracy claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--sources', type=Path, required=True, help='Matching frozen source directory')
    args = parser.parse_args()
    print(json.dumps(audit(args.directory, args.sources), indent=2))


if __name__ == '__main__':
    main()

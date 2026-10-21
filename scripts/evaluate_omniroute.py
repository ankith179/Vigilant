"""Bounded, resumable replay of saved evidence; never overwrite the local study.

Default legacy prompts isolate a model/provider change. Expanded prompts are a
separate model+context experiment. Authored labels are not independent ground truth.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm.omniroute import OmniRouteProvider
from llm.providers import LLMProvider
from evaluation.resume import atomic_json

SOURCE = ROOT/'experiments/ablation/20261006T194639-30694b4d/results.json'


class LegacyOmniRoute(OmniRouteProvider):
    prompt_version = 'legacy-six-excerpts-400chars'
    legacy_truncation = True
    investigation_request = LLMProvider.legacy_investigation_request

    def investigate(self, question, evidence):
        return LLMProvider.investigate(self, question, evidence)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', choices=['legacy','expanded'], default='legacy')
    parser.add_argument('--max-calls', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.max_calls <= 60:
        parser.error('--max-calls must be between 1 and 60')
    engine = LegacyOmniRoute() if args.profile == 'legacy' else OmniRouteProvider()
    _, _, model = engine.configuration()
    if model not in {x['id'] for x in engine.models()}:
        raise ValueError('Configured route is not available in the gateway model catalog')
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    identity = {'requested_model': model, 'profile': args.profile, 'prompt_version': engine.prompt_version,
                'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
                'context_source_sha256': hashlib.sha256((ROOT/'llm/context.py').read_bytes()).hexdigest(),
                'provider_source_sha256': hashlib.sha256((ROOT/'llm/omniroute.py').read_bytes()).hexdigest(),
                'validator_source_sha256': hashlib.sha256((ROOT/'llm/providers.py').read_bytes()).hexdigest()}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    folder = ROOT/'experiments/omniroute-evaluation'/key
    folder.mkdir(parents=True, exist_ok=True)
    atomic_json(folder/'configuration.json', identity)
    observations, new_calls = [], 0
    for row in source['rows']:
        target = folder/(row['case_id']+'-'+row['variant']+'.json')
        if target.exists():
            result = json.loads(target.read_text())
        else:
            if new_calls >= args.max_calls:
                break
            messages = row['model']['messages']
            if args.profile == 'legacy':
                # Exact saved prompt, not a reconstruction or a newly tuned one.
                def request(question, evidence, saved=messages):
                    _, selected, aliases, amap = LLMProvider.legacy_investigation_request(engine, question, evidence)
                    return saved, selected, aliases, amap
                engine.investigation_request = request
            question = messages[-1]['content'].split('\nEVIDENCE\n', 1)[0]
            result = engine.investigate(question, row['evidence'])
            new_calls += 1
            if result['validation_error']:
                atomic_json(folder/'last-failure.json', {'case_id':row['case_id'],'variant':row['variant'],
                    'result':result,'excluded_from_accuracy':True})
                print('Stopped on invalid/unavailable response. No automatic retry or fallback.')
                return 2
            # Expected labels enter only after generation, never the prompt.
            result = {'case_id':row['case_id'],'variant':row['variant'],
                      'expected_status':row['expected_status'],'result':result,
                      'correct':result['decision']['decision']==row['expected_status']}
            atomic_json(target,result)
        observations.append(result)
    complete = len(observations) == len(source['rows'])
    summary = {'status':'COMPLETED' if complete else 'PARTIAL_UNSCORED', 'configuration':identity,
               'saved_calls':len(observations),'planned_calls':len(source['rows']), 'new_calls':new_calls,
               'accuracy':sum(x['correct'] for x in observations)/len(observations) if complete else None,
               'uncertainty_rate':sum(x['result']['decision']['decision']=='UNCERTAIN' for x in observations)/len(observations) if complete else None,
               'limitations':['Authored, correlated cases; independent semantic review remains required.',
                              'Expanded profile changes both model and evidence context.',
                              'Free-provider model revisions/availability may change; inspect reported_model per call.']}
    atomic_json(folder/'summary.json',summary)
    print(json.dumps(summary,indent=2))
    return 0 if complete else 75


if __name__ == '__main__':
    raise SystemExit(main())

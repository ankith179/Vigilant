"""Saved-run audit checks use synthetic responses, never model accuracy claims."""
import json
from pathlib import Path
import sqlite3
import pytest
from llm.providers import LLMProvider, uncertain
from scripts.evaluate_local_models import run
from scripts.audit_local_models import audit
from scripts.checkpoint import validate_snapshots
from scripts.restore_checkpoint import restore_database


@pytest.mark.parametrize('damage', [None, 'raw', 'score', 'missing', 'source', 'current-prompt'])
def test_offline_audit_rejects_corruption(tmp_path, damage, monkeypatch):
    identity = {'model': 'fixture', 'digest': 'synthetic-digest'}

    class Fixture(LLMProvider):
        def __init__(self, model):
            pass

        def preflight(self):
            return identity

        def complete(self, messages):
            return uncertain('insufficient',schema_version=2).model_dump_json(), {
                'local_model': identity, 'output_tokens': 10, 'api_cost_usd': 0}

    data = {'split': 'diagnostic', 'cases': [{'case_id': 'one', 'question': 'check',
                                            'evidence': [], 'expected_status': 'UNCERTAIN'}]}
    output = tmp_path/'run'
    output.mkdir()
    (output/'dataset.json').write_text(json.dumps(data))
    run(data, ['fixture'], output, 1, Fixture)
    config = next(output.glob('*/configuration.json'))
    frozen = tmp_path/'frozen'
    root = Path(__file__).resolve().parents[1]
    for name in json.loads(config.read_text())['sources']:
        target = frozen/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root/name).read_bytes())
    if damage in {'raw', 'missing'}:
        observation = next(p for p in config.parent.glob('*.json')
                           if p.name not in {'configuration.json', 'summary.json'})
        if damage == 'missing':
            observation.unlink()
        else:
            row = json.loads(observation.read_text())
            row['result']['raw_output'] = uncertain('tampered').model_dump_json()
            observation.write_text(json.dumps(row))
    elif damage == 'score':
        path = config.parent/'summary.json'
        row = json.loads(path.read_text())
        row['metrics']['accuracy'] = 0.75
        path.write_text(json.dumps(row))
    elif damage == 'source':
        (frozen/'llm/context.py').write_text('changed')
    if damage == 'current-prompt':
        import llm.context as current_context
        def changed_prompt(*args, **kwargs):
            raise AssertionError('The current prompt must not replay historical observations')
        monkeypatch.setattr(current_context, 'request', changed_prompt)
        assert audit(output, frozen)['observations'] == 1
        assert current_context.request is changed_prompt
    elif damage:
        with pytest.raises(ValueError):
            audit(output, frozen)
    else:
        result = audit(output, frozen)
        assert result['observations'] == 1 and result['new_inference_calls'] == 0
        assert result['models'][0]['correct'] == 1


def test_lfs_snapshot_is_rejected_without_overwriting_destination(tmp_path):
    source = tmp_path/'data/snapshots/vigilant.db'
    source.parent.mkdir(parents=True)
    source.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:example\nsize 123\n')
    destination = tmp_path/'live.db'
    destination.write_bytes(b'preserve existing work')
    with pytest.raises(ValueError, match='Git LFS'):
        validate_snapshots(tmp_path)
    with pytest.raises(ValueError, match='Git LFS'):
        restore_database(source, destination)
    assert destination.read_bytes() == b'preserve existing work'
    source.unlink()
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE example(id INTEGER)')
    validate_snapshots(tmp_path)

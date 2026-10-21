from evaluation.resume import reusable_model, reusable_completion, atomic_json, preserve_previous
import json


def test_resume_requires_real_matching_inference():
    identity = {'model': 'model', 'revision': 'pin', 'dtype': 'bfloat16'}
    messages = [{'role': 'user', 'content': 'real evidence'}]
    row = {'model': {'raw_output': '{}', 'messages': messages, 'usage': {
        **identity, 'output_tokens': 2, 'temperature': 0, 'max_new_tokens': 220}}}
    assert reusable_model(row, messages, identity)
    assert not reusable_model(row, [{'role': 'user', 'content': 'changed evidence'}], identity)
    assert not reusable_model(row, messages, {**identity, 'revision': 'other'})
    row['model']['usage']['output_tokens'] = 0
    assert not reusable_model(row, messages, identity)


def test_previous_observation_is_preserved(tmp_path):
    path = tmp_path/'observation.json'
    atomic_json(path, {'raw': 'first'})
    preserve_previous(path)
    atomic_json(path, {'raw': 'second'})
    assert json.loads(next((tmp_path/'previous').glob('*.json')).read_text()) == {'raw': 'first'}
    assert json.loads(path.read_text()) == {'raw': 'second'}


def test_direct_completion_requires_full_fingerprint_match():
    identity = {'model': 'model', 'revision': 'pin', 'dtype': 'bfloat16'}
    messages = [{'role': 'user', 'content': 'evidence'}]
    row = {'raw_output': '{"statuses":{}}', 'messages': messages,
           'call_fingerprint': 'call-v1', 'usage': {
               **identity, 'output_tokens': 4, 'temperature': 0, 'max_new_tokens': 220}}
    assert reusable_completion(row, messages, identity, 'call-v1')
    assert not reusable_completion(row, messages, identity, 'call-v2')
    assert not reusable_completion(row, messages + [{'role': 'user', 'content': 'changed'}], identity, 'call-v1')
    row['usage']['output_tokens'] = 0
    assert not reusable_completion(row, messages, identity, 'call-v1')

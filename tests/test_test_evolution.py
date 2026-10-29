import subprocess
import pytest
from scripts.test_evolution import (candidate_items, candidate_kind, prepare, paths,
                                    read_blobs, score)
from scripts.recover_test_evolution_failures import merge_predictions


def test_no_answers_in_test_evolution_inputs():
    row = {'instance_id': 'p__abcd', 'project': 'p', 'repo': 'owner/repo', 'v_minus_1_commit': 'a' * 40,
           'v0_commit': 'b' * 40, 'labels': ['missing'], 'changed_test_methods': ['SecretTest.answer'],
           'source_patch': 'diff --git a/src/X.java b/src/X.java\n+changed',
           'test_patch': 'diff --git a/test/SecretTest.java b/test/SecretTest.java\n+answer'}
    inputs, gold = prepare([row])
    assert 'SecretTest' not in str(inputs) and 'evolution_labels' not in inputs[0]
    assert 'full_answer_commit' not in inputs[0] and gold[0]['evolution_labels'] == ['missing']
    with pytest.raises(ValueError): prepare([row, row])
    with pytest.raises(ValueError): paths('diff --git a/../outside b/../outside')


def test_test_file_recall_keeps_new_invalid_and_missing_files():
    gold = [{'case_id': 'a', 'developer_changed_test_files': ['old', 'new']},
            {'case_id': 'b', 'developer_changed_test_files': ['old']},
            {'case_id': 'c', 'developer_changed_test_files': ['old']}]
    pred = [{'case_id': 'a', 'status': 'RANKED', 'candidate_files': ['old'], 'rankings': {'bm25': ['old']}},
            {'case_id': 'b', 'status': 'RANKED', 'candidate_files': ['old'], 'rankings': {'bm25': ['old', 'old']}}]
    r = score(gold, pred, 'bm25')
    assert r['cases'] == 3 and r['invalid_or_missing'] == 2
    assert r['mean_recall_at_5'] == pytest.approx(1 / 6)
    assert r['case_metrics'][0]['unavailable_in_base'] == ['new']
    with pytest.raises(ValueError): score(gold, [{'case_id': 'foreign'}], 'bm25')


def test_batch_blob_read_is_binary_exact(tmp_path):
    subprocess.run(['git', 'init', str(tmp_path)], check=True, capture_output=True)
    raw = b'first\n\x00\xff\nlast\n'
    oid = subprocess.run(['git', '-C', str(tmp_path), 'hash-object', '-w', '--stdin'],
                         input=raw, capture_output=True, check=True).stdout.decode().strip()
    assert read_blobs(tmp_path, [oid, oid]) == {oid: raw}
    assert read_blobs(tmp_path, []) == {}
    with pytest.raises(ValueError): read_blobs(tmp_path, ['HEAD:secret'])


def test_test_candidate_policy_covers_sources_and_safe_resource_paths():
    assert candidate_kind({'file': 'src/test/java/pkg/UnitTest.java', 'eligible': True}) == 'indexed_test_artifact'
    assert candidate_kind({'file': 'src/test/resources/cases/data.txt', 'eligible': True}) == 'indexed_test_artifact'
    assert candidate_kind({'file': 'src/test/resources/fixture.zip', 'eligible': False,
                           'exclusion_reason': 'unsupported-suffix'}) == 'path_only_test_resource'
    assert candidate_kind({'file': 'src/main/resources/runtime.zip', 'eligible': False,
                           'exclusion_reason': 'unsupported-suffix'}) is None
    assert candidate_kind({'file': 'src/test/resources/huge.txt', 'eligible': False,
                           'exclusion_reason': 'size-limit'}) is None
    assert candidate_kind({'file': 'src/main/java/pkg/Unit.java', 'eligible': True}) is None


def test_candidate_items_do_not_index_binary_resource_contents():
    rows = [
        {'file': 'src/test/java/pkg/UnitTest.java', 'eligible': True, 'object_id': 'source'},
        {'file': 'src/test/resources/fixture.zip', 'eligible': False,
         'exclusion_reason': 'unsupported-suffix', 'object_id': 'binary'},
    ]
    items = candidate_items(rows, {'source': b'class UnitTest {}', 'binary': b'PK\x00secret'})
    assert items == [
        {'id': 'src/test/java/pkg/UnitTest.java', 'text': 'src/test/java/pkg/UnitTest.java\nclass UnitTest {}'},
        {'id': 'src/test/resources/fixture.zip', 'text': 'src/test/resources/fixture.zip'},
    ]


def test_recovery_replaces_only_valid_retried_rows():
    original = [{'case_id': 'a', 'status': 'FAILED', 'error': 'temporary'},
                {'case_id': 'b', 'status': 'RANKED', 'rankings': {'rank_rrf': ['old']}}]
    recovered = [{'case_id': 'a', 'status': 'RANKED', 'candidate_policy': 'test-tree-and-resource-v2',
                  'rankings': {'rank_rrf': ['new']}}]
    merged = merge_predictions(original, recovered)
    assert merged[0]['rankings']['rank_rrf'] == ['new']
    assert merged[1] is original[1]
    assert original[0]['status'] == 'FAILED'
    with pytest.raises(ValueError):
        merge_predictions(original, [{'case_id': 'foreign', 'status': 'RANKED'}])

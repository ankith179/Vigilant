import json
from scripts.sync_dashboard import experiment_record


def test_loading_failure_is_not_displayed_as_model_accuracy(tmp_path):
    p = tmp_path/'results.json'
    p.write_text(json.dumps({'kind': 'ablation', 'run_id': 'failed-load',
                            'status': 'COMPLETED', 'summary': [{'status_accuracy': .25}]}))
    (tmp_path/'EXCLUDED.json').write_text(json.dumps({'excluded_from_accuracy_comparison': True,
                                                    'failure_reason': 'No inference executed'}))
    record = experiment_record(p)
    assert record['status'] == 'EXCLUDED_RUNTIME_FAILURE'
    assert record['summary'] is None
    assert record['excluded_from_accuracy_comparison'] is True

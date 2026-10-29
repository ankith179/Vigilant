import json
from hashlib import sha256
from pathlib import Path

import pytest

from tools.measure import (axis_metrics, compare, evaluate, load_gold, load_predictions,
                           mcnemar_exact, score_legacy_single_label)


def test_strict_accuracy_counts_abstentions_and_missing_as_wrong():
    gold = {
        "a": {"repository_id": "r1", "consistency": "INCONSISTENT"},
        "b": {"repository_id": "r1", "consistency": "CONSISTENT"},
        "c": {"repository_id": "r2", "consistency": "INCONSISTENT"},
    }
    predictions = {"a": {"consistency": "UNCERTAIN"},
                   "b": {"consistency": "CONSISTENT"}}
    metrics = axis_metrics(gold, predictions, "consistency", bootstrap_reps=200, seed=7)
    assert metrics["strict_accuracy"] == pytest.approx(1/3)
    assert metrics["decisive_coverage"] == pytest.approx(1/3)
    assert metrics["selective_accuracy"] == 1.0
    assert metrics["missing_predictions"] == 1
    assert metrics["repository_cluster_bootstrap95"] is not None


def test_one_repository_does_not_claim_cluster_interval():
    gold = {"a": {"repository_id": "r1", "consistency": "CONSISTENT"}}
    pred = {"a": {"consistency": "CONSISTENT"}}
    assert axis_metrics(gold, pred, "consistency")["repository_cluster_bootstrap95"] is None


def test_paired_comparison_reports_discordance_and_exact_mcnemar():
    gold = {"a": {"repository_id": "r1", "consistency": "CONSISTENT"},
            "b": {"repository_id": "r2", "consistency": "INCONSISTENT"}}
    first = {"a": {"consistency": "CONSISTENT"}, "b": {"consistency": "CONSISTENT"}}
    second = {"a": {"consistency": "UNCERTAIN"}, "b": {"consistency": "INCONSISTENT"}}
    result = compare(gold, first, second, "consistency", reps=200, seed=3)
    assert (result["A_only_correct"], result["B_only_correct"]) == (1, 1)
    assert result["mcnemar_exact_two_sided"] == mcnemar_exact(1, 1) == 1.0


def test_gold_and_prediction_duplicate_case_ids_are_rejected(tmp_path):
    gold = tmp_path / "gold.csv"
    gold.write_text("case_id,repository_id,split,trace,consistency,test_obligation\n"
                    "x,r1,test,,CONSISTENT,\nx,r2,test,,CONSISTENT,\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case_id"):
        load_gold(gold, "test")
    pred = tmp_path / "pred.jsonl"
    pred.write_text(json.dumps({"case_id": "x", "consistency": "CONSISTENT"})+"\n"+
                    json.dumps({"case_id": "x", "consistency": "INCONSISTENT"})+"\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate case_id"):
        load_predictions(pred)


def test_evaluator_compares_each_system_to_the_declared_baseline():
    gold = {"a": {"repository_id": "r1", "consistency": "CONSISTENT"},
            "b": {"repository_id": "r2", "consistency": "INCONSISTENT"}}
    hist = {"a": {"consistency": "CONSISTENT"}, "b": {"consistency": "CONSISTENT"}}
    new = {"a": {"consistency": "UNCERTAIN"}, "b": {"consistency": "INCONSISTENT"}}
    result = evaluate(gold, {"historical": (hist, "a"*64), "new": (new, "b"*64)},
                      split="test", bootstrap_reps=200, seed=4, baseline="historical")
    assert list(result["paired_comparisons"]) == ["historical_vs_new"]


def test_frozen_historical_diagnostic_known_answer_not_v3_quality():
    root = Path(__file__).resolve().parents[1]
    source = root / "reports/llm-diagnostic-error-analysis/case-analysis.json"
    raw = source.read_bytes()
    assert sha256(raw).hexdigest() == "c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864"
    cases = json.loads(raw)["cases"]
    pairs = [(case["actual_label"], case["expected_label_authored"]) for case in cases]
    result = score_legacy_single_label(pairs)
    mismatches = [cases[i]["case_id"] for i in result["mismatch_indices"]]
    assert (result["correct"], result["n"], result["accuracy"]) == (4, 12, 4/12)
    assert result["macro_f1"] == pytest.approx(0.325)
    assert result["wilson95"][0] == pytest.approx(0.138, abs=0.002)
    assert result["wilson95"][1] == pytest.approx(0.609, abs=0.002)
    assert result["majority_baseline"] == 0.5
    assert mismatches == ["03-code-changed", "04-code-deleted", "05-test-changed",
                          "06-test-deleted", "08-api-changed", "09-backend-changed",
                          "10-consumer-changed", "11-implementation-test-drift"]
    assert sha256(source.read_bytes()).hexdigest() == "c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864"


def test_self_comparison_has_no_discordant_pairs():
    gold = {"a": {"repository_id": "r1", "consistency": "CONSISTENT"},
            "b": {"repository_id": "r2", "consistency": "INCONSISTENT"}}
    predictions = {"a": {"consistency": "CONSISTENT"}, "b": {"consistency": "UNCERTAIN"}}
    result = compare(gold, predictions, predictions, "consistency", reps=200, seed=5)
    assert result["A_only_correct"] == result["B_only_correct"] == 0
    assert result["mcnemar_exact_two_sided"] == 1.0

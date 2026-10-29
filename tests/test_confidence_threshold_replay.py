from copy import deepcopy

from scripts.replay_confidence_thresholds import replay


def case(case_id, label, prediction, confidence):
    return {
        "case_id": case_id,
        "expected_label_authored": label,
        "actual_label": prediction,
        "confidence_raw_uncalibrated": confidence,
    }


def test_threshold_replay_abstains_without_rewriting_saved_decisions():
    cases = [
        case("low-correct", "A", "A", 0.5),
        case("boundary-correct", "A", "A", 0.8),
        case("high-wrong", "B", "A", 0.95),
        case("boundary-correct-2", "B", "B", 0.8),
    ]
    original = deepcopy(cases)

    result = replay(cases, "a" * 64)
    base, at_80, at_95 = result["policies"]

    assert (base["accepted"], base["exact_matches_all_cases"], base["accepted_errors"]) == (4, 3, 1)
    assert (at_80["accepted"], at_80["exact_matches_all_cases"], at_80["accepted_errors"]) == (3, 2, 1)
    assert at_80["correct_predictions_suppressed"] == 1
    assert at_80["errors_eliminated_by_abstention"] == 0
    assert (at_95["accepted"], at_95["exact_matches_all_cases"], at_95["accepted_errors"]) == (1, 0, 1)
    assert at_95["correct_predictions_suppressed"] == 3
    assert at_95["errors_eliminated_by_abstention"] == 0
    assert cases == original

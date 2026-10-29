import copy

import pytest

from evaluation.reviewer_agreement import summarize_reviewer_agreement


def forms_fixture():
    def assessment(case_id, label, links, affected):
        return {
            "case_id": case_id,
            "consistency_label": label,
            "trace_links": links,
            "affected_artifact_ids": affected,
            "rationale": "Illustrative fixture only.",
            "evidence": [{
                "artifact_id": "artifact-" + case_id,
                "commit_id": "a" * 40,
                "file": "src/example.py",
                "content_hash": "hash-" + case_id,
                "start_line": 1,
                "end_line": 1,
            }],
        }

    left = {"reviewer_id": "r1", "independent_of_pipeline_author": True, "cases": [
        assessment("a", "UNCERTAIN", ["x->y"], ["x"]),
        assessment("b", "CONSISTENT", [], []),
    ]}
    right = copy.deepcopy(left)
    right["reviewer_id"] = "r2"
    right["cases"][1]["consistency_label"] = "UNCERTAIN"
    right["cases"][1]["trace_links"] = ["x->z"]
    right["cases"][1]["affected_artifact_ids"] = ["z"]
    return [left, right]


def test_reports_descriptive_label_and_multilabel_agreement_without_claiming_accuracy():
    result = summarize_reviewer_agreement(forms_fixture())
    assert result["status"] == "INTER_RATER_AGREEMENT_DESCRIPTIVE_ONLY"
    assert result["case_count"] == 2
    assert result["consistency_label"]["raw_agreement"] == 0.5
    assert result["consistency_label"]["cohen_kappa"] == pytest.approx(0.0)
    assert result["trace_link_sets"]["reviewer_1_to_reviewer_2_micro"]["f1"] == pytest.approx(2 / 3)
    assert result["affected_artifact_sets"]["reviewer_1_to_reviewer_2_micro"]["f1"] == pytest.approx(2 / 3)
    assert "not accuracy" in result["limitations"][0]


def test_empty_agreement_is_reported_without_inventing_denominator():
    forms = forms_fixture()
    for form in forms:
        for case in form["cases"]:
            case["trace_links"] = []
            case["affected_artifact_ids"] = []
            case["consistency_label"] = "UNCERTAIN"
    result = summarize_reviewer_agreement(forms)
    assert result["trace_link_sets"]["exact_set_agreement_rate"] == 1.0
    assert result["trace_link_sets"]["reviewer_1_to_reviewer_2_micro"]["f1"] is None
    assert result["consistency_label"]["cohen_kappa"] is None
    assert result["consistency_label"]["kappa_status"] == "UNDEFINED_DEGENERATE_MARGINALS"


@pytest.mark.parametrize("mutate", ["duplicate_id", "mismatch", "not_independent", "same_reviewer"])
def test_rejects_incomplete_or_nonindependent_form_pairs(mutate):
    forms = forms_fixture()
    if mutate == "duplicate_id":
        forms[0]["cases"].append(copy.deepcopy(forms[0]["cases"][0]))
    elif mutate == "mismatch":
        forms[1]["cases"].pop()
    elif mutate == "not_independent":
        forms[0]["independent_of_pipeline_author"] = False
    else:
        forms[1]["reviewer_id"] = forms[0]["reviewer_id"]
    with pytest.raises(ValueError):
        summarize_reviewer_agreement(forms)

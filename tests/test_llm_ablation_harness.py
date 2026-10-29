import json

import pytest

from scripts.llm_ablation_harness import (
    build_request,
    DATASET,
    ERROR_REPORT,
    load_frozen_request,
    rank_evidence,
    repository_family,
    verify_prediction,
)
from scripts.evaluate_local_models import validate_dataset


def _evidence(evidence_id, file, commit, **extra):
    return {
        "evidence_id": evidence_id,
        "artifact_id": "artifact-" + evidence_id,
        "file": file,
        "commit": commit,
        "quote": "source text",
        "score": 0.1,
        "retrieval_method": "bm25",
        **extra,
    }


def test_rank_evidence_puts_target_pair_first_and_preserves_candidates():
    base, head = "a" * 40, "b" * 40
    candidates = [
        _evidence("other", "src/other.py", head, score=0.99),
        _evidence("target-base", "src/target.py", base, pair_id="p", retrieval_method="changed-base"),
        _evidence("target-head", "src/target.py", head, pair_id="p", retrieval_method="changed-head"),
        _evidence("test", "tests/test_target.py", head, score=0.8),
    ]

    ranked = rank_evidence(f"Assess consistency around src/target.py. Base {base}; head {head}", candidates)

    assert [item["evidence_id"] for item in ranked[:2]] == ["target-base", "target-head"]
    assert {item["evidence_id"] for item in ranked} == {item["evidence_id"] for item in candidates}


@pytest.mark.parametrize(
    ("question", "family"),
    [
        ("Assess consistency around .rtmx/requirements/a.md. Base x; head y", "rtmx"),
        ("Assess consistency around src/flask/helpers.py. Base x; head y", "Flask"),
        ("Assess consistency around frontend/src/app.tsx. Base x; head y", "fullstack"),
        ("Assess consistency around unknown/file.txt. Base x; head y", "unknown"),
    ],
)
def test_repository_family_comes_from_artifact_path(question, family):
    assert repository_family({"question": question}) == family


def test_prompt_builder_does_not_accept_or_serialize_gold_labels():
    evidence = [_evidence("E1", "src/a.py", "a" * 40)]

    def request_fn(question, rows, budget, limit):
        assert rows == evidence
        return [
            {"role": "system", "content": "baseline"},
            {"role": "user", "content": json.dumps({"question": question, "evidence": rows})},
        ], rows, {}, {}

    messages, *_ = build_request("E1", "question", evidence, request_fn)
    payload = json.loads(messages[-1]["content"])
    assert "expected_status" not in payload
    assert "supplied revision-scoped evidence" in messages[0]["content"]


def test_evidence_verifier_checks_identity_and_revision_scope():
    base, head = "a" * 40, "b" * 40
    candidate = _evidence(
        "E1", "src/a.py", head, start_line=1, end_line=1, content_hash="hash", pair_id=None
    )
    payload = {
        "evidence": [{
            "evidence_id": "E1", "file": candidate["file"], "commit": head,
            "excerpt": candidate["quote"], "start_line": 1, "end_line": 1,
            "content_hash": "hash", "pair_id": None, "retrieval_method": "bm25",
        }]
    }
    result = {
        "messages": [{"role": "user", "content": json.dumps(payload)}],
        "decision": {"evidence_ids": ["E1"], "affected_artifacts": [candidate["artifact_id"]]},
    }
    question = f"Base {base}; head {head}"

    assert verify_prediction(result, question, [candidate])["passed"]
    result["decision"]["evidence_ids"] = ["unknown"]
    assert not verify_prediction(result, question, [candidate])["passed"]


def test_oracle_condition_stays_blocked_without_reviewed_evidence_map():
    with pytest.raises(ValueError, match="reviewed oracle evidence"):
        build_request("E3", "question", [], lambda *args, **kwargs: None)


def test_development_split_is_valid_for_dependent_experiments():
    validate_dataset(
        {"split": "development", "cases": [{"case_id": "dev-1", "expected_status": "UNCERTAIN", "question": "q", "evidence": []}]},
        ["qwen3:8b"],
    )


def test_frozen_baseline_prompt_matches_all_saved_messages():
    request_fn, config = load_frozen_request()
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    saved = json.loads((ERROR_REPORT / "case-analysis.json").read_text(encoding="utf-8"))
    assert config["sources"]["ingestion/models.py"]
    assert len(data["cases"]) == len(saved["cases"]) == 12
    for source_case, saved_case in zip(data["cases"], saved["cases"]):
        messages, *_ = request_fn(source_case["question"], source_case["evidence"], budget=18000, limit=24)
        assert messages == saved_case["prompt_messages"], source_case["case_id"]


def test_frozen_citation_schema_keeps_v1_and_selected_aliases():
    from scripts.llm_ablation_harness import frozen_citation_schema

    request_fn, _ = load_frozen_request()
    messages = [{"role": "user", "content": json.dumps({"evidence": [
        {"evidence_id": "E1", "artifact_id": "A1"}
    ]})}]
    schema = frozen_citation_schema(messages, request_fn)
    assert "schema_version" not in schema["properties"]
    assert schema["properties"]["evidence_ids"]["items"]["enum"] == ["E1"]
    assert schema["properties"]["affected_artifacts"]["items"]["enum"] == ["A1"]

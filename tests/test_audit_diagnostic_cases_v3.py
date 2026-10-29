import importlib.util
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "scripts" / "audit_diagnostic_cases_v3.py"
if not MODULE.exists():
    MODULE = Path(__file__).with_name("audit_diagnostic_cases_v3.py")
SPEC = importlib.util.spec_from_file_location("audit_diagnostic_cases_v3", MODULE)
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


def candidate(case_id, repo="owner/repo", family="family", split="dev", base="a", head="b"):
    return {
        "case_id": case_id, "repository_id": repo, "family": family, "split": split,
        "base_revision": base, "head_revision": head, "path": "src/a.py", "symbol": "f",
        "candidate_category": "CODE_CHANGED", "label_status": "UNREVIEWED_SILVER",
        "expected_trace": None, "expected_consistency": None,
        "expected_test_obligation": None, "expected_authority": None,
        "impact_ground_truth": None, "artifacts": {"code": []},
    }


def test_load_rows_supports_json_array_and_jsonl(tmp_path):
    json_path = tmp_path / "rows.json"
    json_path.write_text('[{"case_id":"a"}]', encoding="utf-8")
    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text('{"case_id":"a"}\n{"case_id":"b"}\n', encoding="utf-8")
    assert len(audit_module.rows(audit_module.load(json_path))) == 1
    assert len(audit_module.rows(audit_module.load(jsonl_path))) == 2


def test_candidate_audit_finds_exact_event_overlap_and_family_split_conflict():
    dev = candidate("a")
    test = candidate("b", split="test")
    result = audit_module.audit({"cases": []}, candidate_pools=[("dev", [dev]), ("test", [test])])
    overlap = result["candidate_pool_overlaps"][0]
    assert overlap["candidate_id_overlap_count"] == 0
    assert overlap["exact_event_overlap_count"] == 1
    assert overlap["repository_revision_path_overlap_count"] == 1
    assert result["candidate_pool_split_contamination"]["families"] == {"family": ["dev", "test"]}


def test_retrieval_array_identity_overlap_is_checked():
    result = audit_module.audit(
        {"cases": [{"case_id": "original", "repository_family": "family"}]},
        retrieval=[{"case_id": "retrieval", "repository": "owner/repo", "base_commit": "a", "full_answer_commit": "b"}],
        candidate_pools=[("pool", [candidate("candidate")])],
        identity_map={"repository_family_case_ids": {"family": ["original"]},
                      "repository_identity_evidence": {"family": {"url": "https://github.com/owner/repo"}}},
    )
    assert result["retrieval_overlap"]["retrieval_case_count"] == 1
    assert result["retrieval_overlap"]["diagnostic_repository_ids_from_identity_map"] == ["owner/repo"]
    assert result["retrieval_overlap"]["diagnostic_repository_overlap_from_identity_map"] == ["owner/repo"]
    assert result["retrieval_overlap"]["candidate_repository_overlap"] == ["owner/repo"]
    assert result["retrieval_overlap"]["candidate_diagnostic_repository_overlap"] == ["owner/repo"]
    assert result["retrieval_overlap"]["candidate_exact_repository_revision_pair_overlap_count"] == 1


def test_unreviewed_candidate_label_assignment_is_reported():
    row = candidate("a")
    row["expected_consistency"] = "CONSISTENT"
    result = audit_module.audit({"cases": []}, candidate_pools=[("pool", [row])])
    assert result["candidate_pools"][0]["nonnull_labels_on_unreviewed"] == [
        {"case_id": "a", "fields": ["expected_consistency"]}
    ]


def test_repeated_candidate_event_keys_are_counted_without_relabelling():
    first = candidate("a")
    second = candidate("b")
    result = audit_module.audit({"cases": []}, candidate_pools=[("pool", [first, second])])
    pool = result["candidate_pools"][0]
    assert pool["repeated_event_key_groups"] == 1
    assert pool["rows_in_repeated_event_keys"] == 2
    assert pool["label_status_counts"] == {"UNREVIEWED_SILVER": 2}

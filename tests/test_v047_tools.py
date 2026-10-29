import json
import subprocess

from ingestion.models import DecisionV3, FactsV3
from tools.export_decision_schemas import export
from tools.mine_cases import mine_repository, _grep, _git_bytes, UnsupportedGitObjectError
import pytest


def test_exported_v3_schemas_match_runtime_models(tmp_path):
    export(tmp_path)
    assert json.loads((tmp_path / "schemas" / "decision-schema-v3.json").read_text()) == DecisionV3.model_json_schema()
    assert json.loads((tmp_path / "schemas" / "facts-v3.json").read_text()) == FactsV3.model_json_schema()


def test_local_commit_miner_marks_candidates_unreviewed_and_keeps_repository_split(tmp_path):
    repo = tmp_path / "private-repo-name"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (repo / "module.py").write_text("def value(): return 1\n")
    git("add", ".")
    git("commit", "-m", "base")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_value.py").write_text("def test_value(): assert value() == 1\n")
    git("add", ".")
    git("commit", "-m", "add test")

    head = git("rev-parse", "HEAD")
    records, sampled = mine_repository(repo, repository_id="example/private", family="example",
                                       split="dev", pinned_rev=head)

    assert records
    assert sampled == 2
    assert all(row["label_status"] == "UNREVIEWED_SILVER" for row in records)
    assert all(row["adjudication"]["status"] == "PENDING" for row in records)
    assert all(row[key] is None for row in records for key in
               ("expected_trace", "expected_consistency", "expected_test_obligation", "expected_authority"))
    assert {row["split"] for row in records} == {"dev"}
    assert all(row["head"] == head for row in records)
    assert str(repo) not in json.dumps(records)


def test_reference_search_detects_test_call_and_ignores_function_definition(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (repo / "module.py").write_text("def value(): return 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_value.py").write_text("def test_value(): assert value() == 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "fixture")
    head = git("rev-parse", "HEAD")
    found = _grep(repo, head, "value", tests_only=True, calls_only=True)
    assert found["status"] == "COMPLETE"
    assert found["paths"] == ["tests/test_value.py"]
    absent = _grep(repo, head, "other", tests_only=True, calls_only=True)
    assert absent == {"status": "COMPLETE", "paths": [], "lines": []}
    assert _git_bytes(repo, head, "module.py") == b"def value(): return 1\n"
    assert _git_bytes(repo, head, "absent.py") is None
    with pytest.raises(subprocess.CalledProcessError):
        _git_bytes(repo, "f" * 40, "absent.py")


def test_gitlink_is_reported_as_unsupported_candidate_not_missing_or_batch_failure(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (repo / "module.py").write_text("def value(): return 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")
    git("update-index", "--add", "--cacheinfo", f"160000,{base},vendor/http-parser")
    git("commit", "-m", "add submodule pointer")
    head = git("rev-parse", "HEAD")

    with pytest.raises(UnsupportedGitObjectError) as caught:
        _git_bytes(repo, head, "vendor/http-parser")
    assert caught.value.object_type == "commit"
    assert caught.value.object_id == base

    rows, sampled = mine_repository(repo, repository_id="example/repo", family="example",
                                    split="dev", pinned_rev=head, max_commits=2)
    assert sampled == 2
    candidate = next(row for row in rows if row["candidate_category"] == "UNSUPPORTED_GIT_OBJECT_CANDIDATE")
    assert candidate["d_ids"] == []
    assert candidate["label_status"] == "UNREVIEWED_SILVER"
    assert all(candidate[key] is None for key in
               ("expected_trace", "expected_consistency", "expected_test_obligation", "expected_authority"))
    base_evidence, head_evidence = candidate["facts"]["evidence"]
    assert base_evidence["presence"] == "ABSENT_AT_REVISION"
    assert head_evidence["presence"] == "PRESENT_UNSUPPORTED_GIT_OBJECT"
    assert head_evidence["object_type"] == "commit"
    assert head_evidence["object_id"] == base
    assert head_evidence["content_hash"] is None

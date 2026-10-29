"""Offline rules-only replay of the authored 12-case development diagnostic."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from pathlib import Path

from agents.assurance import assess_changes
from change_analysis.diff import detect
from database.store import Store
from ingestion.git import revision
from ingestion.service import import_repository


CASE_REVISIONS = re.compile(r"Base ([0-9a-f]{40}); head ([0-9a-f]{40})")


def replay(dataset_path, project_root, output_path):
    dataset_path = Path(dataset_path)
    project_root = Path(project_root)
    raw = dataset_path.read_bytes()
    dataset = json.loads(raw)
    store = Store("sqlite:///:memory:")
    cases = []
    inputs = [{"case_id": case["case_id"], "question": case["question"]} for case in dataset["cases"]]
    for case in inputs:
        match = CASE_REVISIONS.search(case["question"])
        if not match:
            cases.append({"case_id": case["case_id"], "status": "BLOCKED_NO_REVISION_PAIR"})
            continue
        base, head = match.groups()
        repo = project_root / case["case_id"]
        row = {"case_id": case["case_id"], "base_commit": base, "head_commit": head}
        try:
            if revision(repo, base) != base or revision(repo, head) != head:
                raise ValueError("Resolved revision differs from frozen case input")
            project = "diagnostic-" + case["case_id"]
            imported = import_repository(store, repo, project, base)
            head_import = import_repository(store, repo, project, head)
            if imported["repository"] != head_import["repository"]:
                raise ValueError("BASE and HEAD imported under different repository identities")
            repository_id = imported["repository"]
            before = store.artifacts(repository_id, base)
            after = store.artifacts(repository_id, head)
            changes = detect(repo, base, head, before, after)
            assurance = assess_changes(changes, before, after, repo, model="none")
            row.update({"status": "COMPLETED_RULES_ONLY", "inference_calls": 0,
                        "assessments": [{"subject_id": x["subject_id"], "path": x["path"],
                                         "symbol": x["symbol"], "decision": x["rule_decision"]}
                                        for x in assurance["assessments"]],
                        "inference_status": sorted({x["inference_status"] for x in assurance["assessments"]})})
        except Exception as exc:
            if not (repo / ".git").exists():
                row.update({"status": "BLOCKED_NO_GIT_HISTORY",
                            "blocker": "The local case directory has no .git metadata; BASE/HEAD commits cannot be verified or re-imported.",
                            "inference_calls": 0})
            else:
                row.update({"status": "FAILED", "error_type": type(exc).__name__,
                            "error": str(exc)[:500], "inference_calls": 0})
        cases.append(row)
    result = {"schema_version": "v047-rules-only-replay-v1",
              "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "cohort": "AUTHORED_12_CASE_DEVELOPMENT_REGRESSION",
              "dataset_sha256": sha256(raw).hexdigest(),
              "pipeline": "current deterministic V3 rules; model=none",
              "labels_loaded_into_pipeline": False,
              "inference_calls": 0,
              "cases": cases,
              "accuracy": "NOT_MEASURED: authored expected_status is a legacy mixed-axis label; no valid V3 per-axis adjudicated gold labels exist"}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="experiments/local-model-comparison/citation-fix-20261021/dataset.json")
    parser.add_argument("--repositories", default="data/changebench")
    parser.add_argument("--output", default="reports/v047/rules-only-diagnostic-replay.json")
    args = parser.parse_args()
    result = replay(args.dataset, args.repositories, args.output)
    print(json.dumps({"status_counts": {status: sum(x["status"] == status for x in result["cases"])
                                      for status in sorted({x["status"] for x in result["cases"]})},
                      "case_count": len(result["cases"]), "inference_calls": 0,
                      "accuracy": result["accuracy"], "output": args.output}, indent=2))


if __name__ == "__main__":
    main()

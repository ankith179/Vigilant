"""Exploratory replay of raw model confidence cutoffs; never changes decisions."""
import argparse
import hashlib
import json
from pathlib import Path


def replay(cases, source_sha256):
    labels = sorted({case["expected_label_authored"] for case in cases}
                    | {case["actual_label"] for case in cases})
    policies = [("A_existing_no_confidence_cutoff", None),
                ("B_exploratory_0.80", 0.80),
                ("C_exploratory_0.95", 0.95)]
    results = []
    for name, threshold in policies:
        rows = []
        for case in cases:
            confidence = case["confidence_raw_uncalibrated"]
            accepted = threshold is None or confidence >= threshold
            prediction = case["actual_label"] if accepted else "ABSTAIN_REVIEW_REQUIRED"
            rows.append({
                "case_id": case["case_id"],
                "authored_label": case["expected_label_authored"],
                "original_prediction": case["actual_label"],
                "raw_confidence": confidence,
                "accepted": accepted,
                "policy_prediction": prediction,
                "original_match": case["actual_label"] == case["expected_label_authored"],
                "policy_match": accepted and case["actual_label"] == case["expected_label_authored"],
            })
        n = len(rows)
        accepted_rows = [row for row in rows if row["accepted"]]
        correct = sum(row["policy_match"] for row in rows)
        errors = sum(row["accepted"] and not row["original_match"] for row in rows)
        abstentions = n - len(accepted_rows)
        matrix_labels = labels + ["ABSTAIN_REVIEW_REQUIRED"]
        matrix = {truth: {pred: 0 for pred in matrix_labels} for truth in labels}
        for row in rows:
            matrix[row["authored_label"]][row["policy_prediction"]] += 1
        results.append({
            "policy": name,
            "threshold": threshold,
            "comparison": ">= threshold; below threshold becomes abstain/review in this replay only" if threshold is not None else "no cutoff; preserve saved prediction",
            "n": n,
            "exact_matches_all_cases": correct,
            "authored_label_accuracy_all_cases": correct / n if n else None,
            "accepted": len(accepted_rows),
            "coverage": len(accepted_rows) / n if n else None,
            "accepted_correct": correct,
            "accepted_errors": errors,
            "selective_accuracy": correct / len(accepted_rows) if accepted_rows else None,
            "selective_risk": errors / len(accepted_rows) if accepted_rows else None,
            "abstentions": abstentions,
            "errors_eliminated_by_abstention": sum(not r["original_match"] and not r["accepted"] for r in rows),
            "correct_predictions_suppressed": sum(r["original_match"] and not r["accepted"] for r in rows),
            "confusion_matrix_authored_labels": matrix,
            "cases": rows,
        })
    return {
        "schema_version": 1,
        "experiment": "offline_raw_confidence_threshold_replay",
        "source_sha256": source_sha256,
        "label_source": "authored diagnostic labels; dependent and correlated, not independent ground truth",
        "new_model_calls": 0,
        "confidence_semantics": "raw model-reported confidence; uncalibrated",
        "below_threshold_action": "ABSTAIN_REVIEW_REQUIRED in replay output only; original prediction/evidence retained",
        "policies": results,
        "limitations": [
            "A high raw confidence does not establish correctness.",
            "The 12 authored cases are not independent ground truth.",
            "This replay changes only the acceptance/abstention mask; it does not rerun or relabel model predictions.",
            "No production decision threshold is created or changed.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("reports/llm-diagnostic-error-analysis/case-analysis.json"))
    parser.add_argument("--output", type=Path, default=Path("experiments/confidence-threshold-20261027/results.json"))
    args = parser.parse_args()
    raw = args.input.read_bytes()
    source = json.loads(raw.decode("utf-8"))
    if source.get("baseline", {}).get("correct") != 4 or len(source.get("cases", [])) != 12:
        raise ValueError("Expected the preserved 12-case authored diagnostic baseline")
    result = replay(source["cases"], hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite prior experiment output: {args.output}")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({p["policy"]: {k: p[k] for k in (
        "n", "exact_matches_all_cases", "authored_label_accuracy_all_cases", "accepted",
        "coverage", "accepted_errors", "selective_risk", "abstentions",
        "errors_eliminated_by_abstention", "correct_predictions_suppressed")}
        for p in result["policies"]}, indent=2))


if __name__ == "__main__":
    main()

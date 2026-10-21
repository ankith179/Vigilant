"""Render the four completed, audited RAG comparisons without new inference."""
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("SMOS", "iTrust", "eTour_en", "RTMX-module-valid")
METRICS = {
    "precision": "Precision@10", "recall": "Micro Recall@10", "f1": "F1@10",
    "mrr": "MRR", "map": "MAP", "ndcg_at_10": "nDCG@10",
    "recall_at_1": "Macro Recall@1", "recall_at_5": "Macro Recall@5",
    "recall_at_10": "Macro Recall@10",
}


def main():
    audit = json.loads((ROOT / "reports/verification/rag-observations-audit.json").read_text())
    if audit["status"] != "PASS":
        raise ValueError("Run the observation audit successfully before reporting")
    checked = {row["dataset"]: row for row in audit["datasets"]}
    summaries = []
    reports = []
    for name in DATASETS:
        pointer = json.loads((ROOT / "experiments/rag-trace-partial" / f"{name}-complete.json").read_text())
        path = ROOT / pointer["result_path"]
        payload = json.loads(path.read_text())
        row = payload["results"][0]
        verified = checked[name]
        if not (row["status"] == "COMPLETED" and row["dataset"] == name
                and row["dataset_fingerprint"] == pointer["dataset_fingerprint"] == verified["dataset_fingerprint"]
                and len(row["calls"]) == row["linked_queries"] == verified["verified_observations"] == verified["expected_queries"]):
            raise ValueError(f"Incomplete or mismatching result: {name}")
        baseline = row["baseline_metrics"]
        metrics = row["metrics"]
        base_queries = {q["query"]: q for q in row["baseline_per_query"]}
        query_deltas = [{"query": q["query"], **{key: q[key] - base_queries[q["query"]][key]
                         for key in ("map", "mrr", "ndcg_at_10")}} for q in row["per_query"]]
        mean_seconds = statistics.mean(call["seconds"] for call in row["calls"])
        summary = {
            "dataset": name, "queries": row["linked_queries"],
            "source_run": pointer["result_path"], "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "baseline_metrics": baseline, "rag_metrics": metrics,
            "metric_deltas": {key: metrics[key] - baseline[key] for key in METRICS},
            "changed_rankings": row["changed_query_rankings"],
            "candidate_status_counts": row["candidate_status_counts"],
            "mean_generation_seconds": mean_seconds,
            "strict_schema_valid_rate": verified["strict_schema_valid_rate"],
            "per_query_deltas": query_deltas,
            "semantic_grounding": None, "hallucination_rate": None,
        }
        summaries.append(summary)
        lines = [f"# {name} linked-query RAG result", "Status: **COMPLETED and independently audited**.",
                 f"Immutable run: `{pointer['result_path']}`. Split: {row['split']}. "
                 f"Linked queries and actual generations: {row['linked_queries']}.",
                 f"Model: `{payload['model']['model']}` at `{payload['model']['revision']}`. "
                 f"Protocol: `{row['protocol_version']}`.",
                 "## Measured comparison", "| Metric | Hybrid | Hybrid + RAG | Difference |\n| --- | ---: | ---: | ---: |"]
        lines[-1] += "\n" + "\n".join(f"| {label} | {baseline[key]:.6f} | {metrics[key]:.6f} | {metrics[key]-baseline[key]:+.6f} |"
                                      for key, label in METRICS.items())
        lines.extend(["The frozen method only reorders the first five hybrid candidates. Recall@5 and Recall@10 "
                      "cannot change. These are descriptive paired results, with no statistical significance or general superiority claim.",
                      "## Model decisions and runtime",
                      f"Changed rankings: {row['changed_query_rankings']}/{row['linked_queries']}. "
                      f"Candidate judgments: {json.dumps(row['candidate_status_counts'], sort_keys=True)}.",
                      f"Runner schema validity: {row['schema_valid_rate']:.6f}. Independent full-schema validity: "
                      f"{verified['strict_schema_valid_rate']:.6f}. Mean recorded generation time: {mean_seconds:.2f} seconds.",
                      "Generation times retain cold-load and resumed-call effects. Prefix evidence may omit relevant code. "
                      "Valid JSON, known citation IDs and exact source excerpts do not establish semantic entailment. "
                      "Independent grounding review and hallucination measurement remain unmeasured."])
        if name == "RTMX-module-valid":
            lines.append("RTMX has seven candidate test modules and 22 resolved module-level links. Recall@10 is "
                         "necessarily 1.0. This is not a 24-function traceability benchmark; its cutoff scores must not be "
                         "pooled with the larger code corpora.")
        reports.append((name, "\n\n".join(lines) + "\n"))
    out = ROOT / "reports/rag"
    out.mkdir(parents=True, exist_ok=True)
    for name, content in reports:
        (out / f"{name}.md").write_text(content)
    (out / "paired-comparisons.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print("Reported", len(summaries), "audited datasets;", sum(r["queries"] for r in summaries), "actual generations")


if __name__ == "__main__":
    main()

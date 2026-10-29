"""Populate the thesis draft's tables directly from audited immutable results."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submission/output"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] +
                     ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'submission/thesis-content.md')
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    output = args.output.resolve()
    data_path = ROOT / "reports/results/summary.json"
    data = json.loads(data_path.read_text())
    assert data["status"] == "COMPLETED" and not data["missing_rag_datasets"]
    assert sum(row["queries"] for row in data["rag"]) == 251
    assert data["metric_audit"]["status"] == "PASS"
    for source in data["provenance"].values():
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    labels = {"tfidf":"TF-IDF", "bm25":"BM25", "embedding":"MiniLM", "hybrid":"Hybrid",
              "hybrid_kg":"Hybrid + KG", "hybrid_rag_top5":"Hybrid + RAG"}
    replacements = {
        "DATASETS": table(["Dataset", "Split", "Requirements", "Linked", "Targets", "Links"],
                          [[r[k] for k in ["dataset", "split", "requirements", "linked_queries", "targets", "links"]] for r in data["datasets"]]),
        "TRACE": table(["Dataset", "Method", "MAP", "MRR", "nDCG@10", "Micro F1@10"],
                       [[r["dataset"], labels[r["method"]]] + [f"{r[k]:.4f}" for k in ["map", "mrr", "ndcg_at_10", "f1"]] for r in data["traceability"]]),
        "RAG": table(["Dataset", "Queries", "Changed ranks", "Uncertain judgments", "Mean seconds"],
                     [[r["dataset"], r["queries"], r["changed_rankings"], r["uncertain"], f"{r['mean_generation_seconds']:.2f}"] for r in data["rag"]]),
        "CHANGES": table(["Case", "Expected status", "Known hits", "Known misses"],
                         [[r["case"], r["expected_status"].replace("_", " "), r["known_affected_recovered"], r["known_affected_missed"]] for r in data["changebench"]]),
        "ABLATION": table(["Variant", "Calls", "Agreement", "Uncertainty", "Citation validity", "Known endpoint recall"],
                          [[r["variant"], r["cases"]] + [f"{r[k]:.3f}" for k in ["status_agreement", "uncertainty_rate", "schema_citation_validity", "known_endpoint_recall"]] for r in data["ablation"]["summary"]]),
        "PROVENANCE": "\n\n".join(f"- {key}: `{value['path']}`" for key,value in data["provenance"].items()),
        "REFERENCES": (ROOT / "submission/references.md").read_text(),
    }
    content = args.source.read_text()
    for key,value in replacements.items():
        content = content.replace("@" + key + "@", value)
    hits = sum(r["known_affected_recovered"] for r in data["changebench"])
    misses = sum(r["known_affected_missed"] for r in data["changebench"])
    content = content.replace("@KNOWN_TOTAL@",str(hits+misses)).replace("@KNOWN_HITS@",str(hits)).replace("@KNOWN_MISSES@",str(misses))
    output.mkdir(parents=True, exist_ok=True)
    (output / "Thesis-Draft.md").write_text(content)
    cmd = ["pandoc", str(output / "Thesis-Draft.md"), "--standalone", "--toc", "--toc-depth=1", "--number-sections",
           "--top-level-division=chapter", "-V", "documentclass=report", "-V", "fontsize=11pt",
           "-V", "papersize=a4", "-V", "geometry:margin=25mm", "-V", "colorlinks=true", "--resource-path", str(ROOT / "submission")]
    logs = ROOT / "reports/submission"; logs.mkdir(parents=True,exist_ok=True)
    with (logs / "thesis-build.log").open("w") as log:
        subprocess.run(cmd + ["-o", str(output / "Thesis-Draft.tex")], cwd=ROOT / "submission", stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(cmd + ["--pdf-engine=pdflatex", "-o", str(output / "Thesis-Draft.pdf")], cwd=ROOT / "submission", stdout=log, stderr=subprocess.STDOUT, check=True)
    (logs / "thesis-source-provenance.json").write_text(json.dumps({
        "summary_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "status":"DRAFT_FOR_REVIEW", "known_affected_recovered":hits, "known_affected_missed":misses,
        "institutional_format_verified":False, "independent_semantic_review":False,
        "sources":data["provenance"]},indent=2)+"\n")
    print(output / "Thesis-Draft.pdf")


if __name__ == "__main__": main()

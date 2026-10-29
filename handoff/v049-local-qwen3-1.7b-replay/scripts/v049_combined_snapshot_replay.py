"""Snapshot-bound V3 rules + BM25 RAG + local Qwen3 replay; authored regression only."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
from datetime import datetime
import sys
import argparse

WORK = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Users\Ankith\Downloads\vigilant project code")
sys.path.insert(0, str(PROJECT))

from agents.decision_rules import decide, extract_facts
from ingestion.models import Artifact, FactsV3
from ingestion.parsers import extract
from llm.ollama import OllamaProvider
from rag.evidence import evidence, paired_versions, retrieve, verify
from change_analysis.diff import format_change_facts

CASE_DIR = PROJECT / "data" / "changebench"
DB_PATH = PROJECT / "data" / "snapshots" / "changebench.db"
HISTORICAL = PROJECT / "reports" / "llm-diagnostic-error-analysis" / "case-analysis.json"
PREREG006 = WORK / "contract-continuation" / "v047-authored-regression-preregister-006.json"
SOURCE_MANIFEST = WORK / "contract-continuation" / "v047-replay-source-manifest.json"
EXPECTED_HISTORICAL_SHA = "c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864"
SCOPE_BUDGET_PER_CASE = 1  # bounded fast pass; remaining semantic scopes keep the rules result


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(value) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load_revision(db, repository, commit_id):
    rows = db.execute("select payload from artifacts where repository=? and commit_id=?", (repository, commit_id)).fetchall()
    artifacts = []
    for (raw,) in rows:
        payload = json.loads(raw)
        payload.pop("id", None)
        item = Artifact.model_validate(payload)
        if item.repository != repository or item.commit_id != commit_id:
            raise ValueError("Snapshot artifact identity mismatch")
        artifacts.append(item)
    if not artifacts or len({a.artifact_id for a in artifacts}) != len(artifacts):
        raise ValueError("Snapshot revision is empty or has duplicate artifact identities")
    return artifacts


def reparse_metadata(artifacts):
    enriched = list(artifacts)
    parents = {a.file_path: a for a in artifacts if a.artifact_type == "source_file"}
    for path, parent in parents.items():
        parsed = extract(parent.project_id, parent.repository, parent.commit_id, path, parent.content)
        metadata = {(a.artifact_type, a.symbol): a.metadata for a in parsed}
        for i, item in enumerate(enriched):
            m = metadata.get((item.artifact_type, item.symbol)) if item.file_path == path else None
            if m is not None:
                enriched[i] = item.model_copy(update={"metadata": {**m, **item.metadata}})
    return enriched


def artifact_role(a):
    parts = a.file_path.lower().replace("\\", "/").split("/")
    name = parts[-1]
    if a.artifact_type == "requirement":
        return "requirement"
    if a.artifact_type in {"test", "test_method"} or "tests" in parts or name.startswith("test_"):
        return "test"
    if a.artifact_type == "api_caller":
        return "consumer"
    if a.artifact_type in {"api", "function", "method", "source_file"}:
        return "implementation"
    return "unknown"


def prepare_case_context(changes, before, after, query):
    all_artifacts = before + after
    paired = paired_versions(changes, before, after, max_pairs=4)
    for e in paired:
        e["revision_role"] = "HEAD" if e["commit"] == changes["head_commit"] else "BASE"
        a = next(a for a in all_artifacts if a.artifact_id == e["artifact_id"] and a.commit_id == e["commit"])
        e["artifact_role"] = artifact_role(a)
    # Existing BM25 retrieval is the RAG arm. Candidate matches remain candidates, not proof.
    ranked = retrieve(query, after, k=8, max_chars=6000)
    for e in ranked:
        e["revision_role"] = "HEAD"
        a = next(a for a in after if a.artifact_id == e["artifact_id"])
        e["artifact_role"] = artifact_role(a)
    unique = {}
    for e in paired + ranked:
        unique.setdefault(e["evidence_id"], e)
    packet = list(unique.values())
    errors = verify(packet, all_artifacts)
    if errors:
        raise ValueError("Snapshot evidence failed integrity checks: " + "; ".join(errors[:5]))
    return packet, ranked


def prepare_evidence(changes, before, after, facts, base_packet):
    all_artifacts = before + after
    rows = []
    for name in FactsV3.model_fields:
        for source in getattr(facts, name).sources:
            if source.extraction_method == "git_diff_deleted_file":
                continue  # The snapshot copy has no Git blob receipt to independently verify.
            candidates = [a for a in all_artifacts if (a.commit_id, a.file_path, a.content_hash) ==
                          (source.commit_id, source.path, source.content_hash)]
            if not candidates:
                raise ValueError(f"Fact source is not present in exact snapshot: {source.path}")
            excerpts = [evidence(a, source.extraction_method) for a in candidates]
            e = next((item for item in excerpts if item["evidence_id"] == source.evidence_id), None)
            if e is None:
                raise ValueError("Fact source identity differs from exact snapshot excerpt: " +
                    json.dumps({"path": source.path, "method": source.extraction_method,
                                "expected_evidence_id": source.evidence_id,
                                "candidate_evidence_ids": [x["evidence_id"] for x in excerpts]}, ensure_ascii=False))
            if e["start_line"] != source.start_line or e["end_line"] != source.end_line:
                raise ValueError("Fact source line range differs from exact snapshot excerpt")
            e.update(revision_role=source.revision, artifact_role=source.artifact_role)
            rows.append(e)
    unique = {e["evidence_id"]: e for e in base_packet}
    for e in rows:
        unique.setdefault(e["evidence_id"], e)
    packet = list(unique.values())
    errors = verify(packet, all_artifacts)
    if errors:
        raise ValueError("Snapshot fact evidence failed integrity checks: " + "; ".join(errors[:5]))
    return packet


def priority(values, order, fallback):
    present = set(values)
    return next((value for value in order if value in present), fallback)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true", help="validate all snapshot/RAG packets without model generation")
    parser.add_argument("--resume", type=Path, help="resume an incomplete run with unchanged source/model/input hashes")
    args = parser.parse_args()
    if sha(HISTORICAL) != EXPECTED_HISTORICAL_SHA:
        raise SystemExit("STOP: frozen case-analysis.json SHA-256 does not match the expected value")
    prereg = json.loads(PREREG006.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    frozen = {r["case_id"]: r for r in source_manifest["cases"]}
    run_id = args.resume.name if args.resume else "v049-combined-" + datetime.now().strftime("%Y%m%dT%H%M%S")
    out = args.resume.resolve() if args.resume else WORK / run_id
    if not args.resume:
        out.mkdir(parents=True, exist_ok=False)
    elif not (out / "preregistration.json").is_file() or (out / "evaluation.json").exists():
        raise ValueError("Resume requires an incomplete frozen run")
    engine = OllamaProvider("qwen3:1.7b")
    identity = None if args.prepare_only else engine.preflight()
    if not args.prepare_only:
        from v048_runtime import install
        install(engine, out)
    db_digest = sha(DB_PATH)
    source_files = ["agents/decision_rules.py", "agents/assurance.py", "rag/evidence.py", "llm/context_v3.py",
                    "llm/providers.py", "llm/ollama.py", "ingestion/models.py", "ingestion/parsers.py"]
    source_hashes = {name: sha(PROJECT / name) for name in source_files}
    preregistration = {
        "run_id": run_id,
        "condition": "V3_RULES_PLUS_BM25_RAG_PLUS_LOCAL_QWEN3_1_7B_SEMANTIC_RESIDUE",
        "status": "FROZEN_BEFORE_GENERATION",
        "evaluation_population": "12-case development/regression set; authored labels, not independent accuracy",
        "target": "11/12 authored-label agreement under the existing V047 axis projection",
        "model": identity or {"requested": "qwen3:1.7b", "preflight": "NOT_RUN"},
        "generation": {"temperature": 0, "seed": 42, "num_ctx": 8192, "num_predict": 512, "three-vote-and-citation-check": True},
        "runtime": {"keep_alive": "10m", "per_call_cache": True, "runtime_source_sha256": sha(WORK / "v048_runtime.py")},
        "retrieval": {"method": "existing RAG BM25 retrieval on exact HEAD snapshot", "k": 8, "graph": False, "labels_exposed": False},
        "rule_policy": "existing agents.decision_rules V3 decide/apply_llm_guard; rules are not overridden; LLM budget 1 semantic scope per case",
        "scope_budget_per_case": SCOPE_BUDGET_PER_CASE,
        "case_aggregation": prereg["case_scope_aggregation"],
        "label_projection": prereg["label_to_axis_projection"],
        "frozen_case_manifest_sha256": sha(SOURCE_MANIFEST),
        "snapshot_database_sha256": db_digest,
        "historical_case_analysis_sha256_before": sha(HISTORICAL),
        "source_sha256": source_hashes,
        "runner_sha256": sha(Path(__file__)),
        "upstream_git_objects_reverified": False,
    }
    if args.resume:
        saved = json.loads((out / "preregistration.json").read_text(encoding="utf-8"))
        if saved != preregistration:
            raise ValueError("Resume configuration, model, input or source identity changed")
    else:
        atomic_json(out / "preregistration.json", preregistration)
        (out / "raw_outputs.jsonl").write_text("", encoding="utf-8")
        (out / "execution_log.jsonl").write_text("", encoding="utf-8")

    db = sqlite3.connect("file:" + DB_PATH.resolve().as_posix() + "?mode=ro", uri=True)
    db.execute("pragma query_only=on")
    predictions = []
    log_path = out / "execution_log.jsonl"
    raw_path = out / "raw_outputs.jsonl"
    call_count = 0
    try:
        for case_path in sorted(p for p in CASE_DIR.glob("??-*.json") if not p.name.endswith("-report.json")):
            case_id = case_path.stem
            contract = json.loads(case_path.read_text(encoding="utf-8"))
            report_path = case_path.with_name(case_path.stem + "-report.json")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            entry = frozen[case_id]
            if sha(case_path) != entry["input_sha256"] or sha(report_path) != entry["saved_report_sha256"]:
                raise ValueError("Frozen diagnostic input/report hash mismatch: " + case_id)
            if contract["base_commit"] != entry["base_commit"] or contract["change_commit"] != entry["head_commit"]:
                raise ValueError("Frozen revision mismatch: " + case_id)
            repository = report["repository"]
            before = reparse_metadata(load_revision(db, repository, contract["base_commit"]))
            after = reparse_metadata(load_revision(db, repository, contract["change_commit"]))
            changes = report["changes"]
            links = [json.loads(raw) for (raw,) in db.execute(
                "select payload from trace_links where project_id=? and commit_id=?",
                (report["project_id"], contract["change_commit"]))
                if json.loads(raw).get("method") in {"declared", "upstream-rtmx-module-declaration"}]
            change_text = format_change_facts(changes)
            question = (f"Assess semantic consistency for changed artifacts in {contract['file']}. "
                        f"BASE={contract['base_commit']} HEAD={contract['change_commit']}. "
                        "Retrieval candidates are not proof; keep trace and test-obligation dimensions separate.\n"
                        "Change facts (descriptive only):\n" + change_text)
            base_packet, ranked = prepare_case_context(changes, before, after, question)
            # Rebuild case evidence with fact sources for each scope; retrieval itself is fixed per case.
            scopes = []
            model_used = 0
            for row in changes.get("artifacts", []):
                facts = extract_facts(changes, before, after, declared_links=links, subject_id=row["artifact_id"])
                rule = decide(facts)
                packet = prepare_evidence(changes, before, after, facts, base_packet)
                result = {"subject_id": row["artifact_id"], "path": row.get("file"), "symbol": row.get("symbol"),
                          "kind": row.get("kind"), "rule_decision": rule.model_dump(),
                          "decision": rule.model_dump(), "inference_status": "NOT_REQUIRED"}
                if args.prepare_only and rule.needs_llm:
                    result["inference_status"] = "NOT_RUN_PREPARE_ONLY"
                elif rule.needs_llm and model_used < SCOPE_BUDGET_PER_CASE:
                    try:
                        response = engine.investigate_v3(question, packet, facts,
                            head_revision=changes["head_commit"], base_revision=changes["base_commit"],
                            validated_evidence_ids=tuple(e["evidence_id"] for e in packet))
                        call_count += len(response.get("usage", {}).get("per_call", []))
                        model_used += 1
                        result["model"] = response
                        result["decision"] = response["decision"]
                        result["inference_status"] = "COMPLETED" if response.get("inference_requested") else "NOT_REQUESTED"
                        with raw_path.open("a", encoding="utf-8") as stream:
                            stream.write(json.dumps({"case_id": case_id, "subject_id": row["artifact_id"],
                                "raw_outputs": response.get("raw_outputs", []),
                                "raw_confidences": response.get("raw_confidences", []),
                                "citation_checks": response.get("citation_checks", []),
                                "validation_error": response.get("validation_error")}, ensure_ascii=False) + "\n")
                    except Exception as exc:
                        result["inference_status"] = "BLOCKED"
                        result["inference_error"] = type(exc).__name__ + ": " + str(exc)[:500]
                elif rule.needs_llm:
                    result["inference_status"] = "BUDGET_EXHAUSTED"
                scopes.append(result)
                with log_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"case_id": case_id, "subject_id": row["artifact_id"],
                        "inference_status": result["inference_status"], "retrieval_candidates": len(ranked),
                        "verified_packet_excerpts": len(packet), "model_calls_so_far": call_count}, ensure_ascii=False) + "\n")
            aggregation = prereg["case_scope_aggregation"]
            axes = {
                "trace": priority([x["decision"]["trace"] for x in scopes], aggregation["trace_priority"], "UNCERTAIN"),
                "consistency": priority([x["decision"]["consistency"] for x in scopes], aggregation["consistency_priority"], "UNCERTAIN"),
                "test_obligation": priority([x["decision"]["test_obligation"] for x in scopes], aggregation["test_obligation_priority"], "UNVERIFIED"),
            }
            predictions.append({"case_id": case_id, "repository_id": repository,
                "base_commit": contract["base_commit"], "head_commit": contract["change_commit"],
                "input_sha256": sha(case_path), "saved_report_sha256": sha(report_path),
                "retrieval_method": "BM25", "retrieval_candidate_count": len(ranked),
                "model_scopes_used": model_used, "axis_predictions": axes, "scopes": scopes})
            atomic_json(out / "predictions.partial.json", {"run_id": run_id, "completed_cases": len(predictions), "predictions": predictions})
    finally:
        db.close()

    if args.prepare_only:
        if sha(HISTORICAL) != EXPECTED_HISTORICAL_SHA or sha(DB_PATH) != db_digest:
            raise ValueError("Frozen historical diagnostic or snapshot DB changed during preparation")
        atomic_json(out / "prepared_cases.json", {"run_id": run_id, "case_count": len(predictions),
            "cases": [{"case_id": p["case_id"], "retrieval_candidate_count": p["retrieval_candidate_count"],
                       "model_scopes_needed": sum(s["inference_status"] == "NOT_RUN_PREPARE_ONLY" for s in p["scopes"]),
                       "scopes": len(p["scopes"])} for p in predictions],
            "historical_case_analysis_sha256": sha(HISTORICAL), "snapshot_database_sha256": sha(DB_PATH)})
        print(json.dumps({"run_dir": str(out), "prepare_only": True, "cases": len(predictions),
                          "verified_RAG_and_fact_packets": sum(1 for p in predictions if p["scopes"]),
                          "historical_hash_unchanged": sha(HISTORICAL) == EXPECTED_HISTORICAL_SHA}, indent=2))
        return

    # Read authored labels only after all system predictions and raw outputs are saved.
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    gold = {row["case_id"]: row["expected_label_authored"] for row in historical["cases"]}
    comparisons = []
    for prediction in predictions:
        authored = json.loads((CASE_DIR / (prediction["case_id"] + ".json")).read_text(encoding="utf-8"))["status"]
        if authored != gold[prediction["case_id"]]:
            raise ValueError("Authored label cross-check failed")
        mapped = prereg["label_to_axis_projection"][authored]
        predicted = prediction["axis_predictions"][mapped["axis"]]
        comparisons.append({"case_id": prediction["case_id"], "authored_label": authored,
            "axis": mapped["axis"], "expected": mapped["expected_axis_value"], "predicted": predicted,
            "match": predicted == mapped["expected_axis_value"]})
    matches = sum(row["match"] for row in comparisons)
    inference_statuses = [s["inference_status"] for p in predictions for s in p["scopes"] if s["inference_status"] != "NOT_REQUIRED"]
    result = {"run_id": run_id, "condition": preregistration["condition"],
        "evaluation_population": preregistration["evaluation_population"],
        "status": "COMPLETED" if len(predictions) == 12 else "INCOMPLETE",
        "metric": "authored_label_agreement_under_frozen_V047_axis_projection",
        "n": len(comparisons), "matches": matches, "agreement": matches / len(comparisons) if comparisons else None,
        "target": "11/12", "target_met": matches >= 11,
        "pre_registered_model_calls": call_count, "model_scope_budget_per_case": SCOPE_BUDGET_PER_CASE,
        "inference_status_counts": {x: inference_statuses.count(x) for x in sorted(set(inference_statuses))},
        "case_results": comparisons,
        "limitations": ["The 12 cases informed development; result is regression agreement, not generalization or independent accuracy.",
            "Qwen3 receives only one semantic scope per case under a bounded budget; uncapped semantic coverage is not evaluated.",
            "BM25 candidates are verified against immutable snapshot artifacts; upstream Git objects were not reverified.",
            "Authored labels are used only after prediction artifacts are saved; no independent human adjudication is available."]}
    if sha(HISTORICAL) != EXPECTED_HISTORICAL_SHA or sha(DB_PATH) != db_digest:
        raise ValueError("Frozen historical diagnostic or snapshot DB changed during the run")
    result["historical_case_analysis_sha256_after"] = sha(HISTORICAL)
    result["snapshot_database_sha256_after"] = sha(DB_PATH)
    atomic_json(out / "predictions.json", {"run_id": run_id, "predictions": predictions})
    atomic_json(out / "evaluation.json", result)
    (out / "predictions.partial.json").unlink(missing_ok=True)
    atomic_json(WORK / "v049-combined-latest.json", {"run_dir": str(out), **result})
    print(json.dumps({"run_dir": str(out), "status": result["status"], "matches": matches,
        "n": len(comparisons), "agreement": result["agreement"], "target_met": result["target_met"],
        "inference_status_counts": result["inference_status_counts"], "model_calls": call_count}, indent=2))


if __name__ == "__main__":
    main()

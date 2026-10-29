"""Scoped V3 assessments; Git-verified facts precede any optional model calls."""
from ingestion.models import FactsV3
from agents.decision_rules import extract_facts, decide
from rag.evidence import evidence, verify_git
from ingestion.models import digest
from llm.preflight import inspect_local


def _artifact_role(artifact):
    parts = artifact.file_path.lower().replace("\\", "/").split("/")
    name = parts[-1]
    if artifact.artifact_type == "requirement":
        return "requirement"
    if artifact.artifact_type in {"test", "test_method"} or "tests" in parts or name.startswith("test_"):
        return "test"
    if artifact.artifact_type == "api_caller":
        return "consumer"
    if artifact.artifact_type in {"api", "function", "method", "source_file"}:
        return "implementation"
    return "unknown"


def assess_changes(changes, before, after, repo, *, model="none", ollama_model=None,
                   declared_links=(), control=None, max_model_scopes=3, retrieved_evidence=()):
    from llm.providers import provider
    if not 0 <= max_model_scopes <= 3:
        raise ValueError("V3 allows at most three model scopes per investigation")
    rows = changes.get("artifacts", [])
    scopes = []
    for row in rows:
        # File-level comments are assessed once; symbol changes otherwise remain independent.
        file_row = next((f for f in changes["files"] if f["old_path"] == row["file"]), {})
        if row.get("symbol") and file_row.get("change_semantics") == "COMMENT_ONLY":
            continue
        if not row.get("symbol") and file_row.get("change_semantics") != "COMMENT_ONLY":
            if any(r.get("symbol") and r["file"] == row["file"] for r in rows):
                continue
        scopes.append(row)
    results = []; verified = {}; preflight = None; engine = None; model_scopes = 0
    head_by_id = {a.artifact_id: a for a in after}
    rag_candidates = []
    for candidate in (retrieved_evidence if model != "none" else ()):
        if candidate.get("selection_arm") != "retrieval":
            continue
        e = dict(candidate)
        commit = e.get("commit") or e.get("commit_id")
        artifact = head_by_id.get(e.get("artifact_id"))
        if artifact is None or commit != changes.get("head_commit"):
            raise ValueError("RAG evidence is not bound to this exact HEAD snapshot")
        e["commit"] = e["commit_id"] = e["revision"] = commit
        e["path"] = e.get("path") or e.get("file")
        e["revision_role"] = "HEAD"
        e["artifact_role"] = _artifact_role(artifact)
        rag_candidates.append(e)
    if rag_candidates:
        errors = verify_git(rag_candidates, before + after, repo)
        if errors:
            raise ValueError("RAG evidence verification failed: " + str(errors))
    for row in scopes:
        if control: control.check()
        facts = extract_facts(changes, before, after, subject_id=row["artifact_id"], declared_links=declared_links)
        sources = [s for name in FactsV3.model_fields for s in getattr(facts, name).sources]
        ev = []
        for source in sources:
            if source.extraction_method == "git_diff_deleted_file":
                file_row = next((f for f in changes.get("files", [])
                                 if f.get("old_path") == source.path and str(f.get("status", "")).startswith("D")), None)
                if (file_row is None or source.commit_id != changes["head_commit"]
                        or source.content_hash != digest("git-diff-deletion", file_row.get("status"), source.path, file_row.get("patch") or "")
                        or source.evidence_id != digest(source.extraction_method, source.commit_id, source.path, source.content_hash)):
                    raise ValueError("HEAD deletion receipt identity/hash mismatch")
                from ingestion.git import git
                raw = git(repo, "diff", "--name-status", "-z", "-M", changes["base_commit"], changes["head_commit"], "--", source.path, binary=True)
                fields = [x.decode("utf-8", errors="replace") for x in raw.split(b"\0") if x]
                if len(fields) < 2 or not fields[0].startswith("D") or fields[1] != source.path:
                    raise ValueError("Git does not verify this path as deleted at HEAD")
                e = {"evidence_id": source.evidence_id, "artifact_id": source.evidence_id,
                     "repository": str(repo), "project_id": "repository-change", "file": source.path,
                     "path": source.path, "start_line": source.start_line, "end_line": source.end_line,
                     "commit": source.commit_id, "commit_id": source.commit_id, "revision": source.commit_id,
                     "revision_role": "HEAD", "content_hash": source.content_hash,
                     "quote": "Git deletion receipt: path is deleted at HEAD relative to BASE; this is change metadata, not a HEAD source excerpt.",
                     "score": 1.0, "retrieval_method": source.extraction_method,
                     "extraction_method": source.extraction_method, "artifact_role": "implementation"}
            else:
                key = source.path, source.commit_id, source.start_line, source.end_line
                a = next((x for x in before+after if (x.file_path, x.commit_id, x.start_line, x.end_line) == key and x.content_hash == source.content_hash), None)
                if a is None:
                    raise ValueError("Fact source not found in the exact snapshot")
                e = evidence(a, source.extraction_method)
                if source.evidence_id != e["evidence_id"] or source.content_hash != e["content_hash"]:
                    raise ValueError("Fact identity/hash differs from snapshot evidence")
                e["revision_role"] = source.revision
                e["artifact_role"] = source.artifact_role
            if e["evidence_id"] not in {x["evidence_id"] for x in ev}:
                ev.append(e)
        for candidate in rag_candidates:
            if candidate["evidence_id"] not in {x["evidence_id"] for x in ev}:
                ev.append(candidate)
        errors = verify_git([e for e in ev if e.get("extraction_method") != "git_diff_deleted_file"
                             and e.get("selection_arm") != "retrieval"], before+after, repo)
        if errors:
            raise ValueError("V3 fact verification failed: "+str(errors))
        for e in ev: verified.setdefault(e["evidence_id"], e)
        rule = decide(facts)
        result = {"subject_id": row["artifact_id"], "path": row["file"], "symbol": row.get("symbol"),
                  "facts": facts.model_dump(), "rule_decision": rule.model_dump(),
                  "decision": rule.model_dump(), "model": None, "inference_status": "NOT_REQUIRED"}
        if rule.needs_llm:
            result["inference_status"] = "NOT_REQUESTED" if model == "none" else "BUDGET_EXHAUSTED"
            if model != "none" and model_scopes < max_model_scopes:
                if preflight is None:
                    preflight = inspect_local(model, ollama_model or "qwen3:8b")
                if preflight["status"] != "ASSETS_READY":
                    result["inference_status"] = "BLOCKED"
                elif ev:
                    if engine is None:
                        engine = provider(model)
                        if model == "ollama" and ollama_model:
                            from llm.ollama import OllamaProvider
                            engine = OllamaProvider(ollama_model)
                    model_scopes += 1
                    response = engine.investigate_v3(
                        "Assess only unresolved semantic consistency for "+row["file"]+"::"+row.get("symbol", ""),
                        ev, facts, head_revision=changes["head_commit"],
                        base_revision=changes["base_commit"], control=control,
                        validated_evidence_ids=tuple(verified))
                    result.update(model=response, decision=response["decision"], inference_status="COMPLETED")
        results.append(result)
    return {"schema_version": 3, "assessments": results, "evidence": list(verified.values()),
            "preflight": preflight, "model_scopes": model_scopes,
            "max_model_scopes": max_model_scopes, "max_calls_per_scope": 9,
            "rag_candidates_verified": len(rag_candidates),
            "scope_policy": "per-changed-artifact; no cross-scope verdict aggregation",
            "limitations": ["Literal route matches are candidates; dynamic dispatch and runtime compatibility remain unverified.",
                           "Authority and test coverage require approved revision-bound review evidence.",
                           "Model entailment judgments are not independent validation."]}

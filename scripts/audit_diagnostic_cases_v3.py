"""Read-only duplicate, leakage, repository and split audit for evaluation inputs."""
import argparse
import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


LABEL_FIELDS = (
    "expected_trace", "expected_consistency", "expected_test_obligation",
    "expected_authority", "impact_ground_truth",
)


def norm(text):
    # Keep case intact so this audit never normalizes identifiers in source data.
    return " ".join(re.findall(r"[A-Za-z0-9_./-]+", unicodedata.normalize("NFKC", str(text))))


def rows(data):
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        raise ValueError("dataset must be a JSON object, array, or JSONL list")
    for key in ("cases", "inputs", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def load(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def text_fields(row):
    values = [row.get(k, "") for k in (
        "question", "task", "task_type", "target_file", "case_id",
        "candidate_category", "path", "old_path", "symbol", "source_patch",
        "text", "description",
    )]
    for container in ("evidence", "candidate_evidence", "facts"):
        value = row.get(container)
        if isinstance(value, dict):
            value = value.get("evidence", [])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    values.extend(item.get(k, "") for k in ("quote", "text", "snippet", "excerpt"))
    return [str(v) for v in values if isinstance(v, (str, int, float)) and str(v)]


def case_text(row):
    return "\n".join(text_fields(row))


def repo_id(row):
    return row.get("repository_id") or row.get("repository") or row.get("repository_family") or row.get("family")


def event_key(row):
    return (
        repo_id(row), row.get("base_revision") or row.get("base"),
        row.get("head_revision") or row.get("head"), row.get("path"),
        row.get("symbol"), row.get("candidate_category"),
    )


def revision_path_key(row):
    return (repo_id(row), row.get("base_revision") or row.get("base"),
            row.get("head_revision") or row.get("head"), row.get("path"))


def artifact_hashes(row):
    found = set()
    for artifacts in (row.get("artifacts") or {}).values():
        if not isinstance(artifacts, list):
            continue
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("content_hash"):
                found.add(artifact["content_hash"])
    return found


def canonical_repo(value):
    if not value:
        return None
    return str(value).strip().removeprefix("https://github.com/").removesuffix(".git").strip("/")


def case_repo_map(identity_map):
    if not identity_map:
        return {}
    families = identity_map.get("repository_family_case_ids", {})
    evidence = identity_map.get("repository_identity_evidence", {})
    out = {}
    for family, case_ids in families.items():
        item = evidence.get(family, {})
        url = item.get("url") or item.get("remote_url_configured")
        if url:
            canonical = canonical_repo(url)
            out.update({case_id: canonical for case_id in case_ids})
    return out


def audit(dataset, retrieval=None, candidate_pools=(), identity_map=None, retrieval_hash=None):
    data_rows = rows(dataset)
    issues, repo_splits, texts = [], {}, defaultdict(list)
    for row in data_rows:
        cid = row.get("case_id")
        if not cid:
            issues.append({"type": "missing_case_id"})
        repo = repo_id(row)
        split = row.get("split") or (dataset.get("split") if isinstance(dataset, dict) else None)
        if repo and split:
            repo_splits.setdefault(repo, set()).add(split)
        text = norm(case_text(row))
        if text:
            texts[text].append(cid)
    exact = [v for v in texts.values() if len(v) > 1]
    normalized = [(r.get("case_id"), norm(case_text(r))) for r in data_rows]
    near = []
    for i, (a, ta) in enumerate(normalized):
        for b, tb in normalized[i + 1:]:
            if ta and tb and ta != tb:
                score = difflib.SequenceMatcher(None, ta, tb).ratio()
                if score >= 0.92:
                    near.append({"case_ids": [a, b], "similarity": round(score, 4)})

    leakage = []
    for row in data_rows:
        labels = [str(x) for x in row.get("truth", row.get("labels", {})).values() if x] \
            if isinstance(row.get("truth", row.get("labels", {})), dict) else []
        for condition, output in (row.get("predictions") or {}).items():
            prompt = output.get("model_input") or output.get("prompt") if isinstance(output, dict) else None
            found = [label for label in labels if prompt and label in str(prompt)]
            if found:
                leakage.append({"case_id": row.get("case_id"), "condition": condition, "label_strings_found": found})

    retrieval_rows = rows(retrieval) if retrieval is not None else []
    retrieval_repo_ids = {canonical_repo(repo_id(r)) for r in retrieval_rows if repo_id(r)}
    diagnostic_repo_map = case_repo_map(identity_map)
    diagnostic_repo_ids = set(diagnostic_repo_map.values())
    diagnostic_repo_overlap = sorted(diagnostic_repo_ids & retrieval_repo_ids)
    text_overlaps = []
    needles = []
    for row in data_rows:
        for value in text_fields(row):
            candidate = norm(value)
            if len(candidate) >= 80:
                needles.append((row.get("case_id"), candidate))
    for item in retrieval_rows:
        if not isinstance(item, dict):
            continue
        body = norm(" ".join(text_fields(item)))
        for cid, needle in needles:
            if needle in body:
                text_overlaps.append({"diagnostic_case_id": cid, "retrieval_case_id": item.get("case_id"),
                                      "kind": "long_normalized_substring"})

    pool_summaries = []
    all_family_splits, all_repository_splits = defaultdict(set), defaultdict(set)
    for pool_name, pool in candidate_pools:
        current = rows(pool)
        candidate_ids, events, revision_paths, hashes = set(), set(), set(), set()
        event_groups = defaultdict(list)
        complete_event_rows = 0
        families, repositories, splits = defaultdict(set), defaultdict(set), Counter()
        statuses, nonnull_labels = Counter(), []
        did_counts = Counter()
        for row in current:
            cid = row.get("case_id") or row.get("case_candidate_id")
            if cid:
                candidate_ids.add(cid)
            key = event_key(row)
            if all(key):
                events.add(key)
                event_groups[key].append(cid)
                complete_event_rows += 1
            revision_key = revision_path_key(row)
            if all(revision_key):
                revision_paths.add(revision_key)
            repo, family, split = repo_id(row), row.get("family"), row.get("split")
            if family and split:
                families[family].add(split)
                all_family_splits[family].add(split)
            if repo and split:
                repositories[repo].add(split)
                all_repository_splits[repo].add(split)
            if split:
                splits[split] += 1
            statuses[row.get("label_status", "MISSING")] += 1
            did_counts.update(row.get("d_ids") or [])
            hashes.update(artifact_hashes(row))
            if row.get("label_status") == "UNREVIEWED_SILVER":
                filled = [field for field in LABEL_FIELDS if row.get(field) is not None]
                if filled:
                    nonnull_labels.append({"case_id": cid, "fields": filled})
        pool_summaries.append({
            "name": pool_name, "record_count": len(current),
            "repository_ids": sorted({repo_id(r) for r in current if repo_id(r)}),
            "family_counts": dict(Counter(r.get("family") for r in current if r.get("family"))),
            "split_counts": dict(splits), "label_status_counts": dict(statuses),
            "d_id_candidate_counts": dict(did_counts), "nonnull_labels_on_unreviewed": nonnull_labels,
            "repository_split_contamination": {k: sorted(v) for k, v in families.items() if len(v) > 1},
            "repository_id_split_contamination": {k: sorted(v) for k, v in repositories.items() if len(v) > 1},
            "exact_event_keys": len(events), "unique_candidate_ids": len(candidate_ids),
            "complete_event_key_rows": complete_event_rows,
            "rows_missing_event_key_fields": len(current) - complete_event_rows,
            "unique_repository_revision_path_keys": len(revision_paths),
            "repeated_event_key_groups": sum(len(v) > 1 for v in event_groups.values()),
            "rows_in_repeated_event_keys": sum(len(v) for v in event_groups.values() if len(v) > 1),
        })

    pool_overlaps = []
    names = [name for name, _ in candidate_pools]
    for i, (name_a, pool_a) in enumerate(candidate_pools):
        ra = rows(pool_a)
        ids_a = {r.get("case_id") or r.get("case_candidate_id") for r in ra}
        ev_a = {event_key(r) for r in ra if all(event_key(r))}
        paths_a = {revision_path_key(r) for r in ra if all(revision_path_key(r))}
        hashes_a = set().union(*(artifact_hashes(r) for r in ra)) if ra else set()
        for name_b, pool_b in candidate_pools[i + 1:]:
            rb = rows(pool_b)
            ids_b = {r.get("case_id") or r.get("case_candidate_id") for r in rb}
            ev_b = {event_key(r) for r in rb if all(event_key(r))}
            paths_b = {revision_path_key(r) for r in rb if all(revision_path_key(r))}
            hashes_b = set().union(*(artifact_hashes(r) for r in rb)) if rb else set()
            pool_overlaps.append({
                "pool_a": name_a, "pool_b": name_b,
                "candidate_id_overlap_count": len((ids_a - {None}) & (ids_b - {None})),
                "exact_event_overlap_count": len(ev_a & ev_b),
                "repository_revision_path_overlap_count": len(paths_a & paths_b),
                "artifact_content_hash_overlap_count": len(hashes_a & hashes_b),
            })

    candidate_repo_ids = {canonical_repo(repo_id(r)) for _, pool in candidate_pools for r in rows(pool) if repo_id(r)}
    candidate_repo_overlap = sorted(candidate_repo_ids & retrieval_repo_ids)
    candidate_diagnostic_repo_overlap = sorted(candidate_repo_ids & diagnostic_repo_ids)
    candidate_revision_pairs = {
        (canonical_repo(repo_id(r)), r.get("base_revision") or r.get("base"), r.get("head_revision") or r.get("head"))
        for _, pool in candidate_pools for r in rows(pool) if repo_id(r)
    }
    retrieval_revision_pairs = {
        (canonical_repo(repo_id(r)), r.get("base_commit"), r.get("full_answer_commit") or r.get("head_commit"))
        for r in retrieval_rows if repo_id(r)
    }
    diagnostic_revision_pairs = set()
    if identity_map:
        for item in identity_map.get("cases", []):
            canonical = diagnostic_repo_map.get(item.get("case_id"))
            base, head = item.get("base_commit_from_report"), item.get("head_commit_from_report")
            if canonical and base and head:
                diagnostic_revision_pairs.add((canonical, base, head))
    candidate_diagnostic_revision_pairs = candidate_revision_pairs & diagnostic_revision_pairs
    contamination = {k: sorted(v) for k, v in repo_splits.items() if len(v) > 1}
    return {
        "status": "AUDITED_READ_ONLY", "diagnostic_case_count": len(data_rows),
        "dataset_sha256": hashlib.sha256(json.dumps(dataset, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "repository_ids": sorted({repo_id(r) for r in data_rows if repo_id(r)}),
        "exact_duplicate_groups": exact, "near_duplicate_pairs_0_92": near,
        "repository_split_contamination": contamination, "direct_prompt_label_leakage": leakage,
        "label_leakage_scope": "Only explicitly supplied prompt/model_input fields and explicit label dictionaries; absence is not proof of no leakage.",
        "retrieval_overlap": {
            "status": "CHECKED_EXACT_REPOSITORY_AND_TEXT_SCREEN" if retrieval is not None else "NOT_CHECKED_NO_RETRIEVAL_DATASET",
            "retrieval_case_count": len(retrieval_rows), "retrieval_dataset_sha256": retrieval_hash,
            "diagnostic_repository_ids_from_identity_map": sorted(diagnostic_repo_ids),
            "diagnostic_repository_overlap_from_identity_map": diagnostic_repo_overlap,
            "diagnostic_exact_repository_revision_pair_overlap_count": len(diagnostic_revision_pairs & retrieval_revision_pairs),
            "candidate_repository_overlap": candidate_repo_overlap,
            "candidate_diagnostic_repository_overlap": candidate_diagnostic_repo_overlap,
            "candidate_diagnostic_exact_revision_pair_overlap_count": len(candidate_diagnostic_revision_pairs),
            "candidate_exact_repository_revision_pair_overlap_count": len(candidate_revision_pairs & retrieval_revision_pairs),
            "long_normalized_text_substring_pairs": text_overlaps,
            "scope": "Exact repository/revision identity and normalized long-text screen only; no semantic or ancestry inference.",
        },
        "candidate_pools": pool_summaries, "candidate_pool_overlaps": pool_overlaps,
        "candidate_pool_split_contamination": {
            "families": {k: sorted(v) for k, v in all_family_splits.items() if len(v) > 1},
            "repository_ids": {k: sorted(v) for k, v in all_repository_splits.items() if len(v) > 1},
        },
        "candidate_near_duplicate_status": "NOT_MEASURED_NO_RAW_DIFF_HUNKS_IN_CANDIDATE_RECORDS" if candidate_pools else "NOT_APPLICABLE",
        "limitations": [
            "Near-duplicate similarity is a screening signal, not adjudication.",
            "Candidate records contain revision hashes and metadata, not raw diff hunks; semantic near-duplicate screening is not performed.",
            "Repository identity matching is exact after trimming GitHub URL syntax; no aliases, forks, ancestry or mirrors are inferred.",
            "No labels are created or changed by this audit.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--retrieval-dataset", type=Path)
    parser.add_argument("--candidate-pool", type=Path, action="append", default=[])
    parser.add_argument("--identity-map", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = load(args.input)
    retrieval = load(args.retrieval_dataset) if args.retrieval_dataset else None
    candidate_pools = [(p.name, load(p)) for p in args.candidate_pool]
    identity_map = load(args.identity_map) if args.identity_map else None
    result = audit(dataset, retrieval, candidate_pools, identity_map,
                   hashlib.sha256(args.retrieval_dataset.read_bytes()).hexdigest() if args.retrieval_dataset else None)
    result["diagnostic_input_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()
    result["identity_map_sha256"] = hashlib.sha256(args.identity_map.read_bytes()).hexdigest() if args.identity_map else None
    result["audit_run_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    for summary, path in zip(result["candidate_pools"], args.candidate_pool):
        summary["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "diagnostic_cases": result["diagnostic_case_count"],
                      "retrieval_cases": result["retrieval_overlap"]["retrieval_case_count"],
                      "candidate_pools": len(result["candidate_pools"]),
                      "candidate_overlaps": result["candidate_pool_overlaps"]}))


if __name__ == "__main__":
    main()

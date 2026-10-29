"""Strict per-axis evaluation with repository-clustered uncertainty intervals."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random

AXES = {
    "trace": {"LINKED", "BROKEN_TRACE", "MISSING_TRACE", "UNCERTAIN"},
    "consistency": {"CONSISTENT", "INCONSISTENT", "POTENTIAL_INCONSISTENCY", "NO_ASSURANCE_IMPACT", "UNCERTAIN"},
    "test_obligation": {"SATISFIED", "UNSATISFIED", "UNVERIFIED", "NOT_APPLICABLE"},
}
ABSTENTIONS = {"UNCERTAIN", "UNVERIFIED", "<MISSING>"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def wilson(k, n, z=1.959963984540054):
    if not n:
        return None
    p = k / n
    d = 1 + z*z/n
    center = (p + z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [center-half, center+half]


def score_legacy_single_label(pairs):
    """Known-answer arithmetic for historical mixed-label diagnostics only.

    This is not part of the V3 axis evaluator and must not be reported as
    traceability, consistency, independent, or end-to-end quality.
    """
    if not pairs:
        raise ValueError("At least one labeled pair is required")
    truth = [gold for _, gold in pairs]
    correct = sum(pred == gold for pred, gold in pairs)
    labels = sorted(set(truth))
    f1 = []
    for label in labels:
        tp = sum(pred == label and gold == label for pred, gold in pairs)
        fp = sum(pred == label and gold != label for pred, gold in pairs)
        fn = sum(pred != label and gold == label for pred, gold in pairs)
        precision = tp/(tp+fp) if tp+fp else 0.0
        recall = tp/(tp+fn) if tp+fn else 0.0
        f1.append(2*precision*recall/(precision+recall) if precision+recall else 0.0)
    counts = Counter(truth)
    return {"n": len(pairs), "correct": correct, "accuracy": correct/len(pairs),
            "wilson95": wilson(correct, len(pairs)), "macro_f1": sum(f1)/len(f1),
            "macro_f1_label_set": "unique authored gold labels; predicted-only labels are not averaged",
            "majority_baseline": max(counts.values())/len(truth),
            "mismatch_indices": [i for i,(pred,gold) in enumerate(pairs) if pred != gold]}


def cluster_interval(groups, *, reps=2000, seed=11):
    """Percentile interval from repository resampling, retaining every case per draw."""
    if not groups:
        return None
    repos = sorted(groups)
    if len(repos) == 1:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        sampled = [rng.choice(repos) for _ in repos]
        rows = [row for repo in sampled for row in groups[repo]]
        values.append(sum(rows) / len(rows))
    values.sort()
    return [values[int(.025*reps)], values[min(reps-1, int(.975*reps))]]


def load_gold(path, split):
    rows = {}
    seen = set()
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"case_id", "repository_id", "split", *AXES}
        if not reader.fieldnames or not required <= set(reader.fieldnames):
            raise ValueError("Gold CSV must include case_id, repository_id, split, trace, consistency, test_obligation")
        for row in reader:
            case_id = (row.get("case_id") or "").strip()
            if not case_id or case_id in seen:
                raise ValueError("Gold CSV has an empty or duplicate case_id")
            seen.add(case_id)
            if not (row.get("repository_id") or "").strip() or not (row.get("split") or "").strip():
                raise ValueError(f"Gold case {case_id} needs repository_id and split")
            if split and row["split"] != split:
                continue
            cleaned = dict(row)
            for axis, labels in AXES.items():
                value = (row.get(axis) or "").strip()
                if value and value not in labels:
                    raise ValueError(f"Invalid {axis} gold label {value!r} for {case_id}")
                cleaned[axis] = value
            rows[case_id] = cleaned
    if not rows:
        raise ValueError(f"No gold rows for split={split!r}")
    return rows


def load_predictions(path):
    rows = {}
    with open(path, encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            case_id = row.get("case_id")
            if not isinstance(case_id, str) or not case_id.strip() or case_id in rows:
                raise ValueError(f"Prediction line {line_no} has an empty or duplicate case_id")
            for axis, labels in AXES.items():
                value = row.get(axis)
                if value is not None and value not in labels:
                    raise ValueError(f"Invalid {axis} prediction {value!r} for {case_id}")
            rows[case_id] = row
    return rows


def axis_metrics(gold, predictions, axis, *, bootstrap_reps=2000, seed=11):
    cases = [(cid, row, predictions.get(cid, {}).get(axis) or "<MISSING>")
             for cid, row in gold.items() if row.get(axis)]
    if not cases:
        return None
    n = len(cases)
    correct = sum(pred == row[axis] for _, row, pred in cases)
    decisive = [(row, pred) for _, row, pred in cases if pred not in ABSTENTIONS]
    selective_correct = sum(pred == row[axis] for row, pred in decisive)
    truth_counts = Counter(row[axis] for _, row, _ in cases)
    labels = sorted(set(truth_counts) | {pred for _, _, pred in cases})
    per_class = {}
    f1_values = []
    for label in labels:
        tp = sum(pred == label and row[axis] == label for _, row, pred in cases)
        fp = sum(pred == label and row[axis] != label for _, row, pred in cases)
        fn = sum(pred != label and row[axis] == label for _, row, pred in cases)
        precision = tp/(tp+fp) if tp+fp else 0.0
        recall = tp/(tp+fn) if tp+fn else 0.0
        f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0
        per_class[label] = {"precision": precision, "recall": recall, "f1": f1,
                            "support": tp+fn}
        f1_values.append(f1)
    confusion = {g: {p: sum(row[axis] == g and pred == p for _, row, pred in cases)
                     for p in labels} for g in labels}
    groups = defaultdict(list)
    for _, row, pred in cases:
        groups[row["repository_id"]].append(int(pred == row[axis]))
    return {
        "n_adjudicated": n, "correct_strict": correct, "strict_accuracy": correct/n,
        "wilson95_case_level_descriptive": wilson(correct, n),
        "repository_cluster_bootstrap95": cluster_interval(groups, reps=bootstrap_reps, seed=seed),
        "bootstrap_repository_count": len(groups),
        "macro_f1": sum(f1_values)/len(f1_values), "per_class": per_class,
        "confusion_matrix": confusion,
        "majority_baseline": max(truth_counts.values())/n,
        "decisive_coverage": len(decisive)/n,
        "abstention_rate": 1-len(decisive)/n,
        "selective_accuracy": selective_correct/len(decisive) if decisive else None,
        "selective_risk": 1-selective_correct/len(decisive) if decisive else None,
        "missing_predictions": sum(pred == "<MISSING>" for _, _, pred in cases),
        "strict_policy": "UNCERTAIN and missing predictions count incorrect unless UNCERTAIN is the adjudicated gold label; UNVERIFIED is an abstention on test_obligation.",
    }


def per_rule_metrics(gold, predictions, axis):
    grouped = defaultdict(list)
    for case_id, row in gold.items():
        if not row.get(axis):
            continue
        prediction = predictions.get(case_id)
        rule = (prediction or {}).get("rule_id") or "NO_RULE_ID"
        predicted = (prediction or {}).get(axis) or "<MISSING>"
        grouped[rule].append(int(predicted == row[axis]))
    return {rule: {"n": len(values), "correct": sum(values),
                   "strict_accuracy": sum(values)/len(values)}
            for rule, values in sorted(grouped.items())}


def mcnemar_exact(a_only, b_only):
    n = a_only+b_only
    if not n:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(a_only, b_only)+1))/(2**n)
    return min(1.0, 2*tail)


def compare(gold, first, second, axis, *, reps=2000, seed=11):
    rows = [(cid, g, first.get(cid, {}).get(axis) or "<MISSING>",
             second.get(cid, {}).get(axis) or "<MISSING>")
            for cid, g in gold.items() if g.get(axis)]
    a_only = sum(a == g[axis] and b != g[axis] for _, g, a, b in rows)
    b_only = sum(b == g[axis] and a != g[axis] for _, g, a, b in rows)
    groups = defaultdict(list)
    for _, g, a, b in rows:
        groups[g["repository_id"]].append((int(a == g[axis]), int(b == g[axis])))
    delta_groups = {repo: [b-a for a, b in pairs] for repo, pairs in groups.items()}
    interval = None
    if len(groups) > 1:
        repos = sorted(groups)
        rng = random.Random(seed)
        diffs = []
        for _ in range(reps):
            sampled = [rng.choice(repos) for _ in repos]
            pairs = [pair for repo in sampled for pair in groups[repo]]
            diffs.append(sum(b-a for a, b in pairs)/len(pairs))
        diffs.sort()
        interval = [diffs[int(.025*reps)], diffs[min(reps-1, int(.975*reps))]]
    difference = (sum(int(b == g[axis])-int(a == g[axis]) for _, g, a, b in rows)/len(rows)
                  if rows else None)
    return {"n": len(rows), "A_only_correct": a_only, "B_only_correct": b_only,
            "mcnemar_exact_two_sided": mcnemar_exact(a_only, b_only),
            "accuracy_difference_B_minus_A": difference,
            "repository_cluster_bootstrap95_difference": interval,
            "repository_count": len(groups)}


def evaluate(gold, systems, *, split, bootstrap_reps=2000, seed=11, baseline=None):
    repository_ids = {row["repository_id"] for row in gold.values()}
    result = {"status": "DESCRIPTIVE_HELDOUT_EVALUATION" if split == "test" else "DESCRIPTIVE_EVALUATION",
              "split": split, "case_count": len(gold), "repository_count": len(repository_ids),
              "independent_labels_verified": False,
              "primary_metric": "consistency strict accuracy with repository-cluster bootstrap interval",
              "systems": {}, "paired_comparisons": {},
              "limitations": ["This harness does not establish reviewer independence or authenticate label provenance.",
                              "A test result is valid only if code, case list, labels, and predictions were frozen before evaluation."]}
    for name, (predictions, path_hash) in systems.items():
        extras = sorted(set(predictions)-set(gold))
        result["systems"][name] = {"prediction_file_sha256": path_hash,
                                  "extra_prediction_case_ids": extras,
                                  "axes": {axis: axis_metrics(gold, predictions, axis,
                                                              bootstrap_reps=bootstrap_reps, seed=seed)
                                           for axis in AXES},
                                  "per_rule": {axis: per_rule_metrics(gold, predictions, axis)
                                               for axis in AXES}}
    names = list(systems)
    pairs = ([(baseline, name) for name in names if name != baseline] if baseline
             else [(first, second) for i, first in enumerate(names) for second in names[i+1:]])
    for first, second in pairs:
            if first is None:
                continue
            a, b = systems[first][0], systems[second][0]
            result["paired_comparisons"][f"{first}_vs_{second}"] = {
                axis: compare(gold, a, b, axis, reps=bootstrap_reps, seed=seed) for axis in AXES}
    if len(repository_ids) < 5:
        result["warnings"] = ["Fewer than five repositories: cluster-bootstrap intervals are unstable."]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--pred", nargs="+", required=True, help="name=predictions.jsonl")
    parser.add_argument("--baseline")
    parser.add_argument("--output")
    parser.add_argument("--bootstrap-reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    if args.bootstrap_reps < 100:
        parser.error("--bootstrap-reps must be at least 100")
    gold = load_gold(args.gold, args.split)
    systems = {}
    for item in args.pred:
        if "=" not in item:
            parser.error("Each --pred must be name=path")
        name, value = item.split("=", 1)
        if not name or name in systems:
            parser.error("Prediction system names must be nonempty and unique")
        systems[name] = (load_predictions(value), sha256(value))
    if args.baseline and args.baseline not in systems:
        parser.error("--baseline must name one of the supplied systems")
    result = evaluate(gold, systems, split=args.split, bootstrap_reps=args.bootstrap_reps,
                      seed=args.seed, baseline=args.baseline)
    result["gold_file_sha256"] = sha256(args.gold)
    result["seed"] = args.seed
    result["bootstrap_replicates"] = args.bootstrap_reps
    result["baseline_system"] = args.baseline
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix+".tmp")
        tmp.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
        tmp.replace(target)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

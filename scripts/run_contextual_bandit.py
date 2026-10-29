"""Train a bounded contextual-bandit selector on trace links from SMOS only.

The policy chooses one previously saved retrieval ranking per query.  It never
changes a ranking, consumes validation/test rewards during training, or performs
LLM inference.  The held-out projects are evaluated once after the policy is
frozen and remain development evidence rather than the independent 91% gate.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.metrics import ranking
from evaluation.runs import ROOT, save_run


METHODS = ("tfidf", "bm25", "embedding", "hybrid")
SAVED_RUNS = {
    "lexical": ROOT / "experiments/retrieval/20261006T020645-ee4c5e32/results.json",
    "semantic": ROOT / "experiments/retrieval/20261006T021326-432d54b3/results.json",
}
TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def query_features(text: str) -> np.ndarray:
    tokens = TOKEN.findall(text.casefold())
    count = len(tokens)
    return np.array(
        [
            math.log1p(count),
            len(set(tokens)) / max(1, count),
            sum(token.isdigit() for token in tokens) / max(1, count),
        ],
        dtype=float,
    )


def fit_scaler(features: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.vstack(features)
    mean = matrix.mean(axis=0)
    scale = matrix.std(axis=0)
    scale[scale < 1e-12] = 1.0
    return mean, scale


def scale_feature(feature: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return np.concatenate(([1.0], (feature - mean) / scale))


class LinUCB:
    """Small deterministic linear contextual bandit with one observed arm reward."""

    def __init__(self, arms: tuple[str, ...], dimensions: int, alpha: float = 0.5):
        self.arms = arms
        self.alpha = alpha
        self.a = {arm: np.eye(dimensions) for arm in arms}
        self.b = {arm: np.zeros(dimensions) for arm in arms}

    def _score(self, arm: str, x: np.ndarray, explore: bool) -> float:
        inverse = np.linalg.inv(self.a[arm])
        score = float((inverse @ self.b[arm]) @ x)
        if explore:
            score += self.alpha * math.sqrt(float(x @ inverse @ x))
        return score

    def choose(self, x: np.ndarray, explore: bool = False) -> str:
        return max(self.arms, key=lambda arm: (self._score(arm, x, explore), -self.arms.index(arm)))

    def update(self, arm: str, x: np.ndarray, reward: float) -> None:
        self.a[arm] += np.outer(x, x)
        self.b[arm] += reward * x

    def parameters(self) -> dict:
        return {
            arm: {
                "a": self.a[arm].tolist(),
                "b": self.b[arm].tolist(),
                "theta": (np.linalg.inv(self.a[arm]) @ self.b[arm]).tolist(),
            }
            for arm in self.arms
        }


def load_inputs() -> tuple[dict, dict, dict]:
    split_path = ROOT / "data/prepared/splits.json"
    splits = json.loads(split_path.read_text())
    expected = {"train": ["SMOS"], "validation": ["iTrust"], "test": ["eTour_en"]}
    if any(splits.get(key) != value for key, value in expected.items()):
        raise ValueError("Project-level train/validation/test split changed")
    datasets = {
        name: json.loads((ROOT / "data/prepared" / f"{name}.json").read_text())
        for name in ["SMOS", "iTrust", "eTour_en", "RTMX-module-valid"]
    }
    rows = {}
    run_hashes = {}
    for kind, path in SAVED_RUNS.items():
        run_hashes[kind] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        for row in json.loads(path.read_text())["results"]:
            key = (row["dataset"], row["method"])
            if key in rows:
                raise ValueError(f"Duplicate saved ranking {key}")
            rows[key] = row
    for name, dataset in datasets.items():
        source_ids = {item["id"] for item in dataset["sources"]}
        for method in METHODS:
            row = rows.get((name, method))
            if not row or set(row["rankings"]) != source_ids:
                raise ValueError(f"Incomplete saved ranking for {name}/{method}")
            if row["commit"] != dataset["commit"] or row["split"] != dataset["split"]:
                raise ValueError(f"Provenance mismatch for {name}/{method}")
    provenance = {
        "split_manifest": {"path": str(split_path.relative_to(ROOT)), "sha256": sha256(split_path)},
        "prepared_datasets": {
            name: {
                "path": f"data/prepared/{name}.json",
                "sha256": sha256(ROOT / "data/prepared" / f"{name}.json"),
                "commit": dataset["commit"],
                "split": dataset["split"],
                "license": dataset["license"],
            }
            for name, dataset in datasets.items()
        },
        "saved_ranking_runs": run_hashes,
    }
    return splits, datasets, {"rows": rows, "provenance": provenance}


def truth_for(dataset: dict) -> dict[str, list[str]]:
    truth: dict[str, list[str]] = {}
    for source, target in dataset["links"]:
        truth.setdefault(source, []).append(target)
    return truth


def per_query_rewards(dataset: dict, rows: dict) -> dict[str, dict[str, float]]:
    truth = truth_for(dataset)
    rewards = {query: {} for query in truth}
    for method in METHODS:
        _, per_query = ranking(truth, rows[(dataset["name"], method)]["rankings"])
        values = {row["query"]: row["map"] for row in per_query}
        for query in rewards:
            rewards[query][method] = values[query]
    return rewards


def evaluate(dataset: dict, rows: dict, policy: LinUCB, mean: np.ndarray, scale: np.ndarray) -> dict:
    sources = {item["id"]: item for item in dataset["sources"]}
    truth = truth_for(dataset)
    selected = {}
    arm_counts = {arm: 0 for arm in METHODS}
    choices = {}
    for query in sorted(truth):
        x = scale_feature(query_features(sources[query]["text"]), mean, scale)
        arm = policy.choose(x)
        choices[query] = arm
        arm_counts[arm] += 1
        selected[query] = rows[(dataset["name"], arm)]["rankings"][query]
    policy_metrics, policy_rows = ranking(truth, selected)
    baselines = {}
    for method in METHODS:
        metrics, _ = ranking(truth, rows[(dataset["name"], method)]["rankings"])
        baselines[method] = metrics
    best_method = max(METHODS, key=lambda method: baselines[method]["map"])
    return {
        "dataset": dataset["name"],
        "split": dataset["split"],
        "commit": dataset["commit"],
        "linked_queries": len(truth),
        "unlinked_queries_excluded_as_unknown": len(dataset["sources"]) - len(truth),
        "policy": policy_metrics,
        "fixed_baselines": baselines,
        "best_fixed_method_for_reporting_only": best_method,
        "policy_minus_best_fixed_map": policy_metrics["map"] - baselines[best_method]["map"],
        "arm_counts": arm_counts,
        "choices": choices,
        "per_query": policy_rows,
    }


def run(epochs: int = 25, alpha: float = 0.5) -> tuple[Path, dict]:
    splits, datasets, loaded = load_inputs()
    rows = loaded["rows"]
    train = datasets[splits["train"][0]]
    train_sources = {item["id"]: item for item in train["sources"]}
    train_rewards = per_query_rewards(train, rows)
    features = [query_features(train_sources[query]["text"]) for query in sorted(train_rewards)]
    mean, scale = fit_scaler(features)
    policy = LinUCB(METHODS, 4, alpha)
    observations = []
    for epoch in range(epochs):
        for query in sorted(train_rewards):
            x = scale_feature(query_features(train_sources[query]["text"]), mean, scale)
            arm = policy.choose(x, explore=True)
            reward = train_rewards[query][arm]
            policy.update(arm, x, reward)
            observations.append({"epoch": epoch, "query": query, "arm": arm, "reward": reward})
    results = [evaluate(datasets[name], rows, policy, mean, scale) for name in ["SMOS", "iTrust", "eTour_en", "RTMX-module-valid"]]
    payload = {
        "status": "COMPLETED",
        "policy": "linucb-saved-ranking-selector-v1",
        "arms": list(METHODS),
        "alpha": alpha,
        "epochs": epochs,
        "reward": "per-query average precision over reviewed positive links",
        "training_projects": splits["train"],
        "validation_projects": splits["validation"],
        "test_projects": splits["test"],
        "external_sanity_projects": splits["external_test"],
        "training_observations": len(observations),
        "feature_names": ["bias", "standardized_log_token_count", "standardized_unique_token_ratio", "standardized_numeric_token_ratio"],
        "feature_mean": mean.tolist(),
        "feature_scale": scale.tolist(),
        "parameters": policy.parameters(),
        "training_log": observations,
        "results": results,
        "provenance": loaded["provenance"],
        "source_verification": {
            "repository": "https://github.com/ardoco/Replication-Package-ICSE25_LiSSA-Toward-Generic-Traceability-Link-Recovery-through-RAG",
            "commit": "a8e652f29bbdcc4bdcd3d98cd85aa4a37cb65480",
            "commit_url": "https://github.com/ardoco/Replication-Package-ICSE25_LiSSA-Toward-Generic-Traceability-Link-Recovery-through-RAG/commit/a8e652f29bbdcc4bdcd3d98cd85aa4a37cb65480",
            "paper_doi": "10.1109/ICSE55347.2025.00186",
            "replication_doi": "10.5281/zenodo.14714706",
            "outer_package_license": "MIT",
            "verified_at": "2026-10-23",
        },
        "limitations": [
            "All four projects and rankings were exposed in earlier development; none is an independent final test.",
            "Only linked queries have a valid ranking reward; unlinked artifacts remain unknown and are not negatives.",
            "The policy selects an existing ranking and does not learn links or update model weights.",
            "Validation, test and external rewards are never used for policy updates or parameter selection.",
            "This experiment measures trace-ranking behavior only and cannot establish impact or consistency accuracy.",
        ],
        "llm_calls": 0,
        "full_weight_rl": "NOT_RUN",
        "quality_target_91": "NOT_EVALUATED",
    }
    path, result = save_run("contextual-bandit", payload)
    print(path)
    for row in results:
        print(row["dataset"], json.dumps({"policy_map": row["policy"]["map"], "best_fixed": row["best_fixed_method_for_reporting_only"], "delta": row["policy_minus_best_fixed_map"], "arms": row["arm_counts"]}, sort_keys=True))
    return path, result


if __name__ == "__main__":
    run()

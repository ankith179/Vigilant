# Immediate VIGILANT execution

The roadmap is a dependency checklist. Do available work now; do not wait for
the old week/date windows. Keep the existing project, evidence-first pipeline,
knowledge graph, report chatbot and historical results.

## Implemented work

- `scripts/test_evolution.py` imports the exact official TEBench dataset revision
  `eaed7337a15d8db78d0ff3240e39a933784e8088`, verifies its SHA-256 and separates
  source-only inputs from developer test-evolution answers: 314 cases, 10 Java
  projects. Dataset attribution and CC-BY-4.0 notice are in `data/raw/TEBench/README.md`.
- Retrieval ranks every eligible Java test file in each base revision using
  TF-IDF, BM25 and rank-based reciprocal-rank fusion. Gold V0 tests, commit
  messages, evolution labels and changed-test names never enter retrieval.
- Cases save atomically, resume requires matching inputs/source fingerprints,
  failures stay recorded, and each repository has a single sequential worker.
  Three separate repository groups can run concurrently. No subject code runs.
- A bounded LinUCB comparison reuses the existing project implementation. It
  learns only on the first five alphabetically sorted project groups, using
  published changed-test-file Recall@5 as reward. Three epochs and alpha 0.5 are
  fixed. Scaling uses training data only; policy parameters freeze before
  evaluation on the remaining project groups. Every fixed baseline is reported.
- Snapshot chat answers “Explain this project” with a scoped inventory,
  documentation excerpt and exact-source links, making zero model calls.

## Commands

From the existing project root, using its Python environment:

```powershell
python -m pip install pyarrow==23.0.1
# Preparation is needed only once; it refuses to overwrite existing inputs.
python scripts/test_evolution.py prepare
# For a fresh cache, fetch all pinned revisions once before retrieval.
python scripts/prefetch_test_evolution.py --runtime .runtime/tebench --output reports/realworld-20261024/prefetch-fresh.json
python scripts/test_evolution.py run --output experiments/test-evolution/full-20261024 --workers 3
# Use this exact command after an interruption; no completed matching case reruns.
python scripts/test_evolution.py run --output experiments/test-evolution/full-20261024 --workers 3 --resume
python scripts/test_evolution.py policy --baseline experiments/test-evolution/full-20261024 --output experiments/test-evolution/policy-20261024
python scripts/check_quality_target.py --output reports/realworld-20261024/quality-target.json
```

If a prior run recorded fetch failures, preserve it. Fetch into the separate
default recovery cache with `scripts/prefetch_test_evolution.py`, then run:

```powershell
python scripts/recover_test_evolution.py --baseline experiments/test-evolution/full-20261024 --output experiments/test-evolution/recovered-20261024
python scripts/test_evolution.py policy --baseline experiments/test-evolution/recovered-20261024 --output experiments/test-evolution/recovered-policy-20261024
```

The original failures remain in their original report. Recovery reuses successful
rankings and retries only infrastructure failures with the same retrieval logic.

The Parquet library is benchmark preparation tooling, not an application
dependency. Inputs and reference metadata are already packaged after preparation.
Repositories are read into `.runtime/tebench`, which is reproducible and excluded
from distribution. Model weights and installed runtime dependencies stay separate.

## How to read the results

These metrics measure retrieval of the tests developers edited. A newly added
test file cannot be retrieved from the base tree and remains a miss, rather than
being removed from the denominator. An unchanged test is not assumed irrelevant.
Consequently there is no behavioral-impact precision or consistency claim.

All imported TEBench metadata is development-exposed. Its project grouping is a
development comparison, and Apache projects may share change families. It is not
the independent, repository/change-family-disjoint final test. Full LLM-weight
reinforcement learning has not run. The existing saved traceability LinUCB
experiment underperformed the strongest fixed arm on validation; retain that
negative result and compare rather than promoting the policy automatically.

The 91% gate requires separate trace precision/recall/F1 and consistency
accuracy/macro-F1 results on independently reviewed, frozen cases, plus semantic
support review. Do not replace those metrics with test-file Recall@10, software
test pass rates, citation validity, or a carefully selected easy subset.

## Remaining execution queue

1. Complete and audit every test-evolution case and the training-only policy.
2. Analyze misses, unavailable new tests, coverage exclusions and failed fetches.
3. Use source-pinned real changes for independently reviewed contract/impact
   annotations, with explicit unknown regions and negative-label scope.
4. Continue evidence/retrieval and language-tooling improvements on development
   data; preserve all comparative failures and prior exposures.
5. Freeze the actual pipeline, reviewed rubric, split and denominators, then run
   one independent final evaluation. Keep the target at 0.91.

No dates block this queue. Independent reviewer judgments and native Windows/GPU
access cannot be manufactured by a scheduled agent. Save intermediate overlays
with `scripts/research_checkpoint.py`; restore using `RECOVERY_SOURCES.json`.

# Local-model and evidence release — 2026-10-17

Implemented and verified software changes; model accuracy target remains unresolved.

| Check | Result | Evidence |
| --- | --- | --- |
| Core environment installation | PASS, Python 3.12 core dependencies | core-install.log |
| Before-change regression suite | 62 passed | tests-before.log |
| Final regression suite | 74 passed; one dependency deprecation warning | tests-after.log |
| Frontend production build | PASS | frontend-build.log |
| Chromium 138, Linux | PASS, all 13 pages, local selectors, exports, deterministic UI investigation and mobile layout | ../frontend/20261017-local-models/validation.json |
| Saved retrieval arithmetic | PASS, 23 method rows / 1,484 query rows | metrics-audit.json |
| Frozen RAG observation audit | PASS, 251 actual historical generations | rag-audit.json |
| Historical files preserved | All 418 experiment files and 3 snapshot files unchanged | preservation.json |
| Diagnostic input preparation | 12 cases; all excerpts verified against saved snapshots | ../../experiments/local-model-comparison/dataset.json |
| New live local inference | NOT RUN; no Ollama service available, connection refused | local-preflight.json |
| Graph export | 2,134 nodes / 3,993 edges, one exact saved scope | ../../handoff/graphify/EXPORT.json |
| Graphify native integration | UNAVAILABLE / import unverified | ../../docs/GRAPHIFY_HANDOFF.md |
| Native Windows / 32 GB hardware | NOT VERIFIED; launch and comparison scripts supplied | ../../docs/LOCAL_MODELS_32GB.md |

New tests exercise changed-hunk windows after line 400, quote verification, whole-pair omission, neutral vs legacy prompt behavior, loopback-only model routing, schema and model digest recording, bounded resume, label isolation, invalid output scoring, test-set model-selection restriction, graph export scoping, API selection propagation and preservation of truncated output as invalid. Mock transport checks are software tests, not real model observations. A fixture was updated to include the newly fingerprinted shared prompt module; final rerun passed.

The model comparison uses identical prompt/evidence policy for three local candidates; model and exact source/data digests define run identity. Completed diagnostic cases are resumable, partial sets unscored. The supplied old 25% consistency result is unchanged. No claim of >75% independent accuracy, stronger model superiority or complete production architecture is made.

Hourly continuation was enabled on the existing task. It restores saved state, uses bounded calls only if a suitable local runtime is available, and pauses with a specific blocker when only external inputs remain. It cannot operate the user's Windows machine. On that machine, Run-Local-Models.ps1 automates a finite sequential comparison after setup; it does not guarantee a score or tune against held-out tests.

The full project archive includes source, pinned data/Git snapshots, historical results, research Word/PDF drafts, guides and the Graphify handoff. Model weights and installed packages are excluded and reproducible through setup. This release does not modify the historical manuscript results to imply unperformed new experiments.

# VIGILANT accuracy review — 21 October 2026

The supplied Windows source archive already contains a completed citation-only repair experiment. This review audited its saved outputs; it did not generate new model answers. The 75% accuracy goal remains unmet.

| Model | Initial correct / 12 | After citation repair | Valid after repair |
| --- | ---: | ---: | ---: |
| Qwen3 8B | 0 | 4 (33.33%) | 12/12 |
| Qwen2.5 Coder 14B | 1 | 1 (8.33%) | 12/12 |
| Qwen3 14B | 0 | 3 (25%) | 12/12 |

These are 12 authored, correlated development diagnostics. The majority-class baseline is 50%; always-UNCERTAIN is 25%. No tested model exceeds the majority baseline. The largest observed score does not establish model superiority. Nine correct answers would be 75% on these twelve cases, but would not establish independent generalization.

## What failed and what is already fixed

The initial citation errors were file paths in `affected_artifacts`, where the validator required selected A aliases. Evidence E aliases were valid. All 26 initial invalid answers had this artifact-alias problem; the saved finish records do not indicate output truncation.

The supplied `llm/ollama.py` already constrains evidence and artifact references to selected aliases using a per-request JSON schema. All 36 citation-repair responses pass strict validation. This addresses reference syntax; it does not show that cited excerpts support a conclusion. The neutral paired-evidence prompt and authored labels were unchanged between these two experiments.

Remaining errors include treating base-revision code as current behavior, missing route/caller contradictions, and disagreement about the distinction between potential and established inconsistency. Cases 03 and 11 change a default while a docstring still states the old value; the authored label is POTENTIAL_INCONSISTENCY, whereas an INCONSISTENT judgment may be defensible. Case 06 labels a deleted test MISSING_TEST without establishing the explicit testing obligation required by the prompt. Case 09 also needs contract review. These are review questions, not permission to relabel answers to match a model.

## Practical route toward 75%

1. **Define the task and review labels first.** Have two people independently review the blind packets under `reports/citation-fix-20261021/review/`, record missing evidence, and adjudicate disagreements with an explicit rubric. Keep original labels and create a separately versioned reviewed dataset. Do not show reviewers model answers or choose labels to improve scores.
2. **Improve the evidence supplied to the model.** The existing candidate collector in `rag/evidence.py` includes changed hunks and bounded requirement, implementation, caller and test context. Its prepared `evidence-v2-dataset.json` is a separate, unrun development arm. Nine cases lack a selected requirement-artifact role; inline docstrings may still express contracts, so inspect the actual packets before deciding evidence is absent. Add real missing contracts and source links, never invented requirements.
3. **Run one controlled development comparison.** Keep the citation fix, model and decoding settings fixed; change only evidence selection. Qwen3 8B is a reasonable inexpensive first diagnostic run based on the saved latency and observed score. This is not a claim that it is the best general model. Review each failure before spending time on all three models.
4. **Then test reasoning changes individually.** Clearly distinguish base and head revisions and require a contract, current behavior and cited comparison before choosing a label. Compare one change at a time. Keep invalid outputs as errors; report abstention separately. Deterministic checks can help for exact route/default mismatches when their applicability is verified. Do not count a structural similarity edge as proof of a requirement relation.
5. **Measure on unseen, independently annotated cases.** Split by repository and change family before tuning. Use development data for prompt changes, validation data for model/threshold selection, then freeze the full pipeline and evaluate the test set once. Report accuracy, macro-F1, per-class confusion, citation validity, semantic citation review and uncertainty/coverage. Choose test-set size from the desired confidence precision and account for correlated cases. An observed 75% point estimate is different from evidence that population accuracy exceeds 75%.

Fine-tuning or larger models should follow this evidence/label work, because neither fixes an undefined target or missing contract. There is no defensible promise that these changes will reach 75%.

## Commands from the project root on Windows

Audit saved citation-repair results without Ollama or inference:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/audit_local_models.py experiments/local-model-comparison/citation-fix-20261021 --sources reports/citation-fix-20261021/frozen
```

Audit the initial run by substituting `windows-20261021` for both directory names. These audit commands make zero model calls.

After independent packet review, the following is an optional NEW six-call development batch. Start local Ollama first. It writes a separate experiment:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_local_models.py --dataset reports/citation-fix-20261021/evidence-v2-dataset.json --models qwen3:8b --max-calls 6 --output experiments/local-model-comparison/evidence-v2-20261021
```

Exit 75 means a bounded partial run, with full-dataset accuracy withheld. Repeat the identical command for the remaining cases; exact fingerprints reuse saved calls. Do not change dataset/source/model bytes between batches. This candidate has NOT been run in this review. Its current labels remain authored development labels.

`Run-Local-Models.ps1` now defaults to the completed citation-fix directory. Resume can reuse it only when model, inputs and sources match exactly; it still needs the local runtime to establish model identity. Prefer the offline audit when no inference is intended.

## Release verification and limits

- Added an offline auditor of dataset/source/prompt fingerprints, raw response replay, selected citation schema and score arithmetic. Both saved runs pass: 72 observations, zero new inference calls. Frozen sources are retained separately for each arm.
- Added early Git LFS pointer detection for database restore and checkpoint snapshots, plus isolated test database configuration. Normal Linux Python 3.12 test invocation passes **86 tests**, with one dependency deprecation warning. Tamper tests cover changed raw output, scores, missing observations and changed frozen sources.
- A fresh portable extraction passes database restoration, dashboard synchronization, API health and built-frontend response checks on Linux. All 6,691 content entries in the pre-documentation-finalization ZIP matched their manifest hashes; database entries contain SQLite bytes, not LFS pointers. See `portable-release-check.json`.
- Production frontend build passes from the supplied current source (`frontend-build.log`). No browser acceptance was repeated.
- Three frozen SQLite databases pass quick checks. All supplied experiment files remain byte-identical. Two snapshot pointer files were rehydrated from the older supplied archive only after matching their exact SHA-256 object IDs. Missing repository metadata/data files were restored without overwriting existing files; see `archive-recovery.json` and `preservation.json`.
- The latest live Windows database was an unresolved Git LFS pointer and could not be recovered from the supplied older archive. It is excluded from the portable ZIP. A fresh extraction restores the exact frozen snapshot; it cannot reproduce unsnapshotted Windows dashboard rows. Existing user databases must be retained. Do not overwrite the working Windows directory or its `.runtime` with a fresh extraction.
- Native Windows setup, 75-test/browser acceptance and subsequent 80-test citation-fix logs are supplied historical evidence. This review ran on Linux, not the user's Windows machine. No new Windows or browser acceptance is claimed. Runtime binaries, model weights and environment dependencies remain excluded and are installed separately.
- The original experiments, manuscript drafts and older status sections are historical records; this review and the new top-level status take precedence for current diagnostic outcomes.

For a new installation, extract the full project ZIP into a separate folder, then run `Setup-Windows.ps1`. It installs core dependencies, builds the frontend, restores frozen data and tests the application. See `docs/LOCAL_MODELS_32GB.md` for local Ollama setup. For the existing working installation, retain it and compare the release changes before copying reviewed source files; the five fingerprinted inference sources already match the completed citation-fix experiment.

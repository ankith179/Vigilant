# Saved evidence report bundle — 28 October 2026

- Added seven evidence-based evaluation reports and `reports/reproducibility_manifest.json`; they summarize existing records only.
- Frozen case-analysis SHA-256 verified before and after: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. Historical Qwen3 remains 4/12 authored-label agreement. Saved local Qwen2.5 1.5B ablation variants E-I all returned UNCERTAIN and each agreed on 3/12 authored cases; partial endpoint recall increased only in graph/scripted/combined arms. No new inference or labels.
- Retrieval: saved 314-case development run; RRF Recall@10 85.11%, MRR 0.7638, nDCG@10 0.7376. Not assurance accuracy.
- Current V3 accuracy and 33/36 target remain NOT MEASURED; independent 95% remains NOT ESTABLISHED.
- Latest complete full suite is 516 total: 513 passed, 3 Windows symlink setup failures, 0 errors/skips; exit 1. No full suite was run in this report-update step.
- No tests or inference ran while writing these reports. Exact report hashes are in `reports/evaluation_status.md`; source hashes are in `reports/reproducibility_manifest.json`.

# Latest full-suite evidence — 28 October 2026

## Latest complete full-suite reconciliation — 28 October 2026

The authoritative JUnit at `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\contract-continuation\v047-full-suite-009.xml` (SHA-256 `28616c87532f77f2d42312c0cfd7777f14f00f9c1b0aa0b16f101ab1e0c9be44`) contains **516 tests: 513 passed, 3 failed, 0 errors, 0 skipped**; the run took 766.12 seconds and exited 1. The three failures are:
1. `tests.test_local_pilot_blob_recovery::test_recovery_rejects_traversal_and_does_not_follow_source_symlinks`
2. `tests.test_partial_report_api::test_rejects_changed_or_foreign_evidence[symlink]`
3. `tests.test_verified_cache_maps::test_corrupt_or_rebound_cache_rejected[symlink]`

The test report identifies Windows `WinError 1314` while creating symlinks during fixture setup, before the protected-path checks. The prior C++ overload failure is not among these three. A later targeted rerun with `TEMP`/`TMP` redirected passed the C++ test and all four `tests/test_native_languages.py` tests; the full suite was not rerun afterward. Do not describe the suite as passing or fully verified. Frozen `case-analysis.json` remains SHA-256 `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. No inference or new accuracy measurement occurred.


## C++ temp-path follow-up — 28 October 2026

## C++ native-language temp-path recheck (2026-10-28)

The previous C++ overload-resolution failure was reproduced with the sandbox default temporary directory and reported `[WinError 5] Access is denied` while creating the Clang VFS temp folder. Re-running with `TEMP`/`TMP` pointed at the writable task workspace passed the focused test (**1 passed in 3.77s**) and the full `tests/test_native_languages.py` module (**4 passed in 3.61s**). No C++ resolver code changed. JUnit: `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\cpp-overload-current.xml` (SHA-256 `4172fc994caf0086f0c08451a9e939ea097e875ee49c775ba02940364179695e`) and `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\native-languages-current.xml` (SHA-256 `8174b661af9f5b03a95c5d45ab7ab70d567f20d34f58ae44c746d3c336067383`). Full suite was not rerun; the later socketpair-stalled run remains incomplete. No inference/accuracy evaluation ran; frozen case-analysis hash remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. Exact commands and failure details: `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\cpp-native-validation-20261028.txt` (SHA-256 `5ab3f2d049cbfba46c2a0c865cb8937b5b876a1aba09c7420b063c922acde563`).

## Evaluation target scope — 28 October 2026

Both targets are recorded separately: 33/36 is a development diagnostic target, and >=95% is the independent research target. The principal scientific claim is the independent result. Current status: development NOT MEASURED; independent NOT ESTABLISHED.

## V047 mapping v3 validation follow-up — 28 October 2026

- Exact focused command: `rtk .venv/Scripts/python.exe -B -m pytest -q tests/test_measure.py --basetemp="C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\pytest-measure-v047-current" -p no:cacheprovider --junitxml="C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\measure-v047-current.xml"`
- Result: **7 passed, 0 failed, 0 errors, 0 skipped in 1.17s**. JUnit is retained at `C:\Users\Ankith\OneDrive\Documents\ChatGPT\Vigilant ---2\work\measure-v047-current.xml` (SHA-256 `ca6b93f7493efa805916a277578af8883a1567b37de45f8cc9078757884e0a19`). This checks the measurement harness only; it does not run inference or calculate new accuracy.
- The mapping v3 verifier passed for 12 cases and all inventoried local snapshot file hashes. Frozen diagnostic hash after the test: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.
- Full suite was not rerun. The last complete JUnit remains 511 tests total: 507 passed and 4 failed (three Windows symlink-privilege cases, one C++ overload-resolution case). A later run that stalled in sandbox socketpair startup remains incomplete.

# Execution checkpoint — 28 October 2026, repository identity audit v3

## Current verified state

- Working copy: `C:\Users\Ankith\Downloads\vigilant project code`; no `.git` directory, so no commit-based working-tree identity is available.
- Original case-analysis SHA-256 verified before this update: `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. No original labels, prompts, predictions, confidence values, or evidence were edited.
- RTMX repository identity is corroborated by matching frozen README content against the official [rtmx-ai/rtmx-bench](https://github.com/rtmx-ai/rtmx-bench) page. Full Stack FastAPI identity is corroborated by frozen README title/stack text against the official [FastAPI template](https://github.com/fastapi/full-stack-fastapi-template). These establish identity only, not exact BASE/HEAD ancestry.
- Flask BASE commit `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` remains verified in the local `pallets/flask` clone; its HEAD objects remain unmatched locally.
- Added `reports/v047/original-case-mapping-audit-v3.json` (SHA-256 `767457cd2f1c943a6b5ef920044bba3a4d2e4e9579714b763f9e438359e19fb6`) and `.md` (SHA-256 `095e576c7b475a7ccd6fbf5d4c57adf7f5b01da899b82077211e962b3640aa8b`); v1/v2 remain preserved.
- No evaluation split or labels were changed. The original 12 stay development/regression cases. New V3 accuracy and 33/36 are **NOT MEASURED**; independent 95% is **NOT ESTABLISHED**.

## Tests and blockers

- No test suite was run in this checkpoint. The latest completed full-suite JUnit inspected was `reports/v047-full-after-golden.xml`: 511 tests, 507 passed, 4 failed, 0 errors, 0 skipped. The four failures are the three Windows symlink-privilege cases and the C++ overload-resolution case listed in `reports/evaluation_status.md`.
- Latest evaluation status also records a later full-suite attempt that stopped progressing in Starlette/AnyIO Windows socketpair startup; that later run has no final count. Do not treat it as a pass.
- Inference remains blocked by absent Ollama executable and configured model manifest. No inference or accuracy scoring occurred in this milestone.
- Independent review remains pending: 24 cards prepared, 0 labels, 0 independent judgments.

## Next exact action

Run the V047 measurement-harness golden tests and inspect the separate 36-case case-mapping/split manifest. Keep original cases in development; do not freeze a test split until held-out repositories and blinded labels exist. If new repo families remain eligible, have the user/reviewers provide actual labels rather than creating any.

# Execution checkpoint — 27 October 2026, V040

## Frozen diagnostic integrity and decision contract

Working copy: `C:\Users\Ankith\Downloads\vigilant project code`; no `.git` metadata is present. V039's files had advanced from the prompt version described in its report, so this checkpoint records current source state. No labels or historical predictions changed.

### Implemented

- Frozen E0/E2 prompt construction now verifies hashes for the archived `llm/context.py` and `ingestion/models.py`, loads the archived decision class independently, and binds it to the frozen context. This keeps modern schema changes from altering baseline prompt text.
- Local Ollama ablations use the archived v1 schema while restricting citations to selected evidence aliases. Current investigations continue to use v2.
- V2 validation rejects conflicting outcomes when both fields are consistency labels; trace and impact dispositions remain separable.
- The legacy prompt omits the additive `schema_version` field. Model-reported confidence such as `0.95` remains intact.

### Verification

Focused check: **5 passed in 19.03s**, including exact reconstruction of all 12 saved messages. The broader touched-module run completed with **99 passed, 1 deselected, 1 existing Starlette/AnyIO deprecation warning in 14.32s**; the excluded API worker regression then passed in isolation (**1 passed, 1 warning in 7.70s**). JUnit: `reports/decision-contract-20261027/v040-touched-tests.xml` and `v040-api-isolated.xml`. Both runs used temp directories in the Codex work area because Windows denied a project-local temp directory.

These were offline prompt/schema tests. No model inference, calibration, or accuracy evaluation ran. Windows denied a project-local temp directory; the test used the writable Codex work area.

### Acceptance and next action

Offline availability check found no `ollama` executable, no configured local model directory, and no `.runtime` directory. No loopback/network probe was made; the earlier WinError 10013 remains unresolved. The authored Qwen3:8B diagnostic remains 4/12 (33.33%). Its mismatch `0.95` values remain model-reported confidence, not calibrated probability or proof of correctness. Independent labels remain zero; dependent/independent/overall 95% gates remain NOT_MET / NOT_EVALUATED; release readiness remains NOT MET. Full suite has not been newly verified.

Next: check authorized local Ollama and the pinned Qwen3:8B digest without relaxing loopback controls. If unavailable, do not infer; continue feasible non-inference engineering. Run the 12-case prompt-equivalence regression before any ablation.

---

# Execution checkpoint — 26 October 2026, latest bounded milestone

## V039 — diagnostic root cause and versioned decision schema

Working copy: `C:\Users\Ankith\Downloads\vigilant project code`. The ZIP working copy has no `.git` directory; no branch or commit is available. `PROJECT_STATE.json` showed no active lease before this milestone.

### Findings

- Re-read the saved case prompts, raw outputs, evidence package and case analysis. The eight mismatches (03, 04, 05, 06, 08, 09, 10, 11) each contain model-emitted `confidence: 0.95`; there is no 0.95 code default. The score is retained as the model-stated confidence and is not a computed accuracy or calibrated probability. The sample's 0/8 match rate among those eight outputs is diagnostic only.
- Case 04 contains the base `redirect` symbol and a head file excerpt without it; the model hallucinated a head implementation. The context has no complete symbol-search receipt, so absence from the excerpt cannot safely establish deletion.
- Case 06 supplies the deleted test and other tests but no exhaustive head-test search receipt or reviewed obligation registry. The model treated unrelated remaining tests as coverage.
- Cases 08 and 09 contain the route-prefix and default-limit changes, respectively; the model ignores the changed behavior. Case 08 selected 19/28 candidates, so candidate omission and reasoning/attention both remain plausible.
- Case 10 explicitly forced `decision` and `consistency` to match in both schema and prompt, preventing a distinct `BROKEN_TRACE` disposition.
- Cases 03, 05, 09 and 11 retain unresolved authored-label ambiguity. Cases 01, 02, 07 and 12 match authored labels but have not received semantic adjudication.

### Implemented and verified

- Added schema version 2 for modern LLM responses. V1 remains the default for old/persisted response shapes and preserves matching-label validation. V2 separates broad decision disposition from consistency and validates the consistency label set.
- Modern context uses `paired-neutral-v4-orthogonal-decisions`; deterministic validation requires explicit v2 on this prompt. The historical legacy prompt/evaluation path remains v1.
- Confidence `0.95` remains present and unchanged. Prompt text says it is model-reported and uncalibrated; no calibration claim is made.
- Focused command completed: `rtk .venv/Scripts/python.exe -X utf8 -m pytest -q --tb=short --basetemp=tmp/pytest-schema-v2-evidence --junitxml=reports/llm-diagnostic-error-analysis/schema-v2-focused.xml tests/test_pipeline.py::test_contradictory_model_labels tests/test_pipeline.py::test_v2_separates_trace_disposition_and_consistency_without_rewriting_confidence tests/test_pipeline.py::test_v2_rejects_non_consistency_label_on_consistency_axis tests/test_pipeline.py::test_new_prompt_requires_explicit_v2 tests/test_pipeline.py::test_no_model_is_uncertain tests/test_local_models.py::test_v2_prompt_separates_disposition_and_consistency tests/test_local_models.py::test_ollama_schema_and_identity tests/test_local_models.py::test_citation_resolution_stays_strict_and_derives_references tests/test_local_models.py::test_finite_resume_and_labels_never_in_prompt tests/test_omniroute.py::test_transport_maps_citations_and_records_requested_and_reported_models tests/test_omniroute.py::test_unknown_citation_remains_invalid` — **15 passed in 8.06s**.
- Broader test batches did not complete. A default temp-root run failed because pytest could not create a directory under the sandbox temp path. Project-local temp-root reruns then stopped making progress (47 dots in a combined run; 23 in another batch) and were interrupted. They are not passing results. Full suite was not run.
- No fresh model inference was performed. The previously observed loopback `WinError 10013` remains a blocker; do not bypass network/security controls to work around it.

### Files changed in V039

`ingestion/models.py`, `llm/context.py`, `llm/providers.py`, `llm/omniroute.py`, `tests/test_pipeline.py`, `tests/test_local_models.py`, `tests/test_omniroute.py`, `tests/test_local_audit.py`, `tests/test_input_audit_hardening.py`, `reports/llm-diagnostic-error-analysis/decision-schema-v2.md`, `reports/llm-diagnostic-error-analysis/schema-v2-focused.xml`, `docs/VIGILANT_MASTER_TASK_REGISTER.md`, `docs/EXECUTION_CHECKPOINT.md`, `reports/execution/latest-status.json`, `PROJECT_STATE.json`, `RESUME.md`, and `docs/EXECUTION_RESUME_PROMPT.md`.

### Remaining work and next action

The 95% independent/dependent/overall gates remain NOT_MET / NOT_EVALUATED; independent labels remain zero. No 4/12 performance improvement was evaluated. First inspect this checkpoint against the real files and current hashes, then run remaining touched-path tests one module at a time with a fresh project-local `--basetemp` and `-vv` to identify the stalled test. Only run E0/E1/E2/E5/E6 inference if the user-authorized local model/runtime becomes available without bypassing the WinError 10013 control. Next scientific gate: independent adjudication and a frozen, repository/change-family-disjoint cohort.

---

# Prior checkpoint — 26 October 2026, 2026-10-26T16:47:13Z

## VIGILANT LLM diagnostic and retrieval baseline milestone

Working copy: `C:\Users\Ankith\Downloads\vigilant project code`. The ZIP working copy has no `.git` directory, so Git branch, commit, and status cannot be verified. Existing source/report files were inspected in place. Prior release/archive checks predate this milestone; no new release archive was built.

### Completed and verified in this bounded milestone

- Replayed the saved diagnostic outputs with their preserved frozen sources: 36 observations across three saved models; Qwen3:8B remains 4/12 (33.33%) on the authored, correlated 12-case diagnostic. This is score-arithmetic/output validation, not fresh inference or independent accuracy.
- Wrote `reports/llm-diagnostic-error-analysis/README.md` and `case-analysis.json` with all 12 prompts, raw outputs, validated decisions, candidate and selected evidence, configuration, revision context, case findings, root causes, and limitations. Repository-family counts are 3 RTMX, 5 Flask, and 4 fullstack cases.
- Added `scripts/llm_ablation_harness.py`. It prepares 12 label-blind requests each for E1/E2/E5/E6 (48 total), writes per-case hashes and selected/omitted evidence IDs, and keeps inference opt-in. E3 is blocked without adjudicated oracle evidence; E4 is already in the baseline and not isolatable; E7 replays saved alternatives; E8 is not selected before comparisons. No gold labels or baseline outputs were changed.
- Added development split support to `scripts/evaluate_local_models.py` to make dependent development experiments valid without permitting held-out `test` in the ablation runner.
- Local model availability check: `ollama` is not on PATH and `.runtime`/model assets are absent in this copy. The loopback `OllamaProvider().preflight()` probe failed with Windows `WinError 10013` (socket access denied), so server/model availability could not be established; no model generation call was made.
- Offline E2 package diagnostic: 79/80 baseline target-path evidence rows versus 80/80 selected by E2, with target-path evidence in all 12 cases for both. This measures path inclusion only, not relevance or quality; details and input hashes are in `reports/llm-diagnostic-error-analysis/evidence-package-input-diagnostic.json`.
- Recomputed saved TEBench ranking metrics into `reports/llm-diagnostic-error-analysis/retrieval-baseline-audit.json`: 314 exposed development cases, 10 projects, zero invalid rows. Saved RRF Recall@10 is 85.112% (MRR .7638, nDCG@10 .7376); BM25 Recall@10 is 84.716%; TF-IDF is 82.036%. This is an offline replay of saved predictions, not a new retrieval run. Original RRF remains unchanged.
- Reviewed the primary records for R2Code, REST-at, the 2026 multi-agent impact study, and RCT; implications and limits are in `docs/RESEARCH_GUIDED_EXPERIMENTS.md`. No paper result was counted as a VIGILANT result.

### Files changed or generated

- Code/tests: `scripts/llm_ablation_harness.py`, `scripts/evaluate_local_models.py`, `tests/test_llm_ablation_harness.py`.
- Diagnostic artifacts: `reports/llm-diagnostic-error-analysis/README.md`, `case-analysis.json`, `retrieval-baseline-audit.json`, `evidence-package-input-diagnostic.json`, `focused-regression.xml`.
- Ablation artifacts: `experiments/llm-ablation-20261026/plan.json`; `experiments/llm-ablation-20261026/prepared/{E1,E2,E5,E6}/` (12 case JSON files per condition; 48 total).
- Research and state: `docs/RESEARCH_GUIDED_EXPERIMENTS.md`, `docs/EXECUTION_CHECKPOINT.md`, `docs/EXECUTION_RESUME_PROMPT.md`, `docs/VIGILANT_MASTER_TASK_REGISTER.md`, `reports/execution/latest-status.json`, `RESUME.md`, `PROJECT_STATE.json`.

### Actual tests and commands

- `rtk .venv/Scripts/python.exe -B -m pytest -q tests/test_llm_ablation_harness.py --basetemp='C:\Users\Ankith\Documents\Codex\2026-10-25\master-execution-prompt-vigilant-complete-development\work\pytest-vigilant' -p no:cacheprovider` — final rerun: 9 passed. The earlier initial run had one incomplete test-fixture failure; it was fixed. The CLI smoke was fixed after it exposed a missing project-root import.
- `rtk .venv/Scripts/python.exe -B -m pytest -q tests/test_test_evolution.py tests/test_llm_ablation_harness.py --basetemp='C:\Users\Ankith\Documents\Codex\2026-10-25\master-execution-prompt-vigilant-complete-development\work\pytest-vigilant-final' -p no:cacheprovider --junitxml reports/llm-diagnostic-error-analysis/focused-regression.xml` — 15 passed in 8.66 seconds; JUnit retained at that path.
- `rtk .venv/Scripts/python.exe -B -m py_compile scripts/llm_ablation_harness.py scripts/evaluate_local_models.py tests/test_llm_ablation_harness.py` — passed.
- `rtk .venv/Scripts/python.exe -B scripts/llm_ablation_harness.py` — completed offline; saved the case report and prompt packages; new model calls 0.
- `rtk .venv/Scripts/python.exe -B scripts/measure_quality.py --output reports/llm-diagnostic-error-analysis/retrieval-baseline-audit.json` — passed saved-score/provenance arithmetic; new model calls 0.

The prior full Windows suite remains not green (283 passed, 32 failed, 82 errors, 1 warning in the earlier recorded run); it was not rerun for this milestone. Current focused regression only covers this harness plus TEBench retrieval policy.

### Experiment disposition and quality status

- E0: saved outputs replayed; fresh inference not run.
- E1/E2/E5/E6: prepared only; not scored. No local Ollama executable/runtime or pinned model weights are present in this code folder.
- E3: BLOCKED — no separately adjudicated evidence-ID oracle map.
- E4: schema/citation validation was present in E0; no isolated treatment effect.
- E7: saved same-dataset alternative-model observations replayed (Qwen3:14B 3/12; Qwen2.5-Coder:14B 1/12).
- E8: not selected/run before E1–E6 comparisons.
- 95% dependent, independent, and end-to-end assurance gates remain NOT_MET / NOT_EVALUATED. Independent labels remain 0; semantic citation support remains unreviewed. Release readiness remains NOT MET.

Top observed diagnostic hypotheses: deletion/revision/negative-search failures (cases 04/06); consistency-vs-traceability label conflation (especially case 10); missed changed cross-artifact behavior (08/09). Cases 03/05/09/11 need gold-label adjudication before treating all mismatches as ground-truth errors. No score improvement is claimed.

### Exact next actions

1. Inspect the checkpoint and real tree before continuing; confirm the local Ollama service, executable, and expected model digest. If available, run E0/E1/E2/E5/E6 once each on the same declared diagnostic inputs/model; do not tune against an independent holdout. The first command is `rtk .venv/Scripts/python.exe -B scripts/llm_ablation_harness.py --run-local E0 --model qwen3:8b --max-calls 12`.
2. If the runtime/assets are absent, stop inference work and continue engineering tasks that do not require them; request an independently adjudicated evidence map before E3 and qualified independent reviewers before final evaluation.
3. Reconcile the pre-existing `latest-status.json` V037 VERIFIED entry (no matching V037 row was present in the task register during this inspection). This milestone is registered as V038 IMPLEMENTED; its local tests do not imply scientific validation.

No automation or background continuation was started. No external network, paid model, external communication, push, or submission was used; only the blocked loopback preflight was attempted.

# Execution checkpoint - 26 October 2026, 03:54 UTC

## Current Windows code folder — verified 2026-10-26

This folder is the user-requested working copy. `COPY-VERIFICATION.json` records the 15,126-file path/size comparison and 7,394 code/document SHA-256 checks. The copied `.venv` was used to run seven focused tests successfully at this shorter path. The original checkout/runtime is retained; the local `.runtime/tebench` cache was not duplicated. The full suite remains not green (283 passed, 32 failed, 82 errors in the earlier run); do not claim full Windows acceptance.

The 95% traceability, consistency, end-to-end and independent-performance gates remain NOT_EVALUATED / NOT_MET. Independent judgments remain 0. See `reports/realworld-20261026/95-percent-target-update.md`.


## Development retrieval and Windows verification — 26 October 2026

Added `test-tree-and-resource-v2` in `scripts/test_evolution.py`. Supported source/text files below explicit test trees are indexed by path and content; unsupported-suffix resources are retained as path-only candidates, with binary bytes never read into the index. `scripts/recover_test_evolution_failures.py` retries each infrastructure-failed row once into a separate output and preserves the original failed run.

On all 314 exposed TEBench development cases, 592 references and 10 projects, original RRF Recall@10 is 85.112%. Expanded-policy RRF Recall@10 is 84.995%; BM25 is 84.993%. Four original failures were recovered once; zero rows remain invalid in the recovered analysis. Candidate inventory ceiling increased from 94.774% to 95.265%, but this oracle ceiling is not ranked performance. The experiment is a negative candidate-policy result and is not promoted. Full details: `reports/realworld-20261026/95-percent-target-update.md`, `reports/realworld-20261026/miss-decomposition-broad-candidates.json`, and `experiments/test-evolution/broad-candidates-recovery-20261026/`.

Focused tests: 6 passed. Full Windows pytest returned 283 passed, 32 failed, 82 errors and one warning in 687.54 s; full log: `reports/realworld-20261026/full-suite-windows.log`. Errors include denied temp/hard-link operations; lineage Git fixtures also report `Filename too long` under the current long checkout path. One representative atomic review-store test passed with elevated access, but the full suite remains not verified. Do not weaken atomic publication or security behavior to clear environment denials.

Requested code destination: `C:\Users\Ankith\Downloads\vigilant project code`. It existed and was empty at inspection. Copy project code, tests, data, reports and experiment evidence there only after this verification; do not remove the current checkout or mutate the existing runtime caches. Preserve the `.venv` runtime as-is; verify the copied tree and run focused tests from the shorter path. Reconcile the destination contents before any future overwrite.

95% traceability, consistency, end-to-end and independent performance remain NOT_EVALUATED/NOT_MET. The independent label count is zero; TEBench retrieval is not assurance accuracy. Independent reviews, adjudication, frozen disjoint final cohort and evidence-validity scoring remain necessary. The user target does not authorize label changes or claims unsupported by evidence.

## Latest security milestone — V026 bounded repository-import hardening

Remote repository URLs are restricted to HTTPS `github.com`/`gitlab.com`, with credentials, alternate ports, query/fragment, control characters and ambiguous targets rejected before Git starts. Git redirects, `file`/`ext` protocols, system/global config, askpass helpers and inherited repository/config environment are suppressed. Cloning runs from an isolated temporary directory and uses `--no-checkout`; Git blobs are read directly. URL/path lengths are bounded. No live network clone or egress firewall was tested; DNS pinning and host egress controls remain residual risks. Full details: `reports/import-security-20261026/VERIFICATION.md`; structured threat inventory: `docs/THREAT_MODEL.md`.

Combined touched-path regression: **40 passed**, one existing Starlette/AnyIO deprecation warning, 115.85 seconds. This run includes the 22 V015 worker/orchestration tests plus repository-import security/API/storage and transaction checks. JUnit: `reports/import-security-20261026/focused-regression.xml`. Command:

```powershell
rtk .venv\Scripts\python.exe -m pytest tests/test_integration.py tests/test_job_controls.py tests/test_memory_transactions.py tests/test_input_audit_hardening.py tests/test_audit_regressions.py::test_clone_size_limit_cleans_stage_and_success_promotes_atomically -q --basetemp tmp/pytest-v015-v026-final --junitxml reports/import-security-20261026/focused-regression.xml
```

V026 remains IN_PROGRESS: no live public clone, DNS pinning, outbound firewall, hostile compiler, full dependency advisory review or comprehensive resource isolation was verified. V015 remains IN_PROGRESS for POSIX host process-tree evidence, strict wall-clock completion, non-SQLite cancellation and multi-server coordination.

# Execution checkpoint - 26 October 2026, 03:38 UTC (superseded)

## Superseding continuation — V015 ownership and process-tree controls

This section supersedes the 02:45 UTC status below. File-backed SQLite investigations use spawned Python workers with persisted deadlines, bounded cooperative/terminate/kill escalation, atomic report publication, abrupt-exit reconciliation and no automatic replay. On Windows, workers are assigned to a Job Object with `KILL_ON_JOB_CLOSE`; descendant-process tests confirm cancellation and server death stop the worker tree. POSIX workers enter a process group and cancellation sends TERM then KILL to the group even when the group leader exits first. A mocked unit test covers that escalation order; an actual POSIX host was not available in this run.

An OS sidecar lock now enforces one application process per file-backed SQLite database before startup recovery. A spawned second process was rejected while the first server remained healthy; a later server acquired ownership after shutdown. A server-crash fixture terminated the serving process while its worker and child were active; Windows Job Object closure killed the subtree, the lock was released, and a new server marked the interrupted job FAILED without replaying it. This deliberately prevents concurrent server ownership; it is not a distributed queue or multi-server coordination.

Final focused regression: 22 passed, one existing Starlette/AnyIO deprecation warning, 107.24 seconds. JUnit: `reports/job-controls-20261026/tests-v015-final-verified.xml`. Command:

```powershell
rtk .venv\Scripts\python.exe -m pytest tests/test_integration.py tests/test_job_controls.py tests/test_memory_transactions.py -q --basetemp tmp/pytest-v015-current --junitxml reports/job-controls-20261026/tests-v015-final-verified.xml
```

Earlier broken-pipe, process-tree leak and test-timing failures remain in preserved reports; fixes and passing evidence are detailed in `reports/job-controls-20261026/VERIFICATION.md`, `task-update.json`, and `RELEASE.json`. Windows process-tree containment, cross-process ownership locking, and one active-job server-kill/restart/no-replay recovery scenario are verified for this local configuration. The POSIX TERM/KILL ordering has mocked unit coverage but no POSIX execution evidence. In-memory/non-SQLite/custom-thread jobs remain cooperative. Strict wall-clock completion and broader recovery under load remain unverified. Historical full suite not rerun. No model calls or labels changed.

The 95% independent, dependent and overall gates remain NOT_EVALUATED; independent judgments supplied: 0. Release readiness remains NOT MET. Continue from the next task in the master register after reconciling this section with `PROJECT_STATE.json`, `RESUME.md`, and `reports/execution/latest-status.json`. Preserve all archived evidence.

# Execution checkpoint - 26 October 2026, 02:45 UTC (superseded)

Project: IN_PROGRESS. Release readiness: NOT MET. This checkpoint supersedes the 25 October V015 checkpoint; the prior copy is docs/archive/EXECUTION_CHECKPOINT-20261025.md.

## Verified V015 milestone
File-backed SQLite API investigations run in a spawned Python worker with persisted deadlines and bounded cooperative/terminate/kill escalation. Final evidence, findings, graph changes and completed report publish in one SQLite transaction. The parent handles Windows broken-pipe behavior, failed worker exits and startup reconciliation without replay.

Final regression: 18 passed, one existing Starlette/AnyIO deprecation warning, 64.41 sec. JUnit: reports/job-controls-20261026/tests.xml. Command:
rtk .venv\Scripts\python.exe -m pytest tests/test_integration.py tests/test_job_controls.py tests/test_memory_transactions.py -q --basetemp C:\Users\Ankith\AppData\Local\Temp\vig-v015-recorded --junitxml reports/job-controls-20261026/tests.xml

The post-bounded-join job-control run passed 12 tests. Its cancel fixture writes a marker inside the worker runner before cancellation, proving an in-flight child stop. The abrupt-exit case proves no partial report or agent row is left. A pre-fix Windows WinError 109 is recorded in reports/job-controls-20261026/task-update.json and is fixed. Scope and limits: reports/job-controls-20261026/VERIFICATION.md and RELEASE.json.

## Other current evidence
- V008 paired-lineage UI/API: reports/frontend/2026-10-25T17-29-16-513Z/validation.json, pass for paired source, retained replay, stale-result clearing and conservative unknowns.
- Browser regression: reports/frontend/2026-10-26T02-17-03-746Z/validation.json, 13 pages and zero errors. It predates final V015 pipe/termination fixes.
- Frontend build passed after V015 UI text update; frontend unchanged by final fixes.
- Lineage/service combined run: 20 passed and one MCP subprocess timeout; isolated retry passed in 16.43 sec.
- Historical 368-test suite not rerun. No model calls or label changes.

## V015 limits and task state
V015 remains IN_PROGRESS: process-tree containment for Git/compiler/model descendants, multiworker ownership, strict wall-clock bounds, and real service-crash recovery are unverified. In-memory/non-SQLite/custom-thread jobs remain cooperative. Keep one server process. No historical snapshots changed. Source hashes for agents/control.py, agents/workflow.py, backend/app.py, database/store.py, frontend/src/main.jsx, tests/test_integration.py and tests/test_job_controls.py are in reports/job-controls-20261026/RELEASE.json. ZIP has no Git metadata.

V001 VERIFIED; V002 IN_PROGRESS; V003 IN_PROGRESS; V004 IMPLEMENTED; V005 IN_PROGRESS; V006 IN_PROGRESS; V007 IMPLEMENTED; V008 IN_PROGRESS; V009 IMPLEMENTED; V010 IN_PROGRESS; V011 IN_PROGRESS; V012 IN_PROGRESS; V013 IMPLEMENTED; V014 IMPLEMENTED; V015 IN_PROGRESS; V016 IN_PROGRESS; V017 IMPLEMENTED; V018 IMPLEMENTED; V019 IMPLEMENTED; V020 IMPLEMENTED; V021 IMPLEMENTED; V022 VERIFIED; V023 IN_PROGRESS; V024 IMPLEMENTED; V025 IMPLEMENTED; V026 IN_PROGRESS; V027 NOT_STARTED; V028 BLOCKED; V029 BLOCKED; V030 IN_PROGRESS; V031 IN_PROGRESS; V032 BLOCKED; V033 BLOCKED; V034 IN_PROGRESS; V035 VERIFIED.

## 95% and release
Independent, dependent and overall 95% metrics are NOT_EVALUATED; independent labels supplied: 0. The historical 85.11% development Recall@10 is not overall accuracy. No holdout was exposed or tuned. Release readiness is NOT MET.

## Next exact action
Inspect Git/compiler/model subprocess creation and add a file-backed worker test proving whether descendants survive forced termination. Implement bounded process-tree cleanup only with platform-supported evidence. Then verify/reject a second server process before making any ownership claim. Reconcile this checkpoint, PROJECT_STATE.json, RESUME.md, latest-status.json and task register with real files before resuming. Active project lease is null; no Python/Ollama worker was present after the previous process check.


## Reviewer handoff milestone - 2026-10-26 09:30 UTC

Added docs/REVIEWER_WORKFLOW.md with reviewer scope, blinding limits, evidence rules, unknown handling, adjudication, agreement interpretation and the separation between development and final evaluation. Added a deterministic agreement summarizer for nominal-label Cohen kappa/raw agreement and pairwise trace/affected-set metrics; it preserves undefined cases and warns that agreement is not accuracy or source verification. Updated the handoff README and V028 register/gap-matrix evidence.

Focused verification: tests/test_reviewer_agreement.py plus tests/test_review_intake.py - 8 passed, one existing Starlette/AnyIO deprecation warning. JUnit: reports/review-handoff-20261026/focused-review-tests.xml; milestone record: reports/review-handoff-20261026/VERIFICATION.json. Reviewer forms remain blank; no annotations, agreement values, model calls, or accuracy results were created.

V028 and V029 remain BLOCKED: qualified external reviewers, real adjudications, identity authentication, semantic-support reviews, a frozen repository/change-family-disjoint 200+ case final cohort and matching predictions are not present. The 95% quality gates remain NOT_EVALUATED and release readiness remains NOT_MET.

Next action: continue P0 security/release gates that can be checked locally. Then record exact platform, performance and dependency evidence. Do not claim independent validation or 95% until the external review and untouched test requirements are met.


## Clean release packaging milestone - 2026-10-26 10:06 UTC

The packaging inventory now prunes tmp/release-debug-restore and excludes .uv-cache. The release verifier rejects archives containing those generated restore/cache paths. This preserves the local restore workspace and dependency cache while preventing duplicate database snapshots and local runtime cache from entering releases. Both modified scripts pass py_compile.

The first clean build passed manifest and historical-file verification (12,610 files; 550 protected historical files; hash recorded in reports adjacent to the package). A fresh restore completed, but the app TestClient health/stat smoke did not return during bounded observation; app health for the rebuilt archive remains NOT_VERIFIED. A final ZIP is being regenerated after this checkpoint update, so use its own adjacent release-verification JSON as the authoritative archive hash and manifest result.

Release remains NOT MET. Quality targets remain NOT_EVALUATED. Do not infer the blocked 95% scientific gates from engineering or packaging checks.


## Dependency consistency check - 2026-10-26 10:15 UTC

The environment uses uv rather than pip in the project virtual environment. uv pip check --python .venv/Scripts/python.exe passed: 39 installed packages are compatible. npm --prefix frontend ls --depth=0 passed with React, React DOM and Vite present. These checks establish dependency consistency only; advisory vulnerability scanning and egress controls remain NOT_VERIFIED.

The reviewer workflow milestone remains bounded and tested (8 passed, 1 existing deprecation warning). Independent labels remain 0; the 95% independent/dependent/overall gates remain NOT_EVALUATED; release readiness remains NOT_MET. The output files VIGILANT-release-verification-20261026-final.json and VIGILANT-release-assessment-20261026.json contain archive manifest evidence and the app-health limitation.

Next exact action: continue locally verifiable P0 security, performance, and platform gates. Do not claim a vulnerability-free dependency set or 95% assurance quality from these checks.


## V041 — revision evidence, impact context, and confidence preservation (2026-10-27)
Raw model confidence values (including 0.95) are preserved unchanged. Added revision-scoped source facts and bounded graph impact candidates to advisory context; graph paths are explicitly noncausal. V2 permits orthogonal UNCERTAIN disposition and consistency classification. Added regression coverage. Case-level findings and precise limitations: reports/decision-contract-20261027/V041-root-cause-repair.md. Focused test: 19 passed; one cache-write warning. No inference was run; independent labels remain zero; 95% gates NOT_MET / NOT_EVALUATED; release NOT MET.


## V042 end-to-end validation (2026-10-27)
See reports/decision-contract-20261027/V042-verification.md and case-analysis-v042.json. Git metadata is absent, so no diff/status is available; V041 production hashes match the saved V041 checkpoint. Added six v2 storage/rendering combinations and a v1 persistence regression. Focused tests: 26 passed. Selected pipeline/integration tests: 32 passed, one existing deprecation warning. API/CLI/MCP spot checks stalled and were interrupted; full suite not run. No inference; independent labels remain zero; research acceptance NOT ESTABLISHED; release NOT MET.


## V043 confidence threshold audit (2026-10-27)
No production LLM confidence threshold exists. Cases 01/12 raw 0.80 values are preserved. Offline exploratory replay compared no cutoff, >=0.80, and >=0.95; zero errors were eliminated; correct predictions were suppressed (2 and 4 respectively). New script/test and report: scripts/replay_confidence_thresholds.py, tests/test_confidence_threshold_replay.py, reports/confidence-threshold-20261027/, experiments/confidence-threshold-20261027/. Test: 1 passed. No inference; research acceptance NOT ESTABLISHED; release NOT MET.


## V044 diagnostic repair implementation (2026-10-27)
See reports/diagnostic-improvements-20261027/V044-report.md and V044-focused.xml. Added Python comment-only classification, default-parameter observations, and literal route candidate comparison; no production finding labels are automatically assigned. Verification: 62 passed, no failures/errors/skips, one existing deprecation warning. No inference; saved 4/12 remains unchanged; 10/12 and 95% not established.


## V045 validation stop - inference unavailable (2026-10-27)
Fresh repository check confirmed V044 hashes and preserved historical 4/12. Safe preflight found no Ollama executable or model assets; no inference/network probe was made. V045 focused regression rerun: 62 passed, 0 failures/errors/skips, one existing deprecation warning; first temp setup attempt had four setup errors, fixed by creating the parent directory. Report and JUnit: reports/diagnostic-validation-20261027/. No new predictions; 95% acceptance NOT ESTABLISHED.


## V046 checkpoint (2026-10-27)
Verified frozen diagnostic SHA-256 c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864; authored score 4/12 unchanged. V044 source hashes match saved status. Added reports/v046 inventory, hash/frozen manifests, frozen adjudication protocol, form, 12 blinded sheets, pending reviewed_labels.json, replay environment/blocker manifests, V046 artifact test and JUnit/logs. Focused: 65 passed. Full: 353 passed, 11 failed, 82 errors (WinError 5 fixture Git-object unlinking; WinError 1314 symlink privilege; C++ overload assertion). API/report subset: 11 passed, 15 errors (WinError 5). Inference: 0 calls, BLOCKED; reviewers: 0, labels pending; independent/95% NOT_ESTABLISHED. Next: resolve Windows fixture permissions and C++ assertion in authorized Windows environment; obtain two independent reviewers; provide approved local inference assets and run frozen replay; then evaluate a disjoint cohort.


## V046 post-Windows-fixture rerun (2026-10-27T09:39:07+00:00)
API/report/persistence subset after fixture changes: 25 passed, 1 failed, 0 errors. The original 15 setup errors were resolved by clearing read-only attributes on disposable Git objects and using exact committed blob bytes (git cat-file) rather than CRLF-translated worktree contents. The remaining API subset failure is the symlink case (WinError 1314; symlink creation privilege unavailable). Full suite after these fixes: 442 passed, 4 failed, 0 errors; categories {"WinError 1314: symlink creation privilege unavailable": 3, "C++ cross-file overload-resolution assertion": 1}. No tests were skipped/softened. Next: validate on a Windows environment with authorized symlink privilege; investigate the C++ overload-resolution assertion; obtain reviewer submissions and approved model assets.


## GLM integration checkpoint (2026-10-28)
Added explicit optional Z.AI GLM provider, backend provider selection/preflight, dashboard and chat source options, environment example, integration documentation, and mocked transport/API tests. Focused command: project virtualenv pytest over tests/test_glm_provider.py, tests/test_release.py, tests/test_omniroute.py; result 35 passed, 0 failed, 0 skipped; JUnit in reports/glm-integration-20261028/focused-tests.xml. No GLM API key or .env exists; no inference or source transfer occurred, so GLM quality is NOT_MEASURED. Frontend build attempted but Vite is unavailable; source UI changed but built bundle unverified. Next: install/restore approved frontend dependencies in authorized environment; configure GLM credentials privately, confirm billing/data-transfer approval, then run a separately versioned diagnostic comparison and preserve the 4/12 baseline. No independent or 95% claim.


---

# V047 checkpoint â€” 2026-10-28

Project copy: C:\Users\Ankith\Downloads\vigilant project code; root .git absent. Verify live files against reports/v047/artifact_hash_manifest.json before continuing.

Completed: approved decisions are in docs/decision_policy.md; V3 multi-axis contract and legacy mapping; sourced revision-aware facts and deterministic rules; guarded local-only LLM stage; V3 context and report integration; evaluator, data-audit CLI, case schema/validator, coverage scaffold; provisional review entries remain PENDING. The original diagnostic hash is unchanged at c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864.

Tests: baseline 450 passed/4 failed. Focused V047 36 passed. Final full suite 485 passed/4 failed, 0 errors/skipped; all four failures match baseline (three symlink fixture setup failures WinError 1314, one C++ overload resolver failure). One existing deprecation warning. Inference preflight BLOCKED (Ollama executable and configured model manifest absent), 0 calls. No new accuracy was measured; independent labels 0; the 95% target NOT ESTABLISHED.

Next: inspect checkpoint/manifests and verify live hashes; when authorized model assets are available, run the exact preflight command in checkpoint_manifest.json. Do not run inference unless ASSETS_READY. Obtain two blinded independent reviewers and a repository/change-family-disjoint cohort. Resolve the four baseline failures without weakening tests.


## V047 code-review follow-up (2026-10-28T07:07:40+00:00)

- Focused verification: 46 passed, 0 failed; JUnit `reports/v047-followup-focused.xml`.
- Full suite: 500 passed, 4 failed, 0 errors, 0 skipped; same known three WinError 1314 symlink setup failures and one C++ overload-resolution failure; JUnit `reports/v047-followup-tests.xml`. Full run preceded final miner path-independent repository-ID tweak; focused miner test passed after it.
- Added Git-verified HEAD deletion receipt metadata, evidence collision disambiguation, supported-citation gate for every decisive LLM result, URL path route comparison, runtime JSON schemas, and local-only silver commit miner.
- Frozen diagnostic unchanged: SHA-256 `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. No inference, new accuracy, or independent evaluation. 95% NOT ESTABLISHED.
- Next exact action: rerun full suite after the final miner-only tweak if required, then proceed with authorized model preflight and independent adjudication preparation.


## V047 accuracy replay check (2026-10-28T07:15:28+00:00)

New V3 accuracy is NOT MEASURED. Offline rules replay was attempted with inference disabled; all 12 case folders lack `.git` metadata, so 0/12 predictions were produced. Historical Qwen3 8B remains 4/12 authored-label agreement, not independent accuracy. V3 uses orthogonal axes and the authored legacy labels are not multi-axis gold. Frozen diagnostic SHA-256 remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`. See `reports/v047/ACCURACY_REPLAY_STATUS.md` and `reports/v047/rules-only-diagnostic-replay.json`.


## V047 measurement harness (2026-10-28T07:23:57+00:00)

Added `tools/measure.py` with per-axis strict scoring, repository-cluster bootstrap intervals, per-rule results, paired exact McNemar and cluster-bootstrap differences. Five unit tests pass. Held-out evaluation NOT_RUN; no independently adjudicated multi-axis gold or frozen predictions; accuracy NOT_MEASURED. Frozen diagnostic SHA-256 `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864` unchanged. See `reports/v047/measurement-harness-status.md`.


## V047 measurement and full-suite validation (2026-10-28T07:47:29+00:00)

The frozen historical known-answer evaluator test passes: 4/12, macro-F1 0.325, Wilson approximately 13.8%–60.9%, majority 50%, and the eight saved mismatches. This is arithmetic validation against authored legacy labels only, not V3 quality. Harness tests: 7 passed. Full project suite: 507 passed, 4 failed, 0 errors, 0 skipped; 1 existing Starlette/AnyIO deprecation warning. Failures: three Windows WinError 1314 symlink setup tests and one existing C++ compiler-USR resolver test. JUnit: `reports/v047-full-after-golden.xml`. Held-out evaluation remains NOT RUN; new V3 accuracy NOT MEASURED; 95% NOT ESTABLISHED. Frozen diagnostic SHA-256 remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.


# V047 pilot-preparation checkpoint — 2026-10-28

The active source remains `C:\Users\Ankith\Downloads\vigilant project code`; it has no root Git metadata. The original diagnostic SHA-256 was verified before this update as `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.

- Completed a 5-commit-per-repository mining batch: 212 unreviewed candidate rows across 12 development repositories. Candidate category coverage is 9/24 mined D-ID categories, not accuracy. A 30-commit retry was interrupted and its partial output is preserved but excluded.
- Prepared stratified pilot v2: 24 cards, all labels null, all in `dev`, two identical blank reviewer sheets, frozen v2 protocol, and version-matched reviewer instructions. The original 12-case repository mapping remains unresolved; no test split is assigned.
- Targeted verification: 11 passed in 9.45s across miner, candidate-to-card, blind-review, and case-card tests; JUnit `work/miner-repair/caseprep-regression.xml` is in the Codex task workspace. The earlier direct miner suite was 4 passed in 9.10s. Full suite was not run in this bounded preparation step.
- No reviewer labels, model inference, new accuracy, or independent evaluation were produced. Development 33/36 is NOT MEASURED; independent 95% is NOT ESTABLISHED.

Next exact actions: obtain two blinded reviewer submissions if available; recover original 12-case repository/family mapping; then freeze a development cohort and run the preregistered evaluation. Do not place any family in a held-out split until mapping is verified. Model replay remains blocked pending authorized runtime and model assets.

## Original 12-case mapping audit correction — V047 v2

The v1 audit narrative incorrectly said no recorded commits matched local clones. Its per-case data actually showed the Flask BASE commit matching `pallets/flask` for cases 03–06 and 11. A repeat read-only `git cat-file -e` check under the authorized repository-access context confirmed commit `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35` and the verified clone remote `https://github.com/pallets/flask.git`. V2 preserves the v1 audit and corrects its narrative. RTMX and Full Stack FastAPI Template upstream origins remain unresolved; do not change the split.


## 28 October 2026 - V047 candidate-mining continuation

746 new, unique candidate records were mined from 10 sampled commits in each of 12 manifest-pinned repositories (seed 104730). All records remain UNREVIEWED_SILVER in dev; label fields are null. Candidate category coverage is 13/24 D-IDs, not accuracy. No predictions, adjudicated labels, frozen 36-case set, or test split were produced. The exact candidate-ID overlap with the earlier 5-commit sample is zero; semantic near-duplicates were not audited. Candidate data: `data/prepared/v047-candidates-20261028-10commits-seed104730.jsonl`; provenance: `reports/v047/mining-10commit-seed104730-20261028.json`. The frozen diagnostic hash remains `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.


## V047 inference preflight follow-up - 28 October 2026

Fresh local-only preflight reconfirmed Ollama/Qwen3 8B blocked (executable and model manifest absent) and local Qwen2.5 1.5B blocked (inference dependencies/configuration/tokenizer/weights absent). No service, network probe, or generation was attempted. Evidence: `reports/v047/inference-preflight-followup-20261028.md` and `reports/v047/inference-preflight-followup-20261028.json`. LLM + RAG + rules performance remains NOT MEASURED.


## V047 candidate card validation - 29 October 2026

The existing candidate-to-card adapter schema-validated 279 D-ID-tagged records from the 746-row 10-commit development pool. The other 467 generic changes have no D-ID and remain in the source pool. Converted records remain UNREVIEWED_SILVER/dev with null labels and pending adjudication. No new reviewer sample was created; the existing 24-card pilot remains unchanged. Accuracy is NOT MEASURED and the 36-case set is not frozen. Evidence: `reports/v047/candidate-card-validation-20261029.md` and `reports/v047/candidate-card-validation-20261029.json`.


## V047 development-pool integrity audit — 2026-10-29

Read-only audit completed across the frozen 12-case model input, 314 TEBench retrieval-development inputs, and the 212/746-row candidate pools. Diagnostic text screening flagged Cases 01 and 12 (0.9912 under the current case-preserving normalizer), with zero exact duplicate groups. Exact repository/revision/text screens found no overlap between the diagnostic and TEBench inputs. The mined pools have zero exact candidate/event/path/artifact-hash overlap with each other; `pallets/flask` is shared with the original diagnostic, so all such candidates remain development-only. All 958 rows remain unreviewed, with null labels. Semantic near-duplicate screening for candidates is NOT MEASURED because raw hunks are absent. No accuracy or inference result was produced. Details/hashes: `reports/v047/evaluation-pool-audit-20261029.md` and `.json`.

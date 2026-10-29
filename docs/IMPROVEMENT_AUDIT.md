# VIGILANT improvement audit — 23 October 2026

This follow-up implements the preservation baseline and a bounded correctness/input-audit pass requested in the detailed review. It does not complete the independent annotation or held-out evaluation phases. The latest target remains **91%, NOT_EVALUATED**. No new model generations were made.

## Baseline and changes

The full previous release was extracted into a separate working copy. Its SHA-256 is `41eab6b2aedd19b68d837ee8169b6b149e51989722a4683244fd263374dd84dd`. The source release is an archive, not a Git checkout; the separately retained upstream checkout is clean at `7eba731b99dc63c66e2872da1fcc8b723ce30945`. No commit or push was made. Frozen SQLite snapshots, prepared datasets and experiment files have a before/after hash check. See `reports/improvement-20261023/baseline.json` and `preservation.json`.

Baseline: **115 tests passed**, production frontend build passed. After fixes: **121 tests passed**, including six new regression checks. The existing dependency deprecation warning remains. The frontend was not changed. No fresh native Windows or full browser acceptance was performed for this follow-up; the previous release's 13-page Linux browser result remains historical evidence.

## Prioritized findings

| ID / priority | Module and observed evidence | Effect | Change / status | Validation or acceptance |
| --- | --- | --- | --- | --- |
| C01 / P0 | `ingestion/git.py`: diff subprocess inherited `diff.external` and textconv configuration. Synthetic fixtures wrote a marker before the fix. The independent review exporter had a second Git wrapper. | Reading an imported local repository could execute a configured helper. | Fixed shared reads with `--no-ext-diff`, `--no-textconv`, no pager, disabled fsmonitor and platform-native null hooks path. Exporter reuses that helper. This is not a general Git sandbox. | External diff and textconv regressions fail before and pass after; full suite passes. |
| C02 / P1 | `agents/evidence_first.py`: final 7,000-byte pass popped individual excerpts after paired selection; counters retained pre-trim values. | Model could receive one revision of a pair and misleading omission counts. | Fixed whole-pair omission, preserving explicit pair IDs across renames; refresh counts and citation maps. New policy `evidence-first-v3-paired-budget`. | 12-case offline comparison: split pairs 5→0; count mismatches 12→0. Boundary regression covers several excerpt sizes. |
| C03 / P1 | Same module called `investigation_request` again to construct the audit record. | Audit could describe a second selection rather than the actual request. | Capture selected/omitted provenance during the original request. Include actual message hash, bytes and omission reasons. | Counting fixture requests 2→1; recorded actual alias verified. |
| C04 / P1 | Same module invoked its engine with no source excerpts. | An interpretation could be requested from metadata alone. | Fail closed before engine invocation; return a validation failure/UNCERTAIN, retaining the reason. | Empty-evidence fixture calls 1→0. Four corrected diagnostic packets are empty; no inference was attempted. |
| R01 / P0 | `experiments/local-model-comparison`: 96 observations repeat 12 authored, correlated cases. | Repeated model runs cannot establish independent accuracy. | Exact saved-input audit and label-blind review packets exported. Independent labels still REQUIRED. | Two independent reviews, adjudication, evidence sufficiency and semantic support per case before interpreting these labels as reviewed. These cases remain development-only. |
| R02 / P0 | `llm/context.py`, `rag/evidence.py`: byte limits, role selection and changed-hunk windows are heuristics. | Useful contracts/counterevidence may be omitted; a byte limit is not an exact model-token limit. | Audit now records exact prompts, revision/role counts, omitted IDs, hunk-window overlap, actual provider telemetry and unresolved semantic sufficiency. | Controlled input ablation on reviewed development data; no test-label tuning. Empty pairs need a measured excerpt/budget policy, not relaxed citation checks. |
| R03 / P0 | `data/prepared`, `scripts/audit_dataset_quality.py`: link datasets have sparse/incomplete labels and duplicate text. | Unlinked artifacts may be unannotated, not negatives. | Recomputed read-only dataset audit; keep link recovery, impact and consistency separate. | Reviewed label provenance, explicit negatives and task-specific denominators. |
| R04 / P1 | `ingestion/parsers.py`, `ingestion/service.py`, `knowledge_graph/graph.py`: syntax/name/route heuristics; limited explicit FastAPI prefix adapter. | Cross-module, dynamic dispatch and framework resolution can be incomplete. A graph path is a candidate, not proof of impact. | Existing provenance retained; no compiler adapter added in this phase. | Per-language fixtures with ambiguity and unsupported syntax; reviewed dependency paths with edge origin/resolution. |
| R05 / P1 | `ingestion/git.py` suffix allowlist excludes C++/Swift; analysis coverage counts imported files. | Unsupported files disappear before parser coverage can represent all source files. | Coverage limitation documented. | Inventory eligible Git files before extraction; report supported, excluded, failed and unresolved counts. Implement compiler-aware adapters separately. |
| R06 / P1 | `backend/report_chat.py` regex intents and hop-count summaries; `/api/chat` combines previous user text for retrieval. | Follow-ups and graph explanations have limited scope resolution. | Chat preserved, not upgraded to a general project assistant. | Structured scope/intent tests, explicit edge-by-edge path payloads, revision-aware follow-ups; no inferred test coverage. |
| R07 / P1 | Source excerpts/API return repository content; explicit sensitive-content indexing/redaction policy absent. | A local report or selected external provider may expose secrets embedded in source. | Documented deployment limitation; no broad redaction patch in this phase. | Define exclusion/redaction with provenance and false-redaction tests; make provider data transfer clear. |
| R08 / P1 | Local shared token/loopback deployment; chat lacks a dedicated concurrency/rate limiter. HTTPS remote intake restricts host but does not provide a full redirect/network sandbox. | Service is not hardened for shared/public deployment or hostile imported repositories. | Keep local deployment boundary. | Threat-model intake, redirect/port policy, resource quotas, auth and failure paths before broader deployment. |
| R09 / P1 | `evaluation/quality_gate.py`: review and pipeline attestations supplied in JSON. | A threshold pass cannot authenticate human independence or represent every operation. | Draft protocol remains unfrozen. | Strong schema/finiteness checks and independent review records; separate engineering, trace, impact and classification gates. |

Before-fix failures are retained in `reproductions-before.log`. Tests use harmless synthetic helper scripts in temporary repositories; no imported project scripts were executed for analysis.

## Exact input and evidence experiment results

`input-audit/observations.json` covers 36 original Windows outputs, 36 citation-repair outputs, 12 evidence-v2 outputs and 12 change-facts outputs. All 96 observation/configuration/dataset fingerprints match. All excerpt mappings resolve, all mapped quotes match the frozen snapshot, all commits belong to the selected base/head pair, and historical inclusion/omission counts match. Ambiguous identical excerpts in six observations were resolved by the fingerprinted archived selector only after its complete excerpt array matched the saved input. This verifies provenance, not entailment.

The **new offline budget comparison** is distinct from those historical observations. It supplies identical question/evidence/static facts to the pre-fix and corrected wrappers, holds the 7,000-byte budget fixed, and uses no model completion. Rule candidates are empty in both arms. Its prompt-version identifier changes with the policy. It demonstrates structural packet fixes only; it does not show improved classification accuracy or compare retrieval methods. The saved historical runs did not use this wrapper's final budget pass.

Four corrected cases contain no complete evidence pair within the limit. These are visible failures of usable evidence coverage, not successes. Retained-pair counts and changed-hunk window overlap are descriptive; neither proves the relevant contract is present. Independent semantic support and counterevidence completeness remain unreviewed.

## Dataset findings

The recomputed audit retains the reported limitations: RTMX-module-valid has seven targets; SMOS has 32% orphan targets; eTour_en about 23.3%; iTrust about 61.5% with 26 unlinked sources. Normalized duplicate iTrust source text can have different linked targets; this warrants adjudication, not automatic relabelling. Filtering these records cannot manufacture a change-impact benchmark. Full counts, raw-file hash checks and descriptive retrieval intervals are in `dataset-audit.json`.

## Reproduction and review

From the project root, with core requirements installed:

```text
python -m pytest -q
python scripts/audit_diagnostic_inputs.py --output reports/my-input-audit
python scripts/audit_dataset_quality.py --output reports/my-dataset-audit.json
```

The input audit requires a new output directory and refuses to overwrite annotations. Read `reports/improvement-20261023/input-audit/review/README.md` before distributing review packets. Technical audit outputs include model telemetry and private case mappings; reviewers should receive only the packet directory, rubric and their own blank worksheet.

No database migration is required. Extract the updated package into a separate folder; do not replace a newer Windows live database with historical snapshots. Runtime binaries and model weights are excluded. See `DEPENDENCY_COMPATIBILITY.md`, `ARCHITECTURE_CURRENT.md`, `IMPROVEMENT_ROADMAP.md` and `EVALUATION_PROTOCOL.md` for remaining scope.

## Detailed audit v2 follow-up

See AUDIT_V2_RESOLUTION.md for the subsequent 131-test release. It resolves additional extraction/path/scorer defects, exposes repository coverage and claim support, prepares a 32-case unlabelled pilot and fixes the reported frontend dependency advisories. The earlier 121-test results and input-budget experiment above remain historical measurements. Neither release establishes independent 91% accuracy.

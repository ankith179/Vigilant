# Latest continuation - 28 October 2026, V047 maintenance 007

Focused suite: 13 passed, 0 failed/errors/skipped. Full suite: 513 passed, 3 failed, 0 errors/skipped; all three failures are WinError 1314 symlink privilege failures before assertions. See reports/v047/V047_MAINTENANCE_FOLLOWUP-007.md.

Saved 12-case authored-label regression replay is 11/12 (91.67%), development-only. Historical case-analysis SHA-256 remains c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864. No fresh inference ran. Independent performance and 95% remain NOT ESTABLISHED.

Next: resolve symlink test privilege failures in an approved Windows environment; obtain local Git clones and a second reviewer; mine and adjudicate a repository-held-out pilot; then freeze and run the independent evaluation. Refresh the package after code changes.

---

# Latest continuation — 27 October 2026, V040

Read the V040 checkpoint and resume prompt first. Frozen baseline prompts and transport schema are isolated from current schema v2; all 12 reconstructed saved prompts match. Four focused tests, 99 broader touched-module tests, and one isolated API worker test passed; see `reports/decision-contract-20261027/`. No model inference ran. The authored diagnostic remains 4/12; raw mismatch confidence `0.95` is preserved but uncalibrated. Independent labels remain zero; 95% targets remain NOT_MET / NOT_EVALUATED; release readiness remains NOT MET.

Next check authorized local model availability without bypassing WinError 10013; if unavailable, continue non-inference engineering.

---

# Latest resume instructions — 26 October 2026, V039

Start by inspecting the V039 section at the top of `docs/EXECUTION_CHECKPOINT.md`, then reconcile the real project files with `PROJECT_STATE.json`, `reports/execution/latest-status.json`, `docs/VIGILANT_MASTER_TASK_REGISTER.md`, and this file. This ZIP working copy has no Git metadata.

V039 added explicit modern schema v2 for orthogonal decision and consistency labels, kept legacy v1 behavior, and passed 14 focused tests. No LLM inference or accuracy improvement was measured. The raw `0.95` outputs are retained as the model's stated confidence, not calibrated probability. Broader test runs stopped before completion; full Windows acceptance remains unverified. See `reports/llm-diagnostic-error-analysis/decision-schema-v2.md`.

Next exact action: run remaining touched-path tests one module at a time with `-vv` and a fresh project-local `--basetemp` to identify where execution stops. Do not bypass WinError 10013. Independent labels are still zero, and the 95% dependent/independent/overall acceptance targets remain unmet or unevaluated.

---

# Prior resume state — 26 October 2026, 2026-10-26T16:47:13Z

First read the top section of `docs/EXECUTION_CHECKPOINT.md`, then inspect the actual repository and reconcile `PROJECT_STATE.json`, `reports/execution/latest-status.json`, `docs/VIGILANT_MASTER_TASK_REGISTER.md`, `RESUME.md`, and the files listed in the checkpoint. This ZIP working copy has no Git metadata. Do not assume prior tool state or model assets survived.

LLM diagnostic work is at V038 / IMPLEMENTED: saved-output audit only (Qwen3:8B 4/12 on dependent authored cases), case analysis generated, E1/E2/E5/E6 prepared (48 prompts), no new inference. TEBench saved RRF Recall@10 was replayed at 85.112% over 314 development cases. Independent and overall assurance remain NOT_EVALUATED; the 95% target is NOT_MET / NOT_ESTABLISHED. Read `reports/llm-diagnostic-error-analysis/README.md` and `docs/RESEARCH_GUIDED_EXPERIMENTS.md`.

The local Ollama CLI/runtime is absent in this copy, and the loopback preflight was blocked by WinError 10013; recheck only when local execution is available. If the pinned digest is then present, run the following command once per condition, setting `--run-local` to `E0`, `E1`, `E2`, `E5`, and `E6` in separate invocations: `rtk .venv/Scripts/python.exe -B scripts/llm_ablation_harness.py --run-local E0 --model qwen3:8b --max-calls 12`. If unavailable, do not substitute a cloud model or claim the ablation ran. Continue with the next feasible engineering gate and preserve all existing reports.

# Current continuation - 26 October 2026

## Current Windows code folder — verified 2026-10-26

This folder is the user-requested working copy. `COPY-VERIFICATION.json` records the 15,126-file path/size comparison and 7,394 code/document SHA-256 checks. The copied `.venv` was used to run seven focused tests successfully at this shorter path. The original checkout/runtime is retained; the local `.runtime/tebench` cache was not duplicated. The full suite remains not green (283 passed, 32 failed, 82 errors in the earlier run); do not claim full Windows acceptance.

The 95% traceability, consistency, end-to-end and independent-performance gates remain NOT_EVALUATED / NOT_MET. Independent judgments remain 0. See `reports/realworld-20261026/95-percent-target-update.md`.


## 95% target and code-location follow-up — 26 October 2026

The requested 95% traceability, consistency, end-to-end and independent-performance target is not achieved. Independent/dependent/overall assurance gates remain NOT_EVALUATED; independent labels are 0. On exposed TEBench development data (314 cases, 10 projects, 592 references), original RRF Recall@10 is 85.112%. The separately versioned test-source/resource candidate policy reached 84.995% after one recovery pass; its 95.265% inventory ceiling is descriptive only. It was not promoted. Authored diagnostics (rule-only 11/12; best saved LLM 4/12) are dependent and not assurance accuracy. See `reports/realworld-20261026/95-percent-target-update.md`.

`tests/test_test_evolution.py`: 6 passed. Full Windows run: 283 passed, 32 failed, 82 errors, one warning in 687.54 s; log `reports/realworld-20261026/full-suite-windows.log`. Errors include restricted temp/hard-link operations, and lineage Git fixtures encounter `Filename too long` from this long workspace path. A representative atomic-store test passed with elevated access; full suite remains not verified.

The user requested `C:\Users\Ankith\Downloads\vigilant project code` as the code folder. The destination existed and was empty when inspected. After this checkpoint and focused verification, copy the code/project artifacts there without deleting or moving the current `.venv`, `.runtime`, or source checkout. Keep the environment assets at their current location unless a verified target runtime copy is explicitly needed. Then run the focused tests from the shorter destination path. Do not overwrite non-empty destination content.

V026 repository-import URL/Git hardening has 40 current combined tests passing, including the V015 worker suite; evidence is reports/import-security-20261026/focused-regression.xml. Public HTTPS GitHub/GitLab allowlist, redirect and protocol restrictions, isolated Git config/temp cwd, and no-checkout cloning are implemented. Live network cloning, DNS pinning, egress firewall, compiler isolation and broad security acceptance remain open. Release readiness stays NOT MET; the 95% gates remain NOT_EVALUATED.

V015 file-backed SQLite worker isolation, Windows child-process-tree cancellation, cross-process single-server SQLite ownership, server-kill/restart/no-replay recovery, and mocked POSIX TERM/KILL escalation passed 22 focused integration, job-control and transaction tests. Latest evidence: reports/job-controls-20261026/tests-v015-final-verified.xml. V015 remains IN_PROGRESS for POSIX host execution, strict wall-clock bounds, non-SQLite isolation and multi-server coordination. V008 independent identity review remains open.

The 95% assurance target remains NOT_EVALUATED: independent, dependent and overall predictions are not frozen and independent labels supplied are zero. Release readiness remains NOT MET. Read docs/EXECUTION_CHECKPOINT.md before resuming and reconcile it with reports/execution/latest-status.json and the task register.

## Latest continuation - 25 October 2026

V008 paired-lineage controls were implemented. Production build passed; 21 focused tests passed. Browser control checks passed, but full acceptance remains IN_PROGRESS after the restored archive source scope rejected a request. See docs/EXECUTION_CHECKPOINT.md and reports/execution/latest-status.json.

95% assurance is NOT_EVALUATED: independent judgments and frozen predictions are absent; release readiness is NOT MET. Continue from docs/EXECUTION_RESUME_PROMPT.md. The historical 368-test result was not rerun.

# Shared lineage investigation tool — 25 October 2026

Restored newest full v54 (SHA-256 b642559eb37d11e8a52b2a2c1e5690f0faf796ba103c4d977b115db21eb0ad8a)
into a separate copy. Overlay v53 was older and not applied. No active lease or
worker was present. Interim overlay v54 was durably saved before full regression.
Current Git branch/SHA unavailable; current source fingerprint:
f76f5611e7085c70d102032c9adb5de9bf6dbba3f6445e6d42f579a6d0223557 (222 source/config/test files).

Added default-off inspect_lineage to the existing shared InvestigationService.
Set VIGILANT_LINEAGE_TOOLS=1 in the process to expose it through HTTP/CLI/MCP.
Require both indexed canonical revisions and 1–16 explicit paths. Selected parent
identity/type/full-span/content is checked against observer and pinned Git source;
full source is scanned before bounded paired canonical excerpts are returned.
Partial staged commits, forged/foreign source and unavailable revisions reject.
Retained-result and MCP resource reads rebuild both source roles, observer data,
evidence and adapter fingerprints. Turning the flag off also blocks retained reads.
Shared revision lookup converts missing Git subprocess failures into scoped rejection.

368 tests pass (nine new tool tests; initial 20-test focused check retained).
One existing dependency warning. Actual HTTP acceptance retains all nine authored
cases: eight accepted/revalidated sidecars and one missing-revision unknown (409);
all nine unauthenticated requests reject (401). One actual HTTP/CLI/MCP/resource
fixture returns identical retained JSON. Eight valid cases account for 19 base +
20 head artifacts using 11 candidate pairs and 17 unknown observations, plus seven
absent selected file sides. Sixteen tool unknown objects retain scope limitations.

New observations stay UNREVIEWED, logical continuity UNKNOWN, semantic support
NOT_ESTABLISHED. Observer IDs remain separate from frozen canonical IDs. No graph/
citation/obligation transfer, canonical investigation replacement or model call.
Only disposable fixture imports/tool/unknown records are written in acceptance;
frozen snapshots, historical graphs/results/labels/manifests remain unchanged.
Existing frontend bundle/build/browser evidence is reused; no dedicated UI control
or fresh browser run is claimed. Both quality gates NOT_EVALUATED; V008/project
IN_PROGRESS. No independent labels, final-test tuning, old benchmark reruns, current
Windows acceptance, paid service, external message, commit/push or full weight RL.

Read docs/LINEAGE_INVESTIGATION_TOOL.md and reports/lineage-tools-20261025/
VERIFICATION.md, RELEASE.json, task-update.json, acceptance/result.json and tests.log.
Counts and source hashes establish engineering scope, not semantic/lineage accuracy.
File/output bounds are not strict aggregate runtime preemption or security/RBAC
certification. Independent review and full symbol history remain unresolved.

Next: explicit lineage UI controls using exact base/head/path selection, paired
canonical source navigation, retained revalidation and stale-result clearing.
Preserve unknowns/frozen IDs and separate source observations from semantic review.
Independent review, disjoint final labels/evaluation and wider acceptance remain.

---

# Source-backed lineage observations — 25 October 2026

Resumed from full v53 plus newer saved overlay v53 after workspace replacement.
Source and eight acceptance records were recovered from that saved overlay. The
unsaved final full-suite files, documentation and packages were lost; they were
rebuilt and freshly verified, not recovered. No other worker was active. Existing
lease belongs to this continued increment and is cleared in the completed state.
Current branch/SHA unavailable; source fingerprint: bc63f95b9561c50047a40c544027eee1a5eec31c1d5bc4fc9c539de889fe8488
(220 source/config/test files). Fixture commits are not the project revision.

Implemented change_analysis/lineage.py, explicit standalone observer CLI and
acceptance runner. Pinned Git blob IDs/raw hashes and parsed endpoint receipts are
bound to a separate code/runtime/parser namespace. Fresh verification requires
expected project/repository/revisions/path selection. All observations stay
UNREVIEWED; logical continuity UNKNOWN; semantic equivalence NOT_ESTABLISHED;
no graph/citation/obligation transfer. Frozen canonical IDs remain unchanged.

Fresh 359 tests pass (15 new observer cases, including caller-canonical namespace
separation; one existing dependency warning). All saved acceptance records match
fresh reproduction: eight sidecars and one missing-revision unknown under nine
cases. 19 base + 20 head artifacts are accounted for by 11 candidate pairs and
17 unknown observations; seven absent selected file sides remain explicit. These
are authored engineering checks, not independent semantic/lineage labels.

No canonical consumers or Store writes, model calls, final-test exposure, historical
benchmark replay, current Windows run or full weight RL. Existing parser/delta/
backend/frontend callers and bundle are unchanged; their browser/build evidence
is reused. Both independent gates remain NOT_EVALUATED; V008/project IN_PROGRESS.

Read docs/LINEAGE_OBSERVATIONS.md and reports/lineage-observations-20261025/
VERIFICATION.md, RELEASE.json, workspace-recovery.json, tests-restored.log and
acceptance-restored/result.json. History is a bounded 32-commit file-deletion scan;
symbol disappearance inside surviving files and complete logical identity remain
unresolved. Caller context is not authenticated repository ownership. No approved
review lifecycle, strict aggregate runtime sandbox or automatic propagation exists.

Next: scoped opt-in existing-repository investigation-tool integration with source/
revision/identity/authentication guards. Preserve frozen IDs, all old evidence and
unknowns. Independent review/final disjoint labels and broader acceptance remain
prerequisites. Do not replay completed experiments or invent labels.

---

# Artifact lineage behavior audit — 25 October 2026

Restored full v52 into a separate archive copy. Overlay v50 has identical project
state and was not applied. No active lease or worker was found. Interim overlay
v51 saved before the full regression. No current Git branch/SHA exists in this
package; disposable authored fixture commit SHAs are not the project revision.
Current source fingerprint: 431c3a89c5f2f2e8a67eaf1c3203edd942a8cd697a0edae55971bcb9eff73a62 (216 source/config/test files).

Added scripts/audit_artifact_lineage.py and two regression checks. Nine authored
Python/Git fixtures record exact base/head commits, trees, blob inventories,
extracted artifacts, deltas and versioned observation IDs. Git 2.51.1 is recorded.
Pure/modified file renames pair same symbol/type under new path-bound IDs; a copy
stays a distinct ID. Missing revision fails closed. Five limits remain visible:
cross-file symbol move, renamed symbol, duplicate ordinal reuse, divergent branch
identity and an intervening delete/recreate hidden by identical endpoints.
All logical continuity remains UNKNOWN; source correspondence is not semantic proof.

344 tests pass, with one existing dependency warning. The final fixture source also
passes repeatability checks in the full suite; an earlier two-test focused log is
retained. No production code/identity behavior changed and no historical snapshot,
graph, label, benchmark or manuscript was rewritten. Existing frontend build and
browser evidence are reused because production sources/bundles are unchanged.
No model calls, independent labels, final-test tuning, current Windows or weight RL.
Both independent quality gates remain NOT_EVALUATED; project IN_PROGRESS.

Evidence: reports/lineage-audit-20261025/{VERIFICATION.md,RELEASE.json,
observations/result.json,tests.log,tests.xml,inventory/source-inventory.json}.
V008 remains IN_PROGRESS. Next: separately versioned opt-in lineage observations,
source/revision validation and ambiguity lifecycle, before production integration.
Preserve frozen artifact IDs. Independent review, final disjoint labels/evaluation
and broader security/language/platform/release acceptance remain open.

---

# Partial-report guided presentation — 25 October 2026

Restored full v51; overlay v48 matched state and was not applied. No active worker
or lease was present before work. This is a separate archive copy, with no current
Git branch/commit metadata and no canonical repository modification/commit/push.
Current source fingerprint:
67d3ddc763583927b55780df149e2b6c6f90aae10d9a18112c306350b22d2c6d
(214 source/config/test files; separately captured in the new report).

Partial Reports now offers six guided explanation topics: scope, changes, unknowns,
graph, evidence and limitations. Each freshly revalidates the original report and
exact pinned scope. Claims bind report-field JSON pointers and exact values with
REPORT_FIELD_MATCH_ONLY support. This is deterministic guidance, not free-form
semantic interpretation, reviewer authentication or independent entailment proof.
Unsupported intents/extra question instructions fail with 422. No model is called.

Server JSON and printable HTML exports freshly revalidate before delivery. HTML
shows scope, denominators, unknowns, coverage/obligations, graph limits, evidence,
limitations and validation, and retains the complete original JSON/provenance.
Repository text is escaped; restrictive content policy and no-store headers apply.
The UI clears old report/explanation/source data after presentation failures and
binds explanations/downloads to the selected report ID. Use local browser Print
for PDF; no external service. Partial CSV is not advertised; canonical exports
retain their prior contract. Pinned-registry configuration is unchanged.

342 tests pass (ten new presentation cases); 21 focused guards pass. All 32 original
reports pass 32 rotating-topic explanation requests plus 64 JSON/HTML export round
trips, retaining 371 UNKNOWN outcomes and the frozen source Store hash. This is
not 192 API topic combinations. Fixtures and the first browser report exercise all
six topics. Production build, all 32 report browser checks, print-export/field/
rejection recovery/mobile checks and the 14-page legacy browser regression pass.
Source hashes bind accepted UI receipts. No canonical writes, inference, independent
labels, historical benchmark reruns, final-test exposure or current Windows run.

Read docs/PARTIAL_REPORT_PRESENTATION.md and
reports/partial-report-delivery-20261025/{VERIFICATION.md,RELEASE.json,task-update.json}.
Original master/REA/job-control/source inventories, all 314 TEBench cases, source/
gold separation, failed-fetch records, recovery cache/results and training-only
negative bandit comparison remain unchanged. Both quality gates NOT_EVALUATED;
whole-project completion remains IN_PROGRESS and full REA parity unestablished.

Next dependency-ready work: V008 bounded rename/move lineage audit under separate
records, retaining ambiguity and every frozen logical/version ID. Independent
review, semantic adjudication and final disjoint evaluation remain prerequisites.
Do not replay completed experiments or fabricate labels. Check lease/processes and
save overlays around useful milestones. Hard preemption and broader project/
language/security/performance/platform/research acceptance remain open.

---

# Cooperative job controls — 25 October 2026

Restored full v50; overlay v46 matched state and was not applied. Baseline lease
was null and no live worker was found. Original master/REA/source inventories and
all historical benchmark/graph/source records are preserved. Current source:
98f3b129d50705e35f7d6f6a970495d3188d85acf40cf4bc8781e2f74ba2420a
(211 source/config/test files; separately captured under the new report). No Git
branch/current SHA is available in this archive; no canonical modification/push.

Added agents/control.py plus shared workflow/API controls: authenticated queued/
running cancellation, strict timeout_seconds (1–3600, default 900), original UTC
deadline preserved across queue time/restart, CANCEL_REQUESTED/CANCELLED/TIMED_OUT,
partial-run receipts, provider-boundary checks and protected final publication.
Dashboard exposes budget/cancel/status; comparison chat exits on stopped statuses.
Cancelled queue entries retain capacity until drained, preventing unbounded
executor placeholders under repeated queue/cancel requests. Terminal cancel is
idempotent. Restart never replays cancellation-requested or running work.

332 tests pass (eight new lifecycle tests); 35 focused regression tests and later
strengthened source/provider guard checks pass. Production build and 14-page
legacy Linux browser regression pass. A labelled cooperative-worker fixture drives
actual production UI/API cancellation, one-second timeout, chat terminal handling
and 390px checks. Those fixture outcomes are not research labels/predictions.
Earlier fixture-contract/download failures remain saved. No new model inference,
independent labels, benchmark reruns or native Windows acceptance.

This is cooperative stage-boundary stopping. In-flight Git/parser/compiler/model
operations finish under their existing limits; hard preemption/strict wall-clock
bounds, deeper crash recovery and multiworker ownership remain open. Final report
publication is protected from cooperative stops, not converted into one database
transaction. Direct/CLI/watch callers keep their prior budget unless they supply
RunControl explicitly; custom CLI/watch budget flags and history-wide UI
cancellation remain future work. The API always applies its validated budget.

Read docs/JOB_CONTROLS.md and reports/job-controls-20261025/VERIFICATION.md,
RELEASE.json and task-update.json. Master task V015 remains IN_PROGRESS for its
broader limits; the current docs point to the separately versioned update.
Both quality gates remain NOT_EVALUATED. All 314 TEBench cases, source/gold
separation, original failed fetches, recovery results and negative training-only
bandit comparison are retained. Full LLM-weight RL has not run.

Next dependency-ready step: V035 grounded partial-report chat and human-readable
exports, reusing exact report/source scope and preserving unknowns. Independent
review/semantic adjudication/final split freeze remain prerequisites; do not
invent labels or rerun completed experiments. Read the master register and active
lease/process state before continuing. Save overlays around useful milestones.

---

# Master directive assessment and partial-report application — 25 October 2026

Restored full v49 into a separate working copy; overlay v44 was older and not applied.
No root Git metadata/current branch/SHA is available. Source fingerprint:
92bca439c336b6c4e936bd20bccaa492ce6597d0a0be3e1e4be66c60c7730a9f
(207 source/config/test files). No canonical repository modification, commit or push.

The master directive is preserved as docs/MASTER_DIRECTIVE_20261025.md. Read
PROJECT_BASELINE.md, VIGILANT_MASTER_TASK_REGISTER.md (35 workstreams),
VIGILANT_INTEGRATION_GAP_MATRIX.md, VIGILANT_ACCEPTANCE_CRITERIA.md,
VERIFICATION_AND_EVIDENCE_POLICY.md and COORDINATION_LOG.md under docs/.
Current architecture was updated rather than replaced. The REA matrix inventories
229 tool contracts, 175 CLI command names and six MCP prompts at commit
8e6a95788688439baeeec8e54c9b3e845226f79d (MIT). All 68 captured source files match
upstream Git blobs. Runtime/behavioral REA parity remains NOT_ESTABLISHED.

Production Partial Reports now connects the opt-in API to pinned report scope,
base/head graph candidates, explicit unknown/withheld/out-of-page denominators,
exact-source navigation and JSON export. The new source route revalidates the
report and permits only its selected artifacts/saved graph endpoints at exact
revisions, then uses StagedInvestigationService. Access stays default-disabled;
set VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256 to the packaged registry hash in
PARTIAL_REPORT_API.md to enable. Existing importer guards/canonical records remain.

Checks: 324 Python tests; 11 focused API/source checks; production build; 14-page
legacy browser regression and all 32 real partial reports in the browser, retaining
371 UNKNOWN outcomes. Exact export, selected source/graph navigation, line bounds,
repeat selection, token mode, default-disabled mode, controlled 409 clearing and
390px layout pass. Earlier browser download and navigation-selector failures are
retained; final accepted receipts bind current source hashes. A valid but unselected
same-snapshot source is explicitly rejected. 53 graph and 32 report identities,
frozen Store counts and historical evidence are preserved. No inference/new labels.

Evidence: reports/partial-report-ui-20261025/VERIFICATION.md and RELEASE.json;
reports/master-audit-20261025/ holds source/task/REA/milestone inventories.
Both independent gates remain NOT_EVALUATED. Whole-project completion remains
IN_PROGRESS; independent review, final freeze/evaluation, deeper language/lineage,
job cancellation/deadlines, partial-report chat/human exports, broader security/
performance/platform acceptance and research submission remain open.

Next dependency-ready step: V015 cooperative cancellation/deadline controls on
an isolated database with queue/restart/cancellation acceptance, then V035 grounded
partial-report chat/exports. Do not rerun completed benchmarks or rewrite frozen
parser/artifact identities. User judgments and unavailable Windows access cannot
be manufactured. Use exact resume fingerprints and only free allowed resources.

---

# Opt-in partial report API — 25 October 2026

Added backend/partial_reports.py and two separate routes: GET /api/partial-reports
and GET /api/partial-reports/{report_id}. Existing report/analysis endpoints and
importer guards are unchanged. Access is disabled by default. Enable by setting
VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256 to the expected SHA-256 of
reports/staged-report-20261025/reports/result.json before starting the backend.
For this packaged registry the checksum is 3aff34390d4ba9da4284e66f4492ac0a75b57819fb519d68fed37f802903216b.

Listing is paged and explicitly requires validation on read. Report reads require
repository, base_commit and head_commit query parameters. The service verifies
registry/report identities, then recomposes the exact bounded report using the
validated immutable Store and source policy. Stale sources or changed report data
are rejected; no cache can bypass verification. Responses retain source receipts,
UNKNOWNs, graph candidate status, empty unreviewed findings and original report IDs.
Validation receipts bind the configured registry and access code hashes.
Workspace-token authentication covers both routes. No new user/tenancy claim.

Fresh checks: all 322 tests pass, including nine new API fixtures for default-off,
pagination, source identity, tampering, symlinks, revision scope, stale sources and
authentication. All 32 saved real-project development reports revalidate through
the API, preserving 371 UNKNOWN outcomes. Canonical Store and historical evidence
are unchanged; zero canonical writes, fetches, model calls or independent labels.
One existing dependency deprecation warning remains. Linux only; no new browser,
native Windows or public deployment acceptance. Both quality gates NOT_EVALUATED.

Next: clearly marked partial-report UI and exact-source navigation via the existing
verified inspection path, followed by browser acceptance. Report-chat integration,
reviewed registry intake, independent semantic adjudication and final frozen test
remain unfinished. No model-weight RL or accuracy improvement is claimed.

---

# Separate partial development reports — 25 October 2026

Added investigation/staged_report.py and scripts/compose_staged_reports.py. Composed
32 reports over staged comparison, revision-specific graphs and verified inspection
receipts. Each report binds source module fingerprints, canonical parser/repository
scope, pinned revisions, exact receipt/excerpt IDs and comparison provenance.
The report findings list stays empty without reviewed obligations. No MISSING_TEST,
semantic correctness, complete impact or negative-link label is inferred.

All 313 tests pass (five new report tests, six graph tests; one existing dependency
warning). All 32 cases compose: 141 observed extracted-content differences, 371
UNKNOWN artifact outcomes, 136 verified source-reference occurrences, four absent
references retained under 140. Canonical staged Store remains 29,647 artifacts and
zero analysis_runs/graphs/tool_results. No import, parsing, fetches, model calls,
independent labels, Windows execution or historical benchmark reruns.

Reports are separate JSON artifacts under reports/staged-report-20261025/reports.
Application API/UI/chat delivery and immutable live-Store attachment are unfinished.
Independent review, semantic adjudication and final-test freeze remain required.
Both independent quality gates remain NOT_EVALUATED. Current engineering progress
does not change the saved development retrieval result or establish 91% accuracy.

Next: explicit read-only application delivery, with identity/source revalidation,
unknown retention and no canonical report replacement. Do not bypass importer guards.

---

# Bounded partial staged graph projection — 25 October 2026

Added investigation/staged_graph.py and scripts/audit_staged_graph.py. Graph construction
uses a disposable in-memory Store. Frozen artifacts, importer guards and original
application graphs remain unchanged. Each delivered edge retains the original typed
candidate relationship, both verified endpoint receipts, separate projection identity,
revision, parser identity, source policy, module fingerprints and partial coverage.
Parse-error artifacts cannot produce delivered edges. Unavailable endpoints remain
UNKNOWN_SOURCE_SUPPORT. Every result has empty findings; no missing-test or causal
impact conclusion is inferred. Pagination and withheld counts retain denominators.

Fresh checks: 308 full tests and six new fixtures pass (one existing dependency
warning). All 53 snapshot scopes projected: 1,885 incident candidates; the selected
first pages examined 1,172, returned 1,151 source-verified candidates and retained
21 withheld/unavailable edges. 713 candidates are outside selected pages. These are
bounded engineering observations, not accuracy or complete graph coverage. All 140
packet entries remain accounted for, including four without source references.

The source Store still has 29,647 artifacts and zero analysis_runs, graph_nodes,
graph_edges or tool_results. No fetches, subject execution, model calls, labels,
reviewer judgments, Windows checks or historical benchmark reruns were performed.
Both independent quality gates remain NOT_EVALUATED.

Next: separately versioned partial-aware report composition consuming the comparison,
inspection and graph outputs. Full staged report/API/UI integration, reviewed
registries and independent semantic/final evaluation remain incomplete.

---

# Latest opt-in staged source inspection — 25 October 2026

Restored full v45; overlay v39 matched state and was not applied. Added a separate
StagedInvestigationService inspect_artifact route plus opt-in CLI. Strict pinned
scope and bounded excerpts reuse OfflineReviewSourcePolicy exact local/cache checks.
Result IDs bind excerpt/source receipts, full file status, partial snapshot coverage,
source policy and reader/inspection fingerprints. Sensitive source/arguments/results,
foreign scope, missing artifacts and invalid spans fail closed; no negative labels.
No Store/importer/parser/model/graph/result writes; original import guard retained.

All 136 available source references across 32 development packets pass via this
route (44 local / 92 recovery-cache), retaining four no-reference entries under
140. Frozen source Store remains 29,647 artifacts / zero analysis_runs, graphs or
tool_results. All 302 full tests / nine new focused fixtures pass. Existing dependency
warning retained. All 8,741 baseline files outside five mutable continuity/
checkpoint files match, including 550 historical files, source caches, blank forms,
labels, snapshots, maps, graphs and manifests. No old experiments/browser/doc reruns.

Read docs/STAGED_INSPECTION.md and reports/staged-inspection-20261025/
{RELEASE.json,AUDIT.json,inspections/result.json,VERIFICATION.md,preservation.json}.
Archive integrity/fresh restore receipt is the sibling release-verification JSON.
This is source navigation only, not full staged investigation/API/UI acceptance,
semantic support or independent quality. No fetches, model calls, independent
labels/obligations, commits/pushes or recovery of deleted unsaved measurements.
Both 91% and saved 95% NOT_EVALUATED; native Windows/full-weight RL NOT_RUN.

Next feasible local step: separately versioned partial-aware report/graph integration
using saved comparison + scoped verified inspection receipts, disposable live copies,
all UNKNOWNs and no-obligation/no-MISSING_TEST guard. Do not bypass importer guard or
run full analyze on frozen staged Stores. Independent reviewed registries, semantic
adjudication and repository/change-family-disjoint final freeze remain required.

---

# Latest coverage-aware staged comparison — 25 October 2026

Restored full v44; overlay v37 had matching state and was not applied. Added
investigation/staged_comparison.py over validated read-only StagedSourceReader
snapshots. Every observed union file/artifact has exactly one outcome; unchanged
entries stay visible. Missing map sides, unpaired artifacts and parse-error sides
remain UNKNOWN, never inferred additions/deletions, negative links or impact gold.
Both-side coverage and complete file rows, hashes/spans, source provenance and
comparison-code/payload fingerprints survive. No Git/parser/model/Store writes.

All 32 development pairs pass with 6,618 union file observations (6,504 same
object ID, 110 different, four UNKNOWN) and 17,879 union artifact observations
(17,367 equal extracted hashes, 141 different, 371 UNKNOWN). Case-weighted side
slots retain all 363 unavailable artifact sides and four absent partial-map file
sides. These are engineering observations over partial maps, not independent
quality or complete project denominators. Source-only Store remains 29,647
artifacts / zero analyses / zero graphs. Original application graph is unchanged.

293 full tests / 27 focused checks pass, with 16 new regression cases. Initial
fixture failure retained: selected README contained no numeric literal, fixed to
select Python file; production rules unchanged. All 8,693 baseline files outside
five mutable continuity/checkpoint files match, including all 550 historical
files, original source caches, snapshots, labels/forms, maps, graphs and manifests.
Read docs/STAGED_COMPARISON.md and reports/staged-comparison-20261025/
{RELEASE.json,AUDIT.json,comparisons/result.json,VERIFICATION.md,preservation.json}.
Fresh archive smoke/integrity receipt is the sibling release-verification JSON.

Actual staged investigations remain NOT_RUN; this is comparison only. Raw source
verification is separate from map/Store checks. All search dispositions remain
UNKNOWN; no independent labels, obligations or judgments created. Both 91% and
saved 95% NOT_EVALUATED; native Windows/full-weight RL NOT_RUN. No fetches,
inference, commits/pushes, browser/doc reruns or lost unsaved-result recovery.

Next feasible step: explicit opt-in partial-aware investigation routing using
validated reads/comparisons, scoped raw-source verification and separately
versioned graph/report provenance. Do not bypass import guard or use full analyze
on frozen partial snapshots. Real reviewed registries, semantic adjudication and
repository/change-family-disjoint validation/final freeze remain required.
Preserve all unknowns and historical/negative evidence; no calendar waiting.

---

# Latest validated read-only staged source access — 25 October 2026

Restored full v43; overlay v35 had matching state and was not applied. Added
StagedSourceReader in investigation/staged.py: checksum-pinned immutable/read-only
SQLite + map/index/staging bindings; canonical identity, exact payload/span/hash,
coverage and denominator checks. No Store/import/Git/parser/model invocation.
All file statuses and UNKNOWNs returned; caller mutations do not persist.

All 53 snapshots / 32 development cases / 29,647 artifact versions validate.
All 10,970 UNKNOWN rows and gaps remain explicit (982 missing blobs, 12 parse-error
flags, 2,485 unsupported suffixes and 48 nonregular entries). Write attempt rejected;
audit forbids subprocesses during reads. Frozen source Store hash/counts unchanged.
277 full tests / 17 focused checks pass, with 11 new regressions. All 8,679 baseline
files outside five mutable continuity/checkpoint files match, including all 550
historical files, raw caches, labels/forms, graphs, snapshots, maps and manifests.

Read docs/STAGED_SOURCE_READER.md and reports/staged-source-reader-20261025/
{RELEASE.json,AUDIT.json,probe/result.json,VERIFICATION.md}. Reader verification is
map/Store structural correspondence; raw Git validation is NOT performed by it.
The existing scoped evidence verifier remains separate. Do not infer path/artifact
deletions or negative links from absent partial-map rows. No comparison/workflow
adapter or real completed staged investigation is claimed. Import guard retained.

Next feasible local step: coverage-aware comparison of validated staged snapshots,
retaining unknown/unavailable outcomes and every denominator. Then opt-in partial-
aware investigation routing with source/graph/report provenance. Real independent
review, semantic adjudication and disjoint final freeze remain external. Both 91%
and saved 95% NOT_EVALUATED; native Windows/full-weight RL NOT_RUN. No inference,
source fetches, labels, commits/pushes, browser rerun or lost unsaved-result recovery.
Prior manuscripts, browser evidence and all negative studies are preserved.

---

# Latest staged investigation routing audit — 25 October 2026

Restored full v42; overlay v33 had matching state and was not applied. Audited all
53 staged snapshot routes / 32 development cases without writes/fetches/reparse.
Default project IDs differ on all routes; explicit canonical project IDs match.
Fixed import_repository to reject staged review_source_map commits BEFORE metadata
writes. Empty markers and absent artifacts cannot bypass it. Ordinary snapshot
reuse remains available. This is a preservation guard, not a completed adapter.

53 actual guarded routes have zero metadata write attempts. All 10,970 file-status
entries and 29,647 artifact versions remain unchanged. The source-only Store still
has no completed investigations/graphs; the original application graph is preserved.
266 full tests / 17 focused checks pass (seven new guard regressions). All 8,665
baseline files outside six mutable continuity/checkpoint/importer files match,
including all 550 protected historical files, raw source/cache, forms, labels,
benchmark failures/results, maps, snapshots, graph provenance and manifests.

Read docs/STAGED_INVESTIGATION_ROUTING.md and reports/staged-routing-20261025/
{RELEASE.json,AUDIT.json,probe/result.json,audited-source-fingerprints.json,VERIFICATION.md}.
Full analyze still uses blob diffs, size-based coverage and Git-only source checks;
missing partial artifacts cannot be called additions/deletions or negative links.
Do not bypass the guard or call full analyze on frozen canonical Stores. Actual
staged investigations NOT_RUN; no model inference, source fetches, reviewed labels
or commits/pushes. Both 91% and saved 95% NOT_EVALUATED; current Windows/full-weight
RL NOT_RUN. Prior browser/drafts retained; no lost unsaved results recovered.

Next feasible local step: validated read-only staged-source snapshot access with
explicit file-status coverage, then opt-in partial-aware investigation routing
without re-import or parser-ID rewrites. Use disposable live DB copies for future
execution. Real independent annotations/semantic adjudication and disjoint final
freeze remain required. Never invent obligations/labels or repeat old model/Java
absence diagnostics.

---

# Latest offline immutable obligation-report attachment — 25 October 2026

Restored full v41; overlay v31 had matching state and was not applied. Added the
explicit scoped source policy to attach_obligations and its CLI. Parent, derived
and reused-derived citations are reverified. Opt-in report IDs bind parent,
registry, policy and attachment source fingerprints; default IDs remain unchanged.
Source receipts survive saved report/API/JSON export. No parent/model/graph or
artifact records are rewritten; unknown/counterevidence/no-obligation guards remain.

259 full tests / 30 focused checks pass, with 11 new authored regressions and one
negative CLI check. All 8,653 baseline files outside seven authorized mutable
continuity/checkpoint/attachment files match, including all 550 protected historical
files, original Git caches, snapshots, forms, labels, graphs, manifests and packets.
Read docs/OFFLINE_OBLIGATION_REPORT.md and reports/offline-obligation-report-
20261025/{RELEASE.json,AUDIT.json,real-source-readiness.json,VERIFICATION.md}.

Actual real-project attachment NOT_RUN: the canonical source-only Store has zero
analysis runs and no real reviewed registry supplied. All 32 cases and both
reviewer forms remain blank. No synthetic parent/review labels were inserted to
claim acceptance. No source fetches, model inference, commits/pushes or native
Windows/browser rerun. Both 91% and saved 95% gates NOT_EVALUATED; full-weight RL
NOT_RUN. Original application graph and historical model/bandit results preserved.
No unsaved experiment results removed by maintenance were recovered.

Next feasible local step: audit existing-snapshot investigation routing for the
canonical partial Store, avoiding re-import/fetch/parser-ID rewrites and keeping
unknown coverage explicit. Real independent annotations, semantic adjudication
and a disjoint frozen final test remain required. Never invent reviewed obligations
or labels, or repeat old model studies/Java absence diagnosis. Use disposable live
copies of frozen databases for Store/API/CLI operations.

---

# Latest scoped offline obligation assessment — 25 October 2026

Restored full v40; overlay v29 had matching state and was not applied. The reuse
audit identified reference, historical inventory, CLI and derived-report paths.
The first three now support the explicit offline source policy with receipts.
Default checks/fingerprints and no-obligation/no-MISSING_TEST logic are unchanged.
Saved-report attachment still uses default Git and remains the next local step.

All 53 pinned search boundaries / 32 development cases / 10,970 UNKNOWN entries
verify without blob-size reads or fetching. SEARCHED sources require eligible
regular files and exact source verification; all historical inventories are checked.
248 full tests / 53 focused checks pass, with 14 new regressions and two negative
CLI checks. One initial authored fixture failure is retained: the schema correctly
rejected UNMET with partial search. Fixed fixture satisfaction to UNKNOWN, without
weakening production guards. No actual reviewed-registry intake or labels created.

Read docs/OFFLINE_OBLIGATION_ASSESSMENT.md and reports/obligation-source-policy-
20261025/{RELEASE.json,AUDIT.json,enumeration/result.json,VERIFICATION.md}.
All 8,636 baseline files outside nine mutable continuity/checkpoint/verification
files match, including all 550 historical files, original Git caches, snapshots,
forms, graph, manifests, maps and packets. No lost unsaved measurements recovered.
No source fetches, inference, commits/pushes, Windows or browser rerun. Both 91%
and saved 95% independent gates remain NOT_EVALUATED; full-weight RL NOT_RUN.

Next: connect the explicit source policy to immutable obligation-report attachment
and CLI, checking both parent and derived citations and fingerprinting policy-
specific report IDs. Preserve parents/models/graphs. Real independent annotations,
semantic adjudication and disjoint final freeze remain external requirements.
Never invent reviewed obligations or labels, or repeat old model studies/Java
absence diagnosis. Frozen DBs need disposable writable copies for Store APIs.

---

# Latest opt-in offline reviewer intake — 25 October 2026

Restored full v39; overlay v27 had matching state and was not applied. Added the
explicit OfflineReviewSourcePolicy to validate_reviews and paired opt-in CLI
flags. Default Git validation is unchanged; policy plus disabled source checks
is rejected. Source receipts bind exact Git tree/blob identities, cache/queue/
verifier fingerprints, canonical artifacts and reference spans. Unknowns and
independent reviewer/adjudication requirements remain intact. No original Git
cache writes, source fetches, inference, labels or commits/pushes.

234 full tests / 21 focused tests and three negative CLI checks pass (11 new
regressions). Source-only audit verifies 44 local + 92 recovered references,
retaining four missing-reference entries in denominator 140. Both blank reviewer
forms remain rejected; actual independent intake NOT_RUN. The CLI negative
blank-form check used a disposable writable copy, never the frozen Store.

Read docs/OFFLINE_REVIEW_SOURCE_POLICY.md and reports/offline-review-policy-
20261025/{RELEASE.json,AUDIT.json,receipts/result.json,cli-checks.json,VERIFICATION.md}.
All 8,625 baseline files outside seven mutable continuity/checkpoint/intake files
match, including all 550 protected historical files, source caches, snapshots,
forms, labels, graph, manifests and original maps/packets. No unsaved deleted
experimental results were recovered. Both 91% and saved 95% gates NOT_EVALUATED;
current native Windows and full-weight RL NOT_RUN. Prior browser/drafts retained.

Next feasible local step: audit optional reviewed-obligation intake for safe reuse
of the scoped source policy/receipts, preserving lifecycle/search inventories
and the no-obligation/no-MISSING_TEST guard. Real independent reviews, semantic
adjudication and disjoint final-test freeze remain required. Never invent reviewed
obligations or labels; do not rerun old model studies or Java absence diagnosis.

---

# Latest offline reviewer-source readiness — 24 October 2026

Restored full v38; overlay v25 had matching state and was not applied. Probed all
140 changed-file side entries without network or original Git-cache writes.
Local-only: 44 verified, 92 unavailable blobs, four absent pinned-tree paths.
Scoped verified cache: 44 local + 92 recovered source references verify; four
absences remain unresolved in the denominator. Pinned-tree membership, exact raw
Git hashes, canonical identities, stored spans and all excerpts were checked.

223 full tests / eight new focused checks pass. All 8,615 baseline files outside
five mutable checkpoint/continuity files match, including all 550 historical
files, graphs, labels, forms, manifests, source caches, maps and both Stores/packet
versions. Read docs/REVIEW_SOURCE_READINESS.md and reports/review-source-readiness-
20261024/{RELEASE.json,AUDIT.json,probe/result.json,VERIFICATION.md}.
No source fetches, inference, labels, commits/pushes, Windows or browser rerun.
No unsaved experiment results removed by maintenance were recovered.

Next feasible local step: integrate this scoped offline source verifier as an
explicit opt-in reviewer-intake policy with provenance receipts. Actual intake
remains NOT_RUN: forms are blank and validate_reviews has not been changed to
consume the cache. Preserve default checks, independent reviewer/adjudication
requirements, frozen sources and unknowns. This is source readiness, not semantic
support or an independent accuracy result. Both 91% and saved 95% gates remain
NOT_EVALUATED; current native Windows acceptance and full-weight RL NOT_RUN.
Real reviews, semantic adjudication and disjoint final-test freeze remain required.
Do not repeat old model studies, recovery scans or Java absence diagnosis.

---

# Latest recovered-source reviewer Store and packets — 24 October 2026

Restored full v37; overlay v23 had matching state and was not applied. Reused the
existing builders to stage NEW data/snapshots/pilot-review-recovered-20261024.db
and reports/recovered-review-20261024/packets, preserving all earlier versions.
Four repositories / 53 snapshots / 29,647 artifact versions and all 10,970 file
statuses remain explicit. 136 source references across 32 packets verify, with
four absent pinned-tree paths retained. All reviewer and adjudication judgments
remain blank; all search dispositions UNKNOWN. No new labels/fetches/inference.

215 tests, 53 API navigation checks and all artifact/map/payload/packet checks pass.
8,564 baseline files unchanged outside five mutable continuity/checkpoint files,
including all 550 protected historical files. Read docs/RECOVERED_REVIEW_STORE.md
and reports/recovered-review-20261024/{RELEASE.json,AUDIT.json,VERIFICATION.md}.
Never open frozen snapshots with a writable Store: use a disposable live copy.
No unsaved deleted experiment results were recovered.

Next feasible local step: verify reviewer-intake readiness for exact recovered
cache sources without weakening default Git/source checks or writing original
Git caches. Current blank forms remain invalid for intake. Independent review,
semantic adjudication and a disjoint frozen final test still require real work
outside this automation. Both 91% and saved 95% gates remain NOT_EVALUATED; current
native Windows NOT_RUN. Do not rerun old model studies, local recovery or Java
absence diagnosis. Existing documents/browser evidence retained for their scope.

---

# Latest verified-cache pilot maps — 24 October 2026

Restored full v36; overlay v20 had matching state and was not applied. Prepared a
NEW parser-identity map version using all 79 verified recovered objects, without
fetching or rewriting original Git caches. All 53 snapshots / 32 development cases
retain 10,970 file entries and UNKNOWN search dispositions. 89 recovered snapshot
file rows cover all 92 queued case-side occurrences, producing 29,647 artifact
versions. 982 other missing blobs, 12 syntax-error flags and four absent pinned-tree
paths remain explicit. No independent labels, inference, commits or pushes.

Read docs/VERIFIED_CACHE_PILOT_MAPS.md and reports/verified-cache-maps-20261024/
RELEASE.json, AUDIT.json, VERIFICATION.md, preservation.json and maps/index.json.
215 full tests / 26 focused checks pass (seven new regressions). All 8,496 baseline
files outside seven explicitly mutable builder/continuity/package-metadata files
match, including all historical experiments, inputs, graph, original maps/Store/
packets, cache and labels. No unsaved deleted experimental results were recovered.

Next feasible local step: stage the NEW maps in a NEW isolated source Store under
their parser identity, then create NEW canonical packets with null judgments. The
staging validator now recognizes this exact additional policy. Never overwrite old
maps/snapshots/packets or claim complete semantics. Real independent reviews,
semantic adjudication and a disjoint final-test freeze remain external. Both 91%
and saved 95% gates remain NOT_EVALUATED; current native Windows NOT_RUN. Do not
repeat historical model studies, negative local recovery or Java path diagnosis.

---

# Latest exact source recovery — 24 October 2026

Restored full v35; overlay v18 was older. Local candidates recovered zero of the
79 queued blobs; 79 cache misses, 886 byte mismatches and four unavailable candidates
are preserved. A bounded authorized read-only GitHub pass then returned all 79 exact
objects. All passed native git hash-object, covering 92 missing file-side entries.
Four absent pinned-tree paths remain unresolved. No original maps/stores/packets,
Git caches, failures, graphs, labels or manifests were rewritten. No model inference.

Read docs/PILOT_SOURCE_RECOVERY.md and reports/local-source-recovery-20261024/
VERIFICATION.md, RELEASE.json, AUDIT.json, recovery/result.json and
upstream-verified/result.json. Raw validated bytes are in upstream-verified/objects;
79 original responses and pinned license notice provenance are retained. 208 full
suite tests / four focused checks pass. No unsaved experiment results were recovered.

Next feasible step: consume this validated cache in separately versioned partial
artifact maps under a NEW parser identity, then a new source store and packet
version. Preserve all frozen originals, unknown regions and null reviewer judgments.
Do not repeat the negative local scan or old model studies/22-Java-path diagnosis.
Independent annotations, semantic adjudication and disjoint final-test freeze still
remain external. Both 91% and newer 95% gates remain NOT_EVALUATED. Current native
Windows acceptance remains NOT_RUN.

---

# Latest canonical review packets — 24 October 2026

Restored full v34; overlay v16 was older. Prepared separate canonical-ID packets
for all 32 original development cases, with original patches and null judgments.
140 changed-file side entries include 44 stored source references, 92 missing local
blobs and four absent pinned-tree paths. All 44 references match stored source;
43 unique pinned-Git excerpt checks pass. Two reviewer forms and 32 adjudication
cases remain blank and invalid for scored intake. Packets are NOT review-complete.

Read docs/CANONICAL_REVIEW_PACKETS.md and reports/canonical-review-20261024/
VERIFICATION.md, RELEASE.json, AUDIT.json, packets/manifest.json and
SOURCE_RECOVERY_QUEUE.json. 204 full tests and four focused tests pass. Original
snapshots, graphs, packets, labels and forms are unchanged. No inference/fetches.

Next feasible local step: check existing worktree/cache candidates against the 79
distinct missing Git blob IDs in the queue; preserve every unresolved/mismatched
entry in a separate recovery record. Do not rewrite frozen maps or infer new files
from absent paths. Actual independent review/adjudication, semantic support and a
disjoint final-test freeze remain required. Both 91% and newer 95% gates remain
NOT_EVALUATED. Do not rerun old model studies or the 22-Java-path diagnosis.
Current native Windows acceptance remains NOT_RUN.

---

# Latest isolated review store — 24 October 2026

Restored full v33; overlay v14 was older. Staged existing maps, without reparsing,
into data/snapshots/pilot-review-20261024.db: 4 repositories, 53 snapshots, 28,291
artifact versions. All 10,970 file statuses and UNKNOWN dispositions are preserved,
including 1,071 missing blobs and 12 parse-error flagged files. Original databases,
graphs, artifacts, packets and null reviewer forms remain unchanged.

Read docs/PILOT_REVIEW_STORE.md and reports/pilot-store-20261024/VERIFICATION.md,
RELEASE.json, AUDIT.json and STAGING.json. 200 full tests / six focused checks pass;
53 API snapshot checks and pinned-Git source samples pass on a disposable writable
copy. The frozen snapshot remains unchanged. Never open it with a writable Store;
create a fresh live store using the documented builder and run from project root.

Next feasible local step: generate separate canonical-ID source packets for the
32 development pilot cases, keeping judgments null and source gaps explicit.
Real independent reviews/adjudication, semantic support and disjoint final-test
freeze remain required. Both 91% and the newer 95% gates are NOT_EVALUATED.
No new inference/source fetches/labels. Current native Windows remains NOT_RUN.
Do not repeat historical model studies, old drafts or Java absence diagnosis.

---

# Latest offline pilot artifact maps — 24 October 2026

Restored full v32; overlay v12 was older. Prepared source maps for all 53 snapshots
and 32 existing development cases. All 10,970 file entries retained: 7,354 parsed,
12 parsed with syntax-error flags, 1,071 missing local blobs, 2,485 unsupported
suffixes and 48 nonregular files. 28,291 artifact versions validated. A separate
canonical parser identity contains the offline policy and source digest. Original
artifacts/graphs/databases/packets/labels are untouched. No inference or source fetch.

Read reports/pilot-artifacts-20261024/VERIFICATION.md, RELEASE.json, audit.json and
maps/index.json. 194 full tests and 13 focused checks pass. UNKNOWN dispositions
remain UNKNOWN; no research labels were generated. Both 91% and newer 95% gates
remain NOT_EVALUATED. Do not rerun maps into existing outputs or claim full semantics.

Next feasible local step: stage these maps in a separate development-only Store for
reviewer navigation, preserving all partial-coverage manifests and original databases.
Actual independent reviews/adjudication, semantic support and disjoint final-test
freeze are still external requirements. Do not repeat old model studies or Java
absence diagnosis. Current native Windows acceptance remains NOT_RUN.

---

# Latest UNKNOWN search drafts — 24 October 2026

Restored full v31; overlay v10 was older. Reused build_search_inventory.py; it now
refuses overwrites/empty boundaries and reads tree identities without blob sizes.
All 32 existing development pilot cases map to 53 snapshots / 10,970 UNKNOWN entries,
no failures. These are NOT reviewed labels or source-content verification. Original
pilot aliases and all reviewer forms remain unchanged. Preserve interrupted preparation
record and frozen experimental results. 192 full tests + 11 focused tests pass.

Read reports/search-drafts-20261024/VERIFICATION.md, RELEASE.json and prepared/index.json.
Do not rerun preparation into its existing output. Next feasible local step: prepare
separate parser-identity artifact maps for already available pilot sources; retain
missing-source gaps and original packets. Actual review/adjudication and a frozen,
disjoint independent final set are still required. Both 91% and newer 95% gates remain
NOT_EVALUATED. No model study/Java path diagnosis needs repeating. No new inference.

---

# Latest search provenance increment — 24 October 2026

Continue from full v30 plus the current saved increment. Optional Git inventories
already existed; do not reimplement them. Fixed explicit artifact/commit identity
checking and verification of every historical lifecycle search inventory, with
five new regression cases. 191 tests and 30 focused checks pass; all 550 protected
historical files unchanged. No new inference, independent labels or final-test use.

Read reports/search-provenance-20261024/VERIFICATION.md and
RELEASE.json, docs/VERIFICATION_OBLIGATIONS.md and the existing capability matrix.
The scheduled 91% and saved newer 95% gates both remain NOT_EVALUATED. Preserve
both protocols and the current target; do not lower it. Next: independently
reviewed development registries, exclusion rationales and explicit unknown regions.
Independent labels/frozen disjoint final cases remain required. Do not repeat
historical inference or Java path diagnosis. Native Windows remains unverified
for this increment. Older overlay v9 was inspected but not applied over full v30.

---

# Current checkpoint — VIGILANT investigation tools and 95% target

The current target is 95%. It is NOT established. Recomputed saved development
changed-test retrieval remains 85.11% Recall@10 (314 cases, 10 projects). Historical
citation-repaired authored diagnostic best is 4/12. Neither is independent assurance
correctness. No new inference or independent human labels were generated.

The current increment adds investigation/service.py, the shared validated tool
contracts, retained content identities and unknown revision histories, five bounded
recipes, CLI/MCP/API/UI access, optional source-pinned search inventories, full
artifact Git checks and the separate evaluation/quality-target-95.json protocol.
No external reference was cloned and no third-party source code was copied.
Existing functional pipeline, graphs, RAG, chat, snapshots and experiments remain.

Read docs/VIGILANT_CAPABILITY_MATRIX.md, docs/CLI_REFERENCE.md,
docs/MCP_REFERENCE.md, docs/EVALUATION_PROTOCOL.md and reports/final-95/.
The broad project remains incomplete: independent semantic labels and final 95%
evaluation, full compiler/build semantics, full-weight RL, autonomous patches,
live-provider/hosted-database deployment, native Windows acceptance and institutional
submission remain open. Both connected database accounts had no projects; no
remote writes were made. GitHub was read only; changes were not pushed.

Continue from this checkpoint. Preserve all historical experiments and existing
Windows databases. Extract into a separate folder, install core dependencies, run
scripts/restore_checkpoint.py and start the usual backend. Use Investigation Tools
in the application or python vigilant.py --help. Do not rerun completed model
experiments or fabricate reviewer labels. See the final release report for checks.

---

# Latest saved-report obligation integration — 24 October 2026

The opt-in scripts/attach_obligations.py now creates a separately versioned saved
report from a completed investigation and source-verified development registry.
Parent report/model/graph records remain unchanged. New reports retain all obligation
assessments, scoped citations, counterevidence, fingerprints and inherited metrics.
Existing report API, exports and chat read the derived ID. No global graph/finding
insertion, upload UI, model inference or independent labels. No-registry abstention
is unchanged. 163 tests pass, one dependency warning; five new integration checks.

Read docs/VERIFICATION_OBLIGATIONS.md and
reports/obligation-integration-20261024/VERIFICATION.md. Independent 91% remains
NOT_EVALUATED. Next local engineering task: machine-checkable reviewed search
inventories/exclusions against pinned Git, keeping unknown regions explicit and
avoiding negative labels inferred from absent links. Real reviewed registries,
semantic review and frozen disjoint final cases remain external requirements.
No historical model runs or Java absence diagnoses were repeated. Full archive
v28 and overlay v8 were restored/checked and match the prior local checkpoint.

---

# Latest bounded obligation increment — 24 October 2026

Added an offline source-backed verification-obligation registry with append-history
fingerprints, lifecycle, explicit reviewed search boundary, counterevidence and
source-backed root-cause grouping. 158 tests pass (13 registry checks), one existing
dependency warning. Saved metric audit passes 31 rows / 1,986 query rows. No LLM
calls, independent labels, final-test exposure, historical changes or Windows run.
The 91% gate stays NOT_EVALUATED. Existing no-obligation/no-MISSING_TEST guard is
unchanged. Source verification is not semantic verification or reviewer authentication.

Read docs/VERIFICATION_OBLIGATIONS.md and reports/obligations-20261024/VERIFICATION.md.
This is offline intake only, not yet wired into application/graph/report workflows.
Next local step: connect reviewed development registries to a separately versioned
investigation/report path, retaining absent-registry abstention, scoped search,
counterevidence and all per-obligation records. Real independent review is still
required; do not use authored registry fixtures as research gold. Use canonical
parser IDs from separate imports; never rewrite frozen artifacts. Full v27 was
newer than overlay v7, so no older overlay was applied. No old runs were repeated.

---

# Latest completion pass — 24 October 2026

Implemented bounded C/C++ Clang references, Swift extraction with actual Swift
frontend syntax validation, explicit pinned comparison chat, source-linked test
review questions, independent review intake and a shared SQLite connection fix.
145 tests pass (one existing dependency deprecation); production build and all
13 Linux browser pages pass, including chat comparison and saved follow-up.
No new LLM inference or real independent labels. All 550 historical files match;
31 method rows / 1,986 query rows and 251 saved observations audit successfully.

All 22 Java references previously requiring diagnosis are absent at their exact
pinned base paths. Across all 51 outside references, 43 paths are absent and 8
non-Java paths are present/excluded. No new-file/rename inference or score change.

Latest technical drafts: submission/research-20261024/ (six-page paper PDF and
editable Word, 29-page thesis PDF). All pages rendered and reviewed. Older dated
manuscripts and model studies remain intact. Review handoff:
reports/completion-20261024/review-handoff-final. Reviewer forms remain blank;
canonical imported repository/artifact IDs are required before adjudication.

Independent 91% remains NOT_EVALUATED. All tasks are not complete: independent
labels/semantic review/final freeze, broader semantic/obligation/security
acceptance, full LLM-weight RL, live eligible OmniRoute, native Windows acceptance
of current changes, and institutional/publication requirements remain unresolved.
Read docs/COMPLETION_STATUS_20261024.md for exact boundaries and next local work.
Do not restart, reparse frozen artifacts in place, or replay old model calls.
Hourly continuation resumes after this checkpoint is saved; no calendar waiting.

---

# Latest bounded increment — 24 October 2026

Offline miss decomposition over all 314 exposed development cases is complete.
See reports/realworld-20261024/MISS-DECOMPOSITION.md. Outside-inventory loss is
5.23 percentage points; ranking loss is 9.66. The 51 excluded references include
29 non-Java files and 22 Java absences requiring pinned base-tree review.
The descriptive 94.77% oracle ceiling is NOT an achieved score. No new labels,
inference, tuning, or final-test inspection. Focused stdlib test passes; full
suite not rerun (pytest absent). Saved arithmetic/policy audit passes.
Next: inspect unresolved Java absences at pinned base trees; collect independent
review/adjudication and freeze disjoint evaluation. 91% remains NOT_EVALUATED.

---

# Latest real-project checkpoint — 24 October 2026

Completed all 314 pinned TEBench development retrieval cases and the separate
109-case fetch recovery; 205 successful rankings were reused. Full-set best
Recall@10 is 85.11% (rank fusion). Training-only LinUCB (531 events) gives 84.27%
on 137 held-development cases versus fixed fusion 85.64%; negative result retained.
These are developer test-file retrieval results, not independent consistency or
traceability correctness. The 91% gate remains NOT_EVALUATED. Zero LLM calls.

137 tests, frontend build and 13-page Linux browser acceptance pass. Historical
550 files and saved metric arithmetic (31 rows / 1,986 queries) verify. Snapshot
project overview and Dashboard loading-state race fix are included. Independent
review and native Windows acceptance for these changes remain open.

Read reports/realworld-20261024/VERIFICATION.md and docs/IMMEDIATE_EXECUTION.md.
Completed runs must not rerun on resume. Use the source fingerprints and per-case
records, preserve original failures, and use a separate recovery output/cache.
Roadmap dates are not waiting periods. Hourly bounded continuation is enabled.

---

# Real-world continuation — 24 October 2026

Resume immediately; roadmap dates are not waiting periods. The saved baseline
was recovered after workspace maintenance removed unsaved benchmark output.
The new scripts/test_evolution.py prepares the official checksum-pinned TEBench
inputs/gold, executes base-test retrieval with bounded project concurrency, and
compares a training-only LinUCB policy. Full results remain pending until logged.
Use scripts/test_evolution.py run --output experiments/test-evolution/full-20261024
and add --resume only to reuse matching case fingerprints. Preserve failed cases.
Do not use full V0 answer tests as retrieval input or claim independent 91%.
Optional preparation dependency: pyarrow==23.0.1. No new model calls are authorized
beyond existing local-only limits; this stage requires none.

---

# Contextual-bandit retrieval increment — 23 October 2026

A bounded LinUCB selector now chooses among the frozen TF-IDF, BM25, embedding
and hybrid rankings using only SMOS training rewards. It made zero LLM calls and
did not update model weights. The full suite passes 133 tests (one existing
deprecation warning); all 550 protected historical files match, and 31 saved
method rows/1,986 query rows pass arithmetic checks. The policy improved training
MAP by 0.0313, but trailed the strongest fixed
baseline by 0.0169 MAP on iTrust validation and 0.1410 on the previously exposed
eTour development test. The negative result is retained at
`experiments/contextual-bandit/20261023T162437-621839da/results.json`.

The official LiSSA repository, exact pinned commit, MIT outer-package licence,
paper/replication DOIs, exposure ledger and task boundaries are recorded in
`docs/REAL_WORLD_RESEARCH_PLAN.md`. Unlinked queries remain unknown, not negative.
This run did not create fault-localization gold, complete impact sets, independent
consistency labels or semantic citation review. Full LLM-weight RL is NOT_RUN.
The 91% gate remains NOT_EVALUATED. Next: independently annotate and adjudicate
repository/change-family-disjoint real changes, then freeze validation/final-test
groups without tuning on eTour labels. See
`reports/contextual-bandit-20261023/VERIFICATION.md`.

---

# Detailed audit v2 follow-up — 23 October 2026

The confirmed extraction, graph-path, coverage, report-chat and scoring defects
from this engineering pass are fixed. **131 tests passed**, production build
passed and fresh Linux Chromium acceptance passed all **13 pages**, including
coverage, exact source navigation, exports, graph/evidence, deterministic
investigation and mobile layout. One Python dependency deprecation warning remains.
Vite is pinned to 6.4.5; npm audit reports zero vulnerabilities. This does not
certify Python dependencies, application security, licences or native Windows.

The **91% quality gate remains NOT_EVALUATED**. Independent labels, semantic
review and held-out predictions are missing. There were zero new model calls.
32 real-change pilot packets and strict reviewed-case/verification-obligation
schemas are prepared; their labels remain null. No gold labels were invented.
The original 12 authored diagnostics remain development-only. All **550** canonical
historical files are unchanged; metric and saved RAG provenance audits pass.

New investigations traverse base/head graphs separately and save edge-by-edge
path provenance. Full Git inventory/language coverage is recorded and visible.
Report chat has typed intents, scoped follow-up context and per-claim support.
Missing graph/contract/test proof returns NOT_ESTABLISHED. The scorer rejects
malformed flags and keeps missing/invalid predictions in the denominator.

Read docs/AUDIT_V2_RESOLUTION.md and reports/audit-v2-20261023/RELEASE.json.
Next: two independent reviews of the pilot, separate adjudication records,
reviewed evidence experiments and a repository/change-family-separated test.
Keep evaluation/quality-target.json in DRAFT_NOT_FROZEN until the actual freeze.
Do not rerun historical generations merely to resume. No Git commit/push occurred.

Old snapshot artifacts retain their parser policy. Use the separate identity
created by scripts/reindex_repository.py for syntax-scope-fetch-v3; never rewrite
frozen artifacts. Extract the ZIP separately and preserve your Windows live DB.
Runtime binaries and weights are excluded. Fresh native Windows validation remains
NOT RUN. Archive verification is in the sibling project-checksum JSON.

---

# Correctness and input-audit follow-up — 23 October 2026

The requested Phase 0 baseline and bounded correctness/input-audit pass are complete.
Independent annotation and semantic review remain REQUIRED; Phase 1 as a scientific
review phase is not complete. The 91% target remains **NOT_EVALUATED**.

- Fixed configured Git diff/textconv helper execution during reads, final-budget
  pair splitting/stale counters, duplicate request construction for audit, and
  model calls with no retained source evidence. No database migration.
- **121 tests passed** (baseline 115); production frontend build passed. One
  dependency deprecation warning remains. No fresh Windows or full browser
  acceptance was performed for this follow-up.
- Audited **96 saved observations / 12 authored cases**, with zero fingerprint,
  evidence mapping, snapshot quote, foreign revision or count errors. This is
  provenance validation, not independent semantic correctness.
- Offline 12-case final-budget comparison: split pairs **5→0**, stale counts
  **12→0**. Four corrected packets cannot fit complete evidence pairs and must
  abstain without inference. No new model calls or historical label changes.
- All **550** files in the new preservation manifest match. Three canonical
  frozen databases pass integrity. Saved metric audit covers 31 method rows and
  1,986 query rows; saved RAG provenance audit covers 251 observations.

Read docs/IMPROVEMENT_AUDIT.md, ARCHITECTURE_CURRENT.md, IMPROVEMENT_ROADMAP.md,
EVALUATION_PROTOCOL.md and DEPENDENCY_COMPATIBILITY.md. Machine-readable results
are in reports/improvement-20261023/RELEASE.json. Review packet instructions are
in reports/improvement-20261023/input-audit/review/README.md. Two reviewer forms
and an adjudicator form are blank; do not treat them as completed annotation.

Next: independent development packet review, separate adjudication records,
controlled evidence improvements and a disjoint real-change benchmark. The 79
real-change candidates remain unlabelled; historical diagnostics stay development-only.
Do not rerun saved generations just to resume. No commit or push was made.

Extract the updated ZIP into a separate empty folder. Keep the existing Windows
installation and live database intact. Runtime binaries/weights are excluded.
See the sibling VIGILANT-project-checksum.json for final archive verification.

---

# Latest release — 23 October 2026

The evidence-first code and bug-audit fixes are complete for the documented scope.
GitHub main at `7eba731b99dc63c66e2872da1fcc8b723ce30945` was reviewed and merged
into this package; changes have not been pushed to GitHub.

**115 tests passed**, production build passed, and Linux Chromium acceptance
passed all 13 pages, saved-report chat, exact-source navigation, exports, isolated
deterministic investigation and 390px mobile layout. One dependency deprecation
warning remains. This is not a new native Windows acceptance run.

New investigations establish Git/static facts before retrieval and bounded
advisory interpretation. Graph provenance and dependency direction are explicit;
heuristic links are candidates. Chat explains saved runs without new inference.
The supplied P0/B1–B11 audit fixes and limitations are recorded in
`reports/evidence-first-20261022/BUG-AUDIT.md` and `docs/EVIDENCE_FIRST.md`.

**91% correctness is NOT_EVALUATED, not achieved.** Trace precision/recall/F1 and
consistency accuracy/macro-F1 have separate gates. The draft protocol is not
frozen. Independent annotations, semantic review and a disjoint held-out test
remain necessary; see `docs/QUALITY_TARGET.md`. The 79-candidate review queue is
unlabelled and short of 200; it cannot be counted as evaluation evidence.

All 514 files in the recovery manifest and all 549 files in the merged-history
manifest match their hashes. Four SQLite databases pass integrity checks.
Arithmetic audits cover 31 method rows and 1,986 query rows; provenance audits
cover 251 RAG observations. The original and citation-repair diagnostic runs
(72 observations) replay using their archived sources; two upstream 12-case runs
pass score/fingerprint audits. No new model inference or cloud fallback was used.
The eight-row lexical run was already complete and was not rerun for packaging.

Keep your existing Windows directory and live database intact. Extract this ZIP
into a separate empty folder first. In a fresh extraction use Setup-Windows.ps1,
then Start-VIGILANT.ps1 for evidence-only operation. Runtime binaries and model
weights remain separate reproducible dependencies. The package contains frozen
historical snapshots; it does not claim to contain a newer live Windows database.
To apply parser improvements to previously imported revisions, use the separate
project identity created by scripts/reindex_repository.py; never rewrite old
artifact versions. Full instructions: docs/EVIDENCE_FIRST.md.

Next scientific task: obtain independent reviewed labels and semantic citation
review, record all tuning repositories/change families, freeze selection, then
perform one held-out evaluation. Do not tune against the final test or rerun
historical generations merely to resume. Full release record:
reports/evidence-first-20261022/RELEASE.json.

---

# Latest checkpoint - native Windows, 22 October 2026

The 2026-10-22 reliability audit is in `reports/windows-20261022/AUDIT.md`.
Dataset endpoint/duplicate/hash checks passed for the four prepared retrieval sets
(278 sources, 449 targets, 1,660 links, 705 raw-file hashes). Saved metric and RAG
audits also pass (23 method rows, 1,484 query rows, 251 RAG generations).

One rule-engine fix prevents inferred graph-edge loss from being labeled a confirmed
`BROKEN_TRACE`; only explicitly declared edges receive that status. The declared
marker is transient to preserve immutable graph payloads. Regressions cover both
cases. A read-only repository/snapshot chat panel and `/api/chat` endpoint now
retrieve verified excerpts, optionally call a configured provider, and disclose
that semantic support is not verified. Browser acceptance passed at desktop and
390px mobile widths in evidence-only mode (`reports/frontend/2026-10-22T06-50-58-933Z/validation.json`). Final Windows run: 88 tests passed,
frontend build passed, touched-file diagnostics clean. Use `.venv/Scripts/python.exe -X utf8`.

Do not rerun or alter the 36 saved model generations. The best remains Qwen2.5 Coder
14B originally scored 1/12 on authored, correlated diagnostics. Follow-up scores
are 2/12 with evidence-v2 and 4/12 with Git-derived change facts; neither beats the
50% majority baseline. Rules-only development agreement is 11/12 exact status sets
on these same cases, not independent accuracy. The requested independent test set
is 200+ cases; at exactly 200, 182 exact matches gives 91% observed. It is NOT RUN
or established.
See `reports/windows-20261022/accuracy-debug.json`. Chat history is client-only;
semantic citation support remains unverified. Independent labels and semantic
review remain unfinished. The blind review queue has 79 unlabelled source-change
candidates, short by 121: `reports/independent-review-20261022/`.

Only pytest caches were removed. Preserve `.venv`, `.runtime`, datasets, databases,
historical experiments, reports, and submission drafts. The refreshed portable
package must keep the existing SQLite snapshots (`scripts/checkpoint.py
--preserve-snapshots`).

---

# Prior checkpoint - native Windows, 21 October 2026

Setup and requested local evaluation are complete in this extracted project. The app is running at http://127.0.0.1:8000. After a reboot use Start-Ollama-Local.ps1, then Start-VIGILANT-Local.ps1 in another terminal.

75 tests, production build and Windows browser acceptance pass. All three local Ollama models completed 12 authored diagnostic cases each: Qwen3 8B 0/12, Qwen2.5 Coder 14B 1/12, Qwen3 14B 0/12. Citation validation failures count as errors. No independent accuracy or >75% claim is supported.

All 423 historical experiment/snapshot files are unchanged. New outputs: experiments/local-model-comparison/windows-20261021. Run-Local-Models.ps1 reuses this exact directory; the verified resume made zero new calls. Do not rerun completed generations. Detailed evidence: reports/windows-20261021/VERIFICATION.md. Runtime/weights under .runtime are excluded from portable archives. Independent annotation and review remain external requirements.

---

## Latest extension — 2026-10-13

OmniRoute support is implemented and tested (53 tests; frontend build). No local gateway or provider account is connected here. Live inference, free eligibility and revised accuracy are NOT RUN. Follow docs/OMNIROUTE_FREE.md; default five-call legacy-prompt evaluator preserves original results and excludes provider failures. Free-only operation requires a free-eligible provider account and no paid gateway fallback. Do not resume old Qwen runs. Prior 2026-10-12 browser evidence predates the new provider selector.

# VIGILANT recovery and continuation

Checkpoint: 2026-10-12 UTC. Continue this project without rebuilding it. Read AGENTS.md, PROJECT_STATE.json, docs/FINAL_STATUS.md and actual experiment records. Honor the active lease and check processes before starting jobs.

## Completed evaluation

All 251 linked-query RAG generations are complete: SMOS 67, iTrust 105, eTour English 57 and RTMX module-valid 22. Independent observation audits passed for all 251. Independent arithmetic recomputation passed for 23 method rows and 1484 query rows. A zero-new-call continuation skipped all four completed datasets. Do not rerun these model calls.

| Dataset | Hybrid MAP | Hybrid + RAG MAP | Immutable result |
| --- | ---: | ---: | --- |
| SMOS | 0.3025565167 | 0.3060623896 | experiments/retrieval/20261007T104905-4064b602/results.json |
| iTrust | 0.3068281472 | 0.3043088728 | experiments/retrieval/20261007T163255-0dfbb833/results.json |
| eTour_en | 0.4405532200 | 0.4426837779 | experiments/retrieval/20261007T171402-64fa98d8/results.json |
| RTMX-module-valid | 0.7515151515 | 0.6984848485 | experiments/retrieval/20261007T210208-3f0803cc/results.json |

Results are mixed, with no general superiority or significance claim. The model reviews only five candidates; Recall@5/@10 cannot change. RTMX has seven candidate modules, so Recall@10 necessarily equals one. Full schema validity is 1.0; independent semantic grounding and hallucination rate remain unmeasured.

Final measured tables and inspected scientific plots are in reports/results/. Paired query deltas and dataset reports are in reports/rag/. Derived reports can be regenerated without inference:

```
python scripts/audit_rag_observations.py
python scripts/audit_results.py
python scripts/summarize_rag.py
python scripts/evaluate.py
```

## Other completed work

- Canonical/versioned artifacts, Git extraction, Python/Java/JS/TS parsers, bounded trace candidates, structural knowledge graph, provider abstraction, evidence verification, conservative rules and bounded tool investigation.
- Pinned datasets; actual TF-IDF, BM25, MiniLM, hybrid and graph comparisons. The learned ranker was rejected by its validation rule.
- Twelve controlled Git scenarios with exact saved commits and restored worktrees. Labels are authored and affected sets incomplete. Outside-oracle predictions are unjudged, not verified false positives.
- SAFA artifact-tree evolution, not independently labelled code consistency.
- Sixty genuine calls: experiments/ablation/20261006T194639-30694b4d/results.json. Every variant is 100% UNCERTAIN and agrees with 25% of authored labels, equal to always-UNCERTAIN. Preserve the negative result, five citation failures, excluded loading-only failures and review packets.
- Full local-model investigation: experiments/pipeline/20261006T195007-e56e6b8d/results.json. Twelve tools, 11 changed records, 33 impact candidates, 24 verified excerpts and model UNCERTAIN. Fifteen rule findings concern a shared route-renaming cause, not 15 independent confirmed defects.
- Thirty-four passed tests, frontend production build, dependency manifests, Windows scripts and immutable experiment records.

Preserve knowledge_graph/graph.py, nodes/edges and commit MODIFIES relationships in snapshots. Similarity candidates must not become proven IMPLEMENTS edges. See docs/PROJECT_MAP.md, docs/INTERFACE_CONTRACTS.md, docs/COMPLETION_CHECKLIST.md and docs/EVALUATION_LIMITATIONS.md.

## Next unfinished work

The implementation, frozen model experiments, result tables, thesis draft, separate paper drafts and demonstration deck are complete for their stated scope. Do not repeat inference or rewrite completed drafts.

1. DONE: Chromium 153 browser checks passed across all 13 pages on 2026-10-12. Record: `reports/frontend/2026-10-12T06-01-24-831Z/validation.json`. Do not repeat browser checks unless implementation changes. Dashboard includes all 14 saved experiment runs.
2. Actual Windows execution needs access to the user computer. This hosted session cannot write to the requested Windows folder.
3. Independent labels/semantic review, institution/author details, full-text survey expansion, external plagiarism/scientific review and venue selection remain unresolved.
4. Refresh the source and complete package after any genuine change. Existing graph, raw outputs, failures and immutable experiment runs must survive.

## Restore only missing files

Prefer VIGILANT-project.zip: libfile_62832ff34ccc8191947359933746ec53. Overlay a newer source checkpoint if one exists, preserving active work. Fallback source: libfile_f68b012833688191a771b623813ccd24. Data: libfile_b8166c70bb908191adf712a38cba56c5. Check manifests and dates. This resume: libfile_9a7493f12bb88191bdbe5d5abade3499. Separate state: libfile_2929bdde983081919b1763d10fd6e043.

Reinstall dependencies only if absent. Repair relocated paths with scripts/restore_checkpoint.py. Use scripts/restore_changebench.py only for missing worktrees, never to overwrite a mismatch. Weights, .venv and node_modules are reproducible dependencies excluded from archives.

A reset may remove .venv/bin/python while installed packages remain; restore its missing link from CODEX_PRIMARY_RUNTIME_PYTHON. Use /tmp/vigilant-runtime for live SQLite and SQLite backup for snapshot recovery; set VIGILANT_DB, VIGILANT_BENCH_DB and VIGILANT_EMBEDDING_CACHE accordingly. Never copy a live main database without its WAL.

If a new protocol explicitly requires inference, restore pinned weights to /tmp/vigilant-models with scripts/download_models.py --staging-only and VIGILANT_MODEL_STAGING. Set VIGILANT_LLM_PATH/VIGILANT_EMBEDDING_PATH, validate safetensors and use only one model process. Do not restore models merely to regenerate completed tables.

scripts/checkpoint.py stages and validates archives. scripts/package_project.py produces one combined project. Save after meaningful progress and before stopping because processes and temporary files may disappear. Release the lease on normal stop.

## Windows and external requirements

Requested destination: C:\Users\Ankith\Downloads\Code- Vigilant. This session cannot write there. VIGILANT-project.zip and Install-VIGILANT.ps1 (libfile_977a69c7876881918a0239f3195175a1) target that folder without overwriting existing content. Windows execution is unverified.

Independent labels/semantic review, author/institution/supervisor details, institutional formatting, external plagiarism review, venue selection and indexing verification remain unresolved. No spending, external messages, publication or submission. Keep the existing continuation task; do not create duplicates or promise exact quota-reset restarts. Historical user-reported scores use different populations and must not be pooled with reproduced results.

## Completed submission drafts

- `submission/output/Thesis-Draft.pdf`: 27 A4 pages covering the requested topics, with actual tables, figures, references and reproduction appendix.
- `submission/output/Research-Paper-Draft.pdf`: four IEEE-format pages, mixed/negative results and evidence limitations.
- `submission/output/Survey-Paper-Draft.pdf`: four IEEE-format pages, targeted literature matrix and taxonomy. Full-text/systematic-review coverage is not claimed.
- `submission/output/VIGILANT-Demonstration.pptx`: 14 editable slides with measured charts/tables, recorded graph relationships and API-change evidence. All slides rendered and visually reviewed. Native PowerPoint and live browser execution remain unverified.

Editable templates/builders and source provenance are under `submission/`, `scripts/build_thesis.py`, `scripts/build_papers.py`, `scripts/build_demo_deck.mjs` and `reports/submission/`. The deck builder needs the bundled artifact-tool runtime and RUNTIME_NODE/RUNTIME_NODE_MODULES/RUNTIME_BIN_DIR/RUNTIME_PYTHON variables; the PPTX can be edited directly. Do not rebuild from a scaffold.

Latest browser validation: `reports/frontend/2026-10-12T06-01-24-831Z/validation.json` — PASSED. Graph, evidence export, isolated deterministic investigation and mobile layout checked. Old browser-blocker notes in dated manuscripts/deck are superseded by this release record. Native PowerPoint and Windows execution remain unverified.

## Research paper update — 2026-10-14

The requested exact-title research paper by Ankith Singh is complete for technical review: `submission/research-20261014/VIGILANT-Research-Paper.pdf`, five US Letter pages using official IEEEtran and embedded Times New Roman. Editable LaTeX, two vector figures, two tables, frozen data, 14 references and verification report accompany it. Prior four-page drafts are preserved. No inference was rerun. Affiliation/email, independent review, similarity checks and PDF eXpress remain pending. OmniRoute live evaluation remains NOT RUN. See the new paper directory's README and VERIFICATION.md.

## Review revision and Word deliverable — 2026-10-16

Latest paper: `submission/research-20261016/`, with five-page `VIGILANT-Research-Paper.pdf` and editable `VIGILANT-Research-Paper.docx`. Both were rendered and all pages inspected. Review response, supplementary bootstrap/class metrics, self-contained reanalysis inputs, hashes, blank annotation worksheet and controlled evaluation protocol are included. No new inference was run; 418 historical experiment files match the preceding saved release. Original October 14 paper is preserved.

Consistency detection remains unresolved: all 60 raw outputs are uncertain with confidence zero; macro-F1 is 0.10 and non-uncertain coverage 0%. Additional analysis does not establish a superior model. Independent labels/no-link negatives, controlled component comparison, longitudinal validation, live OmniRoute evaluation, similarity checks and PDF eXpress remain pending. The supplied follow-up protocol is NOT EXECUTED. Do not repeat completed deterministic inference or invent annotations.

## Updated codebase — 2026-10-16

The latest local application release passes 62 tests, the production frontend build
and all 13 browser pages, including JSON/CSV/HTML report exports, graph/evidence,
free OmniRoute selector, settings, a new isolated deterministic investigation and
mobile layout. Queue recovery, reference pinning, immutable snapshot restore,
free-only provider selection and watcher state are covered by regression checks.

Start with `docs/RUN_AND_CODE_GUIDE.md`. Architecture mapping and missing production
services: `docs/ARCHITECTURE_COVERAGE.md`. Exact release verification:
`reports/codebase-20261016/VERIFICATION.md`. All 418 original experiment files are
unchanged; 23 method rows/1,484 query rows and 251 RAG observations passed audits
without new inference. Historical RAG audit requires the archived provider source
argument documented in the guide.

Native Windows, Docker/remote CI and live OmniRoute remain NOT VERIFIED/NOT RUN.
Distributed jobs, webhooks, RBAC and the external observability stack are absent.
The supplied full package is complete for the documented local scope. It is not a
claim of full production architecture or high model accuracy; the saved local
consistency model remains all-UNCERTAIN. Latest paper Word/PDF remains preserved.

## Local models and evidence update — 2026-10-17

Added Qwen3 8B, Qwen2.5 Coder 14B and Qwen3 14B local Ollama selection for a 32 GB PC, neutral schema prompts, paired changed-hunk excerpts, and a finite resumable comparison. See `docs/LOCAL_MODELS_32GB.md`. Run `.\Run-Local-Models.ps1 -DownloadModels` after setup and starting Ollama. This hosted environment has no Ollama runtime: new inference and >75% accuracy are NOT ESTABLISHED. Existing 25% authored-label agreement is unchanged. Independent held-out labels remain required.

74 tests and the production build pass. Chromium acceptance passes all 13 pages including model selection and deterministic end-to-end investigation. All 418 historical experiment files and three snapshot databases are unchanged; historical metric/RAG audits pass. Details: `reports/accuracy-20261017/VERIFICATION.md`. Windows and actual 32 GB hardware execution are unverified.

Graphify was unavailable. `handoff/graphify/` contains the project brief, real snapshot JSON/CSV/GraphML (2,134 nodes, 3,993 edges) and reproduction details. Native Graphify import is unverified.

Existing hourly continuation was enabled with bounded calls, exact resume, lease protection and a pause when only external blockers remain. It cannot run the user's Windows PC. Do not rerun completed historical experiments. Next scientific step: run the supplied local comparison, inspect errors, collect independent labels, select on validation, and evaluate one frozen model/prompt on held-out data.

## Runtime installation attempt — 2026-10-17

Ollama 0.40.5 was installed temporarily and its loopback version endpoint responded. Cloud inference was disabled and only one server was used. Qwen3 8B download failed with `redirect target not allowed` because the Cloudflare R2 storage hostname could not be resolved/reached through the available network. No new model inference ran; scores remain unmeasured. The host has an 8 GiB memory limit and no GPU; 14B downloads were not attempted. The temporary server was stopped. Weights/runtime binaries are reproducible dependencies and are not bundled.

Continuation is PAUSED until a usable model/weights connection or independently annotated data is supplied. No completed tests or historical inference were repeated. See `reports/runtime-20261017/VERIFICATION.md` and `session.json`.

Next bounded Windows commands, after existing setup and starting Ollama, from the VIGILANT folder:

```powershell
ollama pull qwen3:8b
.\.venv\Scripts\python.exe scripts/evaluate_local_models.py --models qwen3:8b --max-calls 6
```

Repeat the same bounded command to resume matching fingerprints. Once the runtime is available, compare candidates on validation, freeze one model and prompt, and test using independently reviewed held-out labels. Authored diagnostic scores cannot verify >75% independent accuracy. Native Windows access and independent annotations remain external requirements.

## Native Windows continuation - 2026-10-21

Working in the extracted project on the user PC. Dependencies and frontend installed. 74 tests and browser acceptance pass. Windows restore fixes applied. Ollama 0.40.7 running with cloud disabled; local model downloads/evaluation in progress. See reports/windows-20261021. Historical files have a pre-work SHA-256 manifest.

Qwen3 8B completed 12/12 native Windows diagnostic generations. All failed output/citation validation and count as errors (0% diagnostic accuracy). Qwen2.5 Coder 14B evaluation is running next. No original inference was repeated.

Qwen2.5 Coder 14B also completed 12/12 calls. Qwen3 14B is the final candidate running; the combined evaluator reuses completed models by exact fingerprint.


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

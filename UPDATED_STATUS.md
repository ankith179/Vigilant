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

Partial-report API increment: 322 tests and all 32 report revalidations pass. UI/chat delivery and independent evaluation remain open. See docs/PARTIAL_REPORT_API.md.

# Updated project status — 25 October 2026

Completed in this pass: separate partial-source graph projection and report composition;
53 graph scopes, 32 reports, 313 tests. Frozen sources and historical measurements preserved.
Read docs/STAGED_GRAPH.md, docs/STAGED_REPORT.md and their reports for receipts.

The entire project is not finished. Open work includes application delivery of these
reports; reviewed obligation intake; independent traceability/impact/consistency and
semantic judgments; frozen unseen final evaluation; broader compiler/build/runtime
semantics; full platform parity and security/deployment acceptance; current Windows
verification; full model-weight RL; and final academic requirements. These are not
satisfied by engineering test passes or source matching. See docs/COMPLETION_STATUS_20261024.md.

91% and 95% assurance gates: NOT_EVALUATED. No independent labels were fabricated.
Saved test-file retrieval Recall@10 remains 85.11%; no new ranking experiment ran.

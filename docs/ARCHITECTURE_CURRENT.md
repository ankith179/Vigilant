# Current architecture and feature coverage

Latest bounded presentation: PARTIAL_REPORT_PRESENTATION.md and reports/partial-report-delivery-20261025/ document six guided field explanations and freshly validated JSON/printable HTML exports. Existing canonical chat and exports retain their separate contracts.

Current continuation: JOB_CONTROLS.md and reports/job-controls-20261026/ record file-backed SQLite worker isolation, Windows child-process termination, single-server database locking, and crash/restart recovery without replay. The 25 October cooperative acceptance remains preserved under reports/job-controls-20261025/.

Remote repository intake is restricted to public HTTPS GitHub/GitLab URLs and uses redirect-disabled, sanitized, no-checkout Git clones; see `docs/SECURITY_MODEL.md` and `reports/import-security-20261026/`. Network egress and DNS are not pinned or certified.

Current continuation index (26 October 2026): PROJECT_BASELINE.md,
VIGILANT_MASTER_TASK_REGISTER.md, VIGILANT_INTEGRATION_GAP_MATRIX.md and
COORDINATION_LOG.md bind the latest source/evidence and open work.

The separately versioned partial source lane flows from checksum-pinned
StagedSourceReader and OfflineReviewSourcePolicy through comparison, graph and
inspection receipts into immutable development report JSON. PartialReportAccess
serves it only when the report registry hash is explicitly configured. Every read
recomposes the original bounded report before delivery. The production Partial
Reports page presents pinned base/head scope, candidates, unknowns and JSON export;
its source route permits only report-selected artifacts/graph endpoints and calls
the same verified staged inspection service. It never sends partial identities to
the canonical importer or silently inserts staged reports into analysis_runs.

The source lane, canonical full investigation worker and independent review/evaluation
remain distinct application boundaries. Source receipts do not establish semantic
support or reviewer authority. Shared workspace token protection applies; there is
no tenant/role authorization claim. Partial-report chat, multi-server job
coordination, path-independent lineage and broader language semantics remain open.
File-backed SQLite API jobs have bounded worker termination and Windows Job Object
descendant cleanup; POSIX process-group cleanup is implemented but not verified in
this Windows run. A sidecar lock rejects a second server owner. In-memory and
non-SQLite jobs remain cooperative.

This describes the inspected 24 October 2026 implementation, including the follow-up correctness and native-adapter fixes. It distinguishes a verified source observation from a predicted impact or a fluent explanation.

| Stage | Implementation | Established behavior | Boundary |
| --- | --- | --- | --- |
| Intake / storage | `backend/app.py`, `ingestion/service.py`, `database/store.py` | Local/allowed remote Git ingestion; versioned artifacts and persisted runs | A release ZIP is a distribution format, not evidence of a hostile-ZIP ingestion service. Local repository content is untrusted. |
| Revision identity | `ingestion/git.py`, `change_analysis/diff.py` | Resolve immutable commits; read Git blobs; detect file/artifact changes and hunks | External diff/textconv disabled; Git changes do not establish defects. |
| Extraction | `ingestion/parsers.py` | Python and Java/JS/TS/Swift syntax plus bounded C/C++ compiler references, symbols, routes and parse metadata | Native fixtures and Swift syntax parsing pass; project build context and whole-program semantics remain unverified. |
| Static investigation | `agents/workflow.py`, `agents/evidence_first.py`, `consistency/rules.py` | Source change facts and deterministic findings precede model interpretation | Rule assumptions and extraction gaps remain explicit; no blanket behavioral proof. |
| Graph | `knowledge_graph/graph.py` | Versioned edges, provenance, direction-aware traversal and candidate paths | Similarity/name links are candidates. Path existence is not causal impact. |
| Retrieval | `retrieval/index.py`, `rag/evidence.py`, experiment scripts | Lexical/hybrid/embedding experiments; changed windows, base/head pairs and graph/context candidates | No universally superior method; role balance and token coverage unproven. |
| Evidence validation | `rag/evidence.py` | Exact stored excerpt checks; new investigation Git-blob checks | Quote fidelity and source identity are not semantic entailment. |
| Advisory model | `llm/*`, `InterpretationProvider` | Selected E/A aliases, revision-labelled evidence, bounded static facts, strict response validation | Model interprets supplied ambiguity. Empty evidence skips inference. Provider token accounting is not an independent tokenizer audit. |
| Report chat | `backend/report_chat.py`, `frontend/src/Chat.jsx` | Explains selected saved changes/findings/evidence; no new inference | Keyword intents and hop-count summaries, not autonomous investigation or complete dependency explanations. |
| Snapshot chat | `/api/chat`, `frontend/src/Chat.jsx` | Retrieval from selected snapshot, optional provider reasoning, citations | Explicit revision comparisons queue the existing pinned worker. General semantic scope resolution remains incomplete. |
| Evaluation | `evaluation/*`, `scripts/audit_*` | Reproducible saved scores, provenance checks, draft acceptance gate | Ground-truth completeness, independent annotations and held-out validity are external prerequisites. |

## Authority and state

Git and extraction establish recorded source facts. Deterministic findings retain their rule/policy identity. Retrieved evidence and graph edges supply candidates. Model decisions remain advisory; they cannot overwrite deterministic findings. The chatbot exposes report/snapshot scope and source citations. Evidence validation rejects unknown aliases or mismatched source versions. Invalid output remains an error, not a correct abstention.

SQLite stores immutable artifact versions and saved analyses. Ingestion reuses an already imported revision; parser upgrades require a separate reindex project identity rather than rewriting history. Old partially imported revisions need explicit audit because any pre-existing artifacts can cause reuse. This phase does not migrate or reparse historical snapshots.

## Capability assessment

| Capability | Current status |
| --- | --- |
| Explain saved findings and navigate exact excerpts | Implemented, bounded |
| Repository evidence retrieval / optional model interpretation | Implemented, bounded |
| Static base/head source facts | Implemented |
| Graph candidates with provenance | Implemented; not verified behavioral impact |
| Interactive edge-by-edge graph explanations | Partial; report chat currently gives hop counts |
| Natural-language multi-turn scope resolution | Partial |
| Explicit base/head comparison through chat tools | Implemented through the existing pinned-revision worker |
| Independent semantic support verification | Not implemented; review packets prepared |
| Complete test coverage and grounded test selection | Not established |
| Reviewable proposed code patches | Future capability |
| C/C++ and Swift adapters | C/C++ USRs under snapshot assumptions; Swift syntax validation only |
| 91% real-world correctness across operations | Not evaluated |

See the audit for concrete failure reproductions, and the roadmap for acceptance criteria rather than feature-count promises.

## Detailed audit v2 update

New investigations now include `coverage` from `ingestion/coverage.py`, with all Git files/exclusions and per-language counts. The report drawer exposes it; `/api/reports/{run_id}/coverage` supplies the machine-readable record. Snapshot graphs are traversed separately and paths retain exact edge provenance under `path_details`.

Saved-report chat now has an explicit intent contract and scoped follow-up context. Keyword fallback remains labelled. Every substantive response includes claim support metadata; impact paths are verified against stored endpoint versions. Historical incomplete paths return NOT_ESTABLISHED. The UI displays revision/role/support metadata. Snapshot history is no longer concatenated into retrieval queries. General conversation resolution and semantic verification remain incomplete.

`evaluation/change_cases.py` defines reviewed change cases and source-backed verification obligations for annotation. It does not turn an obligation into an automatically confirmed production finding. Full details: AUDIT_V2_RESOLUTION.md.

## 24 October completion pass

See COMPLETION_STATUS_20261024.md for current evidence and remaining engineering acceptance. C/C++ uses a snapshot-only virtual filesystem with host fallthrough disabled; errors and missing compiler context stay visible. Swift parsing is not SourceKit semantic resolution. Test suggestions are source-linked review questions, never invented behavior or execution. Independent review intake validates attestations and source references; it does not manufacture judgments or freeze final labels.

## Paired lineage UI continuation - 25 October 2026

The UI selects distinct indexed base/head commits and 1-16 paths, calls the opt-in shared tool, shows paired canonical excerpts and supports retained-result revalidation. Results clear when scope changes. Observations remain UNREVIEWED, continuity UNKNOWN, semantic support NOT_ESTABLISHED and relationship transfer disabled. Build/focused checks pass; full browser acceptance remains IN_PROGRESS. See docs/EXECUTION_CHECKPOINT.md.

## Optional paired lineage tool

InvestigationService now exposes default-off inspect_lineage to the existing HTTP,
CLI and MCP adapters. Both indexed source revisions and retained records revalidate;
observer IDs remain separate. No automatic relationship propagation or dedicated UI.
See LINEAGE_INVESTIGATION_TOOL.md and reports/lineage-tools-20261025/.

## V015 bounded worker update — 26 October 2026

File-backed SQLite API investigations use a spawned Python worker supervised with a persisted UTC budget converted to a monotonic deadline. Cancellation allows a short cooperative grace period, then uses terminate/kill escalation. Findings, evidence, graph changes and the completed report publish atomically. Startup recovery reconciles committed reports and never replays a possibly completed call. Focused evidence is in reports/job-controls-20261026/.

This does not establish process-tree containment, strict wall-clock limits, non-SQLite isolation, or multiworker ownership. Keep one application process and retain those acceptance items as open.

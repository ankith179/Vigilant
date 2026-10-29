# Audit v2 resolution and 91 percent assessment

This pass addresses the attached detailed audit dated 23 October 2026 against the latest delivered code, project version 22. That checkpoint already had 121 passing tests and the preceding input-audit fixes; the attached audit describes the earlier 115-test release. The project was continued from the saved archive in a separate copy.

**The 91% acceptance gate remains NOT_EVALUATED.** Independently reviewed frozen test labels and matching predictions have not been supplied or created by this work. No new model generation was run. The target was kept at 0.91 and malformed inputs now fail more strictly. Test passes, source fidelity, retrieval scores and model classification accuracy retain separate meanings.

## Implemented changes

| Issue | Fix and evidence | Boundary |
| --- | --- | --- |
| A dependency chain could splice edges from base and head into a path that existed in neither revision | Traverse each graph separately; persist every hop's typed edge, commit, endpoint spans/hashes, provenance, resolver status and ambiguity. Chat checks these records against scoped stored artifact versions. | Paths are impact candidates. No causal behavioral impact is asserted. Historical reports without complete path provenance return NOT_ESTABLISHED. |
| Calls inside nested Python functions were assigned to their enclosing function | Stop call collection at nested definitions; likewise separate nested Tree-sitter callable scopes. Regression demonstrates the inner call is absent from the outer function. | Dynamic dispatch and compiler-level reference resolution remain incomplete. |
| `fetch('/items', {method:'POST'})` was classified as GET | Use the parsed call/options for fetch and literal axios calls. Dynamic options remain unresolved; comments/string contents are not fetch calls. | Some framework/generated-client extraction remains heuristic. No full TypeScript resolver claim. |
| Coverage only described imported artifacts | Inventory all Git tree entries before suffix/size/directory exclusions. Persist language counts, exclusions, parse failures, symbols, tests, requirement artifacts, candidate call matches and unresolved/unmodelled calls. | Extraction and candidate matches are not complete semantics. C++/Swift files are counted as discovered but remain unsupported. |
| Coverage gaps were hard to inspect | Add the investigation coverage panel and `/api/reports/{run_id}/coverage`. JSON report/export includes the full inventory. Historical records show NOT_RECORDED. | Existing historical reports are not rewritten. |
| Report chat had an untyped keyword interface and hop-count-only paths | Add explicit intents for changes, finding, impact, requirement trace, API contract, test obligations, evidence and limitations; optional keyword fallback remains labelled. Each claim returns its basis, support level, excerpt IDs and report/revision reference. | Requirement/API tools expose recorded excerpts and insufficiency, not automatic contract verification. |
| Follow-up scope could be ambiguous | Carry a typed selected run/repository/base/head/finding/artifact context; validate it against the current report. Reject foreign scope. Ask for a finding selection when a referent is ambiguous. UI clears context when scope/finding changes. | This is bounded referent handling, not general natural-language understanding. |
| Old user turns could dilute snapshot retrieval | Search the current question; prior turns remain clearly marked dialogue context for optional reasoning. | Automatic cross-revision comparisons still use completed investigations. |
| Test suggestions could imply coverage | Return saved test excerpts as unexecuted review candidates. Without an obligation registry/complete search, missing tests remain NOT_ESTABLISHED. | Runtime obligation-backed MISSING_TEST inference is not added in this pass. Existing conservative protections remain. |
| Truthy strings could produce a false quality-gate approval | Require actual booleans, finite targets, integer sample minimums, string arrays and meaningful distinct reviewer identities. Include missing/invalid predictions in the classification denominator and export a confusion matrix. | Supplied attestations cannot authenticate real reviewers. The evaluator no longer asserts population accuracy from the case-level Wilson interval. |
| A real-change annotation contract was missing | Add strict reviewed-change/source-reference/verification-obligation schemas. Prepare 32 real-change pilot packets from the existing 79-candidate queue. Unknown labels stay null. Unmet test obligations require reviewed complete search scope and evidence. | These are annotation schemas, not automatically verified production obligations. Pilot has zero independent annotations and prior repository exposure; it is not held out. |
| Frontend dependency advisories | Update Vite 6.3.5 to 6.4.5, pin it and refresh the lockfile. npm audit before: one affected high-severity dependency; after: zero reported vulnerabilities. Build/browser pass. | This npm result does not certify Python dependencies, licences, application security or future advisories. |

## Actual validation

- Restored baseline code: **121 tests passed**. Six focused regressions fail on the old source. The before-source files and failure log are retained.
- Final full suite: **131 tests passed**, one Starlette/AnyIO deprecation warning. Targeted checks additionally cover path provenance tampering, scope switching, ambiguous follow-ups, unsupported intents, long input, annotation validation and query contamination.
- Production frontend build passed with Vite 6.4.5.
- Linux Chromium acceptance passed all 13 pages, saved-report chat/source navigation, coverage panel/endpoint, exports, graph/evidence, model selection, deterministic investigation and 390px mobile layout.
- The first browser attempt failed because a selector opened the new support panel instead of a citation. The selector was narrowed to source-citation details and the complete acceptance rerun passed. Both attempts remain recorded.
- Canonical preservation manifest: **550 files unchanged**. Frozen databases pass integrity. Temporary SQLite staging copies use the existing packaging exclusion policy.
- Saved metric audit: **31 method rows and 1,986 query rows**. Saved RAG provenance audit: **251 observations**. No inference was replayed to obtain those checks.
- Python `pip check` reports no broken requirements. No new production Python dependency was added.

Machine-readable logs and reports: `reports/audit-v2-20261023/`. Browser record: `reports/frontend/audit-v2-20261023-final/validation.json`. Screenshots are internal QA and excluded from the release package. Archive validation is recorded in the sibling project-checksum file after packaging.

## What 91 percent still requires

The executed `scripts/check_quality_target.py` result is NOT_EVALUATED. The current consistency accuracy, macro-F1 and reviewed trace precision/recall/F1 for an independent test are unknown, not zero and not 91%. The 32 pilot cases have no independent labels. The 12 authored diagnostic cases remain development-only and their historical poor model scores are preserved.

The existing gate requires at least 200 real, independently reviewed, repository/change-family-separated test cases; separate traceability precision/recall/F1 and consistency accuracy/macro-F1 each at least 0.91; independent semantic citation review; and matching operational checks. A nominal 182/200 observed result would not establish 91% population accuracy. Cluster-aware study design and uncertainty analysis remain necessary.

Next, two reviewers must independently annotate the pilot using the schema, validate the rubric and adjudicate disagreements with source evidence. Preserve those submissions and any revised labels as new versions. Record every tuning repository/family, build an unseen test split, freeze pipeline/model/prompt/retrieval policies and run one final evaluation. Model-generated labels or repeated diagnostics cannot replace this work.

## Remaining audit work

| Workstream | Current status |
| --- | --- |
| Independent labels, semantic entailment and held-out 91% result | External review required; not completed |
| Identical-condition six-method retrieval comparison and reranking | Planned; existing saved measurements audited, no new universal-winner claim |
| Compiler-aware Java/TypeScript, C++/Swift adapters | Not completed; coverage disclosure implemented |
| Full contract/obligation ingestion, lifecycle and search-completeness proof | Annotation schema supplied; production integration remains open |
| Root-cause finding deduplication with complete counterevidence | Existing conservative rules retained; broader review remains open |
| General chatbot tool orchestration, automatic base/head analysis, reviewable patches | Bounded saved-report tools improved; broader capabilities remain open |
| Full secret exclusion/redaction, SSRF redirect/IP policy, rate/resource controls and public auth | Not certified; maintain local loopback deployment |
| Python vulnerability and complete licence audits | Not run in this pass |
| Fresh native Windows acceptance and measured target RAM/VRAM | Not run in this Linux session |

## Applying parser changes safely

Already imported revisions retain their frozen parser artifacts. To use parser policy `syntax-scope-fetch-v3`, import into a new parser identity with the existing tool:

```text
python scripts/reindex_repository.py PATH --project vigilant --revisions BASE HEAD
```

This preserves old artifact versions. Do not reindex in place or replace a newer Windows live database with the packaged snapshots. Extract the complete ZIP into a separate folder first. There is no database schema migration. Runtime/model weights remain separate reproducible dependencies.

Vite primary release reference: https://github.com/vitejs/vite/releases/tag/v6.4.5 . Advisory details and affected ranges are retained in the npm audit JSON.

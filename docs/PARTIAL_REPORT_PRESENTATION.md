# Partial-report guided explanations and print exports — 25 October 2026

The existing **Partial Reports** workflow now offers six guided explanation topics:
scope, changes, unknowns, graph, evidence and limitations. Each request freshly
revalidates the selected original report and exact repository/base/head scope.
The answer uses fixed descriptive text and exact report fields. Every displayed
claim carries the original report ID, a stable claim ID, JSON pointer, exact value
and `REPORT_FIELD_MATCH_ONLY` support classification.

This is bounded deterministic guidance. There is no model call, free-form semantic
interpretation or independent entailment review. Unsupported intents or extra
question/instruction fields are rejected with 422. Scope/source failures remain
409, and disabled/unregistered access remains 404. A field match cannot establish
that a requirement is satisfied, a test is complete, a candidate link is correct,
or the independent 91% target is met.

`POST /api/partial-reports/{report_id}/explain` accepts only:

```json
{"repository":"<canonical repository ID>","base_commit":"<pinned SHA>","head_commit":"<pinned SHA>","intent":"unknowns"}
```

The existing pinned registry configuration and workspace token apply. Repository
content remains untrusted data. Responses retain fresh source-validation receipts,
presentation-code fingerprint, semantic/reviewer status NOT_ESTABLISHED and quality
status NOT_EVALUATED. No canonical analysis, graph, finding, label or tool-result
record is inserted by this path.

`GET /api/partial-reports/{report_id}/export` takes the same three scope query
parameters and `format=json` or `format=html`. Both formats freshly revalidate
before returning an attachment. JSON contains the complete original report and
validation receipt plus a presentation-source fingerprint. HTML provides pinned
scope, outcomes and denominators, unknowns, coverage, obligations, graph limits,
versioned evidence, limitations and validation, followed by the **complete** JSON
record including full graphs/provenance. Missing graph selections remain explicit.
No unknown or unreviewed region becomes a negative link or MISSING_TEST finding.

HTML escapes repository text, contains no executable scripts/external resources,
and declares a restrictive content policy. Export responses use `Cache-Control:
no-store`. Open the downloaded HTML locally and use browser Print → Save as PDF
for a printable copy. No external PDF service is used. CSV is not advertised by
this bounded partial-report adapter; canonical report exports retain their prior
JSON/CSV/HTML behavior.

The frontend clears old report/explanation/source views if presentation validation
fails. Reopening a selection performs fresh verification. In-flight explanation
responses are discarded when their selection changes; export filenames bind the
original report ID. Downloaded files are receipts for their pinned source state,
not a promise that a later changed source remains valid.

Evidence: reports/partial-report-delivery-20261025/. Ten new presentation checks,
the 342-test regression, 32-case API presentation audit, production build and Linux
browser checks pass. The API audit rotates six intents across 32 requests; it is
not a claim that all 192 case/intent combinations were called. All six intents are
also exercised on authored fixtures and the first real browser report. All 32
reports have both JSON and HTML API exports checked for lossless round trips.
Controlled browser rejection responses are labelled fixtures; actual source/scope
rejection is separately tested. No independent accuracy, general conversational
planning, model-weight RL, new Windows acceptance or publication readiness follows.

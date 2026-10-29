# Changelog

## 2026-10-23 — correctness and diagnostic-input audit

- Disable external diff/textconv, pager and fsmonitor helpers in shared Git reads; use the same wrapper for independent-review export.
- Preserve complete evidence pairs during the final Ollama byte-budget pass; update counts/maps after omissions. Policy: `evidence-first-v3-paired-budget`.
- Record actual selected/omitted input provenance without constructing a second request. Skip inference when no source excerpts survive.
- Add a read-only audit for 96 saved observations, exact prompt exports, 12 label-blind development packets, blank reviewer/adjudicator worksheets and a 12-case offline budget comparison.
- Add six regression checks. Baseline 115 tests; final 121 tests. Frontend production build passes. No new inference, label changes, database migration, Git commit or push.
- Add current architecture/coverage, prioritized audit, roadmap, evaluation draft and dependency/compatibility documentation.
- Independent semantic review, reviewed real-change benchmarks, native Windows revalidation and the 91% quality target remain outstanding.

Earlier release history remains in RESUME.md, PROJECT_STATE.json and reports; this file does not rewrite their recorded results.

## 2026-10-23 — detailed audit v2 follow-up

- Isolate impact traversal by revision and persist/reverify typed path provenance.
- Correct nested call attribution and fetch request-method extraction; parser policy `syntax-scope-fetch-v3`.
- Add Git inventory/language coverage, report coverage API and UI panel.
- Add typed saved-report chat intents, scoped follow-up context, claim support metadata, graph explanations and conservative test-review responses. Limit snapshot retrieval to the current question.
- Harden 91% scoring against malformed booleans/arrays, nonfinite thresholds and missing predictions; add confusion output and remove unsupported population claims.
- Add change-centric annotation and verification-obligation schemas plus 32 unlabelled pilot packets.
- Upgrade Vite to 6.4.5; npm audit reports zero vulnerabilities after update.
- 131 tests and 13-page Linux browser acceptance pass; native Windows and independent accuracy remain unverified. See docs/AUDIT_V2_RESOLUTION.md.

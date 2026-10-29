# Opt-in partial report API — 25 October 2026

Latest bounded presentation: PARTIAL_REPORT_PRESENTATION.md and reports/partial-report-delivery-20261025/ document six guided field explanations and freshly validated JSON/printable HTML exports. Existing canonical chat and exports retain their separate contracts.

Current application integration: the production **Partial Reports** page lists
cases with pinned scope, opens freshly recomposed reports, exposes separate
base/head graph candidates and unknown/withheld/out-of-page counts, and exports
the exact JSON report plus validation receipt. The ordinary Reports page remains
for canonical investigation records. Partial-report chat is still a separate task.

Catalog items now include digest-checked repository/base/head scope so users need
not supply hidden IDs. `GET /api/partial-reports/{report_id}/source` takes those
three scope fields plus `commit_id`, `artifact_id`, optional `start_line` and
`max_lines` (1–80; default 40). It freshly revalidates the report, admits only its
selected artifacts and saved graph endpoints at the selected role/revision, then
uses StagedInvestigationService for exact source receipts. Foreign, stale or
invalid source returns 409; unavailable report/disabled access returns 404.
The existing workspace token protects this route as well.

Current checks are recorded in reports/partial-report-ui-20261025/. The dated
322-test result below remains the earlier API milestone, not the final current
test count. No source verification receipt establishes semantic correctness or
independent reviewer authority.

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

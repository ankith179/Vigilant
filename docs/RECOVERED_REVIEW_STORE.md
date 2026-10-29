# Recovered-source reviewer Store and packets — 24 October 2026

The new immutable database is data/snapshots/pilot-review-recovered-20261024.db.
Its separate canonical parser identity comes from the verified-cache maps. It
contains four repositories, 53 snapshots and 29,647 artifact versions. Every one
of the 10,970 file-status entries is retained: 7,443 PARSED, 12 PARSED_WITH_ERRORS,
982 MISSING_LOCAL_BLOB, 2,485 UNSUPPORTED_SUFFIX and 48 NON_REGULAR_FILE.
This is partial development coverage; every search disposition remains UNKNOWN.

reports/recovered-review-20261024/STAGING.json binds the database and map-index checksums to all 32 case routes.
reports/recovered-review-20261024/packets/ contains 32 source packets, two blank reviewer forms, 32 blank adjudication
cases and schemas. All 136 available changed-file side references match exact
stored source spans and hashes; four absent pinned-tree paths remain explicit.
Excerpts show only the first 40 lines. Review full pinned sources before judging.
Changed files are candidates, never complete impact sets or negative labels.

Verification reused the existing staging and packet builders. All 29,647 stored
artifact payloads equal their checksummed maps; all 53 commit file inventories
match. 53 API source-navigation checks pass on a disposable writable database copy.
All 37 packet payload checksums verify. The published snapshot remains unchanged.
215 software tests pass with the existing Starlette/AnyIO deprecation warning.
8,564 baseline files outside five declared mutable checkpoint/continuity files
match full v37, including all 550 protected historical files and both earlier map,
Store and packet versions. See AUDIT.json, preservation.json and tests.log.

No source fetches, model inference, labels, commits/pushes or subject script
execution occurred. Existing negative recovery and bandit results are preserved.
Source/license provenance remains pinned in reports/local-source-recovery-20261024/
LICENSE-PROVENANCE.json and SOURCES.md, plus the original search-draft index.
No new blanket license claim is made. The prior browser and draft acceptance is
retained; current native Windows acceptance was not run.

Read the new packets using the new database/routes. Never merge their canonical
IDs into old packets or open either frozen database with a writable Store; browse
a disposable copy under /tmp/vigilant-runtime, from the project root so repository
paths resolve. Regenerate only into NEW database/report/packet paths using
scripts/stage_pilot_review_store.py and scripts/prepare_canonical_review_packets.py.
Run scripts/audit_recovered_review.py --baseline-archive <full-v37-archive> before
packaging metadata changes, using a new report destination/run to avoid overwrite.
The audit deliberately refuses existing output files.

The reviewer intake still requires real independent reviewer attestations and
adjudication; blank forms are not valid reviews. Its default Git checks currently
use pinned repository caches, so recovered references must be checked for intake
readiness before claiming the handoff is ready for scored annotation ingestion.
Next: verify that path without weakening source checks or writing original Git
caches. Real independent labels/semantic review and a repository/change-family-
disjoint final freeze remain required. Both 91% and saved 95% gates remain
NOT_EVALUATED. Complete language semantics/full LLM-weight RL are not claimed.

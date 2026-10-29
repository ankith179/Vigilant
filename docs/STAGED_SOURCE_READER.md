# Validated read-only staged-source access — 25 October 2026

investigation.staged.StagedSourceReader reads frozen source checkpoints without
Store construction, repository import, Git commands, extraction, graph writes or
model calls. It binds the database, source-index and staging SHA-256 values, reads
SQLite with mode=ro/immutable=1 and query_only, and verifies the database hash again
when closing. It refuses unavailable, duplicated or unpinned routes and unsafe,
oversized or checksum-mismatched map files. Snapshot artifact/text budgets match
the existing 20,000-artifact / 20-million-character investigation bounds.

For each snapshot it reuses the existing map validator for canonical IDs, stored
source spans and file/artifact membership, checks content hashes and exact counts,
then compares every stored artifact payload with its checksummed map. Repository,
project, origin, commit, source-map hash and all stored coverage rows must match.
Extra/missing/forged stored artifacts and rewritten coverage fail closed. Returned
file lists and artifact models are independent copies; caller mutation does not
change later reads or original snapshots. The source-import preservation guard
from the preceding increment remains unchanged.

The reader returns every file status and UNKNOWN search disposition, artifact
versions and data-provenance fingerprints. It explicitly reports partial/unreviewed
scope, no whole-repository/test completeness and no established semantic support.
It verifies checksum-pinned map/Store correspondence only. Raw Git source validation
is NOT_PERFORMED_BY_READER; use the separate scoped source-policy checks before
accepting later evidence. Existing source/license provenance remains unchanged.
An absent row/artifact in a partial map is not a verified deletion or negative link;
full Git-tree/search-boundary and coverage proof remain separate requirements.

Audit: all 53 snapshots / 32 development cases and 29,647 artifact versions pass.
All 10,970 UNKNOWN entries remain: file statuses 7,443 PARSED, 12 PARSED_WITH_ERRORS,
982 MISSING_LOCAL_BLOB, 2,485 UNSUPPORTED_SUFFIX and 48 NON_REGULAR_FILE. A write
attempt was rejected. Subprocess execution is forbidden during the audit reads,
confirming no import/fetch/reparse/model path was used. Source Store counts remain
unchanged: 29,647 artifacts, zero analysis runs and zero graph records in that
source-only Store; the original application graph/investigations are preserved.

277 full tests and 17 focused checks pass, with 11 new regressions for read-only
operation, copy isolation, foreign/unpinned routes, corrupt DB/index/map bindings,
path traversal, forged source payloads/coverage and denominator/count changes.
One existing Starlette/AnyIO deprecation remains. All baseline files outside five
mutable continuity/checkpoint files match, including all 550 protected historical
files, labels, forms, snapshots, graphs, raw caches, benchmark failures/results,
maps, manifests and parser identities. No frozen source or historical experiment
was re-imported, rebuilt or silently replaced. No lost unsaved outputs recovered.

Use the reader as a context manager with a checksum-pinned database, index and
staging report. For the current bundle:

```python
from investigation.staged import StagedSourceReader
with StagedSourceReader(
    'data/snapshots/pilot-review-recovered-20261024.db',
    'reports/verified-cache-maps-20261024/maps/index.json',
    'reports/recovered-review-20261024/STAGING.json',
) as reader:
    snapshot = reader.snapshot(CANONICAL_REPOSITORY_ID, PINNED_COMMIT_SHA)
```

Do not pass a live WAL database or call the full-import/analyze route to bypass
the staged guard. This increment does not implement change comparison or a completed
investigation, and does not attach any fabricated reviewed registry/parent run.
Actual staged investigations and real reviewed-registry intake remain NOT_RUN;
independent 91% and saved 95% gates NOT_EVALUATED. No independent labels, inference,
source fetches or commits/pushes. Current native Windows/full-weight RL NOT_RUN;
prior browser/drafts and negative studies retained.

Reproduce the bounded audit into a NEW output directory:
python scripts/audit_staged_source_reader.py --output /tmp/new-staged-reader-audit

Next: coverage-aware comparison over validated snapshots, preserving every
unknown/unavailable outcome rather than converting extraction gaps to additions,
deletions or negative links. An opt-in investigation adapter still needs partial
coverage, source-policy verification and graph/report provenance. Real independent
annotations, semantic adjudication and disjoint final-test freeze remain required.
Final ZIP and fresh-restoration checks are in the sibling release-verification JSON.

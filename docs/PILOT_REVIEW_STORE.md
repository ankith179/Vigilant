# Isolated development review source store

`data/snapshots/pilot-review-20261024.db` is a separate, immutable SQLite snapshot
of the saved offline parser maps. It contains four repositories, 53 commit
snapshots and 28,291 artifact versions under their existing separate parser
identity. Original application databases, graph records and packets are unchanged.

Each commit retains `review_source_map`: the source-map checksum, every file row,
partial status, all UNKNOWN search dispositions and explicit verification limits.
The 10,970 entries include 1,071 missing local blobs, 12 parse-error flagged files,
2,485 unsupported suffixes and 48 nonregular files. No missing file is labelled
irrelevant, consistent or test-free. The staged store has no graph edges, trace
links, findings, analysis jobs, model outputs or independent labels.

The staging builder validates saved checksums, canonical artifact identities,
content hashes, source spans, inventory membership and denominator counts.
This does not authenticate arbitrary self-rehashed maps or perform new whole-source
Git/semantic review. The validation report additionally samples pinned Git evidence
and API source access for each of the 53 snapshots. This is not a full browser run.

## Use a fresh writable store

Run from the project root. To reproduce, choose a new output and report path:

```powershell
python scripts/stage_pilot_review_store.py --database .runtime/pilot-review-live.db --report .runtime/pilot-review-live.json
$env:VIGILANT_DB = "sqlite:///.runtime/pilot-review-live.db"
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Staging refuses existing databases and reports. Its live construction happens in
a temporary runtime, then a consistent SQLite backup is published without replacing
an existing destination. Linux execution is verified; current native Windows
acceptance remains NOT_RUN. Repository paths are project-relative (`data/repos/...`),
so start the application in the extracted project root. Do not point a writable
Store at the immutable snapshot: opening a live SQLite connection changes WAL state.

`reports/pilot-store-20261024/STAGING.json` retains canonical base/head repository,
commit and parser identities for each original case alias, with UNLABELLED and
UNKNOWN fields. Use the existing `/api/artifacts/{artifact_id}` endpoint with the
canonical repository and commit to inspect a saved version. Blank reviewer forms
and original pilot packets are preserved. No automatic review decision is supplied.
Actual review intake still rechecks source against pinned Git.

The staging addition does not implement a registry editing UI, graph generation,
complete coverage proof or full project semantics. Independent 91% and the saved
newer 95% target remain NOT_EVALUATED. Next: generate separate canonical-ID source
packets for reviewers, retaining source gaps and null judgments, then collect real
independent reviews and adjudication before any final-test freeze.

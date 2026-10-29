# Opt-in staged artifact inspection

`StagedInvestigationService(reader, source_policy).call('inspect_artifact', args)`
provides bounded source navigation over checksum-validated frozen snapshots. It
requires a StagedSourceReader and explicit OfflineReviewSourcePolicy; the ordinary
InvestigationService, importer guard and full analyze workflow are unchanged.

The existing strict Inspect schema supplies canonical repository/artifact IDs,
pinned commit, optional starting line and at most 80 excerpt lines. Unavailable
artifacts, foreign revisions, invalid spans, sensitive arguments/source/results
and oversized output fail closed. Missing artifacts never become negative links.

Each excerpt passes the existing pinned-tree and exact local/recovery-blob
verifier, with full receipt, raw object/hash provenance, snapshot coverage, saved
file status and UNKNOWN search scope retained. Parse-error flags remain unknown.
Result IDs bind the complete returned payload, source policy and reader/inspection
module fingerprints. Equal requests over equal inputs return equal result IDs;
there is no retained-result cache that could bypass fresh source verification.

The opt-in CLI `scripts/inspect_staged_artifact.py` requires --repository,
--commit-id, --artifact-id, --output, --verified-source-cache and
--source-recovery-queue. Default database/index/staging paths select the separate
recovered development Store. Output must be a new file. The service makes no
Store/result/graph writes and invokes no importer, parser, subject script or model.
Local read-only Git object operations are performed by the existing source policy;
no fetch or original Git-cache write is allowed. Successful CLI output is a
separate JSON navigation result, not an analysis_runs record or full report.

`scripts/audit_staged_inspection.py --output NEW_DIRECTORY` validates checksum-
pinned packets and attempts this route for each existing source reference. All
unavailable, failed or withheld entries remain under the 140-entry denominator.
This audit does not populate reviewer forms or infer semantic support, consistency,
complete impact or MISSING_TEST findings. No reviewed obligations exist here.

Graph/report integration, retrieval tools, retained-result API/UI routing and a
completed staged investigation workflow remain unfinished. Next: a separately
versioned partial-aware report/graph path consuming validated comparison and
source receipts, with every UNKNOWN retained. Never run full analyze against a
frozen staged Store or rewrite its parser/artifact identities. Both independent
quality gates remain NOT_EVALUATED; current native Windows acceptance is NOT_RUN.

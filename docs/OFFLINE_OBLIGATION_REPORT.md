# Offline source policy for immutable report attachment — 25 October 2026

attach_obligations now accepts the explicit OfflineReviewSourcePolicy and passes
it through reviewed-registry assessment and search enumeration. It structurally
checks parent and derived citations, then independently verifies their pinned
raw source bytes/spans through the scoped policy. Parent/derived receipts are
retained in derivation.source_verification_receipts; registry/search receipts
remain in obligation_review. Missing, foreign, corrupt or out-of-comparison
references fail before publishing a new report. Unsupported policy objects fail.

Opt-in reports use obligation-report-offline-v1 identity, binding the parent ID
and payload fingerprint, registry fingerprint, source-policy provenance and the
attachment module SHA-256. Policy changes create separate records. Legacy report
IDs/default source checks remain unchanged. Reusing an opt-in derived record
rechecks its binding and citations; it cannot return corrupted stored quotes.
Parent reports, artifacts, model outputs, graph records, historical findings and
metrics are never rewritten. The child preserves inherited model/metric context
while explicitly marking no fresh inference/semantic review. No-obligation and
counterevidence/unknown-inventory abstention are preserved.

The CLI scripts/attach_obligations.py now accepts paired opt-in flags:
--verified-source-cache reports/local-source-recovery-20261024/upstream-verified/result.json
--source-recovery-queue reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json
Use them with --database-url pointing to a disposable writable Store copy under
/tmp/vigilant-runtime, a genuinely completed --parent-run-id and a genuinely reviewed
--registry. Run from the project root. Never open frozen snapshots with writable
Store. The CLI validates the flag pair before opening a database and disposes its
engine afterwards. No cache or subject repository scripts are executed; Git reads
use the existing scoped offline verifier. No original Git objects are written.

259 full-suite tests and 30 focused checks pass, with 11 new authored regressions:
cache-backed derivation/receipts/immutability, changed policy fingerprints, corrupt
parent quotes or registry hashes, foreign revisions, fake policies, corrupted
existing-derived quotes, empty/counterevidence/UNKNOWN inventories and receipt
retention via report API/JSON export. One existing Starlette/AnyIO deprecation
remains. A negative CLI check rejects incomplete flags before database/registry
access. These are engineering fixtures, never independent annotation or accuracy.
Prior comparison/recovery failures and the earlier corrected fixture logs remain.

The separate real-source readiness audit opens the canonical staged Store read-only:
29,647 source artifact versions, zero analysis runs and zero graph nodes/edges in
that source-only Store. This does not describe the original application graph,
which is preserved. All 32 adjudication cases remain unlabelled and both reviewer
forms blank. There is no real completed canonical investigation or reviewed registry
to attach, so actual real-project attachment is NOT_RUN. No synthetic parent or
review judgments were added to real project data to demonstrate this feature.

Every baseline file outside seven authorized continuity/checkpoint/attachment
files matches full v41, including all 550 protected historical files, source
caches, snapshots, labels, forms, graph records, maps, manifests and packets. See
AUDIT.json, preservation.json and real-source-readiness.json. Prior source/license
provenance is retained unchanged. No model inference, source fetches, independent
labels, commits/pushes, native Windows or browser rerun. Prior document/browser
acceptance is retained for its documented scope. Independent 91% and saved 95%
gates remain NOT_EVALUATED; full LLM-weight RL remains NOT_RUN.

Next: audit existing-snapshot investigation routing for the canonical partial
Store, avoiding re-import/fetch/parser-ID rewrites and preserving unknown coverage.
Real independent annotations, semantic adjudication and repository/change-family-
disjoint final freeze remain required. Do not infer complete impact/consistency
truth from source patches or source-validation receipts. Final ZIP/fresh-restore
checks are in the sibling release-verification JSON.

# Opt-in offline reviewer-intake policy — 25 October 2026

An explicit OfflineReviewSourcePolicy now connects the existing tested offline
source verifier to validate_reviews. Without a policy the default Git validation
and returned fields remain unchanged. Combining a policy with check_git=False or
an unsupported policy object is rejected. All existing adjudication, distinct
reviewer, independent-author attestation, evidence-scope and strict-schema checks
run before source acceptance. Identity authentication is still attested, not proven.

The policy validates the recovery manifest and queue, confines repository paths
to the declared project root, checks canonical project/repository/origin identity,
then checks immutable Git trees, exact local/cache blob hashes, full stored spans
and reference excerpts. Cache fallback requires queued origin/commit/path scope.
Missing, foreign or forged sources fail closed. Git transports/lazy fetch are
disabled in this path; original Git objects are never populated or rewritten.
Per-reference receipts retain source status, raw Git object ID/SHA-256, canonical
artifact/commit/hash/spans and origin. Cache, queue and verifier fingerprints are
included in the validated intake output. Search UNKNOWNs remain unchanged.

The CLI scripts/import_independent_reviews.py exposes paired opt-in flags:
--verified-source-cache reports/local-source-recovery-20261024/upstream-verified/result.json
--source-recovery-queue reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json
Use them only with actual completed adjudication and two independent forms. Use
a disposable writable copy of the frozen source Store under /tmp/vigilant-runtime,
run from the project root, and choose a NEW output path. Do not open either frozen
snapshot with writable Store. Output uses exclusive creation to preserve prior work.
No new upload UI or authenticated reviewer-identity service is claimed.

Verification: 234 full tests / 21 focused tests pass, with 11 new policy regressions
for exact receipts/unknown preservation and disabled checks, unsupported policies,
blank or duplicated/unattested reviewers, forged content, foreign repositories,
outside-root paths, unscoped cache entries and corrupt manifests. One existing
Starlette/AnyIO deprecation remains. Three negative CLI checks reject incomplete
flags, prepare-plus-cache and blank completed forms; none creates a labels file.
The blank-form CLI check uses a disposable source Store copy. Originals are intact.

A separate source-only audit exercises the integrated policy on all 140 entries
of the existing 32 development packets: 44 local and 92 recovered references verify,
while four missing-reference entries remain explicit under the same denominator.
Both original blank reviewer forms are still rejected. No real adjudication/intake
completed and no independent labels, model inference, source fetches or commits/
pushes occurred. Source receipts do not establish semantic support, complete impact
truth or consistency accuracy. Independent 91% and saved 95% remain NOT_EVALUATED.
Current native Windows acceptance and full LLM-weight RL remain NOT_RUN. Prior
browser/document acceptance and all negative model/bandit results are preserved.

The preservation manifest checks every baseline file except seven authorized
continuity/checkpoint/intake files, including all 550 protected historical files,
all source caches, snapshots, graphs, experiments, manifests, labels, maps and
packets. Original source/license provenance remains pinned in the prior recovery
and search-draft records; no blanket relicensing or recovered lost measurements.

Reproduce the source-only audit into a NEW output directory:
python scripts/audit_offline_review_policy.py --output /tmp/new-policy-source-audit

Next: audit optional reviewed-obligation intake for safe policy/receipt reuse,
preserving lifecycle/search-inventory checks and the no-obligation/no-MISSING_TEST
guard. Real independent annotations, semantic adjudication and a repository/change-
family-disjoint final freeze are still required. Do not invent them from patches
or source verification. Final package/fresh-restore checks are in the sibling
release-verification JSON.

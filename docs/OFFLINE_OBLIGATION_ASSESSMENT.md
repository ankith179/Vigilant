# Scoped offline obligation assessment — 25 October 2026

The reuse audit identified four verification paths: obligation references, every
historical search inventory, the standalone assessment CLI, and both citation
passes in derived-report attachment. The first three now support explicit opt-in
OfflineReviewSourcePolicy. Default assessment/search behavior and historical
fingerprints remain unchanged. Saved-report attachment still uses its default Git
path; this increment does not claim that integration is complete.

assess_registry accepts source_policy only with check_git=True and the concrete
validated policy type. Every revision source, supporting/counter/cause evidence
and search evidence is checked, with per-obligation/revision receipts. Scope,
append-history, lifecycle, satisfaction, counterevidence and root-cause grouping
logic is unchanged. No obligation means no MISSING_TEST. Actual reviewed input
and explicit complete-search attestations remain necessary; neither bytes nor
unchanged/unlinked tests invent an obligation or a negative label.

The opt-in search path enumerates exact pinned tree identities without requesting
blob sizes or contents for UNKNOWN/EXCLUDED paths. SEARCHED paths still need
regular eligible source files and exact source-policy verification, including the
two-million-byte raw limit, canonical artifacts and reference spans. Missing/forged
sources fail closed. Every historical inventory is checked even if the newest
revision has none. UNKNOWN entries prohibit reviewed completeness. Tree access
returns copies so callers cannot poison the verifier's cached binding. Provenance
now also records the intake module fingerprint. No subject scripts, lazy fetching,
Git transports or original Git-object writes occur in this opt-in path.

Real-source verification retained all 53 saved snapshots / 32 development cases
and all 10,970 UNKNOWN file entries, with zero enumeration failures or fetches.
It created no reviewed registry, obligations, labels or findings. All source Store,
map, packet, draft, graph, label and historical experiment files remain unchanged.
The audit source Store is opened read-only and checked before/after. Original
source/license provenance in prior recovery/search records is retained.

248 tests pass, including 53 focused checks and 14 new cache/search/lifecycle
regressions. Two negative CLI checks reject incomplete policy flags and preserve
existing output. One existing Starlette/AnyIO deprecation remains. An initial
authored fixture incorrectly combined UNMET with partial search; the existing
schema guard correctly rejected it. Both initial failure logs are retained. The
fixture now uses UNKNOWN satisfaction; the production guard was not weakened.
All baseline files except nine explicitly mutable continuity/checkpoint/verification
files match full v40, including all 550 protected historical files.

The assessment CLI scripts/assess_obligations.py exposes paired flags:
--verified-source-cache reports/local-source-recovery-20261024/upstream-verified/result.json
--source-recovery-queue reports/canonical-review-20261024/SOURCE_RECOVERY_QUEUE.json
Use them with a genuinely reviewed --registry, --commit and NEW --output. Keep
frozen snapshots immutable: use a disposable writable source Store copy under
/tmp/vigilant-runtime and the corresponding --database-url. Independent reviewers
must supply their own judgments; reviewer identity and semantic correctness remain
attested, not authenticated. Legacy scopes without Git inventory remain explicitly
NOT_MACHINE_ENUMERATED. This is scoped development intake, not whole-project proof.

Reproduce the UNKNOWN-only audit into a NEW output directory:
python scripts/audit_obligation_source_policy.py --output /tmp/new-obligation-enumeration

Actual reviewed-registry intake and independent 91%/95% evaluation remain NOT_RUN /
NOT_EVALUATED. No model inference, source fetches, commits/pushes or independent
labels. Current native Windows acceptance and full LLM-weight RL NOT_RUN. Prior
browser/documents and negative retrieval/model experiments are preserved.

Next: add explicit source-policy support to immutable report attachment, checking
both original and derived citations and including policy provenance in the new
report identity. Never rewrite parent/model/graph records. Real independent
annotations, semantic adjudication and disjoint final-test freeze remain required.
Final ZIP/restoration checks are in the sibling release-verification JSON.

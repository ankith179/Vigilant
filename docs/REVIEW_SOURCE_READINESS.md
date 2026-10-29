# Offline reviewer-source readiness — 24 October 2026

The bounded probe kept all 140 changed-file side entries from the 32 unlabelled
canonical development packets. Local-only verification finds 44 exact sources,
92 unavailable blobs and four paths absent from pinned trees. With the existing
scoped verified cache, 44 local and 92 recovered references verify. Four absent
paths remain unresolved in the same denominator. No path is called newly added
or renamed, and no unlinked/unchanged artifact is labelled negative.

For every reference the probe checks the immutable commit and tree/path binding,
regular blob mode/type, raw Git object hash, canonical artifact identity, content
hash, full stored artifact span and reference excerpt. Cache fallback requires
an exact queued origin/commit/path scope and rechecks raw bytes. Size limits,
queue/cache manifests and packet/Store fingerprints are retained. Git runs with
lazy fetch and transports disabled, hooks/fsmonitor disabled, and no subject code
execution. Cache reads never populate or rewrite original repository objects.

223 full-suite tests and eight new focused source-check regressions pass, covering
local/cache equivalence, raw-byte corruption, foreign origin/commit, stored-content
or reference-identity changes, invalid spans and absent paths. One existing
Starlette/AnyIO dependency deprecation remains. All baseline files outside the
five declared mutable continuity/checkpoint files match, including historical
experiments, inputs, source caches, manifests, both Stores/packet versions, graph,
labels and forms. Counts and hashes are in AUDIT.json and preservation.json.

The existing validate_reviews path is unchanged: actual intake was NOT_RUN because
forms remain blank, and it does not consume this optional cache probe. This probe
establishes source-readiness only, not independent review, reviewer authentication,
semantic entailment, complete impact/consistency gold or an accuracy result.
Every search disposition remains UNKNOWN. No new fetches, model calls, reviews,
commits or pushes occurred. Independent 91% and saved 95% gates remain
NOT_EVALUATED; full LLM-weight RL and current native Windows acceptance NOT_RUN.
Prior browser/document checks and negative recovery/bandit results are preserved.

Reproduce only into a NEW output directory:

```bash
python scripts/check_review_source_readiness.py --output /tmp/new-source-readiness
python -m pytest -q tests/test_review_source_readiness.py
```

Default inputs bind to reports/recovered-review-20261024/STAGING.json and packets,
data/snapshots/pilot-review-recovered-20261024.db and the pinned prior recovery
queue/cache. Results refuse overwrite. Original license/provenance records in
reports/local-source-recovery-20261024/ and the search-draft index remain unchanged.

Next: connect the scoped offline verifier through an explicit opt-in intake policy
with provenance receipts, preserving default validation, independent attestations
and rejection of invalid references. Then actual independent reviews/adjudication,
semantic review and a repository/change-family-disjoint final freeze are required.
Do not create labels to exercise that scientific gate or repeat old model studies.
Final ZIP checks and fresh-restore evidence are in the sibling release-verification
JSON; original scientific measurements are unchanged.

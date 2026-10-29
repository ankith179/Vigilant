# Verified-cache pilot maps

These maps are a separate unreviewed development source version. They use the
79 exact blobs verified in the prior read-only recovery pass. No new fetches,
model inference, reviewer judgments or independent evaluation occurred.

The immutable output is `reports/verified-cache-maps-20261024/maps/index.json`.
All 53 snapshots / 32 cases retain all 10,970 file entries. The cache supplies
89 distinct snapshot-file rows covering 92 queued case-side occurrences; three
occurrences share already counted snapshot files. Artifact versions increase
from 28,291 to 29,647. There are 7,443 parsed files, 12 with existing parse-error
flags, 982 missing local blobs, 2,485 unsupported suffixes and 48 nonregular
entries. The four absent pinned-tree paths remain unresolved; absence does not
establish creation, rename, impact or consistency.

The new canonical identity binds parser sources, the map-builder source and the
verified-cache manifest. All original artifact IDs, maps, Store, packets, graph
provenance, labels and failed recovery records remain unchanged. New and original
artifact ID sets have zero overlap. Every search disposition is UNKNOWN.

The builder reads local Git objects without lazy fetch, and consumes cache bytes
only for a queued origin/commit/path with the matching pinned blob ID. It checks
cache/queue fingerprints, raw-byte hashes, sizes and safe paths before parsing.
Per-file and snapshot byte budgets still apply. No subject repository code runs.
The staging validator now recognizes this exact additional identity policy;
original-policy validation remains supported. No new source Store was staged.

Reproduce into a NEW output directory (the builder refuses existing outputs):

```bash
python scripts/prepare_pilot_artifact_maps.py --verified-cache reports/local-source-recovery-20261024/upstream-verified/result.json --output /tmp/new-pilot-map-directory
python -m pytest -q tests/test_verified_cache_maps.py tests/test_search_inventory.py tests/test_pilot_review_store.py
```

`reports/verified-cache-maps-20261024/AUDIT.json` records all identity/content/span
checks, every queued occurrence, unchanged boundaries and preserved baseline
files. `scripts/audit_verified_cache_maps.py --baseline-archive <full-v36-archive>`
reproduces that audit before package metadata changes, refusing report overwrite.
The original source URLs, exact Git identities and project-specific license
notice provenance remain in `reports/local-source-recovery-20261024/` and
`reports/search-drafts-20261024/prepared/index.json`; no blanket relicensing.

Next: stage these new maps in a NEW isolated review Store and then generate NEW
canonical reviewer packets using its routes. Keep original snapshots and packets
frozen, preserve unknowns and null judgments. Independent annotations, semantic
review and a repository/change-family-disjoint final freeze remain required.
Both quality gates remain NOT_EVALUATED. Whole-project language semantics,
current native Windows acceptance and full LLM-weight RL remain unestablished.


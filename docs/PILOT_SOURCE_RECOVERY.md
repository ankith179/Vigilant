# Exact queued source recovery

This increment preserves the frozen development pipeline and adds separate recovery
records under `reports/local-source-recovery-20261024`. It does not rewrite the old
maps, review store, packets, Git caches, graph records or reviewer forms.

The local-only pass checked the 79 queued object IDs against existing Git caches,
worktree files and UTF-8 reconstructions of stored source text. It recovered zero
objects: 79 Git-cache misses, 886 byte-mismatch attempts and four unavailable
candidate attempts are retained. There were no scan errors. A reconstructed text or
line-ending variant is never accepted unless its bytes match the queued Git blob ID.

Read-only GitHub blob requests then retrieved all 79 exact queued objects. Their
bytes passed both the verifier and native `git hash-object --stdin`, covering the
92 previously missing changed-file side entries. All 79 responses, source URLs,
response checksums, object IDs and occurrence-level provenance are retained.
`upstream-verified/objects` contains the validated raw source bytes. The original
negative local result remains in `recovery/result.json`. No unsaved prior experiment
results were recovered or claimed recovered.

Four paths absent from their pinned trees remain unresolved. The original packets
still record their old missing-source state: recovery bytes are not silently
promoted to parsed artifacts, reviewed coverage, labels or complete impact gold.
The 32 pilot cases remain exposed development material. Both independent 91% and
the newer 95% target remain NOT_EVALUATED.

## Reproduce verification without fetching

```powershell
python scripts/verify_upstream_pilot_blobs.py --output NEW_VERIFIED_CACHE
```

To repeat the local diagnostic in a new output directory:

```powershell
python scripts/recover_local_pilot_blobs.py --output NEW_LOCAL_RECOVERY
```

Both commands refuse existing output directories. The upstream verifier only reads
saved responses; it does not contact GitHub. Re-fetching uses the read-only source
URLs retained per object. No target repository scripts or model inference run.
Original repository notices remain bundled. `LICENSE-PROVENANCE.json` records pinned
notice object IDs per source occurrence; no blanket relicensing is performed.

Next: incorporate the validated cache into separately versioned partial maps under
a new parser identity, then a new review store/packet version. Keep the originals,
all unknown regions and blank judgments. Real independent annotations, semantic
adjudication and a disjoint final-test freeze remain required.

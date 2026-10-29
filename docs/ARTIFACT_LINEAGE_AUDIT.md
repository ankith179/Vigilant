# Artifact identity and history: bounded audit

Current V008 implementation: LINEAGE_OBSERVATIONS.md and reports/lineage-observations-20261025/task-update.json. Source observer verified; canonical consumers and broader lineage correctness remain open.

V008 remains IN_PROGRESS. This audit records current behavior; it does not add
path-independent identity, migrate IDs, change production deltas or certify lineage.

`ingestion/models.py::artifact` hashes project/repository/path/kind/symbol for the
artifact ID. Content/version hashes and commit IDs are separate. Therefore a path
move changes the artifact ID and a later reuse of a path/symbol can reuse an ID.
`change_analysis/diff.py::detect` compares endpoints and pairs a Git `-M` file
rename only when symbol/type matches uniquely. It does not inspect full history
or prove that a symbol has remained the same logical entity.

| Authored fixture | Observed production behavior | Interpretation |
|---|---|---|
| Exact file rename | `renamed`, new artifact ID | Explicit bounded Git-supported candidate association |
| Modified file rename | `renamed`, differing content hashes | Rename is not semantic equivalence |
| Copy retaining original | `added`, distinct path ID | Identical text is not identity |
| Symbol move between retained files | `deleted` plus `added` | Cross-file continuity unresolved |
| Remove first duplicate definition | First ID reused as `modified`; second `deleted` | Ordinal continuity is ambiguous; first duplicate lacks an ambiguity marker |
| Divergent sibling branches | Same ID, `modified` | Endpoint comparison does not enforce linear ancestry |
| Delete, then recreate identical source | No endpoint artifact delta | Intervening history is not captured by endpoint equality |
| File move plus symbol rename | `deleted` plus `added` | File-level rename does not resolve symbol identity |
| Missing revision | Git resolution rejects | No fabricated comparison |

Run `python scripts/audit_artifact_lineage.py --output <new-directory>` to create
separate records. It writes only disposable locally authored Git fixtures and
the selected output. Fixed fixture dates, authored identities and full source
records make observations repeatable in the same declared Git/parser environment.
It uses the actual snapshot/parser/delta functions and never executes fixture code.
Fixture commits are not commits to VIGILANT. Git similarity is heuristic and can
vary with Git version/configuration; the exact version and resulting commits,
trees, blob inventories, extracted artifacts and deltas are saved.

All logical continuity remains UNKNOWN and all semantic correctness remains
NOT_ESTABLISHED. These fixtures are authored diagnostics, not independent labels,
real-project coverage estimates or research accuracy measurements. Reports retain
all nine cases, including the missing revision, under the declared denominator.

Next implementation acceptance: a separately versioned, opt-in sidecar must bind
both endpoint revisions/artifacts/source fingerprints, reject foreign/stale scope,
retain duplicate/branch/history ambiguity and preserve one-to-one candidate limits.
Copies and equal content must not silently merge entities. Missing/partial source
must remain unknown. Consumers must not transfer graph links, citations or reviewed
obligations across identities based on an unreviewed candidate. Preserve all frozen
artifact IDs and parser identities; no global ID rewrite or reindex is authorized.

Evidence: `reports/lineage-audit-20261025/VERIFICATION.md`, `observations/result.json`
and the separately captured source inventory. Existing frontend/browser evidence is
preserved; production application files and generated frontend are unchanged.

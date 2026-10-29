# Staged investigation routing audit and import guard — 25 October 2026

The canonical partial Store cannot safely enter the full import/analyze path as
though it were a complete source snapshot. The audit found that import_repository
updated repository metadata before its prior-artifact shortcut. A staged row uses
project-relative paths and source-scope fields; the old replacement could erase
those fields before an immutable commit-shape conflict stopped import. No original
Store was mutated to demonstrate this finding.

The importer now checks the resolved repository/commit for the review_source_map
marker before all project/repository/commit writes. Identified staged snapshots
raise an actionable existing-snapshot-route error, even if the marker is empty or
no artifacts are available. Ordinary existing-snapshot reuse still works without
reparse. This is a guard, not a partial-snapshot workflow adapter. It protects a
resolved staged identity; default project imports still target a different ID.

Read-only probes of all 53 actual staged routes / 32 cases confirm 53 expected
guard rejections and zero metadata write attempts, artifact loads, reparses or
fetches. A read-only SQL adapter rejects writes; Git dependencies are replaced in
the audit process with the existing transport-disabled/local-only helper. Only
local commit-resolution and remote-configuration metadata commands run. No native
full analysis is started. Default project IDs differ on all 53 routes; explicit
canonical project IDs match on all 53. Canonical IDs are not rewritten.

All 10,970 file-status entries remain: 7,443 PARSED, 12 PARSED_WITH_ERRORS,
982 MISSING_LOCAL_BLOB, 2,485 UNSUPPORTED_SUFFIX and 48 NON_REGULAR_FILE. The source-
only Store remains at 29,647 artifacts, zero analysis runs and zero graph records.
The original application graph/investigations are separately preserved, not absent.
Frozen Store SHA-256 is checked before and after; raw source/cache/map/packet and
label records are unchanged. No lost unsaved experiment measurements recovered.

Remaining routing barriers are explicit in probe/result.json and source fingerprints:
- analyze still imports snapshots before change/graph analysis and writes job state.
- detect uses Git blob diffs/rename detection and treats missing artifact IDs as
  additions/deletions; unavailable partial sources require separate unknown states.
- coverage and investigation exploration request size-based Git inventories.
- full workflow/tool evidence verification still reads Git blobs directly; it is
  not yet wired to the scoped recovery policy for partial source investigations.
- partial graphs/impact paths need explicit scope/provenance, never complete-impact
  truth or negative labels from absent artifacts/links.

266 full tests and 17 focused checks pass, including seven new guard regressions:
empty/malformed/normal staged markers with and without artifacts stop before writes
or parsing, and ordinary snapshot reuse remains available. One existing Starlette/
AnyIO dependency deprecation remains. The baseline preservation manifest verifies
all files outside six declared mutable continuity/checkpoint/importer files,
including all 550 protected historical files and all benchmark inputs/results,
failed recovery records, labels, forms, graph provenance, snapshots and manifests.

Reproduce this bounded audit into a NEW output directory:
python scripts/audit_staged_routing.py --output /tmp/new-staged-routing-audit

Do not run the full workflow or open frozen snapshots with writable Store to bypass
the guard. For eventual execution use disposable live copies under /tmp/vigilant-
runtime and an explicit existing-snapshot route that preserves coverage/identity.
No reviewed registry, model inference, source fetches, commits/pushes or independent
labels were created. Actual staged investigations remain NOT_RUN. Independent
91% and saved 95% gates remain NOT_EVALUATED; current native Windows acceptance
and full LLM-weight RL NOT_RUN. Prior browser/drafts and negative studies retained.

Next: validated read-only staged-source access with file-status coverage, followed
by opt-in partial-aware investigation routing. Do not reinterpret missing extracted
artifacts as deletion or patches as complete impact/consistency gold. Real independent
review, semantic adjudication and a disjoint final freeze remain required. Source
licenses/provenance remain in the original pinned recovery/search records. Final
ZIP/fresh-restoration evidence is in the sibling release-verification JSON.

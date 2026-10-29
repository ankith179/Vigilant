# Partial staged-source comparison

`investigation.staged_comparison.compare_staged(reader, repository, base, head)`
uses the existing `StagedSourceReader` for two explicitly pinned snapshots under
the same canonical repository/parser identity. It never imports sources, invokes
Git/compiler/model tools, runs subject scripts or changes a Store. The importer
guard remains in force. This is a source observation adapter, not a completed
investigation workflow or an independent quality evaluation.

Every path in the union of the partial file maps is retained, with complete saved
file rows for both sides, or null for an unavailable side. Object IDs present in
both maps produce SAME_OBJECT_ID or DIFFERENT_OBJECT_ID; these describe saved
tree/map observations, including unsupported or unavailable source files. They do
not mean the reader reverified raw bytes. A missing map side produces UNKNOWN,
never an addition or deletion. Pinned-tree absence, renames and full search
boundaries require separate evidence and are not established here.

Every artifact ID present on either side is retained, including unchanged ones.
Paired artifacts in PARSED files have SAME_EXTRACTED_CONTENT or
DIFFERENT_EXTRACTED_CONTENT outcomes. Unpaired artifacts and any non-PARSED side
(including PARSED_WITH_ERRORS) produce UNKNOWN with explicit reasons. A paired
parse-error artifact can still record an observed hash relation without promoting
its outcome. Absence from even a PARSED counterpart does not establish a deletion:
extraction is not complete project semantics. Artifacts present in neither map
cannot be enumerated; file gaps and whole-repository coverage=false remain visible.

Denominators describe observed file/artifact unions and both-side slots, with
observed and unavailable counts. They are engineering observation denominators,
not a substitute for the frozen prediction denominator or independently reviewed
project gold. Each union row has exactly one outcome; UNKNOWN rows are never
filtered from the counts. Case-weighted audit totals count snapshots again when
used in different pairs. All search dispositions, source gaps and snapshot
coverage records survive comparison.

Results bind both reader/map/cache provenance records and the comparison module
SHA256, and carry a deterministic payload fingerprint. Reader validation is
checksum-pinned map/Store correspondence, not fresh raw Git or semantic review.
Semantic equivalence, full impact, consistency and negative links remain
NOT_ESTABLISHED. No consistency finding, MISSING_TEST finding, trace link, graph,
review judgment or model output is generated.

`scripts/audit_staged_comparison.py --output NEW_DIRECTORY` writes separate
development observations for the checksum-bound staged cases, with failed cases
retained. It refuses overwrite and checks routing, all outcome denominators,
fingerprints and unchanged source-only Store counts. Subprocess invocation is
forbidden during comparisons. The original maps/Stores/packets remain frozen.

The next local increment is an explicit opt-in investigation route that consumes
these partial observations with scoped raw-source verification and separately
versioned graph/report provenance. Full analyze remains unsuitable for frozen
staged snapshots; do not bypass its import guard. Real independently reviewed
registries, semantic adjudication and repository/change-family-disjoint freeze
are still required. Both the 91% gate and saved 95% target remain NOT_EVALUATED.

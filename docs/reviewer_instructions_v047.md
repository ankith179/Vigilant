# Reviewer instructions — V047 development pilot

1. Review only the CSV assigned to you. Do not open the other reviewer's sheet or any model output, authored label, D-ID, or candidate-category report before submitting your initial judgments.
2. Run the `diff_command` from the project root to inspect the exact BASE-to-HEAD change. Then inspect the relevant requirement/specification, implementation, consumers, tests, and fixtures at their pinned revisions.
3. Fill the four independent label columns using the exact allowed values. Do not force a decisive answer when evidence is missing. `UNCERTAIN` and `UNVERIFIED` are valid outcomes.
4. Record a privacy-preserving reviewer ID, UTC timestamp, concise rationale, and evidence notes. Cite revision, path, line range, and content hash. If an axis is uncertain or unverified, fill `uncertainty_reason`.
5. Leave `adjudication_status` as `PENDING` while working; set it to `SUBMITTED` only after completing the row and checking all citations. Do not edit case IDs, revisions, paths, or symbols.
6. Return the completed file without sharing it with the other reviewer. Initial judgments are preserved before conflict resolution.

See `docs/adjudication_protocol_v047.md` for the frozen pilot label rules and disagreement process. These are development labels, not independent test labels.

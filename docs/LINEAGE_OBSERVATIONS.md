# Opt-in source-backed lineage observations

Current V008 shared-tool integration: LINEAGE_INVESTIGATION_TOOL.md and reports/lineage-tools-20261025/task-update.json. HTTP/CLI/MCP and retained reads are opt-in verified; UI and broader lineage correctness remain open. Earlier bounded records below retain their original scope.

V008 remains IN_PROGRESS. The observer and standalone command are implemented for
bounded source inspection. Canonical investigations and graph/citation/obligation
consumers do not consume these records. Frozen IDs and original deltas are preserved.

`change_analysis/lineage.py::observe` reads exact pinned Git commits and selected
eligible source blobs, verifies Git object IDs and raw SHA-256, then parses in a
separate observer namespace. The namespace binds caller context, parser policy,
source-module hashes, interpreter, Git and grammar/native-package versions. Caller
context does not establish authenticated repository ownership. Newly parsed observer
IDs are not promoted to canonical IDs or used to rewrite historical snapshots.

Records contain revisions, selected paths, source trees/blob receipts, content
hashes/spans, bounded file-history evidence and deterministic record/observation IDs.
`verify` reconstructs the entire record from the caller's expected project,
repository, base/head SHAs and path selection. Tampered scope/content/policy fails
closed. A saved subset requires the same explicitly expected paths; omitting paths
expects the default eligible selection within the file limit.

| Observation | Meaning |
|---|---|
| SAME_KEY_CANDIDATE | Same endpoint path/type/symbol without a detected blocker |
| GIT_RENAME_CANDIDATE | Git `-M` file correspondence plus matching unique type/symbol |
| UNKNOWN | Unmatched endpoint, duplicate ordinal/content ambiguity, nonlinear/incomplete history or parse error |

Every observation stays UNREVIEWED, logical continuity UNKNOWN, semantic equivalence
NOT_ESTABLISHED and relationship_transfer_allowed=false. Candidates are one-to-one.
Equal content alone never merges copies or cross-file symbols. Duplicate ordinal
groups include the first occurrence even when it lacks an ambiguity marker.
Divergent/reverse/unrelated histories do not generate lineage candidates. An observed
intervening file deletion blocks same-key continuity even for identical endpoint
text. A normal terminal file rename can retain a Git-supported candidate. Unmatched
artifacts do not become confirmed additions/deletions or missing-test findings.

Limits: 64 selected files, 2,000 artifacts per revision, existing Git file/read
limits and a maximum 32-commit file-deletion scan. Longer histories stay unknown.
Ancestry-path and merge-parent deletion evidence is conservative; disappearance or
recreation of a symbol inside a surviving file is unresolved. This is selected-file
syntax inspection, not whole-project semantics or a strict aggregate wall-clock/
process sandbox. Binary and absent selected sides remain in the file denominator.
Missing commits and explicitly excluded/unsupported source paths reject the operation.
Git similarity is heuristic. Current native Windows acceptance is not established.

Explicit command from the project root:

```bash
python scripts/observe_artifact_lineage.py --repository-path /local/repo \
  --project my-project --repository-id my-repository \
  --base FULL_BASE_SHA --head FULL_HEAD_SHA --path src/a.py --path src/moved.py \
  --output /new/path/lineage.json
```

It refuses existing outputs, reads Git objects rather than worktree text, freshly
verifies before saving, and writes no Store/model/graph records. No subject code
runs. Exclusive file creation prevents overwrites; crash-atomic publication is not
claimed. The command remains separate from canonical API/MCP/investigation flows.

`scripts/audit_lineage_observations.py --output <new-directory>` retains all nine
authored cases: eight source-revalidated sidecars and a missing-revision unknown.
Tests cover duplicate groups/content, copies, moves, renamed symbols, divergent
history, file deletion, history limits, parse errors, missing/binary source, scope/
policy tampering, canonical namespace separation and overwrite protection.

Evidence: `reports/lineage-observations-20261025/VERIFICATION.md`, `RELEASE.json`,
`acceptance-restored/result.json`, `tests-restored.log` and `inventory/`.
Saved initial acceptance records remain unchanged. These are authored engineering
checks, not independent labels or semantic/lineage accuracy. Both quality gates
remain NOT_EVALUATED. Next: opt-in scoped investigation-tool integration with
identity/authentication/source guards and no automatic relationship propagation.

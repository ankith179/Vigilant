# Opt-in paired-revision lineage inspection

`inspect_lineage` is implemented through the shared InvestigationService used by
HTTP, CLI and local stdio MCP. It is default-disabled and omitted from discovery.
Set `VIGILANT_LINEAGE_TOOLS=1` in the server/CLI/MCP process environment to enable it.
The flag is not authentication: HTTP retains the existing workspace-token guard;
CLI/MCP use the trusted local process session. No multiuser/RBAC claim is made.

Arguments require repository, exact head `commit_id`, exact `base_commit`, and
1–16 explicitly selected repository-relative paths (at most 1,024 characters each).
Both revisions must already be indexed in the same registered canonical repository
and project/parser scope. Partial staged commits are rejected; their separate
partial-aware workflow is unchanged. No request-supplied filesystem path or import
is accepted by this tool. Missing/unsupported source fails closed.

```json
{"name":"inspect_lineage","arguments":{"repository":"REGISTERED_REPOSITORY_ID","commit_id":"FULL_HEAD_SHA","base_commit":"FULL_BASE_SHA","paths":["src/old.py","src/new.py"]}}
```

Send this payload to `POST /api/investigation/call` using the existing configured
token. CLI: save the arguments object as a new JSON file, then run:

```bash
VIGILANT_LINEAGE_TOOLS=1 python vigilant.py --database DATABASE_URL call inspect_lineage --arguments arguments.json
VIGILANT_LINEAGE_TOOLS=1 python vigilant.py --database DATABASE_URL mcp
```

MCP uses its existing tools/call and retained-result resource protocol. The same
source-verified result is returned by every transport. On PowerShell set
`$env:VIGILANT_LINEAGE_TOOLS='1'` before the existing command. Native Windows
acceptance of this increment remains NOT_RUN.

The adapter obtains a fresh separately namespaced observer record, then matches
selected full-file source parents against each indexed revision: project/repository/
commit, canonical parent ID formula, type, content hash and full span. Full indexed
source is reverified against pinned Git and scanned for known secret patterns.
Returned canonical source excerpts are bounded to 12 lines per selected file side.
Observer IDs remain separate; no graph edge, citation or obligation is transferred
between artifacts. Original parser IDs and source snapshots are not rewritten.

ToolResult remains head-scoped, with the exact paired observer scope in
data.lineage_record. Evidence explicitly retains its own base/head commit. Results
and source-linked unknowns are retained in the existing local tool/unknown tables.
Every candidate remains UNREVIEWED; logical continuity UNKNOWN; semantic support
NOT_ESTABLISHED; relationship_transfer_allowed=false. Unmatched artifacts never
become confirmed additions/deletions or missing-test findings.

`inspect_retained_result` and MCP resource reads rebuild paired source/observer data
and compare evidence, module/policy hashes and scope before reuse. Altered source,
stored parents, data, policy or scope reject. Turning the flag off rejects retained
lineage reads as well. Ordinary historical tool results keep their prior contract.
Shared scope resolution now converts missing Git-revision subprocess failures into
the existing ValueError rejection path rather than leaking an uncaught transport error.

Budgets: existing 20,000-artifact/20-million-character snapshot scope limit, 16 paths,
observer 2,000 artifacts per revision and 32-commit file-deletion scan, and existing
750,000-byte output cap before persistence. Oversized outputs reject rather than
silently removing unknowns. These bounds do not establish strict aggregate wall-clock
preemption or resource/security certification. Secret detection covers the existing
patterns; complete secret discovery is not claimed.

Acceptance: nine new tests plus the existing shared-tool suite; an HTTP audit retains
all nine authored cases, including one missing-revision unknown. Eight valid cases
revalidate on retained reads; unauthenticated calls reject for all nine. One real
API/CLI/MCP/resource fixture verifies identical retained payloads. No model calls,
independent labels or frozen production database changes occur in this acceptance.

See reports/lineage-tools-20261025/VERIFICATION.md and RELEASE.json. V008 remains
IN_PROGRESS: UI controls, complete symbol/history lineage, authenticated independent
review and wider acceptance remain open. Both quality gates remain NOT_EVALUATED.

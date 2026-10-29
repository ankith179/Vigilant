# VIGILANT architecture

Git revisions and immutable artifact snapshots feed deterministic diff/extraction, typed graphs, retrieval, rules, bounded advisory interpretation, evidence checks, saved reports and grounded chat. Existing services remain in place; there is no replacement scaffold.

`agents/workflow.py` owns base/head analysis. `investigation/service.py` exposes reusable snapshot investigation over those records. `vigilant.py`, `investigation/mcp.py`, `/api/investigation/call` and the Investigation Tools UI use that same service. The existing analysis API queues the shared `analyze` workflow; `python vigilant.py compare` calls it synchronously with model=none.

The tool envelope separates structured data, exact-source evidence, unknowns, limitations, scope, tool policy and a semantic content identity. Sources and paths remain revision-scoped. Graph traversal reverses dependencies and never splices edges across commits. Structural candidates are not proof of causal or semantic impact.

SQLite remains the default. Store initialization adds `tool_results` and `unknown_revisions` tables without deleting or rewriting existing rows. Existing frozen databases and experiments remain unchanged. SQLAlchemy PostgreSQL compatibility is existing infrastructure; this release has not validated a hosted PostgreSQL deployment. Both connected database accounts returned no projects; no remote schema or credentials were created.

See INVESTIGATION_ENGINE.md, EVIDENCE_AND_PROVENANCE.md, GRAPH_SCHEMA.md, CLI_REFERENCE.md and MCP_REFERENCE.md.

# Investigation engine

The existing `analyze` workflow resolves Git SHAs, imports snapshots, detects changes, builds each revision graph, recovers candidate links, runs rules, retrieves paired evidence, checks Git blobs and optionally asks a configured model to interpret ambiguity. Advisory output cannot overwrite deterministic findings.

The new shared service offers ten schema-validated operations: explore_repository, inspect_artifact, find_relationships, trace_impact, retrieve_evidence, inspect_investigation, inspect_retained_result, list_unknowns, update_unknown and run_recipe. The HTTP interface and default MCP catalog omit update_unknown. CLI use and explicit MCP `--allow-record-updates` permit local record updates only.

Five recipes are implemented: understand_repository, trace_feature, review_tests, explain_dependencies and review_investigation. They call the same tools, retain step references and stop after one to four allowed steps. Missing required inputs fail; insufficient sources and budget exhaustion stay visible. Recipes use no model and execute no subject code. They are deterministic orchestration for an external agent, not a claim of autonomous semantic reasoning.

Bounds: 100 items per page, four graph hops, 20,000 indexed artifacts, 20 million snapshot characters, 20,000 graph edges, 24 graph endpoint excerpts, 80 lines for direct inspection and a 750 KB result envelope. Snapshot scope is checked before loading payloads. Individual Git operations have existing timeouts. There is no general asynchronous tool cancellation; use bounded calls. Output limits reject oversized results instead of silently dropping content.

Evidence-backed caller resolutions append local unknown history. They are recorded attestations, not independently verified semantic conclusions. Default analysis never writes repository files or executes tests.

# Graph schema and scope

The existing versioned MultiDiGraph persists artifact nodes and typed edges in graph_nodes/graph_edges. Nodes retain artifact, repository, parser and commit identities. Edges retain source/target, relation_type, method, provenance_type, resolution_status, revision, endpoint spans and content hashes. Static syntax, compiler references, declared links and heuristic candidates remain distinguishable; confidence is not calibrated probability.

Supported dependency traversal relations: CALLS, TESTS, IMPORTS, DEPENDS_ON, IMPLEMENTS, VALIDATES, CONSUMES_API and EXPOSES_API. CONTAINED_IN supports navigation but is excluded from impact traversal. Similarity trace recovery remains candidate retrieval rather than confirmed implementation.

`trace_impact` traverses reverse dependencies within the selected revision and returns the first deterministic shortest node path with the exact stored edges. Alternatives are not exhaustively enumerated; depth and output bounds are explicit. No-path does not prove unaffected behavior. `find_relationships` exposes provenance and endpoint source references. The existing investigation workflow compares two separate snapshot traversals.

This release does not infer assertion correctness, full dynamic dispatch or requirement implementation from graph reachability. Full Java/TypeScript compilation and Swift semantic resolution remain incomplete; C/C++ uses snapshot assumptions rather than a verified complete build configuration.

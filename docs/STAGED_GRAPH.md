# Bounded partial staged graph projection — 25 October 2026

Added investigation/staged_graph.py and scripts/audit_staged_graph.py. Graph construction
uses a disposable in-memory Store. Frozen artifacts, importer guards and original
application graphs remain unchanged. Each delivered edge retains the original typed
candidate relationship, both verified endpoint receipts, separate projection identity,
revision, parser identity, source policy, module fingerprints and partial coverage.
Parse-error artifacts cannot produce delivered edges. Unavailable endpoints remain
UNKNOWN_SOURCE_SUPPORT. Every result has empty findings; no missing-test or causal
impact conclusion is inferred. Pagination and withheld counts retain denominators.

Fresh checks: 308 full tests and six new fixtures pass (one existing dependency
warning). All 53 snapshot scopes projected: 1,885 incident candidates; the selected
first pages examined 1,172, returned 1,151 source-verified candidates and retained
21 withheld/unavailable edges. 713 candidates are outside selected pages. These are
bounded engineering observations, not accuracy or complete graph coverage. All 140
packet entries remain accounted for, including four without source references.

The source Store still has 29,647 artifacts and zero analysis_runs, graph_nodes,
graph_edges or tool_results. No fetches, subject execution, model calls, labels,
reviewer judgments, Windows checks or historical benchmark reruns were performed.
Both independent quality gates remain NOT_EVALUATED.

Next: separately versioned partial-aware report composition consuming the comparison,
inspection and graph outputs. Full staged report/API/UI integration, reviewed
registries and independent semantic/final evaluation remain incomplete.

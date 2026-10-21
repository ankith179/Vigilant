# VIGILANT knowledge graph

The graph is implemented and persisted. `knowledge_graph/graph.py` builds a
NetworkX MultiDiGraph from canonical artifacts at a particular commit. Database
tables `graph_nodes` and `graph_edges` retain commit and repository provenance;
the frontend's Knowledge Graph page reads the API's stored records.

| Relationship | Construction and scope |
| --- | --- |
| DEPENDS_ON | Reverse containment and recorded client-owner links |
| CALLS | Unambiguous parsed symbol call; same-file match preferred |
| TESTS | Parsed calls from test methods, or explicit declared baseline traces |
| IMPORTS | Unique module-path resolution for supported source imports |
| EXPOSES_API | Parsed route handler to its API artifact |
| CONSUMES_API | Unique matching literal HTTP method and route |
| Declared trace relations | Supplied baseline links retain their declared method |
| MODIFIES | Workflow persistence connects a commit node to changed artifacts using Git diff |

The main workflow builds both snapshots and traverses their combined graph for
impact candidates. By default it uses two hops and excludes reverse containment
edges during propagation to reduce broad file-to-symbol expansion. Each path is
saved as an explanation for investigating a candidate; it does not prove a
causal defect.

The graph uses static approximations. Dynamic dispatch, reflective calls,
nonliteral URLs and unresolved or ambiguous symbols may be missed. Heuristic
edge confidence values are not statistically calibrated probabilities. Similarity
trace recovery remains a candidate list and is not relabeled as proven IMPLEMENTS.

Controlled change experiments can supply baseline trace links. Such seeded
links must be disclosed in evaluation; recovering a known link after a mutation
does not independently demonstrate automatic trace discovery. Existing retrieval
experiments and graph reranking preserve the exact rankings and metrics needed to
check whether graph context helped on each dataset.

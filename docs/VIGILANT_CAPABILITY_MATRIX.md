# VIGILANT capability and verification matrix

This inventories implemented software-assurance capabilities and explicit exclusions. The current project-wide register is VIGILANT_MASTER_TASK_REGISTER.md; the source-backed REA inventory is REA_CAPABILITY_PARITY_MATRIX.md. Exact MIT-licensed reference files are retained under reports/master-audit-20261025/rea-source solely as audit evidence, with pinned upstream Git-blob checks. They are not application implementations. Presence of a schema or button alone is not counted as verified semantic capability.

| Capability | Status | Implementation / checks | Actual behavior | Limits / open work |
|---|---|---|---|---|
| Repository intake / snapshots | Existing, preserved | ingestion/service.py; ingestion/git.py; test_integration.py | Git/project import; immutable pinned commits; no subject execution | Native Windows not freshly tested |
| Python / Java / JS / TS extraction | Existing, partial semantics | ingestion/parsers.py; tests/test_pipeline.py | Syntax artifacts and conservative relationships | Full compiler/build resolution not established |
| C / C++ / Swift | Existing, bounded | tests/test_native_languages.py | Snapshot compiler references and Swift syntax | Complete project compilation/Swift semantic resolution incomplete |
| Change analysis | Existing, preserved | agents/workflow.py; change_analysis/diff.py | File/symbol/hash changes and separate base/head facts | Behavioral changes require interpretation |
| Traceability graph | Existing + exposed | knowledge_graph/graph.py; tests/test_investigation_tools.py | Typed edges, provenance and revision-scoped traversal | No causal proof or calibrated probabilities |
| Requirements and tests | Existing, preserved | traceability/; consistency/; tests/test_obligations.py | Candidate links, explicit reviewed obligations, no missing-test inference from unchanged tests | No complete semantic coverage proof |
| Repository exploration | Implemented | investigation/service.py; tests/test_investigation_tools.py | Scoped file/symbol paging and Git inventory gaps | 20,000-artifact / 20-million-character budget |
| Artifact inspection | Implemented | investigation/service.py; tests/test_investigation_tools.py | Bounded source excerpts, full artifact and quote checks against Git | Selected source only; common secret patterns withheld |
| Dependency navigation | Implemented | find_relationships / trace_impact; tests/test_investigation_tools.py | Typed edges and bounded candidate paths within one commit | Alternative paths not exhaustively enumerated |
| Retrieval / RAG | Existing + shared tools | rag/evidence.py; tests/test_audit_regressions.py | BM25/TF-IDF/embeddings/hybrid existing; shared BM25 evidence tool | No universal superiority or semantic proof |
| Bounded model interpretation | Existing, preserved | agents/evidence_first.py; tests/test_input_audit_hardening.py | Pair-preserving contexts; validated advisory response; no finding promotion | No new inference in this release |
| Retained evidence contracts | Implemented | investigation/service.py; tests/test_investigation_tools.py | Content identity, stored envelope and reverified source reuse | Local retention does not authenticate human review |
| Unknown registry | Implemented | unknown_revisions; tests/test_investigation_tools.py | Append history, source-linked resolution and expected-revision conflicts | Resolution is caller attestation, not semantic certification |
| Search inventory manifests | Implemented | consistency/search_inventory.py; tests/test_search_inventory.py | Pinned paths/object IDs, scoped exclusions and unknown regions | Enumeration validates boundary, not reviewer search quality |
| Investigation recipes | Implemented, deterministic | run_recipe; tests/test_investigation_tools.py | Five finite recipes with shared tools and visible stop reasons | No unconstrained autonomous loop |
| CLI | Implemented | vigilant.py; subprocess test in test_investigation_tools.py | Discovery, scoped tools, deterministic compare and MCP startup | Existing helper scripts retained; no shell execution tool |
| MCP | Implemented, tested subset | investigation/mcp.py; tests/test_investigation_tools.py | Stdio lifecycle, tool schemas, five prompts and retained resources | 2025-11-25 protocol; no HTTP transport or client certification |
| HTTP and UI | Implemented + existing | backend/app.py; frontend/src/InvestigationTools.jsx | Same service contracts; revision-scoped evidence/navigation | Local workspace authorization only |
| Grounded chat / saved reports | Existing, preserved | backend/report_chat.py; tests/test_audit_v2.py | Saved changes/findings/paths, scoped follow-ups and citations | General natural-language planning and patches remain incomplete |
| Continuous triggers | Existing, explicit | scripts/watch_repository.py | Configured repository watcher; no claim of automatic deployment | User must configure and run it |
| Independent 95% quality | Evaluator implemented; target unestablished | evaluation/assurance_gate.py; tests/test_assurance_95.py | Separate traceability/impact/consistency gates, source and pipeline binding | Independent reviewed final labels/predictions absent |
| Real-world retrieval measurement | Recomputed saved results | scripts/measure_quality.py; reports/final-95/measurement.json | 314 development cases; best Recall@10 85.11% | Not 95% or overall accuracy |
| Full-weight reinforcement learning | Not run | Preserved contextual-bandit experiments | Bandit negative result retained; no promotion | Reliable reviewed rewards, protocol and suitable compute missing |
| Hosted database integration | Not deployed | database/store.py; connected-account read-only inventory | SQLite preserved; PostgreSQL-compatible persistence exists | No projects found in either connected database account |
| Native binaries / runtime debugging / device inspection | Excluded from software-assurance release | Scope decision | No placeholder features or implied runtime evidence | Outside requirements-code-tests scope |
| General agent source patches | Not implemented | docs/IMPLEMENTATION_ROADMAP.md | Advisory test review retained | Reviewable code patch generation and execution remain open |
| Publication / final university submission | Drafts retained | submission/; docs/COMPLETION_STATUS_20261024.md | Earlier technical papers and thesis included | Institutional details, scientific review and final submission pending |

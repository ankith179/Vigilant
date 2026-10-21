# Architecture image → implementation coverage

Release: 16 October 2026. The reference image describes a broader target than the
implemented local research system. Alternative technologies shown in that image
are not all simultaneously installed. This matrix records the actual scope;
“complete package” means all source/data/documents for this implemented scope,
not every distributed production service in the picture.

| Image component | Implementation / location | Status and boundary |
| --- | --- | --- |
| GitHub / GitLab repositories | Git CLI import, `backend/app.py`, `ingestion/git.py` | Local import exercised; public HTTPS URLs supported; live GitLab clone not tested this release. |
| Requirements, docs, source and tests | `ingestion/parsers.py` and pinned input manifests | Repo-file extraction implemented. No authenticated issue/wiki connectors. |
| Python, Java, JavaScript, TypeScript | Python AST and Tree-sitter grammars | Parser regression tests pass. Other languages/dynamic dispatch have limited coverage. |
| REST endpoints / OpenAPI | Static route/call extraction, configuration artifacts | Dedicated OpenAPI semantic validation is not implemented. |
| Dependencies | Imports and structural references | Not a package vulnerability scanner or full build/dependency resolver. |
| Benchmark datasets | LiSSA SMOS/iTrust/eTour, RTMX, SAFA; `data/source-manifest.json` | Pinned datasets and actual saved evaluations included. Dronology evaluation not implemented. |
| Cloning / AST / normalization | `ingestion/` | Implemented with immutable commit/content identities. |
| Chunking / embeddings | `retrieval/index.py`, `data/models.json` | MiniLM optional; install model dependencies/weights separately. |
| Relational store | `database/store.py` | SQLite tested. SQLAlchemy's PostgreSQL-compatible shape is not a tested PostgreSQL deployment. |
| Vector store | NumPy vectors and SQLite embedding cache | Local alternative implemented. FAISS/Chroma/pgvector services absent. |
| Knowledge graph | `knowledge_graph/graph.py`, persisted graph tables | NetworkX alternative implemented. Neo4j absent. |
| Hybrid RAG / reranking | `retrieval/`, `rag/`, `scripts/run_rag_trace.py` | Implemented and frozen results audited; mixed accuracy. API evidence search is explicitly BM25. |
| Project context and evidence | `rag/evidence.py`, canonical IDs/hashes | Exact quote/range/hash checks implemented; semantic entailment unverified. |
| Multi-agent layer | `agents/workflow.py` | Fixed bounded role/tool orchestration; no autonomous agent swarm. |
| Local/on-prem LLM | Qwen2.5-1.5B; optional Ollama adapter | Historical Qwen study included; new model execution not rerun. Llama/Mistral/CodeLlama not bundled/evaluated. |
| OmniRoute | `llm/omniroute.py`, launchers/evaluator | Contract tests pass. Live gateway/account and comparative scores NOT RUN. |
| Structured prompts/output | Provider schemas, citation validator | Implemented; valid format/citations do not guarantee correct reasoning. |
| FastAPI resource routes | `backend/app.py` | Projects/repositories/artifacts/changes/traceability/rag/agents/consistency/evaluation/reports present. |
| Authentication | Optional workspace Bearer token | API tests pass. No per-user login, roles, tenancy or account management. |
| Dashboard, graph, evidence and reports | `frontend/src/`, 13 views | Browser checks pass. React JSX is used, not a TypeScript frontend. |
| Settings | Workspace token; provider dropdown; environment config | No standalone comprehensive administrative settings page. |
| Task queue / workers | SQLite job records + one bounded thread | Queued-job recovery tested. No Celery/RQ/Redis distributed broker or multiworker support. |
| Scheduler / change monitoring | `scripts/watch_repository.py` | Local polling and atomic state; repo mismatch tested. No remote fetch, durable distributed scheduler or exactly-once guarantee. |
| Webhooks | None | NOT IMPLEMENTED. Polling/manual import are the supplied triggers. |
| Trace / impact / consistency outputs | Persisted candidate links, paths, rules, model decision | Implemented; retain uncertainty and evidence limitations. |
| JSON / CSV / PDF reports | JSON, findings CSV, printable HTML | JSON/CSV/HTML tested. PDF requires browser print; no native PDF endpoint. Research PDFs are separately bundled. |
| Evaluation metrics | `evaluation/`, `experiments/`, audit scripts | 23 method rows / 1,484 query metric rows / 251 generations rechecked without new inference. |
| Docker / Compose | `Dockerfile`, `compose.yaml` | Core-only recipe supplied; build/runtime NOT VERIFIED because Docker unavailable. |
| CI | `.github/workflows/verify.yml` | Recipe supplied; remote CI NOT RUN. Local equivalent checks pass. |
| Nginx / HTTPS / public hosting | None | NOT IMPLEMENTED. Default application binds to localhost. |
| Prometheus / Grafana | `/api/metrics` exposes job gauges | Endpoint tested; Prometheus server, dashboards and alerting not supplied. |
| ELK / Loki logs | Console logs and persisted tool/job error records | No external log aggregation service. |

## Acceptance and remaining work

The local core is executable and validated within the documented Linux profile.
Read `reports/codebase-20261016/VERIFICATION.md` for actual checks and
`docs/RUN_AND_CODE_GUIDE.md` for installation and module explanations.

A literal production implementation of every image box remains unfinished: hosted
identity/RBAC, external connectors, webhooks, distributed jobs, observability stack,
reverse proxy and production deployment need separate implementation and validation.
Windows execution, live free-route OmniRoute evaluation and independent accuracy
labels also remain unverified. None is marked completed merely because a recipe,
interface or a diagram mentions it.

# Executed pipeline contracts

This map describes the existing implementation. A completed software stage does
not imply that its predictions are correct or that a model improves a baseline.
The authoritative measurement records are immutable files under `experiments/`.

| Stage and source | Input | Output and verification |
| --- | --- | --- |
| Git acquisition: `ingestion/git.py`, `ingestion/service.py` | Local Git repository, project ID and revision | Resolved commit, text snapshot, stored repository/commit records; Git failures remain errors |
| Parsing: `ingestion/parsers.py` | Repository-relative file path and snapshot text | Canonical file, symbol, requirement, test, API and frontend artifacts; parse failures retained as metadata |
| Canonical model: `ingestion/models.py` | Project, repository, commit, path, kind, symbol, content, line range | Validated `Artifact`; identity separates logical artifact from commit/content version; relative paths, ordered lines and content hash checked |
| Retrieval: `retrieval/index.py` | Target text collection and query | TF-IDF, BM25, MiniLM cosine scores, or BM25/embedding reciprocal-rank fusion with k=60; ranked results and retrieval method |
| Trace recovery: `traceability/recovery.py` | Requirement and target artifacts, optional encoder | Bounded top-three candidates per requirement; lexical fallback threshold 0.12; `RELATED_TO`, proposed relation and `CANDIDATE_REQUIRES_REVIEW`; confidence is null |
| Graph: `knowledge_graph/graph.py` | Snapshot artifacts and optional declared links | Directed structural graph, typed persisted nodes/edges, evidence and provenance; static approximations are disclosed |
| Change detection: `change_analysis/diff.py` | Base/head revisions and both artifact snapshots | Git changes and artifact changes resolved through identity/content hashes |
| Impact: `knowledge_graph/graph.py` | Base/head graph composition and changed artifact seeds | Bounded paths to candidate affected artifacts; paths explain selection but do not prove a defect |
| Evidence retrieval: `rag/evidence.py` | Query, current artifacts, graph/seeds and optional encoder | Lexical or hybrid excerpts plus graph/changed-artifact context under an excerpt budget |
| Evidence verification: `rag/evidence.py` | Evidence entries and versioned artifacts | Missing-version or quote/range/hash errors; pipeline stops on mismatches |
| Rules: `consistency/rules.py` | Changed artifacts, both snapshots and base relationships | Conservative review findings, affected IDs and attached endpoint evidence; model decisions remain separate |
| Model provider: `llm/providers.py` | Query, verified excerpts, selected provider | Raw response, parsed decision, usage, latency and validation errors; insufficient/invalid evidence yields uncertainty |
| Investigation: `agents/workflow.py` | Store, repository, base/head, project, model and semantic flag | Twelve staged tool outcomes in the executed demonstration, changes, impact paths, trace candidates, evidence, rule findings and model decision |
| Persistence: `database/store.py` | Canonical/versioned records and generated reports | SQLite-backed project, artifact, graph, evidence, finding, experiment and analysis records |
| Presentation: `backend/app.py`, `frontend/src/main.jsx` | Stored records, filters and user actions | Local API and frontend pages; dashboard data comes from persisted records |

## Identity and evidence

`artifact_id` hashes project, repository, relative path, artifact type and symbol.
`content_hash` hashes content; `commit_id` identifies the snapshot. A symbol rename
or path change can therefore require explicit change matching rather than being
the same logical identity. The model is not a universal rename oracle.

An evidence entry includes `evidence_id`, `artifact_id`, repository/project,
file, start/end lines, commit, content hash, exact quote, retrieval method and
score. `verify()` checks the quoted slice against the identified artifact version.
This establishes source fidelity, not semantic support for a conclusion.

The workflow's `Decision` requires a supported status label, a numeric confidence
in [0,1], evidence IDs, affected artifact IDs, reason, consistency label and
uncertainty text. Decision and consistency labels must agree. Non-UNCERTAIN
decisions require nonzero confidence and evidence IDs. Numeric model confidence
is not calibrated probability.

## RAG experiment contract

`scripts/run_rag_trace.py` uses a separate candidate-classification schema. Input
is a linked requirement prefix and the first five hybrid-ranked target prefixes.
Aliases E0 and A1–A5 identify supplied evidence. Output assigns SUPPORTED,
UNSUPPORTED or UNCERTAIN to every candidate and supplies citation IDs and a short
reason. Only SUPPORTED candidates move forward; every other full-ranking entry
keeps its previous relative order. The method cannot improve Recall@5 or @10.

Each saved observation includes the exact prompt, evidence aliases, raw output,
parsed decision, decoding/model identity, usage, timing and input fingerprint.
`audit_rag_observations.py` independently checks source prefixes, fingerprints,
raw/parsed agreement and the full schema. `audit_results.py` recomputes ranking
metrics from complete saved rankings. Neither audit annotates semantic entailment.

A completion pointer is written only after every linked query in a dataset has
an actual generated observation. A no-inference model-loading failure stops the
run and is excluded from effectiveness scoring. A bounded stop returns exit 75;
it does not create a completed dataset. `summarize_rag.py` requires all four
completed and audited datasets before writing the paired comparison reports.

## Local API contract

| Request | Behavior |
| --- | --- |
| `GET /api/health`, `/api/stats` | Local server status and stored table counts |
| `POST /api/projects` | Create a named project |
| `POST /api/repositories/import` | Import an allowed local data-directory path or a public HTTPS GitHub URL, resolve revision, extract and persist artifacts/graph/candidates |
| `POST /api/analysis/run` | Queue a bounded analysis on the single local worker; return job ID |
| `GET /api/reports/{run_id}` | Retrieve a persisted analysis or job record |
| `GET /api/artifacts/{artifact_id}` | Retrieve a particular repository and commit version |
| `GET /api/graph` | Retrieve a bounded graph for a repository and commit, including truncation flag |
| Listing endpoints | Projects, repositories, commits, artifacts, traceability, changes, evidence, findings, reports, experiments and agents; filter by scope with offset/limit |

This is a local research application. Public multiuser deployment, authentication,
authorization and production operations have not been validated. Hosted-provider
interfaces are available but the reported experiments use the pinned local model.

## Existing efficiency controls

The implementation caches embeddings by normalized content and model revision,
limits chunking and batch size, reuses exact fingerprint-matched generations,
bounds trace candidates and graph hops, keeps one model worker, stores immutable
experiment records, and skips completed ledger stages. These controls reduce
repeat work. No universal speedup claim or completed performance optimization
study follows from them; changes to scientific settings require a new protocol.

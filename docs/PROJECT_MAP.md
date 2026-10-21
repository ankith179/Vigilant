# Where everything is saved

The `VIGILANT/` directory is the project root in the unified ZIP. Install its
contents in `C:\Users\Ankith\Downloads\Code- Vigilant` using the supplied Windows
installer, or choose another folder. This web session has not written to that
Windows drive.

| Area | Location |
| --- | --- |
| Current task list and completion records | `PROJECT_STATE.json` |
| Restart and recovery instructions | `RESUME.md`, `AGENTS.md` |
| Actual completion scope and blockers | `docs/FINAL_STATUS.md` |
| Git import, parsers, canonical artifacts | `ingestion/` |
| Trace candidate recovery | `traceability/` |
| TF-IDF, BM25, embeddings and fusion | `retrieval/` |
| Knowledge graph and impact traversal | `knowledge_graph/` |
| Grounded evidence and quote verification | `rag/` |
| Model providers and response validation | `llm/` |
| Bounded investigation workflow | `agents/` |
| Git change detection and conservative findings | `change_analysis/`, `consistency/` |
| Local API and application | `backend/`, `frontend/` |
| Persistence and consistent database backups | `database/`, `data/snapshots/` |
| Pinned raw datasets, repositories, prepared data | `data/raw/`, `data/repos/`, `data/prepared/` |
| Controlled change commits and contracts | `data/changebench/` |
| Immutable measured experiment runs | `experiments/` |
| Human-readable results, plots and logs | `reports/` |
| Setup, execution, evaluation and checkpoint commands | `scripts/` |
| Parser, Git, evidence, API and integration tests | `tests/` |

Thesis, separate survey/research papers and the presentation remain pending until
their ledger entries point to actual completed drafts. Model weights and installed
dependencies are downloaded from pinned specifications rather than bundled into
the archive. New output belongs under this same root; do not create a replacement
project or scatter competing copies across unrelated folders.

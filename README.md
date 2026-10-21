# VIGILANT

Research software for change-aware traceability, structural knowledge graphs, evidence retrieval and bounded consistency investigations.

Read [completion status](docs/FINAL_STATUS.md), the [checklist](docs/COMPLETION_CHECKLIST.md), [measured results](reports/results/RESULTS.md) and [reproduction instructions](docs/REPRODUCIBILITY.md). The frozen evaluation contains 251 actual RAG generations, 60 consistency-ablation calls and 12 authored change scenarios. Results are mixed; the local model did not improve consistency classification. The M.Tech submission is not yet final.

Start with [START_HERE.md](START_HERE.md) for Windows installation and the saved demonstration.

## Resume existing work

Read AGENTS.md, PROJECT_STATE.json and RESUME.md. Preserve completed runs. After installing pinned dependencies if absent:

```
python scripts/restore_checkpoint.py
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Windows scripts target C:\Users\Ankith\Downloads\Code- Vigilant; this hosted session has not written to or tested that computer.

## Check results without new inference

```
python scripts/continue_project.py --status
python scripts/audit_rag_observations.py
python scripts/audit_results.py
python scripts/summarize_rag.py
python scripts/evaluate.py
```

The package preserves source, raw/prepared datasets, knowledge graph/database snapshots, results and documentation. Nested clone metadata, machine-local caches and installed dependencies are excluded; pinned weights and dependencies restore separately. See [project map](docs/PROJECT_MAP.md), [contracts](docs/INTERFACE_CONTRACTS.md), [graph](docs/KNOWLEDGE_GRAPH.md), [demo](docs/DEMO_RECORD.md) and [limits](docs/EVALUATION_LIMITATIONS.md).

## Submission drafts

The thesis, separate research and targeted survey papers, and demonstration deck are in `submission/output/`. See [draft build instructions](submission/BUILD.md). Linux browser acceptance has passed across all 13 pages. Actual Windows execution remains unverified. Independent review and institutional completion remain necessary.

## OmniRoute

An explicit free-route adapter, Windows launchers and bounded evaluation runner are included. See [free setup](docs/OMNIROUTE_FREE.md). Contract tests pass; live provider inference and accuracy remain NOT RUN until an eligible free account is connected. Existing measurements are preserved.

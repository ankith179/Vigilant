# VIGILANT continuity rules

Current environment (2026-10-21): native Windows in the extracted VIGILANT
directory, approximately 32 GB RAM and RTX 3050 OEM 8 GB. Continue in this
directory; the old Ankith destination and hosted Linux paths below are historical.
Use `.venv/Scripts/python.exe -X utf8`. Local-only Ollama and model weights live
under `.runtime/`, excluded from archives. Start the service with
`Start-Ollama-Local.ps1`. New diagnostic results are isolated in
`experiments/local-model-comparison/windows-20261021`. Preserve all historical
snapshots when packaging (`scripts/checkpoint.py --preserve-snapshots`).
Read `reports/windows-20261021/VERIFICATION.md` alongside the checkpoint for
native Windows evidence and the actual model outcomes.

Read PROJECT_STATE.json, RESUME.md and docs/FINAL_STATUS.md first. Continue the next unfinished authorized item. Never replace the project with a new scaffold, erase prior results or rerun completed experiments without a concrete reason.

All authored work belongs under this VIGILANT root. The user's requested Windows destination is C:\Users\Ankith\Downloads\Code- Vigilant. This hosted Linux session cannot write to that drive. Deliver a complete package and installation/resume scripts. Do not claim a Windows write or Windows test without evidence.

The knowledge graph is essential: preserve knowledge_graph/graph.py, persisted graph nodes/edges, snapshot provenance and the frontend graph page. Structural edges are evidence candidates. Recovered similarity links remain candidates and must not silently become true IMPLEMENTS relationships.

Use actual saved experiments and their ground-truth scope. Failed model loading is not an LLM accuracy result. Missing runs remain NOT RUN. Citation validity is not semantic entailment. Controlled mutation oracles are authored and incomplete. Do not assert independent accuracy, model superiority, statistical significance, novelty priority or publication indexing without appropriate evidence.

Read the active lease and check whether a worker is still running before starting another run. If the lease is fresh and another worker owns it, defer. Refresh the lease after meaningful work. A stale lease is not proof that a process died; check process/run status. Use one model process at a time on the 8 GiB hosted runtime. Do not spawn subagents unless separately authorized.

On this hosted runtime, use /tmp/vigilant-runtime for live SQLite databases and /tmp/vigilant-models for model weights. VIGILANT_LLM_PATH can point to the completed model in /tmp. Validate safetensor files before inference. Large files copied into synchronized scratch can be truncated if observed during a copy. Stage archives, validate them, then atomically install the completed file. Use SQLite backup instead of copying live WAL files.

After every completed checklist item, update PROJECT_STATE.json and RESUME.md, save source/results through the persistent file workflow, and retain file identities/version history. Before ending, make an integrity-checked VIGILANT-project.zip and refresh the standalone RESUME.md. Automated continuation must use these records rather than conversation memory alone.

Keep external blockers explicit: independent annotation, institutional formatting and author details, venue selection, paid cloud access and publication submission. Do not send messages to others, spend money or submit papers without separate authorization.

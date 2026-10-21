# Latest checkpoint - native Windows, 21 October 2026

Setup and requested local evaluation are complete in this extracted project. The app is running at http://127.0.0.1:8000. After a reboot use Start-Ollama-Local.ps1, then Start-VIGILANT-Local.ps1 in another terminal.

75 tests, production build and Windows browser acceptance pass. All three local Ollama models completed 12 authored diagnostic cases each: Qwen3 8B 0/12, Qwen2.5 Coder 14B 1/12, Qwen3 14B 0/12. Citation validation failures count as errors. No independent accuracy or >75% claim is supported.

All 423 historical experiment/snapshot files are unchanged. New outputs: experiments/local-model-comparison/windows-20261021. Run-Local-Models.ps1 reuses this exact directory; the verified resume made zero new calls. Do not rerun completed generations. Detailed evidence: reports/windows-20261021/VERIFICATION.md. Runtime/weights under .runtime are excluded from portable archives. Independent annotation and review remain external requirements.

---

## Latest extension — 2026-10-13

OmniRoute support is implemented and tested (53 tests; frontend build). No local gateway or provider account is connected here. Live inference, free eligibility and revised accuracy are NOT RUN. Follow docs/OMNIROUTE_FREE.md; default five-call legacy-prompt evaluator preserves original results and excludes provider failures. Free-only operation requires a free-eligible provider account and no paid gateway fallback. Do not resume old Qwen runs. Prior 2026-10-12 browser evidence predates the new provider selector.

# VIGILANT recovery and continuation

Checkpoint: 2026-10-12 UTC. Continue this project without rebuilding it. Read AGENTS.md, PROJECT_STATE.json, docs/FINAL_STATUS.md and actual experiment records. Honor the active lease and check processes before starting jobs.

## Completed evaluation

All 251 linked-query RAG generations are complete: SMOS 67, iTrust 105, eTour English 57 and RTMX module-valid 22. Independent observation audits passed for all 251. Independent arithmetic recomputation passed for 23 method rows and 1484 query rows. A zero-new-call continuation skipped all four completed datasets. Do not rerun these model calls.

| Dataset | Hybrid MAP | Hybrid + RAG MAP | Immutable result |
| --- | ---: | ---: | --- |
| SMOS | 0.3025565167 | 0.3060623896 | experiments/retrieval/20261007T104905-4064b602/results.json |
| iTrust | 0.3068281472 | 0.3043088728 | experiments/retrieval/20261007T163255-0dfbb833/results.json |
| eTour_en | 0.4405532200 | 0.4426837779 | experiments/retrieval/20261007T171402-64fa98d8/results.json |
| RTMX-module-valid | 0.7515151515 | 0.6984848485 | experiments/retrieval/20261007T210208-3f0803cc/results.json |

Results are mixed, with no general superiority or significance claim. The model reviews only five candidates; Recall@5/@10 cannot change. RTMX has seven candidate modules, so Recall@10 necessarily equals one. Full schema validity is 1.0; independent semantic grounding and hallucination rate remain unmeasured.

Final measured tables and inspected scientific plots are in reports/results/. Paired query deltas and dataset reports are in reports/rag/. Derived reports can be regenerated without inference:

```
python scripts/audit_rag_observations.py
python scripts/audit_results.py
python scripts/summarize_rag.py
python scripts/evaluate.py
```

## Other completed work

- Canonical/versioned artifacts, Git extraction, Python/Java/JS/TS parsers, bounded trace candidates, structural knowledge graph, provider abstraction, evidence verification, conservative rules and bounded tool investigation.
- Pinned datasets; actual TF-IDF, BM25, MiniLM, hybrid and graph comparisons. The learned ranker was rejected by its validation rule.
- Twelve controlled Git scenarios with exact saved commits and restored worktrees. Labels are authored and affected sets incomplete. Outside-oracle predictions are unjudged, not verified false positives.
- SAFA artifact-tree evolution, not independently labelled code consistency.
- Sixty genuine calls: experiments/ablation/20261006T194639-30694b4d/results.json. Every variant is 100% UNCERTAIN and agrees with 25% of authored labels, equal to always-UNCERTAIN. Preserve the negative result, five citation failures, excluded loading-only failures and review packets.
- Full local-model investigation: experiments/pipeline/20261006T195007-e56e6b8d/results.json. Twelve tools, 11 changed records, 33 impact candidates, 24 verified excerpts and model UNCERTAIN. Fifteen rule findings concern a shared route-renaming cause, not 15 independent confirmed defects.
- Thirty-four passed tests, frontend production build, dependency manifests, Windows scripts and immutable experiment records.

Preserve knowledge_graph/graph.py, nodes/edges and commit MODIFIES relationships in snapshots. Similarity candidates must not become proven IMPLEMENTS edges. See docs/PROJECT_MAP.md, docs/INTERFACE_CONTRACTS.md, docs/COMPLETION_CHECKLIST.md and docs/EVALUATION_LIMITATIONS.md.

## Next unfinished work

The implementation, frozen model experiments, result tables, thesis draft, separate paper drafts and demonstration deck are complete for their stated scope. Do not repeat inference or rewrite completed drafts.

1. DONE: Chromium 153 browser checks passed across all 13 pages on 2026-10-12. Record: `reports/frontend/2026-10-12T06-01-24-831Z/validation.json`. Do not repeat browser checks unless implementation changes. Dashboard includes all 14 saved experiment runs.
2. Actual Windows execution needs access to the user computer. This hosted session cannot write to the requested Windows folder.
3. Independent labels/semantic review, institution/author details, full-text survey expansion, external plagiarism/scientific review and venue selection remain unresolved.
4. Refresh the source and complete package after any genuine change. Existing graph, raw outputs, failures and immutable experiment runs must survive.

## Restore only missing files

Prefer VIGILANT-project.zip: libfile_62832ff34ccc8191947359933746ec53. Overlay a newer source checkpoint if one exists, preserving active work. Fallback source: libfile_f68b012833688191a771b623813ccd24. Data: libfile_b8166c70bb908191adf712a38cba56c5. Check manifests and dates. This resume: libfile_9a7493f12bb88191bdbe5d5abade3499. Separate state: libfile_2929bdde983081919b1763d10fd6e043.

Reinstall dependencies only if absent. Repair relocated paths with scripts/restore_checkpoint.py. Use scripts/restore_changebench.py only for missing worktrees, never to overwrite a mismatch. Weights, .venv and node_modules are reproducible dependencies excluded from archives.

A reset may remove .venv/bin/python while installed packages remain; restore its missing link from CODEX_PRIMARY_RUNTIME_PYTHON. Use /tmp/vigilant-runtime for live SQLite and SQLite backup for snapshot recovery; set VIGILANT_DB, VIGILANT_BENCH_DB and VIGILANT_EMBEDDING_CACHE accordingly. Never copy a live main database without its WAL.

If a new protocol explicitly requires inference, restore pinned weights to /tmp/vigilant-models with scripts/download_models.py --staging-only and VIGILANT_MODEL_STAGING. Set VIGILANT_LLM_PATH/VIGILANT_EMBEDDING_PATH, validate safetensors and use only one model process. Do not restore models merely to regenerate completed tables.

scripts/checkpoint.py stages and validates archives. scripts/package_project.py produces one combined project. Save after meaningful progress and before stopping because processes and temporary files may disappear. Release the lease on normal stop.

## Windows and external requirements

Requested destination: C:\Users\Ankith\Downloads\Code- Vigilant. This session cannot write there. VIGILANT-project.zip and Install-VIGILANT.ps1 (libfile_977a69c7876881918a0239f3195175a1) target that folder without overwriting existing content. Windows execution is unverified.

Independent labels/semantic review, author/institution/supervisor details, institutional formatting, external plagiarism review, venue selection and indexing verification remain unresolved. No spending, external messages, publication or submission. Keep the existing continuation task; do not create duplicates or promise exact quota-reset restarts. Historical user-reported scores use different populations and must not be pooled with reproduced results.

## Completed submission drafts

- `submission/output/Thesis-Draft.pdf`: 27 A4 pages covering the requested topics, with actual tables, figures, references and reproduction appendix.
- `submission/output/Research-Paper-Draft.pdf`: four IEEE-format pages, mixed/negative results and evidence limitations.
- `submission/output/Survey-Paper-Draft.pdf`: four IEEE-format pages, targeted literature matrix and taxonomy. Full-text/systematic-review coverage is not claimed.
- `submission/output/VIGILANT-Demonstration.pptx`: 14 editable slides with measured charts/tables, recorded graph relationships and API-change evidence. All slides rendered and visually reviewed. Native PowerPoint and live browser execution remain unverified.

Editable templates/builders and source provenance are under `submission/`, `scripts/build_thesis.py`, `scripts/build_papers.py`, `scripts/build_demo_deck.mjs` and `reports/submission/`. The deck builder needs the bundled artifact-tool runtime and RUNTIME_NODE/RUNTIME_NODE_MODULES/RUNTIME_BIN_DIR/RUNTIME_PYTHON variables; the PPTX can be edited directly. Do not rebuild from a scaffold.

Latest browser validation: `reports/frontend/2026-10-12T06-01-24-831Z/validation.json` — PASSED. Graph, evidence export, isolated deterministic investigation and mobile layout checked. Old browser-blocker notes in dated manuscripts/deck are superseded by this release record. Native PowerPoint and Windows execution remain unverified.

## Research paper update — 2026-10-14

The requested exact-title research paper by Ankith Singh is complete for technical review: `submission/research-20261014/VIGILANT-Research-Paper.pdf`, five US Letter pages using official IEEEtran and embedded Times New Roman. Editable LaTeX, two vector figures, two tables, frozen data, 14 references and verification report accompany it. Prior four-page drafts are preserved. No inference was rerun. Affiliation/email, independent review, similarity checks and PDF eXpress remain pending. OmniRoute live evaluation remains NOT RUN. See the new paper directory's README and VERIFICATION.md.

## Review revision and Word deliverable — 2026-10-16

Latest paper: `submission/research-20261016/`, with five-page `VIGILANT-Research-Paper.pdf` and editable `VIGILANT-Research-Paper.docx`. Both were rendered and all pages inspected. Review response, supplementary bootstrap/class metrics, self-contained reanalysis inputs, hashes, blank annotation worksheet and controlled evaluation protocol are included. No new inference was run; 418 historical experiment files match the preceding saved release. Original October 14 paper is preserved.

Consistency detection remains unresolved: all 60 raw outputs are uncertain with confidence zero; macro-F1 is 0.10 and non-uncertain coverage 0%. Additional analysis does not establish a superior model. Independent labels/no-link negatives, controlled component comparison, longitudinal validation, live OmniRoute evaluation, similarity checks and PDF eXpress remain pending. The supplied follow-up protocol is NOT EXECUTED. Do not repeat completed deterministic inference or invent annotations.

## Updated codebase — 2026-10-16

The latest local application release passes 62 tests, the production frontend build
and all 13 browser pages, including JSON/CSV/HTML report exports, graph/evidence,
free OmniRoute selector, settings, a new isolated deterministic investigation and
mobile layout. Queue recovery, reference pinning, immutable snapshot restore,
free-only provider selection and watcher state are covered by regression checks.

Start with `docs/RUN_AND_CODE_GUIDE.md`. Architecture mapping and missing production
services: `docs/ARCHITECTURE_COVERAGE.md`. Exact release verification:
`reports/codebase-20261016/VERIFICATION.md`. All 418 original experiment files are
unchanged; 23 method rows/1,484 query rows and 251 RAG observations passed audits
without new inference. Historical RAG audit requires the archived provider source
argument documented in the guide.

Native Windows, Docker/remote CI and live OmniRoute remain NOT VERIFIED/NOT RUN.
Distributed jobs, webhooks, RBAC and the external observability stack are absent.
The supplied full package is complete for the documented local scope. It is not a
claim of full production architecture or high model accuracy; the saved local
consistency model remains all-UNCERTAIN. Latest paper Word/PDF remains preserved.

## Local models and evidence update — 2026-10-17

Added Qwen3 8B, Qwen2.5 Coder 14B and Qwen3 14B local Ollama selection for a 32 GB PC, neutral schema prompts, paired changed-hunk excerpts, and a finite resumable comparison. See `docs/LOCAL_MODELS_32GB.md`. Run `.\Run-Local-Models.ps1 -DownloadModels` after setup and starting Ollama. This hosted environment has no Ollama runtime: new inference and >75% accuracy are NOT ESTABLISHED. Existing 25% authored-label agreement is unchanged. Independent held-out labels remain required.

74 tests and the production build pass. Chromium acceptance passes all 13 pages including model selection and deterministic end-to-end investigation. All 418 historical experiment files and three snapshot databases are unchanged; historical metric/RAG audits pass. Details: `reports/accuracy-20261017/VERIFICATION.md`. Windows and actual 32 GB hardware execution are unverified.

Graphify was unavailable. `handoff/graphify/` contains the project brief, real snapshot JSON/CSV/GraphML (2,134 nodes, 3,993 edges) and reproduction details. Native Graphify import is unverified.

Existing hourly continuation was enabled with bounded calls, exact resume, lease protection and a pause when only external blockers remain. It cannot run the user's Windows PC. Do not rerun completed historical experiments. Next scientific step: run the supplied local comparison, inspect errors, collect independent labels, select on validation, and evaluate one frozen model/prompt on held-out data.

## Runtime installation attempt — 2026-10-17

Ollama 0.40.5 was installed temporarily and its loopback version endpoint responded. Cloud inference was disabled and only one server was used. Qwen3 8B download failed with `redirect target not allowed` because the Cloudflare R2 storage hostname could not be resolved/reached through the available network. No new model inference ran; scores remain unmeasured. The host has an 8 GiB memory limit and no GPU; 14B downloads were not attempted. The temporary server was stopped. Weights/runtime binaries are reproducible dependencies and are not bundled.

Continuation is PAUSED until a usable model/weights connection or independently annotated data is supplied. No completed tests or historical inference were repeated. See `reports/runtime-20261017/VERIFICATION.md` and `session.json`.

Next bounded Windows commands, after existing setup and starting Ollama, from the VIGILANT folder:

```powershell
ollama pull qwen3:8b
.\.venv\Scripts\python.exe scripts/evaluate_local_models.py --models qwen3:8b --max-calls 6
```

Repeat the same bounded command to resume matching fingerprints. Once the runtime is available, compare candidates on validation, freeze one model and prompt, and test using independently reviewed held-out labels. Authored diagnostic scores cannot verify >75% independent accuracy. Native Windows access and independent annotations remain external requirements.

## Native Windows continuation - 2026-10-21

Working in the extracted project on the user PC. Dependencies and frontend installed. 74 tests and browser acceptance pass. Windows restore fixes applied. Ollama 0.40.7 running with cloud disabled; local model downloads/evaluation in progress. See reports/windows-20261021. Historical files have a pre-work SHA-256 manifest.

Qwen3 8B completed 12/12 native Windows diagnostic generations. All failed output/citation validation and count as errors (0% diagnostic accuracy). Qwen2.5 Coder 14B evaluation is running next. No original inference was repeated.

Qwen2.5 Coder 14B also completed 12/12 calls. Qwen3 14B is the final candidate running; the combined evaluator reuses completed models by exact fingerprint.

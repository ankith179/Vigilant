# Native Windows update - native Windows, 22 October 2026

The current Windows working tree includes the reliability audit and a bounded,
read-only repository/snapshot chat assistant. It uses verified retrieval, can call
an explicitly selected provider, and identifies semantic citation support as
unverified. Conversation history is session-only. The Agent Investigation page
remains a separate record view.

The inferred-edge rule now downgrades a lost heuristic graph edge to
`POTENTIAL_INCONSISTENCY`; `BROKEN_TRACE` is reserved for explicitly declared
relationships. Eighty-eight tests, production build, and mutation-enabled browser
acceptance (including chat and 390px mobile layout) pass. Dataset, metric and RAG
audits are recorded under `reports/windows-20261022/`. Two separate 12-call local
diagnostic comparisons are also preserved; neither establishes independent accuracy.

Accuracy remains unestablished: original best saved model score is 1/12; follow-ups
scored 2/12 and 4/12. Rules-only agreement is 11/12 on the same authored development
cases and is not held-out accuracy. Independent labels, semantic evidence review,
and C++/Swift adapters remain unfinished. See `reports/windows-20261022/AUDIT.md`.

---

# Prior native Windows update - 21 October 2026

Setup and requested local evaluation are complete in this extracted project. The app is running at http://127.0.0.1:8000. After a reboot use Start-Ollama-Local.ps1, then Start-VIGILANT-Local.ps1 in another terminal.

75 tests, production build and Windows browser acceptance pass. All three local Ollama models completed 12 authored diagnostic cases each: Qwen3 8B 0/12, Qwen2.5 Coder 14B 1/12, Qwen3 14B 0/12. Citation validation failures count as errors. No independent accuracy or >75% claim is supported.

All 423 historical experiment/snapshot files are unchanged. New outputs: experiments/local-model-comparison/windows-20261021. Run-Local-Models.ps1 reuses this exact directory; the verified resume made zero new calls. Do not rerun completed generations. Detailed evidence: reports/windows-20261021/VERIFICATION.md. Runtime/weights under .runtime are excluded from portable archives. Independent annotation and review remain external requirements.

---

# VIGILANT research completion status

The implementation and frozen experiments are complete for their stated scope. The overall M.Tech submission is **not complete**. The thesis technical draft (27 pages), separate IEEE research and targeted survey drafts (four pages each), and 14-slide demonstration deck are complete. Linux browser validation is complete. Windows execution, independent review and institutional details remain unresolved.

## Verified work

- Git ingestion, hashed/versioned artifacts, Python/Java/JS/TS extraction, tests/APIs/frontend relationships, recorded parser limitations and bounded trace candidates.
- Pinned real embeddings, lexical/hybrid/graph experiments and validation-based ranker rejection.
- Persisted knowledge graph, structural edges and commit MODIFIES relationships.
- Twelve controlled Git scenarios and SAFA evolution, with authored/incomplete oracle scope disclosed.
- All 251 actual RAG generations across four datasets; provenance/schema audits passed. Arithmetic audits passed for 23 method rows and 1484 query rows. A resume check skipped all four completed datasets.
- Sixty-call consistency ablation: all variants 100% UNCERTAIN, 25% authored-label agreement, equal to always-UNCERTAIN. No classification improvement established.
- Full local-model investigation with 12 tools and 24 verified excerpts; model UNCERTAIN. Fifteen rule findings share a route-renaming cause.
- Sixty-two passing tests and a real-data frontend production build.
- Chromium browser acceptance passed across all 13 pages, with graph navigation, evidence export, error recovery, isolated UI investigation and mobile layout checks. The 22 October run additionally validates repository chat and its mobile layout.
- Complete measured tables and visually inspected scientific plots, raw outputs and reproducibility records.
- Reviewable thesis and separate paper drafts with verified source references and actual mixed/negative findings.
- Fourteen-slide demonstration deck with editable charts/tables, graph relationships and the recorded API-change evidence.

## Actual RAG comparison

| Dataset | Hybrid MAP | Hybrid + RAG MAP |
| --- | ---: | ---: |
| SMOS | 0.302557 | 0.306062 |
| iTrust | 0.306828 | 0.304309 |
| eTour English | 0.440553 | 0.442684 |
| RTMX module-valid | 0.751515 | 0.698485 |

Results are mixed. Top-five reranking cannot improve Recall@5/@10; RTMX has only seven modules. Valid schemas and citations do not prove semantic grounding. No general superiority or significance claim is supported.

## Remaining work

Native Windows execution and browser acceptance are verified for the documented local scope. Drafts still need external review and institutional completion. External requirements include independent semantic/label review, author and institutional details, final formatting, plagiarism review, and selected venue/indexing verification. Other provider adapters have not been experimentally evaluated. No submission is authorized.

See PROJECT_STATE.json, RESUME.md, docs/COMPLETION_CHECKLIST.md and reports/results/RESULTS.md. All authored work remains under this project root.

## Engineering release — 2026-10-12

All 14 saved experiment records are synchronized into the packaged dashboard, including the four completed RAG evaluations. `START_HERE.md` explains installation and the saved demonstration. Browser evidence: `reports/frontend/2026-10-12T06-01-24-831Z/validation.json`. Older manuscript/deck statements about browser availability reflect their 2026-10-08 preparation date; this release record supersedes that engineering limitation. The research results and remaining scientific limitations are unchanged.

## OmniRoute extension — 2026-10-13

Free-route integration and a resumable evaluator are implemented. All 53 tests and the frontend build pass. OmniRoute contract tests use labelled synthetic HTTP fixtures, not live model responses. No OmniRoute account or gateway is connected here; live inference and revised accuracy are NOT RUN. See `docs/OMNIROUTE_FREE.md`. This update does not change prior experimental results or establish model superiority.

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

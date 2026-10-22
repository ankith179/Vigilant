# VIGILANT reliability and data audit

Date: 2026-10-22  
Scope: Current Windows working tree, parser/graph/rule/LLM/API/UI paths, prepared dataset files, preserved model results, tests and frontend build. Two isolated local diagnostic runs were performed; no labels were changed and no cloud inference was used.

## Verified findings

1. **Accuracy is not ready for an independent claim.** Original authored diagnostics: Qwen3 8B 0/12, Qwen2.5 Coder 14B 1/12, Qwen3 14B 0/12. Two isolated Qwen2.5 follow-ups scored 2/12 with evidence-v2 and 4/12 with Git-derived change facts; both had 12/12 valid responses. The 50% majority baseline is 6/12. The change-facts prompt remains below that baseline. Qwen3 outputs failed strict citation/artifact alias validation for all 24 original calls. All cases are authored/correlated development diagnostics. The requested 91% milestone requires 200+ independently reviewed cases (182/200 for 91% observed) and is NOT RUN or established.
2. **A repository-grounded chat assistant is now implemented, with a deliberately limited scope.** A floating chat panel and `POST /api/chat` accept a repository/snapshot, bounded question/history, and optional provider. It retrieves and source-verifies excerpts; the evidence-only default does not call a model. Model citations resolve to returned excerpts, but semantic support remains unverified and conversation history is not persisted. Agent Investigation remains a separate record view.
3. **Language coverage is limited.** `ingestion/parsers.py` has Python AST and Java/JavaScript/TypeScript Tree-sitter branches; C++, Swift, C#, Go and Rust parsing/resolution are absent. Generic file ingestion is not language support.
4. **Graph-derived trace conclusions could be too strong.** The old rule path treated loss of any selected graph edge as `BROKEN_TRACE`, even where the edge was inferred. This audit changes that path: only declared edges can yield `BROKEN_TRACE`; inferred edge loss becomes `POTENTIAL_INCONSISTENCY`. The declared-edge marker is kept transient so immutable persisted graph payloads remain compatible.
5. **Numeric rule confidence is uncalibrated.** `consistency/rules.py` still emits fixed values (1.0 or 0.65). These are rule constants, not empirically calibrated probabilities and should not be presented as model accuracy.
6. **Citation validity is not semantic support.** The model pipeline restricts references to supplied aliases and verifies provenance, but records `semantic_entailment_verified: false`. A valid citation does not show that the cited text entails a conclusion.
7. **Dataset scope limits conclusions.** LiSSA/eTour datasets evaluate requirement-to-code trace-link recovery, not real change-impact accuracy. RTMX is a seven-target module-level subset; its function-level targets do not resolve and two missing test modules are excluded. SAFA is artifact-evolution evidence, not independently labeled source-code consistency ground truth. ChangeBench labels are authored and affected sets incomplete/correlated.
8. **Deployment authentication is opt-in.** `backend/app.py` enforces a bearer token only when `VIGILANT_ACCESS_TOKEN` is set. The default launcher is local-only, but the app does not itself refuse a non-loopback bind without a token; do not expose it on a network without authentication and deployment hardening.

## Accuracy debug follow-up

The prompt-input audit found that the model saw paired excerpts and snapshot IDs,
but not a concise, machine-derived summary of deleted/added/modified artifacts. The
actual Git diff already carried the removed `test_redirect_no_app` function; the
evidence-v2 packet omitted that function's removed lines. A deleted-test case was
then incorrectly described as consistent.

`change_analysis/diff.py` now formats bounded artifact deltas and actual diff lines.
Production and diagnostic prompts label them as orientation, not proof; the model
must still cite source excerpts. `paired-neutral-v3-change-facts` is fingerprinted
separately. The option `--include-git-change-facts` creates a separate diagnostic
dataset without injecting expected labels.

Results, same Qwen2.5 Coder 14B digest and decode settings:

| Input | Correct | Accuracy | Valid responses |
| --- | ---: | ---: | ---: |
| Original paired evidence | 1/12 | 8.3% | 10/12 |
| Evidence-v2 | 2/12 | 16.7% | 12/12 |
| Evidence-v2 + Git change facts | 4/12 | 33.3% | 12/12 |

This is a controlled development comparison on the same 12 authored cases, not a
held-out test. Four correct is still below the 6/12 majority baseline. The change
facts improved deleted-test and API-change examples but failed to fix several
requirement/code-change classifications.

Recomputing current rules on the same authored cases yielded 11/12 exact status-set
matches (91.7% development agreement). This is not independent accuracy: rule work
was informed by these cases. The remaining authored-label mismatch is case 10,
where the expected `BROKEN_TRACE` is stronger than the evidence because no explicit
trace is declared; the conservative `POTENTIAL_INCONSISTENCY` is retained.

The requested 200-case milestone is not met by the 12-case diagnostic set. For
exactly 200 independently reviewed cases, the requested observed threshold is at
least 182 exact matches (91%). Do not duplicate, paraphrase, or synthetically
relabel the existing 12 cases to reach the required count. Even 182/200 would be an
observed score, not by itself proof of 91% population accuracy.

A blind annotation starter is at `reports/independent-review-20261022/`. It has
79 source-changing commits from Express, Flask, the FastAPI full-stack template,
and Spring PetClinic. All reviewer fields are blank, and no expected labels or
model answers are included. The candidate pool is short by 121. These candidates
are not evaluation data until two reviewers annotate independently, disagreements
are adjudicated, and repository/change-family splits are approved.

## Prepared dataset integrity

The current prepared SMOS, iTrust, eTour English and RTMX module-valid files passed checks for duplicate source IDs, target IDs and links; dangling gold-link endpoints; and SHA-256 correspondence to 705 referenced raw artifact files. Full summary: `dataset-integrity.json`.

| Dataset | Sources | Targets | Gold links | Artifact-file hashes checked |
| --- | ---: | ---: | ---: | ---: |
| SMOS | 67 | 100 | 1,044 | 167 |
| iTrust | 131 | 226 | 286 | 357 |
| eTour English | 58 | 116 | 308 | 174 |
| RTMX module-valid | 22 | 7 | 22 | 7 |

All reported integrity error counts were zero. This is a structural/hash check; it does not independently validate whether each gold link is semantically correct or whether dataset licenses permit redistribution beyond their notices.

Sixteen nested `.env` files were inspected without printing their values. Sensitive-looking values in the supplied ChangeBench/repository fixtures matched template defaults; they were preserved as fixture data. The root `.env` is absent; `.env.example` is the only root-level environment file.

## Changes made

- Graph edges built from explicitly supplied declared links carry an in-memory declared marker.
- Lost inferred CALLS/TESTS/API-style edges now create a review-needed potential inconsistency rather than a confirmed broken trace.
- Added regression tests for inferred-edge downgrade, declared-edge confirmation, and immutable graph persistence.
- Added a read-only repository/snapshot chat API and floating frontend panel, with bounded history, source-verified retrieval, citation mapping, evidence-only mode, and explicit semantic-support limitations.
- Added bounded Git/artifact delta facts to model context and fixed duplicate deleted-test/deleted-implementation rule findings; change-facts comparison is kept separate from all frozen outputs.
- Removed only the ignored pytest caches: `.pytest_cache` and two top-level `pytest-cache-files-*` directories. Datasets, model/runtime dependencies, databases, historical runs, and manuscripts were retained.

## Verification

- Python tests: **88 passed**, one existing Starlette/AnyIO deprecation warning. Use `.venv/Scripts/python.exe -X utf8` on Windows.
- Frontend production build: **passed**.
- Browser acceptance: full mutation-enabled run passed existing pages, chat evidence-only workflow, project creation, deterministic investigation, exports, and 390px mobile chat layout; `reports/frontend/2026-10-22T06-50-58-933Z/validation.json`.
- Touched-file diagnostics: **no errors**.
- Saved retrieval metrics: **23 method rows and 1,484 query rows** independently recomputed; see `metrics-audit.json`.
- Saved RAG records: **251 generations** passed provenance/schema audit with the archived provider source; see `rag-audit.json`.
- Two separate 12-call local development comparisons completed. Frozen 2026-10-21 model outputs were not changed; no cloud/provider call or independent annotation was performed.

## Recommended next work

1. Collect independent, repository-separated change-impact labels, including unaffected artifacts and explicit abstention cases; double-review and adjudicate disagreements.
2. Fix the output contract on a development split and inspect raw input/output pairs; do not relax citation validation to raise scores. Compare models and prompt/evidence variants under identical frozen inputs.
3. Measure retrieval quality, semantic citation support and decision quality separately. Preserve all negative results and test once on held-out repositories after model/prompt selection is frozen.
4. Extend chat with clickable in-app source navigation and optional persisted conversation sessions only after access-control and privacy requirements are defined; keep every response tied to the selected commit and verified citations.
5. Add C++/Swift only with language-specific fixtures and compiler-aware resolution, then report per-language parse/resolution coverage. Do not claim support from file indexing alone.
6. Replace fixed confidence values with clearly named rule strength/evidence sufficiency or calibrate probabilities on independent validation data.

**Release conclusion:** engineering verification improved, but the best completed model result remains 4/12 (33.3%) on authored diagnostics, below the 50% majority baseline. Independent accuracy is unmeasured. The requested 91% result on 200+ independent cases is NOT RUN and not established; no general LLM/RAG superiority claim is supported.

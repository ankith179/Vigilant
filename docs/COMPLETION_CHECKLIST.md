# VIGILANT completion checklist

The project is not ready to claim final M.Tech or publication completion.
The executable implementation, frozen evaluation, manuscript drafts and
demonstration deck are complete for their stated scope. Linux browser checks are complete; Windows and external validation are separate gates.
`PROJECT_STATE.json` is the current task ledger; `RESUME.md` identifies the next
step. A row marked executed does not establish superior research performance.

| Requested work | Verified state | Evidence or remaining work |
| --- | --- | --- |
| 1. End-to-end implementation | EXECUTED | `experiments/pipeline/20261006T195007-e56e6b8d/results.json`; Git to artifacts, graph, retrieval, bounded investigation, findings and report |
| 2A. Real pretrained embeddings | EXECUTED | Pinned MiniLM; saved TF-IDF/BM25/embedding/hybrid comparisons across four prepared datasets |
| 2B. Reproducible LLM | EXECUTED LOCALLY | Pinned Qwen 1.5B; raw generated responses and schema validation. Other provider adapters are not experimentally evaluated |
| 2C. Agent execution | EXECUTED, BOUNDED | Twelve recorded tool stages; scripted investigation, not an autonomous planning-agent superiority result |
| 3. Traceability quality | MEASURED | Bounded candidates, hybrid and graph comparisons, validation-based ranker rejection; false positives remain possible and no universal quality gain is established |
| 4. Knowledge graph | IMPLEMENTED AND PERSISTED | `knowledge_graph/graph.py`, stored nodes/edges, structural relationships and commit MODIFIES edges; static-analysis limits are documented |
| 5. Evidence-grounded RAG | PARTLY VALIDATED | Exact quotes/provenance/schema audited; semantic entailment and hallucination rate need independent review |
| 6. Change-aware analysis | EXECUTED ON CONTROLLED CASES | Twelve actual Git scenarios and the API-change demonstration; independently labelled real-change effectiveness remains open |
| 7. VIGILANT-ChangeBench | EXECUTED, AUTHORED ORACLE | Saved baseline/change commits and expected statuses; affected sets are incomplete and correlated |
| 8. Complete experiments | EXECUTED FOR FROZEN PROTOCOLS | All 251 RAG generations across four datasets completed and audited; 23 method rows and 1484 query rows independently recomputed. Existing IR/embedding/KG/SAFA/pipeline runs remain immutable |
| 9. Ablation study | EXECUTED, NEGATIVE RESULT | Sixty generated observations. All five model variants return UNCERTAIN, with 25% authored-label agreement, equal to always-UNCERTAIN |
| 10. Multiple datasets | EXECUTED WITH DISTINCT SCOPES | SMOS, iTrust, eTour English, RTMX module subset; SAFA evolution and controlled repository changes are reported separately |
| 11. Existing-work comparison | TARGETED COMPARISON DRAFTED | Verified primary sources in separate survey and research paper; no external scores treated as reproduced results |
| 12. Frontend | BUILT AND BROWSER VERIFIED | Native Windows Chromium 156: all 13 research pages, pagination, graph, evidence/report exports, recovery, deterministic investigation, repository chat and 390px mobile layout passed; see `reports/frontend/2026-10-22T06-50-58-933Z/validation.json` |
| 13. Reproducibility | IMPLEMENTED; WINDOWS UNVERIFIED | Pinned dependencies/models/data; exact-run reuse, restore scripts, task ledger, archive manifests and Windows scripts |
| 14. Testing | 88 TESTS PASSED | Python parser, Git, evidence, API/chat, Git change-facts, review-pool and integration tests pass on native Windows with UTF-8 mode; production frontend build and browser acceptance pass |
| 15. Tables and figures | MEASURED OUTPUTS COMPLETE | `reports/results/`, `reports/rag/`, `reports/ablation/`; actual tables and scientific plots generated and visually checked |
| 16. Thesis | TECHNICAL DRAFT COMPLETE | 27-page PDF, editable source and audited result-derived tables; author/institution/supervisor details and prescribed format remain external |
| 17. Separate survey paper | TARGETED DRAFT COMPLETE | Four-page IEEE draft with nine research records, two model cards, taxonomy and explicit review limitations; broader full-text review pending |
| 18. Research paper | TECHNICAL DRAFT COMPLETE | Four-page IEEE draft, measured tables, mixed/negative findings, verified references; author and external review pending |
| 19. Publication verification | EXTERNAL BLOCKER | No selected venue; indexing, fees, policies and deadlines not verified. No submission authorized |
| 20. Demonstration | RECORDED DEMO AND DECK COMPLETE | 14-slide editable deck, actual graph edges, route-change commits, evidence and model uncertainty. Linux browser demonstration verified; native Windows execution remains unverified |

## Final acceptance evidence

For every reported result, preserve dataset and commit, input population, method,
model revision, parameters, raw output, gold/oracle scope, metric definition,
unrounded result and source hash. Independent arithmetic audits check saved
rankings; they do not independently label artifacts or prove semantic grounding.

The central claim that the integrated model system detects inconsistency better
or more reliably than appropriate baselines is **not established**. Graph context
and RAG produce dataset-dependent effects. A valid thesis can report these
limitations and negative results, subject to supervisor review; it cannot turn
them into positive evidence by changing the prose.

## Remaining order

1. DONE: Linux browser interaction checks passed on 2026-10-12; record preserved.
2. Run the supplied setup and demonstration on the user's Windows computer.
3. Complete independent annotation and semantic grounding review. Keep negative model results intact.
4. Supply author, supervisor and institution details, then apply prescribed formatting.
5. Expand full-text survey coverage as required and obtain external scientific/plagiarism review.
6. Select a venue before verifying indexing, fees, policies and deadlines. No submission is authorized.

## Time estimate

No inference or manuscript generation remains under the completed protocols.
Linux browser checks are complete. Windows checks require the user computer.
Independent review and institutional approval have no defensible fixed completion
estimate before reviewers, requirements and access are known. The project cannot
be declared finished based only on elapsed time or an unsupported percentage.

## OmniRoute extension — 2026-10-13

- IMPLEMENTED: explicit provider/model route, operator free-eligibility allowlist, no client fallback/retry, expanded complete-excerpt evidence profile and model/usage provenance.
- VERIFIED: 53 total unit/integration tests (synthetic HTTP responses for OmniRoute), frontend build, bounded evaluation/resume and failure exclusion.
- NOT RUN: live OmniRoute inference, free-account quota verification, OmniRoute accuracy comparison and native Windows launch. No gateway or provider account is connected in the hosted session.
- The 2026-10-12 13-page browser record remains preserved. It predates the added OmniRoute selector; the new live provider path is not browser-validated.
- A stronger-model accuracy claim remains unsupported until the new evaluation completes; this is additional work beyond the prior frozen protocol.

# VIGILANT implementation and measurement release

24 October 2026. Current requested target: **95%**.

**The requested 95% accuracy has not been achieved or independently measured.** The engineering implementation was extended and tested. The wider project is not marked fully complete.

## Implemented in this release

- A shared snapshot investigation service used by CLI, MCP, HTTP and the new Investigation Tools UI.
- Ten validated tool contracts (nine enabled in default MCP/HTTP), exact revision scope and bounded repository/artifact/dependency/evidence operations.
- Retained result identities with Git revalidation; append-only unknown history, source-linked resolutions and expected-revision conflict checks.
- Five finite investigation recipes with evidence accumulation, step references, resource budgets and explicit unknowns.
- Optional Git search-inventory manifests for reviewed obligation boundaries: exact paths/object IDs, exclusions, searched artifact identities and unresolved regions.
- Stronger source validation checks the full artifact range as well as its cited excerpt, preventing a genuine short quote from hiding an altered artifact tail.
- A separate 95% assurance protocol checking traceability, impact and consistency, frozen dataset/pipeline identities, independent review fields and missing/stale predictions.
- Fixed a reused-result timestamp mismatch and mobile overflow found during acceptance. Corrected the default historical RAG auditor to use its archived provider source.
- Current capability matrix, architecture, evidence, graph, security, CLI/MCP, evaluation and immediate-execution documentation. Earlier versions of overwritten documentation are preserved under docs/prior-to-investigation-tools/.

The original pipeline, knowledge graph, retrieval methods, model adapters, investigation reports, chat, native language adapters, datasets and manuscript drafts remain present. No external project was cloned, and no third-party source was copied. No GitHub push, deployment or remote database mutation was performed. Both connected database accounts returned no projects.

## Checks actually completed

| Check | Result |
|---|---:|
| Full Python regression suite | **186 passed**; one existing Starlette/AnyIO deprecation warning |
| Production frontend | **Build passed** |
| Browser acceptance | **14 pages passed**, Chromium 141.0.7390.37 on Linux |
| Real repository snapshot tools | **3 passed**: Flask, Spring Petclinic and Express |
| HTTP / CLI / MCP agreement | Passed, including actual MCP subprocess discovery |
| npm audit | **0 vulnerabilities**, including development dependencies |
| Historical preservation | **550 files match saved hashes** |
| Saved retrieval arithmetic | **31 method rows / 1,986 query rows pass** |
| Saved model provenance | **251 RAG generations and 36 citation-repaired diagnostics audited** |
| New model inference / independent labels | **0 / 0** |

Browser tests include source navigation, saved-report chat, deterministic analysis, coverage, exports, new tools, retained-result revalidation, unknowns and mobile layout. An initial browser launch hit restricted Unix sockets; a compatible headless shell with finite test flags completed acceptance. The production server configuration was not weakened. Failed QA attempts are retained with the successful run; screenshots are internal and excluded from delivery. Native Windows acceptance was not run here.

## Actual measured results

Recomputed existing source-only development rankings, **314 real Java changes across 10 projects**. Gold labels were used only by the offline scorer; no rankings were regenerated or tuned in this release.

| Retrieval method | Mean Recall@10 | MRR | Mean nDCG@10 |
|---|---:|---:|---:|
| TF-IDF | 82.04% | 0.7133 | 0.6905 |
| BM25 | 84.72% | 0.7434 | 0.7223 |
| Rank fusion | **85.11%** | 0.7638 | 0.7376 |

Rank fusion fully retrieves the annotated changed-test set within ten results for **230/314 cases (73.25%)**. This is narrower than overall correctness. The preserved retrieval bandit remains unpromoted: 84.27% held-development Recall@10 versus fixed fusion 85.64%. The historical citation-repaired authored diagnostic best is **4/12 (33.33%)**; these are not independent final-test cases.

| Assurance task | 95% result |
|---|---|
| Independent traceability precision / recall / F1 | **NOT_EVALUATED** |
| Independent impact precision / recall / F1 | **NOT_EVALUATED** |
| Independent consistency accuracy / macro-F1 | **NOT_EVALUATED** |
| Independently reviewed semantic evidence support | **NOT_EVALUATED** |

Missing independent final labels, frozen disjoint protocol/data, matching predictions and semantic review prevent this evaluation. Passing software tests or checking citations cannot fill those gaps. The packaged evaluator will not turn missing data into a 95% success.

## Reproduce

```
python -m pytest -q
npm --prefix frontend ci --ignore-scripts
npm --prefix frontend run build
python scripts/restore_checkpoint.py
python scripts/run_frontend_check.py
python scripts/measure_quality.py --output reports/my-measurement.json
python scripts/check_quality_target.py --output reports/my-95-gate.json
python vigilant.py tools
```

For browser tests install a compatible Chromium through tools/browser or set VIGILANT_BROWSER_EXECUTABLE. The reported browser version is explicit; all tests were Linux tests. The supplied 95% gate returns NOT_EVALUATED until reviewed inputs are provided. See docs/EVALUATION_PROTOCOL.md for --dataset/--predictions/--protocol usage and fingerprint requirements.

## Open work

Independent annotation/adjudication, semantic support review and final 95% evaluation; full project-aware compiler semantics; full-weight RL and justified reviewed rewards; general autonomous conversations and source patches; fresh native Windows and live-provider/hosted-database validation; production security/performance certification; final institutional details and academic submission. Older dated drafts retain their historical target/results; this report supersedes them for current implementation status.

Extract the ZIP into a **separate folder** and keep your current Windows database. Dependencies, compiler runtimes, local model weights and provider credentials install separately; they are not bundled. Built frontend, code, tests, preserved data/snapshots, experiments, measurements and documentation are included. Fresh-extraction integrity/application verification is recorded in the sibling release-verification file after packaging.

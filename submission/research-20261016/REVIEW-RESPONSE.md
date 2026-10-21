# Response to the VIGILANT research-paper review

Revision completed 16 October 2026. The exact requested title and author are retained. The revision corrects reporting and adds analyses of saved outputs; it does not claim that editing has resolved the failed consistency capability. No new model outputs or independent annotations were created.

| Review concern | Action and evidence | Status |
|---|---|---|
| Consistency assurance is unsupported | Abstract, Results, Discussion and Conclusion explicitly state that consistency detection remains unresolved and assurance is an objective. | Claims corrected; empirical capability unresolved |
| Small, inconsistent retrieval gains | Added paired-query bootstrap intervals, 20,000 resamples with fixed seeds, a revised signed Figure 2, and per-query AP deltas. | Additional analysis completed |
| Ablation does not isolate components | Described a configuration comparison; disclosed changing inputs/budgets and authored graph trace relations; supplied a controlled-study protocol. | Reporting corrected; new controlled experiment pending |
| No-link queries excluded | Retained exclusion counts (26 iTrust, one eTour), explained scope, and specified independent no-link adjudication before false-positive evaluation. | Scope corrected; evaluation pending |
| Tiny RTMX subset | Described consistently as 22 queries and seven modules; explained Recall@10 ceiling and unresolved function annotations. | Addressed |
| Evidence validity conflated with correctness | Distinguished source/revision validity, partial impact coverage, and semantic correctness in Discussion and limitations. | Addressed |
| Figure 2 says “Absolute” | Changed to “MAP differences produced by LLM reranking”; added signed descriptive uncertainty intervals. | Corrected |
| RAG terminology | Defined retrieved prefixes, candidate judgments, stable supported-first ordering, invariant Recall@5/@10; used “RAG-assisted LLM reranking.” | Addressed |
| Continuous assurance claim | Limited continuous operation to an implemented Git HEAD trigger; no longitudinal guarantee claimed. | Addressed |
| Universal uncertainty | All 60 raw outputs already say UNCERTAIN with confidence zero; five additionally have invalid citation aliases. Prompt example and short excerpts are plausible, unisolated contributors. | Log diagnosis completed; causal test pending |
| Conditions for decisive judgments | Documented matching consistency labels, positive confidence, supplied evidence and valid aliases. SUPPORTED/UNSUPPORTED belong to the separate trace-candidate schema. | Addressed |
| Runtime interpretation | Reported 37.93–70.82 seconds as observed CPU durations, with host, memory, threads and software versions, not controlled throughput. | Addressed |
| Architecture readability | Rebuilt Figure 1 with larger labels and separate graph, retrieval, impact, rules, model and persistence components; explained dashed evidence arrow. | Addressed |
| Reproducibility | Included exact saved inputs, hashes, model/dataset pins, source, CSVs, prompt/validator code and commands. | Saved-result reanalysis reproducible |
| Related work and novelty | Compared task units, artifact scope, revision provenance and decision semantics against LiSSA, REFSQ RAG, TransArC and SWE-agent; no algorithmic novelty or priority claim. | Addressed |
| Confusion matrices and class metrics | Added matrices and class metrics for each configuration, macro-F1 0.10 and non-uncertain coverage 0%; summarized in paper. | Addressed |
| Rules-only baseline | Reported saved multi-label rule findings separately. Expected-label containment is not single-label accuracy; common independent decision units specified for future comparison. | Diagnostic completed; fair controlled comparison pending |
| Reference completeness | Retained 14 references; completed BM25 volume, issue and pages using the author manuscript; added source access dates. | Addressed |
| Official formatting, fonts, readability, length | IEEEtran PDF and IEEE Word-template-based DOCX; local rendering and package checks documented in VERIFICATION.md. | See final verification |
| Similarity check / IEEE PDF eXpress | Neither external service has been run; no submission or certification claimed. | Pending |

## What the analyses establish

Only the SMOS 95% interval excludes zero under within-dataset paired-query resampling. The other three intervals cross zero. These are post-hoc descriptive intervals conditional on the frozen configuration; they do not measure prompt robustness, model-seed variability, independent-project generalization or multiplicity-adjusted significance. The negative RTMX estimate is retained.

All configurations have the same confusion matrix because every decision is uncertain. There are 12 authored cases reused across configurations, not 60 independent cases. The validator did not turn otherwise decisive raw predictions into uncertainty. Universal abstention remains inadequate as an automatic consistency detector.

Rule findings can contain multiple statuses and the authored cases align with implemented rules. A set containing the expected label does not establish independent precision or classification accuracy. The revised paper does not label this as “100% rules accuracy.”

## Work that remains genuinely open

Independent semantic and consistency labels, a fair controlled consistency comparison, verified no-link negatives, prompt/model robustness, longitudinal operation, live OmniRoute accuracy and external submission validation remain outstanding. The included protocol and blank annotation worksheet make that follow-up concrete. No external reviewer was contacted and no fee was incurred.

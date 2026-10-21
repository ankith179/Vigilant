# Supplementary analysis of frozen VIGILANT results

Completed 16 October 2026. Zero new inference calls. Raw experiment results remain unchanged.

## Paired-query bootstrap

Twenty thousand paired-query resamples per dataset; seeds 20261015–20261018. Queries are sorted by ID. Resampling draws query AP differences with replacement and reports percentile 95% intervals. These are descriptive, post-hoc, conditional on the fixed model/prompt and dataset. Correlated queries may violate exchangeability. No project-generalization or multiplicity-adjusted significance claim follows.

| Dataset | Queries | MAP delta | 95% interval | AP improved / worsened / unchanged |
|---|---:|---:|---|---|
| SMOS | 67 | +0.003506 | [+0.000188, +0.007251] | 8 / 2 / 57 |
| iTrust | 105 | -0.002519 | [-0.024396, +0.017745] | 22 / 14 / 69 |
| eTour_en | 57 | +0.002131 | [-0.011850, +0.016945] | 13 / 12 / 32 |
| RTMX-module-valid | 22 | -0.053030 | [-0.148485, +0.021212] | 3 / 5 / 14 |

Only SMOS excludes zero under this query-level resampling. Rank changes can leave AP unchanged, for example when nonrelevant items are reordered. These AP-change counts therefore differ from the ranking-change counts in the main paper.

## Consistency matrices and class metrics

Rows are authored labels; columns are predictions, in this order: POTENTIAL_INCONSISTENCY, BROKEN_TRACE, MISSING_TEST, UNCERTAIN. The 12 cases are reused across configurations; do not pool them as 60 independent observations.

### Configuration E

| Authored label | Potential | Broken | Missing test | Uncertain |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 0 | 0 | 0 | 6 |
| BROKEN_TRACE | 0 | 0 | 0 | 2 |
| MISSING_TEST | 0 | 0 | 0 | 1 |
| UNCERTAIN | 0 | 0 | 0 | 3 |

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 6 | undefined (0 for macro) | 0.00 | 0.00 |
| BROKEN_TRACE | 2 | undefined (0 for macro) | 0.00 | 0.00 |
| MISSING_TEST | 1 | undefined (0 for macro) | 0.00 | 0.00 |
| UNCERTAIN | 3 | 0.25 | 1.00 | 0.40 |

Authored-label agreement: 0.25. Macro-F1: 0.10. Non-uncertain coverage: 0%. Citation failures: 0/12. Accuracy among answered cases is undefined because there are no non-uncertain answers.

### Configuration F

| Authored label | Potential | Broken | Missing test | Uncertain |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 0 | 0 | 0 | 6 |
| BROKEN_TRACE | 0 | 0 | 0 | 2 |
| MISSING_TEST | 0 | 0 | 0 | 1 |
| UNCERTAIN | 0 | 0 | 0 | 3 |

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 6 | undefined (0 for macro) | 0.00 | 0.00 |
| BROKEN_TRACE | 2 | undefined (0 for macro) | 0.00 | 0.00 |
| MISSING_TEST | 1 | undefined (0 for macro) | 0.00 | 0.00 |
| UNCERTAIN | 3 | 0.25 | 1.00 | 0.40 |

Authored-label agreement: 0.25. Macro-F1: 0.10. Non-uncertain coverage: 0%. Citation failures: 1/12. Accuracy among answered cases is undefined because there are no non-uncertain answers.

### Configuration G

| Authored label | Potential | Broken | Missing test | Uncertain |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 0 | 0 | 0 | 6 |
| BROKEN_TRACE | 0 | 0 | 0 | 2 |
| MISSING_TEST | 0 | 0 | 0 | 1 |
| UNCERTAIN | 0 | 0 | 0 | 3 |

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 6 | undefined (0 for macro) | 0.00 | 0.00 |
| BROKEN_TRACE | 2 | undefined (0 for macro) | 0.00 | 0.00 |
| MISSING_TEST | 1 | undefined (0 for macro) | 0.00 | 0.00 |
| UNCERTAIN | 3 | 0.25 | 1.00 | 0.40 |

Authored-label agreement: 0.25. Macro-F1: 0.10. Non-uncertain coverage: 0%. Citation failures: 1/12. Accuracy among answered cases is undefined because there are no non-uncertain answers.

### Configuration H

| Authored label | Potential | Broken | Missing test | Uncertain |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 0 | 0 | 0 | 6 |
| BROKEN_TRACE | 0 | 0 | 0 | 2 |
| MISSING_TEST | 0 | 0 | 0 | 1 |
| UNCERTAIN | 0 | 0 | 0 | 3 |

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 6 | undefined (0 for macro) | 0.00 | 0.00 |
| BROKEN_TRACE | 2 | undefined (0 for macro) | 0.00 | 0.00 |
| MISSING_TEST | 1 | undefined (0 for macro) | 0.00 | 0.00 |
| UNCERTAIN | 3 | 0.25 | 1.00 | 0.40 |

Authored-label agreement: 0.25. Macro-F1: 0.10. Non-uncertain coverage: 0%. Citation failures: 1/12. Accuracy among answered cases is undefined because there are no non-uncertain answers.

### Configuration I

| Authored label | Potential | Broken | Missing test | Uncertain |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 0 | 0 | 0 | 6 |
| BROKEN_TRACE | 0 | 0 | 0 | 2 |
| MISSING_TEST | 0 | 0 | 0 | 1 |
| UNCERTAIN | 0 | 0 | 0 | 3 |

| Class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| POTENTIAL_INCONSISTENCY | 6 | undefined (0 for macro) | 0.00 | 0.00 |
| BROKEN_TRACE | 2 | undefined (0 for macro) | 0.00 | 0.00 |
| MISSING_TEST | 1 | undefined (0 for macro) | 0.00 | 0.00 |
| UNCERTAIN | 3 | 0.25 | 1.00 | 0.40 |

Authored-label agreement: 0.25. Macro-F1: 0.10. Non-uncertain coverage: 0%. Citation failures: 2/12. Accuracy among answered cases is undefined because there are no non-uncertain answers.

## Raw-output diagnosis

All 60 raw JSON responses select UNCERTAIN with confidence zero. Forty-six give “Evidence is incomplete” as their entire reason. Five also contain unknown citation aliases. Thus validation does not explain universal abstention. The system prompt contains an uncertain example, and only six excerpts of at most 400 characters each reach the measured investigation model. Prompt anchoring and evidence truncation are plausible contributors, not proven causes. Positive confidence, matching labels and a supplied citation are syntactic acceptance conditions; they cannot establish entailment.

The graph-assisted consistency configurations receive authored expected_traceability relations through build_graph in run_ablation.py. This is an additional limitation of the configuration comparison. The separate retrieval graph baseline uses extracted structural edges and does not use gold trace links as graph edges.

## Saved rules-only diagnostic

These are the existing deterministic finding sets, not a new rules experiment. Multi-label sets are not comparable to single model labels. Authored cases are aligned with rules. Expected-label containment in all 12 sets is not independently validated accuracy or precision.

| Case | Authored label | Rule status set | Findings |
|---|---|---|---:|
| 01-requirement-changed | POTENTIAL_INCONSISTENCY | POTENTIAL_INCONSISTENCY | 1 |
| 02-requirement-added | UNCERTAIN | UNCERTAIN | 1 |
| 03-code-changed | POTENTIAL_INCONSISTENCY | POTENTIAL_INCONSISTENCY | 1 |
| 04-code-deleted | BROKEN_TRACE | BROKEN_TRACE, POTENTIAL_INCONSISTENCY | 2 |
| 05-test-changed | UNCERTAIN | UNCERTAIN | 1 |
| 06-test-deleted | MISSING_TEST | BROKEN_TRACE, MISSING_TEST | 3 |
| 07-frontend-changed | UNCERTAIN | UNCERTAIN | 1 |
| 08-api-changed | POTENTIAL_INCONSISTENCY | BROKEN_TRACE, POTENTIAL_INCONSISTENCY | 15 |
| 09-backend-changed | POTENTIAL_INCONSISTENCY | POTENTIAL_INCONSISTENCY | 1 |
| 10-consumer-changed | BROKEN_TRACE | BROKEN_TRACE | 1 |
| 11-implementation-test-drift | POTENTIAL_INCONSISTENCY | POTENTIAL_INCONSISTENCY | 1 |
| 12-requirement-test-drift | POTENTIAL_INCONSISTENCY | POTENTIAL_INCONSISTENCY | 1 |

The API-change case has 15 findings sharing a route-renaming cause, not 15 independent defects. The controlled-study protocol defines a common decision unit and independent adjudication for a fair comparison.

## Reproduction

Run `python reanalyse.py` with Python 3 and NumPy. It uses the full project when available, otherwise the supplied `data/reanalysis-inputs` mirror. No weights, API account or network access are required. Input hashes, exact model/dataset pins and per-query CSVs are included. The annotation worksheet deliberately leaves reviewer labels blank.

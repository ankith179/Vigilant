# VIGILANT metrics dictionary — proposed evaluation definitions

This document defines measures, not results. Freeze cohort, labels, applicable classes, exposure, denominators and evidence review policy before evaluation. Unavailable denominators produce NOT MEASURED, never zero or PASS.

| Measure | Definition and denominator | Required evidence or caveat |
| --- | --- | --- |
| Strict per-axis agreement | Matches / all cases with a frozen reviewed label on that axis. A missing prediction or abstention against a decisive label is incorrect. UNCERTAIN can match a reviewed UNCERTAIN label. | Report each axis independently, missing labels and prediction failures; do not merge legacy labels with axes. |
| Per-class precision, recall, F1 | TP/(TP+FP), TP/(TP+FN), 2TP/(2TP+FP+FN), respectively. | Define the unit and one-vs-rest class; zero denominator is undefined. Missing predictions stay in the false-negative accounting. |
| Macro-F1 | Arithmetic mean of predeclared class F1 values. | Report class supports and undefined classes; never conceal a minority failure. |
| Confusion matrix | Counts by reviewed label and predicted label. | Include explicit missing/invalid prediction column and uncertain classes. |
| Decisive coverage and selective risk | Accepted decisive predictions / eligible cases; incorrect decisive predictions / accepted decisive predictions. | Publish both together, define accepted labels by axis and count all eligible cases. |
| Trace or impact precision and recall | Reviewed correct predicted links or affected artifacts divided by predicted items or reviewed true items. | Identify link type, artifact level and complete negative/review scope; graph reachability is a candidate only. |
| Retrieval Recall@k, Precision@k | Reviewed relevant references retrieved in top k / all reviewed references; reviewed relevant top-k results / top-k evaluated results. | Report query aggregation, k, corpus, relevance and completeness; missing reference links are not verified negatives. |
| MRR and nDCG@k | Mean reciprocal rank of first reviewed relevant item; normalized discounted cumulative gain at k. | State relevance grades, tie policy and handling of queries without references. |
| Citation validity and semantic support | Valid referenced evidence IDs / all cited IDs; independently adjudicated supported claims / reviewed claims. | Valid IDs and hashes do not prove entailment; track revision mismatches and incomplete review. |
| Change, parser and identity coverage | Correct reviewed detections / relevant reviewed changes; extracted supported constructs / reviewed applicable constructs. | Include parser failures, rename uncertainty, excluded files and language-specific scope. |
| End-to-end task success | Cases satisfying every preregistered applicable critical gate / all eligible reviewed cases. | Require correct artifacts and revisions, trace, impact, consistency, obligation, evidence support, uncertainty and actionable report as applicable; report individual gate failures. |
| Latency, resource and cost | Time, peak memory, model calls, token counts and cost per run or stage. | Record hardware, runtime, workload, concurrency, model and measurement method. |
| Agent operation quality | Reviewed successful or necessary tool operations / applicable reviewed operations; report step counts, failure and termination rates. | Tool selection or retrieved candidates do not alone prove an investigation correct. |

Intervals: report Wilson intervals for proportions as descriptive under independent Bernoulli assumptions. Cases clustered by repository family require a suitable cluster-aware design; too few families means no defensible cluster claim. Paired comparisons require identical labeled cases and a predeclared unit. No metric here establishes the 95% research target without an independently adjudicated held-out evaluation.

Implementation status: `evaluation/decision_v3.py` now includes authority, missing and invalid prediction columns, and describes matching abstentions. Per-axis paired comparisons report McNemar discordances without modeling repository clusters. It does not yet implement all metrics above or establish independent evidence support; validate each evaluation contract before use.

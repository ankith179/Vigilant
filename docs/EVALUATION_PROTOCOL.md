# Current 95% evaluation protocol

The current requested target is 95%; historical 91% files remain preserved. The new protocol is evaluation/quality-target-95.json. It requires at least 200 independently reviewed real-change final-test cases, adjudication, at least two consistency classes, exact source revisions, frozen dataset/pipeline hashes and separately reviewed semantic citation support. Record every tuning repository and change family before freezing a disjoint final test. Do not tune on that test.

Each traceability precision/recall/F1, impact precision/recall/F1 and consistency accuracy/macro-F1 must reach .95. A high score on one task cannot compensate for another. Predictions bind to pipeline, repository and revisions. Invalid, absent and stale responses stay in the denominator. The checker validates the executable pipeline fingerprint and dataset bytes. It consumes recorded reviewer attestations; it does not authenticate reviewer identities.

Observed scores and a Wilson descriptive interval do not establish a population lower bound or cluster-aware generalization. Report per-project results, class support, coverage and unsupported claims. Review labels and negative assumptions independently. Unknown labels are never synthesized from missing links.

`python scripts/measure_quality.py --output reports/my-measurement.json` recomputes the saved 314-case development retrieval: TF-IDF Recall@10 82.04%, BM25 84.72%, rank fusion 85.11%. It also reports MRR, nDCG@10 and full-set retrieval. These find developer-changed test paths; they are not assurance correctness. The contextual bandit remains unpromoted: held-development Recall@10 84.27% versus fixed fusion 85.64%.

No independent final-test labels or corresponding predictions were available for this release. The 95% gate is NOT_EVALUATED. No new LLM inference or full-weight reinforcement learning was performed. Software-test pass counts, citation syntax and Git correspondence are reported separately. See reports/final-95/measurement.json and quality-gate.json.

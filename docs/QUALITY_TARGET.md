# The 91% acceptance target

Current status: **NOT_EVALUATED**. The code provides separate gates; it does not
manufacture independent labels, change diagnostic labels or claim the target has
been reached. All existing model results remain preserved, including failures.

| Dimension | Required measurement |
| --- | --- |
| Traceability | Precision, recall and F1 each at least 0.91 on reviewed link sets |
| Consistency | Accuracy and macro-F1 each at least 0.91, invalid/missing answers included |
| Citation support | Recorded independent semantic review for every evaluated case |
| Operations | Relevant regression, API, browser, integrity and failure-handling checks reported separately |

Passing engineering tests is not a count of accurate real-world model decisions. Neither
schema validity nor a matching quote establishes semantic support. Retrieval MAP
is not consistency accuracy. Traceability scores use micro link counts; reports
must also examine per-repository/language/change-type performance rather than
hiding poor groups in the aggregate.

## Freeze and review

1. Use development cases to inspect error categories and improve extraction,
   retrieval and ambiguity handling. Never tune using final test labels.
2. Record every training/tuning repository and change family in
   `evaluation/quality-target.json`. Reserve disjoint validation and test groups;
   different commits in one repository are not repository-separated tests.
3. Obtain at least 200 real, independently reviewed test cases with positive and
   negative trace links, unchanged artifacts and abstention cases. The preserved
   79-candidate queue is unlabelled, not a test set, and is short of the minimum.
   Exclude candidates from repositories or families used for tuning.
4. Have two reviewers label independently, then adjudicate disagreements with
   source evidence. Include representative supported languages and change types.
   Do not duplicate the 12 authored diagnostics to increase the sample count.
5. Freeze the pipeline, model, prompt, retrieval/parser policies, dataset and
   decision protocol with hashes before running the held-out evaluation. Set
   protocol `status` to `FROZEN` only after that actual review and freeze.
6. Record every output, including invalid, missing and uncertain responses, and
   separately review semantic citation support. Report coverage, confusion and
   failure cases alongside aggregate scores.

## Input contract and offline scoring

The dataset JSON has `split: "test"`, `authored_diagnostics: false`, and `cases`.
Every case needs `case_id`, `repository`, `change_family`, `base_commit`,
`head_commit`, `consistency_label`, `trace_links`, two distinct `reviewer_ids`,
and `adjudicated: true`. Trace links are stable, directed string identifiers
agreed by the annotation protocol, for example a canonical source→target pair.

Predictions are a JSON array with `case_id`, `valid_response`, `consistency_label`,
`trace_links`, `semantic_citations_reviewed` and `semantic_reviewer_id`. Missing
predictions and invalid responses remain errors. Do not mark an invalid response
as a valid UNCERTAIN result. The gate validates recorded attestations; it cannot
authenticate reviewer independence or prove a supplied pipeline hash.

```text
python scripts/check_quality_target.py --dataset reviewed-test.json --predictions predictions.json --protocol frozen-protocol.json --output quality-result.json
```

Without independently reviewed inputs the result is NOT_EVALUATED. The supplied
protocol intentionally remains DRAFT_NOT_FROZEN. `operational_checks_passed` must
refer to actual matching pipeline validation, with the supporting logs retained.

At exactly 200 cases, 182 correct gives 91% observed accuracy. Its 95% Wilson
lower bound is below 91%, so it does not establish 91% population accuracy.
The gate distinguishes the observed threshold from the consistency interval.
It does not establish a joint population claim for all metrics. Correlated
repository changes require cluster-aware uncertainty analysis; the reported
case-level Wilson interval assumes independent observations.

The practical route is better verified evidence and measured error reduction,
followed by an untouched test. A larger model or relaxed citation validation
cannot guarantee the requested score.

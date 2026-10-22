# Independent change-impact review queue

Status: **79 unlabelled candidates; 200-case target not met; no accuracy score.**

The queue contains source-changing non-merge commits selected from pinned local
histories. It contains no expected labels or model answers. Review diffs in
`candidate-cases.json`; record labels and rationale in `review-worksheet.csv`.

| Repository | Candidate changes |
| --- | ---: |
| Express | 9 |
| Flask | 39 |
| FastAPI full-stack template | 8 |
| Spring Petclinic | 23 |

The 200+ target is short by at least 121 cases. Do not fill the shortfall by
splitting one commit into several purportedly independent examples, duplicating
commits, paraphrasing changes, or copying the existing authored ChangeBench cases.
Add several unrelated repositories with verified licenses and sufficient history.

Before reviewers start, approve or revise `docs/DECISION_LABEL_POLICY.md`; it is
currently proposed. Two reviewers should label each change independently without
seeing model answers or historical labels. Record sufficient/insufficient evidence,
missing facts, a primary label, secondary findings, and rationale. Adjudicate every
disagreement without overwriting the initial labels.

Assign train/validation/test by repository or change family, not random cases.
With only four repositories, this queue is useful for annotation practice and
candidate discovery, but it is too small a cluster population for a strong
repository-generalization claim. Keep all 79 candidates unlabelled until review is
actually completed.

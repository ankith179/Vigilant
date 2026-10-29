# Evaluation protocol — draft, not frozen

**Target:** 91% observed correctness under explicitly separate task metrics. **Status: NOT_EVALUATED.** This document develops the existing `QUALITY_TARGET.md` protocol; it is not an approved final statistical protocol and does not turn authored diagnostics into held-out evidence.

## Task definitions and denominators

| Task | Unit / label | Primary measurements | Invalid or missing data |
| --- | --- | --- | --- |
| Traceability link recovery | Directed source→target links with reviewed positive and negative scope | Precision, recall and F1, each ≥0.91 in the existing draft gate; also MAP/nDCG at fixed cutoffs | Unlinked is not automatically negative. Mark incompletely annotated regions unknown and report excluded scope. |
| Change-impact prediction | Actual base/head change and independently reviewed affected artifact set | Precision/recall/F1, false positives, missed impacts and abstention coverage, by repository/change type | Candidate paths are predictions, not gold. Complete impact truth cannot be inferred from changed files alone. Threshold requires a separately frozen protocol. |
| Consistency classification | One reviewed contract/question at base/head with a label from the rubric | Accuracy and macro-F1 each ≥0.91; class confusion, coverage and uncertainty | Every scheduled case remains in the denominator. Invalid or missing outputs count as errors. A valid UNCERTAIN is correct only against the adjudicated UNCERTAIN label. |
| Semantic citation support | Each claim and the actual cited source excerpt/revision | Entailed, contradicted, insufficient and reviewer agreement | Valid ID/quote alone cannot count as supported. All evaluated cases need independent support review. |
| Operations | A specified API/UI/import/export/restore/failure scenario | Regression acceptance, error recovery, integrity, latency/resource limits | Report operational checks separately; no average with model accuracy. |

The existing gate covers traceability and consistency, not a universal percentage for every operation or a completed impact benchmark. Human reviewers must define the scope of positive/negative links and impact obligations before evaluating.

## Label rubric

- **CONSISTENT:** a stated contract and supplied implementation evidence support the checked obligation. Absence of a detected defect is insufficient.
- **INCONSISTENT:** a direct contradiction between the checked contract and implementation.
- **POTENTIAL_INCONSISTENCY:** concrete possible mismatch with a named unresolved assumption.
- **BROKEN_TRACE:** a declared trace endpoint demonstrably no longer exists.
- **MISSING_TEST:** an explicit testing obligation is demonstrably unmet; unchanged/deleted tests alone do not establish this.
- **AFFECTED:** an evidence-supported dependency impact without a demonstrated contract violation.
- **UNCERTAIN:** available evidence cannot establish one of these conclusions.

Before final annotation, reviewers must resolve label overlap and select one primary question per case. For example, impact and contradiction can both hold; label priority must be frozen rather than inferred differently by each scorer. Record supporting and counterevidence, unresolved assumptions, and rationale; do not use file names or mutation authorship as label evidence.

## Review and split procedure

Two distinct reviewers label independently, blinded to model answers and authored labels. Preserve original submissions. A separate adjudicator resolves disagreements using source evidence; record prior exposure and conflicts. Reviewers may request missing context rather than guessing. The supplied development worksheets are deliberately blank and do not attest that review occurred.

Maintain three distinct datasets: link recovery, real-change impact, and consistency. Track provenance and licence for every repository, commit, contract and annotation. Record all repositories/change families used for any tuning. Split by repository and change family; commits from one repository cannot be treated as repository-independent. Keep validation for selection, and final test sealed until the pipeline is frozen. The draft minimum of 200 real independently reviewed cases is a floor, not a statistical power calculation. The existing 79 unlabelled candidates do not satisfy it.

## Controlled development experiment

Predeclare comparison arms and error categories. Hold model/digest, prompt except the intended component, temperature, seed, context/output limits, candidates and evaluation cases fixed. Compare evidence roles/revision labels, changed-hunk excerpts, graph context, counterevidence and reranking one component at a time or under a declared factorial design. Do not change labels in response to a model output. Save all requested cases including preflight failures, invalid responses and truncations; separate infrastructure failure from model output quality.

The packaged offline comparison changes only the final pair-budget policy and its version identifier with no inference. Its results are **packet integrity metrics**, not semantic accuracy. It exposes four empty packets; a later model experiment must not drop those cases from its denominator to improve scores.

## Freeze and report

Freeze model identity, all pipeline source hashes, dependency versions, retrieval/rule/parser policies, dataset/split hashes, candidate sets, prompts, budget policy, label rubric, thresholds and selection procedure. Store exact requests, selected/omitted evidence and reasons, base/head identity, source hashes and spans, provider token/stop telemetry, raw responses and strict-validation results.

Report aggregate and per-repository/language/change-type results with uncertainty, coverage and errors. The existing case-level Wilson interval assumes independent cases; correlated repository changes require cluster-aware analysis. At 200 cases, 182 correct is 91% observed accuracy, not proof that population accuracy exceeds 91%. Predeclare whether the claim is an observed threshold or a confidence-bound target; do not switch after seeing the test results.

The current gate consumes review attestations but cannot authenticate reviewer independence. Keep protocol status `DRAFT_NOT_FROZEN` until these prerequisites are actually completed. Never merge retrieval MAP, citation validity, operational tests and consistency accuracy into one headline number.

## Scorer hardening and pilot

The v2 follow-up rejects truthy string booleans, malformed arrays, nonfinite thresholds and invalid sample minima. Whitespace variants of the same reviewer ID cannot count as two people. Invalid/missing predictions retain their denominator entries; a confusion matrix is exported. Population-accuracy claims remain false in this gate because its case-level interval does not establish a cluster-aware population result.

The 32-case pilot under `reports/audit-v2-20261023/change-pilot` is unlabelled and development-only. `evaluation/change_cases.py` supplies its reviewed-case and obligation schemas. Unknown fields are null, not negative or inferred labels. Schema validity still requires source/semantic review and cannot authenticate annotator independence. Do not set the protocol FROZEN or count these cases as held out without the actual preregistration, review and split work.

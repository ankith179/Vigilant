# V047 development pilot adjudication protocol

Version: `v047-adjudication-v2`  
Status: **FROZEN FOR THE DEVELOPMENT PILOT; NO REVIEW HAS OCCURRED**  
Date: 2026-10-28

## Purpose and scope

This protocol governs initial human judgments on the 24 candidate cards in `data/prepared/v047-dev-pilot-cards-20261028-v2.jsonl`. The cards are real, revision-pinned repository changes selected from a development candidate pool. They are not labeled examples until humans complete the review. The protocol does not authorize using the pilot as an independent or held-out test set. The broader evaluation protocol remains a draft. This v2 sample supersedes v1 before any reviewer opened a sheet because v1 overrepresented D14 and omitted an available D27 candidate.

## Reviewer eligibility and blinding

Use two reviewers with relevant software development, test, or requirements analysis experience. Reviewers must not have authored the VIGILANT rules/prompts being evaluated, authored the original diagnostic labels, or seen each other's judgments. The coordinator must document each reviewer's qualifications and conflicts privately. The two CSVs are separate, initially identical copies. Reviewers must not see model predictions, historical authored labels, D-IDs, candidate categories, or another reviewer's entries before submitting their initial judgments.

## Evidence to inspect

Use the full BASE and HEAD commit IDs, the changed-path diff command, and the exact local repository named in each row. Inspect relevant requirements/specifications, source, consumers, tests, fixtures, and revision history where available. Record evidence notes with revision, path, line range, and content hash. A missing search result is not proof of absence unless the applicable search scope is complete; parser or retrieval failure is not artifact absence. Candidate links and graph/route relationships are leads, not causal proof.

## Independent label axes

Use the exact values from `docs/decision_policy.md` and the V3 case-card schema. Enter each axis independently:

- Trace: `LINKED`, `BROKEN_TRACE`, `MISSING_TRACE`, or `UNCERTAIN`.
- Consistency: `CONSISTENT`, `INCONSISTENT`, `POTENTIAL_INCONSISTENCY`, `NO_ASSURANCE_IMPACT`, or `UNCERTAIN`.
- Test obligation: `SATISFIED`, `UNSATISFIED`, `UNVERIFIED`, or `NOT_APPLICABLE`.
- Authority: `NORMATIVE`, `INFORMATIONAL`, or `NOT_ESTABLISHED`.

Do not infer one axis from another. A declared/candidate link is not semantic support. `UNSATISFIED` requires an explicit applicable obligation and a complete revision-correct search; otherwise use `UNVERIFIED`. Direct requirement/code disagreement is inconsistent only when authority and violation are established. When evidence is insufficient, choose the appropriate axis-specific uncertainty value and explain why. Do not use confidence scores to choose labels.

## Review record and disagreement handling

For every row, fill a privacy-preserving reviewer ID, UTC timestamp, rationale, and evidence notes; use `uncertainty_reason` whenever an axis is uncertain or unverified. Keep each initial CSV immutable after submission. Compute raw agreement and Cohen's kappa separately for each axis on cases both reviewers labeled. Agreement is not proof of correctness. Preserve both initial judgments; a qualified third adjudicator resolves conflicts where available. If conflicts remain unresolved, mark the relevant axis unresolved and exclude it from scored labels under the predeclared missing-label rule; report the count and reason, without silently converting it to a negative.

## V2 selection design

The 24-card sample includes every D-ID category present in the 5-commit candidate pool, using predeclared quotas and a fixed seed. Sampling also prefers lower-count source families and avoids repeated source/revision/path events. Candidate-category strata are hidden from reviewers. The original 12-case mapping remains unknown, so the sample remains development only.

## Dataset and evaluation status

All selected families remain in `dev` because the original 12-case repository mapping is unresolved. This pilot selection is not a frozen 36-case labeled cohort. Do not tune from it and call a later score independent. No metric is produced by creating the review forms. Accuracy is **NOT MEASURED**; independent evaluation is **NOT ESTABLISHED**.

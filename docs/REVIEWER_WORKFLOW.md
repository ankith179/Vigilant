# VIGILANT independent reviewer workflow

## Scope and current status

The handoff at `reports/completion-20261024/review-handoff-final/` contains
blank forms for 32 existing development-pilot cases. Those cases are useful for
error analysis and workflow validation only. They are not an independent final
test set, do not meet the 200-case 95% protocol, and must not be reported as an
independent accuracy result. No reviewer judgment is prefilled here.

The reviewer forms attest independence but do not authenticate reviewer
identity. Arrange qualified reviewers and identity/independence checks through
the study owner. Do not include private identity details in the annotation
files; use stable pseudonymous reviewer IDs and retain any identity record
separately under the study's access controls.

## Materials and blinding

1. Give each reviewer a separate copy of the exact same blank form and the
   matching case packets. Preserve the original templates.
2. Provide `docs/DECISION_LABEL_POLICY.md`, this workflow, the source-readiness
   report, packet manifest, and the exact base/head revisions. The policy is
   proposed; obtain reviewer approval before treating its interpretations as
   frozen study labels.
3. Do not give reviewers model predictions, historical gold labels, the other
   reviewer's answers, or `reports/ablation/review-key.json`.
4. The review handoff is development material and patch text can reveal change
   intent. This is reduced label exposure, not guaranteed blinding. Record this
   limitation in the provenance and do not call these reviews a held-out test.
5. Do not fetch repositories or execute repository code as part of this
   handoff. Inspect the pinned local source. If required content is unavailable,
   retain the case as unresolved and record the missing revision/path.

## Independent annotation

Reviewers work separately and do not reconcile answers until both forms are
saved and checksummed. For every case, inspect both the base and head context;
the patch and changed-file excerpts are navigation aids, not complete impact
gold. Search the full relevant repository when making a completeness claim.
Record a source reference for every material assertion using the canonical
artifact ID, exact commit, repository-relative path, content hash, and inclusive
1-based line span. Cite both sides of a claimed contradiction where available.

Use the seven labels exactly as defined in `docs/DECISION_LABEL_POLICY.md`.
In particular:

- `CONSISTENT` requires positive evidence for the entire stated check; no
  detected defect is not proof of consistency.
- `INCONSISTENT` requires a specific contract and implementation, caller, or
  test that directly contradicts it.
- `BROKEN_TRACE` requires a previously declared trace endpoint and evidence
  that it is absent at head. Similarity candidates are not declared links.
- `MISSING_TEST` requires an explicit applicable obligation and a reviewed,
  sufficiently complete test search.
- `POTENTIAL_INCONSISTENCY` requires a concrete suspected mismatch and a named,
  testable unresolved assumption.
- `AFFECTED` requires evidence of an exposed dependency and affected operation;
  graph connectivity alone is not enough.
- `UNCERTAIN` is the correct label when evidence or search scope is insufficient
  to support another label. State what evidence is missing.

These are illustrative boundaries, not labels for any included case: an
explicit contract contradicted by a verified head implementation illustrates
`INCONSISTENT`; a plausible mismatch that depends on an unresolved runtime
assumption illustrates `POTENTIAL_INCONSISTENCY`; a missing source revision
that prevents a conclusion illustrates `UNCERTAIN`.

For form fields:

- `trace_links` contains only affirmative, independently supported, directed
  links, encoded as stable canonical source-to-target IDs agreed by the study.
  Do not add candidate links because they appear in a graph or patch.
- `affected_artifact_ids` contains artifacts supported by reviewed impact
  evidence. Changed-file candidates are not a complete affected set. If the
  full relevant search was not completed, say so in the rationale and leave
  the completeness claim unresolved.
- `evidence` and `rationale` are required by the form. Do not manufacture a
  citation to satisfy the schema. If no valid source reference exists, stop
  that case and report it to the study owner for a versioned packet repair.
- `UNCERTAIN` remains an explicit outcome and is retained in denominators.
  Empty link or affected-artifact lists mean no affirmative item was recorded;
  they do not establish that a complete search found none.

The reviewer form has no structured negative-link or search-completeness field.
Do not encode a negative claim by simply leaving `trace_links` empty. Record
the search scope and evidence in the rationale. The adjudication record may
populate `reviewed_negative_links` and `obligation_inventory` only after the
complete reviewed scope and counterevidence are documented; otherwise retain
`UNKNOWN` or `INCOMPLETE` and list unresolved items.

## Agreement and adjudication

Once both initial forms are complete and immutable, calculate descriptive
agreement before reconciliation:

```powershell
.\.venv\Scripts\python.exe scripts\summarize_reviewer_agreement.py `
  --reviewer-forms reports\completion-20261024\review-handoff-final\reviewer-1.json reports\completion-20261024\review-handoff-final\reviewer-2.json `
  --output reports\review-agreement\<new-run-id>.json
```

The output reports nominal raw agreement and Cohen's kappa for consistency
labels, plus exact set agreement, mean per-case Jaccard, and pairwise micro
precision/recall/F1 for trace links and affected artifact sets. `UNCERTAIN` is a
label, not a reason to drop a case. Undefined values remain null with an
explicit status. These are inter-rater agreement statistics, not accuracy,
semantic support, source verification, or proof of reviewer independence.
Report class prevalence and the confusion matrix with kappa; low prevalence can
make chance-adjusted agreement unstable. Agreement does not replace an
adjudicator or a complete negative-link review.

An adjudicator reviews disagreements and source evidence after the two forms
are locked. Preserve both original forms, record disagreements, the final
decision, adjudicator ID, rationale, evidence, and unresolved unknowns in a
separate adjudication file. Do not force consensus: if available evidence does
not decide the case, adjudicate it as `UNCERTAIN` and preserve that uncertainty.
Semantic support for any future model claim requires a separate evidence-based
review; agreement on a case label does not establish citation entailment.

Validate completed development reviews against stored artifacts and exact Git
objects with `scripts/import_independent_reviews.py`. The explicit recovery-cache
mode requires both a checksum-matching verified cache and its recovery queue;
it does not relax the revision, scope, or raw-object checks. The intake records
reviewer independence as self-attested, not independently authenticated. It
exports development annotations and does not certify the 95% target.

## Separate final evaluation

The 32 pilot reviews must not be used as final-test labels. The final cohort
requires at least 200 independently reviewed real-change cases, repository- and
change-family-disjoint from every development/tuning source, both reviewers,
adjudication, semantic evidence review, a frozen dataset and pipeline, and
predictions bound to exact revisions and hashes before the final labels are
scored. Record cohort and subgroup metrics, uncertainty, invalid/missing
outputs, coverage, abstention, false positives, false negatives, and evidence
support under `docs/EVALUATION_PROTOCOL.md` and
`evaluation/quality-target-95.json`. Keep dependent and independent results
separate. Do not tune against a final holdout or infer that a 95% point estimate
proves a 95% population lower bound.

Current blocker: no completed reviewer forms, adjudication, authenticated
reviewers, semantic-support judgments, frozen independent dataset, or matching
independent predictions are present. The quality gates remain
`NOT_EVALUATED`; this handoff guide does not change that status.

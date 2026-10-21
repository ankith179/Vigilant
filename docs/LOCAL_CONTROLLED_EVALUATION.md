# Controlled local follow-up

## Executed factor: citation contract

Baseline: `experiments/local-model-comparison/windows-20261021`.
Citation-only arm: `experiments/local-model-comparison/citation-fix-20261021`.
The new grammar restricts evidence/artifact citations to the exact selected
E/A aliases. Artifact references are also derived from validated cited evidence
in `cited_artifacts`; these are not asserted to be proven impacts. The existing
strict parser still rejects unknown IDs and incomplete output. Raw responses
are preserved, not repaired by guessing filename-to-ID mappings.

All three installed model digests, dataset, 36 messages, label definitions,
temperature 0, seed 42, 8192 context tokens, 512 output tokens and thinking mode
are held fixed. Only the Ollama citation adapter changes. The baseline had 26
invalid artifact-alias responses, no invalid evidence aliases, and no detected
truncated completions. Therefore output limits were not increased.

Report accuracy, macro-F1 over the same gold classes, invalid responses,
UNCERTAIN responses and decisive coverage, token counts, truncation, latency,
alias resolution, and semantic citation support separately. Keep invalid
responses in the accuracy denominator. A resolvable ID does not entail the
model's conclusion. See `reports/citation-fix-20261021/protocol.json`.

## Separate evidence arm

`scripts/prepare_local_review.py` exports the exact selected baseline prompts
and a separate `evidence-v2-dataset.json`, with source-verified excerpts for
changed hunks and candidates for requirements, implementation, callers and tests.
It uses snapshot changes and structural edges, not expected labels, oracle target
files, or oracle trace lists. Structural and lexical matches remain candidates.
The evaluator dataset retains the old authored labels for development comparison;
blind review packets omit labels and model answers.

This arm removes overlapping changed-artifact duplication and gives each role
an opportunity within the same 18000-character/24-excerpt selection budget.
Only four changed hunks and one additional candidate per role are considered.
Missing roles and source-selection omissions are explicit in the coverage file.
Role counts are retrieval diagnostics, not proof of sufficiency or relevance.

Have humans inspect the exact post-selection packets before treating the revised
retrieval as sufficient. Do not silently deploy it into the citation-only study.
Any subsequent evidence comparison uses the citation-fixed provider and changes
only evidence; any label-policy/prompt experiment is another separate arm. Do not
change output tokens unless actual completion flags and raw text show truncation.

## Validation, selection and unseen test - NOT RUN

The user confirmed no independently reviewed dataset exists. No model/prompt is
selected for held-out testing, and no held-out score or interval is reported.

1. Sample new changes before examining model output. Reserve whole repositories
   or change families; retain provenance, base/head revisions and family IDs.
   Do not split the existing correlated mutations into supposed independent sets.
2. Obtain two independent labels and adjudication under the approved decision
   policy. Include genuine consistent/negative cases, trace failures, uncertainty
   and changed-family diversity. Record prompt sufficiency and source support.
3. Split development, validation and test by repository/family. Check no shared
   commit ancestry, copied change or near-duplicate example crosses the boundary.
   Dataset metadata alone cannot certify independence.
4. Use development for retrieval/prompt work. On validation, compare the fixed
   candidates; prespecify selection (primary macro-F1, invalid rate as a guard,
   latency as a tie-breaker), without consulting test labels. Define thresholds
   before scoring. Record exclusions and abstentions in all denominators.
5. Freeze a manifest containing model digest, prompt/schema/source hashes,
   evidence policy, label policy, token/decoding settings, validation dataset hash,
   selection rule and rationale. Freeze test membership and labels separately.
   No frozen selection manifest is created while selection is unperformed.
6. Run one selected model once on the independent test set. Reuse exact saved
   observations only; do not tune against failures or select another model using
   the test results. A revised system needs a new untouched test set.
7. Report sample size, accuracy, per-class precision/recall/F1, macro-F1, invalid
   rate, abstention, decisive coverage, source support and both baselines. Use
   paired repository/change-family cluster bootstrap intervals when enough
   independent clusters exist; disclose if too few clusters support inference.
   A binomial interval may be descriptive for independent cases, but does not
   fix correlation or annotation bias. Do not claim general >75% accuracy from
   the 12 authored diagnostics or from an interval on correlated cases.

External reviewers have not been contacted, and no reviewer labels are simulated.

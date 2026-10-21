# Interpretation and validity limits

## What the measurements establish

The saved experiments establish execution of the pinned retrieval methods,
versioned graph, controlled change workflows, local model calls and evidence
verification. Ranking arithmetic is independently recomputed from stored ranks.
The completed per-query model records contain actual output and token usage;
loading failures are kept separately and do not count as generated judgments.

The implemented efficiency controls are operational choices, not results of a
controlled speedup experiment. The full investigation is a bounded tool workflow.
Calling its stages agents does not demonstrate autonomous tool planning.

## What they do not establish

1. **Independent semantic grounding.** Matching an excerpt, citation identifier,
   line range and content hash proves that a quote came from the recorded source.
   It does not establish that the quote entails the model's conclusion. Strict
   JSON validation also does not measure hallucination. These fields remain null
   until independent annotation is available.
2. **Universal traceability superiority.** Different methods lead on different
   datasets and metrics. The exploratory graph setting helps some rankings and
   hurts others. Small RAG deltas do not support a significance claim, a universal
   benefit or a comparison with papers evaluated under different protocols.
3. **Consistency-classification improvement.** The sixty-call study returns
   UNCERTAIN for every configuration/case. Its 25% authored-label agreement equals
   the always-UNCERTAIN comparator. Richer endpoint coverage cannot substitute for
   correct final classification.
4. **Independent change-impact accuracy.** ChangeBench's expected affected sets
   are incomplete and authored alongside mutations. Predictions outside them are
   unjudged, not verified false positives. Finding an expected status somewhere
   in a report is a regression check, not single-label classification accuracy.
5. **Representative real evolution.** The twelve scenarios are correlated and
   use controlled edits. Declared baseline trace links seed some cases. SAFA's
   artifact-tree differences supply temporal structure, not independent code
   consistency labels. Neither replaces annotated natural software evolution.
6. **Unlinked-query behavior.** Retrieval evaluation excludes requirements with
   no resolved annotated link. It therefore cannot establish rejection quality
   for irrelevant or newly unimplemented requirements.
7. **Comparable RTMX cutoffs.** RTMX uses 22 resolved requirement-to-module links
   and seven existing test modules. Recall@10 must equal one when all candidates
   are returned. Missing modules and unresolved function-level labels preclude
   representing this as the original 24-function evaluation.
8. **Complete evidence exposure.** Embedding preprocessing, chunk limits,
   source-prefix excerpts, top-five model review and prompt budgets constrain
   what the model sees. Relevant implementations may occur outside that context.
   This is a plausible limitation, not an experimentally isolated explanation for
   every wrong judgment.
9. **Causal runtime comparisons.** Per-call timing retains cold-load cost and
   calls saved across runtime restarts. Study arms do not have balanced warmup.
   Report these as observations, not comparative speedups. Saved process RSS is
   a diagnostic snapshot rather than peak whole-system memory; no peak-memory or
   energy efficiency claim is supported. Zero local API charges exclude neither
   compute nor electricity costs.
10. **Production and platform readiness.** Static extraction can miss dynamic
    dispatch, reflection, ambiguous imports and nonliteral URLs. Some syntax
    failures are recorded. Browser checks, local Windows execution and public
    multiuser deployment are separate from successful Python tests/builds.

## Selection and leakage controls

SMOS, iTrust and eTour serve the stated train/validation/test roles. The learned
ranker was rejected because iTrust MAP did not exceed the strongest validation
retrieval baseline. Its eTour result did not determine retention. The frozen RAG
protocol uses annotated links for scoring, not prompt construction. Exact prompt,
schema, provider/model and prepared-data fingerprints govern cache reuse.

These controls do not prove that pretrained models never encountered public
benchmark material during training. Model training-data contamination is not
measured. The fixed graph weight is exploratory, not preregistered. Future tuning
must create a new protocol and preserve an untouched evaluation set rather than
silently replacing the completed results.

## Claim permitted by the current record

VIGILANT executes a reproducible change-aware investigation across repository
artifacts, ranks trace candidates, traverses structural relationships, and records
verifiable source evidence with conservative findings. The reported local-model
studies show mixed retrieval effects and no consistency-classification benefit.
Independent semantic and real-evolution evaluation remain necessary before a
broader reliability claim.

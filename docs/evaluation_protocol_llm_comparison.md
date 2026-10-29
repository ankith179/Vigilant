# VIGILANT evaluation protocol — draft before new predictions

Status: DRAFT / NOT FROZEN. This plan does not authorize relabeling, imply that the eight conditions are runnable, or report new results.

## Cohorts and freeze

1. Treat the original 12 authored cases as exposed development/regression cases. Preserve historical inputs, labels, model outputs and the SHA-256-bound case analysis. Recover revision identity and evidence; record missing Git objects as unavailable rather than reconstructing them as facts.
2. Up to 24 additional development cases require real revision pairs, provenance, reviewer judgments and a case-list freeze. Do not create synthetic gold or infer negative links from omissions. Report original and additional subsets separately; the combined result remains development.
3. For independent evaluation, determine repository-family overlap from the original cases, select disjoint families before mining, blind reviewers, retain individual judgments and adjudicate disagreements. Freeze the case list, all labels, policy, input/evidence exposure, pipeline, model, index and evaluation code before prediction. Keep held-out labels out of tuning and record exposure. Current family split is development only; no test cohort has been approved.

## Comparison and exposure

The planned A–H conditions and their current status are in `reports/experiment_matrix.md`. For every runnable condition record source and case hashes, exact revisions, index build and hash, prompt, model name and digest, schema, ruleset, tool and context budgets, seed where supported, environment, raw predictions, failures, time and cost. Conditions must share eligible cases and predeclared evidence availability; document differences needed to isolate each intervention. Do not describe an unavailable condition as a completed run.

The saved V047 11/12 replay is rules only and projects different authored legacy labels onto different axes. The historical Qwen3 8B 4/12 result uses a single-label diagnostic contract. These scores are not a controlled same-schema ablation and their difference cannot establish a model, retrieval or agent contribution. For a fresh paired comparison, freeze one rubric and mapping before generation, apply it identically to every condition, and save predictions before evaluating. Maintain the legacy projection as a separately identified regression view; it is not a substitute for reviewed per-axis labels.

## Metrics and missingness

Per axis, strict agreement is the number of matching predictions divided by all cases with a frozen reviewed label for that axis; a missing prediction is wrong and an abstention against a decisive label is wrong. An UNCERTAIN prediction may match a reviewed UNCERTAIN label. Publish denominators, class counts, confusion matrices, macro-F1, precision and recall when defined, decisive coverage and selective risk. A missing or unadjudicated axis is reported as unscored, with the reason; no post-result exclusions. Report Wilson intervals as descriptive and a repository-family cluster bootstrap only when enough independent families and a suitable sampling design exist.

Report retrieval Recall@k, MRR and nDCG with reference provenance, and precision only where negatives or completeness are independently reviewed. Retrieval scores do not establish traceability or end-to-end correctness. Evidence validity, semantic entailment, impact and obligation resolution require separately reviewed evidence and denominators. Report unknown and unsupported cases explicitly.

For end-to-end assurance, freeze the case-level rubric and critical gates before the run: relevant artifact and revision, trace, impact, consistency, test obligation, evidence support, appropriate uncertainty and actionable report. No label-only match can satisfy invalid evidence. Record each component gate separately. Until suitable reviewed references exist, end-to-end performance is NOT MEASURED.

## Reproducibility and status

Store immutable run IDs and source/configuration fingerprints, per-case raw and validated outputs, operation failures, aggregate metric code version and environment. Preserve prior runs. Report zero calls as zero calls, not as a model result. Local Ollama Qwen3 8B preflight on 28 October 2026 was BLOCKED (executable and model manifest absent). Independent labels and a frozen held-out cohort remain unavailable. No fresh LLM + rules score is established.

# Controlled consistency evaluation — proposed protocol

Status: NOT EXECUTED. This protocol is a follow-up design, not a result or a preregistration claim. Preserve the original E–I experiment unchanged.

## Decision unit and annotation

Use one repository change with fixed base/head revisions and a prespecified artifact scope as the decision unit. Recruit two reviewers who did not author the mutations, without showing model/rule predictions or expected labels. Give both reviewers the same repository revisions, relevant requirements and tests. Record their independent labels, source-line evidence and uncertainty reasons; adjudicate disagreements with a third reviewer or a documented joint review. Keep independent labels and adjudication separate. Report agreement and disagreement counts; use class-wise agreement and an appropriate chance-adjusted measure, acknowledging small samples.

The supplied worksheet contains case IDs and revisions only; reviewer fields remain blank. The 12 authored mutations are a pilot, not a sufficient basis for broad accuracy claims. Add naturally occurring changes from independent projects, sampled before examining outputs. Choose sample size using a prespecified precision or power target after estimating class prevalence; do not choose it to obtain a significant result. Split model/prompt development from held-out evaluation at the project level.

The existing status vocabulary mixes change/impact labels with semantic consistency. Before labeling, define a mutually exclusive decision taxonomy and precedence rules. Alternatively evaluate binary consistency with explicit abstention and separately annotate defect type. Do not force multi-label rule hypotheses into a single class using a post-hoc mapping optimized against labels. If the original four-class taxonomy is retained, publish an independent mapping policy before evaluation.

## Common evidence and configuration contract

Pin dataset commits, model revision, precision, decoding, output schema, prompt template, token budget and retrieval settings. Keep the allowed decision policy identical across model arms. Use the same cases and artifacts in every arm, with the same maximum input/output budgets. Do not give any arm expected traceability links derived from held-out ground truth. Log actual tokens, discarded evidence, latency, schema failures, aliases, raw text, normalized decisions and abstentions.

Prespecify and run these meaningful arms:

| Arm | Inputs and decision mechanism |
|---|---|
| Abstention baseline | Always UNCERTAIN; establishes label-prevalence agreement and zero coverage |
| Rules-only | Fixed rules; evaluate finding-level outputs or a prespecified common class mapping |
| LLM-only | Same task/change descriptor with no retrieved artifact excerpts |
| LLM + retrieval | Same generator and schema with retrieval-selected excerpts |
| LLM + retrieval + graph | Replace/add graph-selected excerpts within the same budget |
| LLM + retrieval + graph + temporal evidence | Add revision-paired evidence within the same budget |
| Full pipeline | Add rule-derived evidence or features under a prespecified policy, within the same budget |

Use paired cases, identical preprocessing and common budget caps. A changed input length or selection policy must be reported; equal maximum budgets alone do not imply identical information. Isolate prompt anchoring in a separate factor: compare the current uncertain example to a neutral schema or balanced examples with all other settings fixed. This tests a hypothesis suggested by the raw logs; it does not assume the example caused abstention. Check whether relevant excerpts were omitted by the six-excerpt/400-character cap. Do not raise confidence merely to force a decisive answer.

## Separate outcomes

1. Evidence validity: exact match of source revision, path, line range and content hash; citation-alias acceptance rate.
2. Impact coverage: recall against independently annotated impacted artifacts, plus precision where nonimpacted artifacts have actually been judged. Group findings with a shared cause; do not count duplicate symptoms as independent defects.
3. Semantic correctness: class confusion matrices, per-class precision/recall/F1 and macro-F1; non-uncertain coverage; accuracy among answered cases, undefined when no cases are answered; coverage–risk curves only with a justified confidence score. Label agreement alone is not calibrated confidence.
4. Runtime: warmed and cold runs, input/output token counts, hardware ownership/sharing, thread count, memory, per-case distribution and failures. Report local hardware/time cost separately from API charges.

## Retrieval and no-link extension

Independently adjudicate whether excluded unlinked requirements really have no valid target; absent annotation does not prove a negative. Prespecify a rejection threshold on development data. Evaluate false-positive rate on verified no-link requirements and retrieval ranking on linked requirements, reporting their populations separately. Include all 26 iTrust and one eTour exclusions only after suitable labels exist; extend RTMX at its validated module scope or resolve function annotations before changing the task.

## Analysis and execution gates

Report paired differences with intervals that reflect the independent sampling unit (project/change where feasible), rather than treating repeated configurations or correlated requirements as independent. Predefine primary metrics, contrasts, exclusions and any multiplicity handling before evaluating the held-out set. Deterministic reruns can test reproducibility but do not estimate prompt/model variability. Report failures and abstentions in denominators. Preserve all raw records and configuration hashes.

A live OmniRoute arm requires an available gateway, an explicitly free-eligible route with no paid fallback, and the same recorded protocol. Do not merge gateway failures into model-accuracy denominators. No live gateway result is present in this revision.

The protocol can be executed once independent labels and a runnable model/gateway configuration are available. New results must be written to a separate experiment directory and must not replace the original negative study.

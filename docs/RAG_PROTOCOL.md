# Linked-query RAG evaluation protocol

Protocol: `rag-trace-v2-frozen-2026-10-06`.
Executable specification: `scripts/run_rag_trace.py`.

## Population and comparator

Evaluate every requirement with at least one resolved gold link in the pinned
prepared datasets: SMOS (67), iTrust (105), eTour English (57), and the validated
RTMX module-level subset (22). These are 251 linked requirements, not a sample.
Unlinked requirements are excluded by the existing evaluation policy, so these
results do not measure rejection of requirements with no implementation.
RTMX has only seven candidate modules; its cutoff metrics must be interpreted
separately from the larger code corpora.

The comparator is the existing hybrid retrieval ranking: reciprocal rank fusion
with k=60 over lexical and pretrained embedding retrieval. Gold links are used
for scoring only. The model reviews the first five retrieved candidates.

## Fixed inputs and model

The local model is Qwen/Qwen2.5-1.5B-Instruct at revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, bfloat16, greedy decoding
(temperature 0), with at most 220 output tokens and a 3072-token input limit.
The pinned MiniLM encoder and retrieval configuration remain unchanged across
resumes. The provider rejects inputs exceeding its limit rather than silently
truncating them.

Each prompt contains a requirement prefix of at most 900 characters and five
source/test prefixes of at most 1100 characters. Evidence aliases are E0 for
the requirement and A1–A5 for candidates. A schema constrains each candidate
status to SUPPORTED, UNSUPPORTED or UNCERTAIN, plus evidence identifiers and a
short explanation. Full messages, raw output, token counts, elapsed time,
validation errors and model identity are retained for every generated call.

Only candidates classified SUPPORTED move to the front, in their original
relative order. Every other candidate preserves its original order. The model
cannot introduce a candidate outside the top five. Consequently, Recall@5 and
Recall@10 cannot improve through this reranking policy; order-sensitive metrics
such as MAP, MRR and nDCG can change. This is an exploratory reranking study,
not a reproduction of another paper or a semantic grounding assessment.

## Interruption and validity rules

A cached generation is reusable only when its dataset, prepared file, model,
provider source, prompt, schema, evidence, candidate aliases and decoding
configuration fingerprints match. A nonempty raw output and a positive output
token count are required. No-inference errors stop the run and are excluded
from effectiveness measurement. A generated but invalid response is retained
as an observed model failure and falls back to the original hybrid ranking.

Per-query files are written atomically. Replaced partial files are preserved
by content hash. After all linked queries in a dataset are processed, the
runner writes an immutable result and then an atomic completion pointer.
Partial datasets are progress records, not final comparison rows. An interrupted
process can safely resume without repeating already verified calls.

## Reporting and review

Run `python scripts/audit_results.py` to independently recompute stored retrieval
metrics. Run `python scripts/evaluate.py` only when all four RAG datasets are
complete; `--allow-partial` explicitly labels an incomplete synthesis.
Report paired hybrid and RAG scores per dataset, changed rankings, schema
validity, candidate-status counts and the original per-call runtimes. Resume
wall time is not directly comparable with a cold complete run.

Schema compliance and valid evidence identifiers do not establish semantic
entailment. Prefix evidence can omit relevant implementation. Independent
semantic review is still required, and no hallucination rate or improvement
claim follows merely from syntactically valid citations. Negative or unchanged
scores must be retained.

For bounded continuation, `--max-new-calls N` stops before the next uncached
query once N new generations have finished. Exact cached calls do not consume
that budget. A dataset is finalized only after all its linked queries are
available; reaching the budget never creates an incomplete final result.
`--max-new-calls 0` permits a no-new-LLM-generation resume check. This execution
control does not change the scientific protocol or invalidate matching caches.
A budget stop exits with status 75 (continuation needed), rather than success,
so a caller cannot mistake an incomplete batch for a completed evaluation.

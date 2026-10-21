# Paired consistency ablation protocol

The experiment compares five fixed configurations on the same twelve authored
change scenarios. It evaluates the decision returned by the local model and its
validator, separately from the deterministic rules' findings.

| Variant | Evidence and processing |
| --- | --- |
| E | Question alone, with no evidence excerpts |
| F | Six hybrid retrieval excerpts from the changed snapshot |
| G | Hybrid retrieval with structural graph context |
| H | Bounded inspection of changed symbols and graph neighbors, plus quote verification |
| I | Selected before/after excerpts and executed conservative rule hypotheses |

H uses a scripted bounded workflow; it is not a model autonomously selecting
tools. I changes both temporal evidence and rule availability. These comparisons
do not isolate every component's causal contribution. Graph construction can use
declared baseline trace relations. Expected consistency labels are used for
scoring after model inference; the graph's seeded traces remain an explicit
benchmark assumption.

The pinned local model is Qwen/Qwen2.5-1.5B-Instruct, revision
`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, CPU bfloat16, four PyTorch threads,
greedy decoding, at most 220 new tokens, and at most 3072 input tokens. JSON
generation is schema constrained. Validation requires matching decision and
consistency labels, supplied citation aliases, and evidence for a non-uncertain
decision. Invalid output becomes UNCERTAIN with the original error retained.

All variants use the same prompt and decoding settings. No prompt or parameter
was selected based on a preferred test result. The prompt explicitly offers an
UNCERTAIN example; this may bias a small model toward abstention and is a
limitation of this pilot, not a reason to hide the resulting uncertainty rate.

## Metrics and interpretation

- Status agreement is the fraction whose final label matches the authored
  expected label. The twelve cases are correlated and are not a population
  sample; do not present an independent generalization claim.
- Schema/citation validity measures syntactic and identifier checks. It does
  not measure whether the cited evidence entails the decision.
- Known endpoint recall uses the benchmark's incomplete expected affected set.
  It is not complete retrieval recall, and cannot support reliable precision or
  false-positive claims without more annotation.
- Uncertainty rate includes explicit abstention and failed output validation.
- Per-call time covers the recorded preparation/validation interval around the
  model call. Model loading affects the first new call. Reused observations keep
  their original timing; resumed-run wall time is reported separately.
- Semantic grounding, hallucination rate and independent finding correctness
  remain NOT MEASURED. Script tool success is not autonomous agent tool success.

## Interruption safety

Each observation is atomically written under `experiments/ablation-partial/`.
A completed run is also written to a new immutable directory under
`experiments/ablation/`. Replaced partial records are retained under `previous/`.

A cached observation is reused only when prompt messages, full supplied evidence,
model identity/revision/dtype, decoding settings and the current call fingerprint
match. Legacy saved calls additionally require actual generated tokens and raw
output. A schema-invalid generated response is still an observation and is reused.
An unsuccessful model load is not inference, is retried, and is never counted as
an LLM accuracy observation. Runtime failures stop the run before silently scoring
all later calls as uncertain.

The earlier run `20261006T143347-c5f1abef` contains loading failures only; its
`EXCLUDED.json` explicitly removes it from effectiveness comparison. Raw failure
logs remain available for diagnosis.

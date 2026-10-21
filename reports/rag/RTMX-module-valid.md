# RTMX-module-valid linked-query RAG result

Status: **COMPLETED and independently audited**.

Immutable run: `experiments/retrieval/20261007T210208-3f0803cc/results.json`. Split: external_test. Linked queries and actual generations: 22.

Model: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Protocol: `rag-trace-v2-frozen-2026-10-06`.

## Measured comparison

| Metric | Hybrid | Hybrid + RAG | Difference |
| --- | ---: | ---: | ---: |
| Precision@10 | 0.142857 | 0.142857 | +0.000000 |
| Micro Recall@10 | 1.000000 | 1.000000 | +0.000000 |
| F1@10 | 0.250000 | 0.250000 | +0.000000 |
| MRR | 0.751515 | 0.698485 | -0.053030 |
| MAP | 0.751515 | 0.698485 | -0.053030 |
| nDCG@10 | 0.813766 | 0.772834 | -0.040932 |
| Macro Recall@1 | 0.590909 | 0.545455 | -0.045455 |
| Macro Recall@5 | 1.000000 | 1.000000 | +0.000000 |
| Macro Recall@10 | 1.000000 | 1.000000 | +0.000000 |

The frozen method only reorders the first five hybrid candidates. Recall@5 and Recall@10 cannot change. These are descriptive paired results, with no statistical significance or general superiority claim.

## Model decisions and runtime

Changed rankings: 19/22. Candidate judgments: {"SUPPORTED": 70, "UNCERTAIN": 37, "UNSUPPORTED": 3}.

Runner schema validity: 1.000000. Independent full-schema validity: 1.000000. Mean recorded generation time: 67.28 seconds.

Generation times retain cold-load and resumed-call effects. Prefix evidence may omit relevant code. Valid JSON, known citation IDs and exact source excerpts do not establish semantic entailment. Independent grounding review and hallucination measurement remain unmeasured.

RTMX has seven candidate test modules and 22 resolved module-level links. Recall@10 is necessarily 1.0. This is not a 24-function traceability benchmark; its cutoff scores must not be pooled with the larger code corpora.

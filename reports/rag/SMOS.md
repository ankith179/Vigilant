# SMOS linked-query RAG result

Status: **COMPLETED and independently audited**.

Immutable run: `experiments/retrieval/20261007T104905-4064b602/results.json`. Split: train. Linked queries and actual generations: 67.

Model: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Protocol: `rag-trace-v2-frozen-2026-10-06`.

## Measured comparison

| Metric | Hybrid | Hybrid + RAG | Difference |
| --- | ---: | ---: | ---: |
| Precision@10 | 0.280597 | 0.280597 | +0.000000 |
| Micro Recall@10 | 0.180077 | 0.180077 | +0.000000 |
| F1@10 | 0.219370 | 0.219370 | +0.000000 |
| MRR | 0.567570 | 0.587471 | +0.019900 |
| MAP | 0.302557 | 0.306062 | +0.003506 |
| nDCG@10 | 0.309239 | 0.314535 | +0.005296 |
| Macro Recall@1 | 0.028341 | 0.030658 | +0.002317 |
| Macro Recall@5 | 0.114164 | 0.114164 | +0.000000 |
| Macro Recall@10 | 0.191626 | 0.191626 | +0.000000 |

The frozen method only reorders the first five hybrid candidates. Recall@5 and Recall@10 cannot change. These are descriptive paired results, with no statistical significance or general superiority claim.

## Model decisions and runtime

Changed rankings: 17/67. Candidate judgments: {"SUPPORTED": 42, "UNCERTAIN": 217, "UNSUPPORTED": 76}.

Runner schema validity: 1.000000. Independent full-schema validity: 1.000000. Mean recorded generation time: 70.82 seconds.

Generation times retain cold-load and resumed-call effects. Prefix evidence may omit relevant code. Valid JSON, known citation IDs and exact source excerpts do not establish semantic entailment. Independent grounding review and hallucination measurement remain unmeasured.

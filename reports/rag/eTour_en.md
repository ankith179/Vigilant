# eTour_en linked-query RAG result

Status: **COMPLETED and independently audited**.

Immutable run: `experiments/retrieval/20261007T171402-64fa98d8/results.json`. Split: test. Linked queries and actual generations: 57.

Model: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Protocol: `rag-trace-v2-frozen-2026-10-06`.

## Measured comparison

| Metric | Hybrid | Hybrid + RAG | Difference |
| --- | ---: | ---: | ---: |
| Precision@10 | 0.292982 | 0.292982 | +0.000000 |
| Micro Recall@10 | 0.542208 | 0.542208 | +0.000000 |
| F1@10 | 0.380410 | 0.380410 | +0.000000 |
| MRR | 0.725576 | 0.723237 | -0.002339 |
| MAP | 0.440553 | 0.442684 | +0.002131 |
| nDCG@10 | 0.528000 | 0.529339 | +0.001339 |
| Macro Recall@1 | 0.138729 | 0.137726 | -0.001003 |
| Macro Recall@5 | 0.388402 | 0.388402 | +0.000000 |
| Macro Recall@10 | 0.558716 | 0.558716 | +0.000000 |

The frozen method only reorders the first five hybrid candidates. Recall@5 and Recall@10 cannot change. These are descriptive paired results, with no statistical significance or general superiority claim.

## Model decisions and runtime

Changed rankings: 33/57. Candidate judgments: {"SUPPORTED": 110, "UNCERTAIN": 121, "UNSUPPORTED": 54}.

Runner schema validity: 1.000000. Independent full-schema validity: 1.000000. Mean recorded generation time: 37.93 seconds.

Generation times retain cold-load and resumed-call effects. Prefix evidence may omit relevant code. Valid JSON, known citation IDs and exact source excerpts do not establish semantic entailment. Independent grounding review and hallucination measurement remain unmeasured.

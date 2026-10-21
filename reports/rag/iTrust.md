# iTrust linked-query RAG result

Status: **COMPLETED and independently audited**.

Immutable run: `experiments/retrieval/20261007T163255-0dfbb833/results.json`. Split: validation. Linked queries and actual generations: 105.

Model: `Qwen/Qwen2.5-1.5B-Instruct` at `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Protocol: `rag-trace-v2-frozen-2026-10-06`.

## Measured comparison

| Metric | Hybrid | Hybrid + RAG | Difference |
| --- | ---: | ---: | ---: |
| Precision@10 | 0.118095 | 0.118095 | +0.000000 |
| Micro Recall@10 | 0.433566 | 0.433566 | +0.000000 |
| F1@10 | 0.185629 | 0.185629 | +0.000000 |
| MRR | 0.472694 | 0.464758 | -0.007937 |
| MAP | 0.306828 | 0.304309 | -0.002519 |
| nDCG@10 | 0.372252 | 0.369117 | -0.003135 |
| Macro Recall@1 | 0.126296 | 0.116772 | -0.009524 |
| Macro Recall@5 | 0.388450 | 0.388450 | +0.000000 |
| Macro Recall@10 | 0.470023 | 0.470023 | +0.000000 |

The frozen method only reorders the first five hybrid candidates. Recall@5 and Recall@10 cannot change. These are descriptive paired results, with no statistical significance or general superiority claim.

## Model decisions and runtime

Changed rankings: 60/105. Candidate judgments: {"SUPPORTED": 228, "UNCERTAIN": 202, "UNSUPPORTED": 95}.

Runner schema validity: 1.000000. Independent full-schema validity: 1.000000. Mean recorded generation time: 42.23 seconds.

Generation times retain cold-load and resumed-call effects. Prefix evidence may omit relevant code. Valid JSON, known citation IDs and exact source excerpts do not establish semantic entailment. Independent grounding review and hallucination measurement remain unmeasured.

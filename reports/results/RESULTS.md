# VIGILANT measured results

Status: COMPLETED. Missing complete RAG datasets: none.

## Dataset statistics

| Dataset | Split | Requirements | Linked queries | Targets | Links |
| --- | --- | --- | --- | --- | --- |
| SMOS | train | 67 | 67 | 100 | 1044 |
| iTrust | validation | 131 | 105 | 226 | 286 |
| eTour_en | test | 58 | 57 | 116 | 308 |
| RTMX-module-valid | external_test | 22 | 22 | 7 | 22 |

Only queries with an annotated link contribute to ranking metrics. RTMX uses seven existing test modules and 22 requirements; two missing modules and unresolved function labels prevent a comparable 24-function evaluation.

## Traceability performance

| Dataset | Method | P@10 | R@10 | F1@10 | MRR | MAP | Macro R@1 | Macro R@5 | Macro R@10 | nDCG@10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMOS | TF-IDF | 0.2910 | 0.1868 | 0.2275 | 0.6999 | 0.2924 | 0.0364 | 0.1247 | 0.1971 | 0.3530 |
| SMOS | BM25 | 0.2910 | 0.1868 | 0.2275 | 0.6535 | 0.2979 | 0.0324 | 0.1135 | 0.1984 | 0.3334 |
| iTrust | TF-IDF | 0.1324 | 0.4860 | 0.2081 | 0.4439 | 0.3160 | 0.1030 | 0.4004 | 0.5124 | 0.3860 |
| iTrust | BM25 | 0.1429 | 0.5245 | 0.2246 | 0.5356 | 0.3787 | 0.1686 | 0.4436 | 0.5337 | 0.4470 |
| eTour_en | TF-IDF | 0.2526 | 0.4675 | 0.3280 | 0.6807 | 0.4102 | 0.1229 | 0.3762 | 0.4899 | 0.4753 |
| eTour_en | BM25 | 0.2035 | 0.3766 | 0.2642 | 0.5824 | 0.3074 | 0.0761 | 0.3090 | 0.4038 | 0.3704 |
| RTMX-module-valid | TF-IDF | 0.1429 | 1.0000 | 0.2500 | 0.7894 | 0.7894 | 0.6364 | 1.0000 | 1.0000 | 0.8428 |
| RTMX-module-valid | BM25 | 0.1429 | 1.0000 | 0.2500 | 0.7606 | 0.7606 | 0.6364 | 1.0000 | 1.0000 | 0.8194 |
| SMOS | MiniLM | 0.2537 | 0.1628 | 0.1984 | 0.4568 | 0.2859 | 0.0242 | 0.0941 | 0.1776 | 0.2689 |
| SMOS | Hybrid | 0.2806 | 0.1801 | 0.2194 | 0.5676 | 0.3026 | 0.0283 | 0.1142 | 0.1916 | 0.3092 |
| iTrust | MiniLM | 0.0905 | 0.3322 | 0.1422 | 0.3394 | 0.2061 | 0.0665 | 0.2871 | 0.3631 | 0.2658 |
| iTrust | Hybrid | 0.1181 | 0.4336 | 0.1856 | 0.4727 | 0.3068 | 0.1263 | 0.3885 | 0.4700 | 0.3723 |
| eTour_en | MiniLM | 0.2702 | 0.5000 | 0.3508 | 0.7113 | 0.4492 | 0.1499 | 0.3589 | 0.4950 | 0.5011 |
| eTour_en | Hybrid | 0.2930 | 0.5422 | 0.3804 | 0.7256 | 0.4406 | 0.1387 | 0.3884 | 0.5587 | 0.5280 |
| RTMX-module-valid | MiniLM | 0.1429 | 1.0000 | 0.2500 | 0.6795 | 0.6795 | 0.5000 | 1.0000 | 1.0000 | 0.7592 |
| RTMX-module-valid | Hybrid | 0.1429 | 1.0000 | 0.2500 | 0.7515 | 0.7515 | 0.5909 | 1.0000 | 1.0000 | 0.8138 |
| SMOS | Hybrid + KG | 0.2746 | 0.1762 | 0.2147 | 0.5419 | 0.2965 | 0.0257 | 0.1063 | 0.1870 | 0.2953 |
| iTrust | Hybrid + KG | 0.1238 | 0.4545 | 0.1946 | 0.4318 | 0.2958 | 0.0989 | 0.3826 | 0.4934 | 0.3677 |
| eTour_en | Hybrid + KG | 0.2860 | 0.5292 | 0.3713 | 0.7471 | 0.4744 | 0.1664 | 0.3956 | 0.5438 | 0.5415 |
| SMOS | Hybrid + RAG | 0.2806 | 0.1801 | 0.2194 | 0.5875 | 0.3061 | 0.0307 | 0.1142 | 0.1916 | 0.3145 |
| iTrust | Hybrid + RAG | 0.1181 | 0.4336 | 0.1856 | 0.4648 | 0.3043 | 0.1168 | 0.3885 | 0.4700 | 0.3691 |
| eTour_en | Hybrid + RAG | 0.2930 | 0.5422 | 0.3804 | 0.7232 | 0.4427 | 0.1377 | 0.3884 | 0.5587 | 0.5293 |
| RTMX-module-valid | Hybrid + RAG | 0.1429 | 1.0000 | 0.2500 | 0.6985 | 0.6985 | 0.5455 | 1.0000 | 1.0000 | 0.7728 |

P@10, R@10 and F1@10 are micro-averaged over predicted links. The three Macro R columns average each query's recall, and can differ from micro recall. MRR and MAP use the full target ranking. RTMX R@10 is necessarily 1.0 because there are only seven candidates. No cross-dataset pooled superiority claim is made. Figures use completed runs only. Missing methods have no bar.

## RAG scope

| Dataset | Queries | Changed rankings | Runtime validation | Full schema validation | Uncertain candidate judgments | Mean generation seconds |
| --- | --- | --- | --- | --- | --- | --- |
| SMOS | 67 | 17 | 1.0000 | 1.0000 | 217 | 70.82 |
| iTrust | 105 | 60 | 1.0000 | 1.0000 | 202 | 42.23 |
| eTour_en | 57 | 33 | 1.0000 | 1.0000 | 121 | 37.93 |
| RTMX-module-valid | 22 | 19 | 1.0000 | 1.0000 | 37 | 67.28 |

The frozen RAG method reviews only five candidates from hybrid retrieval. Only SUPPORTED candidates move forward. Recall at 5 and 10 cannot change from reranking within the first five positions. Prefix excerpts can omit relevant implementations. Valid JSON and known citation IDs do not establish semantic entailment. Partial generation files are not completed dataset evaluations.

Runtime validation is the runner's recorded decision check. Full schema validation is a separate audit of every required property, enum and length bound. Neither is a semantic grounding or hallucination score. Generation times retain their original observations across resumes and include cold-load effects where applicable.

## Controlled change analysis

| Case | Expected label | Label present | Known hits | Known misses | Outside partial oracle |
| --- | --- | --- | --- | --- | --- |
| 01-requirement-changed | POTENTIAL_INCONSISTENCY | True | 1 | 0 | 0 |
| 02-requirement-added | UNCERTAIN | True | 0 | 0 | 0 |
| 03-code-changed | POTENTIAL_INCONSISTENCY | True | 1 | 0 | 29 |
| 04-code-deleted | BROKEN_TRACE | True | 1 | 0 | 29 |
| 05-test-changed | UNCERTAIN | True | 1 | 0 | 10 |
| 06-test-deleted | MISSING_TEST | True | 1 | 0 | 10 |
| 07-frontend-changed | UNCERTAIN | True | 0 | 0 | 0 |
| 08-api-changed | POTENTIAL_INCONSISTENCY | True | 5 | 0 | 28 |
| 09-backend-changed | POTENTIAL_INCONSISTENCY | True | 1 | 0 | 20 |
| 10-consumer-changed | BROKEN_TRACE | True | 1 | 4 | 3 |
| 11-implementation-test-drift | POTENTIAL_INCONSISTENCY | True | 1 | 0 | 29 |
| 12-requirement-test-drift | POTENTIAL_INCONSISTENCY | True | 1 | 0 | 0 |

All labels are authored and the affected sets are partial. Outside-oracle predictions are not verified false positives. Expected-status presence is a regression check, not independent classification accuracy. Seeded trace relations evaluate maintenance rather than initial recovery.

## Local model ablation

| Variant | Calls | Agreement | Uncertainty | Citation validity | Known endpoint recall | Mean seconds |
| --- | --- | --- | --- | --- | --- | --- |
| E | 12 | 0.2500 | 1.0000 | 1.0000 | 0.0000 | 12.1653 |
| F | 12 | 0.2500 | 1.0000 | 0.9167 | 0.0000 | 18.6228 |
| G | 12 | 0.2500 | 1.0000 | 0.9167 | 0.2000 | 19.1403 |
| H | 12 | 0.2500 | 1.0000 | 0.9167 | 0.3200 | 18.5572 |
| I | 12 | 0.2500 | 1.0000 | 0.8333 | 0.7200 | 20.4021 |

All five variants produce UNCERTAIN for every case. The 0.25 agreement equals always-UNCERTAIN. There is no demonstrated gain in model consistency classification. Five generated responses fail citation validation and become UNCERTAIN. Known endpoint recall describes the partial authored oracle. Independent semantic grounding and hallucination rate remain unmeasured. Cold model loading and resumed calls make these times unsuitable for a causal speed comparison.

## Ranker selection

The trained ranker was rejected by its validation rule: its iTrust MAP did not exceed BM25 MAP 0.3787. eTour test performance was not used to retain it. The fixed 0.15 graph weight is exploratory, not a preregistered confirmatory result.

## Full pipeline and SAFA

{
  "tool_stages": 12,
  "changed_artifact_records": 11,
  "impact_candidates": 33,
  "verified_excerpts": 24,
  "rule_findings": 15,
  "model_status": "UNCERTAIN",
  "model_seconds": 25.104550343000028,
  "metrics": {
    "tool_execution_success": 1.0,
    "quote_verification_rate": 1.0,
    "model_schema_valid": true,
    "semantic_grounding_rate": null,
    "seconds": 33.64662969999995
  }
}

The full API-change pipeline generates 15 rule findings concerning a shared route-renaming cause, not 15 independent confirmed defects. The final local-model decision is UNCERTAIN. SAFA compares artifact-tree versions; it supplies no independent code-consistency accuracy labels.

## Verification and provenance

Independent recomputation checked 23 method rows and 1484 query metric rows. Original experiment files remain unchanged.

| Record | Immutable input |
| --- | --- |
| lexical | experiments/retrieval/20261006T020645-ee4c5e32/results.json |
| semantic | experiments/retrieval/20261006T021326-432d54b3/results.json |
| graph | experiments/retrieval/20261006T142659-bc349a3f/results.json |
| ranker | experiments/ranker/20261006T142709-dea10c63/results.json |
| changebench | experiments/changebench/20261006T143016-f81c6507/results.json |
| ablation | experiments/ablation/20261006T194639-30694b4d/results.json |
| pipeline | experiments/pipeline/20261006T195007-e56e6b8d/results.json |
| safa | experiments/safa/20261006T142403-c681a243/results.json |
| rag_SMOS | experiments/retrieval/20261007T104905-4064b602/results.json |
| rag_iTrust | experiments/retrieval/20261007T163255-0dfbb833/results.json |
| rag_eTour_en | experiments/retrieval/20261007T171402-64fa98d8/results.json |
| rag_RTMX-module-valid | experiments/retrieval/20261007T210208-3f0803cc/results.json |

SHA-256 values, raw ranks, exact input populations and unrounded metrics are in summary.json. Historical user-reported results use different policies and are excluded from these comparisons.

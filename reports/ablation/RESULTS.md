# Local model consistency ablation

This table reports actual generated responses from the pinned Qwen 1.5B model. It measures agreement with authored scenario labels, not independent accuracy.

Source: `experiments/ablation/20261006T194639-30694b4d/results.json`. Calls: 60; reused exact saved inference: 17; newly generated: 43.

| Variant | Cases | Correct | Status agreement | Schema/citation valid | UNCERTAIN | Known endpoint recall | Mean seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E | 12 | 3 | 0.250 | 1.000 | 1.000 | 0.000 | 12.17 |
| F | 12 | 3 | 0.250 | 0.917 | 1.000 | 0.000 | 18.62 |
| G | 12 | 3 | 0.250 | 0.917 | 1.000 | 0.200 | 19.14 |
| H | 12 | 3 | 0.250 | 0.917 | 1.000 | 0.320 | 18.56 |
| I | 12 | 3 | 0.250 | 0.833 | 1.000 | 0.720 | 20.40 |

Variant definitions:
- E: LLM only.
- F: LLM + hybrid RAG.
- G: LLM + RAG + KG.
- H: LLM + RAG + KG + bounded investigation.
- I: Full VIGILANT with temporal evidence and rules.

An always-UNCERTAIN comparator agrees with 25.0% of these authored labels. The best observed variant agrees with 25.0%.

**This pilot does not demonstrate improved consistency classification from the local model or richer evidence.** The deterministic rule findings must remain separate from model effectiveness claims.

Exact evidence quotes and identifiers were checked. Semantic entailment and hallucination rate have not been independently measured. Validation failures are retained as UNCERTAIN. Loading-only failures are excluded, including the historical run marked EXCLUDED.json.

The cases are correlated, the endpoint labels are incomplete, and the graph contains declared baseline traces. H is scripted investigation. I changes temporal context and rules together. Per-call timings retain their original measurements for reused calls; cold-load cost is not balanced between arms. No statistical significance claim is made.

See `docs/ABLATION_PROTOCOL.md` and the raw rows for prompts, evidence, full responses, validation errors, tokens, model revision and per-call timing. `review-packets.json` contains unfilled review fields and omits variant names and authored expected labels; `review-key.json` preserves the mapping separately. These are annotation materials, not completed independent validation.

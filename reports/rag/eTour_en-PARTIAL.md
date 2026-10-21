# eTour English RAG progress — historical checkpoint

Superseded by the completed, audited result in `reports/rag/eTour_en.md` and
`experiments/retrieval/20261007T171402-64fa98d8/results.json`.

Checkpoint: 2026-10-07T16:54:47+00:00.

- Completed actual generations: 30 of 57 linked queries.
- Remaining: 27 queries.
- Batch exit status: 75, the expected bounded-continuation signal.
- Runner validation: 30/30 structurally valid.
- Independent full-schema audit: 30/30 valid.
- Candidate judgments across 150 reviewed candidates: 56 SUPPORTED, 39 UNSUPPORTED and 55 UNCERTAIN.
- Mean recorded generation time: 37.38 seconds. This is not a controlled latency comparison.
- Runtime/no-inference failures counted as effectiveness observations: 0.

No eTour traceability metric is reported from this partial population. The
dataset receives an immutable result, paired baseline comparison and metric
audit only after all 57 linked queries are available. Do not tune the method
using these partial observations. Schema validity and correct evidence IDs do
not establish semantic grounding; independent review remains pending.

Resume with:

```text
python scripts/run_rag_trace.py --datasets eTour_en --max-new-calls 27
```

The first 30 exact calls will be reused and do not consume the new-call budget.

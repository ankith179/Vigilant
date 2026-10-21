# iTrust RAG progress — historical checkpoint

Superseded by the completed, audited result in `reports/rag/iTrust.md` and
`experiments/retrieval/20261007T163255-0dfbb833/results.json`.

Checkpoint: 2026-10-07T16:21:17+00:00.

- Completed actual generations: 90 of 105 linked queries.
- Remaining: 15 queries.
- Batch exit status: 75, the expected bounded-continuation signal.
- Runner validation: 90/90 structurally valid.
- Independent full-schema audit: 90/90 valid.
- Candidate judgments across 450 reviewed candidates: 195 SUPPORTED, 75 UNSUPPORTED and 180 UNCERTAIN.
- Mean recorded generation time: 42.43 seconds. This includes resumed runtime contexts and is not a controlled latency comparison.
- Runtime/no-inference failures counted as effectiveness observations: 0.
- Resume verification: a prior zero-new-call check reused the first 30 exact
  calls and stopped before query 31. After a temporary-runtime interruption at
  44/105, a bounded run reused all 44 exact calls and generated 16 new calls.
  The latest bounded run then reused all 60 exact calls and generated 30 new
  calls, stopping at 90/105 as configured.

No iTrust traceability metric is reported from this partial population. The
dataset receives an immutable result, paired baseline comparison and metric
audit only after all 105 linked queries are available. Do not tune the method
using these partial observations. Schema validity and correct evidence IDs do
not establish semantic grounding; independent review remains pending.

Resume with:

```text
python scripts/run_rag_trace.py --datasets iTrust --max-new-calls 15
```

The first 90 exact calls will be reused and do not consume the new-call budget.

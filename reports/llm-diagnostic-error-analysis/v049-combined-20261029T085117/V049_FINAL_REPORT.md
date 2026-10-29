# V049 Combined Replay — Final Report

**Run:** `v049-combined-20261029T085117`  
**Status:** `COMPLETED`  
**Population:** 12-case development/regression set with authored labels; not an independent test cohort.

## Result

The combined VIGILANT pipeline matched **11 of 12 authored labels (91.67%)** under the preregistered V047 axis projection. This meets the requested 11/12 regression target. It is authored-label agreement on this small regression set, not independent or generalizable system accuracy. A nominal Wilson 95% interval is 64.6%–98.5%; it does not account for possible dependence among cases and should not be interpreted as a population guarantee.

| Axis | Matches | Cases | Result |
|---|---:|---:|---:|
| Consistency | 9 | 9 | 100% observed agreement |
| Trace | 2 | 2 | 100% observed agreement |
| Test obligation | 0 | 1 | 0% observed agreement |
| Frozen projected case result | 11 | 12 | 91.67% authored-label agreement |

The only mismatch is **case 06 — test deleted**: the pipeline returned `UNVERIFIED`; the authored label `MISSING_TEST` was projected to `UNSATISFIED`. The available evidence did not establish an explicit test obligation, so the conservative result remained unverified.

## Configuration and execution

- Rules: existing V3 deterministic rules and LLM guard.
- Retrieval: existing BM25 RAG over exact HEAD snapshots, `k=8`; graph retrieval disabled; labels were not exposed to retrieval.
- Model: local Ollama `qwen3:1.7b`, Q4_K_M, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
- Generation: temperature 0, seed 42, context 8192, maximum 512 generated tokens, thinking disabled.
- The run recorded 37 model calls and 10 model scopes used. The evaluation status counters recorded 10 `COMPLETED` and 11 `BUDGET_EXHAUSTED` entries; therefore this does not show that every semantic scope completed an LLM assessment.
- The model-plus-RAG contribution is **not isolated** by this run. A prior rules-only replay was reported at the same 11/12, so this result does not establish an LLM or RAG uplift.

## Integrity and validation

- The frozen historical `case-analysis.json` SHA-256 remained `c29b442b72950e4f8a8721c843a1ba40caf4a0dd32e51941fc64715d2a20a864`.
- All eight preregistered source-file hashes matched the current source files in the completed-run audit.
- The completed-run audit passed with 12 predictions and 10 raw output scope records.
- No full test suite was run as part of this inference run. The earlier V045 focused test report (62 passed) is a separate historical result.

## Claims and remaining status

| Claim | Status |
|---|---|
| Combined rules + BM25 RAG + local Qwen replay executed | `IMPLEMENTED` / `MEASURED` |
| 11/12 authored-label regression target reached | `MEASURED` |
| LLM or RAG improves over rules-only | `NOT ESTABLISHED` |
| Independently adjudicated performance | `NOT MEASURED` |
| 95% independent/overall research acceptance | `NOT ESTABLISHED` |
| Release readiness | `NOT ESTABLISHED` |

The 12 cases informed system development and are regression evidence only. Independent reviewer labels remain unavailable. Do not describe 91.67% as independent, representative, or overall accuracy.

## Reproducibility artifacts

`evaluation.json`, `predictions.json`, `preregistration.json`, `raw_outputs.jsonl`, `execution_log.jsonl`, and `call_progress.jsonl` are the run records. The preregistration records the model digest, configuration, snapshot and case-manifest hashes, and source hashes. The original historical diagnostic remains unchanged.

# Current execution update — 24 October 2026

Roadmap dates are not waiting periods. The latest bounded work and exact remaining acceptance are in COMPLETION_STATUS_20261024.md. Native adapters, comparison chat, review intake, 145 tests and updated technical drafts are included. Human annotation, final freeze and broader engineering acceptance remain incomplete. The following entries preserve the earlier plan and its historical status.

---

# Improvement roadmap

The supplied audit and master prompt number later phases differently. This roadmap names each workstream explicitly. It preserves the architecture and scopes this release to preservation, reproducible correctness fixes and offline input-review preparation.

| Workstream | Status after this release | Required acceptance before completion |
| --- | --- | --- |
| Preservation / baseline | Completed for this Linux working copy | Prior archive retained, frozen hashes match, SQLite integrity, tests/build and saved metric/provenance checks recorded. Native Windows acceptance remains separate. |
| Correctness pass | Completed for C01–C04 | Regression failures recorded before fixes; 121 tests pass; no history rewritten. Other audit findings remain open. |
| Input and label audit | Automated input audit completed; human review blocked | 12 development packets independently reviewed twice; disagreement adjudication; contract/evidence sufficiency and semantic citation review; preserve original labels separately. |
| Controlled evidence experiment | Offline packet comparison completed; inference ablation NOT_RUN | Freeze reviewed development cases and candidate policies; identical model/digest/generation settings and budget; compare only a predeclared component; save every request/output/failure. No uncontrolled historical reruns. |
| Retrieval comparison | Bounded contextual-bandit comparison completed; broader study remains planned | Training-only LinUCB over frozen TF-IDF/BM25/embedding/hybrid arms underperformed fixed validation/test baselines and is retained. Graph expansion/reranking, latency/memory and paired repository-level uncertainty remain. |
| Traceability / impact / contracts | Planned | Per-edge origin, revision, resolution and ambiguity exposed; exact candidate path; explicit contract checks; deduplication by finding identity; false-positive and unsupported-syntax fixtures. |
| Chat hardening | Planned | Structured intents, selected run/base/head/finding state; scope changes invalidate prior context; graph path tools; grounded test suggestions clearly separated from executed tests. |
| Language coverage | Planned | Improve supported Python/Java/JS/TS adapters; inventory exclusions first; C++ compile database/Clang and Swift compiler/toolchain integration only when available and tested. Unsupported features must remain unknown. |
| Independent benchmark and freeze | Blocked on annotation and data | Actual repository changes, independent reviewers and adjudication; repository/change-family-disjoint splits; frozen selection; untouched test. Authored diagnostics stay in development. |
| Release readiness | Partial | Current package tests/backup checks; native Windows installation/browser test, dependency vulnerability/license review, and measured RAM/VRAM remain open for the intended deployment. |

## Next executable sequence

1. Distribute only the blinded development packets and rubric to two reviewers. Record their identities and prior exposure. Do not supply model answers or authored labels before their independent submissions.
2. Adjudicate ambiguous contracts and insufficient evidence. Keep a versioned adjudication record; do not overwrite archived labels or scores. The 79 real-change candidates are a separate unlabelled queue, not a completed benchmark.
3. Review the four empty bounded packets. Compare smaller verified excerpt windows, metadata allocation and exact-token budgeting under a frozen development protocol. Preserve complete pairs and report omissions; do not silently truncate source.
4. Run one controlled development inference experiment when the local runtime/model digest and reviewed input protocol are available. Record invalids and abstentions; do not select solely by accuracy on the 12 authored cases.
5. Implement graph/chat/language improvements against the failure categories established by that review, with small reversible patches.
6. Freeze pipeline selection and collect a disjoint, independently reviewed test set before measuring the 91% target.

No fine-tuning, larger-model purchase or general agent framework is justified by the current evidence. None can guarantee the requested correctness threshold.

## Detailed audit v2 progress

Revision-isolated graph paths, inventory coverage/API/UI, nested-call/fetch fixes, typed report-chat context/support metadata, strict scorer inputs and the 32-case annotation pilot are implemented. The pilot review, new controlled model/retrieval experiments, compiler adapters, full runtime obligation integration and independent held-out target measurement remain open. See AUDIT_V2_RESOLUTION.md for the issue-by-issue evidence.

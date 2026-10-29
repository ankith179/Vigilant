# Evidence-first investigations

Release: 23 October 2026. This release combines the recovered full project with
GitHub commit `7eba731b99dc63c66e2872da1fcc8b723ce30945` and the fixes recorded in
`reports/evidence-first-20261022/BUG-AUDIT.md`. Historical reports retain their
original policies and conclusions; new code does not retroactively rescore them.

## Authority and execution

1. Resolve immutable base/head Git revisions. Parse artifacts and collect actual
   added, deleted and modified files, symbols and spans.
2. Build versioned graph relationships with explicit provenance. Rules operate
   on these facts before retrieval or model inference. Heuristic edges are
   candidates, not established semantic trace links.
3. Retrieve relevant excerpts, retaining base/head roles. Verify new investigation
   excerpts independently against Git blobs, hashes, identities and line ranges.
   Verification errors fail the stage; an empty denominator produces no rate.
4. Optionally ask a selected LLM to interpret ambiguity within a bounded evidence
   packet. The response is advisory, schema/citation checked and stored separately.
   It cannot overwrite deterministic findings. Invalid answers remain invalid.
5. Save the analysis contract, policies, coverage gaps, evidence and measured
   trajectory. Chat can explain this saved result without another model call.

`agents/workflow.py` is a fixed, bounded pipeline. Its named stages are not
autonomous collaborating agents. The knowledge graph remains a core component.
Reverse dependency traversal proposes affected callers/tests, with containment
excluded by default. A graph path does not prove a behavioral impact.

## Graph and parser policies

New graph records use `typed-v2`, exact endpoint revisions/spans/hashes and
`DECLARED`, `STATICALLY_RESOLVED` or `HEURISTIC` provenance. Numeric graph scores
are ordering priorities; rule confidence is unset rather than an invented
probability. Requirement relationships are normalized code→requirement and
test→requirement; test→code links remain distinct.

Python uses AST parsing; Java, JavaScript and TypeScript use Tree-sitter.
Same-file call resolution is conservative. Unknown receivers and cross-module
name matches do not create definite CALLS edges. Full compiler symbol resolution,
dynamic dispatch, reflection, C++, Swift, C#, Go and Rust adapters remain outside
the verified scope. Parse failures and unsupported files are coverage gaps.

Artifact versions are immutable. Existing imports are reused, so parser fixes do
not silently change old snapshots. To index an existing repository with the new
parser identity, use a new project scope:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/reindex_repository.py C:\path\to\repo --project my-project --revisions BASE_SHA HEAD_SHA
```

The helper appends `::syntax-import-calls-v2` to the project identity. Select the
new repository scope for subsequent investigations. It preserves old evidence.

## Chat

Open Chat, select repository and snapshot, then select an investigation. Ask
about changes, findings, impact candidates, source evidence or suggested tests.
The optional finding selector narrows the explanation. “Open exact source” opens
the cited artifact version. The server validates project, repository, run,
base/head and finding scope; unsupported requests return INSUFFICIENT_EVIDENCE.
Contradictory saved definitive rule/model verdicts require review.

`/api/report-chat` explains saved records and checks quotations against stored
artifact versions. `/api/chat` and `/api/rag` search stored snapshots and disclose
that same verification scope. They do not independently reread Git on every
question. New investigations do reread Git. Citation fidelity is distinct from
semantic entailment; historical findings may have been produced by older rules.
Chat history remains in the browser session; chat cannot modify repositories.

## Local operation and resource limits

Keep existing Windows work intact. Extract the delivered ZIP into a separate
directory first; do not overwrite an active database or replace a newer Windows
database with a packaged historical snapshot. Runtime binaries, model weights,
virtual environments and node_modules are reproducible dependencies excluded
from the archive. Existing local setup instructions and PowerShell launchers
remain in place. The API entry point is now:

```text
python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000
```

After reboot, use `Start-Ollama-Local.ps1` and `Start-VIGILANT-Local.ps1` in separate
terminals. Models stay local and one at a time. Ollama unload-after-call remains
intentional for constrained VRAM. The evidence wrapper budgets complete excerpts,
records aliases/input hashes and rejects missing or overflowing token telemetry;
byte bounds do not independently prove server tokenizer/template behavior.

Embeddings default to CPU. `VIGILANT_EMBEDDING_DEVICE=auto` or `cuda` is an explicit
option; this release did not validate a GPU run. Public repository clones are
staged, time-limited and monitored for size, then installed only on success.
The monitored storage cap can briefly overshoot between checks. Keep the service
on loopback; network deployment needs the existing access-token configuration.

## What establishes the requested 91%

See `QUALITY_TARGET.md`. Software checks, source fidelity, retrieval metrics and
semantic correctness measure different things. No overall 91% correctness claim
is established by this release, and no new model inference was run to produce it.

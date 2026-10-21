# VIGILANT with OmniRoute: free-access setup

OmniRoute is an MIT-licensed gateway, not an LLM or an unlimited token grant.
VIGILANT now supports its OpenAI-compatible local endpoint. An eligible upstream
provider account and free quota are still needed. This mode uses online inference
unless you connect a local backend such as Ollama. No paid account, credit purchase,
or premium-model entitlement is included.

## Suggested first candidate

Try **GPT-OSS 120B through Groq's free plan**, if it is available in your account's
current model/limits page. It is a candidate for validation, not the proven best
VIGILANT model. Groq documents reasoning, tool use and JSON support for
`openai/gpt-oss-120b`; OmniRoute's provider-qualified route identifier may differ.
Copy the exact route from the connected gateway model list rather than guessing it.

Use a free account without paid billing enabled. Connect only free-eligible routes
in the dedicated gateway; disable model fallback/combos and prompt compression for
research runs. VIGILANT has no automatic client fallback or retry. Its allowlist
records the operator's eligibility check; it cannot independently verify provider
billing or override the gateway administrator's configuration. Stop when quota is
exhausted and resume after the provider's legitimate reset. Do not rotate accounts
to bypass limits.

## Windows steps

1. Complete `Setup-Windows.ps1` in your VIGILANT folder. Node.js 24 is recommended
   for the pinned OmniRoute npm package (3.8.51, verified in npm on 2026-10-13).
2. In one PowerShell window run `./Start-OmniRoute.ps1`. The first run downloads
   the pinned gateway package. Open http://localhost:20128.
3. Connect your eligible free provider through its documented account/API-key
   flow. Leave providers marked `tos: avoid` excluded. Keep paid routes and
   fallbacks disabled. Free availability and quotas can change.
4. Copy the gateway key from its Endpoints page. This is different from the
   upstream Groq key: the upstream key belongs in OmniRoute, not VIGILANT.
5. In another PowerShell window, from the project folder, run:

```powershell
.\Start-VIGILANT-OmniRoute.ps1 -Model 'EXACT_PROVIDER/MODEL_FROM_YOUR_GATEWAY'
```

The launcher privately prompts for the gateway key and performs a read-only
catalog check before starting VIGILANT. Then open http://127.0.0.1:8000 and select
**OmniRoute (configured free route)** under Reasoning provider.

## Linux or manually configured environment

```bash
npx --yes omniroute@3.8.51
# In a separate shell after connecting a free provider:
export OMNIROUTE_BASE_URL=http://127.0.0.1:20128/v1
read -rs -p 'OmniRoute gateway key: ' OMNIROUTE_API_KEY
export OMNIROUTE_API_KEY
python scripts/check_omniroute.py --list-models
export OMNIROUTE_MODEL='EXACT_PROVIDER/MODEL_FROM_YOUR_GATEWAY'
export OMNIROUTE_FREE_MODELS="$OMNIROUTE_MODEL"
python scripts/check_omniroute.py
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Use the project's installed Python environment. `.env.example` is documentation;
the application does not automatically load it. Keep credentials out of code,
Git, model outputs, shared logs and archives.

## What changed and what remains unmeasured

- Explicit provider-qualified, operator-approved routes; `auto` and unapproved
  models are rejected. The endpoint is restricted to loopback.
- HTTP errors, quota exhaustion, truncated output and invalid citations are
  reported; no client retry or model fallback is attempted.
- The new investigation profile includes up to 24 full supplied excerpts within
  a 48,000-character evidence budget. It alternates revision/retrieval groups,
  includes line/hash provenance and explicitly counts omitted evidence. It cannot
  recover evidence that was never retrieved upstream.
- Requested and reported models, usage, response ID and prompt hash are saved.
  Costs remain unknown rather than falsely recording every request as $0.
- Existing Qwen/IR/RAG results remain historical immutable measurements. They do
  not become OmniRoute results. No improved accuracy is claimed by this update.

## Bounded validation after connection

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_omniroute.py --profile legacy --max-calls 5
```

Run in a shell with the gateway environment variables configured. Each invocation
adds at most five new calls and reuses completed observations. Exit 75 indicates a
partial, unscored batch; repeat the same command after available quota permits.
The default profile replays the exact saved 60-call study prompts to isolate the
model/provider change. `--profile expanded` starts a separate model-plus-context
comparison. Invalid/provider failures stop the batch and are excluded from accuracy,
not silently counted as model abstentions. Full-set scores appear only after all
60 responses complete. Do not select a winning prompt on test labels; use a new
independently annotated held-out set for a defensible final accuracy claim.

## Sources checked 2026-10-13

- Official gateway: https://github.com/diegosouzapw/OmniRoute
- Free access and provider conditions:
  https://github.com/diegosouzapw/OmniRoute/blob/release/v3.8.52/docs/getting-started/FREE-TIERS-GUIDE.md
- Model: https://console.groq.com/docs/model/openai/gpt-oss-120b
- Account-specific quotas: https://console.groq.com/docs/rate-limits

Gateway integration and synthetic contract tests are separate from a live model
evaluation. No connected OmniRoute server or provider credentials were available
in the hosted session when this update was prepared.

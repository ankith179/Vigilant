# GLM provider integration

VIGILANT can use the explicit GLM provider through Z.ai's OpenAI-compatible chat-completions endpoint. This is an optional hosted provider; it does not replace the local Qwen default or change historical experiment records.

## Safe activation

1. Obtain an authorized Z.ai API key and check the selected model's current billing terms.
2. Set `GLM_API_KEY` in the process environment or a local, untracked `.env`; never commit it or paste it into reports/chat.
3. Set `GLM_MODEL` to the exact model ID enabled for the account (the example uses `glm-5.3`).
4. Explicitly set `VIGILANT_FREE_ONLY=0` to permit provider calls. The default `1` blocks GLM because charges cannot be verified by VIGILANT.
5. Select `glm` in the UI or API. Requests use a fixed Z.ai endpoint, JSON-object output mode, temperature 0, a 90-second timeout, no redirect, no proxy inherited from the environment, retry, or fallback.

Selected requirements, source excerpts, tests, paths, revision IDs, and prompts are sent to Z.ai when inference runs. Do not use this provider for confidential repositories unless that transfer is approved under the project's data policy. The provider reports its model ID, but VIGILANT cannot independently verify remote weights or actual charges; recorded cost is `null`.

## Evaluation

The provider contract tests use mocked HTTP responses and do not call Z.ai or measure model quality. Compare GLM with the saved Qwen run only after configuring authorized credentials and billing, using identical frozen questions/evidence and the same output contract. Keep the 12-case result diagnostic only: it has authored, correlated labels, is already exposed, and is not independent evaluation. Save GLM output separately; never overwrite the historical 4/12 record. A 12-case GLM result is not a general accuracy or 95% acceptance result.

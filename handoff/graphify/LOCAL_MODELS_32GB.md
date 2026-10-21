# Local models on a 32 GB RAM computer

This release adds three local Ollama choices, paired source excerpts and a finite resumable comparison. No paid API is required. Model downloads, hardware, disk and electricity remain the user's responsibility. Larger models have NOT been measured on this project yet; >75% accuracy is a goal, not a result.

| Model tag | Listed quantized download | Use in this project |
| --- | ---: | --- |
| `qwen3:8b` | 5.2 GB | Default lighter candidate |
| `qwen2.5-coder:14b` | 9.0 GB | Code-focused candidate |
| `qwen3:14b` | 9.3 GB | Larger general candidate |

These are candidates expected to fit a 32 GB machine one at a time at the configured 8,192-token context. This is a memory estimate, not a hardware test. Weights are only part of RAM usage: runtime buffers, KV cache, OS and applications also need memory. CPU-only inference can be slow; GPU VRAM and processor are unknown. Close other model services. Keep roughly 30 GB free disk for the three downloads, plus project dependencies. Actual manifests and sizes may change; every evaluation records the installed digest. No weights are bundled.

## Windows start

Extract `VIGILANT-project.zip`. Open PowerShell in the extracted `VIGILANT` folder. Install Python 3.12, Git, Node/npm and Ollama first. Start the Ollama application/service.

```powershell
.\Setup-Windows.ps1
.\Run-Local-Models.ps1 -DownloadModels
.\Start-VIGILANT-Local.ps1 -Model qwen3:8b
```

Setup's `-DownloadModels` flag downloads the OLD Transformers research model; it is not needed for this Ollama profile. Use the flag on **Run-Local-Models.ps1** for the three new candidates. The comparison command downloads sequentially and performs at most 36 diagnostic generations (12 per model). It can take considerable CPU time; a per-call timeout is 600 seconds. If interrupted, rerun without `-DownloadModels`. Completed calls with exactly matching data, code and model digest are reused. A timeout stops that model's batch; it does not loop forever. Do not run the comparison and UI investigation simultaneously. The server itself uses one analysis worker.

Open http://127.0.0.1:8000. Select **Local Ollama (32 GB models)** and the desired **Local model**. The UI starts with qwen3:8b; the launcher's Model argument sets the API default, while an explicit UI selection takes precedence. Model preflight verifies installation before queuing the job. Only loopback Ollama is permitted; cloud-backed models and redirects are rejected. OmniRoute remains available as a separate optional gateway, with its existing free-route checks; it is not required for local inference.

## Linux or bounded continuation

After the existing installation guide, activate the project environment and start Ollama:

```bash
ollama pull qwen3:8b
ollama pull qwen2.5-coder:14b
ollama pull qwen3:14b
python scripts/evaluate_local_models.py --max-calls 6
```

Repeat the same command to continue. Exit 75 means a bounded partial run, 2 means an unresolved runtime blocker, 0 means all selected models completed. A six-call budget applies across models, not six per model. `--models qwen3:8b` limits evaluation to that model. `--prepare-only` verifies and exports inputs without inference. Results are under `experiments/local-model-comparison/`; `latest.json` summarizes the most recent invocation, while hash-keyed directories retain the actual observations. A changed model digest, source, question or dataset creates a new run identity.

## What changed

`llm/context.py` uses a neutral JSON schema instead of a prefilled uncertain decision. It keeps complete supplied excerpts and gives before/after groups priority; an oversized group is omitted as a whole with counts recorded. `rag/evidence.py` selects up to four changed-artifact pairs with 30-line windows around actual diff hunks. Additional retrieved/graph context is retained subject to provider budgets. Only the first intersecting hunk is centered per artifact, so this is bounded evidence selection, not exhaustive code review. `agents/workflow.py` verifies the excerpts against immutable snapshots. The model still must abstain when evidence is insufficient.

`llm/ollama.py` sends a JSON schema, temperature 0, seed 42, 8,192 context tokens and 512 output tokens, with thinking disabled where supported. It unloads after each call. Incomplete output is rejected; a model failure is not a correct uncertain answer. Character budgets do not prove a tokenizer-level fit. Context overflow and empty/invalid responses remain failures requiring inspection. JSON validity and citation IDs do not verify the meaning of an answer.

## Accuracy protocol

The included 12 scenarios are authored and correlated. Their previous model agreement was **25%**, equal to always-UNCERTAIN, with zero decisive coverage. They are diagnostic development inputs, not an independent test set. New model accuracy is **NOT RUN** in this release because no Ollama service or weights were present on the hosted machine. The 74 passing software tests do not measure model accuracy.

The new evaluator does not put expected labels or executed-rule verdicts into the prompt. It uses changed-file metadata, paired snapshot excerpts and saved retrieved evidence. The saved retrieval can reflect upstream declared traces and the controlled mutation wording remains visible; this is not a clean independent corpus. It reports complete-set accuracy, macro F1 over gold classes, valid response rate, uncertainty, decisive coverage, confusion counts, latency and majority/always-uncertain baselines. Invalid generated responses count as errors. Runtime failures without final text keep the set incomplete and unscored. Completed diagnostic scores, even above 75%, never set `target_status` to achieved.

For a real claim, collect independently annotated repository changes with consistent label definitions, negative cases and adjudication. Split by repository/change family to avoid duplicate or related changes crossing splits. Select the model and tune prompts on validation only; freeze them before a single held-out test. Report full accuracy, per-class precision/recall/F1, baselines, sample size and uncertainty intervals, plus semantic citation review. A JSON dataset has `split` (diagnostic/validation/test), `label_source`, and `cases`, each with `case_id`, `question`, `evidence` in the existing evidence format, and `expected_status`. Use `--dataset path.json --models <one-selected-tag>`. Multi-model test-set selection is rejected. Dataset independence and annotation quality require human review and cannot be certified by a metadata flag. Do not repeatedly tune against the held-out set to force a 75% result.

## Verified upstream references

Checked 2026-10-17: [Qwen3 8B](https://ollama.com/library/qwen3:8b), [Qwen3 14B](https://ollama.com/library/qwen3:14b), [Qwen2.5 Coder 14B](https://ollama.com/library/qwen2.5-coder:14b), [Ollama chat API](https://docs.ollama.com/api/chat), [structured outputs](https://docs.ollama.com/capabilities/structured-outputs). These establish availability and API behavior, not VIGILANT accuracy.

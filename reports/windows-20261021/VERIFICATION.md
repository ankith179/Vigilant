# Native Windows continuation - 21 October 2026

Status: Windows setup, application execution and all 36 local diagnostic generations COMPLETED. Exact resume verified with zero new calls. Model quality remains inadequate on these authored diagnostics.

## Environment and application

- Continued the extracted checkpoint in place; no new scaffold or historical inference reruns.
- Native Windows, Python 3.12, approximately 32 GB system RAM, NVIDIA GeForce RTX 3050 OEM with 8 GB VRAM.
- Core dependencies installed in `.venv`; production frontend built successfully.
- Ollama 0.40.7 standalone runtime installed in `.runtime/ollama`; all three requested model tags downloaded and verified by Ollama.
- Models are local, with cloud disabled (`OLLAMA_NO_CLOUD=1`), loopback binding, one loaded model and one parallel inference slot.
- Application running at http://127.0.0.1:8000; `/api/health` returned `ok` and the browser was opened.
- Missing dashboard rows from the interrupted first restore were merged from the read-only frozen snapshot with `INSERT OR IGNORE`; repository paths were repaired. Existing rows were preserved.

## Windows fixes and validation

- Git worktree metadata now uses UTF-8, forward slashes and LF line endings.
- SQLite backup connections explicitly close before atomic replacement; this fixes Windows file-lock failures.
- Windows setup, application, model comparison and browser launchers enable Python UTF-8 mode.
- Browser runner closes its SQLite handles before temporary-directory cleanup.
- Checkpoint ZIP paths are platform independent; `.runtime` and model dependencies are excluded. `--preserve-snapshots` prevents replacement of historical snapshot databases.
- Added a worktree metadata regression and `Start-Ollama-Local.ps1`. The comparison launcher finds the project-local runtime.
- **75 tests passed** (`tests-final.log`); one dependency deprecation warning remains.
- Production build passed (`setup.log`; the first setup subsequently failed during restore, before the fixes).
- Windows Chromium acceptance **PASSED**, all 13 pages plus exports, graph/evidence, local model selection, deterministic investigation and mobile checks: `../frontend/2026-10-21T05-33-37-317Z/validation.json`.
- Native SQLite backup and portable ZIP checks passed. The initial full checkpoint reports no backup failures.

## Local model evaluation

Protocol: the saved neutral paired-evidence prompt; 12 authored, correlated diagnostic cases; temperature 0, seed 42, 8192 context tokens, 512 output tokens, thinking disabled where supported. One model at a time, unloaded after each call. All outputs and exact model/input/source fingerprints are retained separately in `../../experiments/local-model-comparison/windows-20261021/`.

| Model | Completed cases | Correct / 12 | Valid responses | Diagnostic accuracy |
| --- | ---: | ---: | ---: | ---: |
| Qwen3 8B | 12 | 0 | 0/12 | 0% |
| Qwen2.5 Coder 14B | 12 | 1 | 10/12 | 8.33% |
| Qwen3 14B | 12 | 0 | 0/12 | 0% |

Both Qwen3 models failed citation alias validation on every case. Qwen2.5 Coder 14B failed that validation twice; its remaining errors include predicting CONSISTENT where the authored label was different. Invalid output is an error, not a correct UNCERTAIN answer. Validation success does not establish semantic entailment.

The always-UNCERTAIN baseline is 25%; the majority-class baseline is 50%. These cases are development diagnostics, not independent held-out evaluation. No model superiority, independent accuracy, or accuracy above 75% is established. No labels were invented or changed, and no prompt tuning used these results.

## Preservation

All **423 pre-existing experiment and snapshot files** match the pre-work SHA-256 manifest (`historical-sha256.json`, `preservation.json`). Historical metric recomputation passes for **23 method rows and 1484 query rows** (`metrics-audit.json`); all **251 historical RAG generations** pass the provenance audit using the archived provider source (`rag-audit.json`). These audits did not rerun inference.

## Restart and remaining scientific work

Keep using this extracted directory. After a reboot run `Start-Ollama-Local.ps1`, then `Start-VIGILANT-Local.ps1` in another terminal. Runtime binaries and weights are reproducible dependencies excluded from the ZIP. See `../../docs/LOCAL_MODELS_32GB.md` for exact resume commands.

Independent annotations, semantic citation review, repository/change-family-separated validation and test sets, and a frozen selection protocol remain necessary for a defensible accuracy claim. Authorship, institution and publication tasks remain external. No paid inference or cloud fallback was used.

Final checks: `diagnostic-audit.json` verifies all 36 observations and score arithmetic; `diagnostic-review.csv` provides per-case outcomes. `resume-check.log` confirms zero new calls. The five fingerprinted evaluation sources are archived under `frozen/`. All four SQLite databases pass integrity checks; pip reports no broken requirements.

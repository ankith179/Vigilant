# VIGILANT runtime verification — 17 October 2026

Ollama 0.40.5 was installed temporarily and its loopback version endpoint responded. Cloud inference was disabled and only one server was used. Qwen3 8B download failed with `redirect target not allowed` because the Cloudflare R2 storage hostname could not be resolved/reached through the available network. No new model inference ran; scores remain unmeasured. The host has an 8 GiB memory limit and no GPU; 14B downloads were not attempted. The temporary server was stopped. Weights/runtime binaries are reproducible dependencies and are not bundled.

Continuation is PAUSED until a usable model/weights connection or independently annotated data is supplied. No completed tests or historical inference were repeated. See `reports/runtime-20261017/VERIFICATION.md` and `session.json`.

Next bounded Windows commands, after existing setup and starting Ollama, from the VIGILANT folder:

```powershell
ollama pull qwen3:8b
.\.venv\Scripts\python.exe scripts/evaluate_local_models.py --models qwen3:8b --max-calls 6
```

Repeat the same bounded command to resume matching fingerprints. Once the runtime is available, compare candidates on validation, freeze one model and prompt, and test using independently reviewed held-out labels. Authored diagnostic scores cannot verify >75% independent accuracy. Native Windows access and independent annotations remain external requirements.

Restored full project version 17; SHA-256 `8b7c46571b81c566a61bbd1a2a508abbeabd1409fff3367c29700d68102b7f0d`. Input ZIP CRC check passed. Existing 74-test and browser results were retained, not rerun. Graphify exports, graph snapshots, experiments and Word/PDF drafts are preserved.

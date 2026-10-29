# Reproduce or resume VIGILANT

Use Python 3.12, Git and Node.js/npm. The package contains source, prepared and raw
datasets, repository histories, database snapshots and actual experiment records.
Model binaries and installed dependencies are recreated from pinned manifests.
Begin with `PROJECT_STATE.json` and `RESUME.md`; completed experiments need not be
rerun merely to reopen the project.

## Windows

The requested destination is `C:\Users\Ankith\Downloads\Code- Vigilant`.
Place `VIGILANT-project.zip` beside `Install-VIGILANT.ps1`, run the installer, and
open PowerShell in that destination. Then:

```powershell
./Setup-Windows.ps1 -DownloadModels
./Start-VIGILANT.ps1
```

The installer refuses to overwrite a nonempty destination. The bundled raw
datasets and repositories make `-DownloadRepositories` unnecessary for restoring
this checkpoint. Setup builds the frontend, repairs relocated repository paths,
restores a recorded database if absent and runs tests. Windows execution remains
unverified in this Linux development session.

For a manual setup using a trusted PowerShell session:

```powershell
py -3.12 -m venv .venv
./.venv/Scripts/python.exe -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
./.venv/Scripts/python.exe -m pip install -r requirements.txt
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
./.venv/Scripts/python.exe scripts/restore_checkpoint.py
./.venv/Scripts/python.exe scripts/download_models.py
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. View the ledger without running anything with
`./Continue-VIGILANT.ps1 -Status`. The continuation runner executes existing
scripts in dependency order and skips completed stages; it does not write papers,
perform human review or bypass account limits. Honor active leases.

## Linux

```bash
bash scripts/setup.sh
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/restore_checkpoint.py
.venv/bin/python scripts/download_models.py
.venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000
```

`scripts/setup.sh` uses uv. An ordinary Python virtual environment and pip can
install the same pinned requirements if uv is unavailable.

## Hosted temporary-runtime workaround

For this hosted session only, large in-progress scratch writes have been lost or
truncated between operations. Keep live weights and SQLite databases in `/tmp`:

```bash
VIGILANT_MODEL_STAGING=/tmp/vigilant-models HF_HUB_DOWNLOAD_TIMEOUT=60 \
  .venv/bin/python scripts/download_models.py --staging-only
export VIGILANT_LLM_PATH=/tmp/vigilant-models/llm
export VIGILANT_EMBEDDING_PATH=/tmp/vigilant-models/embedding
export VIGILANT_EMBEDDING_CACHE=/tmp/vigilant-runtime/embedding-cache.sqlite
export VIGILANT_BENCH_DB=sqlite:////tmp/vigilant-runtime/changebench.db
export VIGILANT_DB=sqlite:////tmp/vigilant-runtime/vigilant.db
```

Restore valid database snapshots into the runtime directory first. SQLite backup
must be used for a live database; copying its main file without its WAL is unsafe.
Safetensor headers are checked before inference. `scripts/checkpoint.py` stages
and verifies archives before atomically installing them. Persist checkpoints
after meaningful progress; a temporary runtime is not a durable backup.

## Experiment provenance

Raw rankings, per-query metrics, model requests/responses and validation failures
are preserved. `data/models.json`, `data/datasets.json` where present, and each
experiment's `results.json` identify inputs and settings. Failed loading-only
runs with `EXCLUDED.json` must not be used as LLM accuracy results. Model API cost
is zero for local inference; CPU, memory and energy costs are not thereby zero.

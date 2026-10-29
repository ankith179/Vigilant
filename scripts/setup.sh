#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -gt 1 || ($# -eq 1 && "$1" != "--models") ]]; then
  echo 'Usage: bash scripts/setup.sh [--models]' >&2; exit 2
fi
command -v git >/dev/null
command -v npm >/dev/null
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
if [[ "${1:-}" == "--models" ]]; then
  .venv/bin/python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.7.1'
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python scripts/download_models.py
fi
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/restore_checkpoint.py
.venv/bin/python scripts/sync_dashboard.py
.venv/bin/python -m pytest -q
echo 'Run .venv/bin/python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000'

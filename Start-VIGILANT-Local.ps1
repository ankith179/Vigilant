[CmdletBinding()]
param([ValidateSet('qwen3:8b','qwen2.5-coder:14b','qwen3:14b')][string]$Model='qwen3:8b',[int]$Port=8000)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:OLLAMA_MODEL=$Model
$env:OLLAMA_URL='http://127.0.0.1:11434'
$env:VIGILANT_FREE_ONLY='1'
$ProjectPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
& $ProjectPython -c "from llm.ollama import OllamaProvider; print(OllamaProvider().preflight())"
if ($LASTEXITCODE -ne 0) { throw 'Start Ollama and pull the selected model first.' }
& (Join-Path $PSScriptRoot 'Start-VIGILANT.ps1') -Port $Port

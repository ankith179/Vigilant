[CmdletBinding()]
param([switch]$DownloadModels, [string[]]$Models=@('qwen3:8b','qwen2.5-coder:14b','qwen3:14b'),
 [string]$Output='experiments/local-model-comparison/citation-fix-20261021')
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
Set-Location -LiteralPath $PSScriptRoot
$ProjectPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
$Ollama = Join-Path $PSScriptRoot '.runtime\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $Ollama)) {
 $Ollama = (Get-Command ollama -ErrorAction Stop).Source
}
foreach ($Model in $Models) {
 if ($Model -notin @('qwen3:8b','qwen2.5-coder:14b','qwen3:14b')) { throw "Unsupported model: $Model" }
 if ($DownloadModels) { & $Ollama pull $Model; if ($LASTEXITCODE -ne 0) { throw "Download failed: $Model" } }
}
# Finite default comparison: 12 cases x selected models. Resume uses exact input/model digests.
& $ProjectPython scripts/evaluate_local_models.py --models @Models --max-calls 1000 --output $Output
if ($LASTEXITCODE -ne 0) { throw "Evaluation incomplete. Inspect $Output/latest.json; rerun after resolving the blocker." }
Write-Host 'Comparison complete. Diagnostic accuracy is not independent test accuracy.'

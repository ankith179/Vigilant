[CmdletBinding()]
param([switch]$All, [switch]$Status)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$ProjectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
$StageArguments = @('scripts/continue_project.py')
if ($All) { $StageArguments += '--all' }
if ($Status) { $StageArguments += '--status' }
& $ProjectPython @StageArguments
if ($LASTEXITCODE -ne 0) { throw 'Continuation stopped. Review PROJECT_STATE.json and the recorded log.' }

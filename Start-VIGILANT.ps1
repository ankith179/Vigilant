[CmdletBinding()]
param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
$ProjectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
$env:VIGILANT_DB = 'sqlite:///data/vigilant.db'
& $ProjectPython -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port $Port
if ($LASTEXITCODE -ne 0) { throw 'The VIGILANT server exited with an error. Review the message above.' }

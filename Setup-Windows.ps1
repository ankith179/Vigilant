[CmdletBinding()]
param([switch]$DownloadModels, [switch]$DownloadRepositories)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$ProjectRoot = $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Executable" }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows, then run this script again.' }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Install Node.js with npm, then run this script again.' }
$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
    Invoke-Checked -Executable 'py' -Arguments @('-3.12', '-m', 'venv', '.venv')
} else {
    $PythonLauncher = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonLauncher) { throw 'Install Python 3.12 with the Python launcher, then run this script again.' }
    Invoke-Checked -Executable 'python' -Arguments @('-c', 'import sys; assert sys.version_info[:2] == (3,12), "Python 3.12 is required"')
    Invoke-Checked -Executable 'python' -Arguments @('-m', 'venv', '.venv')
}
$ProjectPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
Invoke-Checked -Executable $ProjectPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-Checked -Executable $ProjectPython -Arguments @('-m', 'pip', 'install', '-r', 'requirements-core.txt')
if ($DownloadModels) {
    Invoke-Checked -Executable $ProjectPython -Arguments @('-m', 'pip', 'install', '--index-url', 'https://download.pytorch.org/whl/cpu', 'torch==2.7.1')
    Invoke-Checked -Executable $ProjectPython -Arguments @('-m', 'pip', 'install', '-r', 'requirements.txt')
}
Invoke-Checked -Executable 'npm.cmd' -Arguments @('--prefix', 'frontend', 'ci')
Invoke-Checked -Executable 'npm.cmd' -Arguments @('--prefix', 'frontend', 'run', 'build')
Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/restore_checkpoint.py')
Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/sync_dashboard.py')
if ($DownloadRepositories) {
    Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/download_data.py')
    Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/clone_repositories.py')
    Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/prepare_data.py')
}
if ($DownloadModels) { Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/download_models.py') }
Invoke-Checked -Executable $ProjectPython -Arguments @('-m', 'pytest', '-q')
Write-Host 'Setup complete. Run .\Start-VIGILANT.ps1 and open http://127.0.0.1:8000'

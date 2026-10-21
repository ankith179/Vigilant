[CmdletBinding()]
param([string]$BaseUrl = '', [switch]$InstallBrowser)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Executable" }
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw 'Node.js with npm is required.' }
if ($InstallBrowser) {
    Invoke-Checked -Executable 'npm.cmd' -Arguments @('--prefix', 'tools/browser', 'ci')
    Invoke-Checked -Executable 'npm.cmd' -Arguments @('--prefix', 'tools/browser', 'run', 'install-browser')
}
if (-not (Test-Path 'tools/browser/node_modules/playwright')) { throw 'Run this script with -InstallBrowser first.' }
if ($BaseUrl) {
    $env:VIGILANT_TEST_URL = $BaseUrl
    $env:VIGILANT_TEST_MUTATIONS = '0'
    Invoke-Checked -Executable 'node' -Arguments @('scripts/test_frontend.cjs')
} else {
    $ProjectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
    Invoke-Checked -Executable $ProjectPython -Arguments @('scripts/run_frontend_check.py')
}
Write-Host 'Browser validation passed. Timestamped results and screenshots are in reports/frontend.'

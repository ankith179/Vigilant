[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Model, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$ProjectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $ProjectPython)) { throw 'Run Setup-Windows.ps1 first.' }
# The model must be a provider-qualified route whose free account eligibility
# the operator has checked. This is not an independent billing guarantee.
$env:OMNIROUTE_MODEL = $Model
$env:OMNIROUTE_FREE_MODELS = $Model
if (-not $env:OMNIROUTE_BASE_URL) { $env:OMNIROUTE_BASE_URL = 'http://127.0.0.1:20128/v1' }
if (-not $env:OMNIROUTE_API_KEY) {
    $Secret = Read-Host 'OmniRoute gateway key (Enter only if gateway auth is disabled)' -AsSecureString
    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secret)
    try { $env:OMNIROUTE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer) }
}
& $ProjectPython scripts/check_omniroute.py
if ($LASTEXITCODE -ne 0) { throw 'Configure the gateway and free route before starting VIGILANT.' }
& (Join-Path $PSScriptRoot 'Start-VIGILANT.ps1') -Port $Port

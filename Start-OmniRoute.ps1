[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if (-not (Get-Command npx.cmd -ErrorAction SilentlyContinue)) { throw 'Install Node.js 24 with npm first.' }
Write-Host 'Starting pinned OmniRoute 3.8.51. Connect only an eligible free provider in its dashboard.'
Write-Host 'Do not configure paid fallback routes. No provider account is supplied by VIGILANT.'
& npx.cmd --yes omniroute@3.8.51
if ($LASTEXITCODE -ne 0) { throw 'OmniRoute exited with an error.' }

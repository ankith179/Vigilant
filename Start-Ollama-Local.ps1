[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$Ollama = Join-Path $PSScriptRoot '.runtime\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $Ollama)) {
    $Ollama = (Get-Command ollama -ErrorAction Stop).Source
}
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $PSScriptRoot '.runtime\models'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
& $Ollama serve
if ($LASTEXITCODE -ne 0) { throw 'Ollama exited with an error. Check whether another server already owns port 11434.' }

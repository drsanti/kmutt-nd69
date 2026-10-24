# Dot-source from code/:  . .\env.ps1
$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.\.venv\Scripts\Activate.ps1')) {
  throw "No .venv here. cd to workshops\code and create it (workshop 02)."
}
. .\.venv\Scripts\Activate.ps1
if (-not (Test-Path '.\robotos-v0.3.0-windows-x64\bin\robotos.exe')) {
  throw "Missing robotos-v0.3.0-windows-x64\bin\robotos.exe"
}
$env:PATH = (Resolve-Path '.\robotos-v0.3.0-windows-x64\bin').Path + ';' + $env:PATH
$ver = (robotos.exe version | Out-String).Trim()
Write-Host "OK  venv + robotos on PATH  ($ver)" -ForegroundColor Green

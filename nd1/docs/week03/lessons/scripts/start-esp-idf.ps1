# Run in Windows PowerShell, or use start-esp-idf.cmd / start-esp-idf.sh.
[CmdletBinding()]
param(
    [string]$IdfPath,
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$InstallTools,
    [string]$Target = 'esp32s3',
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
try {
    Remove-Item Env:MSYSTEM -ErrorAction SilentlyContinue
    $savedPath = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
    # Keep caller-specific tool paths after the saved Windows paths.
    $env:Path = $savedPath + ';' + $env:Path
    $env:PATHEXT = [Environment]::GetEnvironmentVariable('PATHEXT', 'Machine')
    $env:PYTHONUTF8 = '1'

    if (-not $IdfPath) { $IdfPath = $env:IDF_PATH }
    if (-not $IdfPath) { $IdfPath = 'D:\dev\esp\v6.1\esp-idf' }
    foreach ($file in @('export.ps1', 'tools\idf.py')) {
        if (-not (Test-Path -LiteralPath (Join-Path $IdfPath $file) -PathType Leaf)) {
            throw "ESP-IDF not found at '$IdfPath'. Supply -IdfPath with your framework directory."
        }
    }
    $IdfPath = (Resolve-Path -LiteralPath $IdfPath).Path
    if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
        throw "Project directory does not exist: $ProjectPath"
    }
    $ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            $pythonExe = py -3 -c 'import sys; print(sys.executable)'
            if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $pythonExe)) {
                $env:Path = (Split-Path -Parent $pythonExe) + ';' + $env:Path
            }
        }
    }
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw 'Python is missing. Install supported Windows Python with Add python.exe to PATH, then reopen your terminal.'
    }
    python -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'A working Python 3.10 or newer is required.' }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git is missing. Install Git for Windows with command-line PATH support, then reopen your terminal.'
    }
    if ($InstallTools) {
        # Isolate install.ps1: it uses exit on failure, which must not close this launcher.
        & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File (Join-Path $IdfPath 'install.ps1') $Target
        if ($LASTEXITCODE -ne 0) { throw 'Tool installation failed. Resolve the installer error and retry.' }
    }
    . (Join-Path $IdfPath 'export.ps1')
    if (-not (Get-Command idf.py -ErrorAction SilentlyContinue)) {
        throw 'Activation failed. Install tools first with -InstallTools, then retry.'
    }
    idf.py --version
    if ($LASTEXITCODE -ne 0) { throw 'ESP-IDF verification failed. Review the activation output above.' }
    Set-Location -LiteralPath $ProjectPath
    Write-Host "ESP-IDF ready in $ProjectPath"
    Write-Host 'Run idf.py build from a project directory. Type exit to close this session.'
} catch {
    Write-Host "ESP-IDF setup failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($CheckOnly) { exit 1 }
    throw
}

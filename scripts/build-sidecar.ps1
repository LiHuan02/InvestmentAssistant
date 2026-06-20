# Build the Python backend sidecar for Tauri (Windows)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$TauriBinaries = Join-Path $ProjectRoot "src-tauri\binaries"

Write-Host "=== Building Python sidecar ==="
Set-Location $BackendDir

# Install PyInstaller if not present
uv run pip install pyinstaller --quiet 2>$null

# Build with PyInstaller
Write-Host "Running PyInstaller..."
uv run pyinstaller investment-backend.spec --clean --noconfirm

# Detect target triple
$Target = (rustc -vV 2>$null | Select-String "host: " | ForEach-Object { $_.Line.Split(": ")[1] })
if (-not $Target) { $Target = "x86_64-pc-windows-msvc" }

# Copy to Tauri binaries
New-Item -ItemType Directory -Force -Path $TauriBinaries | Out-Null
$Output = Join-Path $BackendDir "dist\investment-backend\investment-backend.exe"
$Dest = Join-Path $TauriBinaries "investment-backend-$Target.exe"

if (Test-Path $Output) {
    Copy-Item $Output $Dest -Force
    Write-Host "Sidecar copied to: $Dest"
} else {
    Write-Host "ERROR: Build output not found at $Output"
    exit 1
}

Write-Host "=== Sidecar build complete ==="

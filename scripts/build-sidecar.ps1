# Build the Python backend sidecar for Tauri (Windows)
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$TauriBinaries = Join-Path $ProjectRoot "src-tauri\binaries"

Write-Host "=== Building Python sidecar ==="
Set-Location $BackendDir

uv run pip install pyinstaller --quiet 2>$null

Write-Host "Running PyInstaller..."
uv run pyinstaller investment-backend.spec --clean --noconfirm

$Target = (rustc -vV 2>$null | Select-String "host: " | ForEach-Object { $_.Line.Split(": ")[1] })
if (-not $Target) { $Target = "x86_64-pc-windows-msvc" }

New-Item -ItemType Directory -Force -Path $TauriBinaries | Out-Null
$Dest = Join-Path $TauriBinaries "investment-backend-$Target.exe"
Copy-Item "dist\investment-backend\investment-backend.exe" $Dest -Force
Write-Host "Sidecar: $Dest"
Write-Host "=== Done ==="

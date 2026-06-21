#!/usr/bin/env bash
# Build the Python backend sidecar for Tauri (macOS / Linux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
TAURI_BINARIES="$PROJECT_ROOT/src-tauri/binaries"

echo "=== Building Python sidecar ==="
cd "$BACKEND_DIR"

uv run pip install pyinstaller --quiet 2>/dev/null || true

echo "Running PyInstaller..."
uv run pyinstaller investment-backend.spec --clean --noconfirm

TARGET=$(rustc -vV 2>/dev/null | sed -n 's/host: //p')
if [ -z "$TARGET" ]; then
    echo "ERROR: Cannot detect Rust target triple"
    exit 1
fi

mkdir -p "$TAURI_BINARIES"
DEST="$TAURI_BINARIES/investment-backend-$TARGET"
cp dist/investment-backend/investment-backend "$DEST"
chmod +x "$DEST"
echo "Sidecar: $DEST"
echo "=== Done ==="

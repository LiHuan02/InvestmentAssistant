#!/usr/bin/env bash
# Build the Python backend sidecar for Tauri (macOS / Linux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
TAURI_BINARIES="$PROJECT_ROOT/src-tauri/binaries"

echo "=== Building Python sidecar ==="
cd "$BACKEND_DIR"

# Install PyInstaller if not present
uv run pip install pyinstaller --quiet 2>/dev/null || true

# Build with PyInstaller
echo "Running PyInstaller..."
uv run pyinstaller investment-backend.spec --clean --noconfirm

# Detect target triple
TARGET=$(rustc -vV 2>/dev/null | sed -n 's|host: ||p' || echo "unknown")

# Copy to Tauri binaries
mkdir -p "$TAURI_BINARIES"
OUTPUT="$BACKEND_DIR/dist/investment-backend/investment-backend"
DEST="$TAURI_BINARIES/investment-backend-$TARGET"

if [ -f "$OUTPUT" ]; then
    cp "$OUTPUT" "$DEST"
    chmod +x "$DEST"
    echo "Sidecar copied to: $DEST"
else
    echo "ERROR: Build output not found at $OUTPUT"
    exit 1
fi

echo "=== Sidecar build complete ==="

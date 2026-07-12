#!/usr/bin/env bash
# Build Android APK with embedded Python backend
# Requires: Android SDK, Java 17+, Gradle
# Can run on Linux/macOS, or Windows via WSL
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ANDROID_DIR="$FRONTEND_DIR/android"

echo "=== Building Android APK ==="

# Step 1: Build frontend
echo "[1/4] Building frontend..."
cd "$FRONTEND_DIR"
npm run build

# Step 2: Sync Capacitor (copy dist to Android assets)
echo "[2/4] Syncing Capacitor..."
npx cap sync android

# Step 3: Copy the Android-only Python source files.
# Do not copy backend/: it pulls in FastAPI/LangChain/Chroma and is not
# compatible with the lightweight Chaquopy dependency set.
echo "[3/4] Copying Android Python sources..."
PYTHON_SRC="$ANDROID_DIR/app/src/main/python"
rm -rf "$PYTHON_SRC"
mkdir -p "$PYTHON_SRC/android_backend" "$PYTHON_SRC/frontend"
cp "$PROJECT_ROOT/android_server.py" "$PYTHON_SRC/"
cp "$PROJECT_ROOT/android_backend/"*.py "$PYTHON_SRC/android_backend/"
# The WebView is configured to load the local Python server, so the frontend
# assets must be available beside android_server.py inside the APK as well.
cp -r "$FRONTEND_DIR/dist" "$PYTHON_SRC/frontend/"

# Step 4: Build APK with Gradle
echo "[4/4] Building APK..."
cd "$ANDROID_DIR"

# Use local gradle wrapper if available, otherwise use system gradle
if [ -f "./gradlew" ]; then
    chmod +x ./gradlew
    ./gradlew assembleRelease
else
    gradle assembleRelease
fi

# Find and report APK
APK_PATH="$ANDROID_DIR/app/build/outputs/apk/release/app-release-unsigned.apk"
if [ -f "$APK_PATH" ]; then
    # Copy to project root for easy access
    cp "$APK_PATH" "$PROJECT_ROOT/InvestmentAssistant.apk"
    echo ""
    echo "=== APK built successfully ==="
    echo "Output: $PROJECT_ROOT/InvestmentAssistant.apk"
    echo "Size: $(du -h "$PROJECT_ROOT/InvestmentAssistant.apk" | cut -f1)"
    echo ""
    echo "NOTE: APK is unsigned. To install on a device, either:"
    echo "  1. Sign with: apksigner sign --ks your-keystore.jks InvestmentAssistant.apk"
    echo "  2. Or use debug build: ./gradlew assembleDebug"
else
    echo "ERROR: APK not found at expected path"
    exit 1
fi

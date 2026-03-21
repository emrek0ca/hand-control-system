#!/bin/bash
set -euo pipefail

echo "🚀 HandControlAI .app Fix & Bundle Starting..."

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "❌ This script builds a macOS app bundle only."
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "./venv/bin/python" ]]; then
    PYTHON_BIN="./venv/bin/python"
fi

echo "📦 Installing dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt
if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
    "$PYTHON_BIN" -m pip install pyinstaller
fi

echo "🧹 Cleaning previous build outputs..."
rm -rf build dist

echo "🏗  Building the macOS app bundle..."
"$PYTHON_BIN" -m PyInstaller --noconfirm --clean HandControlAI.spec

echo "🧹 Cleaning macOS bundle metadata..."
if command -v xattr >/dev/null 2>&1; then
    xattr -cr dist/HandControlAI.app || true
fi

if [[ -n "${CODESIGN_IDENTITY:-}" ]]; then
    echo "🔐 Signing bundle with provided identity..."
    codesign --deep --force --options runtime --sign "$CODESIGN_IDENTITY" dist/HandControlAI.app
elif [[ "${ENABLE_ADHOC_CODESIGN:-1}" != "0" ]]; then
    echo "🔐 Applying ad-hoc codesign..."
    codesign --deep --force --options runtime --sign - dist/HandControlAI.app || true
fi

codesign --verify --deep --strict dist/HandControlAI.app >/dev/null 2>&1 || true

echo "🔎 Validating bundle Info.plist..."
plutil -lint resources/macos/Info.plist
plutil -lint dist/HandControlAI.app/Contents/Info.plist

test -x dist/HandControlAI.app/Contents/MacOS/HandControlAI

echo "✅ Build Complete with Permissions Fixed!"
echo "📂 App Path: $(pwd)/dist/HandControlAI.app"
echo "🧾 Release checklist:"
echo "   1. Sign: codesign --deep --force --options runtime --sign <IDENTITY> dist/HandControlAI.app"
echo "   2. Notarize: xcrun notarytool submit dist/HandControlAI.app --wait"
echo "   3. Staple: xcrun stapler staple dist/HandControlAI.app"

#!/bin/bash

echo "🚀 HandControlAI .app Fix & Bundle Starting..."

# 1. Clean previous builds
rm -rf build dist HandControlAI.spec

# 2. Create a temporary Info.plist for permissions
cat > Info.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSCameraUsageDescription</key>
    <string>HandControlAI requires camera access to track hand gestures.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>HandControlAI requires microphone access for voice commands.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>HandControlAI requires permission to control system mouse and keyboard.</string>
    <key>CFBundleIdentifier</key>
    <string>com.ai.handcontrol</string>
    <key>CFBundleName</key>
    <string>HandControlAI</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
</dict>
</plist>
EOF

# 3. Build the macOS App Bundle
# --collect-all mediapipe: Ensures all binary graphs and assets are included
./venv/bin/pyinstaller --noconfirm --windowed --name "HandControlAI" \
    --osx-bundle-identifier "com.ai.handcontrol" \
    --collect-all mediapipe \
    --add-data "requirements.txt:." \
    --add-data "config.py:." \
    --add-data "AGENTS.md:." \
    --add-data "SKILLS.md:." \
    --hidden-import "cv2" \
    --hidden-import "numpy" \
    --hidden-import "pyautogui" \
    --hidden-import "pyttsx3" \
    --hidden-import "speech_recognition" \
    --hidden-import "google.generativeai" \
    --hidden-import "PIL" \
    --hidden-import "PIL.Image" \
    launcher.py

# 4. Apply Info.plist to the bundle
cp Info.plist dist/HandControlAI.app/Contents/Info.plist

echo "✅ Build Complete with Permissions Fixed!"
echo "📂 App Path: $(pwd)/dist/HandControlAI.app"
echo "⚠️  Note: First run might require right-click -> Open to bypass security."

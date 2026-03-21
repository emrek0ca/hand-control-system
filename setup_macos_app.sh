#!/bin/bash

echo "🚀 HandControlAI .app Builder Starting..."

# 1. Install PyInstaller
./venv/bin/pip install pyinstaller

# 2. Build the macOS App Bundle
# --windowed: No terminal window
# --noconfirm: Overwrite existing
# --name: App name
# --add-data: Include requirements and config
# --hidden-import: Ensure all modules are bundled
./venv/bin/pyinstaller --noconfirm --windowed --name "HandControlAI" \
    --add-data "requirements.txt:." \
    --add-data "config.py:." \
    --add-data "AGENTS.md:." \
    --add-data "SKILLS.md:." \
    --hidden-import "mediapipe" \
    --hidden-import "google.generativeai" \
    --hidden-import "cv2" \
    --hidden-import "numpy" \
    --hidden-import "pyautogui" \
    --hidden-import "pyttsx3" \
    --hidden-import "speech_recognition" \
    launcher.py

echo "✅ Build Complete! Your app is in the 'dist' folder."
echo "📂 Path: $(pwd)/dist/HandControlAI.app"

# Hand Control System

Hand Control System is a cross-platform hand gesture controller for macOS, Windows, and Linux.
It combines low-latency hand tracking, per-hand gesture bindings, voice commands, and an advanced settings panel into one lightweight runtime.

## Why It Stands Out

- Cross-platform launcher with graceful fallback paths
- Per-hand binding profiles for left and right hand overrides
- Detailed settings panel with live theme preview
- Mouse tuning for direction, gain, smoothing, scroll, and zoom
- Optional voice commands and optional Gemini-based screen analysis
- macOS app bundle support with a clean build pipeline
- Runtime fallback when optional dependencies are missing

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python launcher.py
```

Open the settings panel from the app, press `p` in the main window, or run:

```bash
python launcher.py --settings-panel
```

## Settings Panel

The settings panel lets users control the full runtime without editing files by hand.

- Profiles and profile duplication
- Primary hand selection
- Global and per-hand gesture/state bindings
- Mouse inversion, pointer gain, smoothing, freeze, scroll, and zoom tuning
- Voice and AI toggles
- Dark, midnight, and light panel themes
- HUD, performance, and debug controls

Per-hand overrides fall back to the global binding when left blank, so the UI stays clean and explicit.

## Runtime Modes

- macOS with `rumps`: menu bar experience
- macOS without `rumps`: direct app window fallback
- Windows and Linux: direct app window
- Missing voice or AI dependencies: core gesture control remains available

## macOS App Bundle

Build the app bundle with:

```bash
bash setup_macos_app.sh
```

The bundle uses `resources/macos/Info.plist` and is packaged through `HandControlAI.spec`.

## Permissions

- Camera: required
- Accessibility / Input Monitoring: required for mouse and keyboard control
- Microphone: optional for voice commands
- `GEMINI_API_KEY`: optional for screen analysis and LLM actions

Settings are stored in the runtime user data directory and reloaded automatically by the app.

## Project Layout

- `launcher.py`: universal entry point and settings-panel launcher
- `main.py`: gesture runtime and multimodal control loop
- `menu_app.py`: macOS menu bar wrapper
- `settings_manager.py`: profiles, bindings, and persistence
- `settings_panel.py`: advanced settings UI
- `system_control.py`: mouse, keyboard, scroll, and zoom execution
- `hand_tracker.py`: gesture and hand state detection

## Reliability Goals

- No hard dependency on optional UI packages
- No crash on missing voice or AI modules
- Clean runtime data separation from source tree
- Safe bundle generation with a single canonical plist

## Troubleshooting

- Camera not accessible: check privacy permissions and close other camera apps
- Voice unavailable: install `pyaudio` and grant microphone permission
- Mouse control not working on macOS: enable Accessibility for the app
- AI screen analysis offline: set `GEMINI_API_KEY` in `.env`

## Release Checklist

1. Build the bundle with `bash setup_macos_app.sh`
2. Run the app and verify camera, gestures, and settings panel
3. Sign the bundle with `codesign`
4. Notarize with `xcrun notarytool`
5. Staple the ticket with `xcrun stapler`

# GEMINI.md - Hand Control System Instructional Context

This file provides the primary instructional context for AI agents working on the **Hand Control System** project. This is an AI-driven, cross-platform hand gesture controller designed for macOS, Windows, and Linux.

## Project Overview
The Hand Control System combines real-time hand tracking, per-hand gesture bindings, voice commands, and Gemini-based screen analysis into a lightweight, high-performance runtime. It aims to bridge the gap between physical movements and digital interaction using standard webcams and minimal hardware.

### Core Architecture
The project follows a modular architecture for clear separation of concerns:
- **`launcher.py`**: Universal entry point. Handles transparent intro, platform detection, and launches either the menu-bar app or the standalone window.
- **`main.py`**: Core application engine (`GestureControlApp`). Orchestrates camera input, tracking, processing, and UI rendering.
- **`hand_tracker.py`**: Wraps MediaPipe Hands to extract 21 landmarks and detect gestures (Pinch, Click, Grab, Scroll, etc.) using a Finite State Machine (FSM).
- **`system_control.py`**: OS-level interaction layer. Uses PyAutoGUI and Pynput for mouse movement, keyboard shortcuts, scrolling, and zooming.
- **`interaction_system.py`**: "Liquid Glass" HUD/Dashboard rendering engine for a futuristic visual experience.
- **`settings_manager.py` / `settings_panel.py`**: Configuration persistence and an advanced Tkinter-based settings UI with themes.
- **`voice_system.py`**: Integrated speech recognition and TTS for multimodal control.
- **`llm_system.py`**: Integration with Gemini (Google Generative AI) for contextual screen analysis and reason-based commands.
- **`runtime_paths.py` / `app_logging.py`**: Cross-platform path management and structured logging.

## Tech Stack
- **Languages**: Python 3.10+
- **Computer Vision**: OpenCV, MediaPipe
- **System Automation**: PyAutoGUI, Pynput, Scipy
- **Voice Intelligence**: SpeechRecognition, Pyttsx3
- **AI/LLM**: Google Generative AI (Gemini Flash)
- **UI Libraries**: Tkinter, Rumps (macOS), NumPy (Matrix Rendering)

## Building and Running
The project uses a `Makefile` for standard operations.

- **Installation**:
  ```bash
  make install
  # or
  python install.py
  ```
- **Execution**:
  ```bash
  make run
  # or
  python launcher.py
  ```
- **Settings Panel**:
  ```bash
  python launcher.py --settings-panel
  ```
- **Testing**:
  ```bash
  make test
  # or
  python test.py
  ```
- **macOS Bundle**:
  ```bash
  bash setup_macos_app.sh
  ```

## Development Guidelines

### 1. Modular Design & Extensibility
- New gestures should be added to `hand_tracker.py`.
- New OS actions should be implemented in `system_control.py`.
- UI elements must use the `DashboardBuilder` and `GlassRenderer` in `interaction_system.py`.

### 2. Error Handling & Fallbacks
- The system must remain functional even if optional dependencies (e.g., `rumps`, `pyaudio`, `GEMINI_API_KEY`) are missing.
- Use `app_logging.py` to log events with appropriate levels.
- Crash logs are stored in the runtime directory managed by `runtime_paths.py`.

### 3. Cross-Platform Consistency
- Always use `runtime_paths.py` for file operations to ensure compatibility across macOS, Windows, and Linux.
- Check `sys.platform` only when absolutely necessary (e.g., menu bar support).

### 4. Code Style
- Follow PEP 8 standards.
- Prefer explicit over implicit.
- Use structured logging with `extra` fields for better debuggability.

## Key Files Directory
- `launcher.py`: Entry point and startup logic.
- `main.py`: Main multimodal interaction loop.
- `hand_tracker.py`: Geometry and FSM-based gesture detection.
- `system_control.py`: Execution of system-level actions.
- `settings_manager.py`: User profile and binding persistence.
- `interaction_system.py`: HUD Rendering and UI interactions.
- `SKILLS.md`: Detailed description of AI agent capabilities.
- `AGENTS.md`: Vision, roadmap, and core algorithm explanation.

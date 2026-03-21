# Quickstart

## 1. Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Run

```bash
python launcher.py
```

Open the settings panel directly with:

```bash
python launcher.py --settings-panel
```

## 3. Use

- Move your hand to move the cursor
- Pinch to click
- Open fist to drag
- Peace gesture for right click
- Use the settings panel to tune mouse direction, gain, smoothing, scroll, zoom, and bindings
- Set different actions for left and right hand
- Choose a light, dark, or midnight theme for the settings panel

## 4. Optional Features

- Add `GEMINI_API_KEY` in `.env` to enable screen analysis
- Install `pyaudio` for microphone input and voice commands
- Use profiles to save different setups for different users or workflows

## 5. macOS Bundle

```bash
bash setup_macos_app.sh
```

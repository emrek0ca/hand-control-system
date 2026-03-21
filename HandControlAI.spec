# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import plistlib

from PyInstaller.utils.hooks import collect_all

try:
    ROOT = Path(__file__).resolve().parent
except NameError:
    ROOT = Path.cwd()

with (ROOT / "resources" / "macos" / "Info.plist").open("rb") as fh:
    info_plist = plistlib.load(fh)

datas = [
    (str(ROOT / "requirements.txt"), "."),
    (str(ROOT / "AGENTS.md"), "."),
    (str(ROOT / "SKILLS.md"), "."),
]
binaries = []
hiddenimports = [
    "cv2",
    "numpy",
    "pyautogui",
    "pyttsx3",
    "speech_recognition",
    "google.generativeai",
    "PIL",
    "PIL.Image",
    "rumps",
    "tkinter",
    "settings_panel",
    "settings_manager",
]
tmp_ret = collect_all("mediapipe")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    [str(ROOT / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HandControlAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='HandControlAI',
)
app = BUNDLE(
    coll,
    name='HandControlAI.app',
    icon=None,
    bundle_identifier='com.ai.handcontrol',
    info_plist=info_plist,
)

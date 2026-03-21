"""
Universal AI Agent Launcher - PRO Edition
Handles transparent intro and bundled app path resolving.
"""

import os
import platform
import sys
import time
import traceback

from app_logging import setup_logging
from runtime_paths import ensure_runtime_dirs, get_crash_log_path
from version import __version__

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def run_transparent_intro():
    """Shows a floating, transparent welcome text using Tkinter."""
    try:
        import tkinter as tk
    except Exception:
        return

    try:
        root = tk.Tk()
        root.title("AI Agent Intro")

        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        root.overrideredirect(True)
        root.attributes("-topmost", True)

        if sys.platform == "darwin":
            try:
                root.attributes("-transparent", True)
                root.config(bg="systemTransparent")
                bg_color = "systemTransparent"
            except Exception:
                root.config(bg="black")
                bg_color = "black"
        else:
            try:
                root.attributes("-transparentcolor", "black")
            except Exception:
                pass
            root.config(bg="black")
            bg_color = "black"

        win_w, win_h = 720, 320
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        root.attributes("-alpha", 0.0)

        label = tk.Label(root, text="MERHABA", font=("Helvetica", 72, "bold"), fg="#FFFFFF", bg=bg_color)
        label.pack(expand=True)

        sub_label = tk.Label(root, text="AI AGENT INITIALIZING...", font=("Courier", 13), fg="#FFFFFF", bg=bg_color)
        sub_label.pack()

        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.06
                root.attributes("-alpha", alpha)
                root.after(35, lambda: fade_in(alpha))
            else:
                root.after(1200, fade_out)

        def fade_out(alpha=1.0):
            if alpha > 0:
                alpha -= 0.06
                root.attributes("-alpha", alpha)
                root.after(35, lambda: fade_out(alpha))
            else:
                root.destroy()

        root.after(100, fade_in)
        root.mainloop()
    except Exception:
        return


def _write_crash_report(exc: Exception):
    logger = setup_logging()
    logger.exception("launcher_crash")
    ensure_runtime_dirs()
    crash_log = get_crash_log_path()
    crash_log.parent.mkdir(parents=True, exist_ok=True)
    with crash_log.open("w", encoding="utf-8") as f:
        f.write(f"{exc}\n")
        f.write(traceback.format_exc())

def start_main():
    """Launch the main AI Agent loop in background and start menu."""
    try:
        logger = setup_logging()
        ensure_runtime_dirs()
        logger.info(
            "launcher_start",
            extra={"event": "launcher_start", "platform": platform.system(), "version": __version__},
        )
        fallback_reason = "non_darwin"
        if platform.system() == "Darwin":
            try:
                from menu_app import HandControlMenuApp, RUMPS_AVAILABLE
                if RUMPS_AVAILABLE:
                    app = HandControlMenuApp()
                    app.start_agent_thread()
                    app.run()
                    return
                fallback_reason = "rumps_unavailable"
            except Exception:
                fallback_reason = "menu_import_failed"

        logger.info(
            "launcher_fallback",
            extra={"event": "launcher_fallback", "reason": fallback_reason, "platform": platform.system()},
        )

        from main import GestureControlApp
        app = GestureControlApp(headless=False)
        app.run()
    except Exception as e:
        _write_crash_report(e)
        raise e

if __name__ == "__main__":
    if "--settings-panel" in sys.argv:
        try:
            from settings_panel import run_settings_panel
        except Exception as exc:
            print(f"Settings panel unavailable: {exc}")
            sys.exit(1)
        run_settings_panel()
    else:
        # 1. Floating Welcome
        run_transparent_intro()
        
        # 2. Main Engine
        start_main()

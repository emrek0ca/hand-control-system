"""
Universal AI Agent Launcher - PRO Edition
Handles transparent intro and bundled app path resolving.
"""

import os
import sys
import time
import tkinter as tk
import threading

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def run_transparent_intro():
    """Shows a floating, transparent welcome text using Tkinter."""
    root = tk.Tk()
    root.title("AI Agent Intro")
    
    # Screen dimensions
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    
    # Window settings: Transparent, No borders, Always on top
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparent", "black") # Makes black background invisible
    root.config(bg="black")
    
    # Center the window
    win_w, win_h = 800, 400
    x = (screen_w - win_w) // 2
    y = (screen_h - win_h) // 2
    root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # Text Frame
    label = tk.Label(root, text="MERHABA", font=("Helvetica", 80, "bold"), 
                     fg="#00FFFF", bg="black")
    label.pack(expand=True)
    
    sub_label = tk.Label(root, text="AI AGENT INITIALIZING...", font=("Courier", 14), 
                         fg="#AAAAAA", bg="black")
    sub_label.pack()

    # Simple Fade In/Out Animation
    def fade_out(alpha=1.0):
        if alpha > 0:
            alpha -= 0.05
            root.attributes("-alpha", alpha)
            root.after(50, lambda: fade_out(alpha))
        else:
            root.destroy()

    def start_fade():
        time.sleep(2.5)
        fade_out()

    threading.Thread(target=start_fade, daemon=True).start()
    root.mainloop()

def start_main():
    """Launch the main AI Agent loop."""
    try:
        from main import GestureControlApp
        # Ensure we are in the right directory for relative assets
        os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
        app = GestureControlApp()
        app.run()
    except Exception as e:
        # Log error to a file if it's a bundled app to debug crashes
        with open("crash_log.txt", "w") as f:
            import traceback
            f.write(str(e))
            f.write(traceback.format_exc())
        raise e

if __name__ == "__main__":
    # 1. Floating Welcome
    run_transparent_intro()
    
    # 2. Main Engine
    start_main()

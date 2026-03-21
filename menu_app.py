"""
macOS Menu Bar Application & Headless Controller
Runs the HandControlAI completely in the background.
"""

import rumps
import threading
import time
import tkinter as tk
from tkinter import ttk
from main import GestureControlApp

class SettingsWindow:
    def __init__(self, app_ref):
        self.app_ref = app_ref
        self.root = tk.Tk()
        self.root.title("HandControlAI Settings")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        
        # Bring to front on macOS
        import os
        os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

        ttk.Label(self.root, text="Agent Sensitivity Configuration", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Pinch Threshold
        ttk.Label(self.root, text="Click Sensitivity (Pinch Threshold)").pack(pady=5)
        self.pinch_var = tk.DoubleVar(value=self.app_ref.tracker.PINCH_THRESH if self.app_ref else 0.12)
        pinch_slider = ttk.Scale(self.root, from_=0.05, to=0.3, variable=self.pinch_var, orient='horizontal', length=200)
        pinch_slider.pack()

        # Motion Smoothing
        ttk.Label(self.root, text="Motion Smoothing (Lower = Smoother)").pack(pady=5)
        self.smooth_var = tk.DoubleVar(value=0.8) # Default approx
        smooth_slider = ttk.Scale(self.root, from_=0.1, to=1.0, variable=self.smooth_var, orient='horizontal', length=200)
        smooth_slider.pack()

        # Apply Button
        ttk.Button(self.root, text="Apply & Save", command=self.apply_settings).pack(pady=20)

    def apply_settings(self):
        if self.app_ref:
            pinch = self.pinch_var.get()
            smooth = self.smooth_var.get()
            # Vel lock can be roughly tied to smooth
            vel_lock = 0.15 - (smooth * 0.05) 
            self.app_ref.set_sensitivity(pinch, vel_lock, smooth)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


class HandControlMenuApp(rumps.App):
    def __init__(self):
        # 🖐️ Icon can be customized later, using text for now
        super(HandControlMenuApp, self).__init__("🖐 AI", quit_button=None)
        
        self.agent_app = None
        self.agent_thread = None
        
        # Menu Items
        self.status_item = rumps.MenuItem("Status: Initializing...", callback=None)
        self.toggle_item = rumps.MenuItem("Pause Agent", callback=self.toggle_control)
        self.settings_item = rumps.MenuItem("Settings...", callback=self.open_settings)
        self.quit_item = rumps.MenuItem("Quit", callback=self.quit_app)
        
        self.menu = [
            self.status_item,
            None, # Separator
            self.toggle_item,
            self.settings_item,
            None,
            self.quit_item
        ]

    def start_agent_thread(self):
        print("[MENU] Starting Headless Agent...")
        self.agent_app = GestureControlApp(headless=True)
        self.agent_thread = threading.Thread(target=self.agent_app.run, daemon=True)
        self.agent_thread.start()
        self.status_item.title = "Status: ACTIVE"

    def toggle_control(self, sender):
        if self.agent_app:
            self.agent_app.system_active = not self.agent_app.system_active
            if self.agent_app.system_active:
                sender.title = "Pause Agent"
                self.status_item.title = "Status: ACTIVE"
                self.title = "🖐 AI"
            else:
                sender.title = "Resume Agent"
                self.status_item.title = "Status: PAUSED"
                self.title = "⏸ AI"

    def open_settings(self, sender):
        """Open Tkinter settings window on the main thread using an external process or careful loop integration.
           Tkinter and rumps don't mix perfectly on the same thread loop, so we run Tkinter in a short-lived loop.
        """
        # Actually, running Tkinter loop while rumps is running can block the menu.
        # But for a quick settings panel, we can launch it and wait.
        def run_tk():
            SettingsWindow(self.agent_app).run()
        
        # Run in a separate thread so the menu doesn't freeze completely
        threading.Thread(target=run_tk, daemon=True).start()

    def quit_app(self, sender):
        print("[MENU] Shutting down agent gracefully...")
        if self.agent_app:
            self.agent_app.running = False
        if self.agent_thread:
            self.agent_thread.join(timeout=2.0)
        rumps.quit_application()

if __name__ == '__main__':
    app = HandControlMenuApp()
    # Start agent in background before starting menu loop
    app.start_agent_thread()
    app.run()

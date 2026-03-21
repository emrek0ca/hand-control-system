"""
macOS Menu Bar Application & Headless Controller
Runs the HandControlAI completely in the background.
"""

import threading
import time

try:
    import rumps
except Exception:  # pragma: no cover - optional dependency
    rumps = None

from main import GestureControlApp

RUMPS_AVAILABLE = rumps is not None

if RUMPS_AVAILABLE:
    class HandControlMenuApp(rumps.App):
        def __init__(self):
            super(HandControlMenuApp, self).__init__("🖐 AI", quit_button=None)

            self.agent_app = None
            self.agent_thread = None

            self.status_item = rumps.MenuItem("Status: Initializing...", callback=None)
            self.toggle_item = rumps.MenuItem("Pause Agent", callback=self.toggle_control)

            self.settings_menu = rumps.MenuItem("Sensitivity Settings")
            self.settings_menu.add(rumps.MenuItem("Low (Smooth but Slow)", callback=lambda s: self.set_sensitivity(s, 0.20, 0.90)))
            self.settings_menu.add(rumps.MenuItem("Medium (Balanced)", callback=lambda s: self.set_sensitivity(s, 0.12, 0.70)))
            self.settings_menu.add(rumps.MenuItem("High (Fast and Responsive)", callback=lambda s: self.set_sensitivity(s, 0.08, 0.40)))
            self.settings_item = rumps.MenuItem("Settings...", callback=self.open_settings_panel)

            self.quit_item = rumps.MenuItem("Quit", callback=self.quit_app)

            self.menu = [
                self.status_item,
                None,
                self.toggle_item,
                self.settings_menu,
                self.settings_item,
                None,
                self.quit_item
            ]

        def set_sensitivity(self, sender, pinch, smooth):
            if self.agent_app:
                vel_lock = 0.15 - (smooth * 0.05)
                self.agent_app.set_sensitivity(pinch, vel_lock, smooth)
                rumps.notification("HandControlAI", "Settings Updated", f"Sensitivity set to: {sender.title}")

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

        def open_settings_panel(self, sender):
            if self.agent_app:
                self.agent_app.open_settings_panel()

        def quit_app(self, sender):
            print("[MENU] Shutting down agent gracefully...")
            if self.agent_app:
                self.agent_app.running = False
            if self.agent_thread:
                self.agent_thread.join(timeout=2.0)
            rumps.quit_application()
else:
    class HandControlMenuApp:
        def __init__(self):
            self.agent_app = None
            self.agent_thread = None

        def set_sensitivity(self, sender, pinch, smooth):
            if self.agent_app:
                vel_lock = 0.15 - (smooth * 0.05)
                self.agent_app.set_sensitivity(pinch, vel_lock, smooth)

        def start_agent_thread(self):
            print("[MENU] rumps unavailable, starting core app directly...")
            self.agent_app = GestureControlApp(headless=False)

        def toggle_control(self, sender=None):
            if self.agent_app:
                self.agent_app.system_active = not self.agent_app.system_active

        def open_settings_panel(self, sender=None):
            if self.agent_app:
                self.agent_app.open_settings_panel()

        def quit_app(self, sender=None):
            if self.agent_app:
                self.agent_app.running = False

        def run(self):
            if self.agent_app is None:
                self.start_agent_thread()
            self.agent_app.run()


if __name__ == '__main__':
    app = HandControlMenuApp()
    app.start_agent_thread()
    app.run()

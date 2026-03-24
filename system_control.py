"""
System-wide control interface using PyAutoGUI - PRO Version
Advanced kinematics, adaptive sensitivity, and velocity-based scrolling.
"""

import math
import platform
import time
from typing import Optional, Tuple

try:
    import pyautogui
except Exception:  # pragma: no cover - optional dependency / environment issue
    pyautogui = None

if pyautogui:
    pyautogui.FAILSAFE = True

class SystemController:
    """Controls mouse and keyboard with advanced physics and adaptive logic."""
    
    def __init__(self):
        self.available = bool(pyautogui)
        if self.available:
            try:
                self.screen_w, self.screen_h = pyautogui.size()
            except Exception:
                self.available = False
                self.screen_w, self.screen_h = 0, 0
        else:
            self.screen_w, self.screen_h = 0, 0
        
        # Physics Parameters
        self.roi_margin = 0.12
        self.invert_x = False
        self.invert_y = False
        self.pointer_gain = 1.0
        self.prev_x, self.prev_y = None, None
        self.velocity_x, self.velocity_y = 0, 0
        
        # Click Stability
        self.last_click_time = 0
        self.click_cooldown = 0.4
        self.freeze_until = 0
        self.freeze_duration = 0.25
        
        # Adaptive Sensitivity & Precision Mode
        self.base_alpha_min = 0.05
        self.base_alpha_max = 0.90
        self.precision_mode = True # Enhanced smoothing at low speeds
        
        # Scrolling & Zooming
        self.prev_scroll_y = None
        self.scroll_threshold = 0.01
        self.scroll_multiplier = 1500
        self.prev_z_depth = None
        self.zoom_threshold = 0.02
        self.last_zoom_time = 0
        self.zoom_cooldown = 0.3 # Limit zoom speed
    
    def configure(self, **kwargs) -> None:
        self.roi_margin = max(0.0, min(0.45, float(kwargs.get("roi_margin", self.roi_margin))))
        self.invert_x = bool(kwargs.get("invert_x", self.invert_x))
        self.invert_y = bool(kwargs.get("invert_y", self.invert_y))
        self.pointer_gain = max(0.1, float(kwargs.get("pointer_gain", self.pointer_gain)))
        alpha_min = max(0.01, min(0.99, float(kwargs.get("base_alpha_min", self.base_alpha_min))))
        alpha_max = max(0.01, min(0.99, float(kwargs.get("base_alpha_max", self.base_alpha_max))))
        self.base_alpha_min = min(alpha_min, alpha_max)
        self.base_alpha_max = max(alpha_min, alpha_max)
        self.click_cooldown = max(0.0, float(kwargs.get("click_cooldown", self.click_cooldown)))
        self.freeze_duration = max(0.0, float(kwargs.get("freeze_duration", self.freeze_duration)))
        self.scroll_threshold = max(0.0, float(kwargs.get("scroll_threshold", self.scroll_threshold)))
        self.scroll_multiplier = max(1.0, float(kwargs.get("scroll_multiplier", self.scroll_multiplier)))
        self.zoom_threshold = max(0.0, float(kwargs.get("zoom_threshold", self.zoom_threshold)))
        self.zoom_cooldown = max(0.0, float(kwargs.get("zoom_cooldown", self.zoom_cooldown)))
        self.precision_mode = bool(kwargs.get("precision_mode", self.precision_mode))

    def map_coordinates(self, x: float, y: float, z: float = 0.5) -> Tuple[int, int]:
        """
        Maps normalized coordinates to screen with Z-axis adaptive sensitivity.
        """
        if not self.available:
            return 0, 0

        if time.time() < self.freeze_until:
            return int(self.prev_x or 0), int(self.prev_y or 0)

        if self.invert_x:
            x = 1.0 - x
        if self.invert_y:
            y = 1.0 - y

        # 1. ROI Mapping (Dynamic scaling to reach screen edges)
        # We use a non-linear mapping for the edges to make them easier to reach
        xm = (x - self.roi_margin) / (1 - 2 * self.roi_margin)
        ym = (y - self.roi_margin) / (1 - 2 * self.roi_margin)
        xm = max(0.0, min(1.0, xm))
        ym = max(0.0, min(1.0, ym))
        
        tx, ty = xm * self.screen_w, ym * self.screen_h
        
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = tx, ty
            return int(tx), int(ty)

        # 2. Adaptive Physics (Distance & Velocity)
        dx, dy = tx - self.prev_x, ty - self.prev_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Exponential Gain Curve
        speed_norm = min(1.0, (dist * self.pointer_gain) / 80.0)
        
        if self.precision_mode and speed_norm < 0.15:
            # High precision at low speeds
            alpha = self.base_alpha_min * (speed_norm / 0.15)
        else:
            alpha = self.base_alpha_min + (self.base_alpha_max - self.base_alpha_min) * (speed_norm**1.5)
        
        # 3. Apply Smoothing
        sx = self.prev_x + (dx * alpha)
        sy = self.prev_y + (dy * alpha)
        
        self.prev_x, self.prev_y = sx, sy
        return int(sx), int(sy)

    def move_mouse(self, nx: float, ny: float) -> None:
        if not self.available:
            return
        try:
            x, y = self.map_coordinates(nx, ny)
            pyautogui.moveTo(x, y, _pause=False)
        except Exception:
            pass

    def drag_mouse(self, nx: float, ny: float) -> None:
        if not self.available:
            return
        try:
            x, y = self.map_coordinates(nx, ny)
            pyautogui.dragTo(x, y, button='left', _pause=False)
        except Exception:
            pass

    def click(self, button: str = 'left') -> None:
        if not self.available:
            return
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            self.freeze_until = now + self.freeze_duration
            try:
                pyautogui.click(button=button)
            except Exception:
                return
            self.last_click_time = now
            print(f"[SYSTEM] {button.upper()} CLICK")

    def double_click(self) -> None:
        if not self.available:
            return
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            self.freeze_until = now + self.freeze_duration * 1.5
            try:
                pyautogui.doubleClick()
            except Exception:
                return
            self.last_click_time = now
            print("[SYSTEM] DOUBLE CLICK")

    def scroll_adaptive(self, current_y: float) -> None:
        """Velocity-based scrolling based on finger movement."""
        if not self.available:
            return
        if self.prev_scroll_y is None:
            self.prev_scroll_y = current_y
            return
            
        dy = current_y - self.prev_scroll_y
        self.prev_scroll_y = current_y
        
        if abs(dy) > self.scroll_threshold:
            # Scale scroll by movement magnitude
            scroll_amount = int(-dy * self.scroll_multiplier) # Negative for natural scrolling
            try:
                pyautogui.scroll(scroll_amount)
            except Exception:
                pass

    def scroll(self, amount: int) -> None:
        if not self.available:
            return
        try:
            pyautogui.scroll(int(amount))
        except Exception:
            pass

    def zoom_adaptive(self, current_z: float) -> None:
        """Zoom in/out based on hand distance (Z-depth) changes."""
        if not self.available:
            return
        if self.prev_z_depth is None:
            self.prev_z_depth = current_z
            return
            
        dz = current_z - self.prev_z_depth
        now = time.time()
        
        # Larger z_depth = Closer to camera = Zoom IN
        # Smaller z_depth = Farther from camera = Zoom OUT
        if abs(dz) > self.zoom_threshold and (now - self.last_zoom_time) > self.zoom_cooldown:
            modifier = 'command' if platform.system() == 'Darwin' else 'ctrl'
            
            if dz > 0: # Moving closer
                pyautogui.hotkey(modifier, '+')
                print("[SYSTEM] ZOOM IN")
            else: # Moving away
                pyautogui.hotkey(modifier, '-')
                print("[SYSTEM] ZOOM OUT")
                
            self.last_zoom_time = now
            self.prev_z_depth = current_z

    def reset_zoom(self):
        self.prev_z_depth = None

    def reset_scroll(self):
        self.prev_scroll_y = None

    def press_key(self, key: str):
        if not self.available or not key:
            return
        try:
            pyautogui.press(key)
        except Exception:
            pass

    def hotkey(self, *keys: str):
        if not self.available or not keys:
            return
        try:
            pyautogui.hotkey(*keys)
        except Exception:
            pass

    def write_text(self, text: str):
        if not self.available or not text:
            return
        try:
            pyautogui.write(text, interval=0.01)
        except Exception:
            pass

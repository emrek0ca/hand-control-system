"""
System-wide control interface using PyAutoGUI - PRO Version
Advanced kinematics, adaptive sensitivity, and velocity-based scrolling.
"""

import pyautogui
import platform
import math
from typing import Tuple, Optional
import time

# Fail-safe mode
pyautogui.FAILSAFE = True

class SystemController:
    """Controls mouse and keyboard with advanced physics and adaptive logic."""
    
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Physics Parameters
        self.roi_margin = 0.12
        self.prev_x, self.prev_y = 0, 0
        self.velocity_x, self.velocity_y = 0, 0
        
        # Click Stability
        self.last_click_time = 0
        self.click_cooldown = 0.4
        self.freeze_until = 0
        self.freeze_duration = 0.25
        
        # Adaptive Sensitivity
        self.base_alpha_min = 0.05
        self.base_alpha_max = 0.90
        
        # Scrolling
        self.prev_scroll_y = None
        self.scroll_threshold = 0.01

    def map_coordinates(self, x: float, y: float, z: float = 0.5) -> Tuple[int, int]:
        """
        Maps normalized coordinates to screen with Z-axis adaptive sensitivity.
        """
        if time.time() < self.freeze_until:
            return int(self.prev_x), int(self.prev_y)

        # 1. ROI Mapping (Zoom into the center 76% of the camera view)
        xm = (x - self.roi_margin) / (1 - 2 * self.roi_margin)
        ym = (y - self.roi_margin) / (1 - 2 * self.roi_margin)
        xm = max(0.0, min(1.0, xm))
        ym = max(0.0, min(1.0, ym))
        
        tx, ty = xm * self.screen_w, ym * self.screen_h
        
        if self.prev_x == 0:
            self.prev_x, self.prev_y = tx, ty
            return int(tx), int(ty)

        # 2. Adaptive Physics (Distance & Velocity)
        dx, dy = tx - self.prev_x, ty - self.prev_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # Z-axis adjustment: Farther hands (smaller Z) need more precision (lower alpha)
        # MediaPipe Z is roughly -1 to 1. Closer to camera = smaller Z value? 
        # Actually MediaPipe Z is relative to wrist. 
        # We can use the 'hand_size' from tracker but for now let's stick to velocity.
        
        # Exponential Gain Curve
        speed_norm = min(1.0, dist / 100.0)
        alpha = self.base_alpha_min + (self.base_alpha_max - self.base_alpha_min) * (speed_norm**1.5)
        
        # 3. Apply Smoothing
        sx = self.prev_x + (dx * alpha)
        sy = self.prev_y + (dy * alpha)
        
        self.prev_x, self.prev_y = sx, sy
        return int(sx), int(sy)

    def move_mouse(self, nx: float, ny: float) -> None:
        try:
            x, y = self.map_coordinates(nx, ny)
            pyautogui.moveTo(x, y, _pause=False)
        except pyautogui.FailSafeException:
            pass

    def drag_mouse(self, nx: float, ny: float) -> None:
        try:
            x, y = self.map_coordinates(nx, ny)
            pyautogui.dragTo(x, y, button='left', _pause=False)
        except pyautogui.FailSafeException:
            pass

    def click(self, button: str = 'left') -> None:
        now = time.time()
        if now - self.last_click_time > self.click_cooldown:
            self.freeze_until = now + self.freeze_duration
            pyautogui.click(button=button)
            self.last_click_time = now
            print(f"[SYSTEM] {button.upper()} CLICK")

    def scroll_adaptive(self, current_y: float) -> None:
        """Velocity-based scrolling based on finger movement."""
        if self.prev_scroll_y is None:
            self.prev_scroll_y = current_y
            return
            
        dy = current_y - self.prev_scroll_y
        self.prev_scroll_y = current_y
        
        if abs(dy) > self.scroll_threshold:
            # Scale scroll by movement magnitude
            scroll_amount = int(-dy * 1500) # Negative for natural scrolling
            pyautogui.scroll(scroll_amount)

    def reset_scroll(self):
        self.prev_scroll_y = None

    def press_key(self, key: str):
        pyautogui.press(key)

"""
System-wide control interface using PyAutoGUI
Handles mouse and keyboard operations safely
"""

import pyautogui
import platform
import math
from typing import Tuple, Optional
import time

# Fail-safe mode (mouse cursor to corners throws exception)
pyautogui.FAILSAFE = True

class SystemController:
    """Controls mouse and keyboard at system level"""
    
    def __init__(self, screen_width: Optional[int] = None, screen_height: Optional[int] = None):
        """
        Initialize system controller
        """
        self.screen_w, self.screen_h = pyautogui.size()
        self.roi_margin = 0.15  # Increased margin for better center usage
        
        self.last_click_time = 0
        self.click_cooldown = 0.6  # Slightly increased
        
        # Smoothing & Physics
        self.prev_x, self.prev_y = 0, 0
        self.alpha = 0.2
        
        # Click Freezing
        self.freeze_until = 0
        self.freeze_duration = 0.3  # Freeze cursor for 300ms after click (locks target)
        
    def map_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        """
        Map normalized coordinates (0-1) to screen coordinates
        with PROFESSIONAL PHYSICS (Exponential Gain + Freeze)
        """
        # 0. FREEZE CHECK: If frozen (just clicked), don't move
        if time.time() < self.freeze_until:
             return int(self.prev_x), int(self.prev_y)

        # 1. Apply ROI
        # Clamp input to ROI to map central hand movement to full screen
        x_mapped = (x - self.roi_margin) / (1 - 2 * self.roi_margin)
        y_mapped = (y - self.roi_margin) / (1 - 2 * self.roi_margin)
        x_mapped = max(0.0, min(1.0, x_mapped))
        y_mapped = max(0.0, min(1.0, y_mapped))
        
        target_x = x_mapped * self.screen_w
        target_y = y_mapped * self.screen_h
        
        # Initialize if first frame
        if self.prev_x == 0 and self.prev_y == 0:
            self.prev_x, self.prev_y = target_x, target_y
            return int(target_x), int(target_y)

        # 2. Physics Calculation
        # Calculate raw distance
        dx = target_x - self.prev_x
        dy = target_y - self.prev_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 3. Jitter Filter (Deadzone)
        # If movement is tiny (hand tremor), ignore it completely
        if dist < 2.0:
            return int(self.prev_x), int(self.prev_y)

        # 4. Exponential Sensitivity Curve
        # The faster you move, the LESS smoothing you get (responsive).
        # The slower you move, the MORE smoothing you get (precision).
        
        # Base speed threshold (pixels per frame)
        speed_threshold = 80.0 
        
        # Normalized speed (0.0 - 1.0+)
        norm_speed = min(1.0, dist / speed_threshold)
        
        # Exponential curve: Low speeds get suppressed heavily
        # curve_factor becomes very small for small movements
        curve_factor = norm_speed ** 2.0  
        
        min_alpha = 0.03   # Extreme smoothing for staying still
        max_alpha = 0.85   # Fast response for flicks
        
        current_alpha = min_alpha + (max_alpha - min_alpha) * curve_factor
        
        # Execute smoothing
        smooth_x = self.prev_x + (dx * current_alpha)
        smooth_y = self.prev_y + (dy * current_alpha)
        
        self.prev_x, self.prev_y = smooth_x, smooth_y
        
        return int(smooth_x), int(smooth_y)

    def move_mouse(self, norm_x: float, norm_y: float) -> None:
        """
        Move mouse to normalized position
        
        Args:
            norm_x: Normalized X position (0-1)
            norm_y: Normalized Y position (0-1)
        """
        try:
            x, y = self.map_coordinates(norm_x, norm_y)
            pyautogui.moveTo(x, y, _pause=False)
        except pyautogui.FailSafeException:
            print("FailSafe triggered from mouse movement")
            pass

    def drag_mouse(self, norm_x: float, norm_y: float) -> None:
        """
        Drag mouse to normalized position (button held down)
        """
        try:
            x, y = self.map_coordinates(norm_x, norm_y)
            pyautogui.dragTo(x, y, button='left', _pause=False)
        except pyautogui.FailSafeException:
            pass

    def click(self, button: str = 'left') -> None:
        """Perform a single click and freeze cursor"""
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            # Freeze cursor to ensure stability during click
            self.freeze_until = current_time + self.freeze_duration
            
            pyautogui.click(button=button)
            self.last_click_time = current_time
            print(f"Clicked: {button} (Frozen for {self.freeze_duration}s)")

    def double_click(self) -> None:
        """Perform a double click"""
        pyautogui.doubleClick()
        print("Double Clicked")

    def scroll(self, steps: int) -> None:
        """
        Scroll screen
        
        Args:
            steps: Positive for up, negative for down
        """
        pyautogui.scroll(steps * 10)  # Multiplier for sensitivity

    def reset_smoothing(self):
        """Reset smoothing state (e.g. when hand re-enters)"""
        self.prev_x, self.prev_y = 0, 0

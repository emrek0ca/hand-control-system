"""
Hand Gesture Control System - PRO Version
Application: AI-Driven Multimodal Interaction Agent
"""

import cv2
import numpy as np
from hand_tracker import HandTracker, GestureType, GestureState
from interaction_system import DashboardBuilder
from voice_system import VoiceCommandEngine, VoiceState
from system_control import SystemController
from advanced_features import AdvancedGestureRecognizer, GestureSequence
import sys
import time


class GestureControlApp:
    """Main AI Agent Application for Hand Gesture and Voice Control."""
    
    def __init__(self, camera_id: int = 0, headless: bool = False):
        self.headless = headless
        
        # Camera Setup
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("Camera not accessible.")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Modules
        self.tracker = HandTracker(confidence_threshold=0.7)
        self.controller = SystemController()
        self.voice = VoiceCommandEngine(on_result=self._on_voice_command)
        self.recognizer = AdvancedGestureRecognizer()
        
        # State
        self.system_active = True
        self.running = True
        self.show_debug = True
        self.current_hand = None
        self.last_swipe = None
        self.swipe_time = 0
        
        # Calibration State
        self.is_calibrating = False
        self.calib_step = 0 # 0: Open Hand, 1: Pinch
        self.calib_samples = []
        self.calib_results = {"pinch": 0, "size": 0}
        
        # UI
        self.dashboard = DashboardBuilder(self.width, self.height)
        self._setup_ui()
        
        # Voice Commands Registry
        self.commands = self._setup_commands()
        
        # Performance
        self.fps = 0
        self.frame_count = 0
        
        # Initial Load
        self._load_calibration()

    def _setup_ui(self):
        """Build the interactive HUD overlay."""
        self.dashboard.add_button(10, 10, 140, 45, "DEBUG [D]", lambda: setattr(self, 'show_debug', not self.show_debug))
        self.dashboard.add_button(160, 10, 140, 45, "CONTROL [M]", self._toggle_system)
        self.dashboard.add_button(310, 10, 140, 45, "VOICE [V]", self.voice.listen_once)
        self.dashboard.add_button(460, 10, 140, 45, "CALIB [C]", self._start_calibration)

    def _setup_commands(self):
        """Define multimodal voice commands."""
        return [
            self.voice.create_command(["ekran", "görüntüsü"], self._action_screenshot, "Ekran görüntüsü al"),
            self.voice.create_command(["sistemi", "kapat"], self._toggle_system, "Sistem kontrolünü durdur"),
            self.voice.create_command(["sistemi", "aç"], self._toggle_system, "Sistem kontrolünü başlat"),
            self.voice.create_command(["tıkla"], lambda: self.controller.click('left'), "Sol tık yap"),
            self.voice.create_command(["sağ", "tık"], lambda: self.controller.click('right'), "Sağ tık yap"),
            self.voice.create_command(["bunu", "sil"], self._multimodal_delete, "Tutulan nesneyi sil"),
            self.voice.create_command(["kalibrasyon", "başlat"], self._start_calibration, "Kişisel kalibrasyonu başlat"),
        ]

    def _start_calibration(self):
        self.is_calibrating = True
        self.calib_step = 0
        self.calib_samples = []
        self.voice.speak("Kalibrasyon başladı. Lütfen elinizi açık şekilde kameraya tutun.")
        print("[AGENT] Calibration Started: Step 0 (Open Hand)")

    def _process_calibration(self, hand):
        """Analyze hand data during calibration steps."""
        # Normalize hand size (Wrist to Middle MCP)
        wrist = hand.smoothed_landmarks[0]
        mcp = hand.smoothed_landmarks[9]
        hand_size = np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2)
        
        if self.calib_step == 0:
            # Establishing Neutral Hand Size
            self.calib_samples.append(hand_size)
            if len(self.calib_samples) >= 30:
                self.calib_results["size"] = np.mean(self.calib_samples)
                self.calib_samples = []
                self.calib_step = 1
                self.voice.speak("Tamam. Şimdi işaret parmağınızla baş parmağınızı birleştirerek tık yapın ve tutun.")
                print(f"[AGENT] Neutral Size: {self.calib_results['size']:.4f}")
                
        elif self.calib_step == 1:
            # Establishing Pinch Threshold
            # We need raw pinch distance / current hand size
            thumb = hand.smoothed_landmarks[4]
            index = hand.smoothed_landmarks[8]
            pinch_dist = np.sqrt((thumb.x - index.x)**2 + (thumb.y - index.y)**2)
            self.calib_samples.append(pinch_dist / hand_size)
            
            if len(self.calib_samples) >= 30:
                self.calib_results["pinch"] = np.mean(self.calib_samples)
                # Apply results
                p_thresh = self.calib_results["pinch"] * 1.2 # Add margin
                r_thresh = p_thresh * 1.5
                self.tracker.apply_calibration(p_thresh, r_thresh, self.calib_results["size"])
                
                self.is_calibrating = False
                self.voice.speak("Kalibrasyon tamamlandı. Sistem size özel optimize edildi.")
                print(f"[AGENT] Calibrated Pinch: {p_thresh:.4f}")
                # Optional: Save to file (Step 3)
                self._save_calibration()

    def _save_calibration(self):
        import json
        data = {
            "pinch": self.tracker.PINCH_THRESH,
            "release": self.tracker.RELEASE_THRESH,
            "size": self.tracker.neutral_hand_size,
            "timestamp": time.time()
        }
        with open("calibration.json", "w") as f:
            json.dump(data, f)
        print("[AGENT] Calibration saved to calibration.json")

    def _load_calibration(self):
        import json
        import os
        if os.path.exists("calibration.json"):
            try:
                with open("calibration.json", "r") as f:
                    data = json.load(f)
                self.tracker.apply_calibration(data["pinch"], data["release"], data["size"])
                print("[AGENT] Calibration loaded from file.")
            except Exception:
                print("[AGENT] Failed to load calibration.")

    def _toggle_system(self):
        self.system_active = not self.system_active
        status = "aktif" if self.system_active else "pasif"
        self.voice.speak(f"Sistem kontrolü {status}")

    def _action_screenshot(self):
        cv2.imwrite(f"cap_{int(time.time())}.png", self.last_frame)
        self.voice.speak("Ekran görüntüsü kaydedildi.")

    def _multimodal_delete(self):
        """Example of Hybrid Control: Command while Grabbing."""
        if self.current_hand and self.current_hand.state == GestureState.GRABBING:
             self.controller.press_key('delete')
             self.voice.speak("Nesne silindi.")
        else:
             self.voice.speak("Silinecek bir nesne tutulmuyor.")

    def _on_voice_command(self, text: str):
        print(f"[VOICE] Raw: {text}")
        cmd = self.voice.match_command(text, self.commands)
        if cmd:
            print(f"[VOICE] Executing: {cmd['description']}")
            cmd['action']()
        else:
            self.voice.speak("Komut anlaşılamadı.")

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.last_frame = frame.copy()
        hands = self.tracker.process_frame(frame)
        self.current_hand = hands[0] if hands else None
        
        # 1. Visual Feedback (Skeleton)
        if not self.headless:
            frame = self.tracker.draw_hand_skeleton(frame, hands)
            
        # 2. Calibration Mode
        if self.is_calibrating and self.current_hand:
            self._process_calibration(self.current_hand)
            self._draw_calibration_hud(frame)
            return frame # Skip other logic during calibration
            
        # 3. Logic Implementation
        if self.current_hand and self.system_active:
            h = self.current_hand
            nx, ny = h.center[0], h.center[1]
            
            # Mouse Control
            if h.state in [GestureState.IDLE, GestureState.MOVING, GestureState.CLICKED, GestureState.RIGHT_CLICK]:
                self.controller.move_mouse(nx, ny)
                
            if h.state == GestureState.CLICKED:
                self.controller.click('left')
                
            if h.state == GestureState.RIGHT_CLICK:
                self.controller.click('right')
                
            if h.state == GestureState.GRABBING:
                self.controller.drag_mouse(nx, ny)
                
            if h.state == GestureState.SCROLLING:
                self.controller.scroll_adaptive(h.scroll_y)
            else:
                self.controller.reset_scroll()
                
            # Zoom Control (Using PEACE pose)
            if h.gesture == GestureType.PEACE:
                self.controller.zoom_adaptive(h.z_depth)
            else:
                self.controller.reset_zoom()
                
            # Voice Mode Trigger (Special pose)
            if h.gesture == GestureType.VOICE_MODE:
                self.voice.listen_once()
                
            # --- Swipe Logic ---
            swipe = self.tracker.detect_swipe()
            if swipe:
                self.last_swipe = swipe
                self.swipe_time = time.time()
                print(f"[AGENT] SWIPE: {swipe}")
                
                # Perform Action
                import platform
                mod = 'command' if platform.system() == 'Darwin' else 'alt'
                
                if swipe == "RIGHT":
                    self.controller.press_key('tab') # Simple tab for now or hotkey
                    # For browser tab: ctrl+tab
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'tab')
                elif swipe == "LEFT":
                    import pyautogui
                    pyautogui.hotkey('ctrl', 'shift', 'tab')
                elif swipe == "UP":
                    self.controller.press_key('up')
                elif swipe == "DOWN":
                    self.controller.press_key('down')

        # 3. UI Rendering
        if not self.headless:
            frame = self.dashboard.get_manager().draw_objects(frame)
            self._draw_hud(frame)
            
        return frame

    def _draw_calibration_hud(self, frame):
        """Draw calibration overlay with progress bar."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        progress = len(self.calib_samples) / 30.0
        bar_w = 400
        x = (self.width - bar_w) // 2
        y = self.height // 2
        
        # Text
        txt = "ADIM 1: Elinizi Açık Tutun" if self.calib_step == 0 else "ADIM 2: Tık Yapın ve Bekleyin"
        cv2.putText(frame, txt, (x, y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Progress Bar
        cv2.rectangle(frame, (x, y), (x + bar_w, y + 30), (100, 100, 100), -1)
        cv2.rectangle(frame, (x, y), (x + int(bar_w * progress), y + 30), (0, 255, 0), -1)

    def _draw_hud(self, frame):
        """Modern AI HUD Overlay."""
        # Status Bar
        status_color = (0, 255, 0) if self.system_active else (0, 0, 255)
        status_text = "SYSTEM ONLINE" if self.system_active else "SYSTEM OFFLINE"
        if self.tracker.is_calibrated: status_text += " | CALIBRATED"
        
        cv2.rectangle(frame, (0, self.height-40), (self.width, self.height), (20, 20, 20), -1)
        cv2.putText(frame, status_text, (20, self.height-12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Voice Status
        v_state = self.voice.state.name
        cv2.putText(frame, f"VOICE ENGINE: {v_state}", (self.width-250, self.height-12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Swipe Feedback
        if self.last_swipe and time.time() - self.swipe_time < 1.0:
            s_txt = f"SWIPE {self.last_swipe}!"
            cv2.putText(frame, s_txt, (self.width//2 - 100, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 255), 3)
        
        if self.show_debug:
            self._draw_debug(frame)

    def _draw_debug(self, frame):
        # Kinematics & Stats
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 70), (250, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        y = 95
        debug_info = [
            f"FPS: {self.fps}",
            f"STATE: {self.current_hand.state.name if self.current_hand else 'NONE'}",
            f"GESTURE: {self.current_hand.gesture.name if self.current_hand else 'NONE'}",
            f"VELOCITY: {self.current_hand.velocity:.4f}" if self.current_hand else "VELOCITY: 0",
            f"Z-DEPTH: {self.current_hand.z_depth:.4f}" if self.current_hand else "Z-DEPTH: 0"
        ]
        for line in debug_info:
            cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            y += 25

    def run(self):
        print("[AGENT] Initializing loop...")
        last_time = time.time()
        f_count = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret: break
                
                # Process
                out = self.process_frame(frame)
                
                # FPS
                f_count += 1
                if time.time() - last_time >= 1.0:
                    self.fps = f_count
                    f_count = 0
                    last_time = time.time()
                
                # Show
                if not self.headless:
                    cv2.imshow("Hand Control System - AI AGENT v2", out)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'): break
                    if key == ord('d'): self.show_debug = not self.show_debug
                    if key == ord('m'): self._toggle_system()
                    if key == ord('v'): self.voice.listen_once()
                    if key == ord('c'): self._start_calibration()
                    
        finally:
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    app = GestureControlApp()
    app.run()

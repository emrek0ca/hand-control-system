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
        
        # State
        self.system_active = True
        self.running = True
        self.show_debug = True
        self.current_hand = None
        
        # UI
        self.dashboard = DashboardBuilder(self.width, self.height)
        self._setup_ui()
        
        # Voice Commands Registry
        self.commands = self._setup_commands()
        
        # Performance
        self.fps = 0
        self.frame_count = 0

    def _setup_ui(self):
        """Build the interactive HUD overlay."""
        self.dashboard.add_button(10, 10, 140, 45, "DEBUG [D]", lambda: setattr(self, 'show_debug', not self.show_debug))
        self.dashboard.add_button(160, 10, 140, 45, "CONTROL [M]", self._toggle_system)
        self.dashboard.add_button(310, 10, 140, 45, "VOICE [V]", self.voice.listen_once)

    def _setup_commands(self):
        """Define multimodal voice commands."""
        return [
            self.voice.create_command(["ekran", "görüntüsü"], self._action_screenshot, "Ekran görüntüsü al"),
            self.voice.create_command(["sistemi", "kapat"], self._toggle_system, "Sistem kontrolünü durdur"),
            self.voice.create_command(["sistemi", "aç"], self._toggle_system, "Sistem kontrolünü başlat"),
            self.voice.create_command(["tıkla"], lambda: self.controller.click('left'), "Sol tık yap"),
            self.voice.create_command(["sağ", "tık"], lambda: self.controller.click('right'), "Sağ tık yap"),
            self.voice.create_command(["bunu", "sil"], self._multimodal_delete, "Tutulan nesneyi sil"),
        ]

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
            
        # 2. Logic Implementation
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
                
            # Voice Mode Trigger (Special pose)
            if h.gesture == GestureType.VOICE_MODE:
                self.voice.listen_once()

        # 3. UI Rendering
        if not self.headless:
            frame = self.dashboard.get_manager().draw_objects(frame)
            self._draw_hud(frame)
            
        return frame

    def _draw_hud(self, frame):
        """Modern AI HUD Overlay."""
        # Status Bar
        status_color = (0, 255, 0) if self.system_active else (0, 0, 255)
        status_text = "SYSTEM ONLINE" if self.system_active else "SYSTEM OFFLINE"
        cv2.rectangle(frame, (0, self.height-40), (self.width, self.height), (20, 20, 20), -1)
        cv2.putText(frame, status_text, (20, self.height-12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Voice Status
        v_state = self.voice.state.name
        cv2.putText(frame, f"VOICE ENGINE: {v_state}", (self.width-250, self.height-12), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
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
            f"VELOCITY: {self.current_hand.velocity:.4f}" if self.current_hand else "VELOCITY: 0"
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
                    
        finally:
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    app = GestureControlApp()
    app.run()

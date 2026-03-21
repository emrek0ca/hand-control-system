"""
Hand Gesture Control System - PRO Version
Application: AI-Driven Multimodal Interaction Agent (Liquid Glass UX)
"""

import cv2
import numpy as np
from hand_tracker import HandTracker, GestureType, GestureState
from interaction_system import DashboardBuilder, GlassRenderer, Point
from voice_system import VoiceCommandEngine, VoiceState
from system_control import SystemController
from advanced_features import AdvancedGestureRecognizer, GestureSequence
from llm_system import LLMAgent
import sys
import time


class GestureControlApp:
    """Main AI Agent Application with Liquid Glass UI and Automation."""
    
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
        self.llm = LLMAgent()
        
        # State
        self.system_active = True
        self.running = True
        self.show_debug = True
        self.current_hand = None
        self.last_swipe = None
        self.swipe_time = 0
        self.aura_intensity = 0.0
        
        # Calibration State
        self.is_calibrating = False
        self.calib_step = 0
        self.calib_samples = []
        self.calib_results = {"pinch": 0, "size": 0}
        
        # UI (Liquid Glass Dashboard)
        self.dashboard = DashboardBuilder(self.width, self.height)
        self._setup_ui()
        
        # Voice Commands Registry
        self.commands = self._setup_commands()
        
        # Performance & Automation
        self.fps = 0
        self.frame_count = 0
        self.last_context_update = 0
        self._load_calibration()

    def _setup_ui(self):
        """Build the fütüristic Liquid Glass HUD overlay."""
        # Main Control Group
        self.dashboard.add_button(10, 10, 140, 45, "DEBUG", lambda: setattr(self, 'show_debug', not self.show_debug), color=(40, 40, 80))
        self.dashboard.add_button(160, 10, 140, 45, "CONTROL", self._toggle_system, color=(40, 80, 40))
        self.dashboard.add_button(310, 10, 140, 45, "VOICE", self.voice.listen_once, color=(80, 40, 40))
        self.dashboard.add_button(460, 10, 140, 45, "CALIBRATE", self._start_calibration, color=(80, 80, 40))
        # Smart Context Button (Will be updated by LLM)
        self.smart_btn = self.dashboard.add_button(610, 10, 160, 45, "AI AGENT", self._llm_describe_screen, color=(100, 40, 100))

    def _setup_commands(self):
        """Define multimodal voice commands (No Emojis)."""
        return [
            self.voice.create_command(["ekran", "görüntüsü"], self._action_screenshot, "Capture Screenshot"),
            self.voice.create_command(["sistemi", "kapat"], self._toggle_system, "Disable System Control"),
            self.voice.create_command(["sistemi", "aç"], self._toggle_system, "Enable System Control"),
            self.voice.create_command(["tıkla"], lambda: self.controller.click('left'), "Left Click"),
            self.voice.create_command(["sağ", "tık"], lambda: self.controller.click('right'), "Right Click"),
            self.voice.create_command(["bunu", "sil"], self._multimodal_delete, "Delete Active Target"),
            self.voice.create_command(["kalibrasyon", "başlat"], self._start_calibration, "Start Calibration"),
            self.voice.create_command(["ekranı", "anlat"], self._llm_describe_screen, "Analyze Screen"),
        ]

    def _update_contextual_ui(self):
        """Periodically update UI based on LLM's understanding of the context."""
        if not self.llm.active or time.time() - self.last_context_update < 10.0:
            return
        
        # Quick check of what's happening
        desc = self.llm.analyze_frame(self.last_frame)
        self.last_context_update = time.time()
        
        # Simple Logic: If browser or meeting is detected, change smart_btn label
        if "tarayıcı" in desc.lower() or "google" in desc.lower():
            self.smart_btn.label = "REFRESH TAB"
            self.smart_btn.on_click = lambda: self.controller.press_key('f5')
        elif "zoom" in desc.lower() or "toplantı" in desc.lower():
            self.smart_btn.label = "MUTE MIC"
            self.smart_btn.on_click = lambda: self.controller.press_key('m')
        else:
            self.smart_btn.label = "ANALYZE SCREEN"
            self.smart_btn.on_click = self._llm_describe_screen

    def _dodge_panels(self, pointer_px):
        """Move UI panels away if the hand is covering them (Automation)."""
        px, py = pointer_px
        for obj in self.dashboard.get_manager().objects:
            # If pointer is near the object, set a dodging target_position
            dist = np.sqrt((obj.position.x + obj.size[0]/2 - px)**2 + (obj.position.y + obj.size[1]/2 - py)**2)
            if dist < 100:
                # Smoothly lower opacity instead of moving for better UX
                obj.opacity = max(0.1, obj.opacity - 0.05)
            else:
                obj.opacity = min(0.4, obj.opacity + 0.02)

    def _start_calibration(self):
        self.is_calibrating = True
        self.calib_step = 0
        self.calib_samples = []
        self.voice.speak("Kalibrasyon başladı. Lütfen elinizi açık şekilde kameraya tutun.")

    def _process_calibration(self, hand):
        wrist = hand.smoothed_landmarks[0]
        mcp = hand.smoothed_landmarks[9]
        hand_size = np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2)
        
        if self.calib_step == 0:
            self.calib_samples.append(hand_size)
            if len(self.calib_samples) >= 30:
                self.calib_results["size"] = np.mean(self.calib_samples)
                self.calib_samples = []
                self.calib_step = 1
                self.voice.speak("Lütfen tık hareketi yapın.")
                
        elif self.calib_step == 1:
            thumb = hand.smoothed_landmarks[4]
            index = hand.smoothed_landmarks[8]
            pinch_dist = np.sqrt((thumb.x - index.x)**2 + (thumb.y - index.y)**2)
            self.calib_samples.append(pinch_dist / hand_size)
            
            if len(self.calib_samples) >= 30:
                self.calib_results["pinch"] = np.mean(self.calib_samples)
                self.tracker.apply_calibration(self.calib_results["pinch"] * 1.2, self.calib_results["pinch"] * 1.8, self.calib_results["size"])
                self.is_calibrating = False
                self.voice.speak("Kalibrasyon tamamlandı.")
                self._save_calibration()

    def _save_calibration(self):
        import json
        data = {"pinch": self.tracker.PINCH_THRESH, "release": self.tracker.RELEASE_THRESH, "size": self.tracker.neutral_hand_size}
        with open("calibration.json", "w") as f: json.dump(data, f)

    def _load_calibration(self):
        import json, os
        if os.path.exists("calibration.json"):
            try:
                with open("calibration.json", "r") as f:
                    data = json.load(f)
                self.tracker.apply_calibration(data["pinch"], data["release"], data["size"])
            except: pass

    def _toggle_system(self):
        self.system_active = not self.system_active
        self.voice.speak(f"Sistem kontrolü {'aktif' if self.system_active else 'pasif'}")

    def _action_screenshot(self):
        cv2.imwrite(f"cap_{int(time.time())}.png", self.last_frame)
        self.voice.speak("Görüntü kaydedildi.")

    def _multimodal_delete(self):
        if self.current_hand and self.current_hand.state == GestureState.GRABBING:
             self.controller.press_key('delete')
             self.voice.speak("Silindi.")
        else: self.voice.speak("Hedef yok.")

    def _llm_describe_screen(self):
        if not self.llm.active: return
        self.voice.speak("Analiz ediliyor...")
        description = self.llm.analyze_frame(self.last_frame)
        self.voice.speak(description)

    def _on_voice_command(self, text: str):
        cmd = self.voice.match_command(text, self.commands)
        if cmd: cmd['action']()
        elif self.llm.active:
            self.voice.speak(self.llm.reason_command(text))

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self.last_frame = frame.copy()
        hands = self.tracker.process_frame(frame)
        self.current_hand = hands[0] if hands else None
        
        # 1. UI Interaction & Automation
        pointer = self.current_hand.center if self.current_hand else (0, 0)
        pointer_px = (int(pointer[0] * self.width), int(pointer[1] * self.height))
        clicked = (self.current_hand.state == GestureState.CLICKED) if self.current_hand else False
        
        # Calculate velocity in pixels for particle effects
        v_px = (0, 0)
        if self.current_hand:
            v_px = (self.tracker.velocity[0] * self.width, self.tracker.velocity[1] * self.height)
        
        self.dashboard.get_manager().check_interactions(pointer_px, clicked, velocity=v_px)
        self._dodge_panels(pointer_px)
        self._update_contextual_ui()
        
        # 2. Logic Implementation
        if self.current_hand and self.system_active and not self.is_calibrating:
            h = self.current_hand
            nx, ny = h.center[0], h.center[1]
            
            if h.state in [GestureState.IDLE, GestureState.MOVING, GestureState.CLICKED, GestureState.RIGHT_CLICK]:
                self.controller.move_mouse(nx, ny)
            if h.state == GestureState.CLICKED: self.controller.click('left')
            if h.state == GestureState.RIGHT_CLICK: self.controller.click('right')
            if h.state == GestureState.GRABBING: self.controller.drag_mouse(nx, ny)
            if h.state == GestureState.SCROLLING: self.controller.scroll_adaptive(h.scroll_y)
            else: self.controller.reset_scroll()
                
            if h.gesture == GestureType.PEACE: self.controller.zoom_adaptive(h.z_depth)
            else: self.controller.reset_zoom()
            if h.gesture == GestureType.VOICE_MODE: self.voice.listen_once()
                
            swipe = self.tracker.detect_swipe()
            if swipe:
                self.last_swipe, self.swipe_time = swipe, time.time()
                import pyautogui
                if swipe == "RIGHT": pyautogui.hotkey('ctrl', 'tab')
                elif swipe == "LEFT": pyautogui.hotkey('ctrl', 'shift', 'tab')

        # 3. Calibration
        if self.is_calibrating and self.current_hand:
            self._process_calibration(self.current_hand)

        # 4. Professional Rendering
        if not self.headless:
            # Aura logic
            if self.current_hand:
                self.aura_intensity = min(1.0, self.aura_intensity + 0.1)
            else:
                self.aura_intensity = max(0.0, self.aura_intensity - 0.05)
            
            # Draw UI
            frame = self.dashboard.get_manager().draw(frame)
            if self.is_calibrating: self._draw_calibration_hud(frame)
            else: self._draw_hud(frame)
            
            # Draw Hand Visuals
            if self.current_hand:
                frame = self.tracker.draw_hand_skeleton(frame, hands)
                # Draw Aura
                radius = int(40 + self.current_hand.z_depth * 100)
                GlassRenderer.draw_aura(frame, pointer_px, radius, (0, 255, 255), self.aura_intensity)
            
        return frame

    def _draw_calibration_hud(self, frame):
        progress = len(self.calib_samples) / 30.0
        txt = "STEP 1: OPEN HAND" if self.calib_step == 0 else "STEP 2: PINCH"
        GlassRenderer.draw_glass_rect(frame, self.width//2 - 200, self.height//2 - 50, 400, 100, (40, 40, 40), 0.7, label=txt)
        cv2.rectangle(frame, (self.width//2 - 180, self.height//2 + 10), (self.width//2 - 180 + int(360 * progress), self.height//2 + 30), (0, 255, 0), -1)

    def _draw_hud(self, frame):
        # Bottom Status Bar (Liquid Glass)
        status_color = (100, 255, 100) if self.system_active else (100, 100, 255)
        status_text = f"SYSTEM ACTIVE | CALIBRATED: {self.tracker.is_calibrated}"
        GlassRenderer.draw_glass_rect(frame, 0, self.height-50, self.width, 50, (20, 20, 20), 0.6)
        cv2.putText(frame, status_text, (20, self.height-18), cv2.FONT_HERSHEY_DUPLEX, 0.6, status_color, 1, cv2.LINE_AA)
        
        # AI Status
        brain_text = "AI BRAIN: ONLINE" if self.llm.active else "AI BRAIN: OFFLINE"
        cv2.putText(frame, brain_text, (self.width-250, self.height-18), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        if self.last_swipe and time.time() - self.swipe_time < 1.0:
            GlassRenderer.draw_glass_rect(frame, self.width//2 - 100, 100, 200, 60, (150, 0, 150), 0.5, label=f"SWIPE {self.last_swipe}")
        
        if self.show_debug: self._draw_debug(frame)

    def _draw_debug(self, frame):
        GlassRenderer.draw_glass_rect(frame, 10, 70, 260, 140, (0, 0, 0), 0.4)
        y = 95
        debug_info = [
            f"FPS: {self.fps}",
            f"STATE: {self.current_hand.state.name if self.current_hand else 'NONE'}",
            f"Z-DEPTH: {self.current_hand.z_depth:.4f}" if self.current_hand else "Z: 0"
        ]
        for line in debug_info:
            cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            y += 25

    def run(self):
        last_time = time.time()
        f_count = 0
        while self.running:
            ret, frame = self.cap.read()
            if not ret: break
            out = self.process_frame(frame)
            f_count += 1
            if time.time() - last_time >= 1.0:
                self.fps, f_count, last_time = f_count, 0, time.time()
            if not self.headless:
                cv2.imshow("HAND CONTROL AI - LIQUID GLASS", out)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'): break
                if key == ord('d'): self.show_debug = not self.show_debug
                if key == ord('c'): self._start_calibration()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = GestureControlApp()
    app.run()

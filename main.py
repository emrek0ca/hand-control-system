"""
Hand Gesture Control System - PRO Version
Application: AI-Driven Multimodal Interaction Agent (Liquid Glass UX)
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from hand_tracker import HandTracker, GestureType, GestureState
from interaction_system import DashboardBuilder, GlassRenderer, Point
from voice_system import VoiceCommandEngine, VoiceState
from system_control import SystemController
from advanced_features import AdvancedGestureRecognizer, GestureSequence, MultiHandAnalyzer
from llm_system import LLMAgent
from app_logging import setup_logging
from runtime_paths import ensure_runtime_dirs, get_calibration_path, get_screenshots_dir, get_settings_path
from settings_manager import CONTINUOUS_ACTIONS, SettingsManager, normalize_handedness
from version import __version__


class GestureControlApp:
    """Main AI Agent Application with Liquid Glass UI and Automation."""
    
    def __init__(self, camera_id: Optional[int] = None, headless: bool = False):
        self.headless = headless
        self.logger = setup_logging()
        ensure_runtime_dirs()

        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.current
        camera_settings = self.settings.get("camera", {})
        if camera_id is None:
            camera_id = camera_settings.get("camera_id", 0)
        self.camera_id = int(camera_id)

        self._settings_mtime = self._read_settings_mtime()
        self._settings_poll_interval = 0.75
        self._last_settings_poll = 0.0
        self.settings_process = None
        self._frame_action_tokens = set()

        # Camera Setup
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("Camera not accessible.")

        self.camera_width = int(camera_settings.get("width", 1280))
        self.camera_height = int(camera_settings.get("height", 720))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Modules
        gesture_settings = self.settings.get("gestures", {})
        self.tracker = HandTracker(
            confidence_threshold=float(camera_settings.get("confidence_threshold", 0.7)),
            max_num_hands=int(camera_settings.get("max_hands", 2)),
            buffer_size=int(gesture_settings.get("buffer_size", 4)),
            filter_alpha=float(gesture_settings.get("filter_alpha", 0.6)),
            pinch_threshold=float(gesture_settings.get("pinch_threshold", 0.12)),
            release_threshold=float(gesture_settings.get("release_threshold", 0.18)),
            velocity_lock=float(gesture_settings.get("velocity_lock", 0.10)),
        )
        self.controller = SystemController()
        self.voice = VoiceCommandEngine(on_result=self._on_voice_command)
        self.voice_engine = self.voice
        self.recognizer = AdvancedGestureRecognizer()
        self.multi_analyzer = MultiHandAnalyzer()
        self.llm = LLMAgent(
            model_name=self.settings.get("ai", {}).get("model", "gemini-2.0-flash"),
            enabled=bool(self.settings.get("ai", {}).get("enabled", False)),
        )
        self.voice_input_available = getattr(self.voice, "input_available", False)
        self.llm_available = self.llm.active
        self.logger.info(
            "app_init",
            extra={
                "event": "app_init",
                "version": __version__,
                "headless": self.headless,
                "voice_input": self.voice_input_available,
                "llm": self.llm_available,
                "camera_id": self.camera_id,
            },
        )
        
        # State
        self.system_active = True
        self.running = True
        self.show_debug = False
        self.debug_override = os.getenv("HAND_CONTROL_DEBUG", "0") == "1"
        self.show_hud = True
        self.zen_mode = False
        self.primary_hand = "auto"
        self.current_hand = None
        self.prev_hand_data = None
        self.prev_hand_state = GestureState.IDLE
        self.prev_gesture_type = GestureType.NONE
        self.prev_hand_state_by_side = {
            "Left": GestureState.IDLE,
            "Right": GestureState.IDLE,
        }
        self.prev_gesture_type_by_side = {
            "Left": GestureType.NONE,
            "Right": GestureType.NONE,
        }
        self.hands = []
        self.last_swipe = None
        self.swipe_time = 0
        self.aura_intensity = 0.0
        self.last_frame = None
        self.stats = {"voice_commands_executed": 0, "settings_reload_count": 0}
        self.frame_skip = 0
        self.fps_limit = 30
        self.adaptive_quality = True
        
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
        self.apply_settings(force=True)

    def _setup_ui(self):
        """Build the fütüristic Liquid Glass HUD overlay."""
        # Main Control Group
        debug_label = "DEBUG ON" if self.show_debug else "DEBUG"
        control_label = "CONTROL ON" if self.system_active else "CONTROL OFF"
        self.debug_btn = self.dashboard.add_button(10, 10, 140, 45, debug_label, self._toggle_debug, color=(40, 40, 80))
        self.control_btn = self.dashboard.add_button(160, 10, 140, 45, control_label, self._toggle_system, color=(40, 80, 40))
        voice_label = "VOICE" if self.voice_input_available else "VOICE OFF"
        self.voice_btn = self.dashboard.add_button(
            310,
            10,
            140,
            45,
            voice_label,
            self.voice.listen_once if self.voice_input_available else self._voice_unavailable,
            color=(80, 40, 40),
        )
        self.calibrate_btn = self.dashboard.add_button(460, 10, 140, 45, "CALIBRATE", self._start_calibration, color=(80, 80, 40))
        self.settings_btn = self.dashboard.add_button(610, 10, 140, 45, "SETTINGS", self.open_settings_panel, color=(40, 70, 90))
        # Smart Context Button (Will be updated by LLM)
        ai_label = "AI AGENT" if self.llm_available else "AI OFF"
        self.smart_btn = self.dashboard.add_button(
            760,
            10,
            160,
            45,
            ai_label,
            self._llm_describe_screen if self.llm_available else self._llm_unavailable,
            color=(100, 40, 100),
        )

    def _setup_commands(self):
        """Define multimodal voice commands (No Emojis)."""
        return [
            self.voice.create_command(["ekran", "görüntüsü"], self._action_screenshot, "Capture Screenshot"),
            self.voice.create_command(["sistemi", "kapat"], self._toggle_system, "Disable System Control"),
            self.voice.create_command(["sistemi", "aç"], self._toggle_system, "Enable System Control"),
            self.voice.create_command(["tıkla"], lambda: self.controller.click('left'), "Left Click"),
            self.voice.create_command(["sağ", "tık"], lambda: self.controller.click('right'), "Right Click"),
            self.voice.create_command(["ayarlar"], self.open_settings_panel, "Open Settings"),
            self.voice.create_command(["ayarları", "aç"], self.open_settings_panel, "Open Settings"),
            self.voice.create_command(["bunu", "sil"], self._multimodal_delete, "Delete Active Target"),
            self.voice.create_command(["kalibrasyon", "başlat"], self._start_calibration, "Start Calibration"),
            self.voice.create_command(["ekranı", "anlat"], self._llm_describe_screen, "Analyze Screen"),
        ]

    def _update_contextual_ui(self):
        """Periodically update UI based on LLM's understanding of the context."""
        if not self.llm.active or self.last_frame is None or time.time() - self.last_context_update < 10.0:
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

    def _voice_unavailable(self):
        self.voice.speak("Mikrofon hazır değil.")

    def _llm_unavailable(self):
        self.voice.speak("Zeka motoru devre dışı.")

    def _process_calibration(self, hand):
        wrist = hand.smoothed_landmarks[0]
        mcp = hand.smoothed_landmarks[9]
        hand_size = max(0.01, np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2))
        
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
        data = {
            "pinch": self.tracker.PINCH_THRESH,
            "release": self.tracker.RELEASE_THRESH,
            "size": self.tracker.neutral_hand_size,
        }
        with open(get_calibration_path(), "w") as f:
            json.dump(data, f)
        self.settings_manager.set_value("gestures", "pinch_threshold", self.tracker.PINCH_THRESH)
        self.settings_manager.set_value("gestures", "release_threshold", self.tracker.RELEASE_THRESH)
        self.settings_manager.set_value("gestures", "neutral_hand_size", self.tracker.neutral_hand_size)
        self.settings_manager.save()
        self._settings_mtime = self._read_settings_mtime()

    def _load_calibration(self):
        import json, os
        calibration_path = get_calibration_path()
        if os.path.exists(calibration_path):
            try:
                with open(calibration_path, "r") as f:
                    data = json.load(f)
                self.tracker.apply_calibration(data["pinch"], data["release"], data["size"])
                self.settings_manager.set_value("gestures", "pinch_threshold", data["pinch"])
                self.settings_manager.set_value("gestures", "release_threshold", data["release"])
                self.settings_manager.set_value("gestures", "neutral_hand_size", data["size"])
                self.settings_manager.save()
                self._settings_mtime = self._read_settings_mtime()
            except Exception:
                pass

    def _read_settings_mtime(self) -> float:
        path = get_settings_path()
        if path.exists():
            return path.stat().st_mtime
        return 0.0

    def _refresh_settings_if_needed(self):
        now = time.time()
        if now - self._last_settings_poll < self._settings_poll_interval:
            return
        self._last_settings_poll = now
        current_mtime = self._read_settings_mtime()
        if current_mtime <= self._settings_mtime:
            return
        self.settings_manager = SettingsManager()
        self._settings_mtime = current_mtime
        self.stats["settings_reload_count"] += 1
        self.apply_settings()

    def _reopen_camera(self, camera_id: int, width: int, height: int) -> bool:
        try:
            if hasattr(self, "cap") and self.cap:
                self.cap.release()
        except Exception:
            pass

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            self.logger.warning("camera_reopen_failed", extra={"event": "camera_reopen_failed", "camera_id": camera_id})
            return False

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap = cap
        self.camera_id = camera_id
        self.camera_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.camera_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = self.camera_width
        self.height = self.camera_height
        self.dashboard = DashboardBuilder(self.width, self.height)
        self._setup_ui()
        return True

    def _build_settings_command(self):
        if getattr(sys, "frozen", False):
            return [sys.executable, "--settings-panel"], None
        launcher_path = Path(__file__).resolve().with_name("launcher.py")
        return [sys.executable, str(launcher_path), "--settings-panel"], str(launcher_path.parent)

    def _launch_settings_panel(self):
        if self.settings_process and self.settings_process.poll() is None:
            return
        cmd, cwd = self._build_settings_command()
        try:
            self.settings_process = subprocess.Popen(cmd, cwd=cwd)
            self.voice.speak("Ayarlar paneli açıldı.")
        except Exception as exc:
            self.logger.exception(
                "settings_panel_launch_failed",
                extra={"event": "settings_panel_launch_failed", "error": str(exc)},
            )
            if self.voice.enabled:
                self.voice.speak("Ayarlar paneli açılamadı.")

    def open_settings_panel(self):
        self._launch_settings_panel()

    def _toggle_debug(self):
        self.show_debug = not self.show_debug
        self.settings_manager.set_value("general", "show_debug", self.show_debug)
        self.settings_manager.set_value("ui", "show_debug_overlay", self.show_debug)
        self.settings_manager.save()
        self._settings_mtime = self._read_settings_mtime()
        if hasattr(self, "debug_btn"):
            self.debug_btn.label = "DEBUG ON" if self.show_debug else "DEBUG"

    def _toggle_zen(self):
        self.zen_mode = not self.zen_mode
        self.settings_manager.set_value("general", "zen_mode", self.zen_mode)
        self.settings_manager.save()
        self._settings_mtime = self._read_settings_mtime()
        if self.voice.enabled:
            self.voice.speak(f"Zen Mode {'Aktif' if self.zen_mode else 'Pasif'}")

    def _toggle_system(self):
        self.system_active = not self.system_active
        self.settings_manager.set_value("general", "system_active", self.system_active)
        self.settings_manager.save()
        self._settings_mtime = self._read_settings_mtime()
        if hasattr(self, "control_btn"):
            self.control_btn.label = "CONTROL ON" if self.system_active else "CONTROL OFF"
        if self.voice.enabled:
            self.voice.speak(f"Sistem kontrolü {'aktif' if self.system_active else 'pasif'}")

    def _apply_camera_settings(self, camera_settings):
        camera_id = int(camera_settings.get("camera_id", self.camera_id))
        width = int(camera_settings.get("width", self.camera_width))
        height = int(camera_settings.get("height", self.camera_height))

        if (
            camera_id != self.camera_id
            or width != self.camera_width
            or height != self.camera_height
            or self.cap is None
            or not self.cap.isOpened()
        ):
            if not self._reopen_camera(camera_id, width, height):
                return
        else:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.camera_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.width = self.camera_width
            self.height = self.camera_height

    def _update_ui_labels(self):
        if hasattr(self, "voice_btn"):
            self.voice_btn.label = "VOICE" if self.voice_input_available else "VOICE OFF"
            self.voice_btn.on_click = self.voice.listen_once if self.voice_input_available else self._voice_unavailable
        if hasattr(self, "smart_btn"):
            self.smart_btn.label = "AI AGENT" if self.llm_available else "AI OFF"
            self.smart_btn.on_click = self._llm_describe_screen if self.llm_available else self._llm_unavailable

    def apply_settings(self, force: bool = False):
        settings = self.settings_manager.current
        self.settings = settings
        general = settings.get("general", {})
        camera = settings.get("camera", {})
        mouse = settings.get("mouse", {})
        gestures = settings.get("gestures", {})
        voice = settings.get("voice", {})
        ai = settings.get("ai", {})
        ui = settings.get("ui", {})

        camera_sig = (
            int(camera.get("camera_id", self.camera_id)),
            int(camera.get("width", self.camera_width)),
            int(camera.get("height", self.camera_height)),
        )
        gesture_sig = (
            float(camera.get("confidence_threshold", 0.7)),
            int(camera.get("max_hands", 2)),
            int(gestures.get("buffer_size", 4)),
            float(gestures.get("filter_alpha", 0.6)),
            float(gestures.get("pinch_threshold", 0.12)),
            float(gestures.get("release_threshold", 0.18)),
            float(gestures.get("velocity_lock", 0.10)),
            float(gestures.get("neutral_hand_size", 1.0)),
        )
        mouse_sig = (
            float(mouse.get("roi_margin", 0.12)),
            bool(mouse.get("invert_x", False)),
            bool(mouse.get("invert_y", False)),
            float(mouse.get("pointer_gain", 1.0)),
            float(mouse.get("alpha_min", 0.05)),
            float(mouse.get("alpha_max", 0.90)),
            float(mouse.get("click_cooldown", 0.4)),
            float(mouse.get("freeze_duration", 0.25)),
            float(mouse.get("scroll_threshold", 0.01)),
            float(mouse.get("scroll_multiplier", 1500)),
            float(mouse.get("zoom_threshold", 0.02)),
            float(mouse.get("zoom_cooldown", 0.30)),
        )
        voice_sig = (
            bool(voice.get("enabled", True)),
            voice.get("language", "tr-TR"),
            int(voice.get("tts_rate", 160)),
            float(voice.get("tts_volume", 0.8)),
            float(voice.get("listen_timeout", 3)),
            float(voice.get("phrase_time_limit", 4)),
        )
        ai_sig = (
            bool(ai.get("enabled", False)),
            ai.get("model", "gemini-2.0-flash"),
        )
        ui_sig = (
            bool(general.get("show_debug", False)),
            bool(general.get("show_hud", True)),
            bool(general.get("system_active", True)),
            bool(general.get("zen_mode", False)),
            bool(ui.get("show_debug_overlay", False)),
            float(ui.get("hud_opacity", 0.6)),
            int(ui.get("trail_max_len", 15)),
            int(ui.get("particle_limit", 150)),
            ui.get("theme", "midnight"),
        )

        if force or camera_sig != getattr(self, "_camera_sig", None):
            self._apply_camera_settings(camera)
            self._camera_sig = camera_sig

        if force or gesture_sig != getattr(self, "_gesture_sig", None):
            self.tracker.reconfigure(
                confidence_threshold=float(camera.get("confidence_threshold", 0.7)),
                max_num_hands=int(camera.get("max_hands", 2)),
                buffer_size=int(gestures.get("buffer_size", 4)),
                filter_alpha=float(gestures.get("filter_alpha", 0.6)),
                pinch_threshold=float(gestures.get("pinch_threshold", 0.12)),
                release_threshold=float(gestures.get("release_threshold", 0.18)),
                velocity_lock=float(gestures.get("velocity_lock", 0.10)),
                neutral_hand_size=float(gestures.get("neutral_hand_size", 1.0)),
            )
            self._gesture_sig = gesture_sig

        if force or mouse_sig != getattr(self, "_mouse_sig", None):
            self.controller.configure(
                roi_margin=float(mouse.get("roi_margin", 0.12)),
                invert_x=bool(mouse.get("invert_x", False)),
                invert_y=bool(mouse.get("invert_y", False)),
                pointer_gain=float(mouse.get("pointer_gain", 1.0)),
                base_alpha_min=float(mouse.get("alpha_min", 0.05)),
                base_alpha_max=float(mouse.get("alpha_max", 0.90)),
                click_cooldown=float(mouse.get("click_cooldown", 0.4)),
                freeze_duration=float(mouse.get("freeze_duration", 0.25)),
                scroll_threshold=float(mouse.get("scroll_threshold", 0.01)),
                scroll_multiplier=float(mouse.get("scroll_multiplier", 1500)),
                zoom_threshold=float(mouse.get("zoom_threshold", 0.02)),
                zoom_cooldown=float(mouse.get("zoom_cooldown", 0.30)),
            )
            self.controller.prev_x = None
            self.controller.prev_y = None
            self.controller.reset_scroll()
            self.controller.reset_zoom()
            self._mouse_sig = mouse_sig

        if force or voice_sig != getattr(self, "_voice_sig", None):
            self.voice.configure(
                enabled=bool(voice.get("enabled", True)),
                rate=int(voice.get("tts_rate", 160)),
                volume=float(voice.get("tts_volume", 0.8)),
                language=voice.get("language", "tr-TR"),
                listen_timeout=float(voice.get("listen_timeout", 3)),
                phrase_time_limit=float(voice.get("phrase_time_limit", 4)),
            )
            self.voice_input_available = bool(self.voice.enabled and getattr(self.voice, "input_available", False))
            self._voice_sig = voice_sig

        if force or ai_sig != getattr(self, "_ai_sig", None):
            self.llm.configure(
                enabled=bool(ai.get("enabled", False)),
                model_name=ai.get("model", "gemini-2.0-flash"),
            )
            self.llm_available = bool(self.llm.active)
            self._ai_sig = ai_sig

        self.system_active = bool(general.get("system_active", True))
        self.zen_mode = bool(general.get("zen_mode", False))
        self.primary_hand = str(general.get("primary_hand", "auto")).strip().lower() or "auto"
        self.show_hud = bool(general.get("show_hud", True))
        self.show_debug = bool(general.get("show_debug", False) or ui.get("show_debug_overlay", False))
        if self.debug_override:
            self.show_debug = True
        performance = settings.get("performance", {})
        self.frame_skip = max(0, int(performance.get("frame_skip", 0)))
        self.fps_limit = max(1, int(performance.get("fps_limit", 30)))
        self.adaptive_quality = bool(performance.get("adaptive_quality", True))

        if force or ui_sig != getattr(self, "_ui_sig", None):
            if hasattr(self, "dashboard"):
                self.dashboard = DashboardBuilder(self.width, self.height)
                self._setup_ui()
            self._ui_sig = ui_sig

        self._update_ui_labels()

    def _select_primary_hand(self):
        if not self.hands:
            return None

        preference = (self.primary_hand or "auto").lower()
        if preference in {"left", "right"}:
            for hand in self.hands:
                if normalize_handedness(hand.handedness).lower() == preference:
                    return hand

        if preference == "auto":
            return max(
                self.hands,
                key=lambda hand: (
                    float(getattr(hand, "confidence", 0.0)),
                    1 if normalize_handedness(hand.handedness) == "Right" else 0,
                ),
            )

        return self.hands[0]

    def _read_bindings(self, group: str, mapping: str, key: str, handedness: Optional[str] = None):
        return self.settings_manager.get_binding(group, mapping, key, handedness=handedness)

    def _execute_hotkey(self, payload: str):
        if not payload:
            return
        parts = [part.strip() for part in payload.replace(",", "+").split("+") if part.strip()]
        if not parts:
            return
        self.controller.hotkey(*parts)

    def _dispatch_binding(self, group: str, mapping: str, key: str, hand, changed: bool, handedness: Optional[str] = None, is_primary: bool = False):
        binding = self._read_bindings(group, mapping, key, handedness=handedness)
        action = binding.get("action", "none")
        payload = binding.get("payload", "")
        if not action or action == "none":
            return
        if action in CONTINUOUS_ACTIONS:
            if action in {"move_mouse", "drag_mouse"}:
                if hand is not None and is_primary:
                    self.perform_action(action, hand=hand, payload=payload, handedness=handedness)
            elif hand is not None:
                self.perform_action(action, hand=hand, payload=payload, handedness=handedness)
        elif changed:
            self.perform_action(action, hand=hand, payload=payload, handedness=handedness)

    def perform_action(self, action: str, hand=None, payload: str = "", handedness: Optional[str] = None):
        if not action or action == "none":
            return

        hand_token = handedness or normalize_handedness(getattr(hand, "handedness", None)) or "global"
        token = f"{hand_token}:{action}:{payload}"
        if token in self._frame_action_tokens:
            return
        self._frame_action_tokens.add(token)

        action = action.lower()
        if action == "move_mouse" and hand is not None:
            self.controller.move_mouse(hand.center[0], hand.center[1])
        elif action == "drag_mouse" and hand is not None:
            self.controller.drag_mouse(hand.center[0], hand.center[1])
        elif action == "left_click":
            self.controller.click("left")
        elif action == "right_click":
            self.controller.click("right")
        elif action == "scroll" and hand is not None:
            self.controller.scroll_adaptive(hand.scroll_y)
        elif action == "scroll_up":
            try:
                amount = int(float(payload)) if payload else 500
            except Exception:
                amount = 500
            self.controller.scroll(amount)
        elif action == "scroll_down":
            try:
                amount = int(float(payload)) if payload else 500
            except Exception:
                amount = 500
            self.controller.scroll(-abs(amount))
        elif action == "zoom_in":
            if hand is not None:
                self.controller.prev_z_depth = hand.z_depth - (self.controller.zoom_threshold + 0.01)
                self.controller.zoom_adaptive(hand.z_depth)
        elif action == "zoom_out":
            if hand is not None:
                self.controller.prev_z_depth = hand.z_depth + (self.controller.zoom_threshold + 0.01)
                self.controller.zoom_adaptive(hand.z_depth)
        elif action == "screenshot":
            self._action_screenshot()
        elif action == "toggle_system":
            self._toggle_system()
        elif action == "toggle_debug":
            self._toggle_debug()
        elif action == "toggle_zen":
            self._toggle_zen()
        elif action == "voice_listen":
            self.voice.listen_once()
        elif action == "llm_analyze":
            self._llm_describe_screen()
        elif action == "open_settings":
            self.open_settings_panel()
        elif action == "calibrate":
            self._start_calibration()
        elif action == "next_tab":
            modifier = "ctrl"
            self.controller.hotkey(modifier, "tab")
        elif action == "previous_tab":
            modifier = "ctrl"
            self.controller.hotkey(modifier, "shift", "tab")
        elif action == "mute_toggle":
            modifier = "command" if sys.platform == "darwin" else "ctrl"
            self.controller.hotkey(modifier, "shift", "m")
        elif action == "press_key":
            self.controller.press_key(payload)
        elif action == "hotkey":
            self._execute_hotkey(payload)
        elif action == "type_text":
            self.controller.write_text(payload)

    def _action_screenshot(self):
        if self.last_frame is None:
            if self.voice.enabled:
                self.voice.speak("Kaydedilecek görüntü yok.")
            return
        screenshot_dir = get_screenshots_dir()
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = screenshot_dir / f"cap_{int(time.time())}.png"
        cv2.imwrite(str(path), self.last_frame)
        if self.voice.enabled:
            self.voice.speak("Görüntü kaydedildi.")

    def _multimodal_delete(self):
        if self.current_hand and self.current_hand.state == GestureState.GRABBING:
             self.controller.press_key('delete')
             self.voice.speak("Silindi.")
        else: self.voice.speak("Hedef yok.")

    def _llm_describe_screen(self):
        if not self.llm.active or self.last_frame is None:
            self._llm_unavailable()
            return
        self.voice.speak("Analiz ediliyor...")
        description = self.llm.analyze_frame(self.last_frame)
        self.voice.speak(description)

    def _on_voice_command(self, text: str):
        cmd = self.voice.match_command(text, self.commands)
        if cmd:
            cmd['action']()
            self.stats["voice_commands_executed"] += 1
        elif self.llm.active:
            self.stats["voice_commands_executed"] += 1
            self.voice.speak(self.llm.reason_command(text))

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        self._refresh_settings_if_needed()
        self._frame_action_tokens = set()
        self.last_frame = frame.copy()
        self.hands = self.tracker.process_frame(frame)
        self.current_hand = self._select_primary_hand() if self.hands else None
        self.prev_hand_data = self.current_hand
        pointer_px = None
        
        # 1. UI Interaction & Automation
        if self.current_hand:
            pointer = self.current_hand.center
            pointer_px = (int(pointer[0] * self.width), int(pointer[1] * self.height))
            if self.show_hud:
                clicked = self.current_hand.state == GestureState.CLICKED and self.prev_hand_state != GestureState.CLICKED
                v = self.current_hand.velocity_vector
                v_px = (v[0] * self.width, v[1] * self.height)

                self.dashboard.get_manager().check_interactions(pointer_px, clicked, velocity=v_px)
                if self.adaptive_quality:
                    self._dodge_panels(pointer_px)
                    self._update_contextual_ui()
        else:
            self.prev_hand_state = GestureState.IDLE
            self.prev_gesture_type = GestureType.NONE
            self.controller.reset_scroll()
            self.controller.reset_zoom()
        
        # 2. Multi-Hand Automation
        if len(self.hands) >= 2:
            rel_data = self.multi_analyzer.calculate_relative_data(self.hands)
            
            # --- Clap Detection (Toggle Mute) ---
            if self.multi_analyzer.detect_clap(rel_data):
                if self.voice.enabled:
                    self.voice.speak("System Muted")
                print("[AGENT] CLAP: SYSTEM MUTE")
                # Add system mute logic if needed
                
            # --- Prayer Pose (Zen Mode) ---
            if self.multi_analyzer.detect_prayer(self.hands, rel_data):
                if not self.multi_analyzer.prayer_active:
                    self._toggle_zen()
                    self.multi_analyzer.prayer_active = True
            else:
                self.multi_analyzer.prayer_active = False

        # 3. Per-hand gesture bindings + primary-hand cursor logic
        if self.system_active and not self.is_calibrating:
            any_scroll_binding = False
            any_zoom_binding = False
            present_sides = set()
            for hand in self.hands:
                side = normalize_handedness(hand.handedness)
                if side:
                    present_sides.add(side)
                if side:
                    previous_state = self.prev_hand_state_by_side.get(side, GestureState.IDLE)
                    previous_gesture = self.prev_gesture_type_by_side.get(side, GestureType.NONE)
                else:
                    previous_state = GestureState.IDLE
                    previous_gesture = GestureType.NONE

                state_changed = hand.state != previous_state
                gesture_changed = hand.gesture != previous_gesture
                is_primary = hand is self.current_hand

                self._dispatch_binding(
                    "gestures",
                    "state_actions",
                    hand.state.name,
                    hand,
                    state_changed,
                    handedness=hand.handedness,
                    is_primary=is_primary,
                )
                self._dispatch_binding(
                    "gestures",
                    "gesture_actions",
                    hand.gesture.name,
                    hand,
                    gesture_changed,
                    handedness=hand.handedness,
                    is_primary=is_primary,
                )

                if side:
                    self.prev_hand_state_by_side[side] = hand.state
                    self.prev_gesture_type_by_side[side] = hand.gesture

                state_binding = self._read_bindings("gestures", "state_actions", hand.state.name, handedness=hand.handedness).get("action")
                gesture_binding = self._read_bindings("gestures", "gesture_actions", hand.gesture.name, handedness=hand.handedness).get("action")
                any_scroll_binding = any_scroll_binding or state_binding == "scroll" or gesture_binding == "scroll"
                any_zoom_binding = any_zoom_binding or state_binding in {"zoom_in", "zoom_out"} or gesture_binding in {"zoom_in", "zoom_out"}

            for side in ("Left", "Right"):
                if side not in present_sides:
                    self.prev_hand_state_by_side[side] = GestureState.IDLE
                    self.prev_gesture_type_by_side[side] = GestureType.NONE

            if self.current_hand:
                h = self.current_hand
                if not any_scroll_binding:
                    self.controller.reset_scroll()
                if not any_zoom_binding:
                    self.controller.reset_zoom()

                swipe = self.tracker.detect_swipe(hand_idx=self.hands.index(self.current_hand))
                if swipe:
                    self.last_swipe, self.swipe_time = swipe, time.time()
                    modifier = 'ctrl'
                    if swipe == "RIGHT":
                        self.controller.hotkey(modifier, 'tab')
                    elif swipe == "LEFT":
                        self.controller.hotkey(modifier, 'shift', 'tab')
        else:
            self.controller.reset_scroll()
            self.controller.reset_zoom()
            self.prev_hand_state_by_side["Left"] = GestureState.IDLE
            self.prev_hand_state_by_side["Right"] = GestureState.IDLE
            self.prev_gesture_type_by_side["Left"] = GestureType.NONE
            self.prev_gesture_type_by_side["Right"] = GestureType.NONE

        if self.current_hand:
            self.prev_hand_state = self.current_hand.state
            self.prev_gesture_type = self.current_hand.gesture
        else:
            self.prev_hand_state = GestureState.IDLE
            self.prev_gesture_type = GestureType.NONE

        # 4. Calibration
        if self.is_calibrating and self.current_hand:
            self._process_calibration(self.current_hand)

        # 5. Professional Rendering
        if not self.headless:
            # Aura logic
            self.aura_intensity = min(1.0, self.aura_intensity + 0.1) if self.current_hand else max(0.0, self.aura_intensity - 0.05)
            
            # Draw UI (Unless in Zen Mode)
            if self.show_hud and not self.zen_mode:
                frame = self.dashboard.get_manager().draw(frame)
                if self.is_calibrating: self._draw_calibration_hud(frame)
                else: self._draw_hud(frame)
            
            # Draw Hands & Energy Bonds
            if self.hands:
                frame = self.tracker.draw_hand_skeleton(frame, self.hands)
                
                # Energy Bond between two hands
                if len(self.hands) >= 2:
                    p1 = (int(self.hands[0].center[0] * self.width), int(self.hands[0].center[1] * self.height))
                    p2 = (int(self.hands[1].center[0] * self.width), int(self.hands[1].center[1] * self.height))
                    dist = np.linalg.norm(np.array(p1) - np.array(p2))
                    if dist < 300:
                        opacity = max(0.1, 1.0 - dist / 300.0)
                        color = (int(255 * opacity), int(255 * opacity), 255)
                        cv2.line(frame, p1, p2, color, 2, cv2.LINE_AA)
                        mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2)
                        cv2.circle(frame, mid, int(10 * opacity), color, -1, cv2.LINE_AA)

                # Draw Main Aura
                if self.current_hand and pointer_px is not None:
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
        status_text = f"SYSTEM ACTIVE | PROFILE: {self.settings_manager.active_profile} | CALIBRATED: {self.tracker.is_calibrated}"
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
            f"LIMIT: {self.fps_limit} | SKIP: {self.frame_skip}",
            f"QUALITY: {'ON' if self.adaptive_quality else 'OFF'}",
            f"STATE: {self.current_hand.state.name if self.current_hand else 'NONE'}",
            f"Z-DEPTH: {self.current_hand.z_depth:.4f}" if self.current_hand else "Z: 0"
        ]
        for line in debug_info:
            cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            y += 25

    def set_sensitivity(self, pinch_thresh: float, velocity_lock: float, smoothing_alpha: float):
        """Update tracker and physics thresholds dynamically."""
        if hasattr(self, 'tracker') and hasattr(self, 'controller'):
            self.tracker.PINCH_THRESH = pinch_thresh
            self.tracker.VELOCITY_LOCK = velocity_lock
            self.controller.base_alpha_min = max(0.01, smoothing_alpha * 0.1)
            self.controller.base_alpha_max = min(0.99, smoothing_alpha)
            self.settings_manager.set_value("gestures", "pinch_threshold", pinch_thresh)
            self.settings_manager.set_value("gestures", "velocity_lock", velocity_lock)
            self.settings_manager.set_value("mouse", "alpha_min", max(0.01, smoothing_alpha * 0.1))
            self.settings_manager.set_value("mouse", "alpha_max", min(0.99, smoothing_alpha))
            self.settings_manager.save()
            self._settings_mtime = self._read_settings_mtime()
            print(f"[AGENT] Sensitivity Updated: Pinch={pinch_thresh:.2f}, VelLock={velocity_lock:.2f}, Alpha={smoothing_alpha:.2f}")

    def run(self):
        last_time = time.time()
        f_count = 0
        processed_frames = 0
        while self.running:
            loop_start = time.time()
            ret, frame = self.cap.read()
            if not ret: break
            processed_frames += 1
            if self.frame_skip and processed_frames % (self.frame_skip + 1) != 0:
                if not self.headless:
                    cv2.waitKey(1)
                if self.fps_limit:
                    target = 1.0 / float(self.fps_limit)
                    elapsed = time.time() - loop_start
                    if elapsed < target:
                        time.sleep(target - elapsed)
                continue

            out = self.process_frame(frame)
            f_count += 1
            if time.time() - last_time >= 1.0:
                self.fps, f_count, last_time = f_count, 0, time.time()
            if not self.headless:
                cv2.imshow("HAND CONTROL AI - LIQUID GLASS", out)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'): break
                if key == ord('d'): self._toggle_debug()
                if key == ord('c'): self._start_calibration()
                if key == ord('p'): self.open_settings_panel()
            if self.fps_limit:
                target = 1.0 / float(self.fps_limit)
                elapsed = time.time() - loop_start
                if elapsed < target:
                    time.sleep(target - elapsed)
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = GestureControlApp()
    app.run()

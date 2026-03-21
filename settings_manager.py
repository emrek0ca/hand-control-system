"""
Persistent settings store for gesture, mouse, voice, and AI configuration.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from runtime_paths import ensure_runtime_dirs, get_settings_path


ACTION_OPTIONS: Dict[str, str] = {
    "none": "None",
    "move_mouse": "Move cursor",
    "left_click": "Left click",
    "right_click": "Right click",
    "drag_mouse": "Drag / drop",
    "scroll": "Scroll",
    "scroll_up": "Scroll up",
    "scroll_down": "Scroll down",
    "zoom_in": "Zoom in",
    "zoom_out": "Zoom out",
    "screenshot": "Screenshot",
    "toggle_system": "Toggle system",
    "toggle_debug": "Toggle debug",
    "toggle_zen": "Toggle zen mode",
    "voice_listen": "Listen once",
    "llm_analyze": "Analyze screen",
    "open_settings": "Open settings",
    "calibrate": "Calibrate",
    "next_tab": "Next tab",
    "previous_tab": "Previous tab",
    "mute_toggle": "Mute toggle",
    "press_key": "Press key",
    "hotkey": "Hotkey",
    "type_text": "Type text",
}

CONTINUOUS_ACTIONS = {"move_mouse", "drag_mouse", "scroll", "zoom_in", "zoom_out"}

HAND_SIDES = ("Left", "Right")


def normalize_handedness(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = str(value).strip().lower()
    if normalized.startswith("l"):
        return "Left"
    if normalized.startswith("r"):
        return "Right"
    return ""

DEFAULT_SETTINGS: Dict[str, Dict[str, Any]] = {
    "general": {
        "show_debug": False,
        "show_hud": True,
        "system_active": True,
        "zen_mode": False,
        "primary_hand": "auto",
    },
    "camera": {
        "camera_id": 0,
        "width": 1280,
        "height": 720,
        "confidence_threshold": 0.7,
        "max_hands": 2,
    },
    "mouse": {
        "roi_margin": 0.12,
        "alpha_min": 0.05,
        "alpha_max": 0.90,
        "invert_x": False,
        "invert_y": False,
        "pointer_gain": 1.0,
        "click_cooldown": 0.4,
        "freeze_duration": 0.25,
        "scroll_threshold": 0.01,
        "scroll_multiplier": 1500,
        "zoom_threshold": 0.02,
        "zoom_cooldown": 0.30,
    },
    "gestures": {
        "pinch_threshold": 0.12,
        "release_threshold": 0.18,
        "velocity_lock": 0.10,
        "buffer_size": 4,
        "filter_alpha": 0.6,
        "neutral_hand_size": 1.0,
        "state_actions": {
            "IDLE": "move_mouse",
            "MOVING": "move_mouse",
            "CLICKED": "left_click",
            "RIGHT_CLICK": "right_click",
            "GRABBING": "drag_mouse",
            "SCROLLING": "scroll",
            "LOCKED": "none",
            "PINCHING": "none",
        },
        "state_payloads": {},
        "gesture_actions": {
            "NONE": "none",
            "POINT": "none",
            "GRAB": "none",
            "PEACE": "right_click",
            "OK": "none",
            "THUMBS_UP": "scroll_up",
            "THUMBS_DOWN": "scroll_down",
            "PALM_OPEN": "none",
            "VOICE_MODE": "voice_listen",
        },
        "gesture_payloads": {},
        "hand_profiles": {
            "Left": {},
            "Right": {},
        },
    },
    "voice": {
        "enabled": True,
        "language": "tr-TR",
        "tts_rate": 160,
        "tts_volume": 0.8,
        "listen_timeout": 3,
        "phrase_time_limit": 4,
    },
    "ai": {
        "enabled": False,
        "model": "gemini-2.0-flash",
        "auto_context": False,
    },
    "ui": {
        "theme": "midnight",
        "hud_opacity": 0.60,
        "trail_max_len": 15,
        "particle_limit": 150,
        "show_debug_overlay": False,
    },
    "performance": {
        "frame_skip": 0,
        "adaptive_quality": True,
        "fps_limit": 30,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _normalize_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    profiles = raw.get("profiles") or {}
    active_profile = raw.get("active_profile") or "Default"
    if active_profile not in profiles:
        profiles[active_profile] = copy.deepcopy(DEFAULT_SETTINGS)

    normalized_profiles: Dict[str, Dict[str, Any]] = {}
    for name, profile in profiles.items():
        normalized = _deep_merge(DEFAULT_SETTINGS, profile if isinstance(profile, dict) else {})
        gestures = normalized.setdefault("gestures", {})
        gestures.setdefault("state_actions", {})
        gestures.setdefault("state_payloads", {})
        gestures.setdefault("gesture_actions", {})
        gestures.setdefault("gesture_payloads", {})
        hand_profiles = gestures.setdefault("hand_profiles", {})
        for side in HAND_SIDES:
            hand_profiles.setdefault(side, {})
        ui = normalized.setdefault("ui", {})
        if ui.get("theme") in {"glass", "glass-dark"}:
            ui["theme"] = "midnight"
        normalized_profiles[name] = normalized

    return {
        "active_profile": active_profile,
        "profiles": normalized_profiles,
    }


class SettingsManager:
    def __init__(self, path: Optional[Path] = None):
        ensure_runtime_dirs()
        self.path = path or get_settings_path()
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    return _normalize_data(json.load(f))
            except Exception:
                pass
        return _normalize_data({"active_profile": "Default", "profiles": {"Default": copy.deepcopy(DEFAULT_SETTINGS)}})

    @property
    def active_profile(self) -> str:
        return self.data["active_profile"]

    @property
    def current(self) -> Dict[str, Any]:
        return self.data["profiles"][self.active_profile]

    def profile_names(self) -> List[str]:
        return sorted(self.data["profiles"].keys())

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self.current.get(section, {}).get(key, default)

    def get_section(self, section: str) -> Dict[str, Any]:
        return copy.deepcopy(self.current.get(section, {}))

    def update(self, updates: Dict[str, Any]) -> None:
        self.data["profiles"][self.active_profile] = _deep_merge(self.current, updates)

    def set_value(self, section: str, key: str, value: Any) -> None:
        current = self.data["profiles"][self.active_profile]
        current.setdefault(section, {})[key] = value

    def get_binding(
        self,
        group: str,
        mapping: str,
        key: str,
        handedness: Optional[str] = None,
    ) -> Dict[str, str]:
        data = self.current.get(group, {})
        payload_name = mapping.replace("_actions", "_payloads")
        hand_name = normalize_handedness(handedness)

        if hand_name:
            hand_profiles = data.get("hand_profiles", {})
            hand_data = hand_profiles.get(hand_name, {})
            if key in hand_data.get(mapping, {}):
                return {
                    "action": hand_data.get(mapping, {}).get(key, "none"),
                    "payload": hand_data.get(payload_name, {}).get(key, ""),
                }

        action = data.get(mapping, {}).get(key, "none")
        payload = data.get(payload_name, {}).get(key, "")
        return {"action": action, "payload": payload}

    def set_binding(
        self,
        group: str,
        mapping: str,
        key: str,
        action: str,
        payload: str = "",
        handedness: Optional[str] = None,
    ) -> None:
        current = self.data["profiles"][self.active_profile]
        group_data = current.setdefault(group, {})
        payload_key = mapping.replace("_actions", "_payloads")
        hand_name = normalize_handedness(handedness)

        if hand_name:
            hand_profiles = group_data.setdefault("hand_profiles", {})
            hand_data = hand_profiles.setdefault(hand_name, {})
            global_action = group_data.get(mapping, {}).get(key, "none")
            global_payload = group_data.get(payload_key, {}).get(key, "")

            if action == global_action and payload == global_payload:
                if mapping in hand_data:
                    hand_data[mapping].pop(key, None)
                    if not hand_data[mapping]:
                        hand_data.pop(mapping, None)
                if payload_key in hand_data:
                    hand_data[payload_key].pop(key, None)
                    if not hand_data[payload_key]:
                        hand_data.pop(payload_key, None)
                return

            hand_data.setdefault(mapping, {})[key] = action
            hand_data.setdefault(payload_key, {})[key] = payload
            return

        group_data.setdefault(mapping, {})[key] = action
        group_data.setdefault(payload_key, {})[key] = payload

    def set_bindings(
        self,
        group: str,
        mapping: str,
        bindings: Dict[str, Dict[str, str]],
        handedness: Optional[str] = None,
    ) -> None:
        for key, value in bindings.items():
            self.set_binding(
                group,
                mapping,
                key,
                value.get("action", "none"),
                value.get("payload", ""),
                handedness=handedness,
            )

    def set_profile(self, profile_name: str, settings: Optional[Dict[str, Any]] = None) -> None:
        if settings is None:
            settings = self.current
        self.data["profiles"][profile_name] = _deep_merge(DEFAULT_SETTINGS, settings)
        self.data["active_profile"] = profile_name

    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        if profile_name not in self.data["profiles"]:
            self.set_profile(profile_name, copy.deepcopy(DEFAULT_SETTINGS))
        self.data["active_profile"] = profile_name
        return self.current

    def delete_profile(self, profile_name: str) -> None:
        if profile_name == self.active_profile:
            return
        self.data["profiles"].pop(profile_name, None)

    def reset_active(self) -> Dict[str, Any]:
        self.data["profiles"][self.active_profile] = copy.deepcopy(DEFAULT_SETTINGS)
        return self.current

    def save(self) -> None:
        ensure_runtime_dirs()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def save_active_as(self, profile_name: str) -> None:
        self.set_profile(profile_name, self.current)
        self.save()

    def bind_action_choices(self) -> List[str]:
        return list(ACTION_OPTIONS.keys())

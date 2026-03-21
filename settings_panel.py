"""
Cross-platform settings panel for Hand Control AI.
Runs in a separate process and persists to runtime JSON.
"""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Dict, Optional

from runtime_paths import ensure_runtime_dirs, get_settings_path
from settings_manager import ACTION_OPTIONS, HAND_SIDES, SettingsManager, normalize_handedness


ACTION_LABELS = {code: f"{code} - {label}" for code, label in ACTION_OPTIONS.items()}
ACTION_CODES_BY_LABEL = {label: code for code, label in ACTION_LABELS.items()}
GLOBAL_ACTION_CHOICES = list(ACTION_LABELS.values())
INHERIT_LABEL = "inherit - Use global default"
HAND_ACTION_CHOICES = [INHERIT_LABEL] + GLOBAL_ACTION_CHOICES
THEME_CHOICES = ("midnight", "dark", "light")

THEME_PALETTES: Dict[str, Dict[str, Any]] = {
    "midnight": {
        "bg": "#08111F",
        "panel": "#101A2E",
        "panel_alt": "#17233B",
        "field": "#121D33",
        "text": "#F3F7FF",
        "muted": "#8FA3C2",
        "accent": "#63D2FF",
        "accent2": "#A78BFA",
        "success": "#38D39F",
        "warning": "#F5A524",
        "danger": "#FB7185",
        "accent_map": {
            "neutral": "#93A8C8",
            "general": "#63D2FF",
            "camera": "#38D39F",
            "mouse": "#F59E0B",
            "gestures": "#A78BFA",
            "voice": "#34D399",
            "ai": "#F472B6",
            "ui": "#FBBF24",
            "performance": "#FB7185",
            "left": "#818CF8",
            "right": "#22C55E",
        },
    },
    "dark": {
        "bg": "#111318",
        "panel": "#1A1F29",
        "panel_alt": "#242A36",
        "field": "#1D2230",
        "text": "#F5F7FA",
        "muted": "#9BA7B8",
        "accent": "#7CC4FF",
        "accent2": "#9F7AEA",
        "success": "#5FD38E",
        "warning": "#F5B65B",
        "danger": "#F87171",
        "accent_map": {
            "neutral": "#A7B1C2",
            "general": "#7CC4FF",
            "camera": "#5FD38E",
            "mouse": "#F5B65B",
            "gestures": "#9F7AEA",
            "voice": "#22C55E",
            "ai": "#F472B6",
            "ui": "#FBBF24",
            "performance": "#F87171",
            "left": "#8B9CFF",
            "right": "#38D39F",
        },
    },
    "light": {
        "bg": "#F3F5F9",
        "panel": "#FFFFFF",
        "panel_alt": "#E9EEF7",
        "field": "#FFFFFF",
        "text": "#0F172A",
        "muted": "#516076",
        "accent": "#0F62FE",
        "accent2": "#7C3AED",
        "success": "#059669",
        "warning": "#D97706",
        "danger": "#DC2626",
        "accent_map": {
            "neutral": "#64748B",
            "general": "#0F62FE",
            "camera": "#059669",
            "mouse": "#D97706",
            "gestures": "#7C3AED",
            "voice": "#0EA5A4",
            "ai": "#D946EF",
            "ui": "#CA8A04",
            "performance": "#DC2626",
            "left": "#4338CA",
            "right": "#15803D",
        },
    },
}


def _action_label(action: str) -> str:
    return ACTION_LABELS.get(action, ACTION_LABELS["none"])


def _action_code(label: str) -> str:
    return ACTION_CODES_BY_LABEL.get(label, "none")


def _theme_name(name: Optional[str]) -> str:
    value = str(name or "midnight").strip().lower()
    if value in {"glass", "glass-dark"}:
        return "midnight"
    return value if value in THEME_PALETTES else "midnight"


def _palette(name: Optional[str]) -> Dict[str, Any]:
    return THEME_PALETTES[_theme_name(name)]


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, palette: Dict[str, Any]):
        super().__init__(parent, style="Panel.TFrame")
        self.palette = palette
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
            bg=palette["bg"],
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Panel.Vertical.TScrollbar")
        self.inner = ttk.Frame(self.canvas, style="Panel.TFrame")

        self.inner.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if self.winfo_containing(event.x_root, event.y_root) is not self.canvas:
            return
        delta = 0
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        elif getattr(event, "delta", 0):
            delta = int(-1 * (event.delta / 120))
        if delta:
            self.canvas.yview_scroll(delta, "units")

    def set_palette(self, palette: Dict[str, Any]):
        self.palette = palette
        self.canvas.configure(bg=palette["bg"], highlightbackground=palette["bg"])


class SettingsPanelApp:
    def __init__(self):
        ensure_runtime_dirs()
        self.manager = SettingsManager()
        self.theme_name = _theme_name(self.manager.get("ui", "theme", "midnight"))
        self.root = tk.Tk()
        self.root.title("Hand Control AI Settings")
        self.root.geometry("1120x840")
        self.root.minsize(980, 720)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.style = ttk.Style(self.root)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.vars: Dict[str, tk.Variable] = {}
        self.widgets: Dict[str, tk.Widget] = {}
        self.binding_vars: Dict[str, Dict[str, Dict[str, Dict[str, tk.StringVar]]]] = {
            "state_actions": {scope: {} for scope in ("global", *HAND_SIDES)},
            "gesture_actions": {scope: {} for scope in ("global", *HAND_SIDES)},
        }

        self._build_shell()
        self._load_profile_names()
        self.load_current_profile()

    def _build_shell(self):
        self._apply_theme(self.theme_name)

        header = ttk.Frame(self.root, padding=(18, 16, 18, 10), style="Header.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="Hand Control AI", style="Title.TLabel")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            header,
            text="Per-hand bindings, live theme preview, and polished runtime profiles.",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.profile_status = ttk.Label(header, text="", style="Meta.TLabel")
        self.profile_status.grid(row=2, column=0, sticky="w", pady=(6, 0))

        body = ttk.Frame(self.root, padding=(18, 0, 18, 12), style="Panel.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(body, style="Control.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew")

        palette = _palette(self.theme_name)
        self.profile_tab = ScrollableFrame(self.notebook, palette)
        self.general_tab = ScrollableFrame(self.notebook, palette)
        self.camera_tab = ScrollableFrame(self.notebook, palette)
        self.mouse_tab = ScrollableFrame(self.notebook, palette)
        self.gestures_tab = ScrollableFrame(self.notebook, palette)
        self.voice_tab = ScrollableFrame(self.notebook, palette)
        self.ai_tab = ScrollableFrame(self.notebook, palette)
        self.ui_tab = ScrollableFrame(self.notebook, palette)
        self.performance_tab = ScrollableFrame(self.notebook, palette)

        self.notebook.add(self.profile_tab, text="Profiles")
        self.notebook.add(self.general_tab, text="General")
        self.notebook.add(self.camera_tab, text="Camera")
        self.notebook.add(self.mouse_tab, text="Mouse")
        self.notebook.add(self.gestures_tab, text="Gestures")
        self.notebook.add(self.voice_tab, text="Voice")
        self.notebook.add(self.ai_tab, text="AI")
        self.notebook.add(self.ui_tab, text="UI")
        self.notebook.add(self.performance_tab, text="Performance")

        self._build_profile_tab(self.profile_tab.inner)
        self._build_general_tab(self.general_tab.inner)
        self._build_camera_tab(self.camera_tab.inner)
        self._build_mouse_tab(self.mouse_tab.inner)
        self._build_gestures_tab(self.gestures_tab.inner)
        self._build_voice_tab(self.voice_tab.inner)
        self._build_ai_tab(self.ai_tab.inner)
        self._build_ui_tab(self.ui_tab.inner)
        self._build_performance_tab(self.performance_tab.inner)

        footer = ttk.Frame(self.root, padding=(18, 0, 18, 18), style="Footer.TFrame")
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self.save_state = ttk.Label(footer, text=str(get_settings_path()), style="Meta.TLabel")
        self.save_state.grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(footer)
        actions.grid(row=0, column=1, sticky="e")

        ttk.Button(actions, text="Reload", command=self.reload_from_disk).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Apply", command=self.apply_now).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(actions, text="Save", command=self.save_current_profile).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(actions, text="Close", command=self.on_close).grid(row=0, column=3)

    def _apply_theme(self, theme_name: Optional[str] = None):
        palette = _palette(theme_name or self.theme_name)
        self.theme_name = _theme_name(theme_name or self.theme_name)
        self.palette = palette
        self.root.configure(bg=palette["bg"])

        self.style.configure(".", background=palette["bg"], foreground=palette["text"], fieldbackground=palette["field"])
        self.style.configure("Panel.TFrame", background=palette["bg"])
        self.style.configure("Header.TFrame", background=palette["panel"])
        self.style.configure("Footer.TFrame", background=palette["bg"])
        self.style.configure("Control.TNotebook", background=palette["bg"], borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            padding=(16, 9),
            background=palette["panel"],
            foreground=palette["muted"],
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", palette["accent"]), ("active", palette["panel_alt"])],
            foreground=[("selected", palette["bg"]), ("active", palette["text"])],
        )
        self.style.configure("TButton", padding=(10, 6), background=palette["panel_alt"], foreground=palette["text"])
        self.style.map("TButton", background=[("active", palette["accent"]), ("pressed", palette["accent2"])], foreground=[("active", palette["bg"]), ("pressed", palette["bg"])])
        self.style.configure("TCheckbutton", background=palette["bg"], foreground=palette["text"])
        self.style.map("TCheckbutton", foreground=[("active", palette["accent"])])
        self.style.configure("TEntry", fieldbackground=palette["field"], foreground=palette["text"], insertcolor=palette["text"])
        self.style.configure("TSpinbox", fieldbackground=palette["field"], foreground=palette["text"], insertcolor=palette["text"])
        self.style.configure("TCombobox", fieldbackground=palette["field"], foreground=palette["text"], background=palette["field"])
        self.style.map("TCombobox", fieldbackground=[("readonly", palette["field"])], foreground=[("readonly", palette["text"])])
        self.style.configure("Panel.Vertical.TScrollbar", background=palette["panel_alt"], troughcolor=palette["bg"], arrowcolor=palette["text"])
        self.style.configure("Title.TLabel", background=palette["panel"], foreground=palette["text"], font=("Helvetica", 18, "bold"))
        self.style.configure("Subtitle.TLabel", background=palette["panel"], foreground=palette["muted"])
        self.style.configure("Meta.TLabel", background=palette["panel"], foreground=palette["muted"])
        self.style.configure("Panel.TLabel", background=palette["bg"], foreground=palette["text"])
        self.style.configure("PanelNote.TLabel", background=palette["bg"], foreground=palette["muted"])

        for name, color in palette["accent_map"].items():
            style_name = f"{name.title()}Section.TLabelframe"
            self.style.configure(style_name, background=palette["bg"], foreground=color, padding=12)
            self.style.configure(f"{style_name}.Label", background=palette["bg"], foreground=color, font=("Helvetica", 11, "bold"))

        if hasattr(self, "profile_tab"):
            for tab in (
                self.profile_tab,
                self.general_tab,
                self.camera_tab,
                self.mouse_tab,
                self.gestures_tab,
                self.voice_tab,
                self.ai_tab,
                self.ui_tab,
                self.performance_tab,
            ):
                tab.set_palette(palette)

        if hasattr(self, "save_state"):
            self.save_state.configure(style="Meta.TLabel")
        if hasattr(self, "profile_status"):
            self.profile_status.configure(style="Meta.TLabel")
        if hasattr(self, "theme_var") and self.theme_var.get() != self.theme_name:
            self.theme_var.set(self.theme_name)

    def _section(self, parent, title: str, accent: str = "neutral"):
        style_name = f"{accent.title()}Section.TLabelframe"
        frame = ttk.LabelFrame(parent, text=title, padding=12, style=style_name)
        frame.pack(fill="x", pady=(0, 12))
        frame.columnconfigure(1, weight=1)
        return frame

    def _row(self, parent, row: int, label: str, widget):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        widget.grid(row=row, column=1, sticky="ew", pady=6)
        parent.columnconfigure(1, weight=1)

    def _add_bool_field(self, parent, key: str, label: str, row: int):
        var = tk.BooleanVar(value=False)
        self.vars[key] = var
        widget = ttk.Checkbutton(parent, variable=var)
        self._row(parent, row, label, widget)

    def _add_int_field(self, parent, key: str, label: str, row: int):
        var = tk.IntVar(value=0)
        self.vars[key] = var
        widget = ttk.Spinbox(parent, from_=-999999, to=999999, textvariable=var, width=12)
        self._row(parent, row, label, widget)

    def _add_float_field(self, parent, key: str, label: str, row: int, min_value: float = None, max_value: float = None):
        var = tk.DoubleVar(value=0.0)
        self.vars[key] = var
        widget = ttk.Spinbox(parent, from_=min_value if min_value is not None else -999999.0, to=max_value if max_value is not None else 999999.0, increment=0.01, textvariable=var, width=12)
        self._row(parent, row, label, widget)

    def _add_text_field(self, parent, key: str, label: str, row: int, width: int = 24):
        var = tk.StringVar(value="")
        self.vars[key] = var
        widget = ttk.Entry(parent, textvariable=var, width=width)
        self._row(parent, row, label, widget)

    def _add_choice_field(self, parent, key: str, label: str, row: int, values):
        var = tk.StringVar(value="")
        self.vars[key] = var
        widget = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
        self.widgets[key] = widget
        self._row(parent, row, label, widget)

    def _build_profile_tab(self, parent):
        section = self._section(parent, "Profile management")
        ttk.Label(section, text="Active profile").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        self.profile_var = tk.StringVar(value="")
        self.profile_combo = ttk.Combobox(section, textvariable=self.profile_var, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky="ew", pady=6)
        section.columnconfigure(1, weight=1)
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self.load_selected_profile())

        buttons = ttk.Frame(section)
        buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(buttons, text="Load", command=self.load_selected_profile).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Save As", command=self.save_as_profile).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(buttons, text="Duplicate", command=self.duplicate_profile).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(buttons, text="Delete", command=self.delete_profile).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(buttons, text="Reset Current", command=self.reset_current_profile).grid(row=0, column=4)

        note = ttk.Label(
            section,
            text="Changes are saved to the runtime JSON store and picked up by the main app automatically.",
            foreground="#555555",
            wraplength=760,
        )
        note.grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def _build_general_tab(self, parent):
        section = self._section(parent, "General", "general")
        self._add_bool_field(section, "general.show_debug", "Show debug overlay", 0)
        self._add_bool_field(section, "general.show_hud", "Show HUD", 1)
        self._add_bool_field(section, "general.system_active", "System active", 2)
        self._add_bool_field(section, "general.zen_mode", "Zen mode", 3)
        self._add_choice_field(section, "general.primary_hand", "Primary hand", 4, ["auto", "left", "right"])

    def _build_camera_tab(self, parent):
        section = self._section(parent, "Camera", "camera")
        self._add_int_field(section, "camera.camera_id", "Camera ID", 0)
        self._add_int_field(section, "camera.width", "Frame width", 1)
        self._add_int_field(section, "camera.height", "Frame height", 2)
        self._add_float_field(section, "camera.confidence_threshold", "Detection confidence", 3, 0.0, 1.0)
        self._add_int_field(section, "camera.max_hands", "Max hands", 4)

    def _build_mouse_tab(self, parent):
        section = self._section(parent, "Pointer physics", "mouse")
        self._add_float_field(section, "mouse.roi_margin", "ROI margin", 0, 0.0, 0.45)
        self._add_float_field(section, "mouse.alpha_min", "Smoothing alpha min", 1, 0.0, 1.0)
        self._add_float_field(section, "mouse.alpha_max", "Smoothing alpha max", 2, 0.0, 1.0)
        self._add_bool_field(section, "mouse.invert_x", "Invert X axis", 3)
        self._add_bool_field(section, "mouse.invert_y", "Invert Y axis", 4)
        self._add_float_field(section, "mouse.pointer_gain", "Pointer gain", 5, 0.1, 4.0)
        self._add_float_field(section, "mouse.click_cooldown", "Click cooldown", 6, 0.0, 3.0)
        self._add_float_field(section, "mouse.freeze_duration", "Click freeze duration", 7, 0.0, 1.0)
        self._add_float_field(section, "mouse.scroll_threshold", "Scroll threshold", 8, 0.0, 0.2)
        self._add_float_field(section, "mouse.scroll_multiplier", "Scroll multiplier", 9, 100.0, 5000.0)
        self._add_float_field(section, "mouse.zoom_threshold", "Zoom threshold", 10, 0.0, 0.2)
        self._add_float_field(section, "mouse.zoom_cooldown", "Zoom cooldown", 11, 0.0, 2.0)

    def _binding_grid(self, parent, title: str, mapping_name: str, keys, handedness: Optional[str] = None, accent: str = "gestures"):
        scope = "global" if not handedness else normalize_handedness(handedness) or "global"
        section = self._section(parent, title, accent)
        section.columnconfigure(1, weight=1)
        section.columnconfigure(2, weight=1)
        title_text = "Gesture / state" if mapping_name == "gesture_actions" else "State"
        ttk.Label(section, text=title_text, style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=(0, 8))
        ttk.Label(section, text="Action", style="Panel.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(0, 8))
        ttk.Label(section, text="Payload", style="Panel.TLabel").grid(row=0, column=2, sticky="w", pady=(0, 8))
        if handedness:
            ttk.Label(
                section,
                text=f"{scope} hand override. Blank or inherit keeps the global value.",
                style="PanelNote.TLabel",
            ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))
            start_row = 2
        else:
            start_row = 1

        for row, key in enumerate(keys, start=start_row):
            ttk.Label(section, text=key).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            action_var = tk.StringVar(value=INHERIT_LABEL if handedness else _action_label("none"))
            payload_var = tk.StringVar(value="")
            self.binding_vars[mapping_name][scope][key] = {"action": action_var, "payload": payload_var}

            values = HAND_ACTION_CHOICES if handedness else GLOBAL_ACTION_CHOICES
            action_combo = ttk.Combobox(section, textvariable=action_var, values=values, state="readonly")
            action_combo.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=4)
            payload_entry = ttk.Entry(section, textvariable=payload_var)
            payload_entry.grid(row=row, column=2, sticky="ew", pady=4)
            section.columnconfigure(2, weight=1)

    def _build_gestures_tab(self, parent):
        section = self._section(parent, "Gesture thresholds", "gestures")
        self._add_float_field(section, "gestures.pinch_threshold", "Pinch threshold", 0, 0.0, 1.0)
        self._add_float_field(section, "gestures.release_threshold", "Release threshold", 1, 0.0, 1.0)
        self._add_float_field(section, "gestures.velocity_lock", "Velocity lock", 2, 0.0, 1.0)
        self._add_int_field(section, "gestures.buffer_size", "Stability buffer", 3)
        self._add_float_field(section, "gestures.filter_alpha", "Landmark filter alpha", 4, 0.0, 1.0)
        self._add_float_field(section, "gestures.neutral_hand_size", "Neutral hand size", 5, 0.0, 10.0)

        self._binding_grid(parent, "State actions - Global", "state_actions", [
            "IDLE",
            "MOVING",
            "CLICKED",
            "RIGHT_CLICK",
            "GRABBING",
            "SCROLLING",
            "LOCKED",
            "PINCHING",
        ], accent="general")
        self._binding_grid(parent, "State actions - Left hand", "state_actions", [
            "IDLE",
            "MOVING",
            "CLICKED",
            "RIGHT_CLICK",
            "GRABBING",
            "SCROLLING",
            "LOCKED",
            "PINCHING",
        ], handedness="Left", accent="left")
        self._binding_grid(parent, "State actions - Right hand", "state_actions", [
            "IDLE",
            "MOVING",
            "CLICKED",
            "RIGHT_CLICK",
            "GRABBING",
            "SCROLLING",
            "LOCKED",
            "PINCHING",
        ], handedness="Right", accent="right")

        self._binding_grid(parent, "Gesture actions - Global", "gesture_actions", [
            "NONE",
            "POINT",
            "GRAB",
            "PEACE",
            "OK",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "PALM_OPEN",
            "VOICE_MODE",
        ], accent="gestures")
        self._binding_grid(parent, "Gesture actions - Left hand", "gesture_actions", [
            "NONE",
            "POINT",
            "GRAB",
            "PEACE",
            "OK",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "PALM_OPEN",
            "VOICE_MODE",
        ], handedness="Left", accent="left")
        self._binding_grid(parent, "Gesture actions - Right hand", "gesture_actions", [
            "NONE",
            "POINT",
            "GRAB",
            "PEACE",
            "OK",
            "THUMBS_UP",
            "THUMBS_DOWN",
            "PALM_OPEN",
            "VOICE_MODE",
        ], handedness="Right", accent="right")

    def _build_voice_tab(self, parent):
        section = self._section(parent, "Voice", "voice")
        self._add_bool_field(section, "voice.enabled", "Voice enabled", 0)
        self._add_text_field(section, "voice.language", "Language", 1)
        self._add_int_field(section, "voice.tts_rate", "TTS rate", 2)
        self._add_float_field(section, "voice.tts_volume", "TTS volume", 3, 0.0, 1.0)
        self._add_float_field(section, "voice.listen_timeout", "Listen timeout", 4, 0.5, 30.0)
        self._add_float_field(section, "voice.phrase_time_limit", "Phrase time limit", 5, 1.0, 30.0)

    def _build_ai_tab(self, parent):
        section = self._section(parent, "AI", "ai")
        self._add_bool_field(section, "ai.enabled", "AI enabled", 0)
        self._add_text_field(section, "ai.model", "Model", 1)
        self._add_bool_field(section, "ai.auto_context", "Auto context analysis", 2)

    def _build_ui_tab(self, parent):
        section = self._section(parent, "UI", "ui")
        self._add_choice_field(section, "ui.theme", "Theme", 0, list(THEME_CHOICES))
        self.theme_var = self.vars["ui.theme"]
        self.widgets["ui.theme"].bind("<<ComboboxSelected>>", lambda _event: self._apply_theme(self.theme_var.get()))
        self._add_float_field(section, "ui.hud_opacity", "HUD opacity", 1, 0.0, 1.0)
        self._add_int_field(section, "ui.trail_max_len", "Trail length", 2)
        self._add_int_field(section, "ui.particle_limit", "Particle limit", 3)
        self._add_bool_field(section, "ui.show_debug_overlay", "Show debug overlay", 4)

    def _build_performance_tab(self, parent):
        section = self._section(parent, "Performance", "performance")
        self._add_int_field(section, "performance.frame_skip", "Frame skip", 0)
        self._add_bool_field(section, "performance.adaptive_quality", "Adaptive quality", 1)
        self._add_int_field(section, "performance.fps_limit", "FPS limit", 2)

    def _load_profile_names(self):
        names = self.manager.profile_names()
        self.profile_combo.configure(values=names)
        if self.manager.active_profile in names:
            self.profile_var.set(self.manager.active_profile)
        elif names:
            self.profile_var.set(names[0])

    def _hand_override(self, profile: Dict[str, Dict], mapping_name: str, key: str, handedness: str) -> Optional[Dict[str, str]]:
        side = normalize_handedness(handedness)
        if not side:
            return None
        gestures = profile.get("gestures", {})
        hand_profiles = gestures.get("hand_profiles", {})
        hand_data = hand_profiles.get(side, {})
        action_data = hand_data.get(mapping_name, {})
        payload_data = hand_data.get(mapping_name.replace("_actions", "_payloads"), {})
        if key not in action_data and key not in payload_data:
            return None
        return {
            "action": action_data.get(key, ""),
            "payload": payload_data.get(key, ""),
        }

    def _apply_profile_to_vars(self, profile: Dict[str, Dict]):
        for section, values in profile.items():
            if not isinstance(values, dict):
                continue
            if section in ("gestures",):
                continue
            for key, value in values.items():
                field_key = f"{section}.{key}"
                var = self.vars.get(field_key)
                if var is not None:
                    var.set(value)

        gestures = profile.get("gestures", {})
        for key, value in gestures.items():
            if key in ("state_actions", "gesture_actions"):
                continue
            field_key = f"gestures.{key}"
            var = self.vars.get(field_key)
            if var is not None:
                var.set(value)

        for mapping_name in ("state_actions", "gesture_actions"):
            mapping = gestures.get(mapping_name, {})
            payloads = gestures.get(mapping_name.replace("_actions", "_payloads"), {})
            global_entries = self.binding_vars[mapping_name]["global"]
            for key, entry in global_entries.items():
                entry["action"].set(_action_label(mapping.get(key, "none")))
                entry["payload"].set(payloads.get(key, ""))

            for side in HAND_SIDES:
                side_entries = self.binding_vars[mapping_name][side]
                for key, entry in side_entries.items():
                    override = self._hand_override(profile, mapping_name, key, side)
                    if override is None:
                        entry["action"].set(INHERIT_LABEL)
                        entry["payload"].set("")
                    else:
                        entry["action"].set(_action_label(override.get("action", "none")))
                        entry["payload"].set(override.get("payload", ""))

    def load_current_profile(self):
        profile = copy.deepcopy(self.manager.current)
        self._apply_profile_to_vars(profile)
        self._apply_theme(self.vars.get("ui.theme").get() if "ui.theme" in self.vars else self.theme_name)
        self.profile_var.set(self.manager.active_profile)
        self.profile_status.configure(text=f"Profile: {self.manager.active_profile} | {get_settings_path()}")

    def load_selected_profile(self):
        profile_name = self.profile_var.get().strip()
        if not profile_name:
            return
        if profile_name != self.manager.active_profile:
            self.manager.load_profile(profile_name)
            self.manager.save()
        self.load_current_profile()

    def _collect_profile_from_vars(self) -> Dict[str, Dict]:
        current = copy.deepcopy(self.manager.current)
        for key, var in self.vars.items():
            section, setting = key.split(".", 1)
            current.setdefault(section, {})
            value = var.get()
            if section == "general" and setting == "primary_hand":
                value = str(value).strip().lower() or "auto"
                if value not in {"auto", "left", "right"}:
                    value = "auto"
            if section == "ui" and setting == "theme":
                value = _theme_name(value)
            if section == "camera" and setting in {"camera_id", "width", "height", "max_hands"}:
                value = max(0 if setting == "camera_id" else 1, int(value))
            if section == "gestures" and setting in {"buffer_size"}:
                value = max(1, int(value))
            if section == "gestures" and setting in {"neutral_hand_size"}:
                value = max(0.01, float(value))
            if section == "ui" and setting == "hud_opacity":
                value = max(0.0, min(1.0, float(value)))
            if section == "voice" and setting == "tts_volume":
                value = max(0.0, min(1.0, float(value)))
            if section == "voice" and setting == "tts_rate":
                value = max(50, int(value))
            if section == "voice" and setting in {"listen_timeout", "phrase_time_limit"}:
                value = max(0.5 if setting == "listen_timeout" else 1.0, float(value))
            if section == "mouse" and setting == "roi_margin":
                value = max(0.0, min(0.45, float(value)))
            if section == "mouse" and setting in {"alpha_min", "alpha_max"}:
                value = max(0.01, min(0.99, float(value)))
            if section == "mouse" and setting == "pointer_gain":
                value = max(0.1, float(value))
            if section == "mouse" and setting == "scroll_multiplier":
                value = max(1.0, float(value))
            if section == "mouse" and setting in {"click_cooldown", "freeze_duration", "scroll_threshold", "zoom_threshold", "zoom_cooldown"}:
                value = max(0.0, float(value))
            if section == "performance" and setting == "frame_skip":
                value = max(0, int(value))
            if section == "performance" and setting == "fps_limit":
                value = max(1, int(value))
            current[section][setting] = value

        gestures = current.setdefault("gestures", {})
        hand_profiles = gestures.setdefault("hand_profiles", {side: {} for side in HAND_SIDES})
        for mapping_name in ("state_actions", "gesture_actions"):
            mappings = {}
            payloads = {}
            for key, entry in self.binding_vars[mapping_name]["global"].items():
                mappings[key] = _action_code(entry["action"].get())
                payloads[key] = entry["payload"].get().strip()
            gestures[mapping_name] = mappings
            gestures[mapping_name.replace("_actions", "_payloads")] = payloads

            for side in HAND_SIDES:
                hand_mappings = {}
                hand_payloads = {}
                for key, entry in self.binding_vars[mapping_name][side].items():
                    action_label = entry["action"].get()
                    payload = entry["payload"].get().strip()
                    if action_label == INHERIT_LABEL:
                        continue
                    action_code = _action_code(action_label)
                    if action_code == mappings.get(key, "none") and payload == payloads.get(key, ""):
                        continue
                    hand_mappings[key] = action_code
                    hand_payloads[key] = payload
                if hand_mappings or hand_payloads:
                    hand_profiles.setdefault(side, {})[mapping_name] = hand_mappings
                    hand_profiles.setdefault(side, {})[mapping_name.replace("_actions", "_payloads")] = hand_payloads
                else:
                    hand_profiles.setdefault(side, {}).pop(mapping_name, None)
                    hand_profiles.setdefault(side, {}).pop(mapping_name.replace("_actions", "_payloads"), None)
        return current

    def apply_now(self):
        try:
            profile = self._collect_profile_from_vars()
        except Exception as exc:
            messagebox.showerror("Settings", f"Invalid value: {exc}")
            return False
        self.manager.set_profile(self.manager.active_profile, profile)
        self.manager.save()
        self._apply_theme(profile.get("ui", {}).get("theme", self.theme_name))
        self.profile_status.configure(text=f"Saved: {self.manager.active_profile} | {get_settings_path()}")
        return True

    def save_current_profile(self):
        if self.apply_now():
            messagebox.showinfo("Settings", "Current profile saved.")

    def save_as_profile(self):
        name = simpledialog.askstring("Save As", "Profile name:", parent=self.root)
        if not name:
            return
        try:
            profile = self._collect_profile_from_vars()
        except Exception as exc:
            messagebox.showerror("Settings", f"Invalid value: {exc}")
            return
        self.manager.set_profile(name.strip(), profile)
        self.manager.save()
        self._load_profile_names()
        self.profile_var.set(self.manager.active_profile)
        self.load_current_profile()

    def duplicate_profile(self):
        name = simpledialog.askstring("Duplicate", "Duplicate profile name:", parent=self.root)
        if not name:
            return
        try:
            profile = self._collect_profile_from_vars()
        except Exception as exc:
            messagebox.showerror("Settings", f"Invalid value: {exc}")
            return
        self.manager.set_profile(name.strip(), profile)
        self.manager.save()
        self._load_profile_names()
        self.profile_var.set(self.manager.active_profile)
        self.load_current_profile()

    def delete_profile(self):
        active = self.manager.active_profile
        if len(self.manager.profile_names()) <= 1:
            messagebox.showwarning("Settings", "At least one profile must remain.")
            return

        target = self.profile_var.get().strip() or active
        if target == active:
            messagebox.showwarning("Settings", "Load another profile before deleting the active one.")
            return

        if not messagebox.askyesno("Delete profile", f"Delete profile '{target}'?"):
            return

        self.manager.delete_profile(target)
        self.manager.save()
        self._load_profile_names()
        self.profile_var.set(self.manager.active_profile)
        self.load_current_profile()

    def reset_current_profile(self):
        if not messagebox.askyesno("Reset profile", "Reset current profile to defaults?"):
            return
        self.manager.reset_active()
        self.manager.save()
        self.load_current_profile()

    def reload_from_disk(self):
        self.manager = SettingsManager()
        self._load_profile_names()
        self.load_current_profile()

    def on_close(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def run_settings_panel():
    try:
        app = SettingsPanelApp()
        app.run()
    except Exception as exc:
        print(f"Settings panel cannot start: {exc}")


if __name__ == "__main__":
    run_settings_panel()
    run_settings_panel()

"""
Voice Recognition and Dictation Engine - PRO Version
Multimodal-ready STT/TTS system with robust command matching.
"""

import threading
import time
from enum import Enum
from typing import Callable, List, Optional

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional dependency
    sr = None

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None


class VoiceState(Enum):
    IDLE = 1
    LISTENING = 2
    PROCESSING = 3
    SUCCESS = 4
    ERROR = 5


class VoiceCommandEngine:
    """Voice engine with non-blocking TTS and multimodal support."""
    
    def __init__(self, on_result: Optional[Callable[[str], None]] = None):
        self.enabled = True
        self.language = "tr-TR"
        self.listen_timeout = 3
        self.phrase_time_limit = 4
        self.recognizer = sr.Recognizer() if sr else None
        self.mic = None
        self.input_available = False

        if self.recognizer and sr and hasattr(sr, "Microphone"):
            try:
                self.mic = sr.Microphone()
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                self.input_available = True
            except Exception:
                self.mic = None
                self.input_available = False

        # Text-to-speech
        try:
            self.tts = pyttsx3.init() if pyttsx3 else None
            if self.tts:
                self.tts.setProperty("rate", 160)
                self.tts.setProperty("volume", 0.8)
        except Exception:
            self.tts = None
        
        self.on_result = on_result
        self.state = VoiceState.IDLE
        self.is_listening = False
        self.available = bool(self.enabled and (self.input_available or self.tts))

    def configure(
        self,
        enabled: Optional[bool] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
        language: Optional[str] = None,
        listen_timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None,
    ):
        if enabled is not None:
            self.enabled = bool(enabled)
        if language is not None:
            self.language = language
        if listen_timeout is not None:
            self.listen_timeout = max(0.5, float(listen_timeout))
        if phrase_time_limit is not None:
            self.phrase_time_limit = max(1.0, float(phrase_time_limit))
        if self.tts:
            if rate is not None:
                self.tts.setProperty("rate", max(50, int(rate)))
            if volume is not None:
                self.tts.setProperty("volume", max(0.0, min(1.0, float(volume))))
        self.available = bool(self.enabled and (self.input_available or self.tts))

    def speak(self, text: str, async_mode: bool = True):
        """Speak text (async by default to avoid blocking the main loop)."""
        if not self.enabled:
            return
        if not self.tts:
            print(f"[TTS] {text}")
            return

        def _speak():
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception:
                pass

        if async_mode:
            threading.Thread(target=_speak, daemon=True).start()
        else:
            _speak()

    def listen_once(self):
        """Listen for a single command in a separate thread."""
        if self.is_listening or not self.enabled or not self.input_available:
            return
        self.is_listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.state = VoiceState.LISTENING
        if not self.enabled or not self.input_available or not self.recognizer or not self.mic:
            self.state = VoiceState.ERROR
            self.is_listening = False
            return
        try:
            with self.mic as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
            
            self.state = VoiceState.PROCESSING
            text = self.recognizer.recognize_google(audio, language=self.language)
            
            if self.on_result:
                self.on_result(text)
            
            self.state = VoiceState.SUCCESS
        except Exception:
            self.state = VoiceState.ERROR
        finally:
            self.is_listening = False
            time.sleep(1)
            self.state = VoiceState.IDLE

    def match_command(self, text: str, commands: List[dict]) -> Optional[dict]:
        """Fuzzy match text against a list of registered commands."""
        text = text.lower()
        best_match = None
        max_score = 0
        
        for cmd in commands:
            keywords = cmd.get("keywords") or [cmd.get("command", "")]
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 1
            
            rel_score = score / max(1, len(keywords))
            if rel_score > 0.6 and rel_score > max_score:
                max_score = rel_score
                best_match = cmd
                
        return best_match

    def create_command(self, keywords: List[str], action: Callable, description: str = ""):
        return {
            "keywords": [k.lower() for k in keywords],
            "action": action,
            "description": description,
        }

    def create_voice_command(self, command: str, action: Callable, description: str = ""):
        return {
            "command": command,
            "keywords": [command.lower()],
            "action": action,
            "description": description or command,
        }

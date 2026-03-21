"""
Voice Recognition and Dictation Engine - PRO Version
Multimodal-ready STT/TTS system with robust command matching.
"""

import speech_recognition as sr
import pyttsx3
import threading
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum
import queue
import time


class VoiceState(Enum):
    IDLE = 1
    LISTENING = 2
    PROCESSING = 3
    SUCCESS = 4
    ERROR = 5


class VoiceCommandEngine:
    """Voice engine with non-blocking TTS and multimodal support."""
    
    def __init__(self, on_result: Optional[Callable[[str], None]] = None):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        # Adjust for ambient noise on init
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            print("[VOICE] No microphone found.")

        # Text-to-speech
        try:
            self.tts = pyttsx3.init()
            self.tts.setProperty('rate', 160)
            self.tts.setProperty('volume', 0.8)
        except Exception:
            self.tts = None
        
        self.on_result = on_result
        self.state = VoiceState.IDLE
        self.is_listening = False

    def speak(self, text: str, async_mode: bool = True):
        """Speak text (async by default to avoid blocking the main loop)."""
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
        if self.is_listening: return
        self.is_listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.state = VoiceState.LISTENING
        try:
            with self.mic as source:
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=4)
            
            self.state = VoiceState.PROCESSING
            text = self.recognizer.recognize_google(audio, language='tr-TR')
            
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
            score = 0
            for kw in cmd['keywords']:
                if kw in text:
                    score += 1
            
            rel_score = score / len(cmd['keywords'])
            if rel_score > 0.6 and rel_score > max_score:
                max_score = rel_score
                best_match = cmd
                
        return best_match

    def create_command(self, keywords: List[str], action: Callable, description: str = ""):
        return {
            'keywords': [k.lower() for k in keywords],
            'action': action,
            'description': description
        }

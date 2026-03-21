"""
Ses ve dikteleme sistemi
Voice Recognition and Dictation Engine
"""

import speech_recognition as sr
import pyttsx3
import threading
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum
import queue


class VoiceState(Enum):
    """Ses durumu"""
    IDLE = 1
    LISTENING = 2
    PROCESSING = 3
    ERROR = 4


@dataclass
class VoiceEvent:
    """Ses olayı"""
    state: VoiceState
    text: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None


class VoiceCommandEngine:
    """Ses komutu ve dikteleme motoru"""
    
    def __init__(self, on_result: Optional[Callable[[str], None]] = None,
                 on_state_change: Optional[Callable[[VoiceState], None]] = None):
        """
        Ses motorunu başlat
        
        Args:
            on_result: Sonuç callback'i
            on_state_change: Durum değişim callback'i
        """
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        
        # Makine öğrenmesi için ses seviyesini ayarla
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # Text-to-speech
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Uyarı: TTS motoru başlatılamadı: {e}")
            self.tts_engine = None
        
        self.on_result = on_result
        self.on_state_change = on_state_change
        self.is_listening = False
        self.state = VoiceState.IDLE
        self.event_queue: queue.Queue = queue.Queue()
        self.listener_thread: Optional[threading.Thread] = None
        
    def _set_state(self, new_state: VoiceState) -> None:
        """Durumu güncelle"""
        self.state = new_state
        if self.on_state_change:
            self.on_state_change(new_state)
    
    def start_listening(self) -> None:
        """Dinlemeyi başla"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self._set_state(VoiceState.LISTENING)
        
        # Arka plan thread'inde dinle
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
    
    def stop_listening(self) -> None:
        """Dinlemeyi durdur"""
        self.is_listening = False
        self._set_state(VoiceState.IDLE)
    
    def _listen_loop(self) -> None:
        """Ses dinleme döngüsü"""
        try:
            with self.mic as source:
                # Timeout ile dinle
                audio = self.recognizer.listen(source, timeout=5)
            
            self._set_state(VoiceState.PROCESSING)
            
            # Google Speech Recognition kullan
            try:
                result = self.recognizer.recognize_google(audio, language='tr-TR')
                confidence = 0.9  # Google API güven skoru döndürmüyor
                
                if self.on_result:
                    self.on_result(result)
                
                self.speak(f"Anladığım: {result}")
                self._set_state(VoiceState.IDLE)
                
            except sr.UnknownValueError:
                error_msg = "Ses tanınamadı"
                self._set_state(VoiceState.ERROR)
                self.speak(error_msg)
                
            except sr.RequestError as e:
                error_msg = f"Hata: {str(e)}"
                self._set_state(VoiceState.ERROR)
                self.speak(error_msg)
        
        except sr.RequestError as e:
            self._set_state(VoiceState.ERROR)
    
    def speak(self, text: str) -> None:
        """Metni sesle oku"""
        try:
            if self.tts_engine:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                print(f"TTS Devre Dışı: {text}")
        except Exception as e:
            print(f"TTS hatası: {e}")
    
    def process_dictation(self, audio_data: Optional[sr.AudioData] = None) -> Optional[str]:
        """
        Dikteleme işle
        
        Args:
            audio_data: Ses verisi (isteğe bağlı)
            
        Returns:
            Tanınan metin
        """
        try:
            if audio_data is None:
                with self.mic as source:
                    audio_data = self.recognizer.listen(source, timeout=3)
            
            text = self.recognizer.recognize_google(audio_data, language='tr-TR')
            return text
        
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None
    
    def create_voice_command(self, command: str, action: Callable) -> dict:
        """
        Ses komutu oluştur
        
        Args:
            command: Komut metni (örn: "kırmızı düğme tıkla")
            action: Çalıştırılacak fonksiyon
            
        Returns:
            Komut sözlüğü
        """
        return {
            'command': command.lower(),
            'action': action,
            'keywords': command.lower().split()
        }
    
    def match_voice_command(self, text: str, commands: list) -> Optional[dict]:
        """
        Metni komutlarla eşleştir
        
        Args:
            text: Tanınan metin
            commands: Komut listesi
            
        Returns:
            Eşleşen komut
        """
        text_lower = text.lower()
        
        for cmd in commands:
            # Anahtar kelimeleri kontrol et
            matches = sum(1 for kw in cmd['keywords'] if kw in text_lower)
            if matches >= len(cmd['keywords']) * 0.7:  # %70 eşleşme
                return cmd
        
        return None
    
    def cleanup(self) -> None:
        """Kaynakları temizle"""
        self.stop_listening()
        if self.tts_engine:
            self.tts_engine.stop()


class KeyboardSimulator:
    """Parmak hareketleriyle klavye benzetimi"""
    
    # Tanınan hareketler -> tuş eşlemeleri
    GESTURE_KEYBOARD_MAP = {
        'point': 'click',  # İşaret parmağı - tıklama
        'peace': 'double_click',  # Peace - çift tıklama
        'ok': 'enter',  # OK - Enter
        'thumbs_up': 'arrow_up',  # Başparmak yukarı
        'thumbs_down': 'arrow_down',  # Başparmak aşağı
    }
    
    # Hareket sekvansları
    GESTURE_SEQUENCES = {
        'swipe_right': 'delete',  # Sağa kaydır
        'swipe_left': 'backspace',  # Sola kaydır
        'swipe_up': 'tab',  # Yukarı kaydır
        'swipe_down': 'escape',  # Aşağı kaydır
    }
    
    @staticmethod
    def get_key_for_gesture(gesture_name: str) -> Optional[str]:
        """Hareket adından tuş al"""
        return KeyboardSimulator.GESTURE_KEYBOARD_MAP.get(gesture_name.lower())
    
    @staticmethod
    def simulate_key_press(key: str) -> None:
        """Tuş basışını simüle et"""
        try:
            import pyautogui
            
            key_mapping = {
                'click': pyautogui.click,
                'double_click': lambda: pyautogui.click(clicks=2),
                'enter': lambda: pyautogui.press('return'),
                'arrow_up': lambda: pyautogui.press('up'),
                'arrow_down': lambda: pyautogui.press('down'),
                'delete': lambda: pyautogui.press('delete'),
                'backspace': lambda: pyautogui.press('backspace'),
                'tab': lambda: pyautogui.press('tab'),
                'escape': lambda: pyautogui.press('esc'),
            }
            
            if key in key_mapping:
                key_mapping[key]()
        
        except ImportError:
            print("pyautogui kütüphanesi gerekli")
    
    @staticmethod
    def type_text(text: str, interval: float = 0.05) -> None:
        """Metin yazı"""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
        except ImportError:
            print("pyautogui kütüphanesi gerekli")

"""
LLM Brain Module - AI Intelligence Engine
Powered by Google Gemini for multimodal reasoning and visual analysis.
"""

import os
from typing import Optional, Tuple

import cv2
from dotenv import load_dotenv

try:
    import PIL.Image
except Exception:  # pragma: no cover - optional dependency
    PIL = None

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None

load_dotenv()

class LLMAgent:
    """Multimodal AI Agent for Screen Understanding and Reasoning."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash", enabled: bool = True):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.enabled = enabled
        self.active = False
        self.failure_count = 0
        self.max_failures = 3
        
        if self.enabled and self.api_key and genai and PIL:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.active = True
                print("[LLM] Brain Connected Successfully.")
            except Exception as e:
                print(f"[LLM] Connection Failed: {e}")
                self.active = False
        else:
            print("[LLM] No API Key provided. Brain is Offline.")

    def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            print("[LLM] Critical failures exceeded. Deactivating AI module.")
            self.active = False

    def configure(self, enabled: Optional[bool] = None, model_name: Optional[str] = None):
        if enabled is not None:
            self.enabled = bool(enabled)
        if model_name:
            self.model_name = model_name

        self.active = False
        if not self.enabled or not self.api_key or not genai or not PIL:
            return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.active = True
        except Exception as e:
            print(f"[LLM] Reconfigure Failed: {e}")

    def analyze_frame(self, frame_bgr) -> str:
        """Describe what is currently on the screen."""
        if not self.active or not genai or not PIL:
            return "AI Brain is currently offline."
        
        try:
            # Convert BGR to RGB for PIL
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(frame_rgb)
            
            prompt = "Şu an ekranda ne olduğunu, aktif pencereleri ve önemli interaktif öğeleri kısaca açıkla. (Türkçe)"
            response = self.model.generate_content([prompt, img])
            self.failure_count = 0 # Reset on success
            return response.text
        except Exception as e:
            self._handle_failure()
            return f"Analiz hatası: {str(e)}"

    def find_element(self, frame_bgr, description: str) -> Optional[Tuple[float, float]]:
        """Find coordinates of an element with robust parsing and failure handling."""
        if not self.active or not genai or not PIL:
            return None
        
        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(frame_rgb)
            
            prompt = (f"Ekrandaki '{description}' öğesini bul ve koordinatlarını [ymin, xmin, ymax, xmax] formatında ver. "
                     "Sadece koordinat listesini döndür. Eğer bulamazsan 'NONE' yaz.")
            
            response = self.model.generate_content([prompt, img])
            text = response.text.strip().upper()
            
            if "NONE" in text: return None
            
            import re
            # Improved regex to find anything that looks like [y, x, y, x]
            match = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", text)
            if match:
                coords = [int(c) / 1000.0 for c in match.groups()]
                center_x = (coords[1] + coords[3]) / 2 # (xmin + xmax) / 2
                center_y = (coords[0] + coords[2]) / 2 # (ymin + ymax) / 2
                self.failure_count = 0 # Reset on success
                return (center_x, center_y)
            
            return None
        except Exception as e:
            print(f"[LLM] Search Error: {e}")
            self._handle_failure()
            return None

    def reason_command(self, query: str) -> str:
        """Process complex text queries for logical reasoning."""
        if not self.active or not genai:
            return "Zeka motoru devre dışı."
        
        try:
            prompt = f"Sen bir bilgisayar kontrol asistanısın. Kullanıcının şu isteğini yorumla ve kısa, aksiyon odaklı bir cevap ver: '{query}'"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return str(e)

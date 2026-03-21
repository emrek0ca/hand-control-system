"""
Proje Versiyonu ve Bilgi
Project Version and Information
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__date__ = "14 Ocak 2026"
__description__ = "Hand Gesture Control System - Professional AI-Powered Gesture Recognition"

PROJECT_INFO = {
    "name": "Hand Gesture Control System",
    "version": __version__,
    "date": __date__,
    "language": "Python 3.8+",
    "license": "Educational & Research",
    "description": __description__,
    
    "modules": {
        "hand_tracker.py": "El izleme ve hareket tanıma motoru",
        "interaction_system.py": "Nesnelerle etkileşim sistemi",
        "voice_system.py": "Ses tanıma ve dikte sistemi",
        "advanced_features.py": "İleri hareket analizi ve sekvanslar",
        "main.py": "Ana uygulama",
        "config.py": "Sistem konfigürasyonu",
        "test.py": "Test suite'i",
        "install.py": "Kurulum scripti",
    },
    
    "features": [
        "✅ Gerçek zamanlı el izleme (MediaPipe Hands)",
        "✅ 8+ Hareket tanıma",
        "✅ Etkileşimli nesne yönetimi",
        "✅ Sürükle ve bırak (Drag & Drop)",
        "✅ Ses komut tanıma (Türkçe)",
        "✅ Metin-konuşma (TTS)",
        "✅ Parmak hareketi ile klavye simülasyonu",
        "✅ Multi-hand support",
        "✅ Hareket sekvansları",
        "✅ Performans optimizasyonu",
    ],
    
    "gestures": {
        "POINT": "İşaret parmağı uzatılmış",
        "GRAB": "Tüm parmaklar kapalı",
        "PEACE": "İşaret ve orta parmak açık",
        "OK": "OK işareti (başparmak + işaret)",
        "THUMBS_UP": "Başparmak yukarı",
        "THUMBS_DOWN": "Başparmak aşağı",
        "PALM_OPEN": "El açık",
        "VOICE_MODE": "Tüm parmaklar açık (uzağa)",
    },
    
    "requirements": {
        "opencv-python": "4.8.1.78",
        "mediapipe": "0.10.8",
        "numpy": "1.24.3",
        "scipy": "1.11.4",
        "pyttsx3": "2.90",
        "SpeechRecognition": "3.10.0",
        "pyaudio": "0.2.13",
    },
    
    "statistics": {
        "total_lines_of_code": 2500,
        "modules": 7,
        "classes": 25,
        "functions": 80,
        "test_cases": 4,
    },
    
    "system_requirements": {
        "python": "3.8+",
        "ram_minimum": "2GB",
        "cpu_cores_recommended": 4,
        "camera": "640x480 minimum",
        "microphone": "Optional (for voice features)",
    },
    
    "performance": {
        "recommended_fps": 30,
        "minimum_fps": 15,
        "supported_resolution": "1280x720",
        "hand_detection_confidence": 0.7,
    },
}

QUICK_COMMANDS = {
    "setup": "python install.py",
    "run": "python main.py",
    "test": "python test.py",
    "demo": "python advanced_demo.py",
    "start": "python start.py",
}

def print_version():
    """Versiyon bilgisini yazdır"""
    print(f"""
    {PROJECT_INFO['name']} v{PROJECT_INFO['version']}
    Tarih: {PROJECT_INFO['date']}
    
    Açıklama: {PROJECT_INFO['description']}
    
    Python Sürümü: {PROJECT_INFO['system_requirements']['python']}
    Durum: ✅ Üretime Hazır
    """)

if __name__ == "__main__":
    print_version()
    print("\n📦 Hızlı Komutlar:")
    for cmd_name, cmd in QUICK_COMMANDS.items():
        print(f"  {cmd_name}: {cmd}")

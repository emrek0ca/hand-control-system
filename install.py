#!/usr/bin/env python3
"""
Installer script for Hand Gesture Control System
Uygulamayı kurmak için çalıştır: python install.py
"""

import os
import sys
import subprocess
import platform
from runtime_paths import ensure_runtime_dirs

def print_header(text):
    """Başlık yazdır"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python_version():
    """Python sürümünü kontrol et"""
    print_header("Python Sürümü Kontrolü")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ gerekli, bulundu: {version.major}.{version.minor}")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Uygun")

def check_dependencies():
    """Sistem bağımlılıklarını kontrol et"""
    print_header("Sistem Bağımlılıkları Kontrolü")
    
    system = platform.system()
    print(f"İşletim Sistemi: {system}")
    
    if system == "Darwin":  # macOS
        print("macOS üzerinde çalışıyor")
        print("✅ macOS kurulumu destekleniyor")
    elif system == "Windows":
        print("Windows üzerinde çalışıyor")
        print("✅ Windows kurulumu destekleniyor")
    elif system == "Linux":
        print("Linux üzerinde çalışıyor")
        print("✅ Linux kurulumu destekleniyor")

def install_requirements():
    """Gerekli kütüphaneleri kur"""
    print_header("Kütüphaneleri Kurma")
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ {requirements_file} bulunamadı")
        sys.exit(1)
    
    print(f"📦 {requirements_file} kurulmaya başlanıyor...\n")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("\n✅ Tüm kütüphaneler başarıyla kuruldu")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Kurulum sırasında hata: {e}")
        sys.exit(1)

def create_directories():
    """Gerekli klasörleri oluştur"""
    print_header("Klasörleri Oluşturma")
    data_dir = ensure_runtime_dirs()
    print(f"✅ Runtime veri dizini hazır: {data_dir}")

def test_installation():
    """Kurulumu test et"""
    print_header("Kurulumun Test Edilmesi")
    
    try:
        # İçe aktar
        print("📝 Modüller kontrol ediliyor...")
        import cv2
        print(f"  ✅ OpenCV {cv2.__version__}")
        
        import mediapipe as mp
        print(f"  ✅ MediaPipe {mp.__version__}")
        
        import numpy as np
        print(f"  ✅ NumPy {np.__version__}")
        
        import speech_recognition as sr
        print(f"  ✅ SpeechRecognition")
        
        print("\n✅ Tüm modüller başarıyla içe aktarıldı")
        return True
    
    except ImportError as e:
        print(f"\n❌ Hata: {e}")
        return False

def print_instructions():
    """Kurulum talimatlarını yazdır"""
    print_header("Kurulum Tamamlandı!")
    
    print("""
📋 BAŞLANGÇ TALIMATLARI

1️⃣  Uygulamayı Çalıştır:
    python launcher.py

2️⃣  Kontroller:
    - İşaret Parmağı → Pointer (fare imleçi)
    - Tutma Hareketi → Nesneleri sürükle
    - Tüm Parmaklar Açık → Ses modu
    - 'q' Tuşu → Çıkış
    - 'd' Tuşu → Debug modu
    - 'p' Tuşu → Settings paneli
    - Settings paneli → Per-hand bindings, profile, and theme controls

3️⃣  Ses Komutları (Türkçe):
    - "Ekran görüntüsü al"
    - "Ses devre dışı"

📚 Daha Fazla Bilgi:
    README.md ve QUICKSTART.md dosyalarını oku

🆘 Sorun Yaşıyorsanız:
    1. README.md'de "Yaygın Sorunlar" bölümünü kontrol et
    2. İşık seviyesini kontrol et
    3. Kameranın düzgün bağlandığını kontrol et
    4. İnternet bağlantısını kontrol et (ses için)
    """)

def main():
    """Ana kurulum fonksiyonu"""
    try:
        print("\n" + "🚀 "*20)
        print("Hand Gesture Control System Installer")
        print("🚀 "*20)
        
        # Kontroller
        check_python_version()
        check_dependencies()
        
        # Kurulum
        install_requirements()
        create_directories()
        
        # Test
        if test_installation():
            print_instructions()
            print("\n✨ Kurulum başarıyla tamamlandı! ✨\n")
            return 0
        else:
            print("\n❌ Kurulum test edilirken hata oluştu\n")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Kurulum kullanıcı tarafından iptal edildi")
        return 1
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

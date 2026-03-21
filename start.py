#!/usr/bin/env python3
"""
Hand Gesture Control System - Başlangıç Scripti
Projenin yapısını açıklar ve rehberlik sağlar
"""

import os
import sys

def print_banner():
    """Başlık yazdır"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║      🎯 Hand Gesture Control System v1.0                 ║
    ║                                                           ║
    ║      El İzleme, Hareket Tanıma & Ses Komutu             ║
    ║                                                           ║
    ║      Profesyonel Etkileşimli Uygulaması                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Ana menüyü göster"""
    menu = """
    📋 ANA MENU
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    1️⃣  🚀 KURULUM VE BAŞLANGIC
        - Bağımlılıkları kur
        - Ortamı hazırla

    2️⃣  ▶️  UYGULAMAYI ÇALIŞTIR
        - Ana el izleme uygulaması
        - Gerçek zamanlı etkileşim

    3️⃣  🧪 TEST VE DOĞRULAMA
        - Sistem testlerini çalıştır
        - Performans ölçümü

    4️⃣  📚 DOKÜMANTASYON
        - README.md (Detaylı)
        - QUICKSTART.md (Hızlı başlangıç)

    5️⃣  🎨 DEMO VE ÖRNEKLERİ
        - Gelişmiş özellikler
        - Hareket sekvansları

    6️⃣  ⚙️  AYARLAR VE KONFİGURASYON
        - Settings panelini aç
        - Profilleri ve komut eşlemesini yönet

    7️⃣  🧹 TEMIZLIK VE MAİNTENANS
        - Geçici dosyaları sil
        - Cache'i temizle

    8️⃣  ℹ️  PROJE YAPISI VE BİLGİSİ
        - Dosya açıklamaları
        - API referansı

    0️⃣  ❌ ÇIKIŞ
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    print(menu)

def option_1_setup():
    """Kurulum"""
    print("\n🔧 KURULUM BAŞLANIYOR...\n")
    os.system("python install.py")

def option_2_run():
    """Uygulamayı çalıştır"""
    print("\n▶️  UYGULAMA BAŞLANIYOR...\n")
    os.system("python launcher.py")

def option_3_test():
    """Test çalıştır"""
    print("\n🧪 TEST SUITE BAŞLANIYOR...\n")
    os.system("python test.py")

def option_4_docs():
    """Dokümantasyon menüsü"""
    print("\n📚 DOKÜMANTASYON\n")
    
    docs_menu = """
    1. README.md (Detaylı dokümantasyon)
    2. QUICKSTART.md (Hızlı başlangıç)
    3. Settings Panel (Ayarlar)
    
    Seç (1-3, 0: Geri): """
    
    choice = input(docs_menu).strip()
    
    docs = {
        '1': 'README.md',
        '2': 'QUICKSTART.md',
    }
    
    if choice in docs:
        filename = docs[choice]
        if os.path.exists(filename):
            os.system(f"cat {filename} | less" if sys.platform != "win32" else f"more {filename}")
        else:
            print(f"❌ {filename} bulunamadı")
    elif choice == '3':
        os.system("python launcher.py --settings-panel")

def option_5_demo():
    """Demo çalıştır"""
    print("\n🎨 DEMO VE ÖRNEKLERİ\n")
    
    demo_menu = """
    1. Gelişmiş Hareket Tanıma Demo
    2. Temel Etkileşim Örnekleri
    
    Seç (1-2, 0: Geri): """
    
    choice = input(demo_menu).strip()
    
    if choice == '1':
        print("\n🎬 Gelişmiş Demo başlatılıyor...\n")
        os.system("python advanced_demo.py")
    elif choice == '2':
        print("\n💡 Temel örnekler hakkında:\n")
        print("""
        Temel etkileşim örneği main.py'de bulunmaktadır.

        Ayrıca şu işlemleri yapabilirsiniz:
        - İşaret parmağını kullanarak pointer oluştur
        - Tutma hareketi ile nesneleri sürükle
        - Ses modu ile komut ver
        - Settings panelinden tüm ayarları yönet

        Daha fazla bilgi için QUICKSTART.md'i okuyun.
        """)

def option_6_config():
    """Konfigürasyon"""
    print("\n⚙️  KONFIGÜRASYON\n")
    
    config_menu = """
    Ayarlanabilir Parametreler:
    
    Settings panelinde:
    - Kamera ayarları
    - El izleme ve hareket eşlemesi
    - Mouse yönü, gain, smoothing
    - UI ve performans ayarları
    - Voice ve AI seçenekleri

    Açmak için: python launcher.py --settings-panel
    """
    print(config_menu)

def option_7_clean():
    """Temizle"""
    print("\n🧹 TEMİZLİK BAŞLANIYOR...\n")
    
    import subprocess
    try:
        subprocess.run(["make", "clean"], check=True)
        print("✅ Temizlik tamamlandı")
    except:
        # Alternatif yöntem
        import shutil
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                shutil.rmtree(os.path.join(root, '__pycache__'))
            if '.DS_Store' in files:
                os.remove(os.path.join(root, '.DS_Store'))
        print("✅ Geçici dosyalar silindi")

def option_8_structure():
    """Proje yapısı"""
    print("\n📁 PROJE YAPISI VE BİLGİSİ\n")
    
    structure = """
    ╔════════════════════════════════════════════════════════════╗
    ║              PROJE DOSYA YAPISI                            ║
    ╚════════════════════════════════════════════════════════════╝
    
    📂 agent/
    ├── 📄 main.py                  (Ana uygulama)
    │   └─ GestureControlApp sınıfı
    │   └─ Ekran, ses ve hareket yönetimi
    ├── 📄 launcher.py              (Platforma göre giriş noktası)
    │   └─ macOS menü çubuğu / direkt uygulama seçimi
    │
    ├── 📄 hand_tracker.py           (El izleme sistemi)
    │   └─ HandTracker sınıfı
    │   └─ Hareket tanıma algoritmaları
    │   └─ MediaPipe Hands entegrasyonu
    │
    ├── 📄 interaction_system.py     (Nesne etkileşimi)
    │   └─ InteractiveObject sınıfı
    │   └─ InteractionManager sınıfı
    │   └─ DashboardBuilder sınıfı
    │
    ├── 📄 voice_system.py           (Ses ve dikte)
    │   └─ VoiceCommandEngine sınıfı
    │   └─ Ses tanıma ve TTS
    │
    ├── 📄 advanced_features.py      (İleri özellikler)
    │   └─ AdvancedGestureRecognizer
    │   └─ HandMotionTracker
    │   └─ MultiHandAnalyzer
    │   └─ Hareket sekvansları
    │
    ├── 📄 advanced_demo.py          (Demo uygulaması)
    │   └─ Gelişmiş özellikler gösterimi
    │
    ├── 📄 settings_panel.py         (Detaylı ayarlar paneli)
    │   └─ Profil yönetimi
    │   └─ Global ve el bazlı gesture/action eşlemesi
    │   └─ Tema, UI ve performans ayarları
    ├── 📄 settings_manager.py       (Kalıcı ayarlar deposu)
    │   └─ JSON profil sistemi
    │   └─ Per-hand override desteği
    │
    ├── 📄 install.py                (Kurulum scripti)
    │   └─ Bağımlılık kurma
    │   └─ Ortam hazırlama
    │
    ├── 📄 runtime_paths.py          (Kullanıcı verisi yolları)
    │   └─ Kalibrasyon, log ve ekran görüntüleri
    │
    ├── 📄 test.py                   (Test scripti)
    │   └─ Sistem testleri
    │   └─ Performans ölçümü
    │
    ├── 📖 README.md                 (Detaylı dokümantasyon)
    ├── 📖 QUICKSTART.md             (Hızlı başlangıç)
    ├── 📋 requirements.txt           (Python paketleri)
    ├── 📝 Makefile                  (Make komutları)
    └── 🎬 start.py                  (Bu script)
    
    ╔════════════════════════════════════════════════════════════╗
    ║              TEMEL SINIFLAR VE YÖNTEMLERİ                  ║
    ╚════════════════════════════════════════════════════════════╝
    
    🎯 HandTracker (hand_tracker.py)
    ├─ process_frame(frame) → List[HandData]
    ├─ apply_calibration(pinch, release, size)
    ├─ detect_swipe(hand_idx=0) → str
    ├─ draw_hand_skeleton(frame, hand_data)
    └─ HandData.velocity_vector

    🎯 InteractionManager (interaction_system.py)
    ├─ add_object(obj) → None
    ├─ add_draggable_widget(x, y, w, h, label, callback=None)
    ├─ check_interactions(pointer, clicked, velocity=(0, 0))
    └─ draw(frame)
    
    🎯 VoiceCommandEngine (voice_system.py)
    ├─ listen_once() → None
    ├─ create_command(keywords, action) → dict
    ├─ create_voice_command(command, action) → dict
    ├─ match_command(text, commands) → dict
    └─ speak(text) → None
    
    ╔════════════════════════════════════════════════════════════╗
    ║              HAREKET TÜRLERİ (GestureType)                 ║
    ╚════════════════════════════════════════════════════════════╝
    
    🖐️  POINT           - İşaret parmağı
    ✊ GRAB            - Tutma hareketi
    ✌️  PEACE           - Peace işareti
    👍 THUMBS_UP      - Başparmak yukarı
    👎 THUMBS_DOWN    - Başparmak aşağı
    👌 OK             - OK işareti
    ✋ PALM_OPEN      - El açık
    🎤 VOICE_MODE     - Ses modu
    
    ╔════════════════════════════════════════════════════════════╗
    ║              ÇOKLU DOSYA ARKİTEKTÜRÜ                       ║
    ╚════════════════════════════════════════════════════════════╝
    
    Olay Akışı (Event Flow):
    
    1. Kameradan Frame
         ↓
    2. HandTracker → El algılama
         ↓
    3. Hareket Tanıma
         ↓
    4. InteractionManager → Nesnelere tıklama/sürükleme
         ↓
    5. VoiceEngine → Ses komutları (hareket bazlı)
         ↓
    6. Render → Ekrana çizme
    
    Thread Yapısı:
    - Main Thread: Kamera + rendering
    - Voice Thread: Ses dinleme (arka planda)
    
    ╔════════════════════════════════════════════════════════════╗
    ║              ÖNEMLİ DEĞİŞKENLER                            ║
    ╚════════════════════════════════════════════════════════════╝
    
settings_panel.py'de:
• Kamera çözünürlüğü
• El izleme hassasiyeti
• Voice dili: 'tr-TR' (Türkçe)
• Mouse yönü, gain ve smoothing
• Her el için ayrı komut eşleme
• Midnight / dark / light tema seçenekleri
    
    main.py'de:
    • self.pointer_position: Fare imleçi konumu
    • self.grab_active: Tutma hareketi durumu
    • self.voice_active: Ses modu durumu
    """
    
    print(structure)

def main():
    """Ana fonksiyon"""
    while True:
        try:
            print_banner()
            print_menu()
            
            choice = input("Seçim yap (0-8): ").strip()
            
            if choice == '0':
                print("\n👋 Güle güle!")
                sys.exit(0)
            elif choice == '1':
                option_1_setup()
            elif choice == '2':
                option_2_run()
            elif choice == '3':
                option_3_test()
            elif choice == '4':
                option_4_docs()
            elif choice == '5':
                option_5_demo()
            elif choice == '6':
                option_6_config()
            elif choice == '7':
                option_7_clean()
            elif choice == '8':
                option_8_structure()
            else:
                print("\n❌ Geçersiz seçim. Lütfen 0-8 arasında bir sayı gir.")
            
            if choice != '0':
                input("\n⏎ Devam etmek için Enter tuşuna bas...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Program kullanıcı tarafından durduruldu")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Hata: {e}")
            input("⏎ Devam etmek için Enter tuşuna bas...")


if __name__ == "__main__":
    main()

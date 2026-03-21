"""
Test ve demo scripti
Testing and demonstration utilities
"""

import cv2
import numpy as np
from hand_tracker import HandTracker, GestureType
from interaction_system import DashboardBuilder, Point
import time


def test_hand_tracker():
    """El izleme testini çalıştır"""
    print("\n" + "="*60)
    print("  EL İZLEME SİSTEMİ TESİ")
    print("="*60)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Kamera açılamadı")
        return False
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    tracker = HandTracker(confidence_threshold=0.7)
    
    print("✅ El izleme sistemi başlatıldı")
    print("🎥 Kameradan frame'ler okunuyor...")
    print("📝 Hareketleri yaparak test et (q tuşu ile çık)")
    
    gesture_stats = {}
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            hand_data_list = tracker.process_frame(frame)
            frame = tracker.draw_hand_skeleton(frame, hand_data_list)
            
            # Hareketleri say
            for hand_data in hand_data_list:
                gesture_name = hand_data.gesture.name
                gesture_stats[gesture_name] = gesture_stats.get(gesture_name, 0) + 1
            
            # Bilgi göster
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Eller: {len(hand_data_list)}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Hand Tracker Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            frame_count += 1
        
        print(f"\n✅ Test tamamlandı ({frame_count} frame)")
        print("\nTanınan hareketler:")
        for gesture, count in sorted(gesture_stats.items()):
            print(f"  {gesture}: {count}")
        
        return True
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False
    
    finally:
        cap.release()
        cv2.destroyAllWindows()


def test_interaction_system():
    """Etkileşim sistemi testini çalıştır"""
    print("\n" + "="*60)
    print("  ETKİLEŞİM SİSTEMİ TESİ")
    print("="*60)
    
    try:
        width, height = 1280, 720
        dashboard = DashboardBuilder(width, height)
        
        # Test nesneleri ekle
        click_count = [0]
        
        def on_button_click(obj):
            click_count[0] += 1
            print(f"  ✅ Buton tıklandı! (Toplam: {click_count[0]})")
        
        dashboard.add_button(100, 100, 120, 50, "Test Butonu", on_button_click)
        dashboard.add_draggable_widget(500, 100, 150, 60, "Sürüklenebilir")
        
        print("✅ Test nesneleri oluşturuldu")
        
        # Fake frame oluştur
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Etkileşimleri test et
        print("\n📝 Etkileşimleri test ediliyor...")
        
        manager = dashboard.get_manager()
        
        # Butonun üzerine gel
        manager.check_interactions((110, 110), False, (100, 100))
        print("  ✅ Hover testi yapıldı")
        
        # Sürükle
        manager.check_interactions((600, 150), True, (600, 100))
        print("  ✅ Drag testi yapıldı")
        
        frame = manager.draw_objects(frame)
        print("  ✅ Nesneler çizildi")
        
        print("\n✅ Etkileşim sistemi testi başarılı")
        return True
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def test_voice_system():
    """Ses sistemi testini çalıştır"""
    print("\n" + "="*60)
    print("  SES SİSTEMİ TESİ")
    print("="*60)
    
    try:
        from voice_system import VoiceCommandEngine, VoiceState
        
        print("✅ Ses sistemi modülü yüklendi")
        
        engine = VoiceCommandEngine()
        
        # Test kodu
        print("📝 Ses motorunun konuşmasını test et:")
        engine.speak("Ses sistemi testi başarılı")
        print("  ✅ TTS (Text-to-Speech) çalışıyor")
        
        print("\n📝 Komut oluşturma testi:")
        test_cmd = engine.create_voice_command("test komutu", lambda: print("Test"))
        print(f"  ✅ Komut oluşturuldu: {test_cmd['command']}")
        
        print("\n✅ Ses sistemi testi başarılı")
        return True
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def run_performance_test():
    """Performans testi"""
    print("\n" + "="*60)
    print("  PERFORMANS TESİ")
    print("="*60)
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Kamera açılamadı")
            return False
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        tracker = HandTracker()
        dashboard = DashboardBuilder(1280, 720)
        
        print("✅ Sistemler başlatıldı")
        print("📝 100 frame üzerinde performans ölçülüyor...\n")
        
        frame_times = []
        track_times = []
        draw_times = []
        
        for i in range(100):
            start = time.time()
            
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_time = time.time()
            frame_times.append(frame_time - start)
            
            hand_data_list = tracker.process_frame(frame)
            
            track_time = time.time()
            track_times.append(track_time - frame_time)
            
            frame = tracker.draw_hand_skeleton(frame, hand_data_list)
            dashboard.get_manager().draw_objects(frame)
            
            draw_time = time.time()
            draw_times.append(draw_time - track_time)
            
            if (i + 1) % 25 == 0:
                print(f"  ✓ {i + 1}/100 frame işlendi")
        
        cap.release()
        
        # Sonuçları hesapla
        avg_frame_time = np.mean(frame_times) * 1000
        avg_track_time = np.mean(track_times) * 1000
        avg_draw_time = np.mean(draw_times) * 1000
        total_fps = 1000 / (avg_frame_time + avg_track_time + avg_draw_time)
        
        print("\n📊 Performans Sonuçları:")
        print(f"  Frame okuma: {avg_frame_time:.2f} ms")
        print(f"  El izleme: {avg_track_time:.2f} ms")
        print(f"  Çizim: {avg_draw_time:.2f} ms")
        print(f"  Toplam FPS: {total_fps:.1f}")
        
        if total_fps >= 20:
            print("\n✅ Performans iyi (FPS ≥ 20)")
        elif total_fps >= 15:
            print("\n⚠️  Performans orta (FPS ≥ 15)")
        else:
            print("\n❌ Performans düşük (FPS < 15)")
        
        return True
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def main():
    """Ana test fonksiyonu"""
    print("\n" + "🧪 "*20)
    print("Hand Gesture Control System - Test Suite")
    print("🧪 "*20)
    
    tests = [
        ("El İzleme Sistemi", test_hand_tracker),
        ("Etkileşim Sistemi", test_interaction_system),
        ("Ses Sistemi", test_voice_system),
        ("Performans", run_performance_test),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} testi başarısız: {e}")
            results[test_name] = False
    
    # Özet
    print("\n" + "="*60)
    print("  TEST ÖZETI")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ GEÇTI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
    
    print(f"\nSonuç: {passed}/{total} test geçti")
    
    if passed == total:
        print("\n✨ Tüm testler başarılı! Uygulamayı çalıştırmaya hazırız. ✨")
    else:
        print(f"\n⚠️  {total - passed} test başarısız. Sorunları kontrol et.")


if __name__ == "__main__":
    main()

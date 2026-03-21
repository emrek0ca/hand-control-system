"""
Örnek Uygulama - Advanced Features Demonstrasyonu
Example Application - Advanced Features Demonstration
"""

from main import GestureControlApp
from advanced_features import (
    AdvancedGestureRecognizer,
    HandMotionTracker,
    MultiHandAnalyzer,
    GestureSequence
)
from hand_tracker import GestureType
import cv2


class AdvancedGestureApp(GestureControlApp):
    """Gelişmiş özellikleri kullanan uygulama"""
    
    def __init__(self, camera_id: int = 0):
        super().__init__(camera_id)
        
        # Gelişmiş hareket tanıyıcı
        self.gesture_recognizer = AdvancedGestureRecognizer()
        
        # El hareket izleyici
        self.motion_tracker = HandMotionTracker()
        
        # Kustom hareketler ekle
        self._setup_advanced_gestures()
        
        print("✅ Gelişmiş özellikler etkinleştirildi")
    
    def _setup_advanced_gestures(self) -> None:
        """Kustom hareket sekvansları kur"""
        
        # Sekvans 1: Peace → OK → Peace (3 hareketi art arda)
        self.gesture_recognizer.add_gesture_sequence(
            GestureSequence(
                sequence=[GestureType.PEACE, GestureType.OK, GestureType.PEACE],
                action=self._on_triple_gesture,
                timeout=3.0,
                name="Triple Gesture"
            )
        )
        
        # Sekvans 2: Point → Grab → Point (Tıklama benzeri)
        self.gesture_recognizer.add_gesture_sequence(
            GestureSequence(
                sequence=[GestureType.POINT, GestureType.GRAB],
                action=self._on_point_grab,
                timeout=1.0,
                name="Point and Grab"
            )
        )
    
    def _on_triple_gesture(self) -> None:
        """Triple hareket algılandı"""
        print("🎉 Triple Gesture Algılandı!")
        self.voice_engine.speak("Triple hareket başarılı")
        self.stats['voice_commands_executed'] += 1
    
    def _on_point_grab(self) -> None:
        """Point + Grab kombinasyonu"""
        print("✋ Point and Grab Kombinasyonu Algılandı!")
        self.voice_engine.speak("Tıklama hareketi tanındı")
    
    def process_frame(self, frame) -> None:
        """Frame'i işle (overrides parent method)"""
        
        # Parent method'u çalıştır
        frame = super().process_frame(frame)
        
        # El hareketini analiz et
        if self.prev_hand_data:
            for hand_data in [self.prev_hand_data]:  # Son el verisini kullan
                motion_info = self.motion_tracker.update_position(
                    hand_data.center[0], hand_data.center[1], 
                    cv2.getTickCount() / cv2.getTickFrequency()
                )
                
                # Hareket bilgileri
                if motion_info['speed'] > 5:
                    direction = self.motion_tracker.get_movement_direction()
                    cv2.putText(frame, f"Yön: {direction}", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Sekvans kontrol
                matched = self.gesture_recognizer.update_gesture(
                    hand_data.gesture,
                    cv2.getTickCount() / cv2.getTickFrequency()
                )
                
                if matched:
                    print(f"✅ Sekvans Bulundu: {matched.name}")
                    matched.action()
        
        return frame


def run_demo():
    """Demo'yu çalıştır"""
    print("\n" + "="*60)
    print("  Gelişmiş Hareket Tanıma Demo")
    print("="*60)
    print("""
Deneyebileceğiniz Özellikler:

1. HAREKET SEKVANSLARı:
   - Peace → OK → Peace (Üçlü hareket)
   - Point → Grab (Tıklama benzeri)

2. HAREKET ANALİZİ:
   - Hareketin yönü gösterilecek
   - Hız ölçülecek
   
3. ÇOK ELLİ ANALİZ:
   - İki el arasındaki mesafe
   - El etkileşimi tipleri

4. KUSTOM KOMBİNASYONLAR:
   - Yeni hareketler öğrenin
   - Sekvansları kombinle

Kontroller:
- 'q': Çıkış
- 'd': Debug toggle
- 's': Ekran görüntüsü
    """)
    
    try:
        app = AdvancedGestureApp(camera_id=0)
        app.run()
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()

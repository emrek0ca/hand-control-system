"""
Ana uygulama - Gesture-based Hand Tracking Interface
Application: Neural Network Hand Gesture Control System
"""

import cv2
import numpy as np
from hand_tracker import HandTracker, GestureType, GestureState
from interaction_system import DashboardBuilder, Point
from voice_system import VoiceCommandEngine, KeyboardSimulator, VoiceState
from system_control import SystemController
from typing import Optional
import sys


class GestureControlApp:
    """Ana uygulama sınıfı"""
    
    def __init__(self, camera_id: int = 0, headless: bool = False):
        """
        Uygulamayı başlat
        
        Args:
            camera_id: Kamera ID'si
            headless: Eğer True ise pencere açılmaz (Background mode)
        """
        self.headless = headless
        if self.headless:
            print("--- PROFESSIONAL MODE (Headless) ---")
            print("Pencere açılmayacak. Çıkış için 'Ctrl+C' kullanın.")
            
        # Kamera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("Kamera açılamadı")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # El izleme
        self.hand_tracker = HandTracker(confidence_threshold=0.7)
        
        # Sistem Kontrolcüsü
        self.system_controller = SystemController()
        self.system_control_active = True  # Varsayılan olarak sistem kontrolü aktif
        
        # Arayüz ve nesneler
        self.dashboard = DashboardBuilder(self.width, self.height)
        self._setup_dashboard()
        
        # Ses sistemi
        self.voice_engine = VoiceCommandEngine(
            on_result=self._on_voice_result,
            on_state_change=self._on_voice_state_change
        )
        self.voice_active = False
        self.voice_commands = self._setup_voice_commands()
        
        # Durum izleme
        self.prev_hand_data = None
        self.pointer_position = (self.width // 2, self.height // 2)
        self.prev_pointer_position = self.pointer_position
        self.grab_active = False
        self.running = True
        self.show_debug = True
        self.gesture_history = []
        self.fps = 0
        self.frame_count = 0
        self.last_gesture = GestureType.NONE
        
        # İstatistikler
        self.stats = {
            'frames_processed': 0,
            'gestures_detected': {},
            'objects_clicked': 0,
            'voice_commands_executed': 0,
        }
    
    def _setup_dashboard(self) -> None:
        """Kontrol panelini kur"""
        margin = 10
        btn_width = 120
        btn_height = 50
        
        # Üst satır - Kontrol butonları
        def callback_clear():
            self.gesture_history.clear()
            print("Hareket geçmişi temizlendi")
        
        def callback_toggle_debug():
            self.show_debug = not self.show_debug
            print(f"Debug: {self.show_debug}")
        
        def callback_voice_toggle():
            if self.voice_active:
                self.voice_engine.stop_listening()
                self.voice_active = False
            else:
                self.voice_engine.start_listening()
                self.voice_active = True
        
        self.dashboard.add_button(
            margin, margin,
            btn_width, btn_height,
            "Temizle",
            callback_clear,
            (100, 100, 200)
        )
        
        self.dashboard.add_button(
            margin * 2 + btn_width, margin,
            btn_width, btn_height,
            "Debug",
            callback_toggle_debug,
            (150, 100, 200)
        )
        
        self.dashboard.add_button(
            margin * 3 + btn_width * 2, margin,
            btn_width, btn_height,
            "Ses On/Off",
            callback_voice_toggle,
            (100, 200, 100)
        )
        
        # Sürüklenebilir widget'ler
        self.dashboard.add_draggable_widget(
            self.width - 200, margin,
            180, 60,
            "Widget 1",
            (100, 200, 150)
        )
        
        self.dashboard.add_draggable_widget(
            self.width - 200, margin * 2 + 60,
            180, 60,
            "Widget 2",
            (150, 100, 200)
        )
    
    def _setup_voice_commands(self) -> list:
        """Ses komutlarını kur"""
        commands = [
            self.voice_engine.create_voice_command(
                "ekran görüntüsü al",
                self._screenshot_action
            ),
            self.voice_engine.create_voice_command(
                "ses devre dışı",
                lambda: self.voice_engine.stop_listening()
            ),
        ]
        return commands
    
    def _screenshot_action(self) -> None:
        """Ekran görüntüsü al"""
        filename = f"screenshot_{self.frame_count}.png"
        cv2.imwrite(filename, self.current_frame)
        print(f"Ekran görüntüsü kaydedildi: {filename}")
        self.voice_engine.speak(f"Ekran görüntüsü kaydedildi")
    
    def _on_voice_result(self, text: str) -> None:
        """Ses tanıma sonucu"""
        print(f"Tanınan metin: {text}")
        
        # Komut eşleştir
        matched_cmd = self.voice_engine.match_voice_command(text, self.voice_commands)
        if matched_cmd:
            print(f"Komut eşleştirildi: {matched_cmd['command']}")
            matched_cmd['action']()
            self.stats['voice_commands_executed'] += 1
        
        # Dikte olarak yazı
        print(f"Yazılacak metin: {text}")
        # KeyboardSimulator.type_text(text)  # İsteğe bağlı: doğrudan yazı
    
    def _on_voice_state_change(self, state: VoiceState) -> None:
        """Ses durumu değiştiğinde"""
        print(f"Ses durumu: {state.name}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Frame'i işle
        
        Args:
            frame: Kamera frame'i
            
        Returns:
            İşlenmiş frame
        """
        self.current_frame = frame.copy()
        
        # El verilerini al
        hand_data_list = self.hand_tracker.process_frame(frame)
        
        if not self.headless:
            # El iskeletini çiz
            frame = self.hand_tracker.draw_hand_skeleton(frame, hand_data_list)
        
        # Etkileşimleri işle
        if hand_data_list:
            for hand_data in hand_data_list:
                # Parmak pozisyonlarını al
                finger_positions = self.hand_tracker.get_finger_positions(
                    hand_data, frame.shape
                )
                
                # İşaret parmağının pozisyonunu kullan (pointer)
                self.pointer_position = finger_positions['index']
                
                # Hareket türünü kontrol et
                gesture = hand_data.gesture
                
                # Tutma hareketi -> grab aktif
                prev_grab = self.grab_active
                self.grab_active = (gesture == GestureType.GRAB)
                
                # Etkileşimleri kontrol et (UI)
                if not self.headless:
                    self.dashboard.get_manager().check_interactions(
                        self.pointer_position,
                        self.grab_active,
                        self.prev_pointer_position
                    )
                
                # --- Sistem Kontrolü ---
                if self.system_control_active:
                    # Normalize koordinatlar (0-1)
                    norm_x = self.pointer_position[0] / self.width
                    norm_y = self.pointer_position[1] / self.height
                    
                    # FSM State Driven Control
                    # We utilize the state calculated by GestureEngine for stability
                    state = getattr(hand_data, 'state', GestureState.IDLE)
                    velocity = getattr(hand_data, 'velocity', 0.0)
                    
                    # Pointer is always moving unless explicitly invalid
                    self.system_controller.move_mouse(norm_x, norm_y)
                    
                    if state == GestureState.CLICKED:
                        # Click state (Active)
                        self.system_controller.click('left')
                        
                    elif state == GestureState.RIGHT_CLICK:
                        # Right Click (Middle Pinch)
                        self.system_controller.click('right')
                        
                    elif state == GestureState.GRABBING:
                        # Dragging
                        self.system_controller.drag_mouse(norm_x, norm_y)
                        
                    elif state == GestureState.SCROLLING:
                        # Scroll Logic
                        # Use Y position change relative to center or velocity
                        # For simplicity, if hand height is above/below center? 
                        # Better: Use relative movement from when scrolling started (advanced)
                        # Simple version: Move hand Up/Down to scroll
                        
                        # Use norm_y to drive scroll speed. 
                        # Center (0.5) = No scroll. < 0.4 = Up, > 0.6 = Down
                        threshold = 0.1
                        if norm_y < (0.5 - threshold):
                            self.system_controller.scroll(1)
                        elif norm_y > (0.5 + threshold):
                            self.system_controller.scroll(-1)
                        
                        # Alternatively utilize scroll_y delta from HandData if available
                        # But simple absolute position zone is easier to control for now.
                # -----------------------
                
                # İstatistikleri güncelle
                gesture_name = gesture.name
                if gesture_name not in self.stats['gestures_detected']:
                    self.stats['gestures_detected'][gesture_name] = 0
                self.stats['gestures_detected'][gesture_name] += 1
                
                # Ses modu
                if gesture == GestureType.VOICE_MODE and not self.voice_active:
                    self.voice_engine.start_listening()
                    self.voice_active = True
                    if not self.headless: print("Ses modu aktivlendi")
                elif gesture != GestureType.VOICE_MODE and self.voice_active:
                    self.voice_engine.stop_listening()
                    self.voice_active = False
        
        if not self.headless:
            # Pointer'ı çiz
            cv2.circle(frame, self.pointer_position, 10, (0, 255, 255), 2)
            cv2.circle(frame, self.pointer_position, 5, (0, 255, 255), -1)
            
            # Nesneleri çiz
            frame = self.dashboard.get_manager().draw_objects(frame)
            
            # Ses durumunu göster
            voice_status = "LISTENING" if self.voice_active else "IDLE"
            color = (0, 255, 0) if self.voice_active else (100, 100, 100)
            cv2.putText(frame, f"Voice: {voice_status}", (10, self.height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                   
            # Sistem Kontrol Durumu
            sys_status = "SYSTEM CONTROL: ON" if self.system_control_active else "SYSTEM CONTROL: OFF"
            sys_color = (0, 255, 255) if self.system_control_active else (0, 0, 255)
            cv2.putText(frame, sys_status, (10, self.height - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, sys_color, 2)
            
            # Debug bilgileri
            if self.show_debug:
                frame = self._draw_debug_info(frame)
        
        self.prev_pointer_position = self.pointer_position
        self.frame_count += 1
        self.stats['frames_processed'] += 1
        
        return frame
    
    def _draw_debug_info(self, frame: np.ndarray) -> np.ndarray:
        """Debug bilgileri çiz"""
        y_offset = 30
        line_height = 25
        
        info_lines = [
            f"FPS: {self.fps:.1f}",
            f"Frame: {self.frame_count}",
            f"Grab Aktif: {self.grab_active}",
            f"Pointer: {self.pointer_position}",
        ]
        
        for i, line in enumerate(info_lines):
            cv2.putText(frame, line, (10, y_offset + i * line_height),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)
        
        # İstatistikler
        stats_text = [
            "=== İstatistikler ===",
            f"Toplam: {self.stats['frames_processed']}",
        ]
        
        y = y_offset + len(info_lines) * line_height + 20
        for i, line in enumerate(stats_text):
            cv2.putText(frame, line, (10, y + i * line_height),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 200, 100), 1)
        
        return frame
    
    def run(self) -> None:
        """Uygulamayı çalıştır"""
        print("Uygulama başlatılıyor...")
        print("Kontroller:")
        print("  - İşaret parmağı: Pointer")
        print("  - Tutma hareketi: Nesneleri sürükle")
        print("  - Tüm parmaklar açık (uzağa): Ses modu")
        print("  - 'q': Çıkış")
        print("  - 'd': Debug toggle")
        
        import time
        fps_counter = 0
        last_time = time.time()
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Frame okunamadı")
                    break
                
                # Frame'i işle
                processed_frame = self.process_frame(frame)
                
                # FPS hesapla
                fps_counter += 1
                current_time = time.time()
                if current_time - last_time >= 1.0:
                    self.fps = fps_counter
                    fps_counter = 0
                    last_time = current_time
                
                # Göster (Sadece headless değilse)
                if not self.headless:
                    cv2.imshow("Hand Gesture Control System", processed_frame)
                    
                    # Tuş kontrolü
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Çıkılıyor...")
                        self.running = False
                    elif key == ord('d'):
                        self.show_debug = not self.show_debug
                    elif key == ord('m'):
                        self.system_control_active = not self.system_control_active
                        print(f"Sistem kontrolü: {self.system_control_active}")
                    elif key == ord('s'):
                        self._screenshot_action()
        
        except KeyboardInterrupt:
            print("Kullanıcı tarafından durduruldu")
        
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Kaynakları temizle"""
        print("Kaynaklar temizleniyor...")
        self.voice_engine.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()
        
        # İstatistikleri yazdır
        print("\n=== Son İstatistikler ===")
        print(f"İşlenen toplam frame: {self.stats['frames_processed']}")
        print(f"Tanınan hareketler: {self.stats['gestures_detected']}")
        print(f"Nesnelere tıklanma: {self.stats['objects_clicked']}")
        print(f"Ses komutları: {self.stats['voice_commands_executed']}")


def main():
    """Ana giriş noktası"""
    import argparse
    parser = argparse.ArgumentParser(description="Hand Gesture Control System")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no window)")
    args = parser.parse_args()

    try:
        app = GestureControlApp(camera_id=0, headless=args.headless)
        app.run()
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

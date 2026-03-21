# 🚀 Hızlı Başlangıç Kılavuzu

## 5 Dakikalık Kurulum

### 1️⃣ Bağımlılıkları Kur
```bash
cd /Users/emrekoca/Desktop/Projeler/agent
python install.py
```

### 2️⃣ Uygulamayı Çalıştır
```bash
python main.py
```

### 3️⃣ Hareketleri Öğren

| Hareket | İşlem | Açıklama |
|---------|-------|----------|
| 🖐️ İşaret Parmağı | Fare imleçi | Ekrana doğru işaret et |
| ✊ Tutma | Sürükleme | Elini yumruğa kapat |
| ✌️ Peace | Çift tıklama | İşaret + orta parmak açık |
| 👍 Başparmak ↑ | Yukarı ok | Başparmağı yukarı kaldır |
| 👎 Başparmak ↓ | Aşağı ok | Başparmağı aşağı indir |
| 👌 OK | Enter tuşu | Başparmak + işaret | 
| ✋ El Açık | Ses modu | Tüm parmakları aç |

## Kullanma Örnekleri

### Örnek 1: Buton Tıklama
```
1. İşaret parmağınızı butona getirin
2. Elleri yumruğa kapatın (GRAB hareketi)
3. 1 saniye bekleyin
4. Elleri açın
```

### Örnek 2: Ses Komutu
```
1. Tüm parmakları açık tutun (VOICE_MODE)
2. Türkçe konuşun: "Ekran görüntüsü al"
3. Sistem tarafından tanınacak
4. Otomatik olarak işlenecek
```

### Örnek 3: Widget Sürükleme
```
1. İşaret parmağını widget'e getirin
2. Elleri yumruğa kapatın
3. Elleri hareket ettirin (sürükleyin)
4. Elleri açın (bırakın)
```

## Sorun Giderme

### "Kamera açılamadı"
```bash
# Kameranın çalışıp çalışmadığını kontrol et
# macOS: System Preferences → Security & Privacy → Camera
# Windows: Settings → Privacy → Camera
```

### "Hareket tanınmıyor"
- ✅ İyi aydınlık ortamda ol
- ✅ Kameraya daha yakın ol (30-50cm)
- ✅ Hareketleri daha belirgin yap

### "Ses tanınmıyor"
- ✅ Mikrofonun seçili olduğunu kontrol et
- ✅ İnternet bağlantısını kontrol et
- ✅ Daha yüksek sesle konuş

## Gelişmiş Özellikler

### Kustom Hareket Ekleme
`hand_tracker.py` dosyasında `_detect_gesture()` metodunu düzenle

### Kustom Ses Komutu
`main.py` dosyasında `_setup_voice_commands()` metoduna ekle

### Debug Modu
Uygulama çalışırken `'d'` tuşuna bas → Debug bilgileri gösterilir

## Dosya Yapısı

```
agent/
├── main.py              ← Ana uygulama
├── hand_tracker.py      ← El izleme
├── interaction_system.py ← Nesnelerle etkileşim
├── voice_system.py      ← Ses ve dikte
├── advanced_features.py ← İleri özellikler
├── config.py            ← Ayarlar
├── install.py           ← Kurulum scripti
├── test.py              ← Test scripti
└── README.md            ← Detaylı dokümantasyon
```

## API Cheat Sheet

### El İzleme
```python
from hand_tracker import HandTracker

tracker = HandTracker()
hand_list = tracker.process_frame(frame)
frame = tracker.draw_hand_skeleton(frame, hand_list)
```

### Nesnelerle Etkileşim
```python
from interaction_system import DashboardBuilder

dashboard = DashboardBuilder(width, height)
dashboard.add_button(x, y, w, h, "Label", callback)
```

### Ses ve Dikte
```python
from voice_system import VoiceCommandEngine

engine = VoiceCommandEngine(on_result=callback)
engine.start_listening()
engine.speak("Merhaba")
```

## Performans İpuçları

| Ayar | Performans | Hassasiyet |
|------|-----------|-----------|
| Çözünürlük ↑ | Düşer ↓ | Artar ↑ |
| Confidence ↑ | Artar ↑ | Düşer ↓ |
| Smoothing ↑ | Artar ↑ | Düşer ↓ |

## Sık Sorulan Sorular

**S: Hangi Python sürümü gerekli?**
C: Python 3.8 veya daha yeni

**S: Offline çalışıyor mu?**
C: El izleme çalışır, ses tanıma internet gerektirir

**S: Kaç elle çalışabilir?**
C: Maksimum 2 elle (ayarlanabilir)

**S: Diğer uygulamalarla entegrasyon yapabilir miyim?**
C: Evet, keyboard simülasyonu kullanarak

**S: FPS kaç olmalı?**
C: 20+ FPS idealdir, 15+ kabul edilebilir

## Yararlı Linkler

- 📖 [MediaPipe Hands Dokümantasyonu](https://mediapipe.dev)
- 🎓 [OpenCV Öğretici](https://opencv.org)
- 🎤 [Speech Recognition Rehberi](https://pypi.org/project/SpeechRecognition/)

## Destek

Problem yaşıyorsanız:
1. README.md'deki "Yaygın Sorunlar" bölümüne bak
2. `python test.py` ile test suite'i çalıştır
3. Console çıktısını kontrol et

---

**Hazırlanma Tarihi**: 14 Ocak 2026
**Versiyon**: 1.0.0
**Durum**: ✅ Üretime Hazır

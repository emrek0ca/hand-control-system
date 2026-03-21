# Hand Gesture Control System - Profesyonel Dokümantasyon

## 📱 Proje Tanımı

**Hand Gesture Control System**, kamera üzerinden elle yapılan hareketleri tanıyarak ekrandaki nesneleri etkileşimsel olarak yönetebileceğiniz, ses komutları işleyebileceğiniz ve parmak hareketleriyle klavye simülasyonu yapabileceğiniz profesyonel bir Python uygulamasıdır.

## ✨ Temel Özellikler

### 1. **El İzleme Sistemi** (Hand Tracking)
- MediaPipe Hands kullanarak gerçek zamanlı el algılaması
- El iskeletini "sinir ağı" benzeri görselleştirme
- İki elle eşzamanlı izleme (sağ ve sol)
- Parmak uçlarının tam koordinat takibi

### 2. **Gelişmiş Hareket Tanıma** (Gesture Recognition)
Aşağıdaki hareketler otomatik olarak tanınır:
- **POINT**: İşaret parmağı uzatılmış (pointer görevinde)
- **GRAB**: Tüm parmaklar kapalı (nesneleri sürükleme)
- **PEACE**: İşaret ve orta parmak açık
- **THUMBS_UP**: Başparmak yukarı
- **THUMBS_DOWN**: Başparmak aşağı
- **PALM_OPEN**: El açık
- **OK**: OK işareti (başparmak + işaret parmağı birleştirilmiş)
- **VOICE_MODE**: Ses modu (tüm parmaklar açık, aralarında mesafe)

### 3. **Nesnelerle Etkileşim Sistemi** (Object Interaction)
- Dinamik buton ve widget oluşturma
- Sürükleme ve bırakma (Drag & Drop) desteği
- Hover (üzerine gelme) efektleri
- Tıklama callback'leri
- Sınır kontrolü (nesneler ekrandan dışına çıkmaz)

### 4. **Ses ve Dikte Sistemi** (Voice & Dictation)
- Gerçek zamanlı ses tanıma (Türkçe destekli)
- Kustom ses komutları
- Metin-konuşma (TTS) motoru
- Otomatik ses seviyeleme

### 5. **Klavye Simülasyonu** (Keyboard Simulation)
Hareket sekvansları tuş basışlarına dönüştürülür:
- İşaret parmağı → Tıklama
- Peace işareti → Çift tıklama
- OK işareti → Enter
- Başparmak yukarı → Yukarı ok tuşu
- Başparmak aşağı → Aşağı ok tuşu

## 🛠 Kurulum

### Gereksinimler
- Python 3.8+
- Macbook/Windows/Linux (kamerası olan)
- Mikrofon (ses komutları için)

### Adım 1: Bağımlılıkları Kur

```bash
pip install -r requirements.txt
```

### Adım 2: Uygulamayı Çalıştır

```bash
python main.py
```

## 📖 Kullanım Rehberi

### Temel Kontroller

| Hareket | İşlem |
|---------|-------|
| **İşaret Parmağı** | Fare imleçi (pointer) |
| **Tutma Hareketi** | Nesneleri sürükle |
| **Ses Modu** | Tüm parmaklar açık → Mikrofon aktif |
| **OK Hareketi** | Enter tuşu benzeri |
| **'q' Tuşu** | Uygulamayı kapat |
| **'d' Tuşu** | Debug bilgilerini aç/kapat |
| **'s' Tuşu** | Ekran görüntüsü al |

### Nesnelerle Etkileşim

1. **Butonlara Tıkla**: İşaret parmağını butona getir, tutma hareketi yap
2. **Widget Sürükle**: Tutma hareketi yap ve harekete devam et
3. **Ses Modu**: Tüm parmakları açık tut → Mikrofon dinlemeye başlar
4. **Komut Ver**: "Ekran görüntüsü al" gibi Türkçe komut söyle

## 🏗 Proje Yapısı

```
agent/
├── requirements.txt          # Python bağımlılıkları
├── main.py                   # Ana uygulama
├── hand_tracker.py           # El izleme motoru
├── interaction_system.py     # Nesne etkileşim sistemi
├── voice_system.py          # Ses ve dikte sistemi
└── README.md                # Bu dosya
```

### Dosya Açıklamaları

#### `hand_tracker.py`
- **HandTracker**: Ana el izleme sınıfı
- **GestureType**: Hareket türleri enum
- **HandData**: El verisi yapısı
- **HandLandmark**: Landmark noktası

Önemli metodlar:
- `process_frame()`: Kareyi işler
- `_detect_gesture()`: Hareketleri tanır
- `draw_hand_skeleton()`: El iskeletini çizer

#### `interaction_system.py`
- **InteractiveObject**: Etkileşimli nesne
- **InteractionManager**: Nesneleri yönetir
- **DashboardBuilder**: UI paneli oluşturur

Önemli metodlar:
- `add_button()`: Buton ekle
- `add_draggable_widget()`: Sürüklenebilir widget ekle
- `check_interactions()`: Etkileşimleri kontrol et

#### `voice_system.py`
- **VoiceCommandEngine**: Ses komutu motoru
- **KeyboardSimulator**: Tuş basışı simülasyonu
- **VoiceState**: Ses durumu

Önemli metodlar:
- `start_listening()`: Dinlemeyi başla
- `match_voice_command()`: Komut eşleştir
- `speak()`: Metni sesle oku

#### `main.py`
- **GestureControlApp**: Ana uygulama sınıfı

## 🧠 Hareket Tanıma Algoritması

Sistem geometrik hesaplamalar kullanarak hareketleri tanır:

```python
# Parmak pozisyonları Y ekseninde karşılaştırılır
# Y < Y_base → Parmak açık
# Y > Y_base → Parmak kapalı

# Mesafeler Öklid formülü kullanılarak hesaplanır
distance = sqrt((x1-x2)² + (y1-y2)² + (z1-z2)²)
```

### Örnek: GRAB Hareketi
```python
if (not thumb_open and not index_open and 
    not middle_open and not ring_open and not pinky_open):
    return GestureType.GRAB
```

## 🔧 Kustom Hareket Ekleme

Yeni hareket eklemek için `hand_tracker.py`'da `_detect_gesture()` metodunu düzenle:

```python
def _detect_gesture(self, landmarks: List[HandLandmark]) -> GestureType:
    # ... mevcut kodlar ...
    
    # Yeni hareket: İndeks ve orta parmak yapışık
    if (abs(landmarks[self.INDEX_TIP].x - landmarks[self.MIDDLE_TIP].x) < 0.05 and
        not thumb_open and not ring_open and not pinky_open):
        return GestureType.CUSTOM_GESTURE  # Yeni hareket türü ekle
    
    return GestureType.NONE
```

## 🎙️ Kustom Ses Komutu Ekleme

`main.py`'da `_setup_voice_commands()` metoduna ekle:

```python
self.voice_engine.create_voice_command(
    "ekran temizle",
    self._custom_action
)
```

## 📊 İstatistikler ve Debug

Uygulama otomatik olarak aşağıdaki bilgileri takip eder:
- İşlenen toplam frame sayısı
- Tanınan hareket sayıları
- Nesne tıklama sayısı
- Ses komutu sayısı

Debug modu açıkken (`'d' tuşu`) ekranda gösterilir:
- FPS (Frames Per Second)
- Frame sayısı
- Pointer pozisyonu
- İstatistikler

## 🚀 Performans İpuçları

1. **Kamera çözünürlüğü**: 1280x720 optimal denge sağlar
2. **Confidence threshold**: 0.7 iyi sonuç verir
3. **Smoothing**: 0.5 stabil izleme sağlar
4. **Işık**: İyi aydınlık ortamda daha iyi çalışır

## ⚠️ Yaygın Sorunlar

### Problem: Hareket tanınmıyor
**Çözüm**: 
- Işığı artır
- Eline çok yakınlaşma/uzaklaşma
- Kameraya düzgün yüz at

### Problem: Ses tanınmıyor
**Çözüm**:
- Mikrofonun sistem ayarlarında seçili olduğunu kontrol et
- Daha yüksek ses seviyesinde konuş
- Internet bağlantısını kontrol et (Google STT için)

### Problem: Düşük FPS
**Çözüm**:
- Başka uygulamaları kapat
- Kamera çözünürlüğünü düşür
- Debug modunu kapat

## 📚 API Referansı

### HandTracker

```python
tracker = HandTracker(confidence_threshold=0.7)
hand_data_list = tracker.process_frame(frame)
frame = tracker.draw_hand_skeleton(frame, hand_data_list)
```

### InteractionManager

```python
manager = InteractionManager(width, height)
manager.add_object(interactive_object)
manager.check_interactions(pointer_pos, grab_active)
manager.draw_objects(frame)
```

### VoiceCommandEngine

```python
engine = VoiceCommandEngine(on_result=callback)
engine.start_listening()
text = engine.process_dictation()
engine.speak("Metin")
```

## 🤝 Katkı Yapma

Geliştirmeleri yapmak için:
1. Kodun logikasını anlayın
2. Yeni features'ı test edin
3. Hataları düzeltin

## 📄 Lisans

Bu proje eğitim ve araştırma amaçlıdır.

## 🎓 Teknik Detaylar

### MediaPipe Hands Landmark'ları
- Toplam 21 landmark
- Her landmark X, Y, Z koordinatlarına ve güven skoruna sahip
- Z: Kameradan derinlik (0 = kamera, 1 = uzakta)

### Hareket Tanıma Yöntemi
1. **Landmark Çıkarma**: MediaPipe'tan 21 landmark al
2. **Parmak Durumu**: Her parmak açık/kapalı hesapla
3. **Mesafe Hesaplama**: Parmaklar arasındaki mesafeler ölç
4. **Kural Uygulaması**: Hareket kurallarına uygulamalarını kontrol et

### Etkileşim Pipeline'ı
```
Frame → El İzleme → Hareket Tanıma → Pointer Konumu
                                         ↓
                                    Hover Kontrolü
                                         ↓
                                    Grab Kontrolü
                                         ↓
                                    Drag & Drop
                                         ↓
                                    Render
```

## 🔮 Gelecek Geliştirmeler

- [ ] Multi-user support (birden fazla kullanıcı)
- [ ] Machine Learning tabanlı kustom hareket öğrenme
- [ ] 3D hareket tanıma
- [ ] USB port üzerinden harici cihaz kontrolü
- [ ] Oyun entegrasyonu
- [ ] Web arayüzü

---

**Geliştirme Tarihi**: 14 Ocak 2026
**Versiyon**: 1.0
**Python Sürümü**: 3.8+

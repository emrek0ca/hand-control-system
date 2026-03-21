# 📑 Hand Gesture Control System - İndeks

## 🎯 Projeye Hızlı Erişim

### 🚀 BAŞLAMAK İÇİN (İşlem Sırası)
1. **[setup.sh](setup.sh)** - Otomatik kurulum (1 dakika)
2. **[QUICKSTART.md](QUICKSTART.md)** - Hızlı başlangıç kılavuzu
3. **[main.py](main.py)** - Uygulamayı çalıştır

### 📚 DOKÜMANTASYON (Öncelik Sırasıyla)
1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** ⭐ - Başlamadan önce oku!
2. **[QUICKSTART.md](QUICKSTART.md)** - 5 dakikalık kurulum
3. **[README.md](README.md)** - Detaylı teknik dokümantasyon
4. **[DELIVERY_REPORT.md](DELIVERY_REPORT.md)** - Proje özeti

### 🔧 YAPIAL DOSYALAR
| Dosya | Amaç | Boyut |
|-------|------|-------|
| **main.py** | Ana uygulama | 12 KB |
| **hand_tracker.py** | El izleme motoru | 11 KB |
| **interaction_system.py** | Nesnelerle etkileşim | 8.8 KB |
| **voice_system.py** | Ses sistemi | 7.7 KB |
| **advanced_features.py** | İleri özellikler | 11 KB |
| **config.py** | Konfigürasyon | 2.1 KB |
| **test.py** | Test suite | 8.2 KB |
| **install.py** | Kurulum | 4.8 KB |
| **advanced_demo.py** | Demo uygulaması | 4.2 KB |
| **version.py** | Sürüm bilgisi | 3.2 KB |
| **start.py** | İnteraktif menü | 13 KB |

### ⚙️ KONFİGURASYON & KÜTÜPHANELER
| Dosya | İçerik |
|-------|--------|
| **config.py** | Sistem ayarları |
| **requirements.txt** | Python paketleri |
| **Makefile** | Make komutları |
| **setup.sh** | Bash kurulum scripti |

### 📖 REFERANS & REHBERLER
| Dosya | Içerik |
|-------|--------|
| **README.md** | Detaylı dokümantasyon |
| **QUICKSTART.md** | Hızlı başlangıç |
| **SETUP_GUIDE.md** | Kurulum rehberi |
| **DELIVERY_REPORT.md** | Teslim belgesi |
| **INDEX.md** | Bu dosya |

---

## 🎮 KULLANMI SENARYOLARI

### Senaryo 1: İlk Kez Çalıştırma
```bash
1. ./setup.sh (Otomatik kurulum)
2. python main.py (Uygulamayı başlat)
3. Hareketleri dene (İşaret parmağı, tutma, etc)
```

### Senaryo 2: Sistem Kontrol
```bash
1. python test.py (Sistemi kontrol et)
2. python main.py (Sorunu gözle)
3. README.md'de çözüm ara
```

### Senaryo 3: Gelişmiş Özellikler
```bash
1. python advanced_demo.py (Demosunu gör)
2. advanced_features.py (Kodu inceле)
3. Kendi hareketiyle ekle
```

---

## 📊 HIZLI REFERANS

### Temel Komutlar
```bash
./setup.sh              # Kurulum
python main.py          # Uygulamayı çalıştır
python test.py          # Testleri çalıştır
python start.py         # İnteraktif menü
make clean              # Temizle
```

### Dosya Seçim Kılavuzu
- **Sorununuz varsa** → README.md
- **Başlamak istiyorsanız** → QUICKSTART.md
- **Teknik detaylar** → README.md + advanced_features.py
- **Kurulumda sorun** → SETUP_GUIDE.md
- **Genel bilgi** → DELIVERY_REPORT.md

### Önemli Sınıflar & Metodlar
```python
# El İzleme
HandTracker.process_frame()
HandTracker._detect_gesture()

# Etkileşim
InteractionManager.check_interactions()
InteractionManager.draw_objects()

# Ses
VoiceCommandEngine.start_listening()
VoiceCommandEngine.speak()
```

---

## ✅ KONTROL LİSTESİ

Başlamadan önce kontrol edin:
- [ ] Python 3.8+ yüklü
- [ ] Kamera bağlı
- [ ] İnternet bağlantısı (ses için)
- [ ] Mikrofon bağlı (opsiyonel)

Kurulum sonrası:
- [ ] `./setup.sh` başarılı oldu
- [ ] `python test.py` tüm testleri geçti
- [ ] `python main.py` başladı
- [ ] Hareketler tanınıyor

---

## 🎯 PROJE YAPISI

```
📂 Hand Gesture Control System/
│
├── 📘 BAŞLANGIÇ (Bunu oku)
│   ├── SETUP_GUIDE.md ⭐
│   ├── QUICKSTART.md
│   └── INDEX.md (Bu dosya)
│
├── 🔧 KURULUM
│   ├── setup.sh (Bash script)
│   ├── install.py (Python script)
│   ├── requirements.txt (Paketler)
│   ├── config.py (Ayarlar)
│   └── Makefile (Make komutları)
│
├── 📚 ANA KOD
│   ├── main.py (Ana uygulama)
│   ├── hand_tracker.py (El izleme)
│   ├── interaction_system.py (Etkileşim)
│   ├── voice_system.py (Ses)
│   └── advanced_features.py (İleri)
│
├── 🎬 DEMO & TEST
│   ├── advanced_demo.py (Demo)
│   ├── test.py (Test suite)
│   ├── start.py (İnteraktif menü)
│   └── version.py (Sürüm bilgisi)
│
└── 📖 DOKÜMANTASYON
    ├── README.md (Detaylı)
    ├── QUICKSTART.md (Hızlı)
    ├── SETUP_GUIDE.md (Kurulum)
    ├── DELIVERY_REPORT.md (Özet)
    └── INDEX.md (Bu dosya)
```

---

## 🚀 BASIT BAŞLANGIÇ

### 1 Dakika Kurulum
```bash
cd /Users/emrekoca/Desktop/Projeler/agent
./setup.sh
```

### 30 Saniye Çalıştırma
```bash
python main.py
```

### Hemen Başla
- İşaret parmağını kameraya göster → Pointer
- Yumruk yap → Nesneleri sürükle
- Tüm parmak aç → Ses modu

---

## 📱 SOS: ACİL YARDIM

| Problem | Çözüm |
|---------|-------|
| Kamera açılamıyor | System Settings → Privacy → Camera |
| Python bulunamıyor | `python3 -V` ile kontrol et |
| Kurulum başarısız | `python install.py` dene |
| Hareket tanınmıyor | İşığı artır, hareketleri belirgin yap |
| Ses tanınmıyor | İnternet bağlantısını kontrol et |

---

## 📞 BAŞLICA KAYNAKLAR

- 📖 **Dokümantasyon**: README.md
- 🚀 **Hızlı Başlangıç**: QUICKSTART.md
- ⚙️ **Kurulum**: SETUP_GUIDE.md
- 🎬 **Demo**: python advanced_demo.py
- 🧪 **Test**: python test.py

---

## 🎓 İSTİNAT ŞEYLERİ

1. **İlk Kez mi?** → SETUP_GUIDE.md oku
2. **Hızlı başlamak?** → QUICKSTART.md oku
3. **Teknik detaylar?** → README.md oku
4. **Sorun mu var?** → test.py çalıştır
5. **Daha fazla bilgi?** → DELIVERY_REPORT.md oku

---

**Sürüm**: 1.0.0 | **Tarih**: 14 Ocak 2026 | **Durum**: ✅ Üretime Hazır

🎉 **Başlamaya hazırsan? [SETUP_GUIDE.md](SETUP_GUIDE.md) ile başla!**

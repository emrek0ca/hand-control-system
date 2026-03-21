# 🛠 Hand Control System - SKILLS.md

Bu dosya, bu repoyu geliştiren ve bu proje üzerinde çalışan **Yapay Zeka Ajanları** için tanımlanmış temel yetenekleri (skills) içerir.

## 👁 Görsel Analiz Yeteneği (Vision Skill)
- **Landmark Çıkarma:** Görüntüden 21 el landmark'ını gerçek zamanlı tespit etme.
- **Dinamik Normalizasyon:** Koordinatları ekran çözünürlüğüne ve kullanıcı mesafesine göre optimize etme.
- **İskelet Çizimi:** El yapısını görselleştirerek geri bildirim sağlama.

## 🤝 Hareket Tanıma Yeteneği (Gesture Recognition Skill)
- **FSM Yönetimi:** Elin durumunu (Pinch, Click, Grab) sonlu durum makinesi ile takip etme.
- **Sekvans Analizi:** Ardışık hareketleri (örn: Double Click) tanıma ve tetikleme.
- **Geometrik Kural Motoru:** Parmaklar arası açı ve mesafeye göre yeni hareketler tanımlama.

## 🖥 Sistem Entegrasyonu Yeteneği (System Interaction Skill)
- **Mouse/Keyboard Otomasyonu:** PyAutoGUI üzerinden imleç hareketi ve tuş simülasyonu.
- **Exponential Smoothing:** Hıza duyarlı fiziksel hareket simülasyonu uygulama.
- **Fail-Safe Mekanizması:** Kritik durumlarda sistemi güvenli bir şekilde durdurma.

## 🎙 Sesli Zeka Yeteneği (Voice Intelligence Skill)
- **STT (Speech-to-Text):** Türkçe sesli komutları metne çevirme ve anlamlandırma.
- **TTS (Text-to-Speech):** Kullanıcıya sesli geri bildirim verme.
- **Doğal Dil Eşleştirme:** Anahtar kelimeler üzerinden esnek komut algılama (%70 eşleşme hassasiyeti).

## 📊 Kinematik Analiz Yeteneği (Kinematic Skill)
- **Hız & İvme Takibi:** Elin hareket yönünü (8 yönlü) ve süratini ölçme.
- **Titreme Filtreleme (Jitter Removal):** Küçük kas hareketlerini ve sensor gürültüsünü eleme.
- **Uzamsal İlişki Analizi:** İki el arasındaki mesafeyi ve etkileşimi (alkış vb.) hesaplama.

---

## 🔧 Geliştirici Ajanlar İçin Araç Seti (Agent Tools)
Bu projede çalışan ajanlar aşağıdaki araçları kullanır:
- `hand_tracker.py` -> Core Engine
- `system_control.py` -> Low-level OS API
- `voice_system.py` -> Audio/NLP Pipeline
- `interaction_system.py` -> UI Overlay System
- `settings_manager.py` -> Profile, per-hand binding, and parameter tuning
- `settings_panel.py` -> User-facing configuration panel with themes

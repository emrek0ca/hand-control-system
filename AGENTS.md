# 🤖 Hand Control System - AGENTS.md

## 🎯 Proje Vizyonu & Algoritma Mimarisi
Bu proje, insan-bilgisayar etkileşimini (HCI) bir üst seviyeye taşıyan, düşük gecikmeli ve yüksek hassasiyetli bir **Yapay Zeka Ajanı** altyapısıdır. Sadece koordinat takibi değil, el hareketlerinin niyetini (intent) anlayan bir "Göz" olarak tasarlanmıştır.

### 🧠 Çekirdek Algoritma İşleyişi
Sistem, üç ana katmandan oluşan bir boru hattı (pipeline) kullanır:

1.  **Görsel Algı (Vision Layer):**
    *   **MediaPipe Hands** kullanarak 21 el landmark'ı 30 FPS hızında çıkarılır.
    *   Ham koordinatlar, ekran çözünürlüğüne göre normalize edilir.

2.  **Niyet Analizi (Cognitive Layer - FSM):**
    *   **Sonlu Durum Makinesi (Finite State Machine):** Elin sadece pozisyonunu değil, *durumunu* (IDLE, CLICKED, GRABBING, SCROLLING) takip eder.
    *   **Stabilizasyon Buffer'ı:** Anlık titremeleri (jitter) engellemek için son N frame'in durumunu kontrol eden bir oylama mekanizması çalışır.

3.  **Fiziksel İcra (Execution Layer):**
    *   **Üstel Yumuşatma (Exponential Smoothing):** Yavaş hareketlerde (hassas tıklama) yüksek yumuşatma, hızlı hareketlerde (imleç kaydırma) düşük gecikme uygular.
    *   **Click Freezing:** Tıklama anında imleci 300ms sabitleyerek hedef sapmasını engeller.

---

### 🚀 Pazarda Fark Yaratan "En İyi" Özellikler

1.  **Hibrid Multimodal Kontrol:**
    *   Aynı anda hem el hareketleri (fiziksel kontrol) hem de sesli komutlar (mantıksal kontrol) kullanılabilir. Örneğin: Eliyle dosyayı tutup sesle "Bunu sil" diyebilme potansiyeli.

2.  **Bağlam Duyarlı Hassasiyet (Context-Aware Physics):**
    *   Sıradan sistemlerin aksine, bu ajan elin hızına göre "Hassas Mod" ve "Hızlı Mod" arasında otomatik geçiş yapar. Bu, Photoshop gibi profesyonel araçlarda kullanım imkanı sağlar.

3.  **Düşük Donanım Gereksinimi:**
    *   Ağır derin öğrenme modelleri yerine, geometrik hesaplamalar ve optimize edilmiş FSM kullanarak standart bir web kamerası ve CPU ile çalışır.

4.  **Genişletilebilir Yetenek (Skill) Altyapısı:**
    *   Yeni bir "Yetenek" (örn: alkışla ekranı kilitleme) eklemek, sadece `hand_tracker.py` içindeki kuralları güncellemek kadar basittir.

---

## 🛠 Gelecek Yol Haritası (Agent Roadmap)
- [ ] **LMM Entegrasyonu:** El hareketlerinin neyi hedeflediğini (buton, resim, yazı) anlamak için hafif bir Vision-Language Model entegrasyonu.
- [ ] **Kişisel Kalibrasyon:** Her kullanıcının el boyutuna ve hareket alışkanlığına göre kendini eğiten (Self-Calibration) mekanizma.
- [ ] **3D Uzamsal Kontrol:** Z ekseni derinliğini kullanarak 3D tasarım araçları için kontrol desteği.

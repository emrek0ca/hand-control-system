"""
Konfigürasyon dosyası
Configuration settings for the application
"""

# Kamera ayarları
CAMERA_CONFIG = {
    'width': 1280,
    'height': 720,
    'fps': 30,
    'camera_id': 0,  # 0 = varsayılan kamera
}

# El izleme ayarları
HAND_TRACKING_CONFIG = {
    'confidence_threshold': 0.7,  # Güven eşiği (0-1)
    'max_hands': 2,  # Maksimum el sayısı
    'smoothing': 0.5,  # Yumuşatma faktörü
}

# Hareket tanıma parametreleri
GESTURE_CONFIG = {
    'point_threshold': 0.05,  # İşaret parmağı mesafe eşiği
    'grab_confidence': 0.8,  # Tutma hareketi güven eşiği
    'voice_mode_distance': 0.1,  # Ses modu minimum parmak arası mesafe
}

# UI ayarları
UI_CONFIG = {
    'button_width': 120,
    'button_height': 50,
    'margin': 10,
    'widget_width': 180,
    'widget_height': 60,
}

# Ses ayarları
VOICE_CONFIG = {
    'language': 'tr-TR',  # Türkçe
    'timeout': 5,  # Dinleme timeout
    'tts_rate': 150,  # Konuşma hızı
    'tts_volume': 0.9,  # Ses seviyesi
}

# Görselleştirme ayarları
VISUALIZATION_CONFIG = {
    'skeleton_color': (0, 255, 100),  # El iskeletinin rengi (BGR)
    'point_color': (255, 100, 0),  # Parmak ucu rengi
    'pointer_color': (0, 255, 255),  # Pointer rengi
    'line_thickness': 2,  # İskelet çizgisi kalınlığı
}

# Debug ayarları
DEBUG_CONFIG = {
    'show_fps': True,
    'show_landmarks': True,
    'show_gesture_name': True,
    'show_statistics': True,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
}

# Renk şeması (BGR format)
COLORS = {
    'primary': (50, 150, 255),      # Mavi
    'secondary': (150, 100, 200),   # Mor
    'success': (100, 200, 100),     # Yeşil
    'warning': (100, 200, 200),     # Sarı
    'danger': (100, 100, 200),      # Kırmızı
    'info': (200, 200, 0),          # Cyan
    'neutral': (150, 150, 150),     # Gri
}

# Performans ayarları
PERFORMANCE_CONFIG = {
    'frame_skip': 0,  # Her N frame'i işle (0 = hepsini işle)
    'max_fps': 30,  # Maksimum FPS
    'enable_threading': True,  # Thread kullanma
}

# Yol ve dosya ayarları
PATHS = {
    'screenshots_dir': './screenshots',
    'logs_dir': './logs',
    'models_dir': './models',
}

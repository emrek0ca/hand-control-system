"""
Advanced Features - İleri Özellikler
Gelişmiş hareket kombinasyonları ve özellikleri
"""

import numpy as np
from typing import List, Callable, Optional
from dataclasses import dataclass
from hand_tracker import HandData, GestureType
import time


@dataclass
class GestureSequence:
    """Hareket sekvansı"""
    sequence: List[GestureType]
    action: Callable
    timeout: float = 2.0  # Sekvans tamamlanma süresi
    name: str = ""


class AdvancedGestureRecognizer:
    """Gelişmiş hareket tanıyıcı - Hareket sekvansları ve kombinasyonları"""
    
    def __init__(self):
        self.gesture_history: List[tuple] = []  # (gesture, timestamp)
        self.current_sequence: List[GestureType] = []
        self.registered_sequences: List[GestureSequence] = []
        self.max_history_size = 30
        
    def add_gesture_sequence(self, sequence: GestureSequence) -> None:
        """Yeni hareket sekvansı ekle"""
        self.registered_sequences.append(sequence)
    
    def update_gesture(self, gesture: GestureType, timestamp: float) -> Optional[GestureSequence]:
        """
        Hareketleri güncelle ve sekvans kontrol et
        
        Args:
            gesture: Yeni hareket
            timestamp: Hareketin zamanı
            
        Returns:
            Eşleşen sekvans varsa
        """
        # Eski hareketleri temizle
        current_time = timestamp
        self.gesture_history = [
            (g, t) for g, t in self.gesture_history
            if current_time - t < 3.0  # Son 3 saniye
        ]
        
        # Yeni hareketi ekle
        self.gesture_history.append((gesture, timestamp))
        
        # Sekvansları kontrol et
        for sequence in self.registered_sequences:
            if self._check_sequence_match(sequence):
                self.gesture_history.clear()
                return sequence
        
        return None
    
    def _check_sequence_match(self, sequence: GestureSequence) -> bool:
        """Sekvans eşleşmesini kontrol et"""
        if len(self.gesture_history) < len(sequence.sequence):
            return False
        
        # Son N hareketi kontrol et
        recent_gestures = [g for g, _ in self.gesture_history[-len(sequence.sequence):]]
        
        for i, expected in enumerate(sequence.sequence):
            if recent_gestures[i] != expected:
                return False
        
        return True
    
    def get_gesture_velocity(self) -> float:
        """El hareketin hızını hesapla"""
        if len(self.gesture_history) < 2:
            return 0.0
        
        recent = self.gesture_history[-5:]  # Son 5 hareket
        if len(recent) < 2:
            return 0.0
        
        time_diff = recent[-1][1] - recent[0][1]
        if time_diff == 0:
            return 0.0
        
        gesture_changes = sum(1 for i in range(1, len(recent)) 
                             if recent[i][0] != recent[i-1][0])
        return gesture_changes / time_diff


class HandMotionTracker:
    """El hareket izleyicisi - Konum, hız, ivme takibi"""
    
    def __init__(self, smoothing_factor: float = 0.3):
        self.smoothing_factor = smoothing_factor
        self.prev_position = None
        self.prev_velocity = None
        self.position_history = []
        self.max_history = 20
        
    def update_position(self, x: float, y: float, timestamp: float) -> dict:
        """
        Pozisyonu güncelle ve kinematiği hesapla
        
        Returns:
            Pozisyon, hız, ivme bilgileri
        """
        current_pos = np.array([x, y])
        
        # Hızı hesapla
        if self.prev_position is not None:
            velocity = current_pos - self.prev_position
        else:
            velocity = np.array([0.0, 0.0])
        
        # Hızı yumuşat
        if self.prev_velocity is not None:
            velocity = (velocity * self.smoothing_factor + 
                       self.prev_velocity * (1 - self.smoothing_factor))
        
        # İvmeyi hesapla (hızın değişim hızı)
        if self.prev_velocity is not None:
            acceleration = velocity - self.prev_velocity
        else:
            acceleration = np.array([0.0, 0.0])
        
        # Geçmişe ekle
        self.position_history.append({
            'position': current_pos,
            'velocity': velocity,
            'acceleration': acceleration,
            'timestamp': timestamp
        })
        
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
        
        self.prev_position = current_pos
        self.prev_velocity = velocity
        
        return {
            'position': current_pos,
            'velocity': velocity,
            'speed': np.linalg.norm(velocity),
            'acceleration': acceleration,
            'direction': np.arctan2(velocity[1], velocity[0]) if np.linalg.norm(velocity) > 0 else 0
        }
    
    def is_stationary(self, threshold: float = 0.5) -> bool:
        """El sabit mi?"""
        if not self.position_history:
            return True
        return self.position_history[-1]['speed'] < threshold
    
    def get_movement_direction(self) -> Optional[str]:
        """Hareket yönünü al"""
        if len(self.position_history) < 2:
            return None
        
        velocity = self.position_history[-1]['velocity']
        speed = np.linalg.norm(velocity)
        
        if speed < 0.1:  # Hareketsiz
            return None
        
        angle = np.arctan2(velocity[1], velocity[0])
        
        # Yönü belirle
        if -np.pi/8 <= angle <= np.pi/8:
            return "RIGHT"
        elif np.pi/8 < angle <= 3*np.pi/8:
            return "DOWN-RIGHT"
        elif 3*np.pi/8 < angle <= 5*np.pi/8:
            return "DOWN"
        elif 5*np.pi/8 < angle <= 7*np.pi/8:
            return "DOWN-LEFT"
        elif angle > 7*np.pi/8 or angle <= -7*np.pi/8:
            return "LEFT"
        elif -7*np.pi/8 <= angle < -5*np.pi/8:
            return "UP-LEFT"
        elif -5*np.pi/8 <= angle < -3*np.pi/8:
            return "UP"
        else:  # -3*np.pi/8 <= angle < -np.pi/8
            return "UP-RIGHT"


class MultiHandAnalyzer:
    """Advanced analysis for interaction between two hands."""
    
    def __init__(self):
        self.last_dist = 0
        self.dist_filter = None # Will be initialized on first use
        self.clap_cooldown = 0
        self.prayer_active = False

    def calculate_relative_data(self, hands: List[HandData]) -> dict:
        """Compute filtered distance and relative velocity between two hands."""
        if len(hands) < 2: return {}
        
        h1, h2 = hands[0], hands[1]
        p1, p2 = np.array(h1.center), np.array(h2.center)
        raw_dist = np.linalg.norm(p1 - p2)
        
        # 1. Stabilization Filter for Inter-hand distance
        if self.dist_filter is None:
            self.dist_filter = raw_dist
        else:
            # High smoothing for distance to keep zoom stable
            self.dist_filter = 0.7 * self.dist_filter + 0.3 * raw_dist
            
        dist = self.dist_filter
        
        # 2. Precise Relative velocity (change in filtered distance)
        rel_vel = dist - self.last_dist
        self.last_dist = dist
        
        return {
            'distance': dist,
            'rel_velocity': rel_vel,
            'midpoint': ((p1[0] + p2[0])/2, (p1[1] + p2[1])/2)
        }

    def detect_clap(self, rel_data: dict) -> bool:
        """High relative velocity inwards + small distance = Clap."""
        if not rel_data: return False
        
        now = time.time()
        if now < self.clap_cooldown: return False
        
        # Condition: distance is small and getting smaller very fast
        if rel_data['distance'] < 0.12 and rel_data['rel_velocity'] < -0.08:
            self.clap_cooldown = now + 1.0 # 1s cooldown
            return True
        return False

    def detect_prayer(self, hands: List[HandData], rel_data: dict) -> bool:
        """Hands parallel and touching = Prayer Pose (Zen Mode)."""
        if len(hands) < 2 or not rel_data: return False
        
        # Parallel check: wrist-to-middle-finger vectors should be roughly opposite or parallel
        # Simplified: distance is very small and velocity is low
        if rel_data['distance'] < 0.08 and abs(rel_data['rel_velocity']) < 0.01:
            return True
        return False

    def get_pinch_scale(self, rel_data: dict) -> float:
        """Use inter-hand distance change for scaling."""
        if not rel_data: return 1.0
        # Return raw distance as a scale factor (normalized 0.0 to 1.0)
        return rel_data['distance']


class GestureCalibration:
    """Hareket kalibrasyonu - Kişisel uyarlama"""
    
    def __init__(self):
        self.calibration_data = {}
        self.user_specific_thresholds = {}
        
    def calibrate_gesture(self, gesture_type: GestureType, 
                         samples: List[HandData]) -> None:
        """Hareketleri kişiye göre ayarla"""
        if not samples:
            return
        
        # İstatistikleri hesapla
        hand_sizes = [np.mean([
            np.sqrt(lm.x**2 + lm.y**2) for lm in sample.landmarks
        ]) for sample in samples]
        
        mean_size = np.mean(hand_sizes)
        std_size = np.std(hand_sizes)
        
        self.calibration_data[gesture_type] = {
            'mean_size': mean_size,
            'std_size': std_size,
            'sample_count': len(samples)
        }
    
    def get_confidence_adjustment(self, gesture_type: GestureType) -> float:
        """Güven ayarlanması al"""
        if gesture_type not in self.calibration_data:
            return 1.0
        
        data = self.calibration_data[gesture_type]
        # Örnek: Daha fazla örnek = daha güvenilir
        return min(2.0, data['sample_count'] / 10.0)


class GestureVisualizationHelper:
    """Hareket görselleştirme yardımcısı"""
    
    @staticmethod
    def get_gesture_description(gesture: GestureType) -> dict:
        """Hareket açıklaması al"""
        descriptions = {
            GestureType.POINT: {
                'name': 'İşaret Parmağı',
                'description': 'İşaret parmağı uzatılmış',
                'color': (0, 255, 0),
                'icon': '👆'
            },
            GestureType.GRAB: {
                'name': 'Tutma Hareketi',
                'description': 'Tüm parmaklar kapalı',
                'color': (255, 0, 0),
                'icon': '✊'
            },
            GestureType.PEACE: {
                'name': 'Peace İşareti',
                'description': 'İşaret ve orta parmak açık',
                'color': (0, 255, 255),
                'icon': '✌️'
            },
            GestureType.OK: {
                'name': 'OK İşareti',
                'description': 'Başparmak ve işaret parmağı birleştirilmiş',
                'color': (255, 255, 0),
                'icon': '👌'
            },
            GestureType.THUMBS_UP: {
                'name': 'Başparmak Yukarı',
                'description': 'Sadece başparmak açık, yukarı bakıyor',
                'color': (0, 200, 100),
                'icon': '👍'
            },
            GestureType.THUMBS_DOWN: {
                'name': 'Başparmak Aşağı',
                'description': 'Sadece başparmak açık, aşağı bakıyor',
                'color': (200, 0, 0),
                'icon': '👎'
            },
            GestureType.PALM_OPEN: {
                'name': 'El Açık',
                'description': 'Tüm parmaklar açık',
                'color': (100, 100, 255),
                'icon': '✋'
            },
            GestureType.VOICE_MODE: {
                'name': 'Ses Modu',
                'description': 'El açık + parmaklar uzağı',
                'color': (255, 100, 0),
                'icon': '🎤'
            },
        }
        
        return descriptions.get(gesture, {
            'name': 'Bilinmeyen',
            'description': 'Tanımlanmayan hareket',
            'color': (128, 128, 128),
            'icon': '❓'
        })

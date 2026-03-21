"""
El izleme ve hareket tanıma sistemi
Profesyonel Hand Tracking ve Gesture Recognition Engine
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class GestureType(Enum):
    """Tanınan hareket türleri (FSM uyumluluğu için)"""
    NONE = 0
    POINT = 1  # İşaret parmağı uzatılmış
    GRAB = 2  # Tüm parmaklar kapalı (tutma hareketi)
    OK = 7  # OK işareti (başparmak + işaret parmağı)

class GestureState(Enum):
    IDLE = 0
    PINCHING = 1   # Pre-click (Transition state)
    CLICKED = 2    # Active Click (Held)
    GRABBING = 3   # Dragging
    MOVING = 4     # Fast motion (Validation Gate)
    LOCKED = 5     # Cooldown state


@dataclass
class HandLandmark:
    """El landmark'ı"""
    x: float
    y: float
    z: float
    confidence: float


@dataclass
class HandData:
    """El verisi"""
    landmarks: List[HandLandmark]
    handedness: str  # 'Right' or 'Left'
    confidence: float
    gesture: GestureType
    center: Tuple[float, float]
    is_valid: bool
    # FSM specific data
    state: GestureState = GestureState.IDLE
    velocity: float = 0.0
    pinch_ratio: float = 0.0
    scroll_y: float = 0.0


class HandTracker:
    # Landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize Hand Tracker with FSM Engine
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1, # Focus on one hand for control
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=confidence_threshold
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # FSM State
        self.state = GestureState.IDLE
        self.state_buffer = [] # For stabilization
        self.BUFFER_SIZE = 3   # Fast reaction, small buffer
        
        # Physics State
        self.prev_palm_center = None
        self.velocity = 0.0
        
        # Config (Self-calibrating thresholds)
        self.PINCH_RATIO_THRESH = 0.10  # Pinch dist / Hand Size
        self.PINCH_RELEASE_RATIO = 0.18 # Hysteresis release
        self.VELOCITY_LIMIT = 0.08      # Normalized movement per frame gate
        
    def process_frame(self, frame: np.ndarray) -> List[HandData]:
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hand_data_list = []
        
        if results.multi_hand_landmarks and results.multi_handedness:
            # Only process the first hand for system control stability
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness_info = results.multi_handedness[0]
            
            # --- 1. Map Landmarks ---
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append(HandLandmark(lm.x, lm.y, lm.z, lm.z))
                
            # --- 2. Physics Calculations ---
            # Hand Size (Normalization Factor): Wrist to Middle MCP
            wrist = landmarks[self.WRIST]
            middle_mcp = landmarks[self.MIDDLE_MCP]
            hand_size = self._dist(wrist, middle_mcp)
            if hand_size == 0: hand_size = 1.0 # Protect div by zero
            
            # Left Click Pinch (Thumb + Index)
            pinch_dist = self._dist(landmarks[self.THUMB_TIP], landmarks[self.INDEX_TIP])
            norm_pinch_dist = pinch_dist / hand_size
            
            # Right Click Pinch (Thumb + Middle)
            middle_pinch_dist = self._dist(landmarks[self.THUMB_TIP], landmarks[self.MIDDLE_TIP])
            norm_middle_pinch = middle_pinch_dist / hand_size
            
            # Palm Center & Velocity
            center_x = np.mean([lm.x for lm in landmarks])
            center_y = np.mean([lm.y for lm in landmarks])
            current_center = (center_x, center_y)
            
            if self.prev_palm_center:
                dx = current_center[0] - self.prev_palm_center[0]
                dy = current_center[1] - self.prev_palm_center[1]
                self.velocity = np.sqrt(dx*dx + dy*dy)
            else:
                self.velocity = 0.0
            self.prev_palm_center = current_center
            
            # --- 3. FSM Update Logic ---
            new_state = self._update_fsm(norm_pinch_dist, norm_middle_pinch, self.velocity, landmarks)
            
            # --- 4. Package Data ---
            # Map FSM state back to GestureType for compatibility check
            # We will use the State directly in main.py mostly, but map for now
            mapped_gesture = self._map_state_to_gesture(new_state)
            
            hand_data = HandData(
                landmarks=landmarks,
                handedness=handedness_info.classification[0].label,
                confidence=handedness_info.classification[0].score,
                gesture=mapped_gesture, 
                center=current_center,
                is_valid=True
            )
            # Attach extra FSM data for advanced control
            hand_data.state = new_state
            hand_data.velocity = self.velocity
            hand_data.pinch_ratio = norm_pinch_dist
            
            # Attach scroll data if scrolling
            if new_state == GestureState.SCROLLING:
                # Use Y movement of index tip for scroll delta
                hand_data.scroll_y = landmarks[self.INDEX_TIP].y
            else:
                hand_data.scroll_y = 0
            
            hand_data_list.append(hand_data)
            
        return hand_data_list

    def _dist(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    def _update_fsm(self, pinch_ratio: float, middle_pinch_ratio: float, velocity: float, landmarks: List[HandLandmark]) -> GestureState:
        """
        Finite State Machine Core
        """
        # Determine strict 'raw' intent based on physics
        raw_intent = GestureState.IDLE
        
        # 1. Check Scroll (Index + Middle UP, others closed)
        # Simplified: Just check if Index and Middle are extended and close together
        index_open = landmarks[self.INDEX_TIP].y < landmarks[self.INDEX_PIP].y
        middle_open = landmarks[self.MIDDLE_TIP].y < landmarks[self.MIDDLE_PIP].y
        ring_closed = landmarks[self.RING_TIP].y > landmarks[self.RING_PIP].y
        pinky_closed = landmarks[self.PINKY_TIP].y > landmarks[self.PINKY_PIP].y
        
        # Distance between index and middle tips should be small for scroll pose
        fingers_together = self._dist(landmarks[self.INDEX_TIP], landmarks[self.MIDDLE_TIP]) < 0.05
        
        # 2. Check Grab (Fist)
        fingers_folded = True
        for tip, pip in [(self.MIDDLE_TIP, self.MIDDLE_PIP), (self.RING_TIP, self.RING_PIP), (self.PINKY_TIP, self.PINKY_PIP)]:
             if landmarks[tip].y < landmarks[pip].y: 
                fingers_folded = False
                break
        
        # Logic Tree
        # Velocity Gate: If moving too fast, lock interaction states (safety)
        if velocity > self.VELOCITY_LIMIT:
             raw_intent = GestureState.MOVING
             
        elif middle_pinch_ratio < self.PINCH_RATIO_THRESH:
             # Right Click Intent
             raw_intent = GestureState.RIGHT_CLICK
             
        elif pinch_ratio < self.PINCH_RATIO_THRESH:
             # Left Click Intent
             if self.state == GestureState.CLICKED:
                 raw_intent = GestureState.CLICKED
             else:
                 raw_intent = GestureState.PINCHING
                 
        elif self.state == GestureState.CLICKED and pinch_ratio < self.PINCH_RELEASE_RATIO:
             # Hysteresis for Left Click
             raw_intent = GestureState.CLICKED

        elif index_open and middle_open and ring_closed and pinky_closed and fingers_together:
             # Two finger scroll
             raw_intent = GestureState.SCROLLING

        elif fingers_folded:
             raw_intent = GestureState.GRABBING
             
        else:
             raw_intent = GestureState.IDLE
             
        # Buffer / Debounce Logic
        self.state_buffer.append(raw_intent)
        if len(self.state_buffer) > self.BUFFER_SIZE:
            self.state_buffer.pop(0)
            
        # Check stability: All frames in buffer must match to switch state
        # Exception: Clicked state holds strong (Schmitt trigger logic above handles release)
        if all(s == raw_intent for s in self.state_buffer):
            # Transition
            if raw_intent == GestureState.PINCHING:
                # Instant transition to click if stable for buffer duration
                self.state = GestureState.CLICKED
            else:
                self.state = raw_intent
                
        return self.state

    def _map_state_to_gesture(self, state: GestureState) -> GestureType:
        if state == GestureState.CLICKED: return GestureType.OK
        if state == GestureState.RIGHT_CLICK: return GestureType.PEACE # Rebrand PEACE as RIGHT_CLICK downstream
        if state == GestureState.GRABBING: return GestureType.GRAB
        if state == GestureState.SCROLLING: return GestureType.THUMBS_UP # Map to scroll logic
        if state == GestureState.MOVING: return GestureType.POINT # Just moving cursor, no interaction
        if state == GestureState.IDLE: return GestureType.POINT   # Idle hand points
        return GestureType.POINT
        
    def draw_hand_skeleton(self, frame: np.ndarray, hand_data_list: List[HandData]) -> np.ndarray:
        if not hand_data_list: return frame
        
        for hand_data in hand_data_list:
            # Custom drawing based on state
            color = (0, 255, 0) # Green IDLE
            if hand_data.state == GestureState.CLICKED: color = (0, 0, 255) # Red CLICK
            if hand_data.state == GestureState.RIGHT_CLICK: color = (255, 0, 255) # Magenta RIGHT CLICK
            if hand_data.state == GestureState.GRABBING: color = (255, 0, 0) # Blue GRAB
            if hand_data.state == GestureState.SCROLLING: color = (0, 165, 255) # Orange SCROLLING
            if hand_data.state == GestureState.MOVING: color = (0, 255, 255) # Yellow MOVING
            
            # Check velocity warning
            if hand_data.velocity > self.VELOCITY_LIMIT:
                cv2.putText(frame, "SPEED LOCK", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            for i, pt in enumerate(points):
                color = (0, 255, 255) if i == self.INDEX_TIP else (255, 100, 0)
                radius = 6 if i in [self.THUMB_TIP, self.INDEX_TIP, self.MIDDLE_TIP, 
                                   self.RING_TIP, self.PINKY_TIP] else 3
                cv2.circle(frame, pt, radius, color, -1)
            
            # El merkezi
            center_x = int(hand_data.center[0] * w)
            center_y = int(hand_data.center[1] * h)
            cv2.circle(frame, (center_x, center_y), 8, (255, 0, 0), 2)
            
            # Hareket adını göster
            gesture_text = hand_data.gesture.name
            text_color = (0, 255, 0) if hand_data.gesture != GestureType.NONE else (0, 0, 255)
            cv2.putText(frame, f"{hand_data.handedness}: {gesture_text}", 
                       (center_x - 50, center_y - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
            
            # Güven skoru
            cv2.putText(frame, f"Conf: {hand_data.confidence:.2f}", 
                       (center_x - 50, center_y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 0), 1)
        
        return frame
    
    def get_finger_positions(self, hand_data: HandData, frame_shape: Tuple[int, int, int]) -> dict:
        """
        Parmak pozisyonlarını ekran koordinatlarında al
        
        Args:
            hand_data: El verisi
            frame_shape: Frame boyutu (h, w, c)
            
        Returns:
            Parmak pozisyonları sözlüğü
        """
        h, w, _ = frame_shape
        
        return {
            'thumb': (int(hand_data.landmarks[self.THUMB_TIP].x * w), 
                     int(hand_data.landmarks[self.THUMB_TIP].y * h)),
            'index': (int(hand_data.landmarks[self.INDEX_TIP].x * w), 
                     int(hand_data.landmarks[self.INDEX_TIP].y * h)),
            'middle': (int(hand_data.landmarks[self.MIDDLE_TIP].x * w), 
                      int(hand_data.landmarks[self.MIDDLE_TIP].y * h)),
            'ring': (int(hand_data.landmarks[self.RING_TIP].x * w), 
                    int(hand_data.landmarks[self.RING_TIP].y * h)),
            'pinky': (int(hand_data.landmarks[self.PINKY_TIP].x * w), 
                     int(hand_data.landmarks[self.PINKY_TIP].y * h)),
            'center': (int(hand_data.center[0] * w), 
                      int(hand_data.center[1] * h)),
        }

"""
Hand Tracking & Gesture Recognition Engine - PRO Version
Advanced FSM-based interaction system with jitter filtering.
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum
import time


class GestureType(Enum):
    """Supported gesture types for system interaction."""
    NONE = 0
    POINT = 1       # Index extended
    GRAB = 2        # Fist (Drag/Grab)
    PEACE = 3       # Index + Middle (Right Click / Context)
    OK = 4          # Thumb + Index pinch (Left Click / Select)
    THUMBS_UP = 5   # Scroll Up / Approve
    THUMBS_DOWN = 6 # Scroll Down / Reject
    PALM_OPEN = 7   # Idle / Stop
    VOICE_MODE = 8  # Custom trigger for voice


class GestureState(Enum):
    """Interaction states for the Finite State Machine."""
    IDLE = 0
    PINCHING = 1    # Transient state before CLICK
    CLICKED = 2     # Active Left Click held
    RIGHT_CLICK = 3 # Active Right Click
    GRABBING = 4    # Drag/Drop mode
    SCROLLING = 5   # Vertical scrolling
    MOVING = 6      # High-speed motion (Input Lock)
    LOCKED = 7      # Cooldown


@dataclass
class HandLandmark:
    x: float
    y: float
    z: float
    confidence: float


@dataclass
class HandData:
    landmarks: List[HandLandmark]
    handedness: str
    confidence: float
    gesture: GestureType
    center: Tuple[float, float]
    is_valid: bool
    state: GestureState = GestureState.IDLE
    velocity: float = 0.0
    pinch_ratio: float = 0.0
    scroll_y: float = 0.0
    z_depth: float = 0.0  # Added for 3D interaction
    # Rolling average for stability
    smoothed_landmarks: List[HandLandmark] = field(default_factory=list)


class EMAFilter:
    """Exponential Moving Average filter for jitter reduction."""
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.value = None

    def apply(self, value):
        if self.value is None:
            self.value = value
        else:
            self.value = self.alpha * value + (1 - self.alpha) * self.value
        return self.value


class KalmanFilter:
    """Simple 2D Kalman Filter for smooth point tracking."""
    def __init__(self, process_noise=0.03, measurement_noise=0.1):
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.state = None # [x, y, vx, vy]
        self.covariance = np.eye(4) * 1.0
        
        self.dt = 1.0 # Will be updated
        self.A = np.eye(4) # State transition matrix
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]]) # Measurement matrix

    def predict(self):
        if self.state is None: return
        self.state = self.A @ self.state
        self.covariance = self.A @ self.covariance @ self.A.T + np.eye(4) * self.process_noise

    def update(self, measurement):
        if self.state is None:
            self.state = np.array([measurement[0], measurement[1], 0, 0])
            return measurement
        
        # Prediction step
        self.predict()
        
        # Update step
        z = np.array(measurement)
        y = z - self.H @ self.state
        S = self.H @ self.covariance @ self.H.T + np.eye(2) * self.measurement_noise
        K = self.covariance @ self.H.T @ np.linalg.inv(S)
        self.state = self.state + K @ y
        self.covariance = (np.eye(4) - K @ self.H) @ self.covariance
        
        return (self.state[0], self.state[1])


class HandTracker:
    # Landmark Mapping
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    INDEX_PIP = 6
    MIDDLE_TIP = 12
    MIDDLE_PIP = 10
    RING_TIP = 16
    RING_PIP = 14
    PINKY_TIP = 20
    PINKY_PIP = 18
    MIDDLE_MCP = 9

    def __init__(self, confidence_threshold: float = 0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=confidence_threshold,
            min_tracking_confidence=confidence_threshold
        )
        
        # Jitter Filtering
        self.filters = {} # Map of index -> (EMA_x, EMA_y, EMA_z)
        self.filter_alpha = 0.6
        self.z_filter = EMAFilter(alpha=0.4)
        self.center_kalman = KalmanFilter()
        
        # FSM State
        self.state = GestureState.IDLE
        self.state_buffer = []
        self.BUFFER_SIZE = 4
        
        # Kinematics
        self.prev_center = None
        self.velocity = (0.0, 0.0) # (vx, vy)
        self.center_history = [] # For swipe detection
        self.SWIPE_MIN_DIST = 0.15 
        self.SWIPE_MAX_TIME = 0.3
        
        # Calibration Thresholds
        self.PINCH_THRESH = 0.12
        self.RELEASE_THRESH = 0.18
        self.VELOCITY_LOCK = 0.10
        self.SCROLL_FINGER_GAP = 0.06
        
        # Calibrated Values
        self.is_calibrated = False
        self.neutral_hand_size = 1.0
        
    def apply_calibration(self, pinch: float, release: float, size: float):
        """Apply user-specific calibrated thresholds."""
        self.PINCH_THRESH = pinch
        self.RELEASE_THRESH = release
        self.neutral_hand_size = size
        self.is_calibrated = True
        print(f"[TRACKER] Calibration Applied: P={pinch:.3f}, R={release:.3f}, S={size:.3f}")

    def _get_filter(self, idx: int):
        if idx not in self.filters:
            self.filters[idx] = (EMAFilter(self.filter_alpha), 
                                 EMAFilter(self.filter_alpha), 
                                 EMAFilter(self.filter_alpha))
        return self.filters[idx]

    def detect_swipe(self) -> Optional[str]:
        """Detect rapid hand movements (flicks)."""
        if len(self.center_history) < 3: return None
        start_pos, start_time = self.center_history[0]
        end_pos, end_time = self.center_history[-1]
        dt = end_time - start_time
        if dt > self.SWIPE_MAX_TIME or dt < 0.05: return None
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        dist = np.sqrt(dx*dx + dy*dy)
        if dist < self.SWIPE_MIN_DIST: return None
        if abs(dx) > abs(dy): return "RIGHT" if dx > 0 else "LEFT"
        else: return "DOWN" if dy > 0 else "UP"

    def process_frame(self, frame: np.ndarray) -> List[HandData]:
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        hand_data_list = []
        
        if results.multi_hand_landmarks:
            landmarks_raw = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label
            conf = results.multi_handedness[0].classification[0].score
            
            # 1. Landmark Filtering & Mapping
            smoothed = []
            for i, lm in enumerate(landmarks_raw.landmark):
                fx, fy, fz = self._get_filter(i)
                smoothed.append(HandLandmark(fx.apply(lm.x), fy.apply(lm.y), fz.apply(lm.z), lm.z))
            
            # 2. Geometry & Physics
            wrist = smoothed[self.WRIST]
            mcp = smoothed[self.MIDDLE_MCP]
            hand_size = np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2)
            if hand_size < 0.01: hand_size = 0.01
            z_smooth = self.z_filter.apply(hand_size)
            
            idx_tip = smoothed[self.INDEX_TIP]
            mid_tip = smoothed[self.MIDDLE_TIP]
            thumb_tip = smoothed[self.THUMB_TIP]
            pinch_dist = self._dist(thumb_tip, idx_tip) / hand_size
            mid_pinch = self._dist(thumb_tip, mid_tip) / hand_size
            
            # Velocity & Kalman Filtering
            now = time.time()
            raw_center = (np.mean([lm.x for lm in smoothed]), np.mean([lm.y for lm in smoothed]))
            center = self.center_kalman.update(raw_center)
            
            self.center_history.append((center, now))
            self.center_history = [(c, t) for c, t in self.center_history if now - t < 0.5]
            
            if self.prev_center:
                self.velocity = (center[0]-self.prev_center[0], center[1]-self.prev_center[1])
            self.prev_center = center
            
            # 3. FSM Update
            speed = np.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
            self.state = self._update_fsm(pinch_dist, mid_pinch, speed, smoothed, hand_size)
            
            # 4. Data Packaging
            data = HandData(
                landmarks=[HandLandmark(lm.x, lm.y, lm.z, lm.z) for lm in landmarks_raw.landmark],
                smoothed_landmarks=smoothed,
                handedness=handedness,
                confidence=conf,
                gesture=self._map_state_to_gesture(self.state, smoothed),
                center=center,
                is_valid=True,
                state=self.state,
                velocity=speed,
                pinch_ratio=pinch_dist,
                z_depth=z_smooth
            )
            if self.state == GestureState.SCROLLING: data.scroll_y = idx_tip.y
            hand_data_list.append(data)
            
        return hand_data_list

    def _dist(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def _update_fsm(self, pinch: float, m_pinch: float, vel: float, lms: List[HandLandmark], size: float) -> GestureState:
        raw = GestureState.IDLE
        idx_up = lms[self.INDEX_TIP].y < lms[self.INDEX_PIP].y
        mid_up = lms[self.MIDDLE_TIP].y < lms[self.MIDDLE_PIP].y
        ring_up = lms[self.RING_TIP].y < lms[self.RING_PIP].y
        pinky_up = lms[self.PINKY_TIP].y < lms[self.PINKY_PIP].y
        
        if vel > self.VELOCITY_LOCK: raw = GestureState.MOVING
        elif m_pinch < self.PINCH_THRESH: raw = GestureState.RIGHT_CLICK
        elif pinch < self.PINCH_THRESH: raw = GestureState.CLICKED if self.state in [GestureState.PINCHING, GestureState.CLICKED] else GestureState.PINCHING
        elif self.state == GestureState.CLICKED and pinch < self.RELEASE_THRESH: raw = GestureState.CLICKED
        elif idx_up and mid_up and not ring_up and not pinky_up: raw = GestureState.SCROLLING
        elif not idx_up and not mid_up and not ring_up and not pinky_up: raw = GestureState.GRABBING
        else: raw = GestureState.IDLE

        self.state_buffer.append(raw)
        if len(self.state_buffer) > self.BUFFER_SIZE: self.state_buffer.pop(0)
        if all(s == raw for s in self.state_buffer):
            if raw == GestureState.PINCHING: return GestureState.CLICKED
            return raw
        return self.state

    def _map_state_to_gesture(self, state: GestureState, lms: List[HandLandmark]) -> GestureType:
        if state == GestureState.CLICKED: return GestureType.OK
        if state == GestureState.RIGHT_CLICK: return GestureType.PEACE
        if state == GestureState.GRABBING: return GestureType.GRAB
        thumb_up = lms[self.THUMB_TIP].y < lms[self.THUMB_TIP-2].y and lms[self.THUMB_TIP].y < lms[self.INDEX_TIP].y
        if thumb_up and lms[self.INDEX_TIP].y > lms[self.INDEX_PIP].y: return GestureType.THUMBS_UP
        if lms[self.INDEX_TIP].y < lms[self.INDEX_PIP].y and lms[self.MIDDLE_TIP].y > lms[self.MIDDLE_PIP].y: return GestureType.POINT
        return GestureType.PALM_OPEN

    def draw_hand_skeleton(self, frame: np.ndarray, hand_data_list: List[HandData]) -> np.ndarray:
        h, w, _ = frame.shape
        for data in hand_data_list:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in data.smoothed_landmarks]
            connections = mp.solutions.hands.HAND_CONNECTIONS
            color = (0, 255, 0)
            if data.state == GestureState.CLICKED: color = (0, 0, 255)
            if data.state == GestureState.GRABBING: color = (255, 0, 0)
            if data.state == GestureState.SCROLLING: color = (0, 165, 255)
            for conn in connections: cv2.line(frame, pts[conn[0]], pts[conn[1]], color, 2)
            for pt in pts: cv2.circle(frame, pt, 4, (255, 255, 255), -1)
            cv2.putText(frame, f"{data.state.name}", (pts[0][0]-20, pts[0][1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame

    def get_finger_positions(self, hand_data: HandData, frame_shape: Tuple[int, int, int]) -> dict:
        h, w, _ = frame_shape
        lms = hand_data.smoothed_landmarks
        return {
            'index': (int(lms[self.INDEX_TIP].x * w), int(lms[self.INDEX_TIP].y * h)),
            'thumb': (int(lms[self.THUMB_TIP].x * w), int(lms[self.THUMB_TIP].y * h)),
            'center': (int(hand_data.center[0] * w), int(hand_data.center[1] * h))
        }

"""
Hand Tracking & Gesture Recognition Engine - PRO Version
Advanced FSM-based interaction system with jitter filtering.
Dual-hand support enabled.
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
    z_depth: float = 0.0
    velocity_vector: Tuple[float, float] = (0.0, 0.0)
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
        self.A = np.eye(4)
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])

    def predict(self):
        if self.state is None: return
        self.state = self.A @ self.state
        self.covariance = self.A @ self.covariance @ self.A.T + np.eye(4) * self.process_noise

    def update(self, measurement):
        if self.state is None:
            self.state = np.array([measurement[0], measurement[1], 0, 0])
            return measurement
        self.predict()
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

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        max_num_hands: int = 2,
        buffer_size: int = 4,
        filter_alpha: float = 0.6,
        pinch_threshold: float = 0.12,
        release_threshold: float = 0.18,
        velocity_lock: float = 0.10,
    ):
        self.mp_hands = mp.solutions.hands
        self.confidence_threshold = confidence_threshold
        self.max_num_hands = max_num_hands
        self._build_hands()
        
        # Per-hand storage (keyed by hand index)
        self.filters = {} # (hand_idx, landmark_idx) -> (EMA_x, EMA_y, EMA_z)
        self.z_filters = {} # hand_idx -> EMAFilter
        self.kalman_filters = {} # hand_idx -> KalmanFilter
        self.states = {} # hand_idx -> GestureState
        self.state_buffers = {} # hand_idx -> List[GestureState]
        self.prev_centers = {} # hand_idx -> Tuple
        self.velocities = {} # hand_idx -> (vx, vy)
        self.histories = {} # hand_idx -> List
        
        self.filter_alpha = filter_alpha
        self.BUFFER_SIZE = buffer_size
        
        # Thresholds
        self.PINCH_THRESH = pinch_threshold
        self.RELEASE_THRESH = release_threshold
        self.VELOCITY_LOCK = velocity_lock
        self.is_calibrated = False
        self.neutral_hand_size = 1.0

    def _build_hands(self):
        if hasattr(self, "hands") and self.hands:
            try:
                self.hands.close()
            except Exception:
                pass
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.confidence_threshold,
            min_tracking_confidence=self.confidence_threshold,
        )

    def reconfigure(
        self,
        confidence_threshold: Optional[float] = None,
        max_num_hands: Optional[int] = None,
        buffer_size: Optional[int] = None,
        filter_alpha: Optional[float] = None,
        pinch_threshold: Optional[float] = None,
        release_threshold: Optional[float] = None,
        velocity_lock: Optional[float] = None,
        neutral_hand_size: Optional[float] = None,
    ):
        rebuild = False
        if confidence_threshold is not None and confidence_threshold != self.confidence_threshold:
            self.confidence_threshold = confidence_threshold
            rebuild = True
        if max_num_hands is not None and max_num_hands != self.max_num_hands:
            self.max_num_hands = max(1, int(max_num_hands))
            rebuild = True
        if buffer_size is not None:
            self.BUFFER_SIZE = max(1, int(buffer_size))
        if filter_alpha is not None:
            self.filter_alpha = max(0.01, min(0.99, float(filter_alpha)))
            rebuild = True
        if pinch_threshold is not None:
            self.PINCH_THRESH = float(pinch_threshold)
        if release_threshold is not None:
            self.RELEASE_THRESH = float(release_threshold)
        if velocity_lock is not None:
            self.VELOCITY_LOCK = float(velocity_lock)
        if neutral_hand_size is not None:
            self.neutral_hand_size = float(neutral_hand_size)
        if rebuild:
            self._build_hands()
            self.filters.clear()
            self.z_filters.clear()
            self.kalman_filters.clear()
            self.states.clear()
            self.state_buffers.clear()
            self.prev_centers.clear()
            self.velocities.clear()
            self.histories.clear()

    def _init_hand_storage(self, idx: int):
        if idx not in self.z_filters:
            self.z_filters[idx] = EMAFilter(alpha=0.4)
            self.kalman_filters[idx] = KalmanFilter()
            self.states[idx] = GestureState.IDLE
            self.state_buffers[idx] = []
            self.prev_centers[idx] = None
            self.velocities[idx] = (0.0, 0.0)
            self.histories[idx] = []

    def _get_filter(self, hand_idx: int, lm_idx: int):
        key = (hand_idx, lm_idx)
        if key not in self.filters:
            self.filters[key] = (EMAFilter(self.filter_alpha), 
                                 EMAFilter(self.filter_alpha), 
                                 EMAFilter(self.filter_alpha))
        return self.filters[key]

    def apply_calibration(self, pinch: float, release: float, size: float):
        self.PINCH_THRESH, self.RELEASE_THRESH, self.neutral_hand_size = pinch, release, size
        self.is_calibrated = True

    def detect_swipe(self, hand_idx: int = 0) -> Optional[str]:
        history = self.histories.get(hand_idx, [])
        if len(history) < 3: return None
        start_pos, start_time = history[0]
        end_pos, end_time = history[-1]
        dt = end_time - start_time
        if dt > 0.3 or dt < 0.05: return None
        dx, dy = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
        dist = np.sqrt(dx*dx + dy*dy)
        if dist < 0.15: return None
        return ("RIGHT" if dx > 0 else "LEFT") if abs(dx) > abs(dy) else ("DOWN" if dy > 0 else "UP")

    def process_frame(self, frame: np.ndarray) -> List[HandData]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        hand_data_list = []
        
        if results.multi_hand_landmarks:
            for i, landmarks_raw in enumerate(results.multi_hand_landmarks):
                self._init_hand_storage(i)
                handedness = results.multi_handedness[i].classification[0].label
                conf = results.multi_handedness[i].classification[0].score
                
                smoothed = []
                for j, lm in enumerate(landmarks_raw.landmark):
                    fx, fy, fz = self._get_filter(i, j)
                    smoothed.append(HandLandmark(fx.apply(lm.x), fy.apply(lm.y), fz.apply(lm.z), lm.z))
                
                wrist, mcp = smoothed[self.WRIST], smoothed[self.MIDDLE_MCP]
                hand_size = max(0.01, np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2))
                z_smooth = self.z_filters[i].apply(hand_size)
                
                pinch_dist = self._dist(smoothed[self.THUMB_TIP], smoothed[self.INDEX_TIP]) / hand_size
                mid_pinch = self._dist(smoothed[self.THUMB_TIP], smoothed[self.MIDDLE_TIP]) / hand_size
                
                now = time.time()
                raw_center = (np.mean([lm.x for lm in smoothed]), np.mean([lm.y for lm in smoothed]))
                center = self.kalman_filters[i].update(raw_center)
                
                self.histories[i].append((center, now))
                self.histories[i] = [(c, t) for c, t in self.histories[i] if now - t < 0.5]
                
                if self.prev_centers[i]:
                    self.velocities[i] = (center[0]-self.prev_centers[i][0], center[1]-self.prev_centers[i][1])
                self.prev_centers[i] = center
                
                speed = np.sqrt(self.velocities[i][0]**2 + self.velocities[i][1]**2)
                self.states[i] = self._update_fsm(i, pinch_dist, mid_pinch, speed, smoothed)
                
                data = HandData(
                    landmarks=[HandLandmark(lm.x, lm.y, lm.z, lm.z) for lm in landmarks_raw.landmark],
                    smoothed_landmarks=smoothed,
                    handedness=handedness,
                    confidence=conf,
                    gesture=self._map_state_to_gesture(self.states[i], smoothed),
                    center=center,
                    is_valid=True,
                    state=self.states[i],
                    velocity=speed,
                    pinch_ratio=pinch_dist,
                    z_depth=z_smooth,
                    velocity_vector=self.velocities[i],
                )
                if self.states[i] == GestureState.SCROLLING: data.scroll_y = smoothed[self.INDEX_TIP].y
                hand_data_list.append(data)
                
        return hand_data_list

    def _dist(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def _update_fsm(self, idx: int, pinch: float, m_pinch: float, vel: float, lms: List[HandLandmark]) -> GestureState:
        raw = GestureState.IDLE
        idx_up, mid_up = lms[self.INDEX_TIP].y < lms[self.INDEX_PIP].y, lms[self.MIDDLE_TIP].y < lms[self.MIDDLE_PIP].y
        ring_up, pinky_up = lms[self.RING_TIP].y < lms[self.RING_PIP].y, lms[self.PINKY_TIP].y < lms[self.PINKY_PIP].y
        
        if vel > self.VELOCITY_LOCK: raw = GestureState.MOVING
        elif m_pinch < self.PINCH_THRESH: raw = GestureState.RIGHT_CLICK
        elif pinch < self.PINCH_THRESH: raw = GestureState.CLICKED if self.states[idx] in [GestureState.PINCHING, GestureState.CLICKED] else GestureState.PINCHING
        elif self.states[idx] == GestureState.CLICKED and pinch < self.RELEASE_THRESH: raw = GestureState.CLICKED
        elif idx_up and mid_up and not ring_up and not pinky_up: raw = GestureState.SCROLLING
        elif not idx_up and not mid_up and not ring_up and not pinky_up: raw = GestureState.GRABBING
        else: raw = GestureState.IDLE

        buf = self.state_buffers[idx]
        buf.append(raw)
        if len(buf) > self.BUFFER_SIZE: buf.pop(0)
        if all(s == raw for s in buf):
            return GestureState.CLICKED if raw == GestureState.PINCHING else raw
        return self.states[idx]

    def _map_state_to_gesture(self, state: GestureState, lms: List[HandLandmark]) -> GestureType:
        if state == GestureState.CLICKED: return GestureType.OK
        if state == GestureState.RIGHT_CLICK: return GestureType.PEACE
        if state == GestureState.GRABBING: return GestureType.GRAB
        thumb_up = lms[self.THUMB_TIP].y < lms[self.THUMB_TIP-2].y and lms[self.THUMB_TIP].y < lms[self.INDEX_TIP].y
        thumb_down = lms[self.THUMB_TIP].y > lms[self.THUMB_TIP-2].y
        idx_up = lms[self.INDEX_TIP].y < lms[self.INDEX_PIP].y
        mid_up = lms[self.MIDDLE_TIP].y < lms[self.MIDDLE_PIP].y
        ring_up = lms[self.RING_TIP].y < lms[self.RING_PIP].y
        pinky_up = lms[self.PINKY_TIP].y < lms[self.PINKY_PIP].y
        if thumb_up and idx_up and mid_up and ring_up and pinky_up:
            return GestureType.VOICE_MODE
        if thumb_up and lms[self.INDEX_TIP].y > lms[self.INDEX_PIP].y: return GestureType.THUMBS_UP
        if thumb_down and not idx_up and not mid_up and not ring_up and not pinky_up:
            return GestureType.THUMBS_DOWN
        if idx_up and not mid_up: return GestureType.POINT
        return GestureType.PALM_OPEN

    def draw_hand_skeleton(self, frame: np.ndarray, hand_data_list: List[HandData]) -> np.ndarray:
        h, w = frame.shape[:2]
        for data in hand_data_list:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in data.smoothed_landmarks]
            color = (0, 255, 0)
            if data.state == GestureState.CLICKED: color = (0, 0, 255)
            elif data.state == GestureState.GRABBING: color = (255, 0, 0)
            elif data.state == GestureState.SCROLLING: color = (0, 165, 255)
            for conn in mp.solutions.hands.HAND_CONNECTIONS: cv2.line(frame, pts[conn[0]], pts[conn[1]], color, 2)
            for pt in pts: cv2.circle(frame, pt, 4, (255, 255, 255), -1)
            cv2.putText(frame, f"{data.handedness}: {data.state.name}", (pts[0][0]-20, pts[0][1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame

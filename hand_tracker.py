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
        
        # Persistent per-hand storage by ID
        self.hand_registry = {} # ID -> HandState dictionary
        self.next_hand_id = 0
        self.max_id_distance = 0.15 # Max distance to associate same ID
        self.max_missing_frames = 5
        
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

    def _create_hand_state(self, initial_center):
        return {
            "z_filter": EMAFilter(alpha=0.4),
            "kalman": KalmanFilter(),
            "state": GestureState.IDLE,
            "buffer": [],
            "prev_center": initial_center,
            "velocity": (0.0, 0.0),
            "history": [],
            "missing_count": 0,
            "filters": {} # (landmark_idx) -> (EMA_x, EMA_y, EMA_z)
        }

    def _get_lm_filters(self, state, lm_idx):
        if lm_idx not in state["filters"]:
            state["filters"][lm_idx] = (EMAFilter(self.filter_alpha), 
                                       EMAFilter(self.filter_alpha), 
                                       EMAFilter(self.filter_alpha))
        return state["filters"][lm_idx]

    def process_frame(self, frame: np.ndarray) -> List[HandData]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        hand_data_list = []
        
        # Current detections
        detections = []
        if results.multi_hand_landmarks:
            for i, landmarks_raw in enumerate(results.multi_hand_landmarks):
                handedness = results.multi_handedness[i].classification[0].label
                conf = results.multi_handedness[i].classification[0].score
                raw_center = (np.mean([lm.x for lm in landmarks_raw.landmark]), 
                             np.mean([lm.y for lm in landmarks_raw.landmark]))
                detections.append({
                    "landmarks": landmarks_raw,
                    "handedness": handedness,
                    "confidence": conf,
                    "center": raw_center
                })

        # Match detections to registry
        matched_ids = set()
        for det in detections:
            best_id = None
            min_dist = self.max_id_distance
            
            for hid, hstate in self.hand_registry.items():
                if hid in matched_ids: continue
                dist = np.sqrt((det["center"][0] - hstate["prev_center"][0])**2 + 
                               (det["center"][1] - hstate["prev_center"][1])**2)
                if dist < min_dist:
                    min_dist = dist
                    best_id = hid
            
            if best_id is None:
                best_id = self.next_hand_id
                self.next_hand_id += 1
                self.hand_registry[best_id] = self._create_hand_state(det["center"])
            
            matched_ids.add(best_id)
            hstate = self.hand_registry[best_id]
            hstate["missing_count"] = 0
            
            # Process detection for this ID
            landmarks_raw = det["landmarks"]
            smoothed = []
            for j, lm in enumerate(landmarks_raw.landmark):
                fx, fy, fz = self._get_lm_filters(hstate, j)
                smoothed.append(HandLandmark(fx.apply(lm.x), fy.apply(lm.y), fz.apply(lm.z), lm.z))
            
            wrist, mcp = smoothed[self.WRIST], smoothed[self.MIDDLE_MCP]
            hand_size = max(0.01, np.sqrt((wrist.x - mcp.x)**2 + (wrist.y - mcp.y)**2))
            z_smooth = hstate["z_filter"].apply(hand_size)
            
            pinch_dist = self._dist(smoothed[self.THUMB_TIP], smoothed[self.INDEX_TIP]) / hand_size
            mid_pinch = self._dist(smoothed[self.THUMB_TIP], smoothed[self.MIDDLE_TIP]) / hand_size
            
            now = time.time()
            center = hstate["kalman"].update(det["center"])
            
            hstate["history"].append((center, now))
            hstate["history"] = [(c, t) for c, t in hstate["history"] if now - t < 0.5]
            
            if hstate["prev_center"]:
                hstate["velocity"] = (center[0]-hstate["prev_center"][0], center[1]-hstate["prev_center"][1])
            hstate["prev_center"] = center
            
            speed = np.sqrt(hstate["velocity"][0]**2 + hstate["velocity"][1]**2)
            hstate["state"] = self._update_fsm(best_id, pinch_dist, mid_pinch, speed, smoothed)
            
            data = HandData(
                landmarks=[HandLandmark(lm.x, lm.y, lm.z, lm.z) for lm in landmarks_raw.landmark],
                smoothed_landmarks=smoothed,
                handedness=det["handedness"],
                confidence=det["confidence"],
                gesture=self._map_state_to_gesture(hstate["state"], smoothed),
                center=center,
                is_valid=True,
                state=hstate["state"],
                velocity=speed,
                pinch_ratio=pinch_dist,
                z_depth=z_smooth,
                velocity_vector=hstate["velocity"],
            )
            if hstate["state"] == GestureState.SCROLLING: data.scroll_y = smoothed[self.INDEX_TIP].y
            hand_data_list.append(data)

        # Cleanup missing hands
        to_delete = []
        for hid in self.hand_registry:
            if hid not in matched_ids:
                self.hand_registry[hid]["missing_count"] += 1
                if self.hand_registry[hid]["missing_count"] > self.max_missing_frames:
                    to_delete.append(hid)
        for hid in to_delete:
            del self.hand_registry[hid]
            
        return hand_data_list

    def _update_fsm(self, hid: int, pinch: float, m_pinch: float, vel: float, lms: List[HandLandmark]) -> GestureState:
        hstate = self.hand_registry[hid]
        prev_state = hstate["state"]
        raw = GestureState.IDLE
        idx_up, mid_up = lms[self.INDEX_TIP].y < lms[self.INDEX_PIP].y, lms[self.MIDDLE_TIP].y < lms[self.MIDDLE_PIP].y
        ring_up, pinky_up = lms[self.RING_TIP].y < lms[self.RING_PIP].y, lms[self.PINKY_TIP].y < lms[self.PINKY_PIP].y
        
        # Enhanced Hysteresis: Use different thresholds for entering vs leaving a state
        p_enter = self.PINCH_THRESH
        p_leave = self.RELEASE_THRESH
        
        if vel > self.VELOCITY_LOCK: 
            raw = GestureState.MOVING
        elif m_pinch < p_enter: 
            raw = GestureState.RIGHT_CLICK
        elif prev_state == GestureState.CLICKED:
            # Stay clicked until pinch distance exceeds release threshold
            raw = GestureState.CLICKED if pinch < p_leave else GestureState.IDLE
        elif pinch < p_enter:
            raw = GestureState.CLICKED if prev_state == GestureState.PINCHING else GestureState.PINCHING
        elif idx_up and mid_up and not ring_up and not pinky_up: 
            raw = GestureState.SCROLLING
        elif not idx_up and not mid_up and not ring_up and not pinky_up: 
            raw = GestureState.GRABBING
        else: 
            raw = GestureState.IDLE

        buf = hstate["buffer"]
        buf.append(raw)
        if len(buf) > self.BUFFER_SIZE: buf.pop(0)
        
        # Decision logic based on buffer consistency
        if all(s == raw for s in buf):
            return GestureState.CLICKED if raw == GestureState.PINCHING else raw
        return prev_state

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
            
            # Professional Cyber-UI Palette
            base_color = (255, 200, 0) # Cyan-Blue base
            if data.state == GestureState.CLICKED: base_color = (0, 0, 255) # Red for action
            elif data.state == GestureState.GRABBING: base_color = (255, 0, 100) # Purple for grab
            elif data.state == GestureState.SCROLLING: base_color = (0, 255, 100) # Green for scroll
            
            # 1. Draw connections with Glow effect
            for conn in mp.solutions.hands.HAND_CONNECTIONS:
                p1, p2 = pts[conn[0]], pts[conn[1]]
                # Glow Layer
                cv2.line(frame, p1, p2, base_color, 4, cv2.LINE_AA)
                # Core Layer
                cv2.line(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)
            
            # 2. Draw Joints (Landmarks)
            for i, pt in enumerate(pts):
                radius = 3 if i != 0 else 6 # Wrist is larger
                # Outer Glow
                cv2.circle(frame, pt, radius + 2, base_color, -1, cv2.LINE_AA)
                # Inner White
                cv2.circle(frame, pt, radius, (255, 255, 255), -1, cv2.LINE_AA)
            
            # 3. Side Label with professional Typography feel
            label = f"{data.handedness.upper()} | {data.state.name}"
            cv2.putText(frame, label, (pts[0][0]-40, pts[0][1]+40), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, label, (pts[0][0]-40, pts[0][1]+40), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return frame

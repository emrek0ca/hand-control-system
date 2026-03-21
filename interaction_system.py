"""
Liquid Glass UI Engine - Pro Version
Advanced Glassmorphism UI components with transparency and glow effects.
Emoji-free, professional design language.
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from enum import Enum
import time


class ObjectType(Enum):
    BUTTON = 1
    PANEL = 2
    PROGRESS_BAR = 3
    WIDGET = 4


@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class InteractiveObject:
    object_id: str
    obj_type: ObjectType
    position: Point
    size: Tuple[int, int]
    label: str
    color: Tuple[int, int, int] = (255, 255, 255)
    opacity: float = 0.4
    on_click: Optional[Callable] = None
    is_dragging: bool = False
    is_hovered: bool = False
    glow_intensity: float = 0.0
    # Animation properties
    target_position: Optional[Point] = None
    lerp_speed: float = 0.15
    
    def contains_point(self, point: Point) -> bool:
        return (self.position.x <= point.x <= self.position.x + self.size[0] and
                self.position.y <= point.y <= self.position.y + self.size[1])

    def update_animation(self):
        """Smoothly move position towards target_position."""
        if self.target_position:
            dx = self.target_position.x - self.position.x
            dy = self.target_position.y - self.position.y
            self.position.x += dx * self.lerp_speed
            self.position.y += dy * self.lerp_speed


class TrailManager:
    """Manages a fading liquid trail for the hand pointer."""
    def __init__(self, max_len: int = 15):
        self.points = [] # List of (x, y, timestamp)
        self.max_len = max_len

    def add_point(self, x: int, y: int):
        self.points.append((x, y, time.time()))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def draw(self, frame: np.ndarray, color: Tuple[int, int, int] = (255, 255, 255)):
        if len(self.points) < 2: return
        
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i+1]
            
            # Fade based on age/index
            alpha = (i + 1) / len(self.points)
            thickness = int(2 + 6 * alpha)
            
            cv2.line(frame, (p1[0], p1[1]), (p2[0], p2[1]), color, thickness, cv2.LINE_AA)


class GlassRenderer:
    """Handles professional Glassmorphism rendering in OpenCV."""
    
    @staticmethod
    def draw_glass_rect(frame: np.ndarray, x: int, y: int, w: int, h: int, 
                        color: Tuple[int, int, int], opacity: float, 
                        glow: float = 0.0, label: str = "") -> None:
        """Draws a semi-transparent 'glass' rectangle with optional glow."""
        overlay = frame.copy()
        
        # 1. Main Glass Surface
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        
        # 2. Frost/Blur (Simplified: slightly lighter alpha for the area)
        cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
        
        # 3. Glass Edge (Bright highlight)
        edge_color = (255, 255, 255)
        edge_opacity = 0.6 + (glow * 0.4)
        cv2.rectangle(frame, (x, y), (x + w, y + h), edge_color, 1, cv2.LINE_AA)
        
        # 4. Liquid Glow Effect
        if glow > 0:
            for i in range(1, 4):
                alpha = (glow * 0.3) / i
                glow_color = color
                cv2.rectangle(frame, (x-i, y-i), (x+w+i, y+h+i), glow_color, 1, cv2.LINE_AA)
        
        # 5. Clean Typography (No Emojis)
        if label:
            font = cv2.FONT_HERSHEY_DUPLEX
            scale = 0.55
            thickness = 1
            text_size = cv2.getTextSize(label, font, scale, thickness)[0]
            tx = x + (w - text_size[0]) // 2
            ty = y + (h + text_size[1]) // 2
            
            # Subtle shadow for text
            cv2.putText(frame, label, (tx+1, ty+1), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
            cv2.putText(frame, label, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    @staticmethod
    def draw_aura(frame: np.ndarray, center: Tuple[int, int], radius: int, 
                  color: Tuple[int, int, int], intensity: float):
        """Draws a pulsing glowing aura around a point."""
        if intensity <= 0: return
        
        # Pulsing logic
        pulse = 1.0 + 0.1 * np.sin(time.time() * 5)
        r = int(radius * pulse)
        
        for i in range(1, 5):
            alpha = (intensity * 0.4) / i
            cv2.circle(frame, center, r + i*2, color, 1, cv2.LINE_AA)
        
        cv2.circle(frame, center, r, (255, 255, 255), 1, cv2.LINE_AA)


class InteractionManager:
    """Manages UI objects and their liquid interactions."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.objects: List[InteractiveObject] = []
        self.active_object: Optional[InteractiveObject] = None
        self.trail = TrailManager()

    def add_object(self, obj: InteractiveObject):
        self.objects.append(obj)

    def check_interactions(self, pointer: Tuple[int, int], clicked: bool):
        p = Point(pointer[0], pointer[1])
        self.active_object = None
        self.trail.add_point(pointer[0], pointer[1])
        
        for obj in self.objects:
            obj.update_animation()
            obj.is_hovered = obj.contains_point(p)
            
            # Liquid Glow Animation
            if obj.is_hovered:
                obj.glow_intensity = min(1.0, obj.glow_intensity + 0.2)
                self.active_object = obj
            else:
                obj.glow_intensity = max(0.0, obj.glow_intensity - 0.1)
                
            if clicked and obj.is_hovered and obj.on_click:
                obj.on_click()

    def draw(self, frame: np.ndarray) -> np.ndarray:
        # 1. Draw Trail
        self.trail.draw(frame)
        
        # 2. Draw Objects
        for obj in self.objects:
            x, y = int(obj.position.x), int(obj.position.y)
            w, h = obj.size
            
            GlassRenderer.draw_glass_rect(
                frame, x, y, w, h, 
                obj.color, obj.opacity, 
                obj.glow_intensity, obj.label
            )
        return frame


class DashboardBuilder:
    """API for building the automation dashboard."""
    
    def __init__(self, width: int, height: int):
        self.manager = InteractionManager(width, height)

    def add_button(self, x, y, w, h, label, callback, color=(60, 60, 60)):
        btn = InteractiveObject(
            object_id=label,
            obj_type=ObjectType.BUTTON,
            position=Point(x, y),
            size=(w, h),
            label=label,
            color=color,
            on_click=callback
        )
        self.manager.add_object(btn)
        return btn

    def get_manager(self):
        return self.manager

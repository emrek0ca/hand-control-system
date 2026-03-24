"""
Liquid Glass UI Engine - Pro Version
Advanced Glassmorphism UI components with transparency and glow effects.
Emoji-free, professional design language.
Includes Intro/Splash Screen Engine.
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


class Particle:
    """A single liquid glass particle."""
    def __init__(self, x, y, vx, vy, color, z=0):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, (np.random.random() - 0.5) * 2
        self.life = 1.0  
        self.decay = 0.01 + np.random.random() * 0.02
        self.color = color
        self.size = 2 + np.random.random() * 4
        self.base_size = self.size # For 3D scaling

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        self.life -= self.decay
        self.size *= 0.95
        return self.life > 0

class IntroManager:
    """Handles the fütüristic 3D particle welcome screen."""
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.particles = []
        self.start_time = time.time()
        self.duration = 4.0 # seconds
        self.text = "MERHABA"
        self.sub_text = "AI AGENT INITIALIZING"

    def update(self):
        # Spawn new floating particles
        if len(self.particles) < 200:
            self.particles.append(Particle(
                np.random.randint(0, self.width),
                np.random.randint(0, self.height),
                (np.random.random() - 0.5) * 2,
                (np.random.random() - 0.5) * 2,
                (200, 255, 255),
                z=np.random.random() * 100
            ))
        
        # Update existing
        self.particles = [p for p in self.particles if p.update()]

    def draw(self) -> np.ndarray:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # 1. Draw 3D Floating Particles
        for p in self.particles:
            # Simple 3D projection
            scale = 200 / (200 + p.z)
            px = int(self.width/2 + (p.x - self.width/2) * scale)
            py = int(self.height/2 + (p.y - self.height/2) * scale)
            size = int(p.base_size * scale)
            alpha = p.life * (1.0 - p.z / 200)
            
            if 0 <= px < self.width and 0 <= py < self.height:
                color = tuple(int(c * alpha) for c in p.color)
                cv2.circle(frame, (px, py), size, color, -1, cv2.LINE_AA)

        # 2. Draw Welcome Text (Glow Effect)
        elapsed = time.time() - self.start_time
        text_alpha = min(1.0, elapsed / 1.5)
        if elapsed > self.duration - 1.0:
            text_alpha = max(0.0, self.duration - elapsed)

        font = cv2.FONT_HERSHEY_DUPLEX
        scale = 2.5
        thick = 3
        t_size = cv2.getTextSize(self.text, font, scale, thick)[0]
        tx = (self.width - t_size[0]) // 2
        ty = (self.height + t_size[1]) // 2
        
        color = (int(255 * text_alpha), int(255 * text_alpha), int(255 * text_alpha))
        # Shadow/Glow
        cv2.putText(frame, self.text, (tx+2, ty+2), font, scale, (50, 50, 50), thick, cv2.LINE_AA)
        cv2.putText(frame, self.text, (tx, ty), font, scale, color, thick, cv2.LINE_AA)
        
        # Subtext
        s_scale = 0.7
        s_size = cv2.getTextSize(self.sub_text, font, s_scale, 1)[0]
        cv2.putText(frame, self.sub_text, ((self.width - s_size[0]) // 2, ty + 50), font, s_scale, (150, 150, 150), 1, cv2.LINE_AA)

        return frame

class ParticleEngine:
    """High-performance particle management system."""
    def __init__(self, max_particles: int = 150):
        self.particles: List[Particle] = []
        self.max_particles = max_particles

    def spawn(self, x, y, vx, vy, color, count=1):
        for _ in range(count):
            if len(self.particles) < self.max_particles:
                svx = vx * 0.3 + (np.random.random() - 0.5) * 5
                svy = vy * 0.3 + (np.random.random() - 0.5) * 5
                self.particles.append(Particle(x, y, svx, svy, color))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, frame: np.ndarray):
        for p in self.particles:
            alpha = p.life
            color = tuple(int(c * alpha) for c in p.color)
            cv2.circle(frame, (int(p.x), int(p.y)), int(p.size), color, -1, cv2.LINE_AA)


class GlassRenderer:
    """Handles professional Glassmorphism rendering in OpenCV."""
    
    @staticmethod
    def draw_glass_rect(frame: np.ndarray, x: int, y: int, w: int, h: int, 
                        color: Tuple[int, int, int], opacity: float, 
                        glow: float = 0.0, label: str = "") -> None:
        """Draws a semi-transparent 'glass' rectangle with soft edges and glow."""
        # 1. Main Background with subtle gradient feel
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
        
        # Apply slight blur to overlay for a frosted glass effect
        sub = overlay[y:y+h, x:x+w]
        if sub.size > 0:
            sub = cv2.GaussianBlur(sub, (3, 3), 0)
            overlay[y:y+h, x:x+w] = sub
            
        cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
        
        # 2. Beveled Edges
        edge_color = (255, 255, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), edge_color, 1, cv2.LINE_AA)
        
        # 3. Dynamic Glow Layer
        if glow > 0:
            glow_color = tuple(int(c * 1.2) for c in color)
            for i in range(1, 6):
                alpha = (glow * 0.4) / i
                thickness = i
                # Draw outer soft glow
                cv2.rectangle(frame, (x-i, y-i), (x+w+i, y+h+i), glow_color, 1, cv2.LINE_AA)
        
        if label:
            font = cv2.FONT_HERSHEY_DUPLEX
            scale = 0.5
            thickness = 1
            t_size = cv2.getTextSize(label, font, scale, thickness)[0]
            tx = x + (w - t_size[0]) // 2
            ty = y + (h + t_size[1]) // 2
            # Text shadow
            cv2.putText(frame, label, (tx+1, ty+1), font, scale, (20, 20, 20), thickness, cv2.LINE_AA)
            cv2.putText(frame, label, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

    @staticmethod
    def draw_aura(frame: np.ndarray, center: Tuple[int, int], radius: int, 
                  color: Tuple[int, int, int], intensity: float):
        """Draws a pulsing glowing aura with secondary rings."""
        if intensity <= 0: return
        pulse = 1.0 + 0.15 * np.sin(time.time() * 6)
        r = int(radius * pulse)
        
        # Outer Ring
        cv2.circle(frame, center, r + 10, color, 1, cv2.LINE_AA)
        # Inner Glowing Rings
        for i in range(1, 4):
            alpha = (intensity * 0.5) / i
            c = tuple(int(ch * alpha) for ch in color)
            cv2.circle(frame, center, r - i*3, c, 2, cv2.LINE_AA)
            
        cv2.circle(frame, center, r, (255, 255, 255), 2, cv2.LINE_AA)

    @staticmethod
    def draw_pulse(frame: np.ndarray, center: Tuple[int, int], life: float, color: Tuple[int, int, int]):
        """Visual feedback for a click action."""
        r = int(20 + (1.0 - life) * 60)
        alpha = life
        c = tuple(int(ch * alpha) for ch in color)
        cv2.circle(frame, center, r, c, 3, cv2.LINE_AA)


class InteractionManager:
    """Manages UI objects and their liquid interactions."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.objects: List[InteractiveObject] = []
        self.active_object: Optional[InteractiveObject] = None
        self.trail = TrailManager()
        self.particles = ParticleEngine()
        self.pulses = [] # List of (center, life, color)

    def add_object(self, obj: InteractiveObject):
        self.objects.append(obj)

    def trigger_pulse(self, center: Tuple[int, int], color=(255, 255, 255)):
        self.pulses.append([center, 1.0, color])

    def check_interactions(self, pointer: Tuple[int, int], clicked: bool, velocity: Tuple[float, float] = (0, 0)):
        p = Point(pointer[0], pointer[1])
        self.active_object = None
        self.trail.add_point(pointer[0], pointer[1])
        
        # Pulse on click
        if clicked:
            self.trigger_pulse(pointer, color=(0, 255, 255))
            self.particles.spawn(pointer[0], pointer[1], 0, 0, (255, 255, 255), count=15)
        
        # Spawn particles based on velocity
        speed = np.sqrt(velocity[0]**2 + velocity[1]**2)
        if speed > 8:
            self.particles.spawn(pointer[0], pointer[1], velocity[0], velocity[1], (0, 255, 255), count=1)
        
        for obj in self.objects:
            obj.update_animation()
            obj.is_hovered = obj.contains_point(p)
            
            if obj.is_hovered:
                obj.glow_intensity = min(1.0, obj.glow_intensity + 0.15)
                self.active_object = obj
            else:
                obj.glow_intensity = max(0.0, obj.glow_intensity - 0.08)
                
            if clicked and obj.is_hovered and obj.on_click:
                obj.on_click()
        
        # Update Pulses
        for pulse in self.pulses:
            pulse[1] -= 0.05
        self.pulses = [p for p in self.pulses if p[1] > 0]
        
        self.particles.update()

    def draw(self, frame: np.ndarray) -> np.ndarray:
        self.trail.draw(frame)
        self.particles.draw(frame)
        
        for p in self.pulses:
            GlassRenderer.draw_pulse(frame, p[0], p[1], p[2])
            
        for obj in self.objects:
            x, y = int(obj.position.x), int(obj.position.y)
            w, h = obj.size
            GlassRenderer.draw_glass_rect(frame, x, y, w, h, obj.color, obj.opacity, obj.glow_intensity, obj.label)
        return frame

    def draw_objects(self, frame: np.ndarray) -> np.ndarray:
        return self.draw(frame)


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

    def add_draggable_widget(self, x, y, w, h, label, callback=None, color=(72, 72, 72)):
        widget = InteractiveObject(
            object_id=label,
            obj_type=ObjectType.WIDGET,
            position=Point(x, y),
            size=(w, h),
            label=label,
            color=color,
            on_click=callback,
            is_dragging=True,
        )
        self.manager.add_object(widget)
        return widget

    def get_manager(self):
        return self.manager

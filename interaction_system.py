"""
Nesneler ve etkileşim sistemi
Interactive Object Management System
"""

import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta


class ObjectType(Enum):
    """Nesne türleri"""
    BUTTON = 1
    SLIDER = 2
    TEXT_BOX = 3
    WIDGET = 4
    DRAGGABLE = 5


@dataclass
class Point:
    """2D Nokta"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Mesafeyi hesapla"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)


@dataclass
class InteractiveObject:
    """Etkileşimli nesne"""
    object_id: str
    obj_type: ObjectType
    position: Point
    size: Tuple[int, int]  # (width, height)
    label: str
    color: Tuple[int, int, int]
    on_click: Optional[Callable] = None
    on_drag: Optional[Callable] = None
    on_hover: Optional[Callable] = None
    is_dragging: bool = False
    is_hovered: bool = False
    data: dict = field(default_factory=dict)
    
    def contains_point(self, point: Point) -> bool:
        """Noktanın nesne içinde olup olmadığını kontrol et"""
        return (self.position.x <= point.x <= self.position.x + self.size[0] and
                self.position.y <= point.y <= self.position.y + self.size[1])
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Nesne sınırlarını al (x1, y1, x2, y2)"""
        return (
            int(self.position.x),
            int(self.position.y),
            int(self.position.x + self.size[0]),
            int(self.position.y + self.size[1])
        )


class InteractionManager:
    """Nesne etkileşim yöneticisi"""
    
    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize manager
        
        Args:
            frame_width: Kamera frame genişliği
            frame_height: Kamera frame yüksekliği
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.objects: List[InteractiveObject] = []
        self.object_map = {}  # ID'den objeye hızlı erişim
        self.active_object: Optional[InteractiveObject] = None
        self.dragging_object: Optional[InteractiveObject] = None
        self.interaction_history: List[dict] = []
        
    def add_object(self, obj: InteractiveObject) -> None:
        """Nesne ekle"""
        self.objects.append(obj)
        self.object_map[obj.object_id] = obj
    
    def remove_object(self, object_id: str) -> None:
        """Nesne sil"""
        self.objects = [o for o in self.objects if o.object_id != object_id]
        del self.object_map[object_id]
    
    def get_object_at_point(self, point: Point) -> Optional[InteractiveObject]:
        """Belirtilen noktada nesne ara (en üste olan)"""
        for obj in reversed(self.objects):  # Tersten çünkü en son eklenenler üste
            if obj.contains_point(point):
                return obj
        return None
    
    def check_interactions(self, 
                          pointer_position: Tuple[int, int],
                          grab_active: bool,
                          prev_pointer_position: Optional[Tuple[int, int]] = None) -> None:
        """
        Etkileşimleri kontrol et
        
        Args:
            pointer_position: İşaretçi pozisyonu (x, y)
            grab_active: Tutma hareketi aktif mi?
            prev_pointer_position: Önceki pozisyon (drag için)
        """
        point = Point(pointer_position[0], pointer_position[1])
        
        # Hover kontrolü
        for obj in self.objects:
            was_hovered = obj.is_hovered
            obj.is_hovered = obj.contains_point(point)
            
            if obj.is_hovered and not was_hovered and obj.on_hover:
                obj.on_hover(obj)
        
        # Grab kontrolü
        if grab_active:
            if not self.dragging_object:
                # Nesneleri tutmaya başla
                obj_at_point = self.get_object_at_point(point)
                if obj_at_point:
                    self.dragging_object = obj_at_point
                    self.dragging_object.is_dragging = True
            else:
                # Sürüklemeye devam et
                if prev_pointer_position:
                    delta = Point(
                        pointer_position[0] - prev_pointer_position[0],
                        pointer_position[1] - prev_pointer_position[1]
                    )
                    self.dragging_object.position += delta
                    
                    # Sınırları kontrol et
                    self.dragging_object.position.x = max(0, min(
                        self.dragging_object.position.x,
                        self.frame_width - self.dragging_object.size[0]
                    ))
                    self.dragging_object.position.y = max(0, min(
                        self.dragging_object.position.y,
                        self.frame_height - self.dragging_object.size[1]
                    ))
                    
                    if self.dragging_object.on_drag:
                        self.dragging_object.on_drag(self.dragging_object)
        else:
            # Grab deaktif - sürüklemeyi sonlandır
            if self.dragging_object:
                self.dragging_object.is_dragging = False
                self.dragging_object = None
        
        # Tıklama (grab deaktif olduğunda)
        if not grab_active and self.active_object:
            obj_at_point = self.get_object_at_point(point)
            if obj_at_point and obj_at_point.on_click:
                obj_at_point.on_click(obj_at_point)
            self.active_object = None
        elif grab_active and not self.active_object:
            self.active_object = self.get_object_at_point(point)
    
    def draw_objects(self, frame: np.ndarray) -> np.ndarray:
        """Nesneleri frame'e çiz"""
        for obj in self.objects:
            x1, y1, x2, y2 = obj.get_bounds()
            
            # Arka plan rengi
            color = obj.color
            if obj.is_dragging:
                color = tuple(int(c * 0.7) for c in color)  # Daha koyu
            elif obj.is_hovered:
                color = tuple(min(255, c + 60) for c in color)  # Daha parlak
            
            # Nesneyi çiz
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # Label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            text_size = cv2.getTextSize(obj.label, font, font_scale, thickness)[0]
            
            text_x = x1 + (obj.size[0] - text_size[0]) // 2
            text_y = y1 + (obj.size[1] + text_size[1]) // 2
            
            cv2.putText(frame, obj.label, (text_x, text_y), 
                       font, font_scale, (0, 0, 0), thickness)
            
            # Drag durumu göster
            if obj.is_dragging:
                cv2.circle(frame, (x2 - 10, y1 + 10), 5, (0, 255, 0), -1)
        
        return frame


class DashboardBuilder:
    """Kontrol paneli oluşturucu"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.manager = InteractionManager(width, height)
    
    def add_button(self, 
                  x: int, y: int, 
                  width: int, height: int,
                  label: str,
                  callback: Optional[Callable] = None,
                  color: Tuple[int, int, int] = (50, 150, 255)) -> InteractiveObject:
        """Buton ekle"""
        btn = InteractiveObject(
            object_id=f"btn_{x}_{y}_{label}",
            obj_type=ObjectType.BUTTON,
            position=Point(x, y),
            size=(width, height),
            label=label,
            color=color,
            on_click=callback
        )
        self.manager.add_object(btn)
        return btn
    
    def add_draggable_widget(self,
                           x: int, y: int,
                           width: int, height: int,
                           label: str,
                           color: Tuple[int, int, int] = (100, 200, 150)) -> InteractiveObject:
        """Sürüklenebilir widget ekle"""
        widget = InteractiveObject(
            object_id=f"widget_{x}_{y}_{label}",
            obj_type=ObjectType.DRAGGABLE,
            position=Point(x, y),
            size=(width, height),
            label=label,
            color=color
        )
        self.manager.add_object(widget)
        return widget
    
    def get_manager(self) -> InteractionManager:
        """Interaction manager'ı al"""
        return self.manager

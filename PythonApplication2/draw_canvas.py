# draw_canvas.py - HOLOGRAM EDITION ⬡ v3.5 - SMOOTH DRAWING & ERASER (FIXED)
# ═══════════════════════════════════════════════════════════════════════════
# AIR CANVAS - Cyberpunk HUD • Brush Types • Highlighter • Marker
# Features: One Euro Filter, Bezier Curves, Multiple Brush Effects
# FIXED VERSION - Smooth drawing and eraser with interpolation
# ═══════════════════════════════════════════════════════════════════════════

import cv2
import math
import time
import os
import random
import mediapipe as mp
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import (QPainter, QPen, QColor, QPixmap, QFont, QGuiApplication,
                           QImage, QLinearGradient, QRadialGradient, QBrush, QPolygonF, QPainterPath)
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QObject, QRectF

# Import Presentation Module
from presentation_mode import PresentationDialog, PresentationViewer


# ═══════════════════════════════════════════════════════════════════════════
# CYBERPUNK COLOR SCHEME ⬡
# ═══════════════════════════════════════════════════════════════════════════

class CyberColors:
    """Cyberpunk Holographic Color Palette"""
   
    BG_VOID = QColor(2, 4, 10)
    BG_DARK = QColor(8, 12, 22)
    BG_PANEL = QColor(10, 18, 32, 220)
    BG_HOLOGRAM = QColor(5, 15, 30, 200)
   
    NEON_CYAN = QColor(0, 255, 255)
    NEON_MAGENTA = QColor(255, 0, 128)
    NEON_PURPLE = QColor(180, 60, 255)
    NEON_GREEN = QColor(0, 255, 128)
    NEON_ORANGE = QColor(255, 128, 0)
    NEON_YELLOW = QColor(255, 255, 0)
    NEON_BLUE = QColor(0, 150, 255)
    NEON_PINK = QColor(255, 80, 180)
   
    GRID_LINE = QColor(0, 255, 255, 25)
    SCANLINE = QColor(0, 255, 255, 40)
    GLOW_CYAN = QColor(0, 255, 255, 80)
    GLOW_MAGENTA = QColor(255, 0, 128, 80)
    BORDER_BRIGHT = QColor(0, 255, 255, 200)
    BORDER_DIM = QColor(0, 255, 255, 60)
   
    TEXT_BRIGHT = QColor(220, 255, 255)
    TEXT_NORMAL = QColor(150, 220, 230)
    TEXT_DIM = QColor(80, 140, 160)
    TEXT_WARN = QColor(255, 180, 0)
    TEXT_DANGER = QColor(255, 60, 100)


# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND MODES 🎨
# ═══════════════════════════════════════════════════════════════════════════

class BackgroundMode:
    TRANSPARENT = 0
    VOID = 1
    CYBER_GRADIENT = 2
    FROSTED = 3
   
    NAMES = ["TRANSPARENT", "VOID BLACK", "CYBER GRADIENT", "FROSTED GLASS"]
    COUNT = 4


# ═══════════════════════════════════════════════════════════════════════════
# SHAPE TOOLS 🔷
# ═══════════════════════════════════════════════════════════════════════════

class ShapeTool:
    """Shape tool definitions"""
    FREEHAND = 0
    ARROW = 1
    RECTANGLE = 2
    SQUARE = 3
    CIRCLE = 4
   
    NAMES = ["FREEHAND", "ARROW", "RECTANGLE", "SQUARE", "CIRCLE"]
    ICONS = ["✏️", "➔", "▭", "■", "●"]
    COUNT = 5


# ═══════════════════════════════════════════════════════════════════════════
# BRUSH TYPES 🖌️
# ═══════════════════════════════════════════════════════════════════════════

class BrushType:
    """Brush type definitions"""
    NORMAL = 0
    HIGHLIGHTER = 1
    MARKER = 2
   
    NAMES = ["NORMAL", "HIGHLIGHTER", "MARKER"]
    ICONS = ["✏️", "🖍️", "🖊️"]
    DESCRIPTIONS = [
        "Smooth solid lines",
        "Semi-transparent wide strokes",
        "Bold solid strokes"
    ]
    COUNT = 3


# ═══════════════════════════════════════════════════════════════════════════
# ONE EURO FILTER - BEST SMOOTHING FOR REAL-TIME INPUT 🎯
# ═══════════════════════════════════════════════════════════════════════════

class LowPassFilter:
    """Simple low-pass filter for smoothing"""
   
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.y = None
        self.s = None
   
    def filter(self, value, alpha=None):
        if alpha is None:
            alpha = self.alpha
        if self.y is None:
            self.s = value
        else:
            self.s = alpha * value + (1.0 - alpha) * self.s
        self.y = value
        return self.s
   
    def reset(self):
        self.y = None
        self.s = None
   
    def has_last_value(self):
        return self.y is not None
   
    def last_value(self):
        return self.y


class OneEuroFilter:
    """
    One Euro Filter - Optimal for real-time gesture/drawing smoothing
    """
   
    def __init__(self, freq=60.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.last_time = None
   
    def _alpha(self, cutoff):
        te = 1.0 / self.freq
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)
   
    def filter(self, x, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
       
        if self.last_time is not None and timestamp > self.last_time:
            self.freq = 1.0 / (timestamp - self.last_time)
        self.last_time = timestamp
       
        if self.x_filter.has_last_value():
            dx = (x - self.x_filter.last_value()) * self.freq
        else:
            dx = 0.0
       
        edx = self.dx_filter.filter(dx, self._alpha(self.d_cutoff))
        cutoff = self.min_cutoff + self.beta * abs(edx)
       
        return self.x_filter.filter(x, self._alpha(cutoff))
   
    def reset(self):
        self.x_filter.reset()
        self.dx_filter.reset()
        self.last_time = None


class Point2DFilter:
    """Applies One Euro Filter to 2D points"""
   
    def __init__(self, freq=60.0, min_cutoff=1.0, beta=0.004, d_cutoff=1.0):
        self.x_filter = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)
        self.y_filter = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)
   
    def filter(self, x, y, timestamp=None):
        return (
            self.x_filter.filter(x, timestamp),
            self.y_filter.filter(y, timestamp)
        )
   
    def reset(self):
        self.x_filter.reset()
        self.y_filter.reset()


# ═══════════════════════════════════════════════════════════════════════════
# ULTRA SMOOTH LINE BUFFER 🎯 (FIXED)
# ═══════════════════════════════════════════════════════════════════════════

class UltraSmoothLineBuffer:
    """Ultra-smooth line drawing with One Euro Filter and Catmull-Rom splines - FIXED"""
   
    def __init__(self):
        self.point_filter = Point2DFilter(
            freq=60.0, min_cutoff=1.0, beta=0.004, d_cutoff=1.0
        )
        self.raw_points = []
        self.smooth_points = []
        self.is_drawing = False
        self.jitter_threshold = 1.0
        self.last_smooth_x = None
        self.last_smooth_y = None
        self.last_drawn_index = 0
        self.last_time = None
        self.velocity = 0.0
   
    def start_stroke(self, x, y):
        self.raw_points = [(x, y)]
        self.smooth_points = [QPointF(x, y)]
        self.is_drawing = True
        self.last_smooth_x = x
        self.last_smooth_y = y
        self.last_drawn_index = 0
        self.last_time = time.time()
        self.velocity = 0.0
        self.point_filter.reset()
        self.point_filter.filter(x, y)
   
    def add_point(self, x, y):
        if not self.is_drawing:
            self.start_stroke(x, y)
            return True
       
        current_time = time.time()
       
        # Calculate velocity
        if self.last_time and self.last_smooth_x is not None:
            dt = current_time - self.last_time
            if dt > 0:
                dist = math.hypot(x - self.last_smooth_x, y - self.last_smooth_y)
                self.velocity = dist / dt
       
        # Apply One Euro Filter
        smooth_x, smooth_y = self.point_filter.filter(x, y, current_time)
       
        # Adaptive jitter threshold based on velocity
        if self.last_smooth_x is not None:
            dist = math.hypot(smooth_x - self.last_smooth_x, smooth_y - self.last_smooth_y)
           
            # Velocity-adaptive threshold
            if self.velocity < 50:
                adaptive_threshold = self.jitter_threshold * 2.0
            elif self.velocity < 200:
                adaptive_threshold = self.jitter_threshold * 1.0
            else:
                adaptive_threshold = self.jitter_threshold * 0.3
           
            if dist < adaptive_threshold:
                return False
       
        self.raw_points.append((x, y))
        self.smooth_points.append(QPointF(smooth_x, smooth_y))
        self.last_smooth_x = smooth_x
        self.last_smooth_y = smooth_y
        self.last_time = current_time
        return True
   
    def get_catmull_rom_path(self, start_idx=0):
        """Generate smooth Catmull-Rom spline path"""
        points = self.smooth_points
        n = len(points)
        if n < 2:
            return None
       
        path = QPainterPath()
       
        if start_idx == 0:
            path.moveTo(points[0])
            actual_start = 1
        else:
            actual_start = max(1, start_idx)
            if actual_start > 0 and actual_start <= n:
                path.moveTo(points[actual_start - 1])
       
        for i in range(actual_start, n):
            p0 = points[max(0, i - 2)]
            p1 = points[max(0, i - 1)]
            p2 = points[i]
            p3 = points[min(n - 1, i + 1)]
           
            # Catmull-Rom to Bezier conversion
            tension = 6.0
            c1x = p1.x() + (p2.x() - p0.x()) / tension
            c1y = p1.y() + (p2.y() - p0.y()) / tension
            c2x = p2.x() - (p3.x() - p1.x()) / tension
            c2y = p2.y() - (p3.y() - p1.y()) / tension
           
            path.cubicTo(c1x, c1y, c2x, c2y, p2.x(), p2.y())
       
        return path
   
    def get_new_segments_path(self):
        """Get only NEW segments that haven't been drawn yet"""
        n = len(self.smooth_points)
        if n < 2:
            return None, 0
       
        if self.last_drawn_index >= n - 1:
            return None, n
       
        # Start from 2 points before last_drawn_index for smooth connection
        start = max(0, self.last_drawn_index - 2)
       
        path = self.get_catmull_rom_path(start)
        return path, n
   
    def get_preview_path(self):
        """Get path for live preview - only uncommitted segments"""
        n = len(self.smooth_points)
        if n < 2:
            return None
       
        if self.last_drawn_index >= n - 1:
            return None
       
        preview_start = max(0, self.last_drawn_index)
        points = self.smooth_points[preview_start:]
       
        if len(points) < 2:
            return None
       
        path = QPainterPath()
        path.moveTo(points[0])
       
        for i in range(1, len(points)):
            if i < len(points) - 1:
                mid_x = (points[i].x() + points[i + 1].x()) / 2
                mid_y = (points[i].y() + points[i + 1].y()) / 2
                path.quadTo(points[i].x(), points[i].y(), mid_x, mid_y)
            else:
                path.lineTo(points[i])
       
        return path
   
    def update_drawn_index(self, index):
        """Update with proper bounds checking"""
        self.last_drawn_index = min(index, len(self.smooth_points))
   
    def get_full_path(self):
        return self.get_catmull_rom_path(0)
   
    def get_drawable_points(self):
        return self.smooth_points.copy()
   
    def get_last_point(self):
        if self.smooth_points:
            return self.smooth_points[-1]
        return None
   
    def get_last_two_points(self):
        if len(self.smooth_points) >= 2:
            return self.smooth_points[-2], self.smooth_points[-1]
        return None, None
   
    def end_stroke(self):
        self.is_drawing = False
   
    def clear(self):
        self.raw_points = []
        self.smooth_points = []
        self.is_drawing = False
        self.last_smooth_x = None
        self.last_smooth_y = None
        self.last_drawn_index = 0
        self.point_filter.reset()
   
    def has_points(self):
        return len(self.smooth_points) > 0
   
    def point_count(self):
        return len(self.smooth_points)


# ═══════════════════════════════════════════════════════════════════════════
# SMOOTH ERASER 🧽 (NEW - FIXED WITH INTERPOLATION)
# ═══════════════════════════════════════════════════════════════════════════

class SmoothEraser:
    """Smooth eraser with line interpolation - FIXES gaps when moving fast"""
   
    def __init__(self, alpha=0.6):
        self.alpha = alpha
        self.last_x = None
        self.last_y = None
        self.filter_x = None
        self.filter_y = None
   
    def reset(self):
        self.last_x = None
        self.last_y = None
        self.filter_x = None
        self.filter_y = None
   
    def update(self, x, y):
        """Apply smoothing and return smoothed position"""
        if self.filter_x is None:
            self.filter_x = x
            self.filter_y = y
        else:
            self.filter_x = self.alpha * x + (1 - self.alpha) * self.filter_x
            self.filter_y = self.alpha * y + (1 - self.alpha) * self.filter_y
       
        return self.filter_x, self.filter_y
   
    def get_interpolated_points(self, x, y, eraser_size):
        """
        Get list of points between last position and current position
        This ensures no gaps when moving fast!
        """
        sx, sy = self.update(x, y)
       
        points = []
       
        if self.last_x is None:
            # First point
            points.append((sx, sy))
        else:
            # Calculate distance
            dist = math.hypot(sx - self.last_x, sy - self.last_y)
           
            # Interpolate points based on eraser size
            step = max(eraser_size * 0.3, 2)
           
            if dist > step:
                num_points = int(dist / step) + 1
                for i in range(num_points + 1):
                    t = i / num_points
                    px = self.last_x + (sx - self.last_x) * t
                    py = self.last_y + (sy - self.last_y) * t
                    points.append((px, py))
            else:
                points.append((sx, sy))
       
        # Update last position
        self.last_x = sx
        self.last_y = sy
       
        return points


# ═══════════════════════════════════════════════════════════════════════════
# BRUSH RENDERER 🖌️
# ═══════════════════════════════════════════════════════════════════════════

class BrushRenderer:
    """Renders different brush effects"""
   
    @staticmethod
    def draw_normal(painter, path, color, size):
        """Normal smooth pen"""
        pen = QPen(color, size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
   
    @staticmethod
    def draw_highlighter(painter, path, color, size):
        """Highlighter - semi-transparent wide strokes"""
        highlight_color = QColor(color)
        highlight_color.setAlpha(80)
       
        pen = QPen(highlight_color, size * 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
   
    @staticmethod
    def draw_marker(painter, path, color, size):
        """Marker - bold solid strokes with slight transparency"""
        marker_color = QColor(color)
        marker_color.setAlpha(220)
       
        pen = QPen(marker_color, size * 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)


# ═══════════════════════════════════════════════════════════════════════════
# EYE BLINK DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class EyeBlinkDetector:
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
   
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None
        self.EAR_THRESHOLD = 0.21
        self.BLINK_TIME_MIN = 0.05
        self.LONG_BLINK_TIME = 0.6
        self.eye_close_start_time = None
        self.is_eye_closed = False
        self.last_blink_time = 0
        self.BLINK_COOLDOWN = 0.3
        self.DOUBLE_BLINK_WINDOW = 0.7
        self.blink_count = 0
        self.first_blink_time = 0
        self.blink_flash_time = 0
        self.FLASH_DURATION = 0.3
        self.last_ear = 1.0
        self.enabled = True
   
    def init(self):
        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.5, min_tracking_confidence=0.5)
            return True
        except:
            return False
   
    def release(self):
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None
   
    def set_enabled(self, enabled):
        self.enabled = enabled
   
    def _calculate_ear(self, eye_landmarks, landmarks):
        try:
            coords = [(landmarks[idx].x, landmarks[idx].y) for idx in eye_landmarks]
            v1 = math.hypot(coords[1][0] - coords[5][0], coords[1][1] - coords[5][1])
            v2 = math.hypot(coords[2][0] - coords[4][0], coords[2][1] - coords[4][1])
            h = math.hypot(coords[0][0] - coords[3][0], coords[0][1] - coords[3][1])
            return (v1 + v2) / (2.0 * h) if h != 0 else 1.0
        except:
            return 1.0
   
    def process(self, rgb_frame):
        if not self.face_mesh or not self.enabled:
            return None
        try:
            result = self.face_mesh.process(rgb_frame)
            current_time = time.time()
           
            if not result.multi_face_landmarks:
                self.eye_close_start_time = None
                self.is_eye_closed = False
                return None
           
            face_landmarks = result.multi_face_landmarks[0].landmark
            ear = (self._calculate_ear(self.LEFT_EYE, face_landmarks) +
                   self._calculate_ear(self.RIGHT_EYE, face_landmarks)) / 2.0
            self.last_ear = ear
           
            if self.blink_count > 0 and current_time - self.first_blink_time > self.DOUBLE_BLINK_WINDOW:
                if self.blink_count == 1:
                    self.blink_count = 0
                    self._flash()
                    return 'SINGLE'
                self.blink_count = 0
           
            if ear < self.EAR_THRESHOLD:
                if not self.is_eye_closed:
                    self.eye_close_start_time = current_time
                    self.is_eye_closed = True
                elif current_time - self.eye_close_start_time >= self.LONG_BLINK_TIME:
                    self.eye_close_start_time = None
                    self.is_eye_closed = False
                    self.blink_count = 0
                    self._flash()
                    return 'LONG'
            else:
                if self.is_eye_closed and self.eye_close_start_time:
                    duration = current_time - self.eye_close_start_time
                    if self.BLINK_TIME_MIN <= duration < self.LONG_BLINK_TIME:
                        if current_time - self.last_blink_time > self.BLINK_COOLDOWN:
                            self.last_blink_time = current_time
                            if self.blink_count == 0:
                                self.first_blink_time = current_time
                                self.blink_count = 1
                            elif self.blink_count == 1:
                                self.blink_count = 0
                                self._flash()
                                return 'DOUBLE'
                    self.eye_close_start_time = None
                self.is_eye_closed = False
            return None
        except:
            return None
   
    def _flash(self):
        self.blink_flash_time = time.time()
   
    def get_flash_alpha(self):
        if self.blink_flash_time == 0:
            return 0
        elapsed = time.time() - self.blink_flash_time
        if elapsed > self.FLASH_DURATION:
            self.blink_flash_time = 0
            return 0
        return int(200 * (1.0 - elapsed / self.FLASH_DURATION))
   
    def is_blinking(self):
        return self.is_eye_closed
   
    def get_close_duration(self):
        if self.is_eye_closed and self.eye_close_start_time:
            return time.time() - self.eye_close_start_time
        return 0


# ═══════════════════════════════════════════════════════════════════════════
# PRESENTATION CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════

class PresentationController(QObject):
    presentation_started = Signal()
    presentation_ended = Signal()
    slide_changed = Signal(int, int)
   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slides = []
        self.current_index = 0
        self.is_active = False
        self.annotations = {}
        self.last_nav_time = 0
        self.NAV_COOLDOWN = 0.8
   
    def load_slides(self, slides):
        self.slides = slides
        self.current_index = 0
        self.annotations = {i: QPixmap(s.size()) for i, s in enumerate(slides)}
        for p in self.annotations.values():
            p.fill(Qt.transparent)
   
    def start(self):
        if not self.slides:
            return False
        self.is_active = True
        self.current_index = 0
        self.presentation_started.emit()
        return True
   
    def stop(self):
        self.is_active = False
        self.presentation_ended.emit()
   
    def next_slide(self):
        if time.time() - self.last_nav_time < self.NAV_COOLDOWN:
            return False
        if self.current_index < len(self.slides) - 1:
            self.current_index += 1
            self.last_nav_time = time.time()
            self.slide_changed.emit(self.current_index, len(self.slides))
            return True
        return False
   
    def prev_slide(self):
        if time.time() - self.last_nav_time < self.NAV_COOLDOWN:
            return False
        if self.current_index > 0:
            self.current_index -= 1
            self.last_nav_time = time.time()
            self.slide_changed.emit(self.current_index, len(self.slides))
            return True
        return False
   
    def get_current_slide(self):
        if self.slides and 0 <= self.current_index < len(self.slides):
            return self.slides[self.current_index]
        return None
   
    def get_current_annotation(self):
        return self.annotations.get(self.current_index)
   
    def clear_current_annotation(self):
        if self.current_index in self.annotations:
            self.annotations[self.current_index].fill(Qt.transparent)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CANVAS - HOLOGRAM EDITION v3.5 ⬡ (FIXED)
# ═══════════════════════════════════════════════════════════════════════════

class DrawCanvas(QWidget):
    """
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  ⬡ HOLOGRAM EDITION v3.5 ⬡ FIXED                                      ║
    ║  SMOOTH DRAWING & ERASER • Brush Types • Shapes                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """
   
    exitToDesktop = Signal()
   
    # States
    STATE_IDLE = 'idle'
    STATE_DRAW = 'draw'
    STATE_ERASE = 'erase'
    STATE_COLOR = 'color'
    STATE_EXIT = 'exit'
    STATE_COMMAND = 'command'
    STATE_NAV_NEXT = 'nav_next'
    STATE_NAV_PREV = 'nav_prev'
    STATE_BRUSH_TYPE = 'brush_type'
    STATE_SHAPE = 'shape'
   
    CMD_BACKGROUND = 'background'
    CMD_UI = 'ui'
   
    def __init__(self, parent=None):
        super().__init__(None)
       
        screen = QGuiApplication.primaryScreen().geometry()
        self.screen_w = screen.width()
        self.screen_h = screen.height()
       
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        self.setFocusPolicy(Qt.StrongFocus)
       
        # Canvas
        self.canvas = QPixmap(self.screen_w, self.screen_h)
        self.canvas.fill(Qt.transparent)
       
        # Presentation
        self.presentation = PresentationController(self)
        self.presentation.presentation_started.connect(self._on_presentation_started)
        self.presentation.presentation_ended.connect(self._on_presentation_ended)
        self.presentation.slide_changed.connect(self._on_slide_changed)
        self.presentation_dialog = None
       
        # Display modes
        self.show_ui = True
        self.show_grid = True
        self.bg_mode = BackgroundMode.CYBER_GRADIENT
        self.grid_size = 50
       
        # ═══════════════════════════════════════════════════════════════
        # BRUSH TYPES 🖌️
        # ═══════════════════════════════════════════════════════════════
        self.brush_type = BrushType.NORMAL
        self.brush_switch_hold_start = None
        self.BRUSH_SWITCH_DELAY = 0.4
        self.brush_switch_progress = 0.0
        self.brush_switch_locked = False
       
        # ═══════════════════════════════════════════════════════════════
        # SHAPE TOOLS 🔷
        # ═══════════════════════════════════════════════════════════════
        self.shape_tool = ShapeTool.FREEHAND
        self.shape_start_point = None
        self.shape_current_point = None
        self.is_drawing_shape = False
        self.shape_preview = True
        self.shape_filled = False
       
        self.shape_switch_hold_start = None
        self.SHAPE_SWITCH_DELAY = 0.4
        self.shape_switch_progress = 0.0
        self.shape_switch_locked = False
       
        # ═══════════════════════════════════════════════════════════════
        # ULTRA SMOOTH DRAWING BUFFER 🎯 (FIXED)
        # ═══════════════════════════════════════════════════════════════
        self.line_buffer = UltraSmoothLineBuffer()
       
        # ═══════════════════════════════════════════════════════════════
        # SMOOTH ERASER 🧽 (FIXED)
        # ═══════════════════════════════════════════════════════════════
        self.erase_smoother = SmoothEraser(alpha=0.6)
        self.last_slide_index = -1
       
        # State management
        self.current_state = self.STATE_IDLE
        self.prev_state = self.STATE_IDLE
        self.drawing = False
        self.cursor_pos = None
       
        # Finger tracking
        self.finger_count = 0
        self.prev_finger_count = 0
        self.stable_count = 0
        self.stable_frames = 0
        self.FRAMES_TO_CONFIRM = 3
        self.debug_fingers = [False] * 5
       
        # Gesture stability
        self.gesture_history = []
        self.GESTURE_HISTORY_SIZE = 5
        self.last_confirmed_gesture = self.STATE_IDLE
       
        # Exit gesture
        self.exit_hold_start = None
        self.EXIT_HOLD_DURATION = 1.5
        self.exit_progress = 0.0
       
        # Navigation gesture
        self.nav_hold_start = None
        self.NAV_HOLD_DURATION = 0.6
        self.nav_progress = 0.0
        self.current_nav = None
        self.nav_locked = False
       
        # Command gestures
        self.command_hold_start = None
        self.COMMAND_HOLD_DURATION = 0.8
        self.command_progress = 0.0
        self.current_command = None
        self.command_locked = False
       
        # Eye blink
        self.eye_detector = EyeBlinkDetector()
        self.eye_enabled = False
       
        # Exit button
        self.exit_btn_rect = None
        self.exit_btn_hovered = False
        self.exit_btn_hover_start = None
        self.EXIT_BTN_HOVER_DURATION = 1.0
        self.exit_btn_progress = 0.0
       
        # Color palette
        self.color_switch_locked = False
        self.color_switch_hold_start = None
        self.COLOR_SWITCH_DELAY = 0.5
        self.color_switch_progress = 0.0
       
        self.colors = [
            ("CYAN", CyberColors.NEON_CYAN),
            ("MAGENTA", CyberColors.NEON_MAGENTA),
            ("PURPLE", CyberColors.NEON_PURPLE),
            ("GREEN", CyberColors.NEON_GREEN),
            ("ORANGE", CyberColors.NEON_ORANGE),
            ("YELLOW", CyberColors.NEON_YELLOW),
            ("BLUE", CyberColors.NEON_BLUE),
            ("WHITE", QColor(255, 255, 255)),
        ]
        self.color_idx = 0
        self.pen_color = self.colors[0][1]
        self.color_flash_time = 0
        self.COLOR_FLASH_DURATION = 0.5
       
        # Drawing settings
        self.pen_size = 6
        self.eraser_size = 50
       
        # Camera & MediaPipe
        self.cap = None
        self.hands = None
        self.mp_hands = mp.solutions.hands
       
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_frame)
       
        # Notification
        self.notification_text = ""
        self.notification_time = 0
        self.NOTIFICATION_DURATION = 2.0
       
        # Exit callback
        self._exit_callback = None
        self._exit_to_mode = "DESKTOP"
       
        # Animation
        self.anim_time = 0
       
        # ═══════════════════════════════════════════════════════════════
        # PERFORMANCE OPTIMIZATION
        # ═══════════════════════════════════════════════════════════════
        self._last_frame_time = 0
        self._frame_skip_threshold = 0.012  # ~80fps max
        self._ui_update_counter = 0
        self._ui_update_interval = 3
       
        self.hide()
   
    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════
   
    def set_exit_callback(self, callback):
        self._exit_callback = callback
   
    def start_draw(self):
        if self.drawing:
            return
       
        print("\n" + "⬡" * 40)
        print("⬡  HOLOGRAM EDITION v3.5 - FIXED  ⬡")
        print("⬡" * 40)
       
        self.drawing = True
        self._init_camera()
        self._init_mediapipe()
        self.eye_detector.init()
        self._reset_all_states()
        self.timer.start(16)
       
        self.raise_()
        self.showFullScreen()
        self.setFocus()
       
        self._show_notification("⬡ HOLOGRAM v3.5 - SMOOTH FIXED ⬡")
       
        print("  🖌️ BRUSH TYPES: Normal • Highlighter • Marker")
        print("  🧽 ERASER: Now with smooth interpolation!")
        print("  🤟 3 Fingers = Cycle Brush")
        print("  🤙 Pinky Up = Cycle Shapes")
        print("⬡" * 40 + "\n")
   
    def stop_draw(self):
        if not self.drawing:
            return
        if self.presentation.is_active:
            self.presentation.stop()
        self.drawing = False
        self.timer.stop()
        self._release_resources()
        self.eye_detector.release()
        self._lift_pen()
        self.hide()
        self.exitToDesktop.emit()
        if self._exit_callback:
            self._exit_callback(self._exit_to_mode)
   
    def open_presentation_dialog(self):
        self.hide()
        was_running = self.timer.isActive()
        if was_running:
            self.timer.stop()
        if self.cap:
            for _ in range(5):
                self.cap.read()
        self.presentation_dialog = PresentationDialog()
        self.presentation_dialog.presentation_started.connect(self._on_dialog_presentation_started)
        self.presentation_dialog.exec()
        self.showFullScreen()
        self.setFocus()
        if was_running:
            self.timer.start(16)
   
    def clear(self):
        if self.presentation.is_active:
            self.presentation.clear_current_annotation()
        else:
            self.canvas.fill(Qt.transparent)
        self._show_notification("⬡ CLEARED")
        self._lift_pen()
        self.update()
   
    def save_drawing(self):
        os.makedirs("drawings", exist_ok=True)
        timestamp = int(time.time())
        if self.presentation.is_active:
            slide = self.presentation.get_current_slide()
            annotation = self.presentation.get_current_annotation()
            if slide:
                combined = QPixmap(slide.size())
                painter = QPainter(combined)
                painter.drawPixmap(0, 0, slide)
                if annotation:
                    painter.drawPixmap(0, 0, annotation)
                painter.end()
                filename = f"drawings/slide_{self.presentation.current_index + 1}_{timestamp}.png"
                combined.save(filename, "PNG")
        else:
            filename = f"drawings/drawing_{timestamp}.png"
            self.canvas.save(filename, "PNG")
        self._show_notification("⬡ SAVED")
        return filename
   
    # ═══════════════════════════════════════════════════════════════════════
    # BRUSH TYPE FUNCTIONS 🖌️
    # ═══════════════════════════════════════════════════════════════════════
   
    def set_brush_type(self, brush):
        if 0 <= brush < BrushType.COUNT:
            self.brush_type = brush
            name = BrushType.NAMES[brush]
            icon = BrushType.ICONS[brush]
            self._show_notification(f"🖌️ BRUSH: {icon} {name}")
            self.update()
   
    def cycle_brush_type(self):
        next_brush = (self.brush_type + 1) % BrushType.COUNT
        self.set_brush_type(next_brush)
   
    # ═══════════════════════════════════════════════════════════════════════
    # SHAPE TOOL FUNCTIONS 🔷
    # ═══════════════════════════════════════════════════════════════════════
   
    def set_shape_tool(self, tool):
        if 0 <= tool < ShapeTool.COUNT:
            self.shape_tool = tool
            self._cancel_shape()
            name = ShapeTool.NAMES[tool]
            icon = ShapeTool.ICONS[tool]
            self._show_notification(f"🔷 SHAPE: {icon} {name}")
            self.update()
   
    def cycle_shape_tool(self):
        next_tool = (self.shape_tool + 1) % ShapeTool.COUNT
        self.set_shape_tool(next_tool)
   
    def toggle_shape_fill(self):
        self.shape_filled = not self.shape_filled
        mode = "FILLED" if self.shape_filled else "OUTLINE"
        self._show_notification(f"🔷 SHAPE: {mode}")
        self.update()
   
    def _start_shape(self, x, y):
        if self.shape_tool == ShapeTool.FREEHAND:
            return
        self.shape_start_point = QPointF(x, y)
        self.shape_current_point = QPointF(x, y)
        self.is_drawing_shape = True
   
    def _update_shape(self, x, y):
        if self.is_drawing_shape:
            self.shape_current_point = QPointF(x, y)
   
    def _finish_shape(self):
        if not self.is_drawing_shape or not self.shape_start_point or not self.shape_current_point:
            self._cancel_shape()
            return
       
        canvas = self._get_current_canvas()
        if not canvas:
            self._cancel_shape()
            return
       
        start = self.shape_start_point
        end = self.shape_current_point
       
        if self.presentation.is_active:
            start = self._screen_to_canvas(start)
            end = self._screen_to_canvas(end)
            if not start or not end:
                self._cancel_shape()
                return
       
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
       
        pen = QPen(self.pen_color, self.pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
       
        if self.shape_filled:
            fill_color = QColor(self.pen_color)
            fill_color.setAlpha(100)
            painter.setBrush(fill_color)
        else:
            painter.setBrush(Qt.NoBrush)
       
        self._draw_shape_on_painter(painter, start, end, self.shape_tool)
        painter.end()
       
        self._cancel_shape()
   
    def _cancel_shape(self):
        self.shape_start_point = None
        self.shape_current_point = None
        self.is_drawing_shape = False
   
    def _screen_to_canvas(self, point):
        if not self.presentation.is_active:
            return point
       
        slide = self.presentation.get_current_slide()
        if not slide:
            return None
       
        sw, sh = slide.width(), slide.height()
        scale = min((self.screen_w - 100) / sw, (self.screen_h - 200) / sh)
        disp_w, disp_h = int(sw * scale), int(sh * scale)
        disp_x = (self.screen_w - disp_w) // 2
        disp_y = (self.screen_h - disp_h) // 2 + 30
       
        x = (point.x() - disp_x) / scale
        y = (point.y() - disp_y) / scale
       
        return QPointF(max(0, min(sw, x)), max(0, min(sh, y)))
   
    def _draw_shape_on_painter(self, painter, start, end, tool):
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()
       
        if tool == ShapeTool.ARROW:
            self._draw_arrow(painter, start, end)
        elif tool == ShapeTool.RECTANGLE:
            rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            painter.drawRect(rect)
        elif tool == ShapeTool.SQUARE:
            size = min(abs(x2 - x1), abs(y2 - y1))
            sx = x1 if x2 >= x1 else x1 - size
            sy = y1 if y2 >= y1 else y1 - size
            painter.drawRect(QRectF(sx, sy, size, size))
        elif tool == ShapeTool.CIRCLE:
            radius = math.hypot(x2 - x1, y2 - y1)
            painter.drawEllipse(start, radius, radius)
   
    def _draw_arrow(self, painter, start, end):
        painter.drawLine(start, end)
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        arrow_size = max(15, self.pen_size * 3)
        angle1 = angle + math.pi * 0.85
        angle2 = angle - math.pi * 0.85
        p1 = QPointF(end.x() + arrow_size * math.cos(angle1), end.y() + arrow_size * math.sin(angle1))
        p2 = QPointF(end.x() + arrow_size * math.cos(angle2), end.y() + arrow_size * math.sin(angle2))
        arrow = QPolygonF([end, p1, p2])
        old_brush = painter.brush()
        painter.setBrush(self.pen_color)
        painter.drawPolygon(arrow)
        painter.setBrush(old_brush)
   
    # ═══════════════════════════════════════════════════════════════════════
    # TOGGLE FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════
   
    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self._show_notification(f"⬡ GRID: {'ON' if self.show_grid else 'OFF'}")
        self.update()
   
    def cycle_background(self):
        self.bg_mode = (self.bg_mode + 1) % BackgroundMode.COUNT
        self._show_notification(f"⬡ BG: {BackgroundMode.NAMES[self.bg_mode]}")
        self.update()
   
    def toggle_blink_detection(self):
        self.eye_enabled = not self.eye_enabled
        self.eye_detector.set_enabled(self.eye_enabled)
        self._show_notification(f"👁️ BLINK: {'ON' if self.eye_enabled else 'OFF'}")
        self.update()
   
    def toggle_ui(self):
        self.show_ui = not self.show_ui
        self._show_notification(f"⬡ HUD: {'ON' if self.show_ui else 'OFF'}")
        self.update()
   
    def next_slide(self):
        if self.presentation.is_active and self.presentation.next_slide():
            self._lift_pen()
            self._show_notification(f"▶ SLIDE {self.presentation.current_index + 1}/{len(self.presentation.slides)}")
   
    def prev_slide(self):
        if self.presentation.is_active and self.presentation.prev_slide():
            self._lift_pen()
            self._show_notification(f"◀ SLIDE {self.presentation.current_index + 1}/{len(self.presentation.slides)}")
   
    def exit_presentation(self):
        if self.presentation.is_active:
            self.presentation.stop()
            self._show_notification("⬡ PRESENTATION ENDED")
   
    def set_color(self, *args):
        if len(args) == 3:
            self.pen_color = QColor(int(args[0]), int(args[1]), int(args[2]))
        elif len(args) == 1 and isinstance(args[0], QColor):
            self.pen_color = QColor(args[0])
   
    def set_pen_size(self, size):
        self.pen_size = max(2, min(50, int(size)))
   
    def set_thickness(self, size):
        self.set_pen_size(size)
   
    def get_color(self):
        return self.pen_color
   
    def get_thickness(self):
        return self.pen_size
   
    def lift_pen(self):
        self._lift_pen()
   
    # ═══════════════════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════
   
    def _on_dialog_presentation_started(self, slides):
        self.presentation.load_slides(slides)
        self.presentation.start()
   
    def _on_presentation_started(self):
        self._show_notification(f"⬡ LOADED: {len(self.presentation.slides)} SLIDES")
        self.last_slide_index = 0
        self.update()
   
    def _on_presentation_ended(self):
        self.last_slide_index = -1
        self.update()
   
    def _on_slide_changed(self, current, total):
        self._lift_pen()
        self.last_slide_index = current
        self.update()
   
    # ═══════════════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════
   
    def _init_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
   
    def _init_mediapipe(self):
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=0.7, min_tracking_confidence=0.7)
   
    def _release_resources(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.hands:
            self.hands.close()
            self.hands = None
   
    def _reset_all_states(self):
        self.exit_hold_start = None
        self.exit_progress = 0.0
        self.nav_hold_start = None
        self.nav_progress = 0.0
        self.current_nav = None
        self.nav_locked = False
        self.command_hold_start = None
        self.command_progress = 0.0
        self.current_command = None
        self.command_locked = False
        self.color_switch_locked = False
        self.color_switch_hold_start = None
        self.color_switch_progress = 0.0
        self.shape_switch_hold_start = None
        self.shape_switch_progress = 0.0
        self.shape_switch_locked = False
        self.brush_switch_hold_start = None
        self.brush_switch_progress = 0.0
        self.brush_switch_locked = False
        self.stable_frames = 0
        self.last_slide_index = -1
        self.erase_smoother.reset()
        self.gesture_history = []
        self.last_confirmed_gesture = self.STATE_IDLE
        self._cancel_shape()
        self.line_buffer.clear()
        self._last_frame_time = 0
        self._ui_update_counter = 0
   
    def _show_notification(self, text):
        self.notification_text = text
        self.notification_time = time.time()
   
    # ═══════════════════════════════════════════════════════════════════════
    # FINGER DETECTION
    # ═══════════════════════════════════════════════════════════════════════
   
    def _is_finger_up(self, hand, tip, pip):
        return hand.landmark[tip].y < hand.landmark[pip].y - 0.03
   
    def _is_finger_up_strict(self, hand, tip, pip, mcp):
        t, p, m = hand.landmark[tip], hand.landmark[pip], hand.landmark[mcp]
        return t.y < p.y - 0.05 and t.y < m.y - 0.02 and abs(t.x - p.x) <= 0.10
   
    def _is_finger_down_strict(self, hand, tip, pip):
        return hand.landmark[tip].y >= hand.landmark[pip].y + 0.03
   
    def _is_thumb_out(self, hand):
        tt, ti, im, w = hand.landmark[4], hand.landmark[3], hand.landmark[5], hand.landmark[0]
        ext = tt.x < ti.x - 0.03 if w.x < im.x else tt.x > ti.x + 0.03
        return ext and abs(tt.x - im.x) > 0.06
   
    def _is_thumb_up(self, hand):
        tt, ti, tm = hand.landmark[4], hand.landmark[3], hand.landmark[2]
        if tt.y >= ti.y - 0.05 or tt.y >= tm.y:
            return False
        return all(self._is_finger_down_strict(hand, t, p) for t, p in [(8,6),(12,10),(16,14),(20,18)])
   
    def _is_thumb_down(self, hand):
        tt, ti, tm = hand.landmark[4], hand.landmark[3], hand.landmark[2]
        if tt.y <= ti.y + 0.05 or tt.y <= tm.y:
            return False
        return all(self._is_finger_down_strict(hand, t, p) for t, p in [(8,6),(12,10),(16,14),(20,18)])
   
    def _is_thumb_tucked(self, hand):
        tt = hand.landmark[4]
        px = (hand.landmark[5].x + hand.landmark[9].x) / 2
        py = (hand.landmark[5].y + hand.landmark[9].y) / 2
        return math.hypot(tt.x - px, tt.y - py) < 0.12
   
    def _count_fingers(self, hand):
        fingers = [self._is_thumb_out(hand)]
        for t, p, m in [(8,6,5), (12,10,9), (16,14,13), (20,18,17)]:
            fingers.append(self._is_finger_up_strict(hand, t, p, m))
        return sum(fingers), fingers
   
    def _get_stable_finger_count(self, raw):
        if raw == self.stable_count:
            self.stable_frames += 1
        else:
            self.stable_count = raw
            self.stable_frames = 1
        return self.stable_count if self.stable_frames >= self.FRAMES_TO_CONFIRM else self.prev_finger_count
   
    def _is_index_only(self, hand):
        if not self._is_finger_up_strict(hand, 8, 6, 5):
            return False
        if not all(self._is_finger_down_strict(hand, t, p) for t, p in [(12,10),(16,14),(20,18)]):
            return False
        return abs(hand.landmark[4].x - hand.landmark[5].x) < 0.10
   
    def _is_peace_sign(self, hand):
        if not (self._is_finger_up_strict(hand, 8, 6, 5) and self._is_finger_up_strict(hand, 12, 10, 9)):
            return False
        if not (hand.landmark[16].y > hand.landmark[14].y + 0.03 and hand.landmark[20].y > hand.landmark[18].y + 0.03):
            return False
        return abs(hand.landmark[8].x - hand.landmark[12].x) <= 0.15
   
    def _is_three_fingers_imr(self, hand):
        """Index + Middle + Ring fingers up (for brush type switching)"""
        if not all(self._is_finger_up_strict(hand, t, p, m) for t, p, m in [(8,6,5),(12,10,9),(16,14,13)]):
            return False
        if not self._is_finger_down_strict(hand, 20, 18):
            return False
        thumb_tip = hand.landmark[4]
        index_mcp = hand.landmark[5]
        thumb_not_extended = abs(thumb_tip.x - index_mcp.x) < 0.12
        return thumb_not_extended
   
    def _is_open_palm(self, hand):
        return sum([self._is_finger_up_strict(hand, 8, 6, 5), self._is_finger_up_strict(hand, 12, 10, 9),
                   self._is_finger_up_strict(hand, 16, 14, 13), self._is_finger_up(hand, 20, 18)]) >= 4
   
    def _is_fist(self, hand):
        if not all(self._is_finger_down_strict(hand, t, p) for t, p in [(8,6),(12,10),(16,14),(20,18)]):
            return False
        if not self._is_thumb_tucked(hand):
            return False
        tips = [hand.landmark[i] for i in [8, 12, 16, 20]]
        xs, ys = [t.x for t in tips], [t.y for t in tips]
        return (max(xs) - min(xs)) < 0.15 and (max(ys) - min(ys)) < 0.15
   
    def _is_pinky_only(self, hand):
        """🤙 PINKY ONLY - For shape cycling"""
        if not self._is_finger_up_strict(hand, 20, 18, 17):
            return False
        if not all(self._is_finger_down_strict(hand, t, p) for t, p in [(8,6),(12,10),(16,14)]):
            return False
        thumb_tip = hand.landmark[4]
        index_mcp = hand.landmark[5]
        thumb_not_extended = abs(thumb_tip.x - index_mcp.x) < 0.12
        return thumb_not_extended
   
    def _is_pinched(self, hand):
        tips = [hand.landmark[i] for i in [8, 12, 16, 20]]
        cx = sum(t.x for t in tips) / 4
        cy = sum(t.y for t in tips) / 4
        for t in tips:
            if math.hypot(t.x - cx, t.y - cy) > 0.08:
                return False
        th = hand.landmark[4]
        if math.hypot(th.x - cx, th.y - cy) > 0.12:
            return False
        return hand.landmark[8].y <= hand.landmark[6].y + 0.05 and cy < hand.landmark[9].y + 0.05
   
    def _is_ok_gesture(self, hand):
        if math.hypot(hand.landmark[4].x - hand.landmark[8].x, hand.landmark[4].y - hand.landmark[8].y) > 0.06:
            return False
        return sum([self._is_finger_up(hand, 12, 10), self._is_finger_up(hand, 16, 14), self._is_finger_up(hand, 20, 18)]) >= 2
   
    def _detect_command(self, hand):
        if self._is_pinched(hand):
            return self.CMD_BACKGROUND
        if self._is_ok_gesture(hand):
            return self.CMD_UI
        return None
   
    def _detect_nav(self, hand):
        if self._is_thumb_up(hand):
            return 'NEXT'
        if self._is_thumb_down(hand):
            return 'PREV'
        return None
   
    def _get_stable_gesture(self, gesture):
        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.GESTURE_HISTORY_SIZE:
            self.gesture_history.pop(0)
        if len(self.gesture_history) < 3:
            return self.last_confirmed_gesture
        counts = {}
        for g in self.gesture_history:
            counts[g] = counts.get(g, 0) + 1
        most = max(counts, key=counts.get)
        if counts[most] >= len(self.gesture_history) * 0.6:
            self.last_confirmed_gesture = most
            return most
        return self.last_confirmed_gesture
   
    def _detect_state(self, count, fingers, hand):
        if self._is_fist(hand):
            return self.STATE_EXIT
        if self.presentation.is_active:
            nav = self._detect_nav(hand)
            if nav == 'NEXT':
                return self.STATE_NAV_NEXT
            if nav == 'PREV':
                return self.STATE_NAV_PREV
        cmd = self._detect_command(hand)
        if cmd:
            return self.STATE_COMMAND
        if self._is_pinky_only(hand):
            return self.STATE_SHAPE
        if self._is_three_fingers_imr(hand):
            return self.STATE_BRUSH_TYPE
        if self._is_peace_sign(hand):
            return self.STATE_COLOR
        if self._is_index_only(hand):
            return self.STATE_DRAW
        if self._is_open_palm(hand):
            return self.STATE_ERASE
        return self.STATE_IDLE
   
    def _check_exit_hover(self, x, y):
        if not self.exit_btn_rect:
            return False
        bx, by, bw, bh = self.exit_btn_rect
        return bx <= x <= bx + bw and by <= y <= by + bh
   
    def _update_exit_hover(self, x, y):
        hovering = self._check_exit_hover(x, y)
        if hovering:
            if not self.exit_btn_hover_start:
                self.exit_btn_hover_start = time.time()
            self.exit_btn_progress = min(1.0, (time.time() - self.exit_btn_hover_start) / self.EXIT_BTN_HOVER_DURATION)
            if self.exit_btn_progress >= 1.0:
                self.stop_draw()
        else:
            self.exit_btn_hover_start = None
            self.exit_btn_progress = 0.0
        self.exit_btn_hovered = hovering
   
    def _get_slide_bounds(self):
        if not self.presentation.is_active:
            return None
        slide = self.presentation.get_current_slide()
        if not slide:
            return None
        sw, sh = slide.width(), slide.height()
        scale = min((self.screen_w - 100) / sw, (self.screen_h - 200) / sh)
        dw, dh = int(sw * scale), int(sh * scale)
        dx = (self.screen_w - dw) // 2
        dy = (self.screen_h - dh) // 2 + 30
        return QRectF(0, 0, sw, sh), (dx, dy, scale)
   
    def _is_in_slide(self, sx, sy):
        bounds = self._get_slide_bounds()
        if not bounds:
            return True
        rect, (dx, dy, scale) = bounds
        return rect.contains(QPointF((sx - dx) / scale, (sy - dy) / scale))
   
    # ═══════════════════════════════════════════════════════════════════════
    # MAIN PROCESSING
    # ═══════════════════════════════════════════════════════════════════════
   
    def _process_frame(self):
        if not self.cap or not self.drawing:
            return
       
        current_time = time.time()
        if current_time - self._last_frame_time < self._frame_skip_threshold:
            return
        self._last_frame_time = current_time
       
        self.anim_time = current_time
        self._ui_update_counter += 1
       
        ret, frame = self.cap.read()
        if not ret:
            return
       
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       
        # Eye blinks
        if self.eye_enabled:
            cmd = self.eye_detector.process(rgb)
            if cmd:
                if self.presentation.is_active:
                    if cmd == 'SINGLE':
                        self.next_slide()
                    elif cmd == 'DOUBLE':
                        self.prev_slide()
                    elif cmd == 'LONG':
                        self.exit_presentation()
                elif cmd in ('SINGLE', 'DOUBLE'):
                    self.open_presentation_dialog()
       
        # Hands
        result = self.hands.process(rgb)
       
        if not result.multi_hand_landmarks:
            if self.line_buffer.is_drawing:
                self._commit_smooth_line()
                self.line_buffer.end_stroke()
            if self.is_drawing_shape:
                self._finish_shape()
            self._lift_pen()
            self.cursor_pos = None
            self.current_state = self.STATE_IDLE
            self.finger_count = 0
            self._reset_gesture_states()
            self.update()
            return
       
        hand = result.multi_hand_landmarks[0]
        raw_count, fingers = self._count_fingers(hand)
        self.debug_fingers = fingers
        stable_count = self._get_stable_finger_count(raw_count)
        self.finger_count = stable_count
       
        raw_state = self._detect_state(stable_count, fingers, hand)
        new_state = self._get_stable_gesture(raw_state)
       
        ix = hand.landmark[8].x * self.screen_w
        iy = hand.landmark[8].y * self.screen_h
        px = hand.landmark[9].x * self.screen_w
        py = hand.landmark[9].y * self.screen_h
        wx = hand.landmark[0].x * self.screen_w
        wy = hand.landmark[0].y * self.screen_h
        tx = hand.landmark[4].x * self.screen_w
        ty = hand.landmark[4].y * self.screen_h
        pinky_x = hand.landmark[20].x * self.screen_w
        pinky_y = hand.landmark[20].y * self.screen_h
        mx = hand.landmark[12].x * self.screen_w
        my = hand.landmark[12].y * self.screen_h
       
        # Handle states
        self._handle_nav(new_state, tx, ty, current_time)
        self._handle_command(new_state, px, py, current_time, hand)
        self._handle_exit(new_state, wx, wy, current_time)
        self._handle_color(new_state, current_time)
        self._handle_brush_switch(new_state, mx, my, current_time)
        self._handle_shape_switch(new_state, pinky_x, pinky_y, current_time)
       
        # State transition
        if new_state != self.current_state:
            if self.line_buffer.is_drawing and new_state != self.STATE_DRAW:
                self._commit_smooth_line()
                self.line_buffer.end_stroke()
           
            if self.current_state == self.STATE_DRAW and self.is_drawing_shape:
                self._finish_shape()
           
            if new_state == self.STATE_DRAW:
                self.line_buffer.clear()
            elif new_state == self.STATE_ERASE:
                self.erase_smoother.reset()
            elif new_state not in (self.STATE_EXIT, self.STATE_COMMAND, self.STATE_NAV_NEXT,
                                   self.STATE_NAV_PREV, self.STATE_COLOR, self.STATE_BRUSH_TYPE, self.STATE_SHAPE):
                self._lift_pen()
       
        self.prev_state = self.current_state
        self.current_state = new_state
        self.prev_finger_count = stable_count
       
        # Execute state
        if self.current_state == self.STATE_DRAW:
            if not self.presentation.is_active or self._is_in_slide(ix, iy):
                self._handle_drawing(ix, iy)
            else:
                if self.line_buffer.is_drawing:
                    self._commit_smooth_line()
                    self.line_buffer.end_stroke()
                self._lift_pen()
            self.cursor_pos = (ix, iy, 'draw')
            self._update_exit_hover(ix, iy)
        elif self.current_state == self.STATE_ERASE:
            if not self.presentation.is_active or self._is_in_slide(px, py):
                self._erase_at(px, py)
            self.cursor_pos = (px, py, 'erase')
        elif self.current_state == self.STATE_COLOR:
            self.cursor_pos = (ix, iy, 'color')
        elif self.current_state == self.STATE_BRUSH_TYPE:
            self.cursor_pos = (mx, my, 'brush')
        elif self.current_state == self.STATE_SHAPE:
            self.cursor_pos = (pinky_x, pinky_y, 'shape')
        elif self.current_state == self.STATE_IDLE:
            self.cursor_pos = (ix, iy, 'idle')
            self._update_exit_hover(ix, iy)
       
        self.update()
   
    def _handle_brush_switch(self, state, x, y, current_time):
        """Handle three fingers gesture for brush type switching"""
        if state == self.STATE_BRUSH_TYPE:
            if not self.brush_switch_locked:
                if self.brush_switch_hold_start is None:
                    self.brush_switch_hold_start = current_time
                    self.brush_switch_progress = 0.0
                else:
                    elapsed = current_time - self.brush_switch_hold_start
                    self.brush_switch_progress = min(1.0, elapsed / self.BRUSH_SWITCH_DELAY)
                   
                    if self.brush_switch_progress >= 1.0:
                        self.cycle_brush_type()
                        self.brush_switch_locked = True
                        self.brush_switch_hold_start = None
                        self.brush_switch_progress = 0.0
        else:
            self.brush_switch_hold_start = None
            self.brush_switch_progress = 0.0
            self.brush_switch_locked = False
   
    def _handle_shape_switch(self, state, x, y, current_time):
        """Handle pinky gesture for shape switching"""
        if state == self.STATE_SHAPE:
            if not self.shape_switch_locked:
                if self.shape_switch_hold_start is None:
                    self.shape_switch_hold_start = current_time
                    self.shape_switch_progress = 0.0
                else:
                    elapsed = current_time - self.shape_switch_hold_start
                    self.shape_switch_progress = min(1.0, elapsed / self.SHAPE_SWITCH_DELAY)
                   
                    if self.shape_switch_progress >= 1.0:
                        self.cycle_shape_tool()
                        self.shape_switch_locked = True
                        self.shape_switch_hold_start = None
                        self.shape_switch_progress = 0.0
        else:
            self.shape_switch_hold_start = None
            self.shape_switch_progress = 0.0
            self.shape_switch_locked = False
   
    # ═══════════════════════════════════════════════════════════════════════
    # DRAWING FUNCTIONS WITH BRUSH TYPES 🖌️ (FIXED)
    # ═══════════════════════════════════════════════════════════════════════
   
    def _handle_drawing(self, x, y):
        """Handle drawing - freehand or shape"""
        if self.shape_tool == ShapeTool.FREEHAND:
            self._draw_with_brush(x, y)
        else:
            if not self.is_drawing_shape:
                self._start_shape(x, y)
            else:
                self._update_shape(x, y)
   
    def _draw_with_brush(self, x, y):
        """Draw with current brush type - FIXED"""
        # Check slide change
        if self.presentation.is_active and self.last_slide_index != self.presentation.current_index:
            if self.line_buffer.is_drawing:
                self._commit_smooth_line()
            self.line_buffer.end_stroke()
            self.line_buffer.clear()
            self._lift_pen()
            self.last_slide_index = self.presentation.current_index
            return
       
        # Add point to buffer
        point_added = self.line_buffer.add_point(x, y)
       
        if not point_added:
            return
       
        # Draw incremental smooth line
        if self.line_buffer.point_count() >= 2:
            self._draw_incremental_smooth_line()
   
    def _draw_incremental_smooth_line(self):
        """Draw smooth incremental line with current brush type - FIXED"""
        canvas = self._get_current_canvas()
        if not canvas:
            return
       
        path, new_index = self.line_buffer.get_new_segments_path()
        if path is None:
            return
       
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
       
        if self.presentation.is_active:
            slide = self.presentation.get_current_slide()
            if slide:
                sw, sh = slide.width(), slide.height()
                scale = min((self.screen_w - 100) / sw, (self.screen_h - 200) / sh)
                dx = (self.screen_w - int(sw * scale)) // 2
                dy = (self.screen_h - int(sh * scale)) // 2 + 30
               
                # Use painter transform for cleaner transformation
                painter.save()
                painter.translate(-dx / scale, -dy / scale)
                painter.scale(1.0 / scale, 1.0 / scale)
               
                self._render_brush_path(painter, path, self.pen_size)
               
                painter.restore()
            else:
                painter.end()
                return
        else:
            self._render_brush_path(painter, path, self.pen_size)
       
        painter.end()
       
        # Update drawn index with overlap for smooth connections
        self.line_buffer.update_drawn_index(max(0, new_index - 2))
   
    def _render_brush_path(self, painter, path, size):
        """Render path with current brush type"""
        if self.brush_type == BrushType.NORMAL:
            BrushRenderer.draw_normal(painter, path, self.pen_color, size)
        elif self.brush_type == BrushType.HIGHLIGHTER:
            BrushRenderer.draw_highlighter(painter, path, self.pen_color, size)
        elif self.brush_type == BrushType.MARKER:
            BrushRenderer.draw_marker(painter, path, self.pen_color, size)
        else:
            BrushRenderer.draw_normal(painter, path, self.pen_color, size)
   
    def _commit_smooth_line(self):
        """Commit the final smooth line when stroke ends"""
        pass  # Lines are drawn incrementally
   
    def _reset_gesture_states(self):
        self.color_switch_locked = False
        self.color_switch_hold_start = None
        self.color_switch_progress = 0.0
        self.command_locked = False
        self.command_hold_start = None
        self.command_progress = 0.0
        self.current_command = None
        self.nav_locked = False
        self.stable_frames = 0
        self.exit_hold_start = None
        self.exit_progress = 0.0
        self.nav_hold_start = None
        self.nav_progress = 0.0
        self.current_nav = None
        self.gesture_history = []
        self.shape_switch_hold_start = None
        self.shape_switch_progress = 0.0
        self.shape_switch_locked = False
        self.brush_switch_hold_start = None
        self.brush_switch_progress = 0.0
        self.brush_switch_locked = False
   
    def _handle_nav(self, state, tx, ty, ct):
        if state in (self.STATE_NAV_NEXT, self.STATE_NAV_PREV):
            nav = 'NEXT' if state == self.STATE_NAV_NEXT else 'PREV'
            if not self.nav_locked:
                if self.current_nav != nav:
                    self.current_nav = nav
                    self.nav_hold_start = ct
                    self.nav_progress = 0.0
                else:
                    self.nav_progress = min(1.0, (ct - self.nav_hold_start) / self.NAV_HOLD_DURATION)
                    if self.nav_progress >= 1.0:
                        self.next_slide() if nav == 'NEXT' else self.prev_slide()
                        self.nav_locked = True
                        self.nav_hold_start = None
                        self.nav_progress = 0.0
            self.cursor_pos = (tx, ty, 'nav')
        else:
            self.nav_hold_start = None
            self.nav_progress = 0.0
            self.current_nav = None
            self.nav_locked = False
   
    def _handle_command(self, state, px, py, ct, hand):
        if state == self.STATE_COMMAND:
            cmd = self._detect_command(hand)
            if cmd and not self.command_locked:
                if self.current_command != cmd:
                    self.current_command = cmd
                    self.command_hold_start = ct
                    self.command_progress = 0.0
                else:
                    self.command_progress = min(1.0, (ct - self.command_hold_start) / self.COMMAND_HOLD_DURATION)
                    if self.command_progress >= 1.0:
                        self._exec_command(cmd)
                        self.command_locked = True
                        self.command_hold_start = None
                        self.command_progress = 0.0
            self.cursor_pos = (px, py, 'command')
        else:
            self.command_hold_start = None
            self.command_progress = 0.0
            self.current_command = None
            self.command_locked = False
   
    def _handle_exit(self, state, wx, wy, ct):
        if state == self.STATE_EXIT:
            if not self.exit_hold_start:
                self.exit_hold_start = ct
            self.exit_progress = min(1.0, (ct - self.exit_hold_start) / self.EXIT_HOLD_DURATION)
            if self.exit_progress >= 1.0:
                self.stop_draw()
                return
            self.cursor_pos = (wx, wy, 'exit')
        else:
            self.exit_hold_start = None
            self.exit_progress = 0.0
   
    def _handle_color(self, state, ct):
        if state == self.STATE_COLOR:
            if not self.color_switch_locked:
                if not self.color_switch_hold_start:
                    self.color_switch_hold_start = ct
                    self.color_switch_progress = 0.0
                else:
                    self.color_switch_progress = min(1.0, (ct - self.color_switch_hold_start) / self.COLOR_SWITCH_DELAY)
                    if self.color_switch_progress >= 1.0:
                        self._next_color()
                        self.color_switch_locked = True
                        self.color_switch_hold_start = None
                        self.color_switch_progress = 0.0
        else:
            self.color_switch_hold_start = None
            self.color_switch_progress = 0.0
            self.color_switch_locked = False
   
    def _exec_command(self, cmd):
        if cmd == self.CMD_BACKGROUND:
            self.cycle_background()
        elif cmd == self.CMD_UI:
            self.toggle_ui()
   
    def _next_color(self):
        self.color_idx = (self.color_idx + 1) % len(self.colors)
        name, color = self.colors[self.color_idx]
        self.pen_color = color
        self.color_flash_time = time.time()
        self._show_notification(f"⬡ COLOR: {name}")
   
    def _get_current_canvas(self):
        return self.presentation.get_current_annotation() if self.presentation.is_active else self.canvas
   
    # ═══════════════════════════════════════════════════════════════════════
    # ERASER 🧽 (FIXED - WITH INTERPOLATION)
    # ═══════════════════════════════════════════════════════════════════════
   
    def _erase_at(self, x, y):
        """Eraser with smooth interpolation - FIXED to prevent gaps"""
        canvas = self._get_current_canvas()
        if not canvas:
            return
       
        # Get interpolated points (THIS IS THE KEY FIX!)
        points = self.erase_smoother.get_interpolated_points(x, y, self.eraser_size)
       
        if not points:
            return
       
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.transparent)
       
        if self.presentation.is_active:
            slide = self.presentation.get_current_slide()
            if slide:
                sw, sh = slide.width(), slide.height()
                scale = min((self.screen_w - 100) / sw, (self.screen_h - 200) / sh)
                dx = (self.screen_w - int(sw * scale)) // 2
                dy = (self.screen_h - int(sh * scale)) // 2 + 30
                eraser = self.eraser_size / scale
               
                # Draw eraser at ALL interpolated points
                for px, py in points:
                    pt = QPointF((px - dx) / scale, (py - dy) / scale)
                    painter.drawEllipse(pt, eraser, eraser)
            else:
                painter.end()
                return
        else:
            eraser = self.eraser_size
            # Draw eraser at ALL interpolated points
            for px, py in points:
                painter.drawEllipse(QPointF(px, py), eraser, eraser)
       
        painter.end()
   
    def _lift_pen(self):
        if self.line_buffer.is_drawing:
            self._commit_smooth_line()
            self.line_buffer.end_stroke()
        self.line_buffer.clear()
        self.erase_smoother.reset()
        if self.is_drawing_shape:
            self._finish_shape()
   
    # ═══════════════════════════════════════════════════════════════════════
    # BACKGROUND PAINTING
    # ═══════════════════════════════════════════════════════════════════════
   
    def _paint_background(self, p):
        mode = self.bg_mode
        if mode == BackgroundMode.TRANSPARENT:
            p.fillRect(self.rect(), Qt.transparent)
        elif mode == BackgroundMode.VOID:
            p.fillRect(self.rect(), QColor(2, 4, 10))
        elif mode == BackgroundMode.CYBER_GRADIENT:
            g = QLinearGradient(0, 0, self.screen_w, self.screen_h)
            g.setColorAt(0, QColor(5, 20, 40))
            g.setColorAt(0.5, QColor(15, 10, 35))
            g.setColorAt(1, QColor(5, 20, 40))
            p.fillRect(self.rect(), g)
        elif mode == BackgroundMode.FROSTED:
            p.fillRect(self.rect(), QColor(20, 30, 50, 180))
   
    def _paint_grid(self, p):
        if not self.show_grid:
            return
        color = QColor(0, 255, 255, 20)
        p.setPen(QPen(color, 1))
        for x in range(0, self.screen_w, self.grid_size):
            p.drawLine(x, 0, x, self.screen_h)
        for y in range(0, self.screen_h, self.grid_size):
            p.drawLine(0, y, self.screen_w, y)
   
    # ═══════════════════════════════════════════════════════════════════════
    # PAINT EVENT
    # ═══════════════════════════════════════════════════════════════════════
   
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
       
        # Background
        if self.presentation.is_active:
            p.fillRect(self.rect(), CyberColors.BG_VOID)
            slide = self.presentation.get_current_slide()
            if slide:
                sw, sh = slide.width(), slide.height()
                scale = min((self.screen_w - 100) / sw, (self.screen_h - 200) / sh)
                dw, dh = int(sw * scale), int(sh * scale)
                dx = (self.screen_w - dw) // 2
                dy = (self.screen_h - dh) // 2 + 30
               
                glow = QRadialGradient(dx + dw//2, dy + dh//2, max(dw, dh) * 0.6)
                glow.setColorAt(0, CyberColors.GLOW_CYAN)
                glow.setColorAt(1, Qt.transparent)
                p.setPen(Qt.NoPen)
                p.setBrush(glow)
                p.drawRect(dx - 50, dy - 50, dw + 100, dh + 100)
               
                p.drawPixmap(dx, dy, slide.scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                ann = self.presentation.get_current_annotation()
                if ann:
                    p.drawPixmap(dx, dy, ann.scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self._paint_background(p)
            self._paint_grid(p)
            p.drawPixmap(0, 0, self.canvas)
       
        # Live stroke preview
        if self.line_buffer.is_drawing and self.line_buffer.point_count() >= 2:
            self._paint_live_stroke(p)
       
        # Shape preview
        if self.is_drawing_shape and self.shape_start_point and self.shape_current_point:
            self._paint_shape_preview(p)
       
        # Cursor
        if self.cursor_pos and self.drawing:
            self._paint_cursor(p, *self.cursor_pos)
       
        # UI
        if self.drawing:
            if self.current_state == self.STATE_DRAW and self.line_buffer.is_drawing:
                self._paint_minimal_ui(p)
            elif self.show_ui:
                self._paint_ui(p)
            else:
                self._paint_minimal_ui(p)
       
        # Notification
        if self.notification_time > 0:
            elapsed = time.time() - self.notification_time
            if elapsed < self.NOTIFICATION_DURATION:
                self._paint_notification(p, elapsed)
       
        # Progress bars
        if self.current_state == self.STATE_COMMAND and self.command_progress > 0:
            self._paint_progress(p, "COMMAND", self.command_progress, CyberColors.NEON_PURPLE)
        if self.current_state in (self.STATE_NAV_NEXT, self.STATE_NAV_PREV) and self.nav_progress > 0:
            self._paint_progress(p, "NEXT" if self.current_nav == 'NEXT' else "PREV", self.nav_progress, CyberColors.NEON_CYAN)
        if self.current_state == self.STATE_SHAPE and self.shape_switch_progress > 0:
            self._paint_progress(p, "SWITCH SHAPE", self.shape_switch_progress, CyberColors.NEON_GREEN)
        if self.current_state == self.STATE_BRUSH_TYPE and self.brush_switch_progress > 0:
            self._paint_progress(p, "SWITCH BRUSH", self.brush_switch_progress, CyberColors.NEON_ORANGE)
       
        # Eye indicator
        if self.drawing and self.eye_enabled and self.show_ui:
            self._paint_eye(p)
       
        p.end()
   
    def _paint_live_stroke(self, p):
        """Paint ONLY the last few segments as preview"""
        path = self.line_buffer.get_preview_path()
        if path is None:
            return
       
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)
       
        if self.brush_type == BrushType.HIGHLIGHTER:
            highlight_color = QColor(self.pen_color)
            highlight_color.setAlpha(80)
            p.setPen(QPen(highlight_color, self.pen_size * 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)
        elif self.brush_type == BrushType.MARKER:
            marker_color = QColor(self.pen_color)
            marker_color.setAlpha(220)
            p.setPen(QPen(marker_color, self.pen_size * 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)
        else:
            p.setPen(QPen(self.pen_color, self.pen_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)
       
        p.restore()
   
    def _paint_shape_preview(self, p):
        """Paint shape preview while drawing"""
        p.save()
        pen = QPen(self.pen_color, self.pen_size, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
       
        if self.shape_filled:
            fill = QColor(self.pen_color)
            fill.setAlpha(50)
            p.setBrush(fill)
        else:
            p.setBrush(Qt.NoBrush)
       
        self._draw_shape_on_painter(p, self.shape_start_point, self.shape_current_point, self.shape_tool)
        p.restore()
   
    def _paint_cursor(self, p, x, y, mode):
        if mode == 'draw':
            brush_icon = BrushType.ICONS[self.brush_type]
            p.setFont(QFont("Segoe UI Emoji", 16))
            p.setPen(self.pen_color)
            p.drawText(QPointF(x + 18, y - 18), brush_icon)
           
            if self.shape_tool != ShapeTool.FREEHAND:
                icon = ShapeTool.ICONS[self.shape_tool]
                p.drawText(QPointF(x + 18, y + 5), icon)
           
            glow = QColor(self.pen_color)
            glow.setAlpha(50)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
           
            cursor_size = self.pen_size
            if self.brush_type == BrushType.HIGHLIGHTER:
                cursor_size = self.pen_size * 3
            elif self.brush_type == BrushType.MARKER:
                cursor_size = self.pen_size * 1.5
           
            p.drawEllipse(QPointF(x, y), cursor_size, cursor_size)
           
            p.setPen(QPen(self.pen_color, 2))
            p.drawLine(int(x) - 15, int(y), int(x) - 5, int(y))
            p.drawLine(int(x) + 5, int(y), int(x) + 15, int(y))
            p.drawLine(int(x), int(y) - 15, int(x), int(y) - 5)
            p.drawLine(int(x), int(y) + 5, int(x), int(y) + 15)
               
        elif mode == 'erase':
            p.setPen(QPen(CyberColors.NEON_MAGENTA, 2, Qt.DashLine))
            p.setBrush(QColor(255, 0, 128, 30))
            s = self.eraser_size
            p.drawEllipse(QPointF(x, y), s, s)
            p.setPen(QPen(CyberColors.NEON_MAGENTA, 3))
            p.drawLine(int(x - 15), int(y - 15), int(x + 15), int(y + 15))
            p.drawLine(int(x + 15), int(y - 15), int(x - 15), int(y + 15))
           
        elif mode == 'color':
            pulse = (math.sin(self.anim_time * 5) + 1) / 2
            s = 28 + pulse * 8
            p.setPen(QPen(CyberColors.NEON_PURPLE, 3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(x, y), s, s)
            if self.color_switch_progress > 0:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 255, 128, 100))
                p.drawPie(QRectF(x-s, y-s, s*2, s*2), 90*16, -int(self.color_switch_progress * 360 * 16))
            p.setPen(QPen(CyberColors.TEXT_BRIGHT, 2))
            p.setBrush(self.pen_color)
            p.drawEllipse(QPointF(x, y), 12, 12)
           
        elif mode == 'brush':
            pulse = (math.sin(self.anim_time * 6) + 1) / 2
            s = 40 + pulse * 10
           
            p.setPen(QPen(CyberColors.NEON_ORANGE, 3))
            p.setBrush(QColor(255, 128, 0, 40))
            p.drawEllipse(QPointF(x, y), s, s)
           
            icon = BrushType.ICONS[self.brush_type]
            p.setFont(QFont("Segoe UI Emoji", 24))
            p.setPen(CyberColors.NEON_ORANGE)
            p.drawText(QPointF(x - 16, y + 10), icon)
           
            if self.brush_switch_progress > 0:
                p.setPen(QPen(CyberColors.NEON_ORANGE, 5))
                fill_angle = int(self.brush_switch_progress * 360 * 16)
                p.drawArc(QRectF(x - s - 5, y - s - 5, (s + 5) * 2, (s + 5) * 2), 90 * 16, -fill_angle)
           
        elif mode == 'shape':
            pulse = (math.sin(self.anim_time * 6) + 1) / 2
            s = 35 + pulse * 10
           
            p.setPen(QPen(CyberColors.NEON_GREEN, 3))
            p.setBrush(QColor(0, 255, 128, 40))
            p.drawEllipse(QPointF(x, y), s, s)
           
            icon = ShapeTool.ICONS[self.shape_tool]
            p.setFont(QFont("Segoe UI Emoji", 24))
            p.drawText(QPointF(x - 16, y + 10), icon)
           
            if self.shape_switch_progress > 0:
                p.setPen(QPen(CyberColors.NEON_GREEN, 5))
                fill_angle = int(self.shape_switch_progress * 360 * 16)
                p.drawArc(QRectF(x - s - 5, y - s - 5, (s + 5) * 2, (s + 5) * 2), 90 * 16, -fill_angle)
           
        elif mode == 'nav':
            p.setPen(QPen(CyberColors.NEON_CYAN, 3))
            p.setBrush(QColor(0, 255, 255, 40))
            p.drawEllipse(QPointF(x, y), 35, 35)
            p.setFont(QFont("Consolas", 28, QFont.Bold))
            p.setPen(CyberColors.NEON_CYAN)
            p.drawText(QPointF(x - 12, y + 10), "▲" if self.current_nav == 'NEXT' else "▼")
           
        elif mode == 'command':
            p.setPen(QPen(CyberColors.NEON_PURPLE, 3))
            p.setBrush(QColor(180, 60, 255, 40))
            p.drawEllipse(QPointF(x, y), 40, 40)
            p.setFont(QFont("Consolas", 11, QFont.Bold))
            p.setPen(CyberColors.NEON_PURPLE)
            p.drawText(QPointF(x - 14, y + 5), "BG" if self.current_command == self.CMD_BACKGROUND else "UI")
           
        elif mode == 'exit':
            ps = 40 + int(20 * self.exit_progress)
            p.setPen(QPen(CyberColors.NEON_MAGENTA, 4))
            p.setBrush(QColor(255, 0, 128, 60))
            p.drawEllipse(QPointF(x, y), ps, ps)
            bw = 60
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(50, 20, 40))
            p.drawRect(int(x - bw//2), int(y + 30), bw, 8)
            p.setBrush(CyberColors.NEON_MAGENTA)
            p.drawRect(int(x - bw//2), int(y + 30), int(bw * self.exit_progress), 8)
            p.setFont(QFont("Consolas", 14, QFont.Bold))
            p.setPen(CyberColors.TEXT_DANGER)
            p.drawText(QPointF(x - 20, y + 5), "EXIT")
           
        else:  # idle
            pulse = (math.sin(self.anim_time * 3) + 1) / 2
            s = 10 + pulse * 4
            p.setPen(QPen(CyberColors.NEON_CYAN, 2))
            p.setBrush(QColor(0, 255, 255, 30))
            p.drawEllipse(QPointF(x, y), s, s)
   
    def _paint_eye(self, p):
        x, y = self.screen_w - 70, 175
        p.setPen(QPen(CyberColors.BORDER_BRIGHT, 2))
        p.setBrush(CyberColors.BG_PANEL)
        p.drawRoundedRect(x - 40, y - 22, 95, 90, 5, 5)
       
        if self.eye_detector.is_blinking():
            dur = self.eye_detector.get_close_duration()
            col = CyberColors.NEON_MAGENTA if dur >= 0.4 else CyberColors.NEON_ORANGE
            p.setPen(QPen(col, 3 if dur >= 0.4 else 2))
            p.drawLine(int(x - 20), int(y + 5), int(x + 20), int(y + 5))
        else:
            p.setPen(QPen(CyberColors.NEON_CYAN, 2))
            p.setBrush(QColor(0, 255, 255, 60))
            p.drawEllipse(QPointF(x, y + 5), 18, 12)
            p.setPen(Qt.NoPen)
            p.setBrush(CyberColors.BG_DARK)
            p.drawEllipse(QPointF(x, y + 5), 6, 6)
            p.setBrush(CyberColors.NEON_CYAN)
            p.drawEllipse(QPointF(x, y + 5), 2, 2)
       
        p.setPen(CyberColors.TEXT_DIM)
        p.setFont(QFont("Consolas", 7))
        if self.presentation.is_active:
            p.drawText(int(x - 35), int(y + 35), "1x → NEXT")
            p.drawText(int(x - 35), int(y + 47), "2x → PREV")
            p.drawText(int(x - 35), int(y + 59), "HOLD → EXIT")
        else:
            p.drawText(int(x - 35), int(y + 40), "BLINK →")
            p.drawText(int(x - 35), int(y + 52), "OPEN PRES")
   
    def _paint_progress(self, p, text, progress, color):
        bw, bh = 340, 30
        bx = (self.screen_w - bw) // 2
        by = self.screen_h // 2 + 95
       
        p.setPen(QPen(color, 2))
        p.setBrush(CyberColors.BG_PANEL)
        p.drawRoundedRect(bx - 20, by - 40, bw + 40, bh + 55, 8, 8)
       
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.setPen(color)
        p.drawText(QPointF(bx, by - 18), f"⬡ {text}")
       
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 30, 50))
        p.drawRoundedRect(bx, by, bw, bh, 4, 4)
       
        g = QLinearGradient(bx, by, bx + int(bw * progress), by)
        g.setColorAt(0, color)
        fc = QColor(color)
        fc.setAlpha(150)
        g.setColorAt(1, fc)
        p.setBrush(g)
        p.drawRoundedRect(bx, by, int(bw * progress), bh, 4, 4)
       
        p.setPen(CyberColors.TEXT_BRIGHT)
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.drawText(QPointF(bx + bw // 2 - 15, by + 21), f"{int(progress * 100)}%")
   
    def _paint_notification(self, p, elapsed):
        text = self.notification_text
        p.setFont(QFont("Consolas", 14, QFont.Bold))
        tw = p.fontMetrics().horizontalAdvance(text) + 60
        x, y = (self.screen_w - tw) // 2, 85
       
        alpha = 250 if elapsed <= self.NOTIFICATION_DURATION - 0.5 else int(250 * (1.0 - (elapsed - (self.NOTIFICATION_DURATION - 0.5)) / 0.5))
       
        pc = QColor(CyberColors.BG_PANEL)
        pc.setAlpha(alpha)
        bc = QColor(CyberColors.NEON_CYAN)
        bc.setAlpha(alpha)
       
        p.setPen(QPen(bc, 2))
        p.setBrush(pc)
        p.drawRoundedRect(x, y, tw, 50, 8, 8)
       
        tc = QColor(CyberColors.TEXT_BRIGHT)
        tc.setAlpha(alpha)
        p.setPen(tc)
        p.drawText(x + 30, y + 32, text)
   
    def _paint_minimal_ui(self, p):
        bw, bh = 100, 44
        bx, by = self.screen_w - bw - 25, 25
        self.exit_btn_rect = (bx, by, bw, bh)
       
        if self.exit_btn_hovered:
            p.setBrush(QColor(255, 0, 100, 200))
            border = CyberColors.NEON_MAGENTA
        else:
            p.setBrush(CyberColors.BG_PANEL)
            border = CyberColors.BORDER_DIM
       
        p.setPen(QPen(border, 2))
        p.drawRoundedRect(bx, by, bw, bh, 5, 5)
       
        p.setPen(CyberColors.TEXT_BRIGHT)
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.drawText(QPointF(bx + 15, by + 29), "◀ EXIT")
       
        p.setPen(QPen(CyberColors.NEON_CYAN, 2))
        p.setBrush(self.pen_color)
        p.drawEllipse(20, 20, 30, 30)
       
        brush_icon = BrushType.ICONS[self.brush_type]
        p.setFont(QFont("Segoe UI Emoji", 14))
        p.drawText(60, 42, brush_icon)
       
        shape_icon = ShapeTool.ICONS[self.shape_tool]
        p.drawText(90, 42, shape_icon)
       
        if self.presentation.is_active:
            p.setPen(CyberColors.NEON_CYAN)
            p.setFont(QFont("Consolas", 12, QFont.Bold))
            p.drawText(120, 40, f"⬡ {self.presentation.current_index + 1}/{len(self.presentation.slides)}")
   
    def _paint_ui(self, p):
        # HEADER
        hh = 55
        hg = QLinearGradient(0, 0, self.screen_w, 0)
        hg.setColorAt(0, QColor(0, 255, 255, 20))
        hg.setColorAt(0.5, QColor(180, 60, 255, 30))
        hg.setColorAt(1, QColor(0, 255, 255, 20))
        p.setPen(Qt.NoPen)
        p.setBrush(hg)
        p.drawRect(0, 0, self.screen_w, hh)
        p.setPen(QPen(CyberColors.NEON_CYAN, 1))
        p.drawLine(0, hh, self.screen_w, hh)
       
        p.setFont(QFont("Consolas", 13, QFont.Bold))
        p.setPen(CyberColors.NEON_CYAN)
        p.drawText(20, 25, "⬡ HOLOGRAM v3.5 - SMOOTH FIXED ⬡")
       
        brush_name = BrushType.NAMES[self.brush_type]
        brush_icon = BrushType.ICONS[self.brush_type]
        shape_name = ShapeTool.NAMES[self.shape_tool]
        shape_icon = ShapeTool.ICONS[self.shape_tool]
        p.setFont(QFont("Consolas", 9))
        p.setPen(CyberColors.TEXT_DIM)
        p.drawText(20, 42, f"BRUSH: {brush_icon} {brush_name} │ SHAPE: {shape_icon} {shape_name} │ BG: {BackgroundMode.NAMES[self.bg_mode][:8]}")
       
        # EXIT BUTTON
        bw, bh = 110, 40
        bx, by = self.screen_w - bw - 20, 8
        self.exit_btn_rect = (bx, by, bw, bh)
       
        if self.exit_btn_hovered:
            g = QLinearGradient(bx, by, bx + bw, by)
            g.setColorAt(0, QColor(255, 0, 80, 220))
            g.setColorAt(1, QColor(180, 0, 60, 220))
            p.setBrush(g)
            border = CyberColors.NEON_MAGENTA
        else:
            p.setBrush(CyberColors.BG_PANEL)
            border = CyberColors.BORDER_DIM
       
        p.setPen(QPen(border, 2))
        p.drawRoundedRect(bx, by, bw, bh, 5, 5)
        p.setPen(CyberColors.TEXT_BRIGHT)
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.drawText(QPointF(bx + 18, by + 26), "◀ EXIT")
       
        # BRUSH TYPE PANEL
        bp_x, bp_y = 20, 70
        bp_size = 36
        bp_spacing = 6
        bp_w = BrushType.COUNT * (bp_size + bp_spacing) + bp_spacing + 10
        bp_h = bp_size + 45
       
        p.setPen(QPen(CyberColors.NEON_ORANGE, 2))
        p.setBrush(CyberColors.BG_PANEL)
        p.drawRoundedRect(bp_x - 10, bp_y - 10, bp_w, bp_h, 5, 5)
       
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.setPen(CyberColors.NEON_ORANGE)
        p.drawText(bp_x, bp_y + 8, "🖌️ BRUSH (🤟 3 Fingers)")
       
        for i in range(BrushType.COUNT):
            bsx = bp_x + i * (bp_size + bp_spacing)
            bsy = bp_y + 15
            active = (i == self.brush_type)
           
            if active:
                p.setPen(QPen(CyberColors.NEON_ORANGE, 3))
                pulse = (math.sin(self.anim_time * 4) + 1) / 2
                p.setBrush(QColor(255, 128, 0, 40 + int(pulse * 40)))
            else:
                p.setPen(QPen(CyberColors.BORDER_DIM, 1))
                p.setBrush(CyberColors.BG_DARK)
           
            p.drawRoundedRect(bsx, bsy, bp_size, bp_size, 4, 4)
           
            p.setFont(QFont("Segoe UI Emoji", 14))
            p.setPen(CyberColors.NEON_ORANGE if active else CyberColors.TEXT_DIM)
            p.drawText(bsx + 8, bsy + 24, BrushType.ICONS[i])
       
        # SHAPE TOOL PANEL
        sp_x = bp_x + bp_w + 15
        sp_y = 70
        sp_size = 32
        sp_spacing = 5
        sp_w = ShapeTool.COUNT * (sp_size + sp_spacing) + sp_spacing + 10
        sp_h = sp_size + 45
       
        p.setPen(QPen(CyberColors.NEON_GREEN, 2))
        p.setBrush(CyberColors.BG_PANEL)
        p.drawRoundedRect(sp_x - 10, sp_y - 10, sp_w, sp_h, 5, 5)
       
        p.setFont(QFont("Consolas", 9, QFont.Bold))
        p.setPen(CyberColors.NEON_GREEN)
        p.drawText(sp_x, sp_y + 8, "🔷 SHAPES (🤙 Pinky)")
       
        for i in range(ShapeTool.COUNT):
            sx = sp_x + i * (sp_size + sp_spacing)
            sy = sp_y + 15
            active = (i == self.shape_tool)
           
            if active:
                p.setPen(QPen(CyberColors.NEON_GREEN, 2))
                p.setBrush(QColor(0, 255, 128, 40))
            else:
                p.setPen(QPen(CyberColors.BORDER_DIM, 1))
                p.setBrush(CyberColors.BG_DARK)
           
            p.drawRoundedRect(sx, sy, sp_size, sp_size, 3, 3)
           
            p.setFont(QFont("Segoe UI Emoji", 12))
            p.setPen(CyberColors.NEON_GREEN if active else CyberColors.TEXT_DIM)
            p.drawText(sx + 6, sy + 22, ShapeTool.ICONS[i])
       
        # COLOR PALETTE / SLIDE INFO
        if not self.presentation.is_active:
            cp_x = sp_x + sp_w + 15
            cp_y = 70
            cs = 24
            csp = 4
            cp_w = len(self.colors) * (cs + csp) + csp + 10
            cp_h = cs + 45
           
            p.setPen(QPen(CyberColors.NEON_PURPLE, 2))
            p.setBrush(CyberColors.BG_PANEL)
            p.drawRoundedRect(cp_x - 10, cp_y - 10, cp_w, cp_h, 5, 5)
           
            p.setFont(QFont("Consolas", 9, QFont.Bold))
            p.setPen(CyberColors.NEON_PURPLE)
            p.drawText(cp_x, cp_y + 8, "✌️ COLOR")
           
            for i, (name, color) in enumerate(self.colors):
                cx = cp_x + i * (cs + csp)
                cy = cp_y + 15
                active = (i == self.color_idx)
               
                if active:
                    p.setPen(QPen(CyberColors.NEON_CYAN, 2))
                else:
                    p.setPen(QPen(CyberColors.BORDER_DIM, 1))
               
                p.setBrush(color)
                p.drawEllipse(cx, cy, cs, cs)
        else:
            ps_x, ps_y = sp_x + sp_w + 15, 70
            p.setPen(QPen(CyberColors.NEON_CYAN, 2))
            p.setBrush(CyberColors.BG_PANEL)
            p.drawRoundedRect(ps_x, ps_y, 180, 55, 5, 5)
           
            p.setFont(QFont("Consolas", 13, QFont.Bold))
            p.setPen(CyberColors.NEON_CYAN)
            p.drawText(ps_x + 15, ps_y + 26, f"⬡ SLIDE {self.presentation.current_index + 1:02d}/{len(self.presentation.slides):02d}")
           
            prog = (self.presentation.current_index + 1) / len(self.presentation.slides)
            pw = 150
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(30, 50, 70))
            p.drawRoundedRect(ps_x + 15, ps_y + 38, pw, 6, 3, 3)
            pg = QLinearGradient(ps_x + 15, ps_y + 38, ps_x + 15 + int(pw * prog), ps_y + 38)
            pg.setColorAt(0, CyberColors.NEON_CYAN)
            pg.setColorAt(1, CyberColors.NEON_PURPLE)
            p.setBrush(pg)
            p.drawRoundedRect(ps_x + 15, ps_y + 38, int(pw * prog), 6, 3, 3)
       
        # STATUS PANEL
        st_x, st_y = self.screen_w - 195, 70
        p.setPen(QPen(CyberColors.BORDER_BRIGHT, 2))
        p.setBrush(CyberColors.BG_PANEL)
        p.drawRoundedRect(st_x, st_y, 175, 65, 5, 5)
       
        state_map = {
            self.STATE_DRAW: ("DRAWING", CyberColors.NEON_CYAN),
            self.STATE_ERASE: ("ERASING", CyberColors.NEON_ORANGE),
            self.STATE_COLOR: ("COLOR", CyberColors.NEON_PURPLE),
            self.STATE_EXIT: ("EXITING", CyberColors.NEON_MAGENTA),
            self.STATE_COMMAND: ("COMMAND", CyberColors.NEON_PURPLE),
            self.STATE_NAV_NEXT: ("NEXT", CyberColors.NEON_CYAN),
            self.STATE_NAV_PREV: ("PREV", CyberColors.NEON_CYAN),
            self.STATE_BRUSH_TYPE: ("BRUSH", CyberColors.NEON_ORANGE),
            self.STATE_SHAPE: ("SHAPES", CyberColors.NEON_GREEN),
            self.STATE_IDLE: ("STANDBY", CyberColors.TEXT_DIM),
        }
        st_text, st_color = state_map.get(self.current_state, ("---", CyberColors.TEXT_DIM))
       
        p.setFont(QFont("Consolas", 12, QFont.Bold))
        p.setPen(st_color)
        p.drawText(st_x + 12, st_y + 22, f"⬡ {st_text}")
       
        p.setFont(QFont("Consolas", 9))
        p.setPen(CyberColors.TEXT_DIM)
        p.drawText(st_x + 12, st_y + 40, f"PEN: {self.pen_size}px")
       
        p.setPen(QPen(CyberColors.NEON_CYAN, 2))
        p.setBrush(self.pen_color)
        p.drawEllipse(st_x + 130, st_y + 12, 30, 30)
       
        # INSTRUCTION PANEL
        guide_x = 20
        guide_y = self.screen_h - 180
        guide_w = 380
        guide_h = 145
       
        p.setPen(QPen(CyberColors.NEON_CYAN, 2))
        p.setBrush(CyberColors.BG_HOLOGRAM)
        p.drawRoundedRect(guide_x, guide_y, guide_w, guide_h, 8, 8)
       
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.setPen(CyberColors.NEON_CYAN)
        p.drawText(guide_x + 15, guide_y + 22, "═══════ GESTURE COMMANDS ═══════")
       
        p.setFont(QFont("Consolas", 9))
       
        gestures = [
            ("☝️ INDEX", "DRAW", CyberColors.NEON_CYAN),
            ("✌️ PEACE", "COLOR", CyberColors.NEON_PURPLE),
            ("🤟 3 FINGERS", "BRUSH", CyberColors.NEON_ORANGE),
            ("🤙 PINKY", "SHAPES", CyberColors.NEON_GREEN),
            ("🖐️ PALM", "ERASE", CyberColors.NEON_ORANGE),
            ("✊ FIST", "EXIT", CyberColors.NEON_MAGENTA),
        ]
       
        for i, (gesture, action, color) in enumerate(gestures):
            row, col = i // 2, i % 2
            gx = guide_x + 15 + col * 185
            gy = guide_y + 45 + row * 22
           
            p.setPen(color)
            p.drawText(gx, gy, gesture)
            p.setPen(CyberColors.TEXT_DIM)
            p.drawText(gx + 90, gy, f"→ {action}")
       
        # BOTTOM STATUS BAR
        bar_h = 42
        bar_y = self.screen_h - bar_h
       
        bg = QLinearGradient(0, bar_y, 0, self.screen_h)
        bg.setColorAt(0, QColor(10, 20, 40, 240))
        bg.setColorAt(1, QColor(5, 10, 25, 250))
        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawRect(0, bar_y, self.screen_w, bar_h)
        p.setPen(QPen(CyberColors.NEON_CYAN, 1))
        p.drawLine(0, bar_y, self.screen_w, bar_y)
       
        p.setPen(CyberColors.TEXT_DIM)
        p.setFont(QFont("Consolas", 9))
       
        brush_name = BrushType.NAMES[self.brush_type][:6]
        shape_name = ShapeTool.NAMES[self.shape_tool][:6]
        fill = "●" if self.shape_filled else "○"
        grid = "ON" if self.show_grid else "OFF"
        blink = "ON" if self.eye_enabled else "OFF"
       
        help_text = f"⬡ BRUSH:{brush_name} │ SHAPE:{shape_name}{fill} │ G=Grid({grid}) │ B=BG │ E=Blink({blink}) │ S=Save │ C=Clear │ ESC=Exit"
        p.drawText(25, bar_y + 28, help_text)
       
        p.setPen(CyberColors.NEON_CYAN)
        p.setFont(QFont("Consolas", 10, QFont.Bold))
        p.drawText(self.screen_w - 100, bar_y + 28, time.strftime("%H:%M:%S"))
   
    # ═══════════════════════════════════════════════════════════════════════
    # KEY EVENTS
    # ═══════════════════════════════════════════════════════════════════════
   
    def keyPressEvent(self, event):
        key = event.key()
       
        if Qt.Key_0 <= key <= Qt.Key_4:
            self.set_shape_tool(key - Qt.Key_0)
        elif event.modifiers() & Qt.ShiftModifier:
            if Qt.Key_1 <= key <= Qt.Key_3:
                self.set_brush_type(key - Qt.Key_1)
        elif key == Qt.Key_F:
            self.toggle_shape_fill()
        elif key == Qt.Key_Escape:
            self.exit_presentation() if self.presentation.is_active else self.stop_draw()
        elif key == Qt.Key_C:
            self.clear()
        elif key == Qt.Key_S:
            self.save_drawing()
        elif key == Qt.Key_P:
            if not self.presentation.is_active:
                self.open_presentation_dialog()
        elif key == Qt.Key_B:
            self.cycle_background()
        elif key == Qt.Key_G:
            self.toggle_grid()
        elif key == Qt.Key_E:
            self.toggle_blink_detection()
        elif key == Qt.Key_U:
            self.toggle_ui()
        elif key == Qt.Key_Left:
            self.prev_slide()
        elif key == Qt.Key_Right:
            self.next_slide()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self.pen_size = min(50, self.pen_size + 2)
            self._show_notification(f"⬡ PEN: {self.pen_size}px")
        elif key == Qt.Key_Minus:
            self.pen_size = max(2, self.pen_size - 2)
            self._show_notification(f"⬡ PEN: {self.pen_size}px")
        elif key == Qt.Key_Tab:
            if event.modifiers() & Qt.ShiftModifier:
                self.cycle_brush_type()
            else:
                self.cycle_shape_tool()
        elif key == Qt.Key_Space:
            self.cycle_brush_type()
        elif key == Qt.Key_N:
            self.set_brush_type(BrushType.NORMAL)
        elif key == Qt.Key_H:
            self.set_brush_type(BrushType.HIGHLIGHTER)
        elif key == Qt.Key_M:
            self.set_brush_type(BrushType.MARKER)
        else:
            super().keyPressEvent(event)
   
    def closeEvent(self, event):
        if self.line_buffer.is_drawing:
            self._commit_smooth_line()
            self.line_buffer.end_stroke()
        self.stop_draw()
        super().closeEvent(event)
   
    def close(self):
        if self.line_buffer.is_drawing:
            self._commit_smooth_line()
            self.line_buffer.end_stroke()
        self.stop_draw()
        super().close()


# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
   
    print("\n" + "⬡" * 50)
    print("⬡  HOLOGRAM v3.5 - SMOOTH DRAWING & ERASER FIXED  ⬡")
    print("⬡" * 50)
    print("\n✅ FIXES APPLIED:")
    print("   • Eraser now interpolates between points (no gaps!)")
    print("   • Drawing uses improved path generation")
    print("   • Velocity-adaptive jitter threshold")
    print("   • Better segment tracking for smooth lines")
    print("\n🖌️ BRUSH TYPES:")
    print("   ✏️  NORMAL     - Smooth solid lines")
    print("   🖍️  HIGHLIGHTER - Semi-transparent wide strokes")
    print("   🖊️  MARKER     - Bold solid strokes")
    print("\n🔷 SHAPE TOOLS:")
    print("   ✏️  FREEHAND   - Free drawing")
    print("   ➔  ARROW      - Arrow lines")
    print("   ▭  RECTANGLE  - Rectangles")
    print("   ■  SQUARE     - Squares")
    print("   ●  CIRCLE     - Circles")
    print("\n🎮 GESTURE CONTROLS:")
    print("   🤟 3 Fingers (Index+Middle+Ring) = Cycle Brush Type")
    print("   🤙 Pinky Up = Cycle Shapes")
    print("   ✌️ Peace Sign = Cycle Colors")
    print("   🖐️ Open Palm = Eraser (NOW SMOOTH!)")
    print("\n⌨️ KEYBOARD SHORTCUTS:")
    print("   SPACE / Shift+TAB = Cycle Brush Type")
    print("   N=Normal H=Highlighter M=Marker")
    print("   TAB = Cycle Shapes │ 0-4 = Select Shape")
    print("   Shift+1-3 = Select Brush │ F = Toggle Fill")
    print("   B = Cycle Background │ G = Toggle Grid")
    print("   E = Toggle Eye Blink │ U = Toggle UI")
    print("   S = Save Drawing │ C = Clear Canvas")
    print("   +/- = Pen Size │ ESC = Exit")
    print("⬡" * 50 + "\n")
   
    app = QApplication(sys.argv)
   
    def on_exit(mode):
        print(f"✅ Exit → {mode}")
        app.quit()
   
    canvas = DrawCanvas()
    canvas.set_exit_callback(on_exit)
    canvas.start_draw()
   
    sys.exit(app.exec())
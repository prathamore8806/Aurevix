"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        AUREVIX SPLASH SCREEN                                  ║
║                   Animated Landing Page with Effects                          ║
║              FUTURISTIC CYBERPUNK HOLOGRAM EFFECT (12 SECONDS)                ║
║                    CENTERED LOGO + TEXT MOVED DOWN                            ║
║                    ✅ BINARY DATA STREAMS (PURE 0/1)                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import math
import random
import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    Property, QRect, Signal, QPointF
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QFont, QPen, QBrush, QPixmap, QPainterPath, QPolygonF
)


# ════════════════════════════════════════════════════════════════════════════
#                              EFFECTS CLASSES
# ════════════════════════════════════════════════════════════════════════════

class Particle:
    """Floating particle"""
    def __init__(self, width, height):
        self.reset(width, height, initial=True)
        
    def reset(self, width, height, initial=False):
        self.x = random.randint(0, max(1, width))
        self.y = random.randint(0, max(1, height)) if initial else height + 10
        self.size = random.uniform(1, 4)
        self.speed = random.uniform(0.5, 2)
        self.opacity = random.uniform(0.2, 0.7)
        self.pulse_offset = random.uniform(0, math.pi * 2)
        self.color_type = random.choice(['cyan', 'purple', 'green', 'white'])
        
    def update(self, width, height):
        self.y -= self.speed
        self.x += math.sin(self.y * 0.01 + self.pulse_offset) * 0.5
        if self.y < -10:
            self.reset(width, height)
            
    def get_color(self):
        colors = {
            'cyan': QColor(0, 255, 255),
            'purple': QColor(255, 0, 255),
            'green': QColor(0, 255, 136),
            'white': QColor(255, 255, 255)
        }
        return colors.get(self.color_type, QColor(0, 255, 255))


class ShineStreak:
    """Moving shine/light streak effect"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset(width, height)
        
    def reset(self, width, height):
        self.width = width
        self.height = height
        self.start_x = random.randint(-200, width)
        self.y = random.randint(0, height)
        self.x = self.start_x
        self.length = random.randint(150, 400)
        self.thickness = random.randint(1, 3)
        self.speed = random.uniform(3, 8)
        self.opacity = random.uniform(0.1, 0.3)
        self.angle = random.uniform(-0.3, 0.3)
        
    def update(self):
        self.x += self.speed
        if self.x > self.width + 200:
            self.reset(self.width, self.height)


class Sparkle:
    """Twinkling sparkle effect"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(2, 6)
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.05, 0.15)
        self.max_opacity = random.uniform(0.4, 0.9)
        
    def update(self):
        self.phase += self.speed
        
    def get_opacity(self):
        return abs(math.sin(self.phase)) * self.max_opacity


class GlowingOrb:
    """Floating glowing orb"""
    def __init__(self, x, y, radius, color):
        self.base_x = x
        self.base_y = y
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.01, 0.03)
        
    def update(self):
        self.phase += self.speed
        self.x = self.base_x + math.sin(self.phase) * 30
        self.y = self.base_y + math.cos(self.phase * 0.7) * 20


class FloatingIcon:
    """Floating gesture icon"""
    def __init__(self, x, y, icon, size):
        self.base_x = x
        self.base_y = y
        self.x = x
        self.y = y
        self.icon = icon
        self.size = size
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.005, 0.015)
        self.opacity = random.uniform(0.3, 0.6)
        
    def update(self):
        self.phase += self.speed
        self.x = self.base_x + math.sin(self.phase) * 20
        self.y = self.base_y + math.cos(self.phase * 0.8) * 15


# ════════════════════════════════════════════════════════════════════════════
#                         CYBERPUNK HOLOGRAM EFFECTS
# ════════════════════════════════════════════════════════════════════════════

class ScanLine:
    """Moving horizontal scan line"""
    def __init__(self, height):
        self.height = height
        self.y = random.randint(0, height)
        self.speed = random.uniform(1, 4)
        self.thickness = random.randint(1, 3)
        self.opacity = random.uniform(0.1, 0.4)
        self.color = random.choice([
            QColor(0, 255, 255),  # Cyan
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 136),  # Neon green
        ])
        
    def update(self, height):
        self.y += self.speed
        if self.y > height:
            self.y = -10
            self.speed = random.uniform(1, 4)
            self.opacity = random.uniform(0.1, 0.4)


class DataStream:
    """
    ✅ BINARY ONLY DATA STREAM - Pure 0s and 1s
    Falling matrix-style effect with ONLY binary characters
    """
    def __init__(self, x, height):
        self.x = x
        self.height = height
        # ✅ PURE BINARY - Only "0" and "1"
        self.chars = "01"
        self.reset(height)
        
    def reset(self, height):
        self.y = random.randint(-500, 0)
        self.speed = random.uniform(2, 8)
        self.char_height = random.randint(12, 20)
        self.length = random.randint(5, 20)
        self.opacity = random.uniform(0.3, 0.8)
        # ✅ Generate stream of ONLY 0s and 1s
        self.stream = [random.choice(self.chars) for _ in range(self.length)]
        
    def update(self, height):
        self.y += self.speed
        if self.y > height + 100:
            self.reset(height)
        # ✅ Randomly change characters (still only 0 or 1)
        if random.random() < 0.1:
            idx = random.randint(0, len(self.stream) - 1)
            self.stream[idx] = random.choice(self.chars)


class HexagonCell:
    """Hexagonal grid cell"""
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.phase = random.uniform(0, math.pi * 2)
        self.pulse_speed = random.uniform(0.02, 0.05)
        self.base_opacity = random.uniform(0.05, 0.2)
        
    def update(self):
        self.phase += self.pulse_speed
        
    def get_opacity(self):
        return self.base_opacity * (0.5 + 0.5 * math.sin(self.phase))


class CircuitNode:
    """Circuit board node with connections"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(2, 5)
        self.connections = []
        self.pulse_phase = random.uniform(0, math.pi * 2)
        self.pulse_speed = random.uniform(0.03, 0.08)
        
    def update(self):
        self.pulse_phase += self.pulse_speed
        
    def get_brightness(self):
        return 0.3 + 0.7 * abs(math.sin(self.pulse_phase))


class GlitchEffect:
    """Glitch displacement effect"""
    def __init__(self):
        self.active = False
        self.timer = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0
        self.slice_y = 0
        self.slice_height = 0
        
    def trigger(self):
        if random.random() < 0.02:  # 2% chance per frame
            self.active = True
            self.timer = 0
            self.duration = random.randint(2, 8)
            self.offset_x = random.randint(-20, 20)
            self.offset_y = random.randint(-5, 5)
            self.slice_y = random.randint(0, 1000)
            self.slice_height = random.randint(10, 100)
            
    def update(self):
        if self.active:
            self.timer += 1
            if self.timer >= self.duration:
                self.active = False


class HolographicRing:
    """Pulsing holographic ring"""
    def __init__(self, cx, cy, max_radius):
        self.cx = cx
        self.cy = cy
        self.max_radius = max_radius
        self.radius = random.uniform(0, max_radius)
        self.speed = random.uniform(0.5, 2)
        self.thickness = random.uniform(1, 3)
        self.opacity = 0
        
    def update(self):
        self.radius += self.speed
        # Fade in then out
        progress = self.radius / self.max_radius
        if progress < 0.3:
            self.opacity = progress / 0.3
        elif progress > 0.7:
            self.opacity = (1 - progress) / 0.3
        else:
            self.opacity = 1.0
            
        if self.radius > self.max_radius:
            self.radius = 0
            self.speed = random.uniform(0.5, 2)


# ════════════════════════════════════════════════════════════════════════════
#                              SPLASH SCREEN
# ════════════════════════════════════════════════════════════════════════════

class SplashScreen(QWidget):
    """
    🚀 Aurevix Animated Splash Screen - CYBERPUNK HOLOGRAM EFFECT
    
    Features:
    ✓ FUTURISTIC CYBERPUNK HOLOGRAM BACKGROUND
    ✓ 12 SECOND DURATION
    ✓ FULL SCREEN coverage
    ✓ CENTERED LOGO
    ✓ TEXT MOVED DOWN
    ✓ Dynamic scaling
    ✓ Scan lines effect
    ✓ ✅ BINARY Data streams (Pure 0s and 1s - NO foreign characters)
    ✓ Hexagonal grid overlay
    ✓ Circuit board patterns
    ✓ Glitch effects
    ✓ Holographic rings
    ✓ Neon glow effects
    ✓ Shiny overlay effects
    ✓ Moving shine streaks
    ✓ Sparkle effects
    ✓ Animated logo with glow
    ✓ Gradient title text
    ✓ Particle system
    ✓ Progress bar
    """
    
    splashFinished = Signal()
    
    def __init__(self, duration=12000, parent=None):
        """
        Args:
            duration: Splash duration in ms (default 12000 = 12 seconds)
        """
        super().__init__(parent)
        
        self.duration = duration
        
        # ═══════════════════════════════════════════════════════════════
        #                      GET SCREEN SIZE
        # ═══════════════════════════════════════════════════════════════
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            screen_geometry = screen.geometry()
            self.screen_width = screen_geometry.width()
            self.screen_height = screen_geometry.height()
        else:
            self.screen_width = 1920
            self.screen_height = 1080
        
        # ═══════════════════════════════════════════════════════════════
        #                      WINDOW SETUP - FULL SCREEN
        # ═══════════════════════════════════════════════════════════════
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowTitle("Aurevix - Loading")
        self.setFixedSize(self.screen_width, self.screen_height)
        self.move(0, 0)
        
        # ═══════════════════════════════════════════════════════════════
        #                      ANIMATION STATE
        # ═══════════════════════════════════════════════════════════════
        self._logo_scale = 0.0
        self._logo_opacity = 0.0
        self._title_opacity = 0.0
        self._title_scale = 0.8
        self._tagline_opacity = 0.0
        self._progress = 0.0
        self._glow_intensity = 0.5
        self._typing_index = 0
        self._fade_out_opacity = 1.0
        self._shine_phase = 0.0
        self._hologram_flicker = 1.0
        
        self.glow_direction = 1
        self.frame_count = 0
        
        # Logo
        self.logo_pixmap = None
        self._load_logo()
        
        # ═══════════════════════════════════════════════════════════════
        #                      TEXT CONTENT
        # ═══════════════════════════════════════════════════════════════
        self.app_name = "AUREVIX"
        self.tagline = "Control Your World with Gestures"
        self.version = "v1"
        self.subtitle = "Gesture Control Vision System"
        
        self.loading_texts = [
            "Initializing gesture engine...",
            "Loading AI models...",
            "Calibrating hand tracking...",
            "Preparing gesture recognition...",
            "Setting up control modules...",
            "Almost ready...",
            "Welcome to Aurevix!"
        ]
        self.current_loading_text = self.loading_texts[0]
        self.loading_text_index = 0
        
        # ═══════════════════════════════════════════════════════════════
        #                      CYBERPUNK HOLOGRAM EFFECTS
        # ═══════════════════════════════════════════════════════════════
        
        # Scan lines
        self.scan_lines = [ScanLine(self.screen_height) for _ in range(15)]
        
        # ✅ BINARY Data streams (Pure 0s and 1s)
        stream_count = self.screen_width // 40
        self.data_streams = [
            DataStream(i * 40 + random.randint(-10, 10), self.screen_height) 
            for i in range(stream_count)
        ]
        
        # Hexagonal grid
        self.hexagons = []
        hex_size = 60
        for row in range(self.screen_height // hex_size + 2):
            for col in range(self.screen_width // hex_size + 2):
                x = col * hex_size * 1.5
                y = row * hex_size * 1.732 + (col % 2) * hex_size * 0.866
                if random.random() < 0.3:  # Only some hexagons
                    self.hexagons.append(HexagonCell(x, y, hex_size // 2))
        
        # Circuit nodes
        self.circuit_nodes = []
        for _ in range(50):
            node = CircuitNode(
                random.randint(0, self.screen_width),
                random.randint(0, self.screen_height)
            )
            self.circuit_nodes.append(node)
        
        # Create connections between nearby nodes
        for node in self.circuit_nodes:
            for other in self.circuit_nodes:
                if node != other:
                    dist = math.sqrt((node.x - other.x)**2 + (node.y - other.y)**2)
                    if dist < 150 and random.random() < 0.3:
                        node.connections.append(other)
        
        # Glitch effect
        self.glitch = GlitchEffect()
        
        # Holographic rings
        self.holo_rings = [
            HolographicRing(self.screen_width // 2, int(self.screen_height * 0.4), 
                           min(self.screen_width, self.screen_height) * 0.4)
            for _ in range(5)
        ]
        # Stagger the rings
        for i, ring in enumerate(self.holo_rings):
            ring.radius = ring.max_radius * i / len(self.holo_rings)
        
        # ═══════════════════════════════════════════════════════════════
        #                      VISUAL EFFECTS (Original)
        # ═══════════════════════════════════════════════════════════════
        
        particle_count = int((self.screen_width * self.screen_height) / 20000)
        particle_count = max(50, min(particle_count, 150))
        self.particles = [Particle(self.screen_width, self.screen_height) for _ in range(particle_count)]
        
        streak_count = max(3, self.screen_width // 300)
        self.shine_streaks = [ShineStreak(self.screen_width, self.screen_height) for _ in range(streak_count)]
        
        sparkle_count = int((self.screen_width * self.screen_height) / 30000)
        sparkle_count = max(20, min(sparkle_count, 60))
        self.sparkles = []
        for _ in range(sparkle_count):
            x = random.randint(50, self.screen_width - 50)
            y = random.randint(50, self.screen_height - 50)
            self.sparkles.append(Sparkle(x, y))
        
        w, h = self.screen_width, self.screen_height
        self.orbs = [
            GlowingOrb(int(w * 0.1), int(h * 0.18), 120, QColor(0, 255, 255, 25)),
            GlowingOrb(int(w * 0.9), int(h * 0.24), 140, QColor(255, 0, 255, 20)),
            GlowingOrb(int(w * 0.14), int(h * 0.73), 100, QColor(0, 255, 136, 18)),
            GlowingOrb(int(w * 0.86), int(h * 0.67), 110, QColor(255, 107, 107, 15)),
            GlowingOrb(int(w * 0.5), int(h * 0.12), 90, QColor(255, 215, 0, 12)),
            GlowingOrb(int(w * 0.5), int(h * 0.88), 130, QColor(0, 255, 255, 18)),
        ]
        
        self.floating_icons = [
            FloatingIcon(int(w * 0.07), int(h * 0.37), "👋", 32),
            FloatingIcon(int(w * 0.93), int(h * 0.49), "✋", 30),
            FloatingIcon(int(w * 0.11), int(h * 0.85), "👆", 28),
            FloatingIcon(int(w * 0.89), int(h * 0.85), "✌️", 30),
            FloatingIcon(int(w * 0.21), int(h * 0.15), "🖐️", 26),
            FloatingIcon(int(w * 0.79), int(h * 0.15), "👇", 28),
        ]
        
        # ═══════════════════════════════════════════════════════════════
        #                      TIMERS
        # ═══════════════════════════════════════════════════════════════
        
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_frame)
        self.animation_timer.start(16)
        
        self.loading_text_timer = QTimer(self)
        self.loading_text_timer.timeout.connect(self._update_loading_text)
        self.loading_text_timer.start(600)
        
        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self._update_typing)
        self.typing_timer.start(40)
        
        # Setup animations
        self._setup_animations()
        
        # Print status
        print("═" * 60)
        print("  AUREVIX SPLASH SCREEN - CYBERPUNK HOLOGRAM")
        print("═" * 60)
        print(f"  Screen: {self.screen_width} x {self.screen_height}")
        print(f"  Duration: {duration}ms ({duration/1000} seconds)")
        print(f"  Logo: {'✓ Loaded' if self.logo_pixmap else '○ Using placeholder'}")
        print("  Effects:")
        print("    ✓ Scan lines")
        print("    ✓ ✅ BINARY Data streams (Pure 0s & 1s)")
        print("    ✓ Hexagonal grid")
        print("    ✓ Circuit patterns")
        print("    ✓ Glitch effects")
        print("    ✓ Holographic rings")
        print("    ✓ Neon particles")
        print("═" * 60)
    
    def _load_logo(self):
        """Load logo"""
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        logo_paths = [
            os.path.join(BASE_DIR, "GCVM", "Asset", "logo.png"),
            os.path.join(BASE_DIR, "assets", "logo.png"),
            os.path.join(BASE_DIR, "logo.png"),
        ]
        
        for path in logo_paths:
            if os.path.exists(path):
                self.logo_pixmap = QPixmap(path)
                if not self.logo_pixmap.isNull():
                    print(f"  ✓ Logo loaded: {os.path.basename(path)}")
                    return
    
    # ════════════════════════════════════════════════════════════════════
    #                         ANIMATIONS
    # ════════════════════════════════════════════════════════════════════
    
    def _setup_animations(self):
        """Setup property animations"""
        
        self.logo_scale_anim = QPropertyAnimation(self, b"logo_scale")
        self.logo_scale_anim.setDuration(1200)
        self.logo_scale_anim.setStartValue(0.0)
        self.logo_scale_anim.setEndValue(1.0)
        self.logo_scale_anim.setEasingCurve(QEasingCurve.OutElastic)
        
        self.logo_opacity_anim = QPropertyAnimation(self, b"logo_opacity")
        self.logo_opacity_anim.setDuration(800)
        self.logo_opacity_anim.setStartValue(0.0)
        self.logo_opacity_anim.setEndValue(1.0)
        self.logo_opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.title_opacity_anim = QPropertyAnimation(self, b"title_opacity")
        self.title_opacity_anim.setDuration(800)
        self.title_opacity_anim.setStartValue(0.0)
        self.title_opacity_anim.setEndValue(1.0)
        self.title_opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.title_scale_anim = QPropertyAnimation(self, b"title_scale")
        self.title_scale_anim.setDuration(600)
        self.title_scale_anim.setStartValue(0.8)
        self.title_scale_anim.setEndValue(1.0)
        self.title_scale_anim.setEasingCurve(QEasingCurve.OutBack)
        
        self.tagline_opacity_anim = QPropertyAnimation(self, b"tagline_opacity")
        self.tagline_opacity_anim.setDuration(800)
        self.tagline_opacity_anim.setStartValue(0.0)
        self.tagline_opacity_anim.setEndValue(1.0)
        self.tagline_opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.progress_anim = QPropertyAnimation(self, b"progress")
        self.progress_anim.setDuration(self.duration - 500)
        self.progress_anim.setStartValue(0.0)
        self.progress_anim.setEndValue(1.0)
        self.progress_anim.setEasingCurve(QEasingCurve.Linear)
        
        QTimer.singleShot(100, self._start_logo_animation)
        QTimer.singleShot(800, self._start_title_animation)
        QTimer.singleShot(1200, self._start_tagline_animation)
        QTimer.singleShot(400, self.progress_anim.start)
        self.progress_anim.finished.connect(self._on_progress_complete)
        
    def _start_logo_animation(self):
        self.logo_scale_anim.start()
        self.logo_opacity_anim.start()
        
    def _start_title_animation(self):
        self.title_opacity_anim.start()
        self.title_scale_anim.start()
        
    def _start_tagline_animation(self):
        self.tagline_opacity_anim.start()
    
    def _on_progress_complete(self):
        """Called when progress completes"""
        QTimer.singleShot(300, self._start_fade_out)
    
    def _start_fade_out(self):
        """Start fade out animation"""
        if hasattr(self, '_fade_started') and self._fade_started:
            return
        self._fade_started = True
        
        self.fade_out_anim = QPropertyAnimation(self, b"fade_out_opacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_anim.finished.connect(self._finish_splash)
        self.fade_out_anim.start()
    
    # ════════════════════════════════════════════════════════════════════
    #                         PROPERTIES
    # ════════════════════════════════════════════════════════════════════
    
    def get_logo_scale(self):
        return self._logo_scale
    def set_logo_scale(self, value):
        self._logo_scale = value
        self.update()
    logo_scale = Property(float, get_logo_scale, set_logo_scale)
    
    def get_logo_opacity(self):
        return self._logo_opacity
    def set_logo_opacity(self, value):
        self._logo_opacity = value
        self.update()
    logo_opacity = Property(float, get_logo_opacity, set_logo_opacity)
    
    def get_title_opacity(self):
        return self._title_opacity
    def set_title_opacity(self, value):
        self._title_opacity = value
        self.update()
    title_opacity = Property(float, get_title_opacity, set_title_opacity)
    
    def get_title_scale(self):
        return self._title_scale
    def set_title_scale(self, value):
        self._title_scale = value
        self.update()
    title_scale = Property(float, get_title_scale, set_title_scale)
    
    def get_tagline_opacity(self):
        return self._tagline_opacity
    def set_tagline_opacity(self, value):
        self._tagline_opacity = value
        self.update()
    tagline_opacity = Property(float, get_tagline_opacity, set_tagline_opacity)
    
    def get_progress(self):
        return self._progress
    def set_progress(self, value):
        self._progress = value
        self.update()
    progress = Property(float, get_progress, set_progress)
    
    def get_fade_out_opacity(self):
        return self._fade_out_opacity
    def set_fade_out_opacity(self, value):
        self._fade_out_opacity = value
        self.setWindowOpacity(value)
        self.update()
    fade_out_opacity = Property(float, get_fade_out_opacity, set_fade_out_opacity)
    
    # ════════════════════════════════════════════════════════════════════
    #                         UPDATE
    # ════════════════════════════════════════════════════════════════════
    
    def _update_frame(self):
        """Update all animations"""
        self.frame_count += 1
        self._shine_phase += 0.02
        
        # Hologram flicker effect
        if random.random() < 0.05:  # 5% chance of flicker
            self._hologram_flicker = random.uniform(0.85, 1.0)
        else:
            self._hologram_flicker = min(1.0, self._hologram_flicker + 0.05)
        
        # Glow pulse
        self._glow_intensity += 0.015 * self.glow_direction
        if self._glow_intensity >= 1.0:
            self._glow_intensity = 1.0
            self.glow_direction = -1
        elif self._glow_intensity <= 0.4:
            self._glow_intensity = 0.4
            self.glow_direction = 1
        
        # Update cyberpunk effects
        for scan_line in self.scan_lines:
            scan_line.update(self.height())
        
        for stream in self.data_streams:
            stream.update(self.height())
        
        for hexagon in self.hexagons:
            hexagon.update()
        
        for node in self.circuit_nodes:
            node.update()
        
        self.glitch.trigger()
        self.glitch.update()
        
        for ring in self.holo_rings:
            ring.update()
        
        # Update original effects
        for particle in self.particles:
            particle.update(self.width(), self.height())
        
        for streak in self.shine_streaks:
            streak.width = self.width()
            streak.height = self.height()
            streak.update()
        
        for sparkle in self.sparkles:
            sparkle.update()
        
        for orb in self.orbs:
            orb.update()
        
        for icon in self.floating_icons:
            icon.update()
        
        self.update()
    
    def _update_loading_text(self):
        progress_percent = self._progress * 100
        
        if progress_percent < 15:
            new_index = 0
        elif progress_percent < 30:
            new_index = 1
        elif progress_percent < 45:
            new_index = 2
        elif progress_percent < 60:
            new_index = 3
        elif progress_percent < 75:
            new_index = 4
        elif progress_percent < 95:
            new_index = 5
        else:
            new_index = 6
        
        if new_index != self.loading_text_index:
            self.loading_text_index = new_index
            self.current_loading_text = self.loading_texts[new_index]
            self._typing_index = 0
    
    def _update_typing(self):
        if self._typing_index < len(self.current_loading_text):
            self._typing_index += 1
    
    def _finish_splash(self):
        print("═" * 60)
        print("  ✓ SPLASH COMPLETE")
        print("═" * 60)
        
        self.animation_timer.stop()
        self.loading_text_timer.stop()
        self.typing_timer.stop()
        
        self.splashFinished.emit()
        self.close()
    
    # ════════════════════════════════════════════════════════════════════
    #                         PAINTING
    # ════════════════════════════════════════════════════════════════════
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        
        w = self.width()
        h = self.height()
        
        # Draw all layers
        self._draw_cyberpunk_background(painter, w, h)
        self._draw_perspective_grid(painter, w, h)
        self._draw_hexagon_grid(painter, w, h)
        self._draw_circuit_board(painter, w, h)
        self._draw_data_streams(painter, w, h)
        self._draw_scan_lines(painter, w, h)
        self._draw_holographic_rings(painter, w, h)
        self._draw_shine_overlay(painter, w, h)
        self._draw_shine_streaks(painter, w, h)
        self._draw_orbs(painter, w, h)
        self._draw_particles(painter, w, h)
        self._draw_sparkles(painter, w, h)
        self._draw_floating_icons(painter, w, h)
        self._draw_glitch_effect(painter, w, h)
        self._draw_vignette(painter, w, h)
        self._draw_noise_overlay(painter, w, h)
        self._draw_logo(painter, w, h)
        self._draw_title(painter, w, h)
        self._draw_tagline(painter, w, h)
        self._draw_loading_text(painter, w, h)
        self._draw_progress_bar(painter, w, h)
        self._draw_decorations(painter, w, h)
        self._draw_version(painter, w, h)
        
        painter.end()
    
    def _draw_cyberpunk_background(self, painter, w, h):
        """Draw dark cyberpunk gradient background"""
        gradient = QLinearGradient(0, 0, w, h)
        gradient.setColorAt(0.0, QColor(5, 0, 15))      # Deep purple-black
        gradient.setColorAt(0.2, QColor(10, 5, 25))     # Dark purple
        gradient.setColorAt(0.4, QColor(5, 10, 20))     # Dark blue-purple
        gradient.setColorAt(0.6, QColor(10, 5, 25))     # Dark purple
        gradient.setColorAt(0.8, QColor(5, 15, 20))     # Dark cyan tint
        gradient.setColorAt(1.0, QColor(5, 0, 15))      # Deep purple-black
        painter.fillRect(0, 0, w, h, gradient)
        
        # Add subtle neon glow zones
        glow_size = int(min(w, h) * 0.5 + math.sin(self._shine_phase) * 50)
        
        # Cyan glow top-left
        cyan_glow = QRadialGradient(w * 0.2, h * 0.2, glow_size)
        cyan_glow.setColorAt(0, QColor(0, 255, 255, int(15 * self._glow_intensity * self._hologram_flicker)))
        cyan_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, cyan_glow)
        
        # Magenta glow bottom-right
        magenta_glow = QRadialGradient(w * 0.8, h * 0.8, glow_size)
        magenta_glow.setColorAt(0, QColor(255, 0, 255, int(12 * self._glow_intensity * self._hologram_flicker)))
        magenta_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, magenta_glow)
        
        # Center glow (where logo will be)
        center_glow = QRadialGradient(w / 2, h * 0.4, glow_size * 0.8)
        center_glow.setColorAt(0, QColor(0, 255, 255, int(20 * self._glow_intensity * self._hologram_flicker)))
        center_glow.setColorAt(0.5, QColor(255, 0, 255, int(10 * self._glow_intensity * self._hologram_flicker)))
        center_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, center_glow)
    
    def _draw_perspective_grid(self, painter, w, h):
        """Draw perspective grid fading into distance"""
        # Horizon line
        horizon_y = h * 0.35
        vanishing_x = w / 2
        
        # Grid color
        grid_color = QColor(0, 255, 255, int(30 * self._hologram_flicker))
        painter.setPen(QPen(grid_color, 1))
        
        # Horizontal lines (perspective)
        num_h_lines = 20
        for i in range(num_h_lines):
            progress = i / num_h_lines
            y = horizon_y + (h - horizon_y) * (progress ** 1.5)
            
            # Fade based on distance
            alpha = int(30 * (1 - progress * 0.7) * self._hologram_flicker)
            painter.setPen(QPen(QColor(0, 255, 255, alpha), 1))
            painter.drawLine(0, int(y), w, int(y))
        
        # Vertical lines (converging to vanishing point)
        num_v_lines = 30
        for i in range(num_v_lines):
            x = (i / (num_v_lines - 1)) * w
            
            # Line from bottom to horizon
            alpha = int(25 * self._hologram_flicker)
            painter.setPen(QPen(QColor(0, 255, 255, alpha), 1))
            painter.drawLine(int(x), h, int(vanishing_x), int(horizon_y))
    
    def _draw_hexagon_grid(self, painter, w, h):
        """Draw hexagonal grid overlay"""
        for hexagon in self.hexagons:
            opacity = hexagon.get_opacity() * self._hologram_flicker
            if opacity < 0.02:
                continue
            
            # Create hexagon path
            path = QPainterPath()
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                px = hexagon.x + hexagon.size * math.cos(angle)
                py = hexagon.y + hexagon.size * math.sin(angle)
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            path.closeSubpath()
            
            # Draw hexagon
            color = QColor(0, 255, 255, int(255 * opacity * 0.3))
            painter.setPen(QPen(color, 1))
            painter.setBrush(QColor(0, 255, 255, int(255 * opacity * 0.05)))
            painter.drawPath(path)
    
    def _draw_circuit_board(self, painter, w, h):
        """Draw circuit board pattern"""
        for node in self.circuit_nodes:
            brightness = node.get_brightness() * self._hologram_flicker
            
            # Draw connections
            for other in node.connections:
                alpha = int(40 * brightness)
                painter.setPen(QPen(QColor(0, 255, 136, alpha), 1))
                
                # Draw L-shaped connection
                mid_x = (node.x + other.x) / 2
                painter.drawLine(int(node.x), int(node.y), int(mid_x), int(node.y))
                painter.drawLine(int(mid_x), int(node.y), int(mid_x), int(other.y))
                painter.drawLine(int(mid_x), int(other.y), int(other.x), int(other.y))
            
            # Draw node
            alpha = int(200 * brightness)
            painter.setPen(Qt.NoPen)
            
            # Glow
            glow = QRadialGradient(node.x, node.y, node.size * 4)
            glow.setColorAt(0, QColor(0, 255, 136, alpha // 2))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(glow)
            painter.drawEllipse(int(node.x - node.size * 4), int(node.y - node.size * 4),
                               int(node.size * 8), int(node.size * 8))
            
            # Core
            painter.setBrush(QColor(0, 255, 136, alpha))
            painter.drawEllipse(int(node.x - node.size), int(node.y - node.size),
                               int(node.size * 2), int(node.size * 2))
    
    def _draw_data_streams(self, painter, w, h):
        """
        ✅ DRAW BINARY DATA STREAMS - Pure 0s and 1s only
        Matrix-style falling effect with ONLY binary digits
        """
        for stream in self.data_streams:
            x = stream.x
            y = stream.y
            
            for i, char in enumerate(stream.stream):
                char_y = y - i * stream.char_height
                
                if char_y < -50 or char_y > h + 50:
                    continue
                
                # Fade based on position in stream
                if i == 0:
                    # First character is brightest (white/green)
                    color = QColor(200, 255, 200, int(255 * stream.opacity * self._hologram_flicker))
                else:
                    # Fade to darker green
                    fade = 1 - (i / len(stream.stream))
                    color = QColor(0, 255, 136, int(200 * fade * stream.opacity * self._hologram_flicker))
                
                painter.setPen(color)
                # ✅ Use monospace font for clean binary look
                font = QFont("Consolas", stream.char_height)
                painter.setFont(font)
                painter.drawText(int(x), int(char_y), char)
    
    def _draw_scan_lines(self, painter, w, h):
        """Draw moving scan lines"""
        for scan_line in self.scan_lines:
            # Main scan line
            color = QColor(scan_line.color.red(), scan_line.color.green(), 
                          scan_line.color.blue(), int(255 * scan_line.opacity * self._hologram_flicker))
            painter.setPen(QPen(color, scan_line.thickness))
            painter.drawLine(0, int(scan_line.y), w, int(scan_line.y))
            
            # Glow above and below
            for offset in [-3, -2, -1, 1, 2, 3]:
                glow_alpha = int(50 * scan_line.opacity * (1 - abs(offset) / 4) * self._hologram_flicker)
                glow_color = QColor(scan_line.color.red(), scan_line.color.green(),
                                   scan_line.color.blue(), glow_alpha)
                painter.setPen(QPen(glow_color, 1))
                painter.drawLine(0, int(scan_line.y + offset), w, int(scan_line.y + offset))
        
        # Static scan lines (CRT effect)
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        for y in range(0, h, 3):
            painter.drawLine(0, y, w, y)
    
    def _draw_holographic_rings(self, painter, w, h):
        """Draw pulsing holographic rings around logo area"""
        for ring in self.holo_rings:
            if ring.opacity < 0.05:
                continue
            
            alpha = int(100 * ring.opacity * self._hologram_flicker)
            
            # Cyan ring
            painter.setPen(QPen(QColor(0, 255, 255, alpha), ring.thickness))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(ring.cx - ring.radius), int(ring.cy - ring.radius),
                               int(ring.radius * 2), int(ring.radius * 2))
            
            # Magenta offset ring
            offset = 3
            painter.setPen(QPen(QColor(255, 0, 255, alpha // 2), ring.thickness))
            painter.drawEllipse(int(ring.cx - ring.radius + offset), int(ring.cy - ring.radius),
                               int(ring.radius * 2), int(ring.radius * 2))
    
    def _draw_shine_overlay(self, painter, w, h):
        """Draw shiny overlay effects"""
        # Animated sweep
        sweep_x = (self.frame_count * 3) % (w + 600) - 300
        sweep_gradient = QLinearGradient(sweep_x, 0, sweep_x + 300, h)
        sweep_gradient.setColorAt(0, QColor(255, 255, 255, 0))
        sweep_gradient.setColorAt(0.4, QColor(0, 255, 255, int(15 * self._hologram_flicker)))
        sweep_gradient.setColorAt(0.5, QColor(255, 255, 255, int(25 * self._hologram_flicker)))
        sweep_gradient.setColorAt(0.6, QColor(255, 0, 255, int(15 * self._hologram_flicker)))
        sweep_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(0, 0, w, h, sweep_gradient)
    
    def _draw_shine_streaks(self, painter, w, h):
        """Draw moving light streaks"""
        for streak in self.shine_streaks:
            gradient = QLinearGradient(
                streak.x, streak.y,
                streak.x + streak.length, streak.y + streak.length * streak.angle
            )
            gradient.setColorAt(0, QColor(255, 255, 255, 0))
            gradient.setColorAt(0.3, QColor(0, 255, 255, int(200 * streak.opacity * self._hologram_flicker)))
            gradient.setColorAt(0.5, QColor(255, 255, 255, int(150 * streak.opacity * self._hologram_flicker)))
            gradient.setColorAt(0.7, QColor(255, 0, 255, int(200 * streak.opacity * self._hologram_flicker)))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setPen(QPen(QBrush(gradient), streak.thickness))
            painter.drawLine(
                int(streak.x), int(streak.y),
                int(streak.x + streak.length), int(streak.y + streak.length * streak.angle)
            )
    
    def _draw_sparkles(self, painter, w, h):
        """Draw twinkling sparkles"""
        for sparkle in self.sparkles:
            opacity = sparkle.get_opacity() * self._hologram_flicker
            if opacity < 0.1:
                continue
            
            size = sparkle.size * (0.5 + opacity * 0.5)
            
            painter.setPen(Qt.NoPen)
            
            core_gradient = QRadialGradient(sparkle.x, sparkle.y, size)
            core_gradient.setColorAt(0, QColor(255, 255, 255, int(255 * opacity)))
            core_gradient.setColorAt(0.3, QColor(0, 255, 255, int(200 * opacity)))
            core_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(core_gradient)
            painter.drawEllipse(
                int(sparkle.x - size), int(sparkle.y - size),
                int(size * 2), int(size * 2)
            )
            
            if opacity > 0.5:
                line_length = size * 3
                painter.setPen(QPen(QColor(0, 255, 255, int(150 * opacity)), 1))
                painter.drawLine(
                    int(sparkle.x - line_length), int(sparkle.y),
                    int(sparkle.x + line_length), int(sparkle.y)
                )
                painter.drawLine(
                    int(sparkle.x), int(sparkle.y - line_length),
                    int(sparkle.x), int(sparkle.y + line_length)
                )
    
    def _draw_orbs(self, painter, w, h):
        """Draw glowing orbs"""
        for orb in self.orbs:
            gradient = QRadialGradient(orb.x, orb.y, orb.radius)
            
            alpha = int(orb.color.alpha() * self._glow_intensity * self._hologram_flicker)
            color = QColor(orb.color.red(), orb.color.green(), orb.color.blue(), alpha)
            
            gradient.setColorAt(0, color)
            gradient.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), alpha // 2))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(orb.x - orb.radius),
                int(orb.y - orb.radius),
                int(orb.radius * 2),
                int(orb.radius * 2)
            )
    
    def _draw_particles(self, painter, w, h):
        """Draw particles"""
        for particle in self.particles:
            pulse = 1 + math.sin(particle.pulse_offset + self.frame_count * 0.05) * 0.4
            size = particle.size * pulse
            
            color = particle.get_color()
            gradient = QRadialGradient(particle.x, particle.y, size * 2)
            gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 
                                         int(255 * particle.opacity * self._hologram_flicker)))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(particle.x - size),
                int(particle.y - size),
                int(size * 2),
                int(size * 2)
            )
    
    def _draw_floating_icons(self, painter, w, h):
        """Draw floating icons"""
        for icon in self.floating_icons:
            painter.setOpacity(icon.opacity * self._glow_intensity * self._hologram_flicker)
            
            font = QFont("Segoe UI Emoji", icon.size)
            painter.setFont(font)
            painter.setPen(QColor(0, 255, 255, 180))
            
            painter.drawText(
                int(icon.x - icon.size // 2),
                int(icon.y + icon.size // 2),
                icon.icon
            )
        
        painter.setOpacity(1.0)
    
    def _draw_glitch_effect(self, painter, w, h):
        """Draw glitch displacement effect"""
        if self.glitch.active:
            # Draw colored offset rectangles
            slice_y = self.glitch.slice_y % h
            slice_h = min(self.glitch.slice_height, h - slice_y)
            
            # Cyan offset
            painter.fillRect(
                self.glitch.offset_x, int(slice_y),
                w, int(slice_h),
                QColor(0, 255, 255, 30)
            )
            
            # Magenta offset (opposite direction)
            painter.fillRect(
                -self.glitch.offset_x, int(slice_y + 10),
                w, int(slice_h // 2),
                QColor(255, 0, 255, 30)
            )
    
    def _draw_noise_overlay(self, painter, w, h):
        """Draw subtle noise/static overlay"""
        # Only draw occasional noise pixels for performance
        if random.random() < 0.3:  # 30% of frames
            noise_count = 50
            for _ in range(noise_count):
                x = random.randint(0, w)
                y = random.randint(0, h)
                alpha = random.randint(5, 20)
                size = random.randint(1, 2)
                painter.fillRect(x, y, size, size, QColor(255, 255, 255, alpha))
    
    def _draw_vignette(self, painter, w, h):
        """Draw vignette"""
        gradient = QRadialGradient(w / 2, h / 2, max(w, h) * 0.7)
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.5, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.8, QColor(0, 0, 20, 100))
        gradient.setColorAt(1, QColor(0, 0, 10, 200))
        painter.fillRect(0, 0, w, h, gradient)
    
    def _draw_logo(self, painter, w, h):
        """Draw logo - CENTERED ON SCREEN with holographic effect"""
        if self._logo_opacity < 0.01:
            return
        
        painter.setOpacity(self._logo_opacity * self._hologram_flicker)
        
        # ═══════════════════════════════════════════════════════════════
        #  LOGO POSITION - CENTERED
        # ═══════════════════════════════════════════════════════════════
        cx = w // 2
        cy = int(h * 0.40)  # 40% from top = CENTER
        
        # ═══════════════════════════════════════════════════════════════
        #  LOGO SIZE - LARGE
        # ═══════════════════════════════════════════════════════════════
        base_size = int(min(w, h) * 0.22)
        logo_size = int(base_size * max(0.1, self._logo_scale))
        
        # Holographic glow effect - multiple layers
        glow_size = logo_size + int(logo_size * 0.6)
        
        # Outer cyan glow
        outer_glow = QRadialGradient(cx, cy, glow_size)
        outer_glow.setColorAt(0, QColor(0, 255, 255, int(80 * self._glow_intensity)))
        outer_glow.setColorAt(0.3, QColor(0, 255, 255, int(40 * self._glow_intensity)))
        outer_glow.setColorAt(0.6, QColor(255, 0, 255, int(30 * self._glow_intensity)))
        outer_glow.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.setBrush(outer_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - glow_size, cy - glow_size, glow_size * 2, glow_size * 2)
        
        # Chromatic aberration effect for logo
        if self.logo_pixmap and not self.logo_pixmap.isNull():
            scaled_logo = self.logo_pixmap.scaled(
                logo_size, logo_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Draw with slight color offsets for hologram effect
            painter.setOpacity(self._logo_opacity * 0.3 * self._hologram_flicker)
            painter.drawPixmap(
                cx - scaled_logo.width() // 2 - 3,
                cy - scaled_logo.height() // 2,
                scaled_logo
            )
            
            painter.setOpacity(self._logo_opacity * self._hologram_flicker)
            painter.drawPixmap(
                cx - scaled_logo.width() // 2,
                cy - scaled_logo.height() // 2,
                scaled_logo
            )
        else:
            # Placeholder circle with hand icon - holographic style
            
            # Outer ring glow
            painter.setPen(QPen(QColor(0, 255, 255, int(150 * self._glow_intensity)), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx - logo_size//2 - 5, cy - logo_size//2 - 5, 
                               logo_size + 10, logo_size + 10)
            
            # Main circle with gradient
            gradient = QLinearGradient(cx - logo_size//2, cy - logo_size//2, 
                                       cx + logo_size//2, cy + logo_size//2)
            gradient.setColorAt(0, QColor(0, 255, 255, 150))
            gradient.setColorAt(0.5, QColor(255, 0, 255, 100))
            gradient.setColorAt(1, QColor(0, 255, 255, 150))
            
            painter.setBrush(QColor(10, 20, 30, 200))
            painter.setPen(QPen(QBrush(gradient), 4))
            painter.drawEllipse(cx - logo_size//2, cy - logo_size//2, logo_size, logo_size)
            
            # Hand icon
            painter.setFont(QFont("Segoe UI Emoji", logo_size // 2))
            painter.setPen(QColor(0, 255, 255, 255))
            painter.drawText(
                QRect(cx - logo_size//2, cy - logo_size//2, logo_size, logo_size),
                Qt.AlignCenter,
                "✋"
            )
        
        # Holographic scan line over logo
        scan_y = cy - logo_size//2 + ((self.frame_count * 2) % logo_size)
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        painter.drawLine(cx - logo_size//2, int(scan_y), cx + logo_size//2, int(scan_y))
        
        painter.setOpacity(1.0)
    
    def _draw_title(self, painter, w, h):
        """Draw title - MOVED DOWN with holographic effect"""
        if self._title_opacity < 0.01:
            return
        
        painter.setOpacity(self._title_opacity * self._hologram_flicker)
        
        cx = w // 2
        # ═══════════════════════════════════════════════════════════════
        #  TITLE POSITION - MOVED DOWN (below centered logo)
        # ═══════════════════════════════════════════════════════════════
        title_y = int(h * 0.60)
        
        base_font_size = int(min(w, h) * 0.055)
        font_size = int(base_font_size * self._title_scale)
        
        font = QFont("Segoe UI", font_size, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 12)
        painter.setFont(font)
        
        # Chromatic aberration / hologram offset
        # Cyan layer (offset left)
        painter.setPen(QColor(0, 255, 255, int(100 * self._glow_intensity)))
        painter.drawText(QRect(-3, title_y, w, int(h * 0.1)), Qt.AlignCenter, self.app_name)
        
        # Magenta layer (offset right)
        painter.setPen(QColor(255, 0, 255, int(80 * self._glow_intensity)))
        painter.drawText(QRect(3, title_y, w, int(h * 0.1)), Qt.AlignCenter, self.app_name)
        
        # Glow layers
        glow_layers = [
            (12, QColor(0, 255, 255, int(20 * self._glow_intensity))),
            (8, QColor(0, 255, 255, int(40 * self._glow_intensity))),
            (4, QColor(255, 0, 255, int(30 * self._glow_intensity))),
            (2, QColor(255, 255, 255, int(40 * self._glow_intensity))),
        ]
        
        for offset, color in glow_layers:
            painter.setPen(color)
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        painter.drawText(QRect(dx, title_y + dy, w, int(h * 0.1)), 
                                        Qt.AlignCenter, self.app_name)
        
        # Main text with gradient
        gradient = QLinearGradient(cx - 200, title_y, cx + 200, title_y + 70)
        gradient.setColorAt(0, QColor(0, 255, 255))
        gradient.setColorAt(0.3, QColor(255, 255, 255))
        gradient.setColorAt(0.5, QColor(255, 0, 255))
        gradient.setColorAt(0.7, QColor(255, 255, 255))
        gradient.setColorAt(1, QColor(0, 255, 255))
        
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.drawText(QRect(0, title_y, w, int(h * 0.1)), Qt.AlignCenter, self.app_name)
        
        painter.setOpacity(1.0)
    
    def _draw_tagline(self, painter, w, h):
        """Draw tagline - MOVED DOWN"""
        if self._tagline_opacity < 0.01:
            return
        
        painter.setOpacity(self._tagline_opacity * self._hologram_flicker)
        
        # ═══════════════════════════════════════════════════════════════
        #  TAGLINE POSITION - MOVED DOWN
        # ═══════════════════════════════════════════════════════════════
        tagline_y = int(h * 0.70)
        
        font_size = int(min(w, h) * 0.022)
        font = QFont("Segoe UI", font_size)
        font.setItalic(True)
        painter.setFont(font)
        
        # Holographic glow
        painter.setPen(QColor(0, 255, 255, int(60 * self._glow_intensity)))
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            painter.drawText(QRect(dx, tagline_y + dy, w, int(h * 0.05)), 
                            Qt.AlignCenter, self.tagline)
        
        painter.setPen(QColor(200, 255, 255))
        painter.drawText(QRect(0, tagline_y, w, int(h * 0.05)), Qt.AlignCenter, self.tagline)
        
        painter.setOpacity(1.0)
    
    def _draw_loading_text(self, painter, w, h):
        """Draw loading text - MOVED DOWN"""
        # ═══════════════════════════════════════════════════════════════
        #  LOADING TEXT POSITION - MOVED DOWN
        # ═══════════════════════════════════════════════════════════════
        loading_y = int(h * 0.80)
        
        font_size = int(min(w, h) * 0.016)
        font = QFont("Consolas", font_size)
        painter.setFont(font)
        
        displayed_text = self.current_loading_text[:self._typing_index]
        show_cursor = (self.frame_count // 15) % 2 == 0
        cursor = "▌" if show_cursor else " "
        
        # Glow
        painter.setPen(QColor(0, 255, 255, int(60 * self._hologram_flicker)))
        for dx, dy in [(-1, -1), (1, 1)]:
            painter.drawText(QRect(dx, loading_y + dy, w, int(h * 0.04)), 
                            Qt.AlignCenter, displayed_text + cursor)
        
        painter.setPen(QColor(0, 255, 255, int(230 * self._hologram_flicker)))
        painter.drawText(QRect(0, loading_y, w, int(h * 0.04)), 
                        Qt.AlignCenter, displayed_text + cursor)
    
    def _draw_progress_bar(self, painter, w, h):
        """Draw progress bar - MOVED DOWN with holographic effect"""
        bar_width = int(w * 0.25)
        bar_height = int(h * 0.008)
        bar_x = (w - bar_width) // 2
        # ═══════════════════════════════════════════════════════════════
        #  PROGRESS BAR POSITION - MOVED DOWN
        # ═══════════════════════════════════════════════════════════════
        bar_y = int(h * 0.88)
        
        painter.setPen(Qt.NoPen)
        
        # Outer glow
        glow = QRadialGradient(w // 2, bar_y, bar_width * 0.6)
        glow.setColorAt(0, QColor(0, 255, 255, int(20 * self._hologram_flicker)))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(glow)
        painter.drawRect(bar_x - 50, bar_y - 20, bar_width + 100, 40)
        
        # Background
        painter.setBrush(QColor(10, 20, 30, 200))
        painter.setPen(QPen(QColor(0, 255, 255, 100), 1))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 3, 3)
        
        # Progress fill
        progress_width = int(bar_width * self._progress)
        if progress_width > 0:
            gradient = QLinearGradient(bar_x, bar_y, bar_x + bar_width, bar_y)
            gradient.setColorAt(0, QColor(0, 255, 255))
            gradient.setColorAt(0.5, QColor(255, 0, 255))
            gradient.setColorAt(1, QColor(0, 255, 136))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 3, 3)
            
            # Glowing tip
            tip_x = bar_x + progress_width
            tip_glow = QRadialGradient(tip_x, bar_y + bar_height // 2, 30)
            tip_glow.setColorAt(0, QColor(255, 255, 255, int(255 * self._glow_intensity * self._hologram_flicker)))
            tip_glow.setColorAt(0.3, QColor(0, 255, 255, int(200 * self._glow_intensity * self._hologram_flicker)))
            tip_glow.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(tip_glow)
            painter.drawEllipse(int(tip_x - 20), int(bar_y - 12), 40, 32)
            
            # Shine effect
            shine = QLinearGradient(bar_x, bar_y, bar_x, bar_y + bar_height)
            shine.setColorAt(0, QColor(255, 255, 255, 120))
            shine.setColorAt(0.5, QColor(255, 255, 255, 40))
            shine.setColorAt(1, QColor(255, 255, 255, 0))
            
            painter.setBrush(shine)
            painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height // 2, 2, 2)
        
        # Percentage text
        font_size = int(min(w, h) * 0.015)
        painter.setFont(QFont("Segoe UI", font_size, QFont.Bold))
        percent = int(self._progress * 100)
        
        percent_y = bar_y + int(h * 0.020)
        
        # Glow
        painter.setPen(QColor(0, 255, 255, int(80 * self._glow_intensity * self._hologram_flicker)))
        for dx, dy in [(-1, -1), (1, 1)]:
            painter.drawText(QRect(bar_x + dx, percent_y + dy, bar_width, int(h * 0.03)), 
                            Qt.AlignCenter, f"{percent}%")
        
        painter.setPen(QColor(200, 255, 255))
        painter.drawText(QRect(bar_x, percent_y, bar_width, int(h * 0.03)), 
                        Qt.AlignCenter, f"{percent}%")
    
    def _draw_decorations(self, painter, w, h):
        """Draw corner decorations with holographic effect"""
        corner_length = int(min(w, h) * 0.05)
        corner_offset = int(min(w, h) * 0.025)
        
        glow = int(150 * self._glow_intensity * self._hologram_flicker)
        
        # Cyan corners
        pen = QPen(QColor(0, 255, 255, glow), 2)
        painter.setPen(pen)
        
        # Top-left
        painter.drawLine(corner_offset, corner_offset, 
                        corner_offset, corner_offset + corner_length)
        painter.drawLine(corner_offset, corner_offset, 
                        corner_offset + corner_length, corner_offset)
        
        # Top-right
        painter.drawLine(w - corner_offset, corner_offset, 
                        w - corner_offset, corner_offset + corner_length)
        painter.drawLine(w - corner_offset, corner_offset, 
                        w - corner_offset - corner_length, corner_offset)
        
        # Bottom-left
        painter.drawLine(corner_offset, h - corner_offset, 
                        corner_offset, h - corner_offset - corner_length)
        painter.drawLine(corner_offset, h - corner_offset, 
                        corner_offset + corner_length, h - corner_offset)
        
        # Bottom-right
        painter.drawLine(w - corner_offset, h - corner_offset, 
                        w - corner_offset, h - corner_offset - corner_length)
        painter.drawLine(w - corner_offset, h - corner_offset, 
                        w - corner_offset - corner_length, h - corner_offset)
        
        # Magenta offset (chromatic aberration)
        pen = QPen(QColor(255, 0, 255, glow // 2), 2)
        painter.setPen(pen)
        
        offset = 2
        painter.drawLine(corner_offset + offset, corner_offset, 
                        corner_offset + offset, corner_offset + corner_length)
        painter.drawLine(w - corner_offset + offset, corner_offset, 
                        w - corner_offset + offset, corner_offset + corner_length)
        
        # Corner dots
        dot_pen = QPen(QColor(0, 255, 255, glow), 6)
        painter.setPen(dot_pen)
        painter.drawPoint(corner_offset, corner_offset)
        painter.drawPoint(w - corner_offset, corner_offset)
        painter.drawPoint(corner_offset, h - corner_offset)
        painter.drawPoint(w - corner_offset, h - corner_offset)
        
        # Additional tech decorations
        # Small brackets at edges
        bracket_size = int(min(w, h) * 0.015)
        painter.setPen(QPen(QColor(0, 255, 255, glow // 2), 1))
        
        # Top center brackets
        mid_x = w // 2
        painter.drawLine(mid_x - 50, 15, mid_x - 50, 15 + bracket_size)
        painter.drawLine(mid_x - 50, 15, mid_x - 35, 15)
        painter.drawLine(mid_x + 50, 15, mid_x + 50, 15 + bracket_size)
        painter.drawLine(mid_x + 50, 15, mid_x + 35, 15)
    
    def _draw_version(self, painter, w, h):
        """Draw version - AT BOTTOM"""
        # ═══════════════════════════════════════════════════════════════
        #  VERSION POSITION - AT VERY BOTTOM
        # ═══════════════════════════════════════════════════════════════
        version_y = int(h * 0.95)
        
        font_size = int(min(w, h) * 0.012)
        painter.setFont(QFont("Segoe UI", font_size))
        painter.setPen(QColor(0, 255, 255, int(100 * self._hologram_flicker)))
        
        version_text = f"{self.version}  •  {self.subtitle}  •  © 2026 Aurevix"
        painter.drawText(QRect(0, version_y, w, int(h * 0.03)), 
                        Qt.AlignCenter, version_text)
    
    # ════════════════════════════════════════════════════════════════════
    #                         EVENTS
    # ════════════════════════════════════════════════════════════════════
    
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._finish_splash()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Space, Qt.Key_Return):
            self._finish_splash()
    
    def closeEvent(self, event):
        """Clean up on close"""
        event.accept()


# ════════════════════════════════════════════════════════════════════════════
#                              INTEGRATION
# ════════════════════════════════════════════════════════════════════════════

def show_splash_then_main(main_window_class=None, splash_duration=12000):
    """
    Usage:
        from splash_screen import show_splash_then_main
        from main_window import MainWindow
        
        if __name__ == "__main__":
            show_splash_then_main(MainWindow, splash_duration=12000)
    """
    app = QApplication.instance() or QApplication(sys.argv)
    
    splash = SplashScreen(duration=splash_duration)
    
    main_window = None
    
    def on_splash_finished():
        nonlocal main_window
        if main_window_class:
            main_window = main_window_class()
            main_window.show()
        else:
            app.quit()
    
    splash.splashFinished.connect(on_splash_finished)
    splash.show()
    
    return app.exec()


# ════════════════════════════════════════════════════════════════════════════
#                              TEST
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  AUREVIX SPLASH SCREEN")
    print("  FUTURISTIC CYBERPUNK HOLOGRAM EFFECT")
    print("  ✅ BINARY DATA STREAMS (PURE 0s & 1s)")
    print("═" * 60)
    print("  Layout:")
    print("    • Logo: CENTERED (40% from top)")
    print("    • Title: 60% from top")
    print("    • Tagline: 70% from top")
    print("    • Loading: 80% from top")
    print("    • Progress: 88% from top")
    print("    • Version: 95% from top")
    print("")
    print("  Cyberpunk Effects:")
    print("    • Scan lines")
    print("    • ✅ BINARY Data streams (0 & 1 only)")
    print("    • Hexagonal grid")
    print("    • Circuit patterns")
    print("    • Glitch effects")
    print("    • Holographic rings")
    print("    • Chromatic aberration")
    print("    • Neon glow")
    print("    • Perspective grid")
    print("")
    print("  Controls:")
    print("    • Right-click / ESC / SPACE to skip")
    print("═" * 60 + "\n")
    
    app = QApplication(sys.argv)
    
    splash = SplashScreen(duration=12000)
    
    def on_finished():
        print("\n  ✓ Splash complete!")
        app.quit()
    
    splash.splashFinished.connect(on_finished)
    splash.show()
    
    sys.exit(app.exec())
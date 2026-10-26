"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        ADAPTIVE TRAINER MODE                                 ║
║                   🤖 AI-Powered Difficulty System 🤖                          ║
║                         Version 1.0                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This mode uses AI to adjust training difficulty:
- Starts with simple gestures
- Increases difficulty based on performance
- Reduces difficulty if user struggles
- Adjusts hold time and reaction time automatically
- Shows current difficulty level with visual meter
- Tracks progression over time
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QApplication, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation,
    QEasingCurve, Property, QRectF
)
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPen, QBrush,
    QColor, QLinearGradient, QRadialGradient, QConicalGradient
)
import cv2
import time
import random
import math
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mode_manager
    import config
except ImportError:
    mode_manager = None
    config = None


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 NEON COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Neon:
    CYAN = "#00f5ff"
    MAGENTA = "#ff00ff"
    YELLOW = "#f0ff00"
    GREEN = "#00ff9f"
    ORANGE = "#ff6b00"
    RED = "#ff0055"
    PURPLE = "#bf00ff"
    WHITE = "#ffffff"
    TEXT = "#e0e8ff"
    TEXT_DIM = "#5a7090"
    DARK_BG = "#050a15"


# ═══════════════════════════════════════════════════════════════════════════════
# 🎚️ DIFFICULTY METER WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class DifficultyMeterWidget(QWidget):
    """
    Visual meter showing current AI difficulty level
    Animated gauge with color gradient
    """
   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(250, 250)
       
        self._level = 1  # 1-10
        self._target_level = 1
        self._display_level = 1.0
       
        # Animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(30)
       
        # Level names
        self.level_names = {
            1: "BEGINNER",
            2: "EASY",
            3: "CASUAL",
            4: "NORMAL",
            5: "MODERATE",
            6: "CHALLENGING",
            7: "HARD",
            8: "EXPERT",
            9: "MASTER",
            10: "LEGENDARY"
        }
   
    def set_level(self, level):
        """Set target difficulty level (1-10)"""
        self._target_level = max(1, min(10, level))
   
    def get_level(self):
        return self._level
   
    def animate(self):
        """Smooth animation to target level"""
        diff = self._target_level - self._display_level
        if abs(diff) > 0.05:
            self._display_level += diff * 0.1
            self._level = round(self._display_level)
            self.update()
   
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
       
        center_x = self.width() / 2
        center_y = self.height() / 2 + 20
        radius = 90
       
        # Draw background arc
        self.draw_background_arc(painter, center_x, center_y, radius)
       
        # Draw level arc
        self.draw_level_arc(painter, center_x, center_y, radius)
       
        # Draw center circle
        self.draw_center(painter, center_x, center_y)
       
        # Draw title
        self.draw_title(painter)
       
        # Draw level markers
        self.draw_markers(painter, center_x, center_y, radius)
   
    def draw_background_arc(self, painter, cx, cy, radius):
        """Draw background arc"""
        pen = QPen(QColor(30, 40, 60), 20)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
       
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 225 * 16, -270 * 16)
   
    def draw_level_arc(self, painter, cx, cy, radius):
        """Draw colored level arc"""
        # Calculate progress (1-10 mapped to 0-270 degrees)
        progress = (self._display_level - 1) / 9
        span_angle = int(-progress * 270 * 16)
       
        # Color based on level
        if self._display_level <= 3:
            color = QColor(Neon.GREEN)
        elif self._display_level <= 5:
            color = QColor(Neon.CYAN)
        elif self._display_level <= 7:
            color = QColor(Neon.YELLOW)
        elif self._display_level <= 9:
            color = QColor(Neon.ORANGE)
        else:
            color = QColor(Neon.RED)
       
        pen = QPen(color, 20)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
       
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 225 * 16, span_angle)
   
    def draw_center(self, painter, cx, cy):
        """Draw center display"""
        # Background circle
        painter.setBrush(QBrush(QColor(10, 15, 30)))
        painter.setPen(QPen(QColor(Neon.ORANGE), 3))
        painter.drawEllipse(int(cx - 50), int(cy - 50), 100, 100)
       
        # Level number
        painter.setPen(QColor(Neon.ORANGE))
        font = QFont("Consolas", 36, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(cx - 50, cy - 30, 100, 50), Qt.AlignCenter, str(self._level))
       
        # Level name
        painter.setPen(QColor(Neon.TEXT))
        font = QFont("Consolas", 9, QFont.Bold)
        painter.setFont(font)
        level_name = self.level_names.get(self._level, "UNKNOWN")
        painter.drawText(QRectF(cx - 50, cy + 10, 100, 30), Qt.AlignCenter, level_name)
   
    def draw_title(self, painter):
        """Draw title"""
        painter.setPen(QColor(Neon.ORANGE))
        font = QFont("Consolas", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 5, self.width(), 30), Qt.AlignCenter, "◈ AI DIFFICULTY")
   
    def draw_markers(self, painter, cx, cy, radius):
        """Draw level markers"""
        painter.setPen(QColor(Neon.TEXT_DIM))
        font = QFont("Consolas", 8)
        painter.setFont(font)
       
        for i in [1, 5, 10]:
            # Calculate position
            angle_deg = 225 - ((i - 1) / 9 * 270)
            angle_rad = math.radians(angle_deg)
           
            marker_radius = radius + 25
            x = cx + marker_radius * math.cos(angle_rad)
            y = cy - marker_radius * math.sin(angle_rad)
           
            painter.drawText(QRectF(x - 15, y - 10, 30, 20), Qt.AlignCenter, str(i))


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 PERFORMANCE GRAPH WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class PerformanceGraphWidget(QWidget):
    """
    Shows performance history over time
    Line graph with success rate
    """
   
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 150)
        self.setMaximumHeight(180)
       
        # Performance history (last 20 attempts)
        self.history = []
        self.max_history = 20
   
    def add_result(self, success):
        """Add a result (True/False)"""
        self.history.append(1 if success else 0)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.update()
   
    def get_recent_accuracy(self, n=5):
        """Get accuracy of last n attempts"""
        if not self.history:
            return 0.5
        recent = self.history[-n:] if len(self.history) >= n else self.history
        return sum(recent) / len(recent) if recent else 0.5
   
    def clear(self):
        """Clear history"""
        self.history = []
        self.update()
   
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
       
        # Background
        painter.fillRect(self.rect(), QColor(5, 10, 20))
       
        # Border
        painter.setPen(QPen(QColor(Neon.CYAN), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
       
        # Title
        painter.setPen(QColor(Neon.CYAN))
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(10, 5, 200, 25), Qt.AlignLeft | Qt.AlignVCenter,
                        "◈ PERFORMANCE HISTORY")
       
        # Draw grid
        self.draw_grid(painter)
       
        # Draw graph
        if len(self.history) >= 2:
            self.draw_graph(painter)
       
        # Draw legend
        self.draw_legend(painter)
   
    def draw_grid(self, painter):
        """Draw grid lines"""
        painter.setPen(QPen(QColor(40, 50, 70), 1))
       
        # Horizontal lines (25%, 50%, 75%)
        graph_top = 35
        graph_bottom = self.height() - 30
        graph_height = graph_bottom - graph_top
       
        for pct in [0.25, 0.5, 0.75]:
            y = graph_bottom - (pct * graph_height)
            painter.drawLine(40, int(y), self.width() - 20, int(y))
       
        # Percentage labels
        painter.setPen(QColor(Neon.TEXT_DIM))
        font = QFont("Consolas", 8)
        painter.setFont(font)
       
        for pct, label in [(0, "0%"), (0.5, "50%"), (1.0, "100%")]:
            y = graph_bottom - (pct * graph_height)
            painter.drawText(QRectF(5, y - 8, 35, 16), Qt.AlignRight | Qt.AlignVCenter, label)
   
    def draw_graph(self, painter):
        """Draw the performance line graph"""
        graph_left = 45
        graph_right = self.width() - 25
        graph_top = 35
        graph_bottom = self.height() - 30
        graph_width = graph_right - graph_left
        graph_height = graph_bottom - graph_top
       
        # Calculate points
        points = []
        step = graph_width / (self.max_history - 1)
       
        for i, value in enumerate(self.history):
            x = graph_left + (i * step)
            y = graph_bottom - (value * graph_height)
            points.append((x, y))
       
        if len(points) < 2:
            return
       
        # Draw filled area
        gradient = QLinearGradient(0, graph_top, 0, graph_bottom)
        gradient.setColorAt(0, QColor(0, 255, 159, 100))
        gradient.setColorAt(1, QColor(0, 255, 159, 20))
       
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(points[0][0], graph_bottom)
       
        for x, y in points:
            path.lineTo(x, y)
       
        path.lineTo(points[-1][0], graph_bottom)
        path.closeSubpath()
       
        painter.fillPath(path, QBrush(gradient))
       
        # Draw line
        pen = QPen(QColor(Neon.GREEN), 3)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
       
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
       
        # Draw points
        painter.setBrush(QBrush(QColor(Neon.WHITE)))
        painter.setPen(QPen(QColor(Neon.GREEN), 2))
       
        for x, y in points:
            painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)
   
    def draw_legend(self, painter):
        """Draw legend"""
        accuracy = self.get_recent_accuracy() * 100
       
        painter.setPen(QColor(Neon.GREEN) if accuracy >= 60 else QColor(Neon.RED))
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
       
        text = f"Recent Accuracy: {accuracy:.0f}%"
        painter.drawText(QRectF(self.width() - 180, 5, 170, 25),
                        Qt.AlignRight | Qt.AlignVCenter, text)


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 AI DIFFICULTY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AIDifficultyEngine:
    """
    AI engine that adjusts difficulty based on performance
   
    Factors:
    - Success rate (last N attempts)
    - Reaction time average
    - Stability of performance
    - Gesture complexity
    """
   
    def __init__(self):
        self.level = 1  # 1-10
        self.min_level = 1
        self.max_level = 10
       
        # Performance tracking
        self.recent_results = []  # True/False for last N
        self.recent_times = []    # Reaction times
        self.window_size = 5      # Look at last 5 attempts
       
        # Difficulty parameters
        self.hold_time = 2.5      # Starting hold time
        self.time_limit = 4.0     # Starting time limit
       
        # Thresholds
        self.increase_threshold = 0.8   # 80% success = increase
        self.decrease_threshold = 0.4   # 40% success = decrease
       
        # Gestures by difficulty
        self.gesture_pools = {
            1: ["FIST", "PALM"],
            2: ["FIST", "PALM", "INDEX"],
            3: ["FIST", "PALM", "INDEX", "THUMB"],
            4: ["FIST", "PALM", "INDEX", "THUMB", "PEACE"],
            5: ["FIST", "PALM", "INDEX", "THUMB", "PEACE", "THREE"],
            6: ["INDEX", "THUMB", "PEACE", "THREE", "SHAKA"],
            7: ["INDEX", "PEACE", "THREE", "SHAKA"],
            8: ["PEACE", "THREE", "SHAKA"],
            9: ["THREE", "SHAKA"],
            10: ["SHAKA"],  # Hardest gesture only
        }
   
    def add_result(self, success, reaction_time=None):
        """Add a training result"""
        self.recent_results.append(success)
        if len(self.recent_results) > self.window_size:
            self.recent_results.pop(0)
       
        if reaction_time:
            self.recent_times.append(reaction_time)
            if len(self.recent_times) > self.window_size:
                self.recent_times.pop(0)
       
        # Adjust difficulty
        self.adjust_difficulty()
   
    def get_success_rate(self):
        """Get current success rate"""
        if not self.recent_results:
            return 0.5
        return sum(self.recent_results) / len(self.recent_results)
   
    def get_avg_reaction_time(self):
        """Get average reaction time"""
        if not self.recent_times:
            return 2.0
        return sum(self.recent_times) / len(self.recent_times)
   
    def adjust_difficulty(self):
        """AI adjusts difficulty based on performance"""
        if len(self.recent_results) < self.window_size:
            return  # Not enough data yet
       
        success_rate = self.get_success_rate()
       
        # Increase difficulty
        if success_rate >= self.increase_threshold:
            if self.level < self.max_level:
                self.level += 1
                self.update_parameters()
                print(f"🤖 AI: Difficulty INCREASED to {self.level}")
       
        # Decrease difficulty
        elif success_rate <= self.decrease_threshold:
            if self.level > self.min_level:
                self.level -= 1
                self.update_parameters()
                print(f"🤖 AI: Difficulty DECREASED to {self.level}")
   
    def update_parameters(self):
        """Update hold time and time limit based on level"""
        # Hold time: 2.5s at level 1, 0.5s at level 10
        self.hold_time = 2.5 - ((self.level - 1) * 0.22)
        self.hold_time = max(0.5, self.hold_time)
       
        # Time limit: 4s at level 1, 1.5s at level 10
        self.time_limit = 4.0 - ((self.level - 1) * 0.28)
        self.time_limit = max(1.5, self.time_limit)
   
    def get_next_gesture(self, gestures_data):
        """Get next gesture appropriate for current level"""
        pool = self.gesture_pools.get(self.level, ["FIST"])
       
        # Find matching gestures from data
        available = [g for g in gestures_data if g[1] in pool]
       
        if not available:
            available = gestures_data  # Fallback
       
        return random.choice(available)
   
    def get_hold_time(self):
        return self.hold_time
   
    def get_time_limit(self):
        return self.time_limit
   
    def reset(self):
        """Reset to initial state"""
        self.level = 1
        self.recent_results = []
        self.recent_times = []
        self.hold_time = 2.5
        self.time_limit = 4.0


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 ADAPTIVE TRAINER MODE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AdaptiveTrainerMode(QWidget):
    """
    Adaptive Trainer Mode - AI adjusts difficulty as you improve
   
    Features:
    - Dynamic difficulty adjustment
    - Performance tracking
    - Variable hold time
    - Visual difficulty meter
    - Progression system
    """
   
    mode_closed = Signal()
   
    def __init__(self, parent=None, tracker=None):
        super().__init__(parent)
   
        # ✅ USE SHARED TRACKER (passed from parent)
        self.tracker = tracker
   
        self.setWindowTitle("◈ ADAPTIVE TRAINER")

        self.setMinimumSize(1400, 900)
       
        # ═══ AI ENGINE ═══
        self.ai_engine = AIDifficultyEngine()
       
        # ═══ STATE ═══
        self.is_training = False
        self.is_waiting_for_gesture = False
        self.current_gesture = None
        self.current_gesture_emoji = ""
        self.gesture_hold_start = None
        self.gesture_start_time = 0
       
        # ═══ STATS ═══
        self.total_attempts = 0
        self.total_success = 0
        self.session_start_time = None
        self.best_streak = 0
        self.current_streak = 0
       
        # ═══ GESTURES ═══
        self.gestures = [
            ("☝️", "INDEX", Neon.CYAN, [0, 1, 0, 0, 0]),
            ("✌️", "PEACE", Neon.GREEN, [0, 1, 1, 0, 0]),
            ("🤟", "THREE", Neon.PURPLE, [0, 1, 1, 1, 0]),
            ("✋", "PALM", Neon.ORANGE, [1, 1, 1, 1, 1]),
            ("✊", "FIST", Neon.RED, [0, 0, 0, 0, 0]),
            ("👍", "THUMB", Neon.YELLOW, [1, 0, 0, 0, 0]),
            ("🤙", "SHAKA", Neon.MAGENTA, [1, 0, 0, 0, 1]),
        ]
       
        # ═══ BUILD UI ═══
        self.setup_ui()
        self.apply_theme()
       
        # ═══ TIMERS ═══
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_feed)
       
        self.gesture_check_timer = QTimer()
        self.gesture_check_timer.timeout.connect(self.check_gesture)
       
        self.hold_timer = QTimer()
        self.hold_timer.timeout.connect(self.update_hold_progress)
       
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_timeout)
       
        self.next_gesture_timer = QTimer()
        self.next_gesture_timer.setSingleShot(True)
        self.next_gesture_timer.timeout.connect(self.next_gesture)
       
        # ═══ FPS ═══
        self.frame_count = 0
        self.current_fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.calculate_fps)
        self.fps_timer.start(1000)
       
        # ═══ SESSION TIMER ═══
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.update_session_time)
       
        print("🤖 Adaptive Trainer Mode Initialized")
   
    def setup_ui(self):
        """Build UI with scroll support"""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
   
        # Header (fixed at top)
        header = self.build_header()
        main.addWidget(header)
   
        # ═══════════════════════════════════════════════════════════════
        # ✅ SCROLLABLE CONTENT AREA
        # ═══════════════════════════════════════════════════════════════
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setStyleSheet("""
            #scrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(30, 40, 60, 0.5);
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 107, 0, 0.6);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 107, 0, 0.9);
            }
            QScrollBar:horizontal {
                background: rgba(30, 40, 60, 0.5);
                height: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 107, 0, 0.6);
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
        """)
   
        # Content widget inside scroll
        content = QWidget()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 15, 20, 50)  # ← Bottom margin 15→50
        content_layout.setSpacing(15)

        # Main row: Camera + Difficulty + Training
        main_row = self.build_main_row()
        content_layout.addWidget(main_row)

        # Performance graph
        graph_row = self.build_graph_row()
        content_layout.addWidget(graph_row)

        # AI info row
        ai_row = self.build_ai_info_row()
        content_layout.addWidget(ai_row)

        # ═══════════════════════════════════════════════════════════════
        # ✅ CRITICAL: Add extra bottom spacing to prevent footer overlap
        # ═══════════════════════════════════════════════════════════════
        content_layout.addSpacing(80)  # Extra padding before stretch
        # ═══════════════════════════════════════════════════════════════

        content_layout.addStretch()

        scroll_area.setWidget(content)
        main.addWidget(scroll_area, 1)
   
        # Footer (fixed at bottom)
        footer = self.build_footer()
        main.addWidget(footer)    
    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════
   
    def build_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header")
       
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(25)
       
        # Back Button
        self.back_btn = QPushButton("◄  BACK")
        self.back_btn.setFixedSize(100, 45)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.back_btn.setObjectName("backBtn")
        self.back_btn.clicked.connect(self.close_mode)
        layout.addWidget(self.back_btn)
       
        # Logo
        logo = QLabel("🤖")
        logo.setFont(QFont("Segoe UI Emoji", 28))
        logo.setFixedWidth(50)
        layout.addWidget(logo)
       
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
       
        title = QLabel("ADAPTIVE TRAINER")
        title.setFont(QFont("Consolas", 20, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.ORANGE};")
        title_box.addWidget(title)
       
        subtitle = QLabel("AI-POWERED DIFFICULTY SYSTEM")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
       
        layout.addLayout(title_box)
        layout.addStretch()
       
        # Stats
        self.stat_level = self.make_stat("LEVEL", "1", Neon.ORANGE)
        layout.addWidget(self.stat_level)
       
        self.stat_streak = self.make_stat("STREAK", "0", Neon.YELLOW)
        layout.addWidget(self.stat_streak)
       
        self.stat_accuracy = self.make_stat("ACCURACY", "0%", Neon.GREEN)
        layout.addWidget(self.stat_accuracy)
       
        self.stat_time = self.make_stat("TIME", "0:00", Neon.CYAN)
        layout.addWidget(self.stat_time)
       
        self.stat_fps = self.make_stat("FPS", "0", Neon.MAGENTA)
        layout.addWidget(self.stat_fps)
       
        layout.addStretch()
       
        # Reset Button
        self.reset_btn = QPushButton("⟲  RESET")
        self.reset_btn.setFixedSize(120, 45)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self.reset_training)
        layout.addWidget(self.reset_btn)
       
        return header
   
    def make_stat(self, label, value, color):
        box = QFrame()
        box.setFixedSize(95, 50)
       
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 5, 8, 5)
        lay.setSpacing(2)
       
        lbl = QLabel(label)
        lbl.setFont(QFont("Consolas", 7))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        lay.addWidget(lbl)
       
        val = QLabel(value)
        val.setFont(QFont("Consolas", 14, QFont.Bold))
        val.setAlignment(Qt.AlignCenter)
        val.setStyleSheet(f"color: {color};")
        val.setObjectName("val")
        lay.addWidget(val)
       
        r, g, b = self.hex_rgb(color)
        box.setStyleSheet(f"""
            QFrame {{
                background: rgba({r}, {g}, {b}, 0.1);
                border: 1px solid {color};
                border-radius: 8px;
            }}
        """)
       
        return box
   
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN ROW
    # ═══════════════════════════════════════════════════════════════════════════
   
    def build_main_row(self):
        """✅ RESPONSIVE main row"""
        container = QFrame()
        container.setMinimumHeight(380)  # Reduced from 420
   
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)  # Reduced spacing
   
        # Camera Panel - RESPONSIVE width
        cam_panel = self.build_camera_panel()
        cam_panel.setMinimumWidth(380)  # Min instead of fixed
        cam_panel.setMaximumWidth(480)  # Max width
        layout.addWidget(cam_panel, 2)  # Stretch factor 2
   
        # Difficulty Meter Panel - RESPONSIVE
        diff_panel = self.build_difficulty_panel()
        diff_panel.setMinimumWidth(250)
        diff_panel.setMaximumWidth(300)
        layout.addWidget(diff_panel, 1)  # Stretch factor 1
   
        # Training Panel - Takes remaining space
        train_panel = self.build_training_panel()
        train_panel.setMinimumWidth(350)
        layout.addWidget(train_panel, 2)  # Stretch factor 2
   
        return container
   
    def build_camera_panel(self):
        panel = QFrame()
        panel.setMinimumWidth(380)   # ✅ Min instead of fixed
        panel.setMaximumWidth(480)   # ✅ Max width
        panel.setObjectName("camPanel")
   
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)  # Reduced padding
        layout.setSpacing(10)
   
        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("◉ CAMERA FEED")
        cam_title.setFont(QFont("Consolas", 12, QFont.Bold))  # Smaller font
        cam_title.setStyleSheet(f"color: {Neon.ORANGE};")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        self.cam_status = QLabel("● OFFLINE")
        self.cam_status.setFont(QFont("Consolas", 9, QFont.Bold))
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
        cam_header.addWidget(self.cam_status)
        layout.addLayout(cam_header)
   
        # Camera Display - RESPONSIVE size
        self.camera_label = QLabel("⟨ START TRAINING ⟩\n\nAI will adapt to your skill")
        self.camera_label.setMinimumSize(340, 240)  # ✅ Min size
        self.camera_label.setMaximumSize(420, 300)  # ✅ Max size
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setObjectName("camDisplay")
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
   
        # Detection status
        self.detection_label = QLabel("Waiting for gesture...")
        self.detection_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.detection_label.setAlignment(Qt.AlignCenter)
        self.detection_label.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.detection_label)
   
        return panel
   
    def build_difficulty_panel(self):
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setObjectName("diffPanel")
       
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)
       
        # Difficulty meter
        self.difficulty_meter = DifficultyMeterWidget()
        layout.addWidget(self.difficulty_meter, alignment=Qt.AlignCenter)
       
        # Parameters display
        params_frame = QFrame()
        params_frame.setObjectName("paramsFrame")
        params_layout = QVBoxLayout(params_frame)
        params_layout.setContentsMargins(15, 15, 15, 15)
        params_layout.setSpacing(10)
       
        params_title = QLabel("⟨ AI PARAMETERS ⟩")
        params_title.setFont(QFont("Consolas", 10, QFont.Bold))
        params_title.setStyleSheet(f"color: {Neon.YELLOW};")
        params_title.setAlignment(Qt.AlignCenter)
        params_layout.addWidget(params_title)
       
        # Hold time
        hold_row = QHBoxLayout()
        hold_lbl = QLabel("Hold Time:")
        hold_lbl.setFont(QFont("Consolas", 10))
        hold_lbl.setStyleSheet(f"color: {Neon.TEXT};")
        hold_row.addWidget(hold_lbl)
        hold_row.addStretch()
        self.hold_time_label = QLabel("2.5s")
        self.hold_time_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.hold_time_label.setStyleSheet(f"color: {Neon.CYAN};")
        hold_row.addWidget(self.hold_time_label)
        params_layout.addLayout(hold_row)
       
        # Time limit
        limit_row = QHBoxLayout()
        limit_lbl = QLabel("Time Limit:")
        limit_lbl.setFont(QFont("Consolas", 10))
        limit_lbl.setStyleSheet(f"color: {Neon.TEXT};")
        limit_row.addWidget(limit_lbl)
        limit_row.addStretch()
        self.time_limit_label = QLabel("4.0s")
        self.time_limit_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.time_limit_label.setStyleSheet(f"color: {Neon.MAGENTA};")
        limit_row.addWidget(self.time_limit_label)
        params_layout.addLayout(limit_row)
       
        # Success rate
        rate_row = QHBoxLayout()
        rate_lbl = QLabel("Success Rate:")
        rate_lbl.setFont(QFont("Consolas", 10))
        rate_lbl.setStyleSheet(f"color: {Neon.TEXT};")
        rate_row.addWidget(rate_lbl)
        rate_row.addStretch()
        self.success_rate_label = QLabel("--")
        self.success_rate_label.setFont(QFont("Consolas", 11, QFont.Bold))
        self.success_rate_label.setStyleSheet(f"color: {Neon.GREEN};")
        rate_row.addWidget(self.success_rate_label)
        params_layout.addLayout(rate_row)
       
        params_frame.setStyleSheet(f"""
            #paramsFrame {{
                background: rgba(240, 255, 0, 0.05);
                border: 1px solid rgba(240, 255, 0, 0.3);
                border-radius: 10px;
            }}
        """)
       
        layout.addWidget(params_frame)
       
        panel.setStyleSheet(f"""
            #diffPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.ORANGE};
                border-radius: 20px;
            }}
        """)
       
        return panel
   
    def build_training_panel(self):
        panel = QFrame()
        panel.setObjectName("trainPanel")
       
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
       
        # Title
        title = QLabel("◈ CURRENT GESTURE")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.YELLOW};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
       
        # Gesture display
        self.gesture_display = QFrame()
        self.gesture_display.setFixedSize(250, 200)
        self.gesture_display.setObjectName("gestureDisplay")
       
        gesture_layout = QVBoxLayout(self.gesture_display)
        gesture_layout.setAlignment(Qt.AlignCenter)
        gesture_layout.setSpacing(10)
       
        self.gesture_emoji = QLabel("❓")
        self.gesture_emoji.setFont(QFont("Segoe UI Emoji", 72))
        self.gesture_emoji.setAlignment(Qt.AlignCenter)
        gesture_layout.addWidget(self.gesture_emoji)
       
        self.gesture_name = QLabel("READY?")
        self.gesture_name.setFont(QFont("Consolas", 20, QFont.Bold))
        self.gesture_name.setAlignment(Qt.AlignCenter)
        self.gesture_name.setStyleSheet(f"color: {Neon.CYAN};")
        gesture_layout.addWidget(self.gesture_name)
       
        layout.addWidget(self.gesture_display, alignment=Qt.AlignCenter)
       
        # Hold progress
        hold_box = QVBoxLayout()
        hold_box.setSpacing(8)
       
        hold_header = QHBoxLayout()
        hold_lbl = QLabel("⏱ HOLD PROGRESS")
        hold_lbl.setFont(QFont("Consolas", 11, QFont.Bold))
        hold_lbl.setStyleSheet(f"color: {Neon.MAGENTA};")
        hold_header.addWidget(hold_lbl)
        hold_header.addStretch()
        self.hold_pct = QLabel("0%")
        self.hold_pct.setFont(QFont("Consolas", 11, QFont.Bold))
        self.hold_pct.setStyleSheet(f"color: {Neon.MAGENTA};")
        hold_header.addWidget(self.hold_pct)
        hold_box.addLayout(hold_header)
       
        self.hold_bar = QProgressBar()
        self.hold_bar.setRange(0, 100)
        self.hold_bar.setValue(0)
        self.hold_bar.setFixedHeight(25)
        self.hold_bar.setTextVisible(False)
        self.hold_bar.setObjectName("holdBar")
        hold_box.addWidget(self.hold_bar)
       
        layout.addLayout(hold_box)
       
        # Status message
        self.status_message = QLabel("Press START to begin AI training")
        self.status_message.setFont(QFont("Consolas", 12, QFont.Bold))
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setStyleSheet(f"""
            color: {Neon.CYAN};
            background: rgba(0, 245, 255, 0.1);
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
        """)
        self.status_message.setWordWrap(True)
        self.status_message.setMinimumHeight(60)
        layout.addWidget(self.status_message)
       
        layout.addStretch()
       
        # Start button
        self.start_btn = QPushButton("▶  START AI TRAINING")
        self.start_btn.setFixedSize(250, 60)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFont(QFont("Consolas", 14, QFont.Bold))
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.toggle_training)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
       
        panel.setStyleSheet(f"""
            #trainPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.YELLOW};
                border-radius: 20px;
            }}
            #gestureDisplay {{
                background: rgba(0, 245, 255, 0.08);
                border: 2px solid {Neon.CYAN};
                border-radius: 20px;
            }}
            #holdBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {Neon.MAGENTA};
                border-radius: 12px;
            }}
            #holdBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.MAGENTA},
                    stop:1 {Neon.CYAN}
                );
                border-radius: 11px;
            }}
        """)
       
        return panel
   
    # ═══════════════════════════════════════════════════════════════════════════
    # GRAPH ROW
    # ═══════════════════════════════════════════════════════════════════════════
   
    def build_graph_row(self):
        container = QFrame()
        container.setMinimumHeight(160)
        container.setFixedHeight(200)
       
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
       
        # Performance graph - takes more space
        self.performance_graph = PerformanceGraphWidget()
        self.performance_graph.setMinimumWidth(350)
        layout.addWidget(self.performance_graph, 3)
       
        # Session stats panel - RESPONSIVE
        stats_panel = QFrame()
        stats_panel.setMinimumWidth(250)
        stats_panel.setMaximumWidth(320)
        stats_panel.setObjectName("sessionStats")
       
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(20, 15, 20, 15)
        stats_layout.setSpacing(12)
       
        stats_title = QLabel("◈ SESSION STATS")
        stats_title.setFont(QFont("Consolas", 12, QFont.Bold))
        stats_title.setStyleSheet(f"color: {Neon.GREEN};")
        stats_title.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(stats_title)
       
        # Stats rows
        stats_data = [
            ("Total Attempts", "0", "total_attempts"),
            ("Successful", "0", "successful"),
            ("Best Streak", "0", "best_streak"),
            ("Highest Level", "1", "highest_level"),
        ]
       
        self.session_stats = {}
       
        for name, value, key in stats_data:
            row = QHBoxLayout()
           
            lbl = QLabel(name)
            lbl.setFont(QFont("Consolas", 10))
            lbl.setStyleSheet(f"color: {Neon.TEXT};")
            row.addWidget(lbl)
           
            row.addStretch()
           
            val = QLabel(value)
            val.setFont(QFont("Consolas", 12, QFont.Bold))
            val.setStyleSheet(f"color: {Neon.CYAN};")
            row.addWidget(val)
           
            self.session_stats[key] = val
            stats_layout.addLayout(row)
       
        stats_layout.addStretch()
       
        stats_panel.setStyleSheet(f"""
            #sessionStats {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.GREEN};
                border-radius: 15px;
            }}
        """)
       
        layout.addWidget(stats_panel, 1)
       
        return container
   
    # ═══════════════════════════════════════════════════════════════════════════
    # AI INFO ROW
    # ═══════════════════════════════════════════════════════════════════════════
   
    def build_ai_info_row(self):
        container = QFrame()
        container.setMinimumHeight(80)   # ✅ Min height
        container.setMaximumHeight(110)  # ✅ Max height
        container.setObjectName("aiInfoRow")
   
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)  # ✅ Reduced padding
        layout.setSpacing(20)
       
        # AI behavior explanation
        info_box = QVBoxLayout()
        info_box.setSpacing(5)
       
        info_title = QLabel("🤖 AI BEHAVIOR")
        info_title.setFont(QFont("Consolas", 11, QFont.Bold))
        info_title.setStyleSheet(f"color: {Neon.ORANGE};")
        info_box.addWidget(info_title)
       
        info_text = QLabel(
            "• Success rate ≥80% → AI increases difficulty\n"
            "• Success rate ≤40% → AI decreases difficulty\n"
            "• Hold time and time limit adjust automatically"
        )
        info_text.setFont(QFont("Consolas", 10))
        info_text.setStyleSheet(f"color: {Neon.TEXT};")
        info_box.addWidget(info_text)
       
        layout.addLayout(info_box, 1)
       
        # Current AI decision
        decision_box = QVBoxLayout()
        decision_box.setSpacing(5)
       
        decision_title = QLabel("⚡ AI DECISION")
        decision_title.setFont(QFont("Consolas", 11, QFont.Bold))
        decision_title.setStyleSheet(f"color: {Neon.CYAN};")
        decision_box.addWidget(decision_title)
       
        self.ai_decision = QLabel("Waiting for training data...")
        self.ai_decision.setFont(QFont("Consolas", 10))
        self.ai_decision.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        self.ai_decision.setWordWrap(True)
        decision_box.addWidget(self.ai_decision)
       
        layout.addLayout(decision_box, 1)
       
        # Tips
        tips_box = QVBoxLayout()
        tips_box.setSpacing(5)
       
        tips_title = QLabel("💡 TIPS")
        tips_title.setFont(QFont("Consolas", 11, QFont.Bold))
        tips_title.setStyleSheet(f"color: {Neon.YELLOW};")
        tips_box.addWidget(tips_title)
       
        tips_text = QLabel(
            "• Keep practicing to level up\n"
            "• Don't worry if level drops - it's learning!\n"
            "• Aim for consistent performance"
        )
        tips_text.setFont(QFont("Consolas", 10))
        tips_text.setStyleSheet(f"color: {Neon.TEXT};")
        tips_box.addWidget(tips_text)
       
        layout.addLayout(tips_box, 1)
       
        container.setStyleSheet(f"""
            #aiInfoRow {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(255, 107, 0, 0.3);
                border-radius: 15px;
            }}
        """)
       
        return container
   
    # ═══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════
   
    def build_footer(self):
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setObjectName("footer")
       
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 0, 30, 0)
       
        self.sys_status = QLabel("◉ AI READY")
        self.sys_status.setFont(QFont("Consolas", 11, QFont.Bold))
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(self.sys_status)
       
        layout.addStretch()
       
        self.ai_hint = QLabel("AI will adapt to your performance")
        self.ai_hint.setFont(QFont("Consolas", 10))
        self.ai_hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.ai_hint)
       
        layout.addStretch()
       
        version = QLabel("ADAPTIVE TRAINER v1.0")
        version.setFont(QFont("Consolas", 10))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
       
        return footer
   
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎮 TRAINING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════
   
    def toggle_training(self):
        if not self.is_training:
            self.start_training()
        else:
            self.stop_training()
   
    def start_training(self):
        """✅ FIXED: Start AI training with tracker"""
        print("\n" + "🤖"*40)
        print("🤖 STARTING ADAPTIVE AI TRAINING")
        print("🤖"*40)
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: STOP desktop camera
        # ═══════════════════════════════════════════════════════════════
        print("  📡 Step 1: Stopping desktop camera...")
   
        try:
            import hand_tracker
            if hasattr(hand_tracker, 'set_camera_state'):
                hand_tracker.set_camera_state(False)
                hand_tracker.set_gesture_state(False)
                print("  ✅ Desktop camera stopped")
        except Exception as e:
            print(f"  ⚠️ Could not stop desktop: {e}")
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: START training tracker
        # ═══════════════════════════════════════════════════════════════
        print("  📸 Step 2: Starting training tracker...")
   
        try:
            from training_tracker import TrainingGestureTracker
            import config
       
            # Get camera index
            camera_idx = getattr(config, 'camera_index', 0)
            print(f"  📷 Using camera index: {camera_idx}")
       
            # Create tracker if not exists
            if self.tracker is None:
                self.tracker = TrainingGestureTracker(camera_index=camera_idx)
       
            # Start tracker
            if not self.tracker.start():
                print("  ❌ Failed to start tracker!")
   
                # Re-enable desktop on error
                try:
                    hand_tracker.set_camera_state(True)
                    hand_tracker.set_gesture_state(True)
                except:
                    pass
   
                self.ai_hint.setText("❌ CAMERA ERROR")
                self.ai_hint.setStyleSheet(f"color: {Neon.RED};")
                return

            # ✅ CRITICAL FIX: Wait for camera to initialize
            import time
            time.sleep(0.3)  # 300ms delay for camera hardware
            print("  ✅ Training tracker started!")
       
        except Exception as e:
            print(f"  ❌ Tracker error: {e}")
            import traceback
            traceback.print_exc()
       
            try:
                hand_tracker.set_camera_state(True)
                hand_tracker.set_gesture_state(True)
            except:
                pass
       
            self.ai_hint.setText("❌ TRACKER ERROR")
            return
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Start AI training session
        # ═══════════════════════════════════════════════════════════════
        print("  🤖 Step 3: Starting AI training session...")
   
        self.is_training = True
        self.session_start_time = time.time()
   
        # Update UI
        self.start_btn.setText("■  STOP TRAINING")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 0, 85, 0.15);
                color: {Neon.RED};
                border: 2px solid {Neon.RED};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(255, 0, 85, 0.3);
            }}
        """)
   
        self.cam_status.setText("● LIVE")
        self.cam_status.setStyleSheet(f"color: {Neon.GREEN};")
   
        self.sys_status.setText("◉ AI TRAINING ACTIVE")
        self.sys_status.setStyleSheet(f"color: {Neon.YELLOW};")
   
        # Start timers
        self.camera_timer.start(33)
        self.session_timer.start(1000)
   
        # Start first gesture
        self.next_gesture()
   
        print("✅ AI Training ACTIVE!")
        print("  📸 Training camera: LIVE")
        print("  🖥️ Desktop camera: STOPPED")
        print("  🤖 AI Engine: Level 1")
        print("🤖"*40 + "\n")
   
    def stop_training(self):
        """✅ FIXED: Stop training and restore desktop camera"""
        print("\n" + "⏹️"*40)
        print("⏹️ STOPPING AI TRAINING")
        print("⏹️"*40)
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: STOP training tracker
        # ═══════════════════════════════════════════════════════════════
        print("  📷 Step 1: Stopping training tracker...")
   
        if self.tracker is not None:
            try:
                self.tracker.stop()
                print("  ✅ Training tracker stopped")
       
                # ✅ CRITICAL FIX: Wait for camera to release
                import time
                time.sleep(0.3)  # 300ms delay
                print("  ⏱️ Camera release delay applied")
       
            except Exception as e:
                print(f"  ⚠️ Tracker stop error: {e}")
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: RESTART desktop camera
        # ═══════════════════════════════════════════════════════════════
        print("  📡 Step 2: Restarting desktop camera...")
   
        try:
            import hand_tracker
            if hasattr(hand_tracker, 'set_camera_state'):
                hand_tracker.set_camera_state(True)
                hand_tracker.set_gesture_state(True)
                print("  ✅ Desktop camera restarted")
        except Exception as e:
            print(f"  ⚠️ Could not restart desktop: {e}")
   
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Reset training state
        # ═══════════════════════════════════════════════════════════════
        print("  🎨 Step 3: Resetting UI...")
   
        self.is_training = False
        self.is_waiting_for_gesture = False
   
        # Stop all timers
        self.camera_timer.stop()
        self.gesture_check_timer.stop()
        self.hold_timer.stop()
        self.timeout_timer.stop()
        self.next_gesture_timer.stop()
        self.session_timer.stop()
   
        # Update UI
        self.start_btn.setText("▶  START AI TRAINING")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 107, 0, 0.15);
                color: {Neon.ORANGE};
                border: 2px solid {Neon.ORANGE};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(255, 107, 0, 0.3);
            }}
        """)
   
        self.cam_status.setText("● OFFLINE")
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
   
        self.sys_status.setText("◉ AI READY")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
   
        self.gesture_emoji.setText("🏁")
        self.gesture_name.setText("FINISHED")
   
        self.status_message.setText(f"Training complete! Final level: {self.ai_engine.level}")
   
        self.camera_label.setText(
            f"⟨ SESSION ENDED ⟩\n\n"
            f"Level: {self.ai_engine.level}\n"
            f"Accuracy: {self.get_accuracy():.0f}%"
        )
   
        print(f"✅ Training stopped!")
        print(f"  📊 Final Level: {self.ai_engine.level}")
        print(f"  📈 Accuracy: {self.get_accuracy():.0f}%")
        print("  📸 Training camera: STOPPED")
        print("  🖥️ Desktop camera: LIVE")
        print("⏹️"*40 + "\n")
   
    def next_gesture(self):
        """Get next gesture from AI"""
        if not self.is_training:
            return
       
        # Get gesture from AI engine
        gesture = self.ai_engine.get_next_gesture(self.gestures)
        self.current_gesture = gesture
        self.current_gesture_emoji = gesture[0]
       
        # Update display
        self.gesture_emoji.setText(gesture[0])
        self.gesture_name.setText(gesture[1])
        self.gesture_name.setStyleSheet(f"color: {gesture[2]};")
       
        # Update gesture display style
        r, g, b = self.hex_rgb(gesture[2])
        self.gesture_display.setStyleSheet(f"""
            #gestureDisplay {{
                background: rgba({r}, {g}, {b}, 0.15);
                border: 3px solid {gesture[2]};
                border-radius: 20px;
            }}
        """)
       
        self.status_message.setText(f"Show: {gesture[0]} {gesture[1]}")
        self.status_message.setStyleSheet(f"""
            color: {gesture[2]};
            background: rgba({r}, {g}, {b}, 0.1);
            border: 1px solid {gesture[2]};
            border-radius: 10px;
            padding: 15px;
        """)
       
        # Reset hold progress
        self.hold_bar.setValue(0)
        self.hold_pct.setText("0%")
        self.gesture_hold_start = None
       
        # Start gesture detection
        self.gesture_start_time = time.time()
        self.is_waiting_for_gesture = True
        self.gesture_check_timer.start(50)
       
        # Start timeout timer
        self.timeout_timer.start(int(self.ai_engine.get_time_limit() * 1000))
       
        print(f"🤖 AI: Show {gesture[1]} (Level {self.ai_engine.level})")
   
    def check_gesture(self):
        """✅ FIXED: Check gesture using tracker"""
        if not self.is_waiting_for_gesture:
            return
   
        # Get current finger states from tracker
        current_fingers = [0, 0, 0, 0, 0]
        hand_detected = False
   
        if self.tracker:
            hand_detected = self.tracker.hand_detected
            if hasattr(self.tracker, 'finger_states'):
                current_fingers = list(self.tracker.finger_states)[:5]
       
        if not hand_detected:
            # No hand - reset hold
            self.gesture_hold_start = None
            self.hold_bar.setValue(0)
            self.hold_pct.setText("0%")
            self.detection_label.setText("👋 Show your hand")
            self.detection_label.setStyleSheet(f"color: {Neon.ORANGE};")
            return
       
        expected = self.current_gesture[3]
       
        # Check if gesture matches
        if current_fingers == expected:
            # Correct gesture - track hold time
            if self.gesture_hold_start is None:
                self.gesture_hold_start = time.time()
           
            elapsed = time.time() - self.gesture_hold_start
            required_hold = self.ai_engine.get_hold_time()
            progress = min(1.0, elapsed / required_hold)
           
            # Update hold bar
            self.hold_bar.setValue(int(progress * 100))
            self.hold_pct.setText(f"{int(progress * 100)}%")
           
            remaining = max(0, required_hold - elapsed)
            self.detection_label.setText(f"✓ Hold: {remaining:.1f}s")
            self.detection_label.setStyleSheet(f"color: {Neon.GREEN};")
           
            # Success!
            if progress >= 1.0:
                self.on_success()
        else:
            # Wrong gesture - reset hold
            self.gesture_hold_start = None
            self.hold_bar.setValue(0)
            self.hold_pct.setText("0%")
            self.detection_label.setText("✗ Wrong gesture")
            self.detection_label.setStyleSheet(f"color: {Neon.RED};")
   
    def on_success(self):
        """Handle successful gesture"""
        if not self.is_waiting_for_gesture:
            return
       
        self.is_waiting_for_gesture = False
        self.gesture_check_timer.stop()
        self.timeout_timer.stop()
       
        # Calculate reaction time
        reaction_time = time.time() - self.gesture_start_time
       
        # Update AI engine
        self.ai_engine.add_result(True, reaction_time)
       
        # Update stats
        self.total_attempts += 1
        self.total_success += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
       
        # Update performance graph
        self.performance_graph.add_result(True)
       
        # Update UI
        self.gesture_emoji.setText("✅")
        self.gesture_name.setText("SUCCESS!")
        self.gesture_name.setStyleSheet(f"color: {Neon.GREEN};")
       
        self.gesture_display.setStyleSheet(f"""
            #gestureDisplay {{
                background: rgba(0, 255, 159, 0.2);
                border: 3px solid {Neon.GREEN};
                border-radius: 20px;
            }}
        """)
       
        self.status_message.setText(f"✓ Correct! +{self.current_streak} streak")
        self.status_message.setStyleSheet(f"""
            color: {Neon.GREEN};
            background: rgba(0, 255, 159, 0.1);
            border: 1px solid {Neon.GREEN};
            border-radius: 10px;
            padding: 15px;
        """)
       
        self.detection_label.setText(f"⚡ {reaction_time:.2f}s")
        self.detection_label.setStyleSheet(f"color: {Neon.GREEN};")
       
        self.update_all_stats()
       
        # Next gesture after delay
        self.next_gesture_timer.start(1200)
       
        print(f"✓ Success! Reaction: {reaction_time:.2f}s, Streak: {self.current_streak}")
   
    def on_timeout(self):
        """Handle timeout"""
        if not self.is_waiting_for_gesture:
            return
       
        self.is_waiting_for_gesture = False
        self.gesture_check_timer.stop()
       
        # Update AI engine
        self.ai_engine.add_result(False)
       
        # Update stats
        self.total_attempts += 1
        self.current_streak = 0
       
        # Update performance graph
        self.performance_graph.add_result(False)
       
        # Update UI
        self.gesture_emoji.setText("⏰")
        self.gesture_name.setText("TOO SLOW!")
        self.gesture_name.setStyleSheet(f"color: {Neon.ORANGE};")
       
        self.gesture_display.setStyleSheet(f"""
            #gestureDisplay {{
                background: rgba(255, 107, 0, 0.2);
                border: 3px solid {Neon.ORANGE};
                border-radius: 20px;
            }}
        """)
       
        self.status_message.setText("⏰ Time's up! Try to be faster.")
        self.status_message.setStyleSheet(f"""
            color: {Neon.ORANGE};
            background: rgba(255, 107, 0, 0.1);
            border: 1px solid {Neon.ORANGE};
            border-radius: 10px;
            padding: 15px;
        """)
       
        self.hold_bar.setValue(0)
        self.hold_pct.setText("0%")
       
        self.update_all_stats()
       
        # Next gesture after delay
        self.next_gesture_timer.start(1500)
       
        print("⏰ Timeout!")
   
    # ═══════════════════════════════════════════════════════════════════════════
    # 📊 STATS & UPDATES
    # ═══════════════════════════════════════════════════════════════════════════
   
    def update_all_stats(self):
        """Update all stat displays"""
        # Update difficulty meter
        self.difficulty_meter.set_level(self.ai_engine.level)
       
        # Update header stats
        self.stat_level.findChild(QLabel, "val").setText(str(self.ai_engine.level))
        self.stat_streak.findChild(QLabel, "val").setText(str(self.current_streak))
        self.stat_accuracy.findChild(QLabel, "val").setText(f"{self.get_accuracy():.0f}%")
       
        # Update AI parameters display
        self.hold_time_label.setText(f"{self.ai_engine.get_hold_time():.1f}s")
        self.time_limit_label.setText(f"{self.ai_engine.get_time_limit():.1f}s")
       
        success_rate = self.ai_engine.get_success_rate() * 100
        self.success_rate_label.setText(f"{success_rate:.0f}%")
       
        if success_rate >= 80:
            self.success_rate_label.setStyleSheet(f"color: {Neon.GREEN};")
        elif success_rate >= 40:
            self.success_rate_label.setStyleSheet(f"color: {Neon.YELLOW};")
        else:
            self.success_rate_label.setStyleSheet(f"color: {Neon.RED};")
       
        # Update session stats
        self.session_stats["total_attempts"].setText(str(self.total_attempts))
        self.session_stats["successful"].setText(str(self.total_success))
        self.session_stats["best_streak"].setText(str(self.best_streak))
        self.session_stats["highest_level"].setText(str(self.ai_engine.level))
       
        # Update AI decision text
        success_rate = self.ai_engine.get_success_rate()
        if success_rate >= 0.8:
            self.ai_decision.setText("📈 Performance excellent! Increasing difficulty...")
            self.ai_decision.setStyleSheet(f"color: {Neon.GREEN};")
        elif success_rate <= 0.4:
            self.ai_decision.setText("📉 Struggling detected. Reducing difficulty...")
            self.ai_decision.setStyleSheet(f"color: {Neon.ORANGE};")
        else:
            self.ai_decision.setText("📊 Maintaining current difficulty level.")
            self.ai_decision.setStyleSheet(f"color: {Neon.CYAN};")
   
    def get_accuracy(self):
        """Get overall accuracy"""
        if self.total_attempts == 0:
            return 0
        return (self.total_success / self.total_attempts) * 100
   
    def update_session_time(self):
        """Update session time display"""
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.stat_time.findChild(QLabel, "val").setText(f"{minutes}:{seconds:02d}")
   
    def update_hold_progress(self):
        """Update hold progress (called by timer)"""
        pass  # Handled in check_gesture
   
    def update_camera_feed(self):
        """✅ FIXED: Use shared tracker"""
        if self.tracker is None or not self.tracker.is_running:
            self.camera_label.setText("⟨ WAITING FOR TRACKER ⟩")
            return
   
        frame, gesture, hand_detected, dwell = self.tracker.get_frame()
   
        if frame is not None:
            self.frame_count += 1
       
            resized = cv2.resize(frame, (410, 280))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
       
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
       
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.camera_label.setText("⟨ NO CAMERA FRAME ⟩")
   
    def calculate_fps(self):
        self.current_fps = self.frame_count
        self.frame_count = 0
        self.stat_fps.findChild(QLabel, "val").setText(str(self.current_fps))
   
    def reset_training(self):
        """Reset all training data"""
        self.stop_training()
       
        self.ai_engine.reset()
        self.performance_graph.clear()
       
        self.total_attempts = 0
        self.total_success = 0
        self.current_streak = 0
        self.best_streak = 0
       
        self.difficulty_meter.set_level(1)
       
        self.gesture_emoji.setText("❓")
        self.gesture_name.setText("READY?")
        self.gesture_name.setStyleSheet(f"color: {Neon.CYAN};")
       
        self.status_message.setText("Press START to begin AI training")
        self.status_message.setStyleSheet(f"""
            color: {Neon.CYAN};
            background: rgba(0, 245, 255, 0.1);
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
        """)
       
        self.hold_bar.setValue(0)
        self.hold_pct.setText("0%")
       
        self.update_all_stats()
       
        print("🔄 Training Reset")
   
    def close_mode(self):
        """Close and return to hub"""
        print("🚪 Closing Adaptive Trainer...")
   
        # Stop training if active
        if self.is_training:
            self.stop_training()
   
        # ✅ Force stop tracker if still running
        if self.tracker is not None:
            try:
                self.tracker.stop()
                self.tracker = None
                print("  🔒 Force-stopped tracker")
            except:
                pass
   
        # Wait before emitting signal
        import time
        time.sleep(0.2)
   
        self.mode_closed.emit()
   
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
   
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎨 THEME
    # ═══════════════════════════════════════════════════════════════════════════
   
    def apply_theme(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000510,
                    stop:0.5 #050a18,
                    stop:1 #0a1225
                );
                color: {Neon.TEXT};
                font-family: 'Consolas', monospace;
            }}
           
            #header {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 107, 0, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-bottom: 3px solid {Neon.ORANGE};
            }}
           
            #backBtn {{
                background: rgba(255, 107, 0, 0.15);
                color: {Neon.ORANGE};
                border: 2px solid {Neon.ORANGE};
                border-radius: 12px;
            }}
            #backBtn:hover {{
                background: rgba(255, 107, 0, 0.35);
            }}
           
            #resetBtn {{
                background: rgba(255, 0, 85, 0.15);
                color: {Neon.RED};
                border: 2px solid {Neon.RED};
                border-radius: 12px;
            }}
            #resetBtn:hover {{
                background: rgba(255, 0, 85, 0.35);
            }}
           
            #camPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.ORANGE};
                border-radius: 20px;
            }}
           
            #camDisplay {{
                background: #000000;
                border: 2px solid rgba(255, 107, 0, 0.4);
                border-radius: 12px;
                color: {Neon.TEXT_DIM};
                font-size: 14px;
            }}
           
            #startBtn {{
                background: rgba(255, 107, 0, 0.15);
                color: {Neon.ORANGE};
                border: 2px solid {Neon.ORANGE};
                border-radius: 15px;
            }}
            #startBtn:hover {{
                background: rgba(255, 107, 0, 0.3);
            }}
           
            #footer {{
                background: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(255, 107, 0, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-top: 3px solid {Neon.ORANGE};
            }}
        """)


    def set_tracker(self, tracker):
        """✅ Set shared tracker from parent"""
        self.tracker = tracker
        print(f"✅ {self.__class__.__name__} received shared tracker")
   
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
   
    # adaptive_trainer.py - Line 1193 ke baad add karo

    # ═══════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP - ADD THIS SECTION
    # ═══════════════════════════════════════════════════════════════════════════
   
    def cleanup(self):
        """✅ FIXED: Clean up resources with proper camera shutdown"""
        print("🧹 Cleaning up Adaptive Trainer...")
   
        # Stop training if active
        if self.is_training:
            self.stop_training()
   
        # Stop all timers
        timer_list = [
            'camera_timer',
            'gesture_check_timer',
            'hold_timer',
            'timeout_timer',
            'next_gesture_timer',
            'fps_timer',
            'session_timer'
        ]
   
        for timer_name in timer_list:
            if hasattr(self, timer_name):
                timer = getattr(self, timer_name)
                if timer and timer.isActive():
                    timer.stop()
   
        # ✅ FORCE STOP TRACKER (Camera release)
        if self.tracker is not None:
            try:
                print("  🔒 Force stopping tracker...")
                self.tracker.stop()
           
                # Wait for camera hardware to release
                import time
                time.sleep(0.3)
                print("  ✅ Tracker force-stopped")
            except Exception as e:
                print(f"  ⚠️ Tracker cleanup error: {e}")
            finally:
                self.tracker = None
   
        print("✅ Adaptive Trainer cleaned up")
   
    def closeEvent(self, event):
        """✅ UPDATED: Handle close event with cleanup"""
        print("❌ Adaptive Trainer closing...")
        self.cleanup()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN - For Testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
   
    window = AdaptiveTrainerMode()
    window.showMaximized()
   
    sys.exit(app.exec())
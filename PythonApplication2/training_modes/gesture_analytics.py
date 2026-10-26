"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       GESTURE ANALYTICS MODE                                 ║
║                   📊 Performance Analysis System 📊                           ║
║                         Version 1.1 - FIXED                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

✅ FIXED: Attempt counting now uses proper state machine
- Attempts only count when hand appears/disappears
- Success only counts when gesture held correctly for 1 second
- No more continuous incrementing!
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPen, QBrush, 
    QColor, QLinearGradient, QRadialGradient, QPainterPath,
    QPolygonF
)
import cv2
import time
import math
import sys
import os

# Add parent directory to path for imports
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
# 📊 RADAR CHART WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class RadarChartWidget(QWidget):
    """
    Radar/Spider chart showing performance metrics:
    - Accuracy
    - Speed  
    - Stability
    - Precision
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ✅ INCREASED SIZE - labels ke liye space
        self.setMinimumSize(400, 400)
        self.setMaximumSize(450, 450)
        
        # Metrics (0.0 to 1.0)
        self.metrics = {
            "Accuracy": 0.0,
            "Speed": 0.0,
            "Stability": 0.0,
            "Precision": 0.0
        }
        
        # Animation
        self.target_metrics = self.metrics.copy()
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_metrics)
        self.anim_timer.start(30)
    
    def set_metrics(self, accuracy=0.0, speed=0.0, stability=0.0, precision=0.0):
        """Set target metrics for animation"""
        self.target_metrics = {
            "Accuracy": min(1.0, max(0.0, accuracy)),
            "Speed": min(1.0, max(0.0, speed)),
            "Stability": min(1.0, max(0.0, stability)),
            "Precision": min(1.0, max(0.0, precision))
        }
    
    def animate_metrics(self):
        """Smoothly animate to target metrics"""
        changed = False
        for key in self.metrics:
            diff = self.target_metrics[key] - self.metrics[key]
            if abs(diff) > 0.01:
                self.metrics[key] += diff * 0.1
                changed = True
        
        if changed:
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # ✅ Center with more padding for labels
        center = QPointF(self.width() / 2, self.height() / 2)
        # ✅ Smaller radius = more space for labels around edges
        radius = min(self.width(), self.height()) / 2 - 90
        
        # Draw background circles
        self.draw_background(painter, center, radius)
        
        # Draw axes
        self.draw_axes(painter, center, radius)
        
        # Draw data polygon
        self.draw_data(painter, center, radius)
        
        # Draw labels
        self.draw_labels(painter, center, radius)
    
    def draw_background(self, painter, center, radius):
        """Draw concentric circles"""
        pen = QPen(QColor(Neon.CYAN))
        pen.setWidth(1)
        
        for i in range(1, 6):
            r = radius * (i / 5)
            alpha = 30 + (i * 10)
            pen.setColor(QColor(0, 245, 255, alpha))
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, r, r)
    
    def draw_axes(self, painter, center, radius):
        """Draw axis lines"""
        pen = QPen(QColor(0, 245, 255, 80))
        pen.setWidth(1)
        painter.setPen(pen)
        
        num_axes = 4
        for i in range(num_axes):
            angle = (2 * math.pi * i / num_axes) - math.pi / 2
            end_x = center.x() + radius * math.cos(angle)
            end_y = center.y() + radius * math.sin(angle)
            painter.drawLine(center, QPointF(end_x, end_y))
    
    def draw_data(self, painter, center, radius):
        """Draw the data polygon"""
        metrics_list = list(self.metrics.values())
        num_points = len(metrics_list)
        
        # Create polygon points
        points = []
        for i, value in enumerate(metrics_list):
            angle = (2 * math.pi * i / num_points) - math.pi / 2
            # ✅ Minimum value so polygon is always visible
            r = radius * max(0.05, value)
            x = center.x() + r * math.cos(angle)
            y = center.y() + r * math.sin(angle)
            points.append(QPointF(x, y))
        
        # Draw filled polygon
        polygon = QPolygonF(points)
        
        # Gradient fill
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0, QColor(0, 255, 159, 100))
        gradient.setColorAt(0.7, QColor(0, 245, 255, 60))
        gradient.setColorAt(1, QColor(255, 0, 255, 40))
        
        painter.setBrush(QBrush(gradient))
        
        # Border
        pen = QPen(QColor(Neon.GREEN))
        pen.setWidth(3)
        painter.setPen(pen)
        
        painter.drawPolygon(polygon)
        
        # Draw points
        for point in points:
            painter.setBrush(QBrush(QColor(Neon.CYAN)))
            painter.setPen(QPen(QColor(Neon.WHITE), 2))
            painter.drawEllipse(point, 6, 6)
    
    def draw_labels(self, painter, center, radius):
        """
        ✅ FIXED: Draw metric labels - no clipping
        """
        metrics_names = list(self.metrics.keys())
        num_labels = len(metrics_names)
    
        for i, name in enumerate(metrics_names):
            angle = (2 * math.pi * i / num_labels) - math.pi / 2
        
            # Position outside chart
            label_radius = radius + 30
            x = center.x() + label_radius * math.cos(angle)
            y = center.y() + label_radius * math.sin(angle)
        
            # Get value and color
            value = self.metrics[name] * 100
            if value >= 80:
                color = QColor(Neon.GREEN)
            elif value >= 50:
                color = QColor(Neon.YELLOW)
            else:
                color = QColor(Neon.ORANGE)
        
            value_text = f"{value:.0f}%"
        
            if i == 0:  # TOP - Accuracy
                name_rect = QRectF(x - 60, y - 38, 120, 20)
                val_rect = QRectF(x - 60, y - 18, 120, 20)
                name_align = Qt.AlignCenter
                val_align = Qt.AlignCenter
            
            elif i == 1:  # RIGHT - Speed
                name_rect = QRectF(x + 8, y - 18, 100, 20)
                val_rect = QRectF(x + 8, y + 2, 100, 20)
                name_align = Qt.AlignLeft
                val_align = Qt.AlignLeft
            
            elif i == 2:  # BOTTOM - Stability ✅ FIXED
                name_rect = QRectF(x - 60, y + 2, 120, 20)
                val_rect = QRectF(x - 60, y + 15, 120, 20)  # ✅ y+25 → y+30
                name_align = Qt.AlignCenter
                val_align = Qt.AlignCenter
            
            else:  # LEFT - Precision (i == 3) ✅ FIXED
                name_rect = QRectF(x - 105, y - 18, 110, 20)  # ✅ -105 → -115, width 100 → 110
                val_rect = QRectF(x - 105, y + 2, 110, 20)    # ✅ same
                name_align = Qt.AlignRight
                val_align = Qt.AlignRight
        
            # Draw name
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.setPen(QColor(Neon.TEXT))
            painter.drawText(name_rect, name_align, name)
        
            # Draw value
            painter.setFont(QFont("Consolas", 12, QFont.Bold))
            painter.setPen(color)
            painter.drawText(val_rect, val_align, value_text)


# ═══════════════════════════════════════════════════════════════════════════════
# 🖐️ FINGER HEATMAP WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class FingerHeatmapWidget(QWidget):
    """
    Visual heatmap showing finger positions
    Green = Correct, Red = Incorrect
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 420)
        self.setMaximumSize(480, 480)
        
        # Finger states: [thumb, index, middle, ring, pinky]
        # 0 = down, 1 = up
        self.current_fingers = [0, 0, 0, 0, 0]
        self.expected_fingers = [0, 0, 0, 0, 0]
        
        # Finger names
        self.finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    
    def set_finger_states(self, current, expected):
        """Set current and expected finger states"""
        self.current_fingers = current[:5] if len(current) >= 5 else current + [0] * (5 - len(current))
        self.expected_fingers = expected[:5] if len(expected) >= 5 else expected + [0] * (5 - len(expected))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(5, 10, 20))
        
        # Draw hand outline
        self.draw_hand(painter)
        
        # Draw title
        self.draw_title(painter)
    
    def draw_title(self, painter):
        """Draw title"""
        font = QFont("Consolas", 12, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(Neon.CYAN))
        painter.drawText(QRectF(0, 10, self.width(), 30), Qt.AlignCenter, "◈ FINGER HEATMAP")
    
    def draw_hand(self, painter):
        """Draw hand with colored fingers"""
        center_x = self.width() / 2
        base_y = self.height() - 80
        
        # Palm
        palm_rect = QRectF(center_x - 60, base_y - 100, 120, 100)
        painter.setBrush(QBrush(QColor(30, 40, 60)))
        painter.setPen(QPen(QColor(Neon.CYAN), 2))
        painter.drawRoundedRect(palm_rect, 20, 20)
        
        # Finger positions (x offset from center, height)
        finger_positions = [
            (-70, 60, 25),   # Thumb (x, height, width)
            (-40, 100, 22),  # Index
            (-12, 110, 22),  # Middle
            (16, 100, 22),   # Ring
            (44, 80, 20),    # Pinky
        ]
        
        for i, (x_off, height, width) in enumerate(finger_positions):
            x = center_x + x_off
            y = base_y - 100 - height
            
            # Determine color based on correctness
            current = self.current_fingers[i]
            expected = self.expected_fingers[i]
            
            if current == expected:
                # Correct - Green
                color = QColor(0, 255, 159, 200)
                border_color = QColor(Neon.GREEN)
                status = "✓"
            else:
                # Incorrect - Red
                color = QColor(255, 0, 85, 200)
                border_color = QColor(Neon.RED)
                status = "✗"
            
            # Draw finger
            finger_rect = QRectF(x - width/2, y, width, height)
            
            # Gradient
            gradient = QLinearGradient(finger_rect.topLeft(), finger_rect.bottomLeft())
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(border_color, 2))
            painter.drawRoundedRect(finger_rect, 10, 10)
            
            # Finger tip indicator
            tip_y = y + 5
            painter.setBrush(QBrush(border_color))
            painter.drawEllipse(QPointF(x, tip_y), 8, 8)
            
            # Status indicator
            font = QFont("Consolas", 8, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(Neon.WHITE))
            painter.drawText(QRectF(x - 10, tip_y - 6, 20, 12), Qt.AlignCenter, status)
        
        # Draw finger labels
        font = QFont("Consolas", 8)
        painter.setFont(font)
        painter.setPen(QColor(Neon.TEXT_DIM))
        
        label_y = base_y + 10
        for i, (x_off, _, _) in enumerate(finger_positions):
            x = center_x + x_off
            painter.drawText(QRectF(x - 30, label_y, 60, 20), Qt.AlignCenter, self.finger_names[i])
        
        # Draw legend
        self.draw_legend(painter)
    
    def draw_legend(self, painter):
        """Draw legend"""
        legend_y = 50
        
        font = QFont("Consolas", 9)
        painter.setFont(font)
        
        # Correct
        painter.setBrush(QBrush(QColor(0, 255, 159)))
        painter.setPen(QPen(QColor(Neon.GREEN), 1))
        painter.drawEllipse(QPointF(30, legend_y), 8, 8)
        painter.setPen(QColor(Neon.TEXT))
        painter.drawText(QRectF(45, legend_y - 10, 80, 20), Qt.AlignLeft | Qt.AlignVCenter, "Correct")
        
        # Incorrect
        painter.setBrush(QBrush(QColor(255, 0, 85)))
        painter.setPen(QPen(QColor(Neon.RED), 1))
        painter.drawEllipse(QPointF(130, legend_y), 8, 8)
        painter.setPen(QColor(Neon.TEXT))
        painter.drawText(QRectF(145, legend_y - 10, 80, 20), Qt.AlignLeft | Qt.AlignVCenter, "Incorrect")


# ═══════════════════════════════════════════════════════════════════════════════
# 📈 GESTURE PROGRESS WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class GestureProgressWidget(QFrame):
    """
    Progress bars for each gesture showing training progress
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("gestureProgress")
        
        # Gesture progress data
        self.gesture_data = {
            "INDEX": {"practiced": 0, "success": 0, "color": Neon.CYAN},
            "PEACE": {"practiced": 0, "success": 0, "color": Neon.GREEN},
            "THREE": {"practiced": 0, "success": 0, "color": Neon.PURPLE},
            "PALM": {"practiced": 0, "success": 0, "color": Neon.ORANGE},
            "FIST": {"practiced": 0, "success": 0, "color": Neon.RED},
            "THUMB": {"practiced": 0, "success": 0, "color": Neon.YELLOW},
            "SHAKA": {"practiced": 0, "success": 0, "color": Neon.MAGENTA},
        }
        
        self.progress_bars = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("◈ GESTURE PROGRESS")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.YELLOW};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Progress bars for each gesture
        for gesture, data in self.gesture_data.items():
            row = self.create_progress_row(gesture, data["color"])
            layout.addLayout(row)
        
        layout.addStretch()
        
        # Apply styling
        self.setStyleSheet(f"""
            #gestureProgress {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.YELLOW};
                border-radius: 15px;
            }}
        """)
    
    def create_progress_row(self, gesture, color):
        """Create a progress bar row for a gesture"""
        row = QHBoxLayout()
        row.setSpacing(15)
        
        # Gesture name
        name = QLabel(gesture)
        name.setFont(QFont("Consolas", 10, QFont.Bold))
        name.setStyleSheet(f"color: {color};")
        name.setFixedWidth(70)
        row.addWidget(name)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setFixedHeight(20)
        progress.setTextVisible(False)
        
        r, g, b = self.hex_rgb(color)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba({r}, {g}, {b}, 0.5);
                border-radius: 10px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color},
                    stop:1 rgba({r}, {g}, {b}, 0.6)
                );
                border-radius: 9px;
            }}
        """)
        row.addWidget(progress, 1)
        
        # Percentage label
        pct = QLabel("0%")
        pct.setFont(QFont("Consolas", 10, QFont.Bold))
        pct.setStyleSheet(f"color: {color};")
        pct.setFixedWidth(45)
        pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(pct)
        
        # Store reference
        self.progress_bars[gesture] = {"bar": progress, "label": pct}
        
        return row
    
    def update_gesture(self, gesture, practiced, success):
        """Update progress for a gesture"""
        if gesture in self.gesture_data:
            self.gesture_data[gesture]["practiced"] = practiced
            self.gesture_data[gesture]["success"] = success
            
            accuracy = (success / practiced * 100) if practiced > 0 else 0
            
            if gesture in self.progress_bars:
                self.progress_bars[gesture]["bar"].setValue(int(accuracy))
                self.progress_bars[gesture]["label"].setText(f"{accuracy:.0f}%")
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 GESTURE ANALYTICS MODE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class GestureAnalyticsMode(QWidget):
    """
    Gesture Analytics Mode - Performance analysis with visual feedback
    
    ✅ FIXED in v1.1:
    - Attempts now count properly using state machine
    - Success only counted when gesture held for 1 second
    - No more continuous incrementing!
    """
    
    mode_closed = Signal()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎯 ATTEMPT TRACKING CONSTANTS
    # ═══════════════════════════════════════════════════════════════════════════
    HOLD_TIME_REQUIRED = 1.0  # Seconds to hold gesture for success
    COOLDOWN_TIME = 0.5       # Seconds between attempts
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
        # ✅ Tracker is None initially
        self.tracker = None
        self.tracker_active = False
        self.setWindowTitle("◈ GESTURE ANALYTICS")
        self.setMinimumSize(1400, 900)
        
        # ═══ STATE ═══
        self.is_analyzing = False
        self.current_gesture = None
        self.current_gesture_emoji = ""
        
        # ═══════════════════════════════════════════════════════════════════════
        # ✅ NEW: STATE MACHINE FOR ATTEMPT TRACKING
        # ═══════════════════════════════════════════════════════════════════════
        self.attempt_state = "WAITING"  # WAITING, DETECTING, HOLDING, COOLDOWN
        self.last_hand_detected = False
        self.gesture_start_time = None
        self.correct_hold_start = None
        self.cooldown_start = None
        self.current_accuracy = 0.0
        
        # Performance metrics for current attempt
        self.current_attempt_metrics = {
            "peak_accuracy": 0.0,
            "stability_samples": [],
            "start_time": None,
        }
        # ═══════════════════════════════════════════════════════════════════════
        
        self.session_data = {
            "total_attempts": 0,
            "total_success": 0,
            "reaction_times": [],
            "stability_scores": [],
            "start_time": None,
        }
        
        # Gesture tracking
        self.gesture_stats = {
            "INDEX": {"practiced": 0, "success": 0},
            "PEACE": {"practiced": 0, "success": 0},
            "THREE": {"practiced": 0, "success": 0},
            "PALM": {"practiced": 0, "success": 0},
            "FIST": {"practiced": 0, "success": 0},
            "THUMB": {"practiced": 0, "success": 0},
            "SHAKA": {"practiced": 0, "success": 0},
        }
        
        # Expected finger patterns
        self.gesture_patterns = {
            "INDEX": [0, 1, 0, 0, 0],
            "PEACE": [0, 1, 1, 0, 0],
            "THREE": [0, 1, 1, 1, 0],
            "PALM": [1, 1, 1, 1, 1],
            "FIST": [0, 0, 0, 0, 0],
            "THUMB": [1, 0, 0, 0, 0],
            "SHAKA": [1, 0, 0, 0, 1],
        }
        
        # Performance metrics (for radar chart)
        self.metrics = {
            "accuracy": 0.0,
            "speed": 0.0,
            "stability": 0.0,
            "precision": 0.0
        }
        
        # ═══ BUILD UI ═══
        self.setup_ui()
        self.apply_theme()
        
        # ═══ TIMERS ═══
        self.camera_timer = QTimer()
        self.camera_timer.timeout.connect(self.update_camera_feed)
        
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.analyze_performance)
        
        # ═══ FPS ═══
        self.frame_count = 0
        self.current_fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.calculate_fps)
        self.fps_timer.start(1000)
        
        # ═══ SESSION TIMER ═══
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.update_session_time)
        
        print("📊 Gesture Analytics Mode Initialized (v1.1 - FIXED)")
    
    def setup_ui(self):
        """Build UI"""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
    
        # Header
        header = self.build_header()
        main.addWidget(header)
    
        # Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setObjectName("scrollArea")
    
        content = QWidget()
        content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 50)
        content_layout.setSpacing(25)
    
        # Row 1: Camera + Heatmap + Radar
        row1 = self.build_analysis_row()
        content_layout.addWidget(row1)
    
        # Row 2: Gesture Progress
        row2 = self.build_progress_section()
        content_layout.addWidget(row2)
    
        # Row 3: Controls
        row3 = self.build_controls_section()
        content_layout.addWidget(row3)
    
        content_layout.addSpacing(60)
    
        scroll.setWidget(content)
        main.addWidget(scroll, 1)
    
        # Footer
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
        logo = QLabel("📊")
        logo.setFont(QFont("Segoe UI Emoji", 28))
        logo.setFixedWidth(50)
        layout.addWidget(logo)
        
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        
        title = QLabel("GESTURE ANALYTICS")
        title.setFont(QFont("Consolas", 20, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.GREEN};")
        title_box.addWidget(title)
        
        subtitle = QLabel("PERFORMANCE ANALYSIS SYSTEM")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
        
        layout.addLayout(title_box)
        layout.addStretch()
        
        # Stats
        self.stat_attempts = self.make_stat("ATTEMPTS", "0", Neon.CYAN)
        layout.addWidget(self.stat_attempts)
        
        self.stat_success = self.make_stat("SUCCESS", "0", Neon.GREEN)
        layout.addWidget(self.stat_success)
        
        self.stat_accuracy = self.make_stat("ACCURACY", "0%", Neon.YELLOW)
        layout.addWidget(self.stat_accuracy)
        
        self.stat_fps = self.make_stat("FPS", "0", Neon.MAGENTA)
        layout.addWidget(self.stat_fps)
        
        layout.addStretch()
        
        # Reset Button
        self.reset_btn = QPushButton("⟲  RESET")
        self.reset_btn.setFixedSize(120, 45)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self.reset_analytics)
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
        val.setFont(QFont("Consolas", 15, QFont.Bold))
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
    # ANALYSIS ROW (Camera + Heatmap + Radar)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_analysis_row(self):
        container = QFrame()
        container.setMinimumHeight(420)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Camera Panel
        cam_panel = self.build_camera_panel()
        layout.addWidget(cam_panel)
        
        # Heatmap Panel
        heatmap_panel = QFrame()
        heatmap_panel.setObjectName("heatmapPanel")
        heatmap_layout = QVBoxLayout(heatmap_panel)
        heatmap_layout.setContentsMargins(10, 10, 10, 10)
        
        self.heatmap = FingerHeatmapWidget()
        heatmap_layout.addWidget(self.heatmap, alignment=Qt.AlignCenter)
        
        heatmap_panel.setStyleSheet(f"""
            #heatmapPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.MAGENTA};
                border-radius: 20px;
            }}
        """)
        layout.addWidget(heatmap_panel)
        
        # Radar Panel
        radar_panel = QFrame()
        radar_panel.setObjectName("radarPanel")
        radar_layout = QVBoxLayout(radar_panel)
        radar_layout.setContentsMargins(10, 10, 10, 10)
        
        radar_title = QLabel("◈ PERFORMANCE RADAR")
        radar_title.setFont(QFont("Consolas", 12, QFont.Bold))
        radar_title.setStyleSheet(f"color: {Neon.CYAN};")
        radar_title.setAlignment(Qt.AlignCenter)
        radar_layout.addWidget(radar_title)
        
        self.radar_chart = RadarChartWidget()
        radar_layout.addWidget(self.radar_chart, alignment=Qt.AlignCenter)
        
        radar_panel.setStyleSheet(f"""
            #radarPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.CYAN};
                border-radius: 20px;
            }}
        """)
        layout.addWidget(radar_panel)
        
        return container
    
    def build_camera_panel(self):
        panel = QFrame()
        panel.setFixedWidth(480)
        panel.setObjectName("camPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("◉ LIVE FEED")
        cam_title.setFont(QFont("Consolas", 13, QFont.Bold))
        cam_title.setStyleSheet(f"color: {Neon.GREEN};")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        self.cam_status = QLabel("● OFFLINE")
        self.cam_status.setFont(QFont("Consolas", 10, QFont.Bold))
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
        cam_header.addWidget(self.cam_status)
        layout.addLayout(cam_header)
        
        # Camera Display
        self.camera_label = QLabel("⟨ START ANALYSIS ⟩\n\nClick button below")
        self.camera_label.setFixedSize(440, 300)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setObjectName("camDisplay")
        layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        
        # Current gesture display
        self.gesture_display = QLabel("No gesture selected")
        self.gesture_display.setFont(QFont("Consolas", 12, QFont.Bold))
        self.gesture_display.setAlignment(Qt.AlignCenter)
        self.gesture_display.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.gesture_display)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ✅ NEW: Attempt state indicator
        # ═══════════════════════════════════════════════════════════════════════
        self.state_display = QLabel("STATE: WAITING")
        self.state_display.setFont(QFont("Consolas", 10, QFont.Bold))
        self.state_display.setAlignment(Qt.AlignCenter)
        self.state_display.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.state_display)
        
        # Hold progress bar
        self.hold_progress = QProgressBar()
        self.hold_progress.setRange(0, 100)
        self.hold_progress.setValue(0)
        self.hold_progress.setFixedHeight(15)
        self.hold_progress.setTextVisible(False)
        self.hold_progress.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid {Neon.CYAN};
                border-radius: 7px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.GREEN},
                    stop:1 {Neon.CYAN}
                );
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.hold_progress)
        
        return panel
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROGRESS SECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_progress_section(self):
        container = QFrame()
        container.setMinimumHeight(340)
    
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
    
        # Gesture Progress Widget
        self.gesture_progress = GestureProgressWidget()
        self.gesture_progress.setMinimumHeight(320)
        layout.addWidget(self.gesture_progress, 1)
    
        # Quick Stats Panel
        stats_panel = self.build_quick_stats()
        stats_panel.setMinimumHeight(320)
        layout.addWidget(stats_panel)
    
        return container
    
    def build_quick_stats(self):
        panel = QFrame()
        panel.setFixedWidth(350)
        panel.setObjectName("quickStats")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("◈ QUICK STATS")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.ORANGE};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Stats rows
        stats = [
            ("Best Gesture", "---", Neon.GREEN),
            ("Needs Practice", "---", Neon.RED),
            ("Avg. Reaction", "---", Neon.CYAN),
            ("Session Time", "0:00", Neon.MAGENTA),
            ("Total Score", "0", Neon.YELLOW),
        ]
        
        self.quick_stat_labels = {}
        
        for name, value, color in stats:
            row = QHBoxLayout()
            
            lbl = QLabel(name)
            lbl.setFont(QFont("Consolas", 11))
            lbl.setStyleSheet(f"color: {Neon.TEXT};")
            row.addWidget(lbl)
            
            row.addStretch()
            
            val = QLabel(value)
            val.setFont(QFont("Consolas", 12, QFont.Bold))
            val.setStyleSheet(f"color: {color};")
            row.addWidget(val)
            
            self.quick_stat_labels[name] = val
            
            layout.addLayout(row)
        
        layout.addStretch()
        
        panel.setStyleSheet(f"""
            #quickStats {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.ORANGE};
                border-radius: 15px;
            }}
        """)
        
        return panel
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONTROLS SECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_controls_section(self):
        section = QFrame()
        section.setFixedHeight(120)
        section.setObjectName("controlsSection")
        
        layout = QHBoxLayout(section)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(30)
        
        # Gesture selector
        gesture_box = QVBoxLayout()
        gesture_box.setSpacing(10)
        
        gesture_lbl = QLabel("⟨ SELECT GESTURE ⟩")
        gesture_lbl.setFont(QFont("Consolas", 11, QFont.Bold))
        gesture_lbl.setStyleSheet(f"color: {Neon.CYAN};")
        gesture_box.addWidget(gesture_lbl)
        
        # Gesture buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        gestures = [
            ("☝️", "INDEX"), ("✌️", "PEACE"), ("🤟", "THREE"), ("✋", "PALM"),
            ("✊", "FIST"), ("👍", "THUMB"), ("🤙", "SHAKA")
        ]
        
        self.gesture_buttons = {}
        for emoji, name in gestures:
            btn = QPushButton(emoji)
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Segoe UI Emoji", 20))
            btn.setCheckable(True)
            btn.setObjectName("gestureBtn")
            btn.clicked.connect(lambda checked, n=name, e=emoji: self.select_gesture(n, e))
            btn_row.addWidget(btn)
            self.gesture_buttons[name] = btn
        
        gesture_box.addLayout(btn_row)
        layout.addLayout(gesture_box)
        
        layout.addStretch()
        
        # Start/Stop button
        self.start_btn = QPushButton("▶  START ANALYSIS")
        self.start_btn.setFixedSize(200, 60)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFont(QFont("Consolas", 14, QFont.Bold))
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.toggle_analysis)
        layout.addWidget(self.start_btn)
        
        section.setStyleSheet(f"""
            #controlsSection {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(0, 245, 255, 0.3);
                border-radius: 20px;
            }}
            #gestureBtn {{
                background: rgba(0, 245, 255, 0.1);
                border: 2px solid rgba(0, 245, 255, 0.3);
                border-radius: 12px;
            }}
            #gestureBtn:hover {{
                background: rgba(0, 245, 255, 0.2);
                border: 2px solid {Neon.CYAN};
            }}
            #gestureBtn:checked {{
                background: rgba(0, 245, 255, 0.3);
                border: 3px solid {Neon.CYAN};
            }}
        """)
        
        return section
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_footer(self):
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.sys_status = QLabel("◉ ANALYTICS READY")
        self.sys_status.setFont(QFont("Consolas", 11, QFont.Bold))
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(self.sys_status)
        
        layout.addStretch()
        
        self.analysis_hint = QLabel("Select a gesture and start analysis")
        self.analysis_hint.setFont(QFont("Consolas", 10))
        self.analysis_hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.analysis_hint)
        
        layout.addStretch()
        
        version = QLabel("GESTURE ANALYTICS v1.1")
        version.setFont(QFont("Consolas", 10))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
        
        return footer
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎮 GESTURE SELECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def select_gesture(self, name, emoji):
        """Select a gesture for analysis"""
        # Uncheck other buttons
        for btn_name, btn in self.gesture_buttons.items():
            if btn_name != name:
                btn.setChecked(False)
        
        self.current_gesture = name
        self.current_gesture_emoji = emoji
        
        self.gesture_display.setText(f"{emoji} {name}")
        self.gesture_display.setStyleSheet(f"color: {Neon.CYAN};")
        
        # Update heatmap expected pattern
        expected = self.gesture_patterns.get(name, [0, 0, 0, 0, 0])
        self.heatmap.set_finger_states([0, 0, 0, 0, 0], expected)
        
        # Reset attempt state
        self.reset_attempt_state()
        
        print(f"📊 Analyzing: {name}")
    
    def reset_attempt_state(self):
        """Reset the attempt state machine"""
        self.attempt_state = "WAITING"
        self.last_hand_detected = False
        self.gesture_start_time = None
        self.correct_hold_start = None
        self.cooldown_start = None
        self.current_accuracy = 0.0
        self.hold_progress.setValue(0)
        self.current_attempt_metrics = {
            "peak_accuracy": 0.0,
            "stability_samples": [],
            "start_time": None,
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎬 ANALYSIS CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def toggle_analysis(self):
        """Toggle analysis on/off"""
        if not self.is_analyzing:
            self.start_analysis_mode()
        else:
            self.stop_analysis_mode()
    
    def start_analysis_mode(self):
        """Start analysis session"""
    
        # Check if gesture selected
        if not self.current_gesture:
            self.analysis_hint.setText("⚠ Please select a gesture first!")
            self.analysis_hint.setStyleSheet(f"color: {Neon.RED};")
            return
    
        print("\n" + "📊"*40)
        print("📊 STARTING ANALYSIS SESSION")
        print("📊"*40)
    
        # STEP 1: STOP desktop/main camera
        print("  📡 Step 1: Stopping desktop camera...")
        try:
            import hand_tracker
            if hasattr(hand_tracker, 'set_camera_state'):
                hand_tracker.set_camera_state(False)
                hand_tracker.set_gesture_state(False)
                print("  ✅ Desktop camera stopped")
        except Exception as e:
            print(f"  ⚠️ Could not stop desktop camera: {e}")
    
        # STEP 2: START training tracker
        print("  📸 Step 2: Starting training tracker...")
        try:
            from training_tracker import TrainingGestureTracker
            import config
        
            camera_idx = getattr(config, 'camera_index', 0)
            print(f"  📷 Using camera index: {camera_idx}")
        
            self.tracker = TrainingGestureTracker(camera_index=camera_idx)
        
            if not self.tracker.start():
                print("  ❌ Failed to start training tracker!")
                try:
                    hand_tracker.set_camera_state(True)
                    hand_tracker.set_gesture_state(True)
                except:
                    pass
                self.analysis_hint.setText("❌ CAMERA ERROR - TRY AGAIN")
                self.analysis_hint.setStyleSheet(f"color: {Neon.RED};")
                return
        
            print("  ✅ Training tracker started successfully!")
        
        except Exception as e:
            print(f"  ❌ Tracker initialization error: {e}")
            import traceback
            traceback.print_exc()
            try:
                hand_tracker.set_camera_state(True)
                hand_tracker.set_gesture_state(True)
            except:
                pass
            self.analysis_hint.setText("❌ TRACKER ERROR")
            return
    
        # STEP 3: Activate analysis state
        print("  📊 Step 3: Activating analysis mode...")
    
        self.is_analyzing = True
        self.tracker_active = True
        
        # Reset attempt state
        self.reset_attempt_state()
        
        # Session start time
        self.session_data["start_time"] = time.time()
    
        # Update UI
        self.start_btn.setText("■  STOP ANALYSIS")
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
    
        self.sys_status.setText("◉ ANALYZING")
        self.sys_status.setStyleSheet(f"color: {Neon.YELLOW};")
    
        self.analysis_hint.setText(f"Show {self.current_gesture_emoji} {self.current_gesture} gesture")
        self.analysis_hint.setStyleSheet(f"color: {Neon.CYAN};")
    
        # Start timers
        self.camera_timer.start(33)
        self.analysis_timer.start(50)  # 50ms for smoother state updates
        self.session_timer.start(1000)
    
        print("✅ Analysis session ACTIVE!")
        print("📊"*40 + "\n")
    
    def stop_analysis_mode(self):
        """Stop analysis session"""

        print("\n" + "⏹️"*40)
        print("⏹️ STOPPING ANALYSIS SESSION")
        print("⏹️"*40)

        # STEP 1: STOP training tracker
        print("  📷 Step 1: Stopping training tracker...")

        if self.tracker is not None:
            try:
                self.tracker.stop()
                print("  ✅ Training tracker stopped")
                time.sleep(0.3)
                print("  ⏱️ Camera release delay applied")
            except Exception as e:
                print(f"  ⚠️ Tracker stop error: {e}")
            self.tracker = None

        self.tracker_active = False
    
        # STEP 2: RESTART desktop/main camera
        print("  📡 Step 2: Restarting desktop camera...")
        try:
            import hand_tracker
            if hasattr(hand_tracker, 'set_camera_state'):
                hand_tracker.set_camera_state(True)
                hand_tracker.set_gesture_state(True)
                print("  ✅ Desktop camera restarted")
        except Exception as e:
            print(f"  ⚠️ Could not restart desktop: {e}")
    
        # STEP 3: Reset UI state
        print("  🎨 Step 3: Resetting UI...")
    
        self.is_analyzing = False
    
        self.start_btn.setText("▶  START ANALYSIS")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 255, 159, 0.1);
                color: {Neon.GREEN};
                border: 2px solid {Neon.GREEN};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(0, 255, 159, 0.25);
            }}
        """)
    
        self.cam_status.setText("● OFFLINE")
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
    
        self.sys_status.setText("◉ ANALYTICS READY")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
    
        self.analysis_hint.setText("Select a gesture and start analysis")
        self.analysis_hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
    
        self.state_display.setText("STATE: STOPPED")
        self.state_display.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        self.hold_progress.setValue(0)
    
        # Stop timers
        self.camera_timer.stop()
        self.analysis_timer.stop()
        self.session_timer.stop()
    
        # Clear camera display
        self.camera_label.setText("⟨ ANALYSIS STOPPED ⟩")
    
        print("✅ Analysis session STOPPED!")
        print("⏹️"*40 + "\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📷 CAMERA FEED
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_camera_feed(self):
        """Update camera display"""
        if self.tracker is None or not self.tracker.is_running:
            self.camera_label.setText("⟨ WAITING FOR TRACKER ⟩")
            return
    
        frame, gesture, hand_detected, dwell = self.tracker.get_frame()
    
        if frame is not None:
            self.frame_count += 1
        
            resized = cv2.resize(frame, (440, 300))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            self.camera_label.setText("⟨ NO CAMERA FRAME ⟩")

    def set_tracker(self, tracker):
        """Set shared tracker from parent"""
        self.tracker = tracker
        print(f"✅ {self.__class__.__name__} received shared tracker")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📊 ✅ FIXED: PERFORMANCE ANALYSIS WITH REAL-TIME SPEED
    # ═══════════════════════════════════════════════════════════════════════════════

    def analyze_performance(self):
        """
        ✅ FIXED: State machine with real-time speed tracking
        """
        if not self.current_gesture or not self.is_analyzing:
            return

        # ═══════════════════════════════════════════════════════════════════════
        # GET CURRENT DATA FROM TRACKER
        # ═══════════════════════════════════════════════════════════════════════
        current_fingers = [0, 0, 0, 0, 0]
        hand_detected = False

        if self.tracker:
            # Get finger states
            if hasattr(self.tracker, 'finger_states'):
                current_fingers = list(self.tracker.finger_states)[:5]
        
            # ✅ Get hand detection from get_frame
            if hasattr(self.tracker, 'get_frame'):
                try:
                    frame, gesture, detected, dwell = self.tracker.get_frame()
                    hand_detected = detected
                except:
                    pass

        expected = self.gesture_patterns.get(self.current_gesture, [0, 0, 0, 0, 0])

        # Update heatmap
        self.heatmap.set_finger_states(current_fingers, expected)

        # Calculate accuracy
        correct_fingers = sum(1 for c, e in zip(current_fingers, expected) if c == e)
        accuracy = correct_fingers / 5
        self.current_accuracy = accuracy

        is_correct = accuracy >= 1.0
        current_time = time.time()
    
        # ═══════════════════════════════════════════════════════════════════════
        # ✅ REAL-TIME SPEED TRACKING
        # ═══════════════════════════════════════════════════════════════════════
        current_speed = 0.0
        if self.gesture_start_time and hand_detected:
            elapsed = current_time - self.gesture_start_time
            # Speed: How quickly did we reach correct gesture?
            # Fast (< 0.5s) = 100%, Slow (> 3s) = 0%
            if is_correct or accuracy > 0.6:
                current_speed = max(0, min(1, (3.0 - elapsed) / 2.5))
    
        # ═══════════════════════════════════════════════════════════════════════
        # STATE MACHINE
        # ═══════════════════════════════════════════════════════════════════════
    
        if self.attempt_state == "WAITING":
            self.state_display.setText("STATE: WAITING FOR HAND")
            self.state_display.setStyleSheet(f"color: {Neon.TEXT_DIM};")
            self.hold_progress.setValue(0)
        
            if hand_detected:
                self.attempt_state = "DETECTING"
                self.gesture_start_time = current_time
                self.current_attempt_metrics = {
                    "peak_accuracy": 0.0,
                    "stability_samples": [],
                    "start_time": current_time,
                    "time_to_correct": None,  # ✅ Track time to reach correct gesture
                }
                print(f"🖐️ Hand detected - Starting attempt")
    
        elif self.attempt_state == "DETECTING":
            self.state_display.setText(f"STATE: DETECTING ({accuracy*100:.0f}%)")
            self.state_display.setStyleSheet(f"color: {Neon.YELLOW};")
        
            # Track metrics
            self.current_attempt_metrics["peak_accuracy"] = max(
                self.current_attempt_metrics["peak_accuracy"], 
                accuracy
            )
            self.current_attempt_metrics["stability_samples"].append(accuracy)
        
            if not hand_detected:
                self.record_attempt(success=False, speed_metric=current_speed)
                self.attempt_state = "COOLDOWN"
                self.cooldown_start = current_time
                print(f"❌ Hand removed - Failed attempt")
            
            elif is_correct:
                # ✅ Record time to reach correct gesture
                self.current_attempt_metrics["time_to_correct"] = current_time - self.gesture_start_time
                self.attempt_state = "HOLDING"
                self.correct_hold_start = current_time
                print(f"✅ Correct gesture - Start holding (took {self.current_attempt_metrics['time_to_correct']:.2f}s)")
    
        elif self.attempt_state == "HOLDING":
            hold_time = current_time - self.correct_hold_start
            hold_percent = min(100, (hold_time / self.HOLD_TIME_REQUIRED) * 100)
        
            self.state_display.setText(f"STATE: HOLD ({hold_time:.1f}s / {self.HOLD_TIME_REQUIRED}s)")
            self.state_display.setStyleSheet(f"color: {Neon.GREEN};")
            self.hold_progress.setValue(int(hold_percent))
        
            self.current_attempt_metrics["stability_samples"].append(accuracy)
        
            if not hand_detected:
                self.record_attempt(success=False, speed_metric=current_speed)
                self.attempt_state = "COOLDOWN"
                self.cooldown_start = current_time
                print(f"❌ Hand removed during hold - Failed")
            
            elif not is_correct:
                self.attempt_state = "DETECTING"
                self.correct_hold_start = None
                self.hold_progress.setValue(0)
                print(f"⚠️ Gesture changed - Back to detecting")
            
            elif hold_time >= self.HOLD_TIME_REQUIRED:
                # ✅ Calculate final speed based on time_to_correct
                final_speed = current_speed
                if self.current_attempt_metrics["time_to_correct"]:
                    ttc = self.current_attempt_metrics["time_to_correct"]
                    final_speed = max(0, min(1, (2.0 - ttc) / 1.5))
            
                self.record_attempt(success=True, speed_metric=final_speed)
                self.attempt_state = "COOLDOWN"
                self.cooldown_start = current_time
                print(f"🎉 SUCCESS! Speed: {final_speed*100:.0f}%")
    
        elif self.attempt_state == "COOLDOWN":
            cooldown_elapsed = current_time - self.cooldown_start
            remaining = max(0, self.COOLDOWN_TIME - cooldown_elapsed)
        
            self.state_display.setText(f"STATE: COOLDOWN ({remaining:.1f}s)")
            self.state_display.setStyleSheet(f"color: {Neon.MAGENTA};")
            self.hold_progress.setValue(0)
        
            if cooldown_elapsed >= self.COOLDOWN_TIME and not hand_detected:
                self.attempt_state = "WAITING"
                print(f"⏱️ Cooldown complete - Ready")

        # ═══════════════════════════════════════════════════════════════════════
        # ✅ UPDATE RADAR WITH REAL-TIME SPEED
        # ═══════════════════════════════════════════════════════════════════════
        self.update_radar_metrics(current_speed=current_speed)
    
        self.last_hand_detected = hand_detected


    def record_attempt(self, success: bool, speed_metric: float = 0.0):
        """
        ✅ Record a single attempt with speed tracking
        """
        self.session_data["total_attempts"] += 1
    
        if success:
            self.session_data["total_success"] += 1
    
        # Update gesture stats
        if self.current_gesture in self.gesture_stats:
            self.gesture_stats[self.current_gesture]["practiced"] += 1
            if success:
                self.gesture_stats[self.current_gesture]["success"] += 1
    
        # ✅ Calculate and store reaction time
        if self.current_attempt_metrics.get("time_to_correct"):
            reaction_time = self.current_attempt_metrics["time_to_correct"]
            self.session_data["reaction_times"].append(reaction_time)
            print(f"   📊 Reaction time: {reaction_time:.2f}s")
        elif self.current_attempt_metrics["start_time"]:
            # Fallback: time since start
            reaction_time = time.time() - self.current_attempt_metrics["start_time"]
            self.session_data["reaction_times"].append(reaction_time)
    
        # Calculate stability
        samples = self.current_attempt_metrics["stability_samples"]
        if len(samples) > 1:
            mean = sum(samples) / len(samples)
            variance = sum((x - mean) ** 2 for x in samples) / len(samples)
            stability = 1.0 - min(1.0, variance * 2)
            self.session_data["stability_scores"].append(stability)
    
        # ✅ Store speed metric
        if "speed_scores" not in self.session_data:
            self.session_data["speed_scores"] = []
        self.session_data["speed_scores"].append(speed_metric)
    
        # Update UI
        self.update_stats_display()
    
        # Visual feedback
        if success:
            self.analysis_hint.setText(f"✅ SUCCESS! Speed: {speed_metric*100:.0f}%")
            self.analysis_hint.setStyleSheet(f"color: {Neon.GREEN};")
        else:
            self.analysis_hint.setText(f"❌ Try again! Hold {self.current_gesture_emoji} for 1 second")
            self.analysis_hint.setStyleSheet(f"color: {Neon.RED};")
    
        print(f"📊 Attempt: {'SUCCESS' if success else 'FAILED'} | "
              f"Total: {self.session_data['total_attempts']} | "
              f"Success: {self.session_data['total_success']}")


    def update_radar_metrics(self, current_speed: float = 0.0):
        """
        ✅ FIXED: Update radar with real-time metrics including speed
        """
        attempts = self.session_data["total_attempts"]
        success = self.session_data["total_success"]
    
        # ═══════════════════════════════════════════════════════════════════════
        # ACCURACY (overall success rate)
        # ═══════════════════════════════════════════════════════════════════════
        accuracy_metric = (success / attempts) if attempts > 0 else self.current_accuracy * 0.5
    
        # ═══════════════════════════════════════════════════════════════════════
        # ✅ SPEED (real-time + historical average)
        # ═══════════════════════════════════════════════════════════════════════
        speed_scores = self.session_data.get("speed_scores", [])
    
        if speed_scores:
            # Average of recorded speeds + current
            avg_speed = sum(speed_scores) / len(speed_scores)
            speed_metric = avg_speed * 0.7 + current_speed * 0.3  # Blend
        else:
            # No attempts yet - show current speed in real-time
            speed_metric = current_speed
    
        # ═══════════════════════════════════════════════════════════════════════
        # STABILITY (consistency of accuracy samples)
        # ═══════════════════════════════════════════════════════════════════════
        stability_scores = self.session_data.get("stability_scores", [])
        if stability_scores:
            stability_metric = sum(stability_scores) / len(stability_scores)
        else:
            # Real-time stability from current attempt
            samples = self.current_attempt_metrics.get("stability_samples", [])
            if len(samples) > 3:
                mean = sum(samples) / len(samples)
                variance = sum((x - mean) ** 2 for x in samples) / len(samples)
                stability_metric = 1.0 - min(1.0, variance * 3)
            else:
                stability_metric = 0.0
    
        # ═══════════════════════════════════════════════════════════════════════
        # PRECISION (current accuracy level)
        # ═══════════════════════════════════════════════════════════════════════
        precision_metric = self.current_accuracy
    
        # ═══════════════════════════════════════════════════════════════════════
        # UPDATE RADAR CHART
        # ═══════════════════════════════════════════════════════════════════════
        self.radar_chart.set_metrics(
            accuracy=accuracy_metric,
            speed=speed_metric,
            stability=stability_metric,
            precision=precision_metric
        )
    
    def update_stats_display(self):
        """Update stats in header"""
        attempts = self.session_data["total_attempts"]
        success = self.session_data["total_success"]
        accuracy = (success / attempts * 100) if attempts > 0 else 0
        
        self.stat_attempts.findChild(QLabel, "val").setText(str(attempts))
        self.stat_success.findChild(QLabel, "val").setText(str(success))
        self.stat_accuracy.findChild(QLabel, "val").setText(f"{accuracy:.0f}%")
        
        # Update gesture progress
        for gesture, stats in self.gesture_stats.items():
            self.gesture_progress.update_gesture(
                gesture, 
                stats["practiced"], 
                stats["success"]
            )
        
        # Update quick stats
        self.update_quick_stats()
    
    def update_quick_stats(self):
        """Update quick stats panel"""
        # Best gesture (highest success rate with at least 1 attempt)
        best_gesture = "---"
        best_rate = 0
        worst_gesture = "---"
        worst_rate = 1.0
        
        for gesture, stats in self.gesture_stats.items():
            if stats["practiced"] > 0:
                rate = stats["success"] / stats["practiced"]
                if rate > best_rate:
                    best_rate = rate
                    best_gesture = gesture
                if rate < worst_rate:
                    worst_rate = rate
                    worst_gesture = gesture
        
        self.quick_stat_labels["Best Gesture"].setText(best_gesture)
        self.quick_stat_labels["Needs Practice"].setText(worst_gesture if worst_gesture != "---" else "---")
        
        # Average reaction time
        reaction_times = self.session_data["reaction_times"]
        if reaction_times:
            avg_reaction = sum(reaction_times) / len(reaction_times)
            self.quick_stat_labels["Avg. Reaction"].setText(f"{avg_reaction:.2f}s")
        else:
            self.quick_stat_labels["Avg. Reaction"].setText("---")
        
        # Total score (attempts * accuracy * 10)
        attempts = self.session_data["total_attempts"]
        success = self.session_data["total_success"]
        score = success * 10
        self.quick_stat_labels["Total Score"].setText(str(score))
    
    def update_session_time(self):
        """Update session time display"""
        if self.session_data["start_time"]:
            elapsed = time.time() - self.session_data["start_time"]
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.quick_stat_labels["Session Time"].setText(f"{minutes}:{seconds:02d}")
    
    def calculate_fps(self):
        self.current_fps = self.frame_count
        self.frame_count = 0
        self.stat_fps.findChild(QLabel, "val").setText(str(self.current_fps))
    
    def reset_analytics(self):
        """Reset all analytics data"""
        self.session_data = {
            "total_attempts": 0,
            "total_success": 0,
            "reaction_times": [],
            "stability_scores": [],
            "speed_scores": [],  # ✅ ADD THIS
            "start_time": time.time() if self.is_analyzing else None,
        }
    
        for gesture in self.gesture_stats:
            self.gesture_stats[gesture] = {"practiced": 0, "success": 0}
    
        self.reset_attempt_state()
        self.radar_chart.set_metrics(0, 0, 0, 0)
        self.update_stats_display()
    
        # Reset quick stats labels
        self.quick_stat_labels["Best Gesture"].setText("---")
        self.quick_stat_labels["Needs Practice"].setText("---")
        self.quick_stat_labels["Avg. Reaction"].setText("---")
        self.quick_stat_labels["Session Time"].setText("0:00")
        self.quick_stat_labels["Total Score"].setText("0")
    
        print("🔄 Analytics Reset")
    
    def close_mode(self):
        """Close analytics mode"""
        print("🚪 Closing Gesture Analytics...")

        if self.is_analyzing:
            self.stop_analysis_mode()
            time.sleep(0.2)

        if self.tracker is not None:
            try:
                self.tracker.stop()
                self.tracker = None
            except:
                pass

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
            
            #scrollArea {{
                background: transparent;
                border: none;
            }}
            
            #scrollContent {{
                background: transparent;
            }}
            
            QScrollBar:vertical {{
                background: rgba(0, 30, 60, 0.4);
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.GREEN},
                    stop:1 {Neon.CYAN}
                );
                border-radius: 5px;
                min-height: 50px;
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            #header {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 255, 159, 0.1),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-bottom: 3px solid {Neon.GREEN};
            }}
            
            #backBtn {{
                background: rgba(0, 255, 159, 0.15);
                color: {Neon.GREEN};
                border: 2px solid {Neon.GREEN};
                border-radius: 12px;
            }}
            #backBtn:hover {{
                background: rgba(0, 255, 159, 0.35);
            }}
            
            #resetBtn {{
                background: rgba(255, 107, 0, 0.15);
                color: {Neon.ORANGE};
                border: 2px solid {Neon.ORANGE};
                border-radius: 12px;
            }}
            #resetBtn:hover {{
                background: rgba(255, 107, 0, 0.35);
            }}
            
            #camPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.GREEN};
                border-radius: 20px;
            }}
            
            #camDisplay {{
                background: #000000;
                border: 2px solid rgba(0, 255, 159, 0.4);
                border-radius: 12px;
                color: {Neon.TEXT_DIM};
                font-size: 14px;
            }}
            
            #startBtn {{
                background: rgba(0, 255, 159, 0.1);
                color: {Neon.GREEN};
                border: 2px solid {Neon.GREEN};
                border-radius: 15px;
            }}
            #startBtn:hover {{
                background: rgba(0, 255, 159, 0.25);
            }}
            
            #footer {{
                background: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(0, 255, 159, 0.1),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-top: 3px solid {Neon.GREEN};
            }}
        """)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up Gesture Analytics...")

        if self.is_analyzing:
            self.stop_analysis_mode()

        if hasattr(self, 'fps_timer'):
            self.fps_timer.stop()
        if hasattr(self, 'camera_timer'):
            self.camera_timer.stop()
        if hasattr(self, 'analysis_timer'):
            self.analysis_timer.stop()
        if hasattr(self, 'session_timer'):
            self.session_timer.stop()

        if self.tracker is not None:
            try:
                self.tracker.stop()
                time.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️ Tracker cleanup error: {e}")
            finally:
                self.tracker = None
    
    def closeEvent(self, event):
        """Proper cleanup on close"""
        self.cleanup()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN - For Testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    window = GestureAnalyticsMode()
    window.showMaximized()
    
    sys.exit(app.exec())
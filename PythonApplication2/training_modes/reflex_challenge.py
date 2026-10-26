"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        REFLEX CHALLENGE MODE                                 ║
║                   ⚡ Speed & Memory Training System ⚡                        ║
║                         Version 1.0                                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

This mode tests reaction speed and gesture memory:
- Random gesture prompts with time limits
- Reaction time measurement
- Correct/incorrect feedback with animations
- Memory sequence challenge (repeat gestures in order)
- Scoring system with combos
- Multiple difficulty levels
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QApplication, QStackedWidget
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, 
    QEasingCurve, Property, QSequentialAnimationGroup
)
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPen, QBrush, 
    QColor, QLinearGradient, QRadialGradient
)
import cv2
import time
import random
import sys
import os

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
# ⏱️ COUNTDOWN TIMER WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class CountdownWidget(QWidget):
    """
    Circular countdown timer with animation
    """
    
    timeout = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        
        self._progress = 1.0  # 1.0 = full, 0.0 = empty
        self._time_left = 0
        self._total_time = 3.0
        
        self.color = QColor(Neon.CYAN)
        self.warning_color = QColor(Neon.ORANGE)
        self.danger_color = QColor(Neon.RED)
        
        # Timer for countdown
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.tick)
        
    def start_countdown(self, seconds=3.0):
        """Start countdown"""
        self._total_time = seconds
        self._time_left = seconds
        self._progress = 1.0
        self.countdown_timer.start(50)  # Update every 50ms
        self.update()
    
    def stop_countdown(self):
        """Stop countdown"""
        self.countdown_timer.stop()
    
    def tick(self):
        """Update countdown"""
        self._time_left -= 0.05
        self._progress = max(0, self._time_left / self._total_time)
        
        if self._time_left <= 0:
            self.countdown_timer.stop()
            self.timeout.emit()
        
        self.update()
    
    def get_time_left(self):
        return self._time_left
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(self.width(), self.height()) / 2 - 15
        
        # Background circle
        painter.setPen(QPen(QColor(50, 60, 80), 8))
        painter.setBrush(QBrush(QColor(10, 15, 30)))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2))
        
        # Progress arc
        if self._progress > 0.5:
            color = self.color
        elif self._progress > 0.25:
            color = self.warning_color
        else:
            color = self.danger_color
        
        pen = QPen(color, 10)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw arc (Qt uses 1/16th of a degree)
        start_angle = 90 * 16  # Start from top
        span_angle = int(-self._progress * 360 * 16)  # Clockwise
        
        rect = self.rect().adjusted(15, 15, -15, -15)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Center text
        painter.setPen(color)
        font = QFont("Consolas", 36, QFont.Bold)
        painter.setFont(font)
        
        time_text = f"{self._time_left:.1f}"
        painter.drawText(self.rect(), Qt.AlignCenter, time_text)
        
        # Label
        painter.setPen(QColor(Neon.TEXT_DIM))
        font = QFont("Consolas", 10)
        painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, 55, 0, 0), Qt.AlignCenter, "SECONDS")


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 GESTURE PROMPT WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class GesturePromptWidget(QFrame):
    """
    Large gesture prompt display with animations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 300)
        self.setObjectName("gesturePrompt")
        
        self._scale = 1.0
        self._opacity = 1.0
        
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Emoji display
        self.emoji_label = QLabel("❓")
        self.emoji_label.setFont(QFont("Segoe UI Emoji", 80))
        self.emoji_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.emoji_label)
        
        # Gesture name
        self.name_label = QLabel("READY?")
        self.name_label.setFont(QFont("Consolas", 24, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(self.name_label)
        
        # Apply style
        self.setStyleSheet(f"""
            #gesturePrompt {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 255, 0.15),
                    stop:0.5 rgba(5, 10, 25, 0.95),
                    stop:1 rgba(0, 245, 255, 0.15)
                );
                border: 3px solid {Neon.CYAN};
                border-radius: 25px;
            }}
        """)
    
    def setup_animations(self):
        """Setup pulse animation"""
        self.pulse_anim = QPropertyAnimation(self, b"windowOpacity")
        self.pulse_anim.setDuration(200)
    
    def set_gesture(self, emoji, name, color=None):
        """Set the gesture to display"""
        self.emoji_label.setText(emoji)
        self.name_label.setText(name)
        
        if color:
            self.name_label.setStyleSheet(f"color: {color};")
            r, g, b = self.hex_rgb(color)
            self.setStyleSheet(f"""
                #gesturePrompt {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({r}, {g}, {b}, 0.2),
                        stop:0.5 rgba(5, 10, 25, 0.95),
                        stop:1 rgba({r}, {g}, {b}, 0.2)
                    );
                    border: 3px solid {color};
                    border-radius: 25px;
                }}
            """)
    
    def show_success(self):
        """Show success state"""
        self.emoji_label.setText("✅")
        self.name_label.setText("CORRECT!")
        self.name_label.setStyleSheet(f"color: {Neon.GREEN};")
        self.setStyleSheet(f"""
            #gesturePrompt {{
                background: rgba(0, 255, 159, 0.2);
                border: 4px solid {Neon.GREEN};
                border-radius: 25px;
            }}
        """)
    
    def show_fail(self):
        """Show fail state"""
        self.emoji_label.setText("❌")
        self.name_label.setText("WRONG!")
        self.name_label.setStyleSheet(f"color: {Neon.RED};")
        self.setStyleSheet(f"""
            #gesturePrompt {{
                background: rgba(255, 0, 85, 0.2);
                border: 4px solid {Neon.RED};
                border-radius: 25px;
            }}
        """)
    
    def show_timeout(self):
        """Show timeout state"""
        self.emoji_label.setText("⏰")
        self.name_label.setText("TOO SLOW!")
        self.name_label.setStyleSheet(f"color: {Neon.ORANGE};")
        self.setStyleSheet(f"""
            #gesturePrompt {{
                background: rgba(255, 107, 0, 0.2);
                border: 4px solid {Neon.ORANGE};
                border-radius: 25px;
            }}
        """)
    
    def reset(self):
        """Reset to default state"""
        self.set_gesture("❓", "READY?", Neon.CYAN)
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 MEMORY SEQUENCE WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class MemorySequenceWidget(QFrame):
    """
    Display sequence of gestures to memorize
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("memorySequence")
        self.setFixedHeight(120)
        
        self.sequence = []
        self.current_index = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("◈ SEQUENCE TO REPEAT")
        title.setFont(QFont("Consolas", 11, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.PURPLE};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Sequence display
        self.sequence_layout = QHBoxLayout()
        self.sequence_layout.setAlignment(Qt.AlignCenter)
        self.sequence_layout.setSpacing(15)
        layout.addLayout(self.sequence_layout)
        
        # Style
        self.setStyleSheet(f"""
            #memorySequence {{
                background: rgba(191, 0, 255, 0.1);
                border: 2px solid {Neon.PURPLE};
                border-radius: 15px;
            }}
        """)
    
    def set_sequence(self, gestures):
        """Set the sequence to display"""
        self.sequence = gestures
        self.current_index = 0
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the sequence display"""
        # Clear existing
        while self.sequence_layout.count():
            item = self.sequence_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add gesture indicators
        for i, (emoji, name, color) in enumerate(self.sequence):
            indicator = QLabel(emoji)
            indicator.setFont(QFont("Segoe UI Emoji", 32))
            indicator.setAlignment(Qt.AlignCenter)
            indicator.setFixedSize(60, 60)
            
            if i < self.current_index:
                # Completed - green
                indicator.setStyleSheet(f"""
                    background: rgba(0, 255, 159, 0.3);
                    border: 2px solid {Neon.GREEN};
                    border-radius: 12px;
                """)
            elif i == self.current_index:
                # Current - highlighted
                indicator.setStyleSheet(f"""
                    background: rgba(240, 255, 0, 0.3);
                    border: 3px solid {Neon.YELLOW};
                    border-radius: 12px;
                """)
            else:
                # Upcoming - dim
                indicator.setStyleSheet(f"""
                    background: rgba(255, 255, 255, 0.05);
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-radius: 12px;
                """)
            
            self.sequence_layout.addWidget(indicator)
    
    def advance(self):
        """Move to next in sequence"""
        self.current_index += 1
        self.refresh_display()
        return self.current_index >= len(self.sequence)
    
    def reset(self):
        """Reset sequence"""
        self.current_index = 0
        self.refresh_display()


# ═══════════════════════════════════════════════════════════════════════════════
# ⚡ REFLEX CHALLENGE MODE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class ReflexChallengeMode(QWidget):
    """
    Reflex Challenge Mode - Speed and memory training
    
    Features:
    - Random gesture prompts with countdown
    - Reaction time measurement
    - Correct/incorrect feedback
    - Memory sequence challenge
    - Score tracking with combos
    - Multiple game modes
    """
    
    mode_closed = Signal()
    
    def __init__(self, parent=None, tracker=None):
        super().__init__(parent)
    
        # ✅ USE SHARED TRACKER (passed from parent)
        self.tracker = tracker
    
        self.setWindowTitle("◈ REFLEX CHALLENGE")
        self.setMinimumSize(1400, 900)
        
        # ═══ GAME STATES ═══
        self.game_mode = "reflex"  # "reflex" or "memory"
        self.is_playing = False
        self.is_waiting_for_gesture = False
        self.current_round = 0
        self.max_rounds = 10
        
        # ═══ CURRENT GESTURE ═══
        self.current_gesture = None
        self.current_gesture_emoji = ""
        self.gesture_start_time = 0
        
        # ═══ STATS ═══
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.reaction_times = []
        self.time_limit = 3.0  # seconds
        
        # ═══ MEMORY MODE ═══
        self.memory_sequence = []
        self.memory_index = 0
        self.sequence_length = 3
        
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
        
        self.next_round_timer = QTimer()
        self.next_round_timer.setSingleShot(True)
        self.next_round_timer.timeout.connect(self.next_round)
        
        # ═══ FPS ═══
        self.frame_count = 0
        self.current_fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.calculate_fps)
        self.fps_timer.start(1000)
        
        print("⚡ Reflex Challenge Mode Initialized")
    
    def setup_ui(self):
        """Build UI"""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
    
        # Header
        header = self.build_header()
        main.addWidget(header)
    
        # ═══════════════════════════════════════════════════════════════
        # ✅ SCROLLABLE CONTENT AREA (Prevent overlap)
        # ═══════════════════════════════════════════════════════════════
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setObjectName("scrollArea")
    
        # Content widget
        content = QWidget()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 50)  # ← Bottom margin 25→50
        content_layout.setSpacing(25)
    
        # Mode selector row
        mode_row = self.build_mode_selector()
        content_layout.addWidget(mode_row)
    
        # Main game area
        game_row = self.build_game_area()
        content_layout.addWidget(game_row, 1)
    
        # Memory sequence (hidden by default)
        self.memory_widget = MemorySequenceWidget()
        self.memory_widget.setVisible(False)
        content_layout.addWidget(self.memory_widget)
    
        # Stats row
        stats_row = self.build_stats_row()
        content_layout.addWidget(stats_row)
    
        # ═══════════════════════════════════════════════════════════════
        # ✅ CRITICAL: Add extra bottom spacing
        # ═══════════════════════════════════════════════════════════════
        content_layout.addSpacing(60)  # Extra padding to prevent footer overlap
        # ═══════════════════════════════════════════════════════════════
    
        # Set content to scroll area
        scroll_area.setWidget(content)
        main.addWidget(scroll_area, 1)
    
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
        logo = QLabel("⚡")
        logo.setFont(QFont("Segoe UI Emoji", 28))
        logo.setFixedWidth(50)
        layout.addWidget(logo)
        
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        
        title = QLabel("REFLEX CHALLENGE")
        title.setFont(QFont("Consolas", 20, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.MAGENTA};")
        title_box.addWidget(title)
        
        subtitle = QLabel("SPEED & MEMORY TRAINING")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
        
        layout.addLayout(title_box)
        layout.addStretch()
        
        # Live stats
        self.stat_score = self.make_stat("SCORE", "0", Neon.YELLOW)
        layout.addWidget(self.stat_score)
        
        self.stat_combo = self.make_stat("COMBO", "0x", Neon.MAGENTA)
        layout.addWidget(self.stat_combo)
        
        self.stat_round = self.make_stat("ROUND", "0/10", Neon.CYAN)
        layout.addWidget(self.stat_round)
        
        self.stat_fps = self.make_stat("FPS", "0", Neon.GREEN)
        layout.addWidget(self.stat_fps)
        
        layout.addStretch()
        
        # Reset Button
        self.reset_btn = QPushButton("⟲  RESET")
        self.reset_btn.setFixedSize(120, 45)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self.reset_game)
        layout.addWidget(self.reset_btn)
        
        return header
    
    def make_stat(self, label, value, color):
        box = QFrame()
        box.setFixedSize(100, 50)
        
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
    # MODE SELECTOR
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_mode_selector(self):
        container = QFrame()
        container.setFixedHeight(80)
        container.setObjectName("modeSelector")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("⟨ SELECT GAME MODE ⟩")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Reflex Mode Button
        self.reflex_mode_btn = QPushButton("⚡  REFLEX MODE")
        self.reflex_mode_btn.setFixedSize(180, 50)
        self.reflex_mode_btn.setCursor(Qt.PointingHandCursor)
        self.reflex_mode_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.reflex_mode_btn.setCheckable(True)
        self.reflex_mode_btn.setChecked(True)
        self.reflex_mode_btn.setObjectName("modeBtn")
        self.reflex_mode_btn.clicked.connect(lambda: self.set_game_mode("reflex"))
        layout.addWidget(self.reflex_mode_btn)
        
        # Memory Mode Button
        self.memory_mode_btn = QPushButton("🧠  MEMORY MODE")
        self.memory_mode_btn.setFixedSize(180, 50)
        self.memory_mode_btn.setCursor(Qt.PointingHandCursor)
        self.memory_mode_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.memory_mode_btn.setCheckable(True)
        self.memory_mode_btn.setObjectName("modeBtn")
        self.memory_mode_btn.clicked.connect(lambda: self.set_game_mode("memory"))
        layout.addWidget(self.memory_mode_btn)
        
        layout.addStretch()
        
        # Difficulty selector
        diff_label = QLabel("DIFFICULTY:")
        diff_label.setFont(QFont("Consolas", 10))
        diff_label.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(diff_label)
        
        self.diff_buttons = {}
        for diff, time_limit in [("EASY", 4.0), ("NORMAL", 3.0), ("HARD", 2.0), ("INSANE", 1.0)]:
            btn = QPushButton(diff)
            btn.setFixedSize(80, 40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Consolas", 9, QFont.Bold))
            btn.setCheckable(True)
            btn.setObjectName("diffBtn")
            if diff == "NORMAL":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, t=time_limit, d=diff: self.set_difficulty(t, d))
            layout.addWidget(btn)
            self.diff_buttons[diff] = btn
        
        container.setStyleSheet(f"""
            #modeSelector {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(0, 245, 255, 0.3);
                border-radius: 15px;
            }}
            #modeBtn {{
                background: rgba(255, 0, 255, 0.1);
                color: {Neon.MAGENTA};
                border: 2px solid rgba(255, 0, 255, 0.3);
                border-radius: 10px;
            }}
            #modeBtn:hover {{
                background: rgba(255, 0, 255, 0.2);
                border: 2px solid {Neon.MAGENTA};
            }}
            #modeBtn:checked {{
                background: rgba(255, 0, 255, 0.3);
                border: 3px solid {Neon.MAGENTA};
            }}
            #diffBtn {{
                background: rgba(0, 245, 255, 0.1);
                color: {Neon.CYAN};
                border: 1px solid rgba(0, 245, 255, 0.3);
                border-radius: 8px;
            }}
            #diffBtn:hover {{
                background: rgba(0, 245, 255, 0.2);
            }}
            #diffBtn:checked {{
                background: rgba(0, 245, 255, 0.3);
                border: 2px solid {Neon.CYAN};
            }}
        """)
        
        return container
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAME AREA
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_game_area(self):
        container = QFrame()
        container.setMinimumHeight(450)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)
        
        # Camera Panel
        cam_panel = self.build_camera_panel()
        layout.addWidget(cam_panel)
        
        # Game Panel (Prompt + Timer)
        game_panel = self.build_game_panel()
        layout.addWidget(game_panel, 1)
        
        # Results Panel
        results_panel = self.build_results_panel()
        layout.addWidget(results_panel)
        
        return container
    
    def build_camera_panel(self):
        panel = QFrame()
        panel.setFixedWidth(450)
        panel.setObjectName("camPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("◉ YOUR CAMERA")
        cam_title.setFont(QFont("Consolas", 13, QFont.Bold))
        cam_title.setStyleSheet(f"color: {Neon.MAGENTA};")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        self.cam_status = QLabel("● OFFLINE")
        self.cam_status.setFont(QFont("Consolas", 10, QFont.Bold))
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
        cam_header.addWidget(self.cam_status)
        layout.addLayout(cam_header)
        
        # Camera Display
        self.camera_label = QLabel("⟨ START GAME ⟩\n\nPress START to begin")
        self.camera_label.setFixedSize(410, 300)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setObjectName("camDisplay")
        layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        
        # Current detection display
        self.detection_label = QLabel("Waiting...")
        self.detection_label.setFont(QFont("Consolas", 14, QFont.Bold))
        self.detection_label.setAlignment(Qt.AlignCenter)
        self.detection_label.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.detection_label)
        
        return panel
    
    def build_game_panel(self):
        panel = QFrame()
        panel.setObjectName("gamePanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("◈ PERFORM THIS GESTURE")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.YELLOW};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Gesture prompt and timer row
        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(40)
        prompt_row.setAlignment(Qt.AlignCenter)
        
        # Countdown timer
        self.countdown = CountdownWidget()
        self.countdown.timeout.connect(self.on_timeout)
        prompt_row.addWidget(self.countdown)
        
        # Gesture prompt
        self.gesture_prompt = GesturePromptWidget()
        prompt_row.addWidget(self.gesture_prompt)
        
        layout.addLayout(prompt_row)
        
        layout.addSpacing(20)
        
        # Reaction time display
        self.reaction_display = QLabel("REACTION: ---")
        self.reaction_display.setFont(QFont("Consolas", 16, QFont.Bold))
        self.reaction_display.setAlignment(Qt.AlignCenter)
        self.reaction_display.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(self.reaction_display)
        
        layout.addStretch()
        
        # Start button
        self.start_btn = QPushButton("▶  START GAME")
        self.start_btn.setFixedSize(220, 65)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFont(QFont("Consolas", 16, QFont.Bold))
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.toggle_game)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
        
        panel.setStyleSheet(f"""
            #gamePanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.YELLOW};
                border-radius: 20px;
            }}
        """)
        
        return panel
    
    def build_results_panel(self):
        panel = QFrame()
        panel.setFixedWidth(280)
        panel.setObjectName("resultsPanel")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("◈ SESSION STATS")
        title.setFont(QFont("Consolas", 14, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.GREEN};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Stats
        stats = [
            ("✓ Correct", "0", Neon.GREEN, "correct"),
            ("✗ Wrong", "0", Neon.RED, "wrong"),
            ("⚡ Avg Reaction", "---", Neon.CYAN, "avg_reaction"),
            ("🔥 Best Reaction", "---", Neon.YELLOW, "best_reaction"),
            ("🎯 Accuracy", "0%", Neon.MAGENTA, "accuracy"),
            ("🏆 Max Combo", "0x", Neon.ORANGE, "max_combo"),
        ]
        
        self.result_labels = {}
        
        for name, value, color, key in stats:
            row = QHBoxLayout()
            
            lbl = QLabel(name)
            lbl.setFont(QFont("Consolas", 11))
            lbl.setStyleSheet(f"color: {Neon.TEXT};")
            row.addWidget(lbl)
            
            row.addStretch()
            
            val = QLabel(value)
            val.setFont(QFont("Consolas", 13, QFont.Bold))
            val.setStyleSheet(f"color: {color};")
            row.addWidget(val)
            
            self.result_labels[key] = val
            layout.addLayout(row)
        
        layout.addStretch()
        
        # Recent reactions
        recent_title = QLabel("⟨ RECENT TIMES ⟩")
        recent_title.setFont(QFont("Consolas", 10, QFont.Bold))
        recent_title.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        recent_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(recent_title)
        
        self.recent_times = QLabel("---")
        self.recent_times.setFont(QFont("Consolas", 10))
        self.recent_times.setStyleSheet(f"color: {Neon.CYAN};")
        self.recent_times.setAlignment(Qt.AlignCenter)
        self.recent_times.setWordWrap(True)
        layout.addWidget(self.recent_times)
        
        panel.setStyleSheet(f"""
            #resultsPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.GREEN};
                border-radius: 20px;
            }}
        """)
        
        return panel
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATS ROW
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_stats_row(self):
        container = QFrame()
        container.setFixedHeight(100)
        container.setObjectName("statsRow")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(30)
        
        # Progress bar
        progress_box = QVBoxLayout()
        progress_box.setSpacing(8)
        
        progress_header = QHBoxLayout()
        progress_lbl = QLabel("⟨ ROUND PROGRESS ⟩")
        progress_lbl.setFont(QFont("Consolas", 11, QFont.Bold))
        progress_lbl.setStyleSheet(f"color: {Neon.CYAN};")
        progress_header.addWidget(progress_lbl)
        progress_header.addStretch()
        self.progress_pct = QLabel("0%")
        self.progress_pct.setFont(QFont("Consolas", 11, QFont.Bold))
        self.progress_pct.setStyleSheet(f"color: {Neon.CYAN};")
        progress_header.addWidget(self.progress_pct)
        progress_box.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setObjectName("progressBar")
        progress_box.addWidget(self.progress_bar)
        
        layout.addLayout(progress_box, 2)
        
        # Instructions
        instructions = QLabel(
            "⚡ REFLEX: React to random gestures as fast as possible!\n"
            "🧠 MEMORY: Watch the sequence, then repeat it in order!"
        )
        instructions.setFont(QFont("Consolas", 10))
        instructions.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions, 1)
        
        container.setStyleSheet(f"""
            #statsRow {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(0, 245, 255, 0.3);
                border-radius: 15px;
            }}
            #progressBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {Neon.CYAN};
                border-radius: 12px;
            }}
            #progressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.CYAN},
                    stop:0.5 {Neon.MAGENTA},
                    stop:1 {Neon.YELLOW}
                );
                border-radius: 11px;
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
        
        self.sys_status = QLabel("◉ READY TO PLAY")
        self.sys_status.setFont(QFont("Consolas", 11, QFont.Bold))
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(self.sys_status)
        
        layout.addStretch()
        
        self.game_hint = QLabel("Select a mode and press START")
        self.game_hint.setFont(QFont("Consolas", 10))
        self.game_hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.game_hint)
        
        layout.addStretch()
        
        version = QLabel("REFLEX CHALLENGE v1.0")
        version.setFont(QFont("Consolas", 10))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
        
        return footer
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎮 GAME LOGIC
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_game_mode(self, mode):
        """Set game mode"""
        self.game_mode = mode
        
        self.reflex_mode_btn.setChecked(mode == "reflex")
        self.memory_mode_btn.setChecked(mode == "memory")
        
        self.memory_widget.setVisible(mode == "memory")
        
        if mode == "memory":
            self.game_hint.setText("Watch the sequence, then repeat!")
        else:
            self.game_hint.setText("React to gestures as fast as possible!")
        
        print(f"🎮 Game mode: {mode}")
    
    def set_difficulty(self, time_limit, name):
        """Set difficulty level"""
        self.time_limit = time_limit
        
        for diff, btn in self.diff_buttons.items():
            btn.setChecked(diff == name)
        
        print(f"⚡ Difficulty: {name} ({time_limit}s)")
    
    def toggle_game(self):
        """Start or stop game"""
        if not self.is_playing:
            self.start_game()
        else:
            self.stop_game()
    
    def start_game(self):
        """✅ FIXED: Start game with tracker"""
        print("\n" + "⚡"*40)
        print("⚡ STARTING REFLEX GAME")
        print("⚡"*40)
    
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
    
                self.game_hint.setText("❌ CAMERA ERROR")
                self.game_hint.setStyleSheet(f"color: {Neon.RED};")
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
        
            self.game_hint.setText("❌ TRACKER ERROR")
            return
    
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: Activate game state
        # ═══════════════════════════════════════════════════════════════
        print("  🎮 Step 3: Starting game...")
    
        self.is_playing = True
        self.current_round = 0
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.reaction_times = []
    
        # Update UI
        self.start_btn.setText("■  STOP GAME")
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
    
        self.sys_status.setText("◉ GAME ACTIVE")
        self.sys_status.setStyleSheet(f"color: {Neon.YELLOW};")
    
        # Start camera feed
        self.camera_timer.start(33)
    
        # Setup game mode
        if self.game_mode == "memory":
            self.generate_memory_sequence()
            self.show_memory_sequence()
        else:
            self.next_round()
    
        print("✅ Reflex game ACTIVE!")
        print("  📸 Training camera: LIVE")
        print("  🖥️ Desktop camera: STOPPED")
        print("⚡"*40 + "\n")
    
    def stop_game(self):
        """✅ FIXED: Stop game and restore desktop camera"""
        print("\n" + "⏹️"*40)
        print("⏹️ STOPPING REFLEX GAME")
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
        # STEP 3: Reset game state
        # ═══════════════════════════════════════════════════════════════
        print("  🎨 Step 3: Resetting UI...")
    
        self.is_playing = False
        self.is_waiting_for_gesture = False
    
        # Stop timers
        self.camera_timer.stop()
        self.gesture_check_timer.stop()
        self.countdown.stop_countdown()
        self.next_round_timer.stop()
    
        # Update UI
        self.start_btn.setText("▶  START GAME")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 0, 255, 0.1);
                color: {Neon.MAGENTA};
                border: 2px solid {Neon.MAGENTA};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(255, 0, 255, 0.25);
            }}
        """)
    
        self.cam_status.setText("● OFFLINE")
        self.cam_status.setStyleSheet(f"color: {Neon.RED};")
    
        self.sys_status.setText("◉ GAME OVER")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
    
        self.gesture_prompt.reset()
        self.camera_label.setText(f"⟨ GAME OVER ⟩\n\nFinal Score: {self.score}")
    
        print(f"✅ Game stopped! Score: {self.score}")
        print("  📸 Training camera: STOPPED")
        print("  🖥️ Desktop camera: LIVE")
        print("⏹️"*40 + "\n")
    
    def next_round(self):
        """Move to next round"""
        if not self.is_playing:
            return
        
        self.current_round += 1
        
        if self.current_round > self.max_rounds:
            self.stop_game()
            return
        
        # Update progress
        progress = (self.current_round - 1) / self.max_rounds * 100
        self.progress_bar.setValue(int(progress))
        self.progress_pct.setText(f"{int(progress)}%")
        self.stat_round.findChild(QLabel, "val").setText(f"{self.current_round}/{self.max_rounds}")
        
        # Pick random gesture
        gesture = random.choice(self.gestures)
        self.current_gesture = gesture
        self.current_gesture_emoji = gesture[0]
        
        # Update prompt
        self.gesture_prompt.set_gesture(gesture[0], gesture[1], gesture[2])
        
        # Start countdown
        self.countdown.start_countdown(self.time_limit)
        
        # Start gesture detection
        self.gesture_start_time = time.time()
        self.is_waiting_for_gesture = True
        self.gesture_check_timer.start(50)
        
        self.game_hint.setText(f"Show: {gesture[0]} {gesture[1]}")
        
        print(f"⚡ Round {self.current_round}: {gesture[1]}")
    
    def check_gesture(self):
        """✅ FIXED: Check gesture using tracker"""
        if not self.is_waiting_for_gesture:
            return
    
        # Get current finger states from tracker
        current_fingers = [0, 0, 0, 0, 0]
        if self.tracker and hasattr(self.tracker, 'finger_states'):
            current_fingers = list(self.tracker.finger_states)[:5]
        expected = self.current_gesture[3]  # Finger pattern
        
        # Check if gesture matches
        if current_fingers == expected:
            self.on_correct_gesture()



    def set_tracker(self, tracker):
        """Set shared tracker from parent"""
        self.tracker = tracker
        print(f"✅ {self.__class__.__name__} received shared tracker")
    
    def on_correct_gesture(self):
        """Handle correct gesture"""
        if not self.is_waiting_for_gesture:
            return
        
        self.is_waiting_for_gesture = False
        self.gesture_check_timer.stop()
        self.countdown.stop_countdown()
        
        # Calculate reaction time
        reaction_time = time.time() - self.gesture_start_time
        self.reaction_times.append(reaction_time)
        
        # Update stats
        self.correct_count += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        
        # Calculate score (faster = more points, combo bonus)
        base_score = int(100 * (self.time_limit / reaction_time))
        combo_bonus = self.combo * 10
        round_score = base_score + combo_bonus
        self.score += round_score
        
        # Update UI
        self.gesture_prompt.show_success()
        self.reaction_display.setText(f"REACTION: {reaction_time:.3f}s (+{round_score})")
        self.reaction_display.setStyleSheet(f"color: {Neon.GREEN};")
        self.detection_label.setText(f"✓ {self.current_gesture[1]}")
        self.detection_label.setStyleSheet(f"color: {Neon.GREEN};")
        
        self.update_stats_display()
        
        # Next round after delay
        self.next_round_timer.start(1200)
        
        print(f"✓ Correct! Time: {reaction_time:.3f}s, Score: +{round_score}")
    
    def on_timeout(self):
        """Handle timeout"""
        if not self.is_waiting_for_gesture:
            return
        
        self.is_waiting_for_gesture = False
        self.gesture_check_timer.stop()
        
        # Reset combo
        self.wrong_count += 1
        self.combo = 0
        
        # Update UI
        self.gesture_prompt.show_timeout()
        self.reaction_display.setText("REACTION: TOO SLOW!")
        self.reaction_display.setStyleSheet(f"color: {Neon.ORANGE};")
        self.detection_label.setText("⏰ Timeout")
        self.detection_label.setStyleSheet(f"color: {Neon.ORANGE};")
        
        self.update_stats_display()
        
        # Next round after delay
        self.next_round_timer.start(1500)
        
        print("⏰ Timeout!")
    
    def on_wrong_gesture(self):
        """Handle wrong gesture (optional - called if wrong gesture detected)"""
        self.wrong_count += 1
        self.combo = 0
        
        self.gesture_prompt.show_fail()
        self.detection_label.setText("✗ Wrong gesture")
        self.detection_label.setStyleSheet(f"color: {Neon.RED};")
        
        self.update_stats_display()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧠 MEMORY MODE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_memory_sequence(self):
        """Generate random sequence for memory mode"""
        self.memory_sequence = random.sample(self.gestures, min(self.sequence_length, len(self.gestures)))
        self.memory_index = 0
        
        # Convert to format for widget
        seq_data = [(g[0], g[1], g[2]) for g in self.memory_sequence]
        self.memory_widget.set_sequence(seq_data)
    
    def show_memory_sequence(self):
        """Show the sequence to memorize"""
        self.game_hint.setText("Watch the sequence...")
        
        # Show each gesture in sequence
        self.show_sequence_index = 0
        self.sequence_display_timer = QTimer()
        self.sequence_display_timer.timeout.connect(self.display_next_in_sequence)
        self.sequence_display_timer.start(1500)
    
    def display_next_in_sequence(self):
        """Display next gesture in sequence"""
        if self.show_sequence_index >= len(self.memory_sequence):
            self.sequence_display_timer.stop()
            self.game_hint.setText("Now repeat the sequence!")
            self.start_memory_challenge()
            return
        
        gesture = self.memory_sequence[self.show_sequence_index]
        self.gesture_prompt.set_gesture(gesture[0], gesture[1], gesture[2])
        self.show_sequence_index += 1
    
    def start_memory_challenge(self):
        """Start the memory challenge (user repeats sequence)"""
        self.memory_index = 0
        self.memory_widget.reset()
        self.next_memory_gesture()
    
    def next_memory_gesture(self):
        """Move to next gesture in memory sequence"""
        if self.memory_index >= len(self.memory_sequence):
            # Completed sequence!
            self.score += 500  # Bonus for completing sequence
            self.game_hint.setText("Sequence complete! +500 bonus")
            self.sequence_length += 1  # Increase difficulty
            QTimer.singleShot(2000, self.start_game)  # Restart with longer sequence
            return
        
        gesture = self.memory_sequence[self.memory_index]
        self.current_gesture = gesture
        self.gesture_prompt.set_gesture(gesture[0], gesture[1], gesture[2])
        
        self.countdown.start_countdown(self.time_limit)
        self.gesture_start_time = time.time()
        self.is_waiting_for_gesture = True
        self.gesture_check_timer.start(50)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📊 STATS & CAMERA
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_stats_display(self):
        """Update all stats displays"""
        # Header stats
        self.stat_score.findChild(QLabel, "val").setText(str(self.score))
        self.stat_combo.findChild(QLabel, "val").setText(f"{self.combo}x")
        
        # Results panel
        self.result_labels["correct"].setText(str(self.correct_count))
        self.result_labels["wrong"].setText(str(self.wrong_count))
        self.result_labels["max_combo"].setText(f"{self.max_combo}x")
        
        # Accuracy
        total = self.correct_count + self.wrong_count
        if total > 0:
            accuracy = self.correct_count / total * 100
            self.result_labels["accuracy"].setText(f"{accuracy:.0f}%")
        
        # Reaction times
        if self.reaction_times:
            avg_time = sum(self.reaction_times) / len(self.reaction_times)
            best_time = min(self.reaction_times)
            self.result_labels["avg_reaction"].setText(f"{avg_time:.3f}s")
            self.result_labels["best_reaction"].setText(f"{best_time:.3f}s")
            
            # Recent times
            recent = self.reaction_times[-5:]
            recent_str = " | ".join([f"{t:.2f}s" for t in recent])
            self.recent_times.setText(recent_str)
    
    def update_camera_feed(self):
        """✅ FIXED: Use shared tracker"""
        if self.tracker is None or not self.tracker.is_running:
            self.camera_label.setText("⟨ WAITING FOR TRACKER ⟩")
            return
    
        frame, gesture, hand_detected, dwell = self.tracker.get_frame()
    
        if frame is not None:
            self.frame_count += 1
        
            resized = cv2.resize(frame, (410, 300))
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
    
    def reset_game(self):
        """Reset all game stats"""
        self.stop_game()
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.reaction_times = []
        self.current_round = 0
        self.sequence_length = 3
        
        self.progress_bar.setValue(0)
        self.progress_pct.setText("0%")
        self.gesture_prompt.reset()
        self.reaction_display.setText("REACTION: ---")
        self.reaction_display.setStyleSheet(f"color: {Neon.CYAN};")
        
        self.update_stats_display()
        
        print("🔄 Game Reset")
    
    def close_mode(self):
        """Close and return to hub"""
        print("🚪 Closing Reflex Challenge...")
    
        # Stop game if active
        if self.is_playing:
            self.stop_game()
    
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
                #scrollArea {{
                background: transparent;
                border: none;
            }}
        
            QScrollBar:vertical {{
                background: rgba(30, 40, 60, 0.5);
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }}
        
            QScrollBar::handle:vertical {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.MAGENTA},
                    stop:1 {Neon.CYAN}
                );
                border-radius: 5px;
                min-height: 30px;
            }}
        
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.CYAN},
                    stop:1 {Neon.MAGENTA}
                );
            }}
        
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
            #header {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 0, 255, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-bottom: 3px solid {Neon.MAGENTA};
            }}
            
            #backBtn {{
                background: rgba(255, 0, 255, 0.15);
                color: {Neon.MAGENTA};
                border: 2px solid {Neon.MAGENTA};
                border-radius: 12px;
            }}
            #backBtn:hover {{
                background: rgba(255, 0, 255, 0.35);
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
                border: 2px solid {Neon.MAGENTA};
                border-radius: 20px;
            }}
            
            #camDisplay {{
                background: #000000;
                border: 2px solid rgba(255, 0, 255, 0.4);
                border-radius: 12px;
                color: {Neon.TEXT_DIM};
                font-size: 14px;
            }}
            
            #startBtn {{
                background: rgba(255, 0, 255, 0.1);
                color: {Neon.MAGENTA};
                border: 2px solid {Neon.MAGENTA};
                border-radius: 15px;
            }}
            #startBtn:hover {{
                background: rgba(255, 0, 255, 0.25);
            }}
            
            #footer {{
                background: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(255, 0, 255, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-top: 3px solid {Neon.MAGENTA};
            }}
        """)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def cleanup(self):
        """✅ FIXED: Clean up resources with proper camera shutdown"""
        print("🧹 Cleaning up Reflex Challenge...")

        # Stop game
        if self.is_playing:
            self.stop_game()

        # Stop all timers
        timers = ['camera_timer', 'gesture_check_timer', 'countdown_timer', 
                  'next_round_timer', 'fps_timer', 'sequence_display_timer']

        for timer_name in timers:
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

        print("✅ Reflex Challenge cleaned up")
    
    def closeEvent(self, event):
        self.cleanup()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN - For Testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    window = ReflexChallengeMode()
    window.showMaximized()
    
    sys.exit(app.exec())
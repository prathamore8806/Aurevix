"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📊 AI ANALYTICS WIDGET - PERFORMANCE VISUALIZATION        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📈 Real-time performance graphs                                             ║
║  🎯 Gesture mastery indicators                                               ║
║  💡 Personalized recommendations                                             ║
║  ✨ Cyberpunk holographic design                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath
)
import math
from collections import deque

from gaming_mode.constants import CyberColors


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 AI ANALYTICS WIDGET - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AIAnalyticsWidget(QWidget):
    """
    📊 AI Analytics Dashboard Widget
    
    Displays real-time AI learning analytics in cyberpunk style:
    - Gesture mastery bars
    - Performance trend graph
    - Recommendations panel
    - Live stats
    """
    
    def __init__(self, ai_learner=None, parent=None):
        super().__init__(parent)
        self.ai_learner = ai_learner
        self.setFixedWidth(280)
        self.setMinimumHeight(450)
        
        # Animation
        self.animation_frame = 0
        self.pulse_frame = 0
        
        # Data caching
        self.cached_stats = {}
        self.performance_history = deque(maxlen=50)
        
        # Timer for animations
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(100)  # 10 FPS for smooth animations
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container frame
        self.container = QFrame()
        self.container.setObjectName("analyticsContainer")
        self.container.setStyleSheet(f"""
            #analyticsContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(13, 27, 42, 0.95),
                    stop:1 rgba(5, 10, 21, 0.95));
                border: 2px solid {CyberColors.CYAN_DARK};
                border-radius: 8px;
            }}
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(10)
        
        # Header
        header = QLabel("◢ AI ANALYTICS ◣")
        header.setFont(QFont("Consolas", 11, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(32)
        header.setStyleSheet(f"""
            color: {CyberColors.NEON_PURPLE};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {CyberColors.NAVY_DARKEST},
                stop:0.5 {CyberColors.NAVY_DARKER},
                stop:1 {CyberColors.NAVY_DARKEST});
            border: 1px solid {CyberColors.NEON_PURPLE};
            border-radius: 4px;
        """)
        container_layout.addWidget(header)
        
        # Canvas for custom painting
        self.canvas = AIAnalyticsCanvas(self.ai_learner)
        container_layout.addWidget(self.canvas, stretch=1)
        
        layout.addWidget(self.container)
    
    def _animate(self):
        """Update animation"""
        self.animation_frame = (self.animation_frame + 1) % 360
        self.pulse_frame = (self.pulse_frame + 5) % 360
        
        # Update canvas
        if self.canvas:
            self.canvas.update()
    
    def set_ai_learner(self, ai_learner):
        """Set the AI learner instance"""
        self.ai_learner = ai_learner
        if self.canvas:
            self.canvas.ai_learner = ai_learner
    
    def update_stats(self):
        """Force update statistics"""
        if self.canvas:
            self.canvas.update()


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 AI ANALYTICS CANVAS - CUSTOM PAINTING
# ═══════════════════════════════════════════════════════════════════════════════

class AIAnalyticsCanvas(QWidget):
    """Custom widget for AI analytics visualization"""
    
    def __init__(self, ai_learner=None, parent=None):
        super().__init__(parent)
        self.ai_learner = ai_learner
        self.animation_frame = 0
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(100)
    
    def _animate(self):
        self.animation_frame = (self.animation_frame + 1) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background
        bg_gradient = QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0, QColor(5, 15, 25, 250))
        bg_gradient.setColorAt(1, QColor(10, 20, 35, 250))
        painter.fillRect(0, 0, w, h, bg_gradient)
        
        if not self.ai_learner:
            self._draw_no_data(painter, w, h)
            painter.end()
            return
        
        # Get stats
        try:
            overall_stats = self.ai_learner.get_overall_stats()
            gesture_report = self.ai_learner.get_gesture_report()
        except Exception as e:
            print(f"⚠️ Analytics error: {e}")
            self._draw_no_data(painter, w, h)
            painter.end()
            return
        
        # Layout sections
        y_offset = 10
        
        # 1. Overall Stats Summary
        y_offset = self._draw_overall_stats(painter, w, y_offset, overall_stats)
        y_offset += 15
        
        # 2. Gesture Mastery Bars
        y_offset = self._draw_mastery_bars(painter, w, y_offset, gesture_report)
        y_offset += 15
        
        # 3. Performance Trend
        y_offset = self._draw_performance_trend(painter, w, y_offset)
        y_offset += 15
        
        # 4. Recommendations
        self._draw_recommendations(painter, w, y_offset, overall_stats)
        
        painter.end()
    
    def _draw_no_data(self, painter, w, h):
        """Draw when no data available"""
        painter.setPen(QColor(CyberColors.TEXT_DIM))
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignCenter,
                        "◎ NO DATA\n\nStart training to\nsee analytics")
    
    def _draw_overall_stats(self, painter, w, y_offset, stats):
        """Draw overall statistics summary"""
        # Section header
        painter.setPen(QColor(CyberColors.CYAN_PRIMARY))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(10, y_offset + 15, "◢ OVERALL STATS")
        
        # Stats background
        stats_bg = QRectF(10, y_offset + 20, w - 20, 75)
        painter.fillRect(stats_bg, QColor(0, 20, 40, 180))
        painter.setPen(QPen(QColor(0, 150, 200, 100), 1))
        painter.drawRoundedRect(stats_bg, 4, 4)
        
        # Stats data
        painter.setFont(QFont("Consolas", 8))
        
        # Mastery (large)
        avg_mastery = stats.get('avg_mastery', 0.0)
        mastery_color = self._get_mastery_color(avg_mastery)
        painter.setPen(mastery_color)
        painter.setFont(QFont("Consolas", 18, QFont.Bold))
        painter.drawText(QRectF(15, y_offset + 28, 80, 30), Qt.AlignCenter,
                        f"{avg_mastery:.0%}")
        
        painter.setFont(QFont("Consolas", 7))
        painter.setPen(QColor(CyberColors.TEXT_DIM))
        painter.drawText(QRectF(15, y_offset + 58, 80, 15), Qt.AlignCenter, "AVG MASTERY")
        
        # Stats grid (right side)
        painter.setFont(QFont("Consolas", 8))
        
        success_rate = stats.get('success_rate', 0.0)
        total_attempts = stats.get('total_attempts', 0)
        sessions = stats.get('total_sessions', 0)
        
        stats_list = [
            ("SUCCESS:", f"{success_rate:.0%}", QColor(0, 255, 136)),
            ("ATTEMPTS:", f"{total_attempts}", QColor(0, 200, 255)),
            ("SESSIONS:", f"{sessions}", QColor(255, 215, 0)),
        ]
        
        for i, (label, value, color) in enumerate(stats_list):
            y = y_offset + 30 + i * 16
            painter.setPen(QColor(CyberColors.TEXT_DIM))
            painter.drawText(105, y, label)
            painter.setPen(color)
            painter.drawText(180, y, value)
        
        return int(stats_bg.bottom()) + 5
    
    def _draw_mastery_bars(self, painter, w, y_offset, gesture_report):
        """Draw gesture mastery bars"""
        # Section header
        painter.setPen(QColor(CyberColors.NEON_GREEN))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(10, y_offset + 15, "◢ GESTURE MASTERY")
        
        # Background
        bar_section = QRectF(10, y_offset + 20, w - 20, 120)
        painter.fillRect(bar_section, QColor(0, 20, 40, 180))
        painter.setPen(QPen(QColor(0, 150, 200, 100), 1))
        painter.drawRoundedRect(bar_section, 4, 4)
        
        # Draw bars for each gesture
        directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        bar_height = 20
        bar_spacing = 6
        
        for i, direction in enumerate(directions):
            if direction not in gesture_report:
                continue
            
            data = gesture_report[direction]
            mastery = data.get('mastery_level', 0.0)
            needs_practice = data.get('needs_practice', True)
            
            y = y_offset + 30 + i * (bar_height + bar_spacing)
            
            # Icon and label
            icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}
            icon = icons.get(direction, "●")
            
            painter.setPen(QColor(CyberColors.TEXT_LIGHT))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(18, int(y + 15), icon)
            
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(35, int(y + 14), direction)
            
            # Bar background
            bar_x = 85
            bar_w = w - bar_x - 60
            
            painter.fillRect(int(bar_x), int(y), int(bar_w), bar_height,
                           QColor(20, 40, 60))
            
            # Mastery bar (animated)
            pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.05 + i * 0.5)
            
            mastery_color = self._get_mastery_color(mastery)
            bar_fill = int(bar_w * mastery)
            
            gradient = QLinearGradient(bar_x, y, bar_x + bar_fill, y)
            gradient.setColorAt(0, mastery_color)
            gradient.setColorAt(1, QColor(
                mastery_color.red(),
                mastery_color.green(),
                mastery_color.blue(),
                int(150 + 100 * pulse)
            ))
            
            painter.fillRect(int(bar_x), int(y), bar_fill, bar_height, gradient)
            
            # Border
            painter.setPen(QPen(mastery_color, 1))
            painter.drawRect(int(bar_x), int(y), int(bar_w), bar_height)
            
            # Percentage
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.drawText(int(bar_x + bar_w + 8), int(y + 14), f"{mastery:.0%}")
            
            # Practice indicator
            if needs_practice:
                pulse_alpha = int(100 + 100 * pulse)
                painter.setPen(QColor(255, 165, 0, pulse_alpha))
                painter.setFont(QFont("Consolas", 7))
                painter.drawText(int(bar_x + 2), int(y + 12), "⚠")
        
        return int(bar_section.bottom()) + 5
    
    def _draw_performance_trend(self, painter, w, y_offset):
        """Draw performance trend graph"""
        # Section header
        painter.setPen(QColor(CyberColors.GOLD))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(10, y_offset + 15, "◢ PERFORMANCE TREND")
        
        # Graph background
        graph_rect = QRectF(10, y_offset + 20, w - 20, 80)
        painter.fillRect(graph_rect, QColor(0, 20, 40, 180))
        painter.setPen(QPen(QColor(0, 150, 200, 100), 1))
        painter.drawRoundedRect(graph_rect, 4, 4)
        
        # Get recent performance data
        if not self.ai_learner or not hasattr(self.ai_learner, 'recent_performance'):
            return int(graph_rect.bottom()) + 5
        
        recent = list(self.ai_learner.recent_performance)
        
        if len(recent) < 2:
            # Not enough data
            painter.setPen(QColor(CyberColors.TEXT_DIM))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(graph_rect, Qt.AlignCenter, "Collecting data...")
            return int(graph_rect.bottom()) + 5
        
        # Draw graph
        graph_x = graph_rect.left() + 15
        graph_y = graph_rect.top() + 15
        graph_w = graph_rect.width() - 30
        graph_h = graph_rect.height() - 30
        
        # Grid lines
        painter.setPen(QPen(QColor(0, 100, 150, 30), 1, Qt.DashLine))
        for i in range(5):
            y = graph_y + (graph_h / 4) * i
            painter.drawLine(int(graph_x), int(y), int(graph_x + graph_w), int(y))
        
        # Plot performance line
        points = []
        max_points = min(30, len(recent))
        recent_subset = recent[-max_points:]
        
        for i, perf in enumerate(recent_subset):
            x = graph_x + (graph_w / max_points) * i
            # Success = 1, Failure = 0
            value = 1.0 if perf.get('success', False) else 0.0
            y = graph_y + graph_h - (value * graph_h)
            points.append(QPointF(x, y))
        
        # Draw line
        if len(points) > 1:
            painter.setPen(QPen(QColor(0, 255, 200), 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # Draw points
        for i, point in enumerate(points):
            success = recent_subset[i].get('success', False)
            color = QColor(0, 255, 136) if success else QColor(255, 80, 80)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(point, 3, 3)
        
        # Trend indicator
        trend = self.ai_learner.get_recent_performance_trend()
        trend_text = {
            "IMPROVING": ("↗ IMPROVING", QColor(0, 255, 136)),
            "DECLINING": ("↘ DECLINING", QColor(255, 80, 80)),
            "STABLE": ("→ STABLE", QColor(0, 200, 255)),
            "INSUFFICIENT_DATA": ("◎ LOADING", QColor(CyberColors.TEXT_DIM))
        }
        
        text, color = trend_text.get(trend, ("?", QColor(CyberColors.TEXT_DIM)))
        painter.setPen(color)
        painter.setFont(QFont("Consolas", 7, QFont.Bold))
        painter.drawText(int(graph_x + graph_w - 60), int(graph_y - 5), text)
        
        return int(graph_rect.bottom()) + 5
    
    def _draw_recommendations(self, painter, w, y_offset, stats):
        """Draw AI recommendations"""
        # Section header
        painter.setPen(QColor(CyberColors.NEON_PINK))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(10, y_offset + 15, "◢ AI RECOMMENDATIONS")
        
        # Recommendations background
        rec_rect = QRectF(10, y_offset + 20, w - 20, 75)
        painter.fillRect(rec_rect, QColor(0, 20, 40, 180))
        painter.setPen(QPen(QColor(0, 150, 200, 100), 1))
        painter.drawRoundedRect(rec_rect, 4, 4)
        
        # Get weakest gesture
        weakest = stats.get('weakest_gesture', 'NONE')
        weakest_mastery = stats.get('weakest_mastery', 0.0)
        
        # Icon
        icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶", "NONE": "◎"}
        icon = icons.get(weakest, "●")
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
        icon_color = QColor(255, 165, 0, int(150 + 100 * pulse))
        
        painter.setPen(icon_color)
        painter.setFont(QFont("Consolas", 36, QFont.Bold))
        painter.drawText(QRectF(15, y_offset + 25, 60, 50), Qt.AlignCenter, icon)
        
        # Recommendation text
        painter.setPen(QColor(CyberColors.TEXT_LIGHT))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(85, y_offset + 38, "FOCUS ON:")
        
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        painter.drawText(85, y_offset + 54, weakest)
        
        painter.setFont(QFont("Consolas", 7))
        painter.setPen(QColor(CyberColors.TEXT_DIM))
        painter.drawText(85, y_offset + 68, f"Mastery: {weakest_mastery:.0%}")
        
        # Motivational message
        if weakest_mastery < 0.3:
            msg = "⚠ Needs practice!"
            color = QColor(255, 100, 100)
        elif weakest_mastery < 0.6:
            msg = "💪 Keep going!"
            color = QColor(255, 165, 0)
        else:
            msg = "✨ Almost there!"
            color = QColor(0, 255, 136)
        
        painter.setPen(color)
        painter.setFont(QFont("Consolas", 7, QFont.Bold))
        painter.drawText(85, y_offset + 82, msg)
    
    def _get_mastery_color(self, mastery):
        """Get color based on mastery level"""
        if mastery >= 0.8:
            return QColor(0, 255, 136)  # Green - Expert
        elif mastery >= 0.6:
            return QColor(0, 200, 255)  # Cyan - Good
        elif mastery >= 0.4:
            return QColor(255, 215, 0)  # Gold - Average
        elif mastery >= 0.2:
            return QColor(255, 165, 0)  # Orange - Poor
        else:
            return QColor(255, 80, 80)  # Red - Needs work


# ═══════════════════════════════════════════════════════════════════════════════
# COMPACT VERSION - For smaller displays
# ═══════════════════════════════════════════════════════════════════════════════

class CompactAnalyticsWidget(QWidget):
    """Compact version of analytics widget for smaller spaces"""
    
    def __init__(self, ai_learner=None, parent=None):
        super().__init__(parent)
        self.ai_learner = ai_learner
        self.setFixedSize(200, 120)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor(0, 20, 40, 200))
        painter.setPen(QPen(QColor(0, 150, 200), 2))
        painter.drawRoundedRect(1, 1, w-2, h-2, 6, 6)
        
        if not self.ai_learner:
            painter.setPen(QColor(CyberColors.TEXT_DIM))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, "NO DATA")
            painter.end()
            return
        
        try:
            stats = self.ai_learner.get_overall_stats()
        except:
            painter.end()
            return
        
        # Title
        painter.setPen(QColor(CyberColors.CYAN_PRIMARY))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(10, 20, "AI STATS")
        
        # Quick stats
        painter.setFont(QFont("Consolas", 8))
        
        avg_mastery = stats.get('avg_mastery', 0.0)
        success_rate = stats.get('success_rate', 0.0)
        
        painter.setPen(QColor(0, 255, 136))
        painter.drawText(10, 40, f"Mastery: {avg_mastery:.0%}")
        
        painter.setPen(QColor(0, 200, 255))
        painter.drawText(10, 56, f"Success: {success_rate:.0%}")
        
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(10, 72, f"Attempts: {stats.get('total_attempts', 0)}")
        
        # Weakest gesture indicator
        weakest = stats.get('weakest_gesture', 'NONE')
        icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}
        icon = icons.get(weakest, "●")
        
        painter.setPen(QColor(255, 165, 0))
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(10, 88, "Focus:")
        
        painter.setFont(QFont("Consolas", 16, QFont.Bold))
        painter.drawText(10, 108, icon)
        
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(30, 105, weakest)
        
        painter.end()


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    # Import AI learner for testing
    try:
        from gaming_mode.ai_pattern_learner import AIPatternLearner
        ai_learner = AIPatternLearner()
        
        # Simulate some data
        import random
        ai_learner.start_session()
        for _ in range(30):
            direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
            success = random.random() > 0.3
            reaction_time = random.uniform(0.5, 2.0)
            ai_learner.record_gesture(direction, success, reaction_time)
        
    except ImportError:
        print("⚠️ AI Pattern Learner not found, using None")
        ai_learner = None
    
    print("\n" + "=" * 60)
    print("  📊 AI ANALYTICS WIDGET - Standalone Test")
    print("=" * 60 + "\n")
    
    app = QApplication(sys.argv)
    
    # Test full widget
    widget = AIAnalyticsWidget(ai_learner)
    widget.setWindowTitle("AI Analytics - Full")
    widget.show()
    
    # Test compact widget
    compact = CompactAnalyticsWidget(ai_learner)
    compact.setWindowTitle("AI Analytics - Compact")
    compact.move(320, 0)
    compact.show()
    
    sys.exit(app.exec())
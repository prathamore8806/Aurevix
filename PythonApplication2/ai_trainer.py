"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           AI TRAINER ANALYSIS PAGE                           ║
║                    📊 Complete Performance Analytics 📊                       ║
║                         Version 2.0 - FULLY FIXED                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝

FIXED:
✅ All content visible
✅ Proper responsive layout
✅ No hidden content
✅ Smaller optimized boxes
✅ Both scrollbars working
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QPropertyAnimation, 
    QEasingCurve, Property, QRectF, QPointF
)
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPen, QBrush, 
    QColor, QLinearGradient, QPainterPath, QPolygonF
)
import json
import os
import sys
from datetime import datetime, timedelta
import math


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
# 📊 PROGRESS CHART WIDGET - RESPONSIVE
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressChartWidget(QWidget):
    """Line chart - Responsive size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ✅ FIXED: Flexible size
        self.setMinimumSize(400, 220)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.sessions = []
        self.load_sample_data()
    
    def load_sample_data(self):
        self.sessions = [
            (1, 1, 45), (2, 2, 55), (3, 2, 60), (4, 3, 65), (5, 3, 70),
            (6, 4, 68), (7, 4, 75), (8, 5, 72), (9, 5, 80), (10, 6, 78),
        ]
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(5, 10, 20))
        painter.setPen(QPen(QColor(Neon.CYAN), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        
        painter.setPen(QColor(Neon.CYAN))
        font = QFont("Consolas", 11, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(10, 5, 250, 25), Qt.AlignLeft | Qt.AlignVCenter, 
                        "◈ LEVEL PROGRESSION")
        
        if not self.sessions:
            return
        
        self.draw_grid(painter)
        self.draw_level_line(painter)
        self.draw_accuracy_line(painter)
        self.draw_legend(painter)
    
    def draw_grid(self, painter):
        left = 50
        right = self.width() - 20
        top = 40
        bottom = self.height() - 40
        
        painter.setPen(QPen(QColor(40, 50, 70), 1))
        for i in range(5):
            y = top + (bottom - top) * i / 4
            painter.drawLine(left, int(y), right, int(y))
        
        painter.setPen(QColor(Neon.TEXT_DIM))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        
        for i, label in enumerate(["100", "75", "50", "25", "0"]):
            y = top + (bottom - top) * i / 4
            painter.drawText(QRectF(5, y - 8, 40, 16), Qt.AlignRight | Qt.AlignVCenter, label)
        
        painter.setPen(QPen(QColor(60, 70, 90), 2))
        painter.drawLine(left, bottom, right, bottom)
        painter.drawLine(left, top, left, bottom)
    
    def draw_level_line(self, painter):
        left = 50
        right = self.width() - 20
        top = 40
        bottom = self.height() - 40
        
        width = right - left
        height = bottom - top
        
        if len(self.sessions) < 2:
            return
        
        points = []
        step = width / (len(self.sessions) - 1)
        
        for i, (_, level, _) in enumerate(self.sessions):
            x = left + i * step
            y = bottom - (level / 10.0 * height)
            points.append(QPointF(x, y))
        
        pen = QPen(QColor(Neon.ORANGE), 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        
        painter.setBrush(QBrush(QColor(Neon.WHITE)))
        painter.setPen(QPen(QColor(Neon.ORANGE), 2))
        
        for point in points:
            painter.drawEllipse(point, 4, 4)
    
    def draw_accuracy_line(self, painter):
        left = 50
        right = self.width() - 20
        top = 40
        bottom = self.height() - 40
        
        width = right - left
        height = bottom - top
        
        if len(self.sessions) < 2:
            return
        
        points = []
        step = width / (len(self.sessions) - 1)
        
        for i, (_, _, accuracy) in enumerate(self.sessions):
            x = left + i * step
            y = bottom - (accuracy / 100.0 * height)
            points.append(QPointF(x, y))
        
        pen = QPen(QColor(Neon.GREEN), 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        
        painter.setBrush(QBrush(QColor(Neon.WHITE)))
        painter.setPen(QPen(QColor(Neon.GREEN), 2))
        
        for point in points:
            painter.drawEllipse(point, 3, 3)
    
    def draw_legend(self, painter):
        x = self.width() - 150
        y = 5
        
        painter.setPen(QColor(Neon.TEXT))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        
        painter.setPen(QPen(QColor(Neon.ORANGE), 2))
        painter.drawLine(x, y + 10, x + 20, y + 10)
        painter.setPen(QColor(Neon.TEXT))
        painter.drawText(QRectF(x + 25, y + 2, 60, 16), Qt.AlignLeft | Qt.AlignVCenter, "Level")
        
        y += 18
        painter.setPen(QPen(QColor(Neon.GREEN), 2))
        painter.drawLine(x, y + 10, x + 20, y + 10)
        painter.setPen(QColor(Neon.TEXT))
        painter.drawText(QRectF(x + 25, y + 2, 80, 16), Qt.AlignLeft | Qt.AlignVCenter, "Accuracy")


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 GESTURE ACCURACY WIDGET - SMALLER SIZE
# ═══════════════════════════════════════════════════════════════════════════════

class GestureAccuracyWidget(QWidget):
    """Horizontal bars - Compact size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ✅ FIXED: Smaller fixed size
        self.setFixedSize(280, 260)
        
        self.gesture_data = [
            ("FIST", 85, Neon.RED),
            ("PALM", 90, Neon.ORANGE),
            ("INDEX", 75, Neon.CYAN),
            ("PEACE", 70, Neon.GREEN),
            ("THREE", 65, Neon.PURPLE),
            ("THUMB", 80, Neon.YELLOW),
            ("SHAKA", 60, Neon.MAGENTA),
        ]
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(5, 10, 20))
        painter.setPen(QPen(QColor(Neon.MAGENTA), 2))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        
        painter.setPen(QColor(Neon.MAGENTA))
        font = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 5, self.width(), 22), Qt.AlignCenter, 
                        "◈ GESTURE ACCURACY")
        
        self.draw_bars(painter)
    
    def draw_bars(self, painter):
        start_y = 32
        bar_height = 28
        spacing = 4
        left_margin = 60
        right_margin = 15
        
        max_width = self.width() - left_margin - right_margin
        
        for i, (name, accuracy, color) in enumerate(self.gesture_data):
            y = start_y + i * (bar_height + spacing)
            
            painter.setPen(QColor(Neon.TEXT))
            font = QFont("Consolas", 8, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(5, y, 52, bar_height), Qt.AlignRight | Qt.AlignVCenter, name)
            
            painter.setBrush(QBrush(QColor(30, 40, 60)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(left_margin, y, max_width, bar_height, 4, 4)
            
            bar_width = int((accuracy / 100.0) * max_width)
            gradient = QLinearGradient(left_margin, 0, left_margin + bar_width, 0)
            
            r, g, b = self.hex_rgb(color)
            gradient.setColorAt(0, QColor(r, g, b, 180))
            gradient.setColorAt(1, QColor(r, g, b, 255))
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(left_margin, y, bar_width, bar_height, 4, 4)
            
            painter.setPen(QColor(color))
            font = QFont("Consolas", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(left_margin, y, bar_width, bar_height), 
                           Qt.AlignCenter, f"{accuracy}%")
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 AI TRAINER ANALYSIS PAGE - FULLY FIXED
# ═══════════════════════════════════════════════════════════════════════════════

class AITrainerPage(QWidget):
    """✅ FULLY FIXED: All content visible"""
    
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("◈ AI TRAINER ANALYSIS")
        self.setMinimumSize(1200, 800)
        
        self.training_data = self.load_training_data()
        
        self.setup_ui()
        self.apply_theme()
        
        print("📊 AI Trainer Analysis Page - FULLY FIXED")
    
    def load_training_data(self):
        data_file = "adaptive_training_data.json"
        
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_sessions": 0,
            "total_attempts": 0,
            "total_success": 0,
            "best_streak": 0,
            "highest_level": 1,
            "total_time": 0,
            "sessions": [],
            "gesture_stats": {}
        }
    
    def setup_ui(self):
        """✅ FIXED: Complete UI setup"""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        
        # Header
        header = self.build_header()
        main.addWidget(header)
        
        # ═══════════════════════════════════════════════════════════════
        # ✅ SCROLL AREA - PROPERLY CONFIGURED
        # ═══════════════════════════════════════════════════════════════
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setObjectName("scrollArea")
        
        # ✅ Content widget
        content = QWidget()
        content.setObjectName("scrollContent")
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 80)
        content_layout.setSpacing(15)
        
        # Overview stats
        overview = self.build_overview_stats()
        content_layout.addWidget(overview)
        
        # Charts
        charts = self.build_charts_row()
        content_layout.addWidget(charts)
        
        # Detailed stats
        detailed = self.build_detailed_stats()
        content_layout.addWidget(detailed)
        
        # AI recommendations
        ai_rec = self.build_ai_recommendations()
        content_layout.addWidget(ai_rec)
        
        # Session history
        history = self.build_session_history()
        content_layout.addWidget(history)
        
        # Extra spacing
        content_layout.addSpacing(60)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main.addWidget(scroll, 1)
        # ═══════════════════════════════════════════════════════════════
        
        # Footer
        footer = self.build_footer()
        main.addWidget(footer)
    
    def build_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        back_btn = QPushButton("◄ BACK")
        back_btn.setFixedSize(90, 40)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFont(QFont("Consolas", 10, QFont.Bold))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        logo = QLabel("📊")
        logo.setFont(QFont("Segoe UI Emoji", 24))
        logo.setFixedWidth(40)
        layout.addWidget(logo)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        
        title = QLabel("AI TRAINER ANALYSIS")
        title.setFont(QFont("Consolas", 18, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.CYAN};")
        title_box.addWidget(title)
        
        subtitle = QLabel("PERFORMANCE ANALYTICS")
        subtitle.setFont(QFont("Consolas", 8))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
        
        layout.addLayout(title_box)
        layout.addStretch()
        
        refresh_btn = QPushButton("⟲ REFRESH")
        refresh_btn.setFixedSize(100, 40)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFont(QFont("Consolas", 10, QFont.Bold))
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        return header
    
    # ═══════════════════════════════════════════════════════════════════════════
    # OVERVIEW STATS - RESPONSIVE GRID
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_overview_stats(self):
        """✅ FIXED: 6 cards in responsive grid"""
        container = QFrame()
        container.setObjectName("overviewStats")
        
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        total_sessions = self.training_data.get("total_sessions", 0)
        total_attempts = self.training_data.get("total_attempts", 0)
        total_success = self.training_data.get("total_success", 0)
        accuracy = (total_success / total_attempts * 100) if total_attempts > 0 else 0
        best_streak = self.training_data.get("best_streak", 0)
        highest_level = self.training_data.get("highest_level", 1)
        total_time = self.training_data.get("total_time", 0)
        
        stats = [
            ("SESSIONS", str(total_sessions), Neon.CYAN, "📅"),
            ("ATTEMPTS", str(total_attempts), Neon.ORANGE, "🎯"),
            ("ACCURACY", f"{accuracy:.1f}%", Neon.GREEN, "✓"),
            ("STREAK", str(best_streak), Neon.YELLOW, "🔥"),
            ("LEVEL", str(highest_level), Neon.MAGENTA, "⭐"),
            ("TIME", self.format_time(total_time), Neon.PURPLE, "⏱"),
        ]
        
        for i, (label, value, color, icon) in enumerate(stats):
            card = self.make_stat_card(label, value, color, icon)
            row = i // 6  # All in one row
            col = i % 6
            layout.addWidget(card, row, col)
        
        return container
    
    def make_stat_card(self, label, value, color, icon):
        """✅ FIXED: Smaller compact cards"""
        card = QFrame()
        card.setFixedHeight(90)
        card.setMinimumWidth(150)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setObjectName("statCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        
        # Icon + Label
        top_row = QHBoxLayout()
        top_row.setSpacing(5)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
        top_row.addWidget(icon_lbl)
        
        label_lbl = QLabel(label)
        label_lbl.setFont(QFont("Consolas", 8, QFont.Bold))
        label_lbl.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        top_row.addWidget(label_lbl)
        top_row.addStretch()
        
        layout.addLayout(top_row)
        
        # Value
        value_lbl = QLabel(value)
        value_lbl.setFont(QFont("Consolas", 22, QFont.Bold))
        value_lbl.setStyleSheet(f"color: {color};")
        value_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_lbl)
        
        r, g, b = self.hex_rgb(color)
        card.setStyleSheet(f"""
            #statCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({r}, {g}, {b}, 0.15),
                    stop:1 rgba(5, 10, 20, 0.9)
                );
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)
        
        return card
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CHARTS ROW - RESPONSIVE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_charts_row(self):
        """✅ FIXED: Responsive charts row"""
        container = QFrame()
        container.setMinimumHeight(260)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        progress_chart = ProgressChartWidget()
        layout.addWidget(progress_chart, 1)  # Stretch factor
        
        gesture_chart = GestureAccuracyWidget()
        layout.addWidget(gesture_chart, 0)  # Fixed size
        
        return container
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DETAILED STATS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_detailed_stats(self):
        container = QFrame()
        container.setObjectName("detailedStats")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        title = QLabel("◈ DETAILED STATISTICS")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.YELLOW};")
        layout.addWidget(title)
        
        # ✅ 3 columns grid
        grid = QGridLayout()
        grid.setSpacing(10)
        
        stats = [
            ("Avg Duration", self.get_avg_session_duration()),
            ("Avg Accuracy", self.get_avg_accuracy()),
            ("Success Rate", self.get_success_rate()),
            ("Gestures", str(len(self.training_data.get("gesture_stats", {})))),
            ("Best Gesture", self.get_best_gesture()),
            ("Needs Work", self.get_worst_gesture()),
        ]
        
        for i, (label, value) in enumerate(stats):
            row = i // 3
            col = i % 3
            stat_box = self.make_detail_stat(label, value)
            grid.addWidget(stat_box, row, col)
        
        layout.addLayout(grid)
        
        container.setStyleSheet(f"""
            #detailedStats {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.YELLOW};
                border-radius: 12px;
            }}
        """)
        
        return container
    
    def make_detail_stat(self, label, value):
        box = QFrame()
        box.setMinimumHeight(50)
        box.setObjectName("detailBox")
        
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        
        lbl = QLabel(label)
        lbl.setFont(QFont("Consolas", 9))
        lbl.setStyleSheet(f"color: {Neon.TEXT};")
        layout.addWidget(lbl)
        
        val = QLabel(value)
        val.setFont(QFont("Consolas", 13, QFont.Bold))
        val.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(val)
        
        box.setStyleSheet(f"""
            #detailBox {{
                background: rgba(0, 245, 255, 0.08);
                border: 1px solid rgba(0, 245, 255, 0.3);
                border-radius: 8px;
            }}
        """)
        
        return box
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AI RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_ai_recommendations(self):
        container = QFrame()
        container.setObjectName("aiRec")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        title = QLabel("🤖 AI RECOMMENDATIONS")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(title)
        
        recommendations = self.generate_recommendations()
        
        for rec in recommendations:
            rec_label = QLabel(f"• {rec}")
            rec_label.setFont(QFont("Consolas", 10))
            rec_label.setStyleSheet(f"color: {Neon.TEXT};")
            rec_label.setWordWrap(True)
            layout.addWidget(rec_label)
        
        container.setStyleSheet(f"""
            #aiRec {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.GREEN};
                border-radius: 12px;
            }}
        """)
        
        return container
    
    def generate_recommendations(self):
        recs = []
        
        accuracy = self.get_avg_accuracy_value()
        
        if accuracy < 60:
            recs.append("Focus on basic gestures (FIST, PALM) first")
            recs.append("Practice in better lighting")
        elif accuracy < 75:
            recs.append("Good progress! Increase consistency")
            recs.append("Practice difficult gestures more")
        else:
            recs.append("Excellent! Try higher levels")
            recs.append("Practice complex sequences")
        
        worst = self.get_worst_gesture()
        if worst and worst != "N/A":
            recs.append(f"Improve '{worst}' gesture")
        
        recs.append("Take breaks to avoid fatigue")
        
        return recs
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION HISTORY
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_session_history(self):
        container = QFrame()
        container.setObjectName("sessionHistory")
        container.setMinimumHeight(220)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        title = QLabel("◈ RECENT SESSIONS")
        title.setFont(QFont("Consolas", 11, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.PURPLE};")
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Date", "Duration", "Attempts", "Success", "Accuracy", "Level"])
        
        sessions = self.training_data.get("sessions", [])[-8:]
        table.setRowCount(len(sessions))
        
        for i, session in enumerate(sessions):
            table.setItem(i, 0, QTableWidgetItem(session.get("date", "N/A")))
            table.setItem(i, 1, QTableWidgetItem(self.format_time(session.get("duration", 0))))
            table.setItem(i, 2, QTableWidgetItem(str(session.get("attempts", 0))))
            table.setItem(i, 3, QTableWidgetItem(str(session.get("success", 0))))
            accuracy = session.get("accuracy", 0)
            table.setItem(i, 4, QTableWidgetItem(f"{accuracy:.1f}%"))
            table.setItem(i, 5, QTableWidgetItem(str(session.get("level", 1))))
        
        table.setObjectName("historyTable")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setMaximumHeight(180)
        
        table.setStyleSheet("""
            #historyTable {
                background: rgba(5, 10, 20, 0.9);
                border: 1px solid rgba(191, 0, 255, 0.3);
                border-radius: 6px;
                color: #e0e8ff;
                gridline-color: rgba(90, 112, 144, 0.3);
                font-size: 10px;
            }
            #historyTable::item {
                padding: 5px;
            }
            #historyTable::item:selected {
                background: rgba(191, 0, 255, 0.3);
            }
            QHeaderView::section {
                background: rgba(191, 0, 255, 0.2);
                color: #bf00ff;
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        
        layout.addWidget(table)
        
        container.setStyleSheet(f"""
            #sessionHistory {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.PURPLE};
                border-radius: 12px;
            }}
        """)
        
        return container
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_footer(self):
        footer = QFrame()
        footer.setFixedHeight(40)
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 0, 20, 0)
        
        info = QLabel("📊 Analysis updated in real-time")
        info.setFont(QFont("Consolas", 9))
        info.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(info)
        
        layout.addStretch()
        
        version = QLabel("AI TRAINER v2.0")
        version.setFont(QFont("Consolas", 9))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
        
        return footer
    
    # ═══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"
    
    def get_avg_session_duration(self):
        sessions = self.training_data.get("sessions", [])
        if not sessions:
            return "N/A"
        total = sum(s.get("duration", 0) for s in sessions)
        avg = total / len(sessions)
        return self.format_time(avg)
    
    def get_avg_accuracy(self):
        val = self.get_avg_accuracy_value()
        return f"{val:.1f}%"
    
    def get_avg_accuracy_value(self):
        sessions = self.training_data.get("sessions", [])
        if not sessions:
            return 0
        total = sum(s.get("accuracy", 0) for s in sessions)
        return total / len(sessions)
    
    def get_success_rate(self):
        total = self.training_data.get("total_attempts", 0)
        success = self.training_data.get("total_success", 0)
        if total == 0:
            return "N/A"
        rate = (success / total) * 100
        return f"{rate:.1f}%"
    
    def get_best_gesture(self):
        gesture_stats = self.training_data.get("gesture_stats", {})
        if not gesture_stats:
            return "N/A"
        best = max(gesture_stats.items(), key=lambda x: x[1].get("accuracy", 0))
        return f"{best[0]}"
    
    def get_worst_gesture(self):
        gesture_stats = self.training_data.get("gesture_stats", {})
        if not gesture_stats:
            return "N/A"
        worst = min(gesture_stats.items(), key=lambda x: x[1].get("accuracy", 0))
        return f"{worst[0]}"
    
    def refresh_data(self):
        self.training_data = self.load_training_data()
        layout = self.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.setup_ui()
        print("🔄 Data refreshed")
    
    def hex_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # THEME - COMPLETE
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
                background: rgba(0, 30, 60, 0.5);
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.CYAN},
                    stop:1 {Neon.PURPLE}
                );
                border-radius: 5px;
                min-height: 40px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {Neon.CYAN};
            }}
            
            QScrollBar:horizontal {{
                background: rgba(0, 30, 60, 0.5);
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.CYAN},
                    stop:1 {Neon.PURPLE}
                );
                border-radius: 5px;
                min-width: 40px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {Neon.CYAN};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                height: 0;
                width: 0;
            }}
            
            #header {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 255, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-bottom: 2px solid {Neon.CYAN};
            }}
            
            #backBtn {{
                background: rgba(0, 245, 255, 0.15);
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 10px;
            }}
            #backBtn:hover {{
                background: rgba(0, 245, 255, 0.35);
            }}
            
            #refreshBtn {{
                background: rgba(0, 255, 159, 0.15);
                color: {Neon.GREEN};
                border: 2px solid {Neon.GREEN};
                border-radius: 10px;
            }}
            #refreshBtn:hover {{
                background: rgba(0, 255, 159, 0.35);
            }}
            
            #footer {{
                background: qlineargradient(
                    x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(0, 245, 255, 0.15),
                    stop:1 rgba(0, 0, 0, 0.9)
                );
                border-top: 2px solid {Neon.CYAN};
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    window = AITrainerPage()
    window.showMaximized()
    
    sys.exit(app.exec())
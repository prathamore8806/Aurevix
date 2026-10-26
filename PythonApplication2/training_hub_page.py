"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    AUREVIX NEURAL TRAINING HUB                               ║
║                   🌟 TRAINING MODE SELECTION SCREEN 🌟                        ║
║                         Version 1.1 - 3 CARDS                                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QGraphicsDropShadowEffect,
    QStackedWidget, QApplication, QMessageBox
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve, 
    Property, QTimer
)
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPalette


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
# 🎴 ANIMATED TRAINING MODE CARD
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingModeCard(QPushButton):
    """Interactive card for each training mode"""
    
    def __init__(self, icon, title, description, color, parent=None):
        super().__init__(parent)
        self.icon_text = icon
        self.title_text = title
        self.description_text = description
        self.card_color = color
        self._glow_intensity = 0.0
        self._scale = 1.0
        
        self.setFixedSize(320, 280)
        self.setCursor(Qt.PointingHandCursor)
        self.setup_ui()
        self.setup_animations()
        self.apply_style()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 30, 25, 25)
        layout.setSpacing(12)
        
        # Icon
        icon_container = QFrame()
        icon_container.setFixedSize(100, 100)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel(self.icon_text)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 52))
        self.icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        layout.addSpacing(8)
        
        # Title
        self.title_label = QLabel(self.title_text)
        self.title_label.setFont(QFont("Consolas", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"color: {self.card_color}; background: transparent;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Separator
        line = QFrame()
        line.setFixedHeight(2)
        r, g, b = self.hex_to_rgb(self.card_color)
        line.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba({r},{g},{b},0.8),
                stop:0.7 rgba({r},{g},{b},0.8), stop:1 transparent);
        """)
        layout.addWidget(line)
        layout.addSpacing(5)
        
        # Description
        self.desc_label = QLabel(self.description_text)
        self.desc_label.setFont(QFont("Consolas", 10))
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet(f"color: {Neon.TEXT}; background: transparent;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumHeight(40)
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
        
        # Click hint
        self.click_hint = QLabel("▶ CLICK TO START")
        self.click_hint.setFont(QFont("Consolas", 8, QFont.Bold))
        self.click_hint.setAlignment(Qt.AlignCenter)
        self.click_hint.setStyleSheet(f"color: {Neon.TEXT_DIM}; background: transparent;")
        self.click_hint.setVisible(False)
        layout.addWidget(self.click_hint)
        
        # Glow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(QColor(self.card_color))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
    
    def setup_animations(self):
        self.glow_anim = QPropertyAnimation(self, b"glow_intensity")
        self.glow_anim.setDuration(300)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_anim = QPropertyAnimation(self, b"card_scale")
        self.scale_anim.setDuration(150)
        self.scale_anim.setEasingCurve(QEasingCurve.OutCubic)
    
    def get_glow_intensity(self):
        return self._glow_intensity
    
    def set_glow_intensity(self, value):
        self._glow_intensity = value
        self.shadow.setBlurRadius(int(value * 50))
        self.update()
    
    glow_intensity = Property(float, get_glow_intensity, set_glow_intensity)
    
    def get_card_scale(self):
        return self._scale
    
    def set_card_scale(self, value):
        self._scale = value
        self.update()
    
    card_scale = Property(float, get_card_scale, set_card_scale)
    
    def enterEvent(self, event):
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(1.0)
        self.glow_anim.start()
        self.click_hint.setVisible(True)
        self.click_hint.setStyleSheet(f"color: {self.card_color}; background: transparent;")
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.glow_anim.stop()
        self.glow_anim.setStartValue(self._glow_intensity)
        self.glow_anim.setEndValue(0.0)
        self.glow_anim.start()
        self.click_hint.setVisible(False)
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        self.scale_anim.stop()
        self.scale_anim.setStartValue(1.0)
        self.scale_anim.setEndValue(0.95)
        self.scale_anim.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.scale_anim.stop()
        self.scale_anim.setStartValue(0.95)
        self.scale_anim.setEndValue(1.0)
        self.scale_anim.start()
        super().mouseReleaseEvent(event)
    
    def apply_style(self):
        r, g, b = self.hex_to_rgb(self.card_color)
        self.setStyleSheet(f"""
            TrainingModeCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(8,15,30,0.95), stop:0.5 rgba(5,10,25,0.98),
                    stop:1 rgba(3,8,20,0.95));
                border: 2px solid rgba({r},{g},{b},0.4);
                border-radius: 20px;
            }}
            TrainingModeCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba({r},{g},{b},0.2), stop:0.5 rgba({r},{g},{b},0.1),
                    stop:1 rgba(5,10,25,0.95));
                border: 3px solid {self.card_color};
            }}
            TrainingModeCard:pressed {{
                background: rgba({r},{g},{b},0.3);
            }}
        """)
    
    def hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════════════════════
# 🎮 TRAINING HUB PAGE - 3 CARDS
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingHubPage(QWidget):
    mode_closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("◈ AUREVIX NEURAL TRAINING HUB")
        self.setMinimumSize(1200, 800)
        
        self.shared_tracker = None
        self._init_shared_tracker()
        
        self.current_mode_widget = None
        self.stacked_widget = None
        
        self.setup_ui()
        self.apply_theme()
    
    def _init_shared_tracker(self):
        try:
            from training_tracker import TrainingGestureTracker
            try:
                import config
                camera_idx = getattr(config, 'camera_index', 0)
            except ImportError:
                camera_idx = 0
            
            self.shared_tracker = TrainingGestureTracker(camera_index=camera_idx)
            self.shared_tracker.start()
            print(f"✅ Shared tracker started (camera {camera_idx})")
        except Exception as e:
            print(f"⚠️ Tracker not available: {e}")
            self.shared_tracker = None
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        
        self.hub_page = QWidget()
        self.setup_hub_page()
        self.stacked_widget.addWidget(self.hub_page)
        
        main_layout.addWidget(self.stacked_widget)
    
    def setup_hub_page(self):
        layout = QVBoxLayout(self.hub_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = self.build_header()
        layout.addWidget(header)
        
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(50, 40, 50, 40)
        content_layout.setSpacing(30)
        
        title_section = self.build_title_section()
        content_layout.addWidget(title_section)
        
        # ✅ 3 CARDS IN HORIZONTAL ROW
        cards_container = self.build_cards_row()
        content_layout.addWidget(cards_container, 1)
        
        content_layout.addSpacing(20)
        layout.addWidget(content_container, 1)
        
        footer = self.build_footer()
        layout.addWidget(footer)
    
    def build_header(self):
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(20)
        
        self.back_btn = QPushButton("◄  BACK")
        self.back_btn.setFixedSize(120, 45)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        self.back_btn.setObjectName("backBtn")
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)
        
        layout.addSpacing(20)
        
        logo = QLabel("◈")
        logo.setFont(QFont("Segoe UI", 32))
        logo.setStyleSheet(f"color: {Neon.CYAN};")
        layout.addWidget(logo)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        
        title = QLabel("NEURAL TRAINING")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.CYAN};")
        title_box.addWidget(title)
        
        subtitle = QLabel("HOLOGRAPHIC TRAINING SYSTEM")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
        
        layout.addLayout(title_box)
        layout.addStretch()
        
        # Status
        status_box = QFrame()
        status_box.setFixedSize(150, 45)
        status_layout = QHBoxLayout(status_box)
        status_layout.setContentsMargins(15, 5, 15, 5)
        
        tracker_ok = self.shared_tracker is not None
        status_color = Neon.GREEN if tracker_ok else Neon.ORANGE
        
        status_dot = QLabel("●")
        status_dot.setFont(QFont("Consolas", 14))
        status_dot.setStyleSheet(f"color: {status_color};")
        status_layout.addWidget(status_dot)
        
        status_text = QLabel("SYSTEM ONLINE" if tracker_ok else "NO CAMERA")
        status_text.setFont(QFont("Consolas", 9, QFont.Bold))
        status_text.setStyleSheet(f"color: {status_color};")
        status_layout.addWidget(status_text)
        
        status_box.setStyleSheet(f"""
            QFrame {{
                background: rgba(0,255,159,0.1);
                border: 1px solid {status_color};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(status_box)
        
        return header
    
    def build_title_section(self):
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("🎯 Select a Training Mode")
        title.setFont(QFont("Consolas", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {Neon.YELLOW};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(240,255,0,0), stop:0.3 rgba(240,255,0,0.1),
                stop:0.7 rgba(240,255,0,0.1), stop:1 rgba(240,255,0,0));
            padding: 15px;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("⟨ Choose your path to master gesture control ⟩")
        subtitle.setFont(QFont("Consolas", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(subtitle)
        
        return section
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📌 3 CARDS IN HORIZONTAL ROW
    # ═══════════════════════════════════════════════════════════════════════════
    
    def build_cards_row(self):
        """✅ Build 3 cards in a horizontal row"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Horizontal layout for 3 cards
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setSpacing(50)
        cards_layout.setContentsMargins(40, 30, 40, 30)
        
        # ═══ CARD 1: GESTURE ANALYTICS ═══
        card1 = TrainingModeCard(
            icon="📊",
            title="Gesture Analytics",
            description="Analyze gesture accuracy with\nheatmaps and performance radar",
            color=Neon.GREEN
        )
        card1.clicked.connect(self.open_gesture_analytics)
        cards_layout.addWidget(card1, alignment=Qt.AlignCenter)
        
        # ═══ CARD 2: REFLEX CHALLENGE ═══
        card2 = TrainingModeCard(
            icon="⚡",
            title="Reflex Challenge",
            description="Test your speed and gesture\nmemory with timed challenges",
            color=Neon.MAGENTA
        )
        card2.clicked.connect(self.open_reflex_challenge)
        cards_layout.addWidget(card2, alignment=Qt.AlignCenter)
        
        # ═══ CARD 3: ADAPTIVE TRAINER ═══
        card3 = TrainingModeCard(
            icon="🤖",
            title="Adaptive Trainer",
            description="AI adjusts difficulty based\non your performance level",
            color=Neon.ORANGE
        )
        card3.clicked.connect(self.open_adaptive_trainer)
        cards_layout.addWidget(card3, alignment=Qt.AlignCenter)
        
        container_layout.addWidget(cards_widget, 1, Qt.AlignCenter)
        
        return container
    
    def build_footer(self):
        footer = QFrame()
        footer.setFixedHeight(55)
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 0, 30, 0)
        
        left_status = QLabel("◉ TRAINING HUB READY")
        left_status.setFont(QFont("Consolas", 10, QFont.Bold))
        left_status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(left_status)
        
        layout.addStretch()
        
        hint = QLabel("⟨ SELECT A MODE TO BEGIN TRAINING ⟩")
        hint.setFont(QFont("Consolas", 10))
        hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(hint)
        
        layout.addStretch()
        
        version = QLabel("AUREVIX v1.1 // 3 TRAINING MODES")
        version.setFont(QFont("Consolas", 9))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
        
        return footer
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎮 MODE LAUNCHERS - ONLY 3 MODES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def open_gesture_analytics(self):
        print("📊 Opening Gesture Analytics...")
        try:
            from training_modes.gesture_analytics import GestureAnalyticsMode
            self.current_mode_widget = GestureAnalyticsMode(
                parent=self, tracker=self.shared_tracker
            )
            self.current_mode_widget.mode_closed.connect(self.return_to_hub)
            self.current_mode_widget.showMaximized()
            self.hide()
        except ImportError as e:
            self.show_error_message("Gesture Analytics", str(e))
    
    def open_reflex_challenge(self):
        print("⚡ Opening Reflex Challenge...")
        try:
            from training_modes.reflex_challenge import ReflexChallengeMode
            self.current_mode_widget = ReflexChallengeMode(
                parent=self, tracker=self.shared_tracker
            )
            self.current_mode_widget.mode_closed.connect(self.return_to_hub)
            self.current_mode_widget.showMaximized()
            self.hide()
        except ImportError as e:
            self.show_error_message("Reflex Challenge", str(e))
    
    def open_adaptive_trainer(self):
        print("🤖 Opening Adaptive Trainer...")
        try:
            from training_modes.adaptive_trainer import AdaptiveTrainerMode
            self.current_mode_widget = AdaptiveTrainerMode(
                parent=self, tracker=self.shared_tracker
            )
            self.current_mode_widget.mode_closed.connect(self.return_to_hub)
            self.current_mode_widget.showMaximized()
            self.hide()
        except ImportError as e:
            self.show_error_message("Adaptive Trainer", str(e))
    
    def show_error_message(self, mode_name, error):
        print(f"❌ {mode_name}: {error}")
        QMessageBox.warning(
            self, f"⚠️ {mode_name} Not Available",
            f"Could not load {mode_name}.\n\nError: {error}",
            QMessageBox.Ok
        )
    
    def return_to_hub(self):
        print("↩️ Returning to Hub...")
        if self.current_mode_widget:
            if hasattr(self.current_mode_widget, 'cleanup'):
                try:
                    self.current_mode_widget.cleanup()
                except Exception as e:
                    print(f"  ⚠️ Cleanup error: {e}")
            self.current_mode_widget.close()
            self.current_mode_widget.deleteLater()
            self.current_mode_widget = None
        
        self.show()
        self.showMaximized()
        print("✅ Returned to hub")
    
    def go_back(self):
        print("◄ Returning to Dashboard...")
        if self.current_mode_widget:
            if hasattr(self.current_mode_widget, 'cleanup'):
                try:
                    self.current_mode_widget.cleanup()
                except:
                    pass
            self.current_mode_widget.close()
            self.current_mode_widget.deleteLater()
            self.current_mode_widget = None
        
        self.mode_closed.emit()
    
    def apply_theme(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000510, stop:0.3 #050a18,
                    stop:0.7 #030815, stop:1 #0a1225);
                color: {Neon.TEXT};
                font-family: 'Consolas', monospace;
            }}
            #header {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0,245,255,0.15), stop:0.5 rgba(0,245,255,0.05),
                    stop:1 rgba(0,0,0,0.9));
                border-bottom: 3px solid {Neon.CYAN};
            }}
            #backBtn {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0,245,255,0.2), stop:1 rgba(0,245,255,0.1));
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 12px;
            }}
            #backBtn:hover {{
                background: rgba(0,245,255,0.35);
                border: 2px solid {Neon.WHITE};
            }}
            #contentContainer {{ background: transparent; }}
            #footer {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(255,0,255,0.15), stop:0.5 rgba(255,0,255,0.05),
                    stop:1 rgba(0,0,0,0.9));
                border-top: 3px solid {Neon.MAGENTA};
            }}
        """)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧹 CLEANUP - SINGLE METHOD
    # ═══════════════════════════════════════════════════════════════════════════
    
    def cleanup(self):
        print("🧹 Training Hub cleanup...")
        
        if self.current_mode_widget:
            if hasattr(self.current_mode_widget, 'cleanup'):
                try:
                    self.current_mode_widget.cleanup()
                except:
                    pass
            self.current_mode_widget.close()
            self.current_mode_widget.deleteLater()
            self.current_mode_widget = None
        
        if self.shared_tracker:
            try:
                self.shared_tracker.stop()
                print("  📷 Tracker stopped")
            except:
                pass
            self.shared_tracker = None
        
        print("✅ Cleaned up")
    
    def closeEvent(self, event):
        self.cleanup()
        event.accept()


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(5, 10, 21))
    palette.setColor(QPalette.WindowText, QColor(224, 232, 255))
    app.setPalette(palette)
    
    window = TrainingHubPage()
    window.showMaximized()
    
    sys.exit(app.exec())
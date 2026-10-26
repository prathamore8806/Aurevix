# futuristic_dashboard.py - WITH PRESENTATION MODE BUTTON

import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QComboBox, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPixmap, QImage, QColor, QLinearGradient, QPainter, QBrush, QPen

import config
import mode_manager
from fps_graph import FPSGraphWidget
from ai_status_indicator import AIStatusIndicator
from glass_card import GlassCard
from mode_card import ModeCard
from gesture_mapping_row import GestureMappingRow
from profile_badge import ProfileBadge

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════════════
# SMALL ICON BUTTON (For Camera Controls)
# ══════════════════════════════════════════════════════════════════════════════
class SmallIconButton(QPushButton):
    """Small icon button for camera control row."""
    
    def __init__(self, icon, tooltip, color="#00d4ff", parent=None):
        super().__init__(icon, parent)
        self._color = color
        
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgba({self._hex_to_rgb(color)}, 0.15);
                border: 1px solid rgba({self._hex_to_rgb(color)}, 0.4);
                border-radius: 10px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: rgba({self._hex_to_rgb(color)}, 0.3);
                border: 1px solid rgba({self._hex_to_rgb(color)}, 0.7);
            }}
            QPushButton:disabled {{
                background: rgba(50,50,50,0.1);
                border: 1px solid rgba(100,100,100,0.2);
                color: #334455;
            }}
        """)
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r},{g},{b}"


# ══════════════════════════════════════════════════════════════════════════════
# 🔥 TRAINING MODE BUTTON - GAMING STYLE WITH RGB ANIMATED BORDER
# ══════════════════════════════════════════════════════════════════════════════
class TrainingModeButton(QPushButton):
    """
    🎯 Gaming Style Training Mode Button with:
    - RGB animated border
    - Glowing effect
    - Cyber/Gaming aesthetics
    - Hover animations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._hue = 0  # For RGB cycling
        self._glow_intensity = 20
        self._is_hovered = False
        
        self.setFixedSize(320, 65)
        self.setCursor(Qt.PointingHandCursor)
        
        # Glow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setColor(QColor(0, 255, 255, 180))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)
        
        # RGB Animation timer
        self._rgb_timer = QTimer(self)
        self._rgb_timer.timeout.connect(self._animate_rgb)
        self._rgb_timer.start(30)  # Fast RGB cycling
        
        self._update_style()
    
    def _animate_rgb(self):
        """Animate RGB border color cycling"""
        self._hue = (self._hue + 2) % 360
        
        # Create RGB color from hue
        color = QColor.fromHsv(self._hue, 255, 255)
        
        # Update glow color
        if self._is_hovered:
            self._shadow.setBlurRadius(35)
            self._shadow.setColor(QColor(color.red(), color.green(), color.blue(), 220))
        else:
            self._shadow.setBlurRadius(20)
            self._shadow.setColor(QColor(color.red(), color.green(), color.blue(), 150))
        
        self._update_style()
    
    def _update_style(self):
        """Update button style with current RGB color"""
        # Get current RGB color
        color = QColor.fromHsv(self._hue, 255, 255)
        r, g, b = color.red(), color.green(), color.blue()
        
        # Next color in spectrum (for gradient)
        next_color = QColor.fromHsv((self._hue + 60) % 360, 255, 255)
        r2, g2, b2 = next_color.red(), next_color.green(), next_color.blue()
        
        # Third color
        third_color = QColor.fromHsv((self._hue + 120) % 360, 255, 255)
        r3, g3, b3 = third_color.red(), third_color.green(), third_color.blue()
        
        hover_bg = "rgba(255,255,255,0.15)" if self._is_hovered else "rgba(0,0,0,0.6)"
        border_width = "3px" if self._is_hovered else "2px"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10, 10, 30, 0.9),
                    stop:0.5 rgba(20, 20, 50, 0.9),
                    stop:1 rgba(10, 10, 30, 0.9)
                );
                border: {border_width} solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgb({r}, {g}, {b}),
                    stop:0.33 rgb({r2}, {g2}, {b2}),
                    stop:0.66 rgb({r3}, {g3}, {b3}),
                    stop:1 rgb({r}, {g}, {b})
                );
                border-radius: 12px;
                color: #ffffff;
                font-size: 16px;
                font-weight: 900;
                font-family: 'Segoe UI', 'Arial Black', sans-serif;
                letter-spacing: 3px;
                padding: 12px 25px;
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({r}, {g}, {b}, 0.3),
                    stop:1 rgba({r2}, {g2}, {b2}, 0.3)
                );
            }}
        """)
    
    def setText(self, text):
        """Override to add gaming style arrows"""
        super().setText(f"▶▶  {text}  ◀◀")
    
    def enterEvent(self, event):
        self._is_hovered = True
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hovered = False
        super().leaveEvent(event)
    
    def showEvent(self, event):
        """Set initial text when shown"""
        if not self.text():
            self.setText("TRAINING MODE")
        super().showEvent(event)
    
    def cleanup(self):
        """Stop animations"""
        self._rgb_timer.stop()


# ══════════════════════════════════════════════════════════════════════════════
# 📽️ PRESENTATION MODE BUTTON - PURPLE GRADIENT STYLE
# ══════════════════════════════════════════════════════════════════════════════
class PresentationModeButton(QPushButton):
    """
    📽️ Presentation Mode Button with:
    - Purple/violet gradient
    - Glow effect
    - Professional aesthetics
    - Hover animations
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._is_hovered = False
        
        self.setFixedSize(320, 65)
        self.setCursor(Qt.PointingHandCursor)
        
        # Glow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(20)
        self._shadow.setColor(QColor(168, 85, 247, 180))
        self._shadow.setOffset(0, 0)
        self.setGraphicsEffect(self._shadow)
        
        self._update_style()
    
    def _update_style(self):
        """Update button style"""
        blur = "35" if self._is_hovered else "20"
        border_width = "3px" if self._is_hovered else "2px"
        
        self._shadow.setBlurRadius(int(blur))
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(139, 92, 246, 0.4),
                    stop:0.5 rgba(168, 85, 247, 0.5),
                    stop:1 rgba(139, 92, 246, 0.4)
                );
                border: {border_width} solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgb(139, 92, 246),
                    stop:0.5 rgb(168, 85, 247),
                    stop:1 rgb(139, 92, 246)
                );
                border-radius: 12px;
                color: #ffffff;
                font-size: 16px;
                font-weight: 900;
                font-family: 'Segoe UI', 'Arial Black', sans-serif;
                letter-spacing: 2px;
                padding: 12px 25px;
            }}
            QPushButton:pressed {{
                background: rgba(139, 92, 246, 0.7);
            }}
        """)
    
    def setText(self, text):
        """Override to add presentation style icon"""
        super().setText(f"📽️  {text}  📊")
    
    def enterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)
    
    def showEvent(self, event):
        """Set initial text when shown"""
        if not self.text():
            self.setText("PRESENTATION MODE")
        super().showEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
# FUTURISTIC DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class FuturisticDashboard(QWidget):
    """
    Main dashboard widget with:
    - Camera preview
    - Mode cards (Desktop, Gaming, Draw)
    - Training mode button
    - Presentation mode button (NEW!)
    - AI stats and status
    """
    
    # ═══════════════════════════════════════════════════════════════
    # 📡 SIGNALS
    # ═══════════════════════════════════════════════════════════════
    startTrackingRequested = Signal()
    stopTrackingRequested = Signal()
    modeChanged = Signal(str)
    mirrorChanged = Signal(bool)
    screenshotRequested = Signal()
    gamingPageRequested = Signal()          # 🎮 Gaming card clicked
    trainingModeRequested = Signal()        # 🎯 Training button clicked
    presentationModeRequested = Signal()    # 📽️ Presentation button clicked (NEW!)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracking_active = False
        self._last_frame = None
        self._build_ui()
        
        print("✅ FuturisticDashboard initialized with signals:")
        print("   - startTrackingRequested")
        print("   - stopTrackingRequested")
        print("   - modeChanged")
        print("   - mirrorChanged")
        print("   - screenshotRequested")
        print("   - gamingPageRequested (🎮 Gaming card → Gaming page)")
        print("   - trainingModeRequested (🎯 Training button → Training page)")
        print("   - presentationModeRequested (📽️ Presentation button → Presentation page)")
    
    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # ─────────────────────────────────────────────────────────────
        # CENTER PANEL
        # ─────────────────────────────────────────────────────────────
        center_panel = QVBoxLayout()
        center_panel.setSpacing(14)

        # ═══ CAMERA CARD ═══
        camera_card = GlassCard(border_color="#00d4ff")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(14, 14, 14, 14)
        camera_layout.setSpacing(8)

        cam_header = QHBoxLayout()
        cam_title = QLabel("📷 Live Camera")
        cam_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e0e8f0; background: transparent;")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()

        self.ai_status = AIStatusIndicator()
        cam_header.addWidget(self.ai_status)

        camera_layout.addLayout(cam_header)

        self.camera_preview = QLabel()
        self.camera_preview.setFixedSize(780, 450)
        self.camera_preview.setAlignment(Qt.AlignCenter)
        self.camera_preview.setStyleSheet("""
            background: rgba(0, 0, 0, 0.5); border: 2px dashed rgba(0, 212, 255, 0.15);
            border-radius: 12px; color: #445566; font-size: 14px;
        """)
        self.camera_preview.setText("📹 Camera Preview\nClick 'Start Tracking' to begin")
        camera_layout.addWidget(self.camera_preview, alignment=Qt.AlignCenter)

        # ═══ CAMERA CONTROLS WITH ICONS ═══
        cam_controls = QHBoxLayout()
        cam_controls.setSpacing(8)

        self.cam_selector = QComboBox()
        self.cam_selector.setFixedWidth(130)
        self.cam_selector.setStyleSheet("""
            QComboBox { background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.2);
                border-radius: 8px; padding: 4px 10px; color: #a0c0e0; font-size: 12px; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border: none; }
            QComboBox QAbstractItemView { background: #0a0a2a; border: 1px solid rgba(0,212,255,0.3);
                color: #c0d0e0; selection-background-color: rgba(0,212,255,0.2); }
        """)
        self._detect_cameras()
        cam_controls.addWidget(self.cam_selector)

        self.start_tracking_btn = QPushButton("▶  Start Tracking")
        self.start_tracking_btn.setCursor(Qt.PointingHandCursor)
        self.start_tracking_btn.setFixedHeight(36)
        self.start_tracking_btn.setStyleSheet("""
            QPushButton { background: rgba(0,212,255,0.12); border: 1px solid rgba(0,212,255,0.3);
                border-radius: 10px; color: #00d4ff; font-size: 13px; font-weight: 700; padding: 6px 20px; }
            QPushButton:hover { background: rgba(0,212,255,0.25); border: 1px solid rgba(0,212,255,0.5); }
        """)
        self.start_tracking_btn.clicked.connect(self.startTrackingRequested.emit)
        cam_controls.addWidget(self.start_tracking_btn)

        self.stop_tracking_btn = QPushButton("⏹  Stop")
        self.stop_tracking_btn.setCursor(Qt.PointingHandCursor)
        self.stop_tracking_btn.setFixedHeight(36)
        self.stop_tracking_btn.setEnabled(False)
        self.stop_tracking_btn.setStyleSheet("""
            QPushButton { background: rgba(255,82,82,0.12); border: 1px solid rgba(255,82,82,0.3);
                border-radius: 10px; color: #ff5252; font-size: 13px; font-weight: 700; padding: 6px 20px; }
            QPushButton:hover { background: rgba(255,82,82,0.25); border: 1px solid rgba(255,82,82,0.5); }
            QPushButton:disabled { color: #334455; border: 1px solid rgba(255,255,255,0.05); background: rgba(50,50,50,0.1); }
        """)
        self.stop_tracking_btn.clicked.connect(self.stopTrackingRequested.emit)
        cam_controls.addWidget(self.stop_tracking_btn)

        self.mirror_btn = QPushButton("🪞")
        self.mirror_btn.setCursor(Qt.PointingHandCursor)
        self.mirror_btn.setCheckable(True)
        self.mirror_btn.setChecked(getattr(config, 'mirror', False))
        self.mirror_btn.setFixedSize(36, 36)
        self.mirror_btn.setToolTip("Mirror")
        self.mirror_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px; font-size: 16px; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
            QPushButton:checked { background: rgba(0,212,255,0.15); border: 1px solid rgba(0,212,255,0.4); }
        """)
        self.mirror_btn.clicked.connect(lambda c: self.mirrorChanged.emit(c))
        cam_controls.addWidget(self.mirror_btn)

        # Screenshot Button
        self.screenshot_btn_cam = SmallIconButton("📸", "Screenshot", "#6366f1")
        self.screenshot_btn_cam.setEnabled(False)
        self.screenshot_btn_cam.clicked.connect(self.screenshotRequested.emit)
        cam_controls.addWidget(self.screenshot_btn_cam)

        # Volume Button
        self.volume_btn = SmallIconButton("🔊", "Volume Control", "#ff6b35")
        self.volume_btn.clicked.connect(self._handle_volume)
        cam_controls.addWidget(self.volume_btn)

        # Voice Button
        self.voice_btn = SmallIconButton("🎤", "Voice Control", "#ffc107")
        self.voice_btn.clicked.connect(self._handle_voice)
        cam_controls.addWidget(self.voice_btn)

        # Lock Button
        self.lock_btn = SmallIconButton("🔒", "Lock Screen", "#00e676")
        self.lock_btn.clicked.connect(self._handle_lock)
        cam_controls.addWidget(self.lock_btn)

        cam_controls.addStretch()

        self.cam_status_text = QLabel("⚫ Tracking Off")
        self.cam_status_text.setStyleSheet("color: #556677; font-size: 11px; background: transparent; font-weight: 600;")
        cam_controls.addWidget(self.cam_status_text)

        camera_layout.addLayout(cam_controls)
        center_panel.addWidget(camera_card)

        # ═══════════════════════════════════════════════════════════════
        # 🎮 MODE SELECTION
        # ═══════════════════════════════════════════════════════════════
        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)

        self.mode_cards = {}
        
        # Desktop Mode Card - Normal mode switch
        desktop_card = ModeCard("Desktop Mode", "🖥️", "Cursor & click", color="#00d4ff")
        desktop_card.selected.connect(self._on_desktop_card_clicked)
        self.mode_cards["DESKTOP"] = desktop_card
        mode_row.addWidget(desktop_card)

        # 🎮 Gaming Mode Card - OPENS GAMING PAGE!
        gaming_card = ModeCard("Gaming Mode", "🎮", "Click to play games", color="#ff6b35")
        gaming_card.selected.connect(self._on_gaming_card_clicked)
        self.mode_cards["GAMING"] = gaming_card
        mode_row.addWidget(gaming_card)

        # Draw Mode Card - Normal mode switch
        draw_card = ModeCard("Draw Mode", "✏️", "Drawing & annotation", color="#a855f7")
        draw_card.selected.connect(self._on_draw_card_clicked)
        self.mode_cards["DRAW"] = draw_card
        mode_row.addWidget(draw_card)

        center_panel.addLayout(mode_row)

        # ══════════════════════════════════════════════════════════════
        # 🎯 TRAINING MODE & 📽️ PRESENTATION MODE BUTTONS ROW
        # ══════════════════════════════════════════════════════════════
        special_modes_row = QHBoxLayout()
        special_modes_row.setSpacing(20)
        special_modes_row.setAlignment(Qt.AlignCenter)
        
        # 🎯 Training Mode Button
        self.training_btn = TrainingModeButton()
        self.training_btn.clicked.connect(self._handle_training_mode)
        special_modes_row.addWidget(self.training_btn)
        
        # 📽️ Presentation Mode Button (NEW!)
        self.presentation_btn = PresentationModeButton()
        self.presentation_btn.clicked.connect(self._handle_presentation_mode)
        special_modes_row.addWidget(self.presentation_btn)
        
        center_panel.addLayout(special_modes_row)

        top_row.addLayout(center_panel, 3)

        # ─────────────────────────────────────────────────────────────
        # RIGHT SIDEBAR
        # ─────────────────────────────────────────────────────────────
        right_sidebar = QVBoxLayout()
        right_sidebar.setSpacing(14)

        # ═══ GESTURE MAPPING ═══
        gm_card = GlassCard(border_color="#00e676")
        gm_layout = QVBoxLayout(gm_card)
        gm_layout.setContentsMargins(14, 14, 14, 14)
        gm_layout.setSpacing(8)
        
        gm_title = QLabel("🤌 Gesture Mapping")
        gm_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e0e8f0; background: transparent;")
        gm_layout.addWidget(gm_title)
        
        for icon, gesture, action, color in [
            ("☝️", "Index", "Cursor", "#00d4ff"),
            ("✌️", "Two Fingers", "Scroll", "#ff6b35"),
            ("✋", "Open Palm", "Double Click", "#a855f7"),
            ("🤙", "Shaka", "Play/Pause", "#00e676"),
        ]:
            gm_layout.addWidget(GestureMappingRow(icon, gesture, action, color))
        
        gm_layout.addStretch()
        right_sidebar.addWidget(gm_card)

        # ═══ MANAGE PROFILES ═══
        pr_card = GlassCard(border_color="#a855f7")
        pr_layout = QVBoxLayout(pr_card)
        pr_layout.setContentsMargins(14, 14, 14, 14)
        pr_layout.setSpacing(8)
        
        pr_title = QLabel("👤 Active Profiles")
        pr_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e0e8f0; background: transparent;")
        pr_layout.addWidget(pr_title)
        
        for name, icon, color, active in [
            ("Work Mode", "💼", "#00d4ff",True),
            ("Gaming Mode", "🎮", "#ff6b35", True),
            ("Presentation Mode", "📊", "#a855f7", True),
        ]:
            pr_layout.addWidget(ProfileBadge(name, icon, color, active))
        
        pr_layout.addStretch()
        right_sidebar.addWidget(pr_card)

        # ═══ REAL-TIME AI STATS ═══
        stats_card = GlassCard(border_color="#ff6b35")
        st_layout = QVBoxLayout(stats_card)
        st_layout.setContentsMargins(14, 14, 14, 14)
        st_layout.setSpacing(8)
        
        st_title = QLabel("📈 Real-Time AI Stats")
        st_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e0e8f0; background: transparent;")
        st_layout.addWidget(st_title)

        fps_label = QLabel("FPS (Last 60 Seconds)")
        fps_label.setStyleSheet("font-size: 12px; color: #7788aa; background: transparent;")
        st_layout.addWidget(fps_label)

        self.fps_graph = FPSGraphWidget()
        st_layout.addWidget(self.fps_graph)

        self.ai_stats_label = QLabel(
            "🔴 AI Engine: Stopped\n⚡ Latency: --\n🎯 Mode: DESKTOP\n🖐 Hands: 0"
        )
        self.ai_stats_label.setStyleSheet("font-size: 12px; color: #8899bb; line-height: 1.6; background: transparent;")
        st_layout.addWidget(self.ai_stats_label)
        
        st_layout.addStretch()
        right_sidebar.addWidget(stats_card)

        # ═══ AI STATUS ═══
        ai_status_card = GlassCard(border_color="#00e676")
        ai_status_layout = QVBoxLayout(ai_status_card)
        ai_status_layout.setContentsMargins(14, 14, 14, 14)
        ai_status_layout.setSpacing(8)
        
        ai_status_title = QLabel("🤖 AI Status")
        ai_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e0e8f0; background: transparent;")
        ai_status_layout.addWidget(ai_status_title)
        
        self.ai_condition_label = QLabel("⚫ Idle\nWaiting for activation...")
        self.ai_condition_label.setStyleSheet("font-size: 12px; color: #7788aa; background: transparent;")
        ai_status_layout.addWidget(self.ai_condition_label)
        
        ai_status_layout.addStretch()
        right_sidebar.addWidget(ai_status_card)

        right_sidebar.addStretch()
        top_row.addLayout(right_sidebar, 2)

        main_layout.addLayout(top_row)

        # ══════════════════════════════════════════════════════════════
        # BOTTOM STATUS BAR
        # ══════════════════════════════════════════════════════════════
        self.dashboard_status = QLabel("⚡ System Ready | Tracking: Off | Mode: Desktop")
        self.dashboard_status.setStyleSheet("""
            font-size: 12px; color: #556677; padding: 8px 14px;
            background: rgba(0,0,0,0.2); border-radius: 10px;
            border: 1px solid rgba(0,212,255,0.08);
        """)
        main_layout.addWidget(self.dashboard_status)
        main_layout.addStretch()

        scroll.setWidget(content)
        
        wrapper_layout = QVBoxLayout(self)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll)

    # ═══════════════════════════════════════════════════════════════
    # 🎮 MODE CARD HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    def _on_desktop_card_clicked(self):
        """Handle Desktop Mode card click - switches to desktop mode"""
        print("🖥️ Desktop Mode card clicked - Switching mode")
        self.modeChanged.emit("DESKTOP")
    
    def _on_gaming_card_clicked(self):
        """Handle Gaming Mode card click - OPENS GAMING PAGE!"""
        print("\n" + "="*50)
        print("🎮 GAMING MODE CARD CLICKED!")
        print("   Emitting gamingPageRequested signal...")
        print("   This will open gaming_mode_page.py")
        print("="*50 + "\n")
        self.gamingPageRequested.emit()
    
    def _on_draw_card_clicked(self):
        """Handle Draw Mode card click - switches to draw mode"""
        print("✏️ Draw Mode card clicked - Switching mode")
        self.modeChanged.emit("DRAW")

    # ═══════════════════════════════════════════════════════════════
    # 🎯 TRAINING MODE HANDLER
    # ═══════════════════════════════════════════════════════════════
    
    def _handle_training_mode(self):
        """Handle Training Mode button click - OPENS TRAINING PAGE!"""
        print("\n" + "="*50)
        print("🎯 TRAINING MODE BUTTON CLICKED!")
        print("   Emitting trainingModeRequested signal...")
        print("   This will open training_mode_page.py")
        print("="*50 + "\n")
        self.trainingModeRequested.emit()

    # ═══════════════════════════════════════════════════════════════
    # 📽️ PRESENTATION MODE HANDLER (NEW!)
    # ═══════════════════════════════════════════════════════════════
    
    def _handle_presentation_mode(self):
        """Handle Presentation Mode button click - OPENS PRESENTATION PAGE!"""
        print("\n" + "="*50)
        print("📽️ PRESENTATION MODE BUTTON CLICKED!")
        print("   Emitting presentationModeRequested signal...")
        print("   This will open presentation_mode_page.py")
        print("="*50 + "\n")
        self.presentationModeRequested.emit()

    # ═══════════════════════════════════════════════════════════════
    # OTHER HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    def _handle_volume(self):
        print("🔊 Volume Control clicked")

    def _handle_voice(self):
        print("🎤 Voice Control clicked")

    def _handle_lock(self):
        print("🔒 Lock Screen clicked")

    def _detect_cameras(self):
        """Show ALL camera options with connection status."""
        self.cam_selector.clear()
    
        if not CV2_AVAILABLE:
            self.cam_selector.addItem("⚠ OpenCV Missing")
            self.cam_selector.setEnabled(False)
            return

        # Show ALL 3 camera options
        for index in range(3):
            # Get name from config
            base_name = config.CAMERA_SOURCES.get(index, f"📷 Camera {index}")
        
            # Check if camera is connected
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if cap.isOpened() and cap.read()[0]:
                    name = f"{base_name} ✅"
                else:
                    name = f"{base_name} ❌"
                cap.release()
            except Exception:
                name = f"{base_name} ❌"
        
            self.cam_selector.addItem(name, index)

        # Set current selection based on config
        cfg_idx = getattr(config, 'camera_index', 0)
        if cfg_idx < self.cam_selector.count():
            self.cam_selector.setCurrentIndex(cfg_idx)

    # ═══════════════════════════════════════════════════════════════
    # STATE UPDATES
    # ═══════════════════════════════════════════════════════════════

    def set_tracking_active(self, active):
        """Update UI when tracking state changes"""
        self._tracking_active = active
        self.ai_status.set_active(active)
        
        if active:
            self.start_tracking_btn.setEnabled(False)
            self.start_tracking_btn.setText("✅ Running")
            self.stop_tracking_btn.setEnabled(True)
            self.screenshot_btn_cam.setEnabled(True)
            self.cam_selector.setEnabled(False)
            self.cam_status_text.setText("🟢 Tracking Active")
            self.cam_status_text.setStyleSheet("color: #00e676; font-size: 11px; background: transparent; font-weight: 600;")
            self.camera_preview.setStyleSheet("""
                background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 12px;
            """)
            self.ai_condition_label.setText("🟢 Active\nTracking smoothly...")
            self.ai_condition_label.setStyleSheet("font-size: 12px; color: #00e676; background: transparent;")
        else:
            self.start_tracking_btn.setEnabled(True)
            self.start_tracking_btn.setText("▶  Start Tracking")
            self.stop_tracking_btn.setEnabled(False)
            self.screenshot_btn_cam.setEnabled(False)
            self.cam_selector.setEnabled(True)
            self.cam_status_text.setText("⚫ Tracking Off")
            self.cam_status_text.setStyleSheet("color: #556677; font-size: 11px; background: transparent; font-weight: 600;")
            self.camera_preview.clear()
            self.camera_preview.setText("📹 Camera Preview\nClick 'Start Tracking' to begin")
            self.camera_preview.setStyleSheet("""
                background: rgba(0, 0, 0, 0.5); border: 2px dashed rgba(0, 212, 255, 0.15);
                border-radius: 12px; color: #445566; font-size: 14px;
            """)
            self.ai_condition_label.setText("⚫ Idle\nWaiting for activation...")
            self.ai_condition_label.setStyleSheet("font-size: 12px; color: #7788aa; background: transparent;")

    def update_frame(self, frame):
        """Update camera preview with new frame"""
        self._last_frame = frame.copy()
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (780, 450))
            h, w, ch = resized.shape
            bpl = ch * w
            qimg = QImage(resized.data, w, h, bpl, QImage.Format_RGB888)
            self.camera_preview.setPixmap(
                QPixmap.fromImage(qimg).scaled(
                    780, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        except Exception as e:
            print(f"Frame display error: {e}")

    def update_fps(self, fps):
        """Update FPS graph"""
        self.fps_graph.add_fps_value(fps)

    def update_mode_cards(self, mode):
        """Update mode card selection state"""
        for mode_key, card in self.mode_cards.items():
            card.set_selected(mode_key == mode)

    def update_ai_stats(self, tracking_active, fps, mode, hand_detected):
        """Update AI stats display"""
        hands = "1" if hand_detected else "0"
        self.ai_stats_label.setText(
            f"{'🟢' if tracking_active else '🔴'} AI Engine: {'Running' if tracking_active else 'Stopped'}\n"
            f"⚡ FPS: {fps}\n"
            f"🎯 Mode: {mode}\n"
            f"🖐 Hands Detected: {hands}"
        )
        self.ai_status.set_active(tracking_active and hand_detected)

    def update_status_bar(self, user, tracking_active, fps, mode, hand_detected, gesture_count):
        """Update bottom status bar"""
        mode_emoji = {"DESKTOP": "🖥", "GAMING": "🎮", "DRAW": "✏️"}
        emoji = mode_emoji.get(mode, "❓")
        hand = "✅ Yes" if hand_detected else "❌ No"
        cam_text = f"FPS: {fps}" if tracking_active else "Tracking: Off"
        self.dashboard_status.setText(
            f"⚡ {user} | {cam_text} | Mode: {emoji} {mode} | Hand: {hand} | Gestures: {gesture_count}"
        )

    def get_selected_camera(self):
        """Get selected camera index"""
        return self.cam_selector.currentData()

    def get_last_frame(self):
        """Get last camera frame"""
        return self._last_frame

    def cleanup(self):
        """Cleanup resources"""
        self.ai_status.cleanup()
        self.training_btn.cleanup()
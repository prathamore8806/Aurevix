import config
import hand_tracker
import os
import cv2
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QComboBox, QFrame, QPushButton,
    QCheckBox, QScrollArea, QGraphicsDropShadowEffect,
    QSizePolicy, QSpacerItem, QSpinBox
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Signal, QSize, Property
)
from PySide6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPainterPath, QLinearGradient
)


# ─── ANIMATED TOGGLE SWITCH ─────────────────────────────────────────
class ToggleSwitch(QWidget):
    """Custom animated toggle switch replacing ugly QCheckBox."""
    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._signals_blocked = False
        self._circle_x = 27.0 if checked else 3.0
        self._bg_color = QColor("#2563eb") if checked else QColor("#3a3a4a")

        self._anim = QPropertyAnimation(self, b"circleX")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def _get_circle_x(self):
        return self._circle_x

    def _set_circle_x(self, val):
        self._circle_x = val
        t = max(0.0, min(1.0, (val - 3.0) / 24.0))
        r = int(58 + t * (37 - 58))
        g = int(58 + t * (99 - 58))
        b = int(74 + t * (235 - 74))
        self._bg_color = QColor(r, g, b)
        self.update()

    circleX = Property(float, _get_circle_x, _set_circle_x)

    def isChecked(self):
        return self._checked

    def setChecked(self, val):
        if self._checked == val:
            return
        self._checked = val
        self._circle_x = 27.0 if val else 3.0
        self._bg_color = QColor("#2563eb") if val else QColor("#3a3a4a")
        self.update()

    def blockSignals(self, block):
        """Support blockSignals like standard Qt widgets."""
        self._signals_blocked = block

    def mousePressEvent(self, e):
        self._checked = not self._checked
        self._anim.setStartValue(self._circle_x)
        self._anim.setEndValue(27.0 if self._checked else 3.0)
        self._anim.start()
        if not self._signals_blocked:
            self.toggled.emit(self._checked)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Track background
        track = QPainterPath()
        track.addRoundedRect(0, 0, 50, 26, 13, 13)
        p.fillPath(track, self._bg_color)

        # Glow when active
        if self._checked:
            glow = QColor("#2563eb")
            glow.setAlpha(60)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawRoundedRect(-2, -2, 54, 30, 15, 15)
            p.fillPath(track, self._bg_color)

        # Circle knob
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("white"))
        p.drawEllipse(int(self._circle_x), 3, 20, 20)
        p.end()


# ─── CUSTOM STYLED SLIDER ───────────────────────────────────────────
class StyledSlider(QWidget):
    """Slider with live value label."""
    valueChanged = Signal(int)

    def __init__(self, min_v, max_v, curr, suffix="", parent=None):
        super().__init__(parent)
        self.suffix = suffix
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedWidth(130)
        self.slider.setRange(min_v, max_v)
        self.slider.setValue(curr)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.08);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2563eb;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid #3b82f6;
            }
            QSlider::handle:horizontal:hover {
                background: #3b82f6;
                border: 2px solid #60a5fa;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1d4ed8, stop:1 #2563eb);
                border-radius: 3px;
            }
        """)

        self.value_label = QLabel(f"{curr}{suffix}")
        self.value_label.setFixedWidth(45)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            background: rgba(37, 99, 235, 0.15);
            color: #60a5fa;
            border-radius: 6px;
            padding: 2px 6px;
            font-weight: bold;
            font-size: 11px;
            border: 1px solid rgba(37, 99, 235, 0.3);
        """)

        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self._on_change)

    def _on_change(self, v):
        self.value_label.setText(f"{v}{self.suffix}")
        self.valueChanged.emit(v)

    def setValue(self, v):
        self.slider.setValue(v)
        self.value_label.setText(f"{v}{self.suffix}")

    def value(self):
        return self.slider.value()


# ─── STYLED COMBO BOX ───────────────────────────────────────────────
class StyledCombo(QComboBox):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setFixedWidth(160)
        self.addItems(items)
        self.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 6px 12px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid rgba(37, 99, 235, 0.5);
                background: rgba(255, 255, 255, 0.08);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #60a5fa;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #1e1e2e;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #e2e8f0;
                selection-background-color: #2563eb;
                padding: 4px;
            }
        """)


# ─── MAIN PREFERENCES PAGE ──────────────────────────────────────────
class PreferencesPage(QWidget):
    """Complete preferences page with all signals for main window."""

    # ── Signals for main window to connect ──
    themeChanged = Signal(str)
    penColorChanged = Signal(int)
    thicknessChanged = Signal(int)
    autoclearChanged = Signal(int)
    cameraChanged = Signal(int)
    startupChanged = Signal(bool)
    trayChanged = Signal(bool)
    popupsChanged = Signal(bool)
    skeletonChanged = Signal(bool)
    fpsChanged = Signal(int)
    leftHandChanged = Signal(bool)
    clickSensChanged = Signal(int)
    
    # ── Calibration Signals ──
    calibrationModeChanged = Signal(int)
    calibrationStabilityChanged = Signal(int)
    calibrationCountdownChanged = Signal(int)
    calibrationSoundChanged = Signal(bool)
    calibrationVolumeChanged = Signal(int)
    calibrationSkeletonChanged = Signal(bool)
    calibrationGridChanged = Signal(bool)
    calibrationPointCountChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 25, 30, 25)
        self.main_layout.setSpacing(0)

        # ── HEADER ROW ───────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(15)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Preferences")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: 700;
            color: #f1f5f9;
            letter-spacing: -0.5px;
        """)

        subtitle = QLabel("Customize your gesture control experience")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b;")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        # Reset button
        self.reset_btn = QPushButton("  Reset Defaults")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setFixedHeight(36)
        self.reset_btn.clicked.connect(self.reset_defaults)
        header_row.addWidget(self.reset_btn)

        self.main_layout.addLayout(header_row)
        self.main_layout.addSpacing(18)

        # ── NAV PILLS ────────────────────────────────────────────
        nav_container = QFrame()
        nav_container.setFixedHeight(44)
        nav_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        self.nav_bar = QHBoxLayout(nav_container)
        self.nav_bar.setContentsMargins(4, 4, 4, 4)
        self.nav_bar.setSpacing(4)

        sections = [
            ("Drawing", "🎨"),
            ("System", "⚙️"),
            ("Visuals", "✨"),
            ("Logic", "🧠"),
            ("Calibration", "🎯"),  # NEW
        ]

        self.nav_btns = []
        for i, (name, icon) in enumerate(sections):
            btn = QPushButton(f" {icon}  {name}")
            btn.setObjectName("navPill")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            if i == 0:
                btn.setChecked(True)
            btn.clicked.connect(
                lambda checked, idx=i: self.scroll_to_section(idx)
            )
            self.nav_bar.addWidget(btn)
            self.nav_btns.append(btn)

        self.nav_bar.addStretch()
        self.main_layout.addWidget(nav_container)
        self.main_layout.addSpacing(16)

        # ── SCROLL AREA ──────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 6, 0)

        self.groups = []

        # ══════════════════════════════════════════════════════════
        # SECTION 1: CANVAS & DRAWING
        # ══════════════════════════════════════════════════════════
        draw_sec = self._create_section(
            "🎨", "Canvas & Drawing",
            "Pen color, thickness, and canvas behavior"
        )

        colors = ["Neon Red", "Electric Blue", "Toxic Green", "Hot Pink"]
        self.pen_color_combo = self._add_combo_setting(
            draw_sec, "Default Pen Color",
            "Primary color used in Draw Mode",
            colors, self.set_pen_color
        )

        self.thickness_slider = self._add_slider_setting(
            draw_sec, "Pen Thickness",
            "Adjust brush size for drawing",
            1, 20, getattr(config, 'draw_thickness', 5),
            "px", self.set_thickness
        )

        autoclear_opts = ["Off", "5 seconds", "10 seconds", "30 seconds"]
        self.autoclear_combo = self._add_combo_setting(
            draw_sec, "Auto-Clear Timer",
            "Automatically clear canvas after duration",
            autoclear_opts, self.set_autoclear
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 2: SYSTEM & STARTUP
        # ══════════════════════════════════════════════════════════
        sys_sec = self._create_section(
            "⚙️", "System & Startup",
            "Camera, startup behavior, and notifications"
        )

        cameras = self.get_available_cameras()
        self.camera_combo = self._add_combo_setting(
            sys_sec, "Active Camera",
            "Select which webcam to use for tracking",
            cameras, self.set_camera
        )

        self.startup_toggle = self._add_toggle_setting(
            sys_sec, "Run at Startup",
            "Automatically launch SGCC with Windows",
            False, self.toggle_startup
        )

        self.tray_toggle = self._add_toggle_setting(
            sys_sec, "Minimize to Tray",
            "Keep running in system tray when closed",
            getattr(config, 'minimize_to_tray', True),
            self.toggle_tray
        )

        self.popup_toggle = self._add_toggle_setting(
            sys_sec, "Mode Popups",
            "Show notification popups on mode switch",
            getattr(config, 'show_popups', True),
            self.toggle_popups
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 3: VISUALS & PERFORMANCE
        # ══════════════════════════════════════════════════════════
        vis_sec = self._create_section(
            "✨", "Visuals & Performance",
            "Theme, overlays, and frame rate settings"
        )

        themes = ["Deep Space (Dark)", "Cloud (Light)"]
        self.theme_combo = self._add_combo_setting(
            vis_sec, "App Theme",
            "Switch between Dark and Light interface",
            themes, self.set_theme
        )

        self.skeleton_toggle = self._add_toggle_setting(
            vis_sec, "Skeleton Overlay",
            "Show hand landmark connections on camera feed",
            getattr(config, 'show_skeleton', True),
            self.toggle_skeleton
        )

        self.fps_slider = self._add_slider_setting(
            vis_sec, "FPS Cap",
            "Limit processing frame rate to save resources",
            15, 60, getattr(config, 'fps_limit', 30),
            " fps", self.set_fps
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 4: LOGIC & CALIBRATION
        # ══════════════════════════════════════════════════════════
        log_sec = self._create_section(
            "🧠", "Logic & Calibration",
            "Handedness, sensitivity, and gesture tuning"
        )

        self.lefthand_toggle = self._add_toggle_setting(
            log_sec, "Left-Handed Mode",
            "Mirror tracking coordinates for left hand use",
            getattr(config, 'left_handed_mode', False),
            self.toggle_left_hand
        )

        self.click_slider = self._add_slider_setting(
            log_sec, "Click Sensitivity",
            "Pinch distance threshold for click detection",
            1, 10, getattr(config, 'click_sensitivity', 5),
            "", self.set_click_sense
        )

        # ══════════════════════════════════════════════════════════
        # SECTION 5: CALIBRATION SETTINGS (NEW)
        # ══════════════════════════════════════════════════════════
        cal_sec = self._create_section(
            "🎯", "Calibration Settings",
            "Auto-capture behavior, visual feedback, and defaults"
        )

        # Capture Mode
        capture_modes = ["🖱️ Manual Click", "⏱️ Hold Stable", "⏰ Auto Countdown"]
        mode_idx = getattr(config, 'calibration_capture_mode', 2)
        self.capture_mode_combo = self._add_combo_setting(
            cal_sec, "Capture Mode",
            "How calibration points are captured",
            capture_modes, self.set_capture_mode
        )
        self.capture_mode_combo.setCurrentIndex(mode_idx)

        # Stability Threshold
        self.cal_stability_slider = self._add_slider_setting(
            cal_sec, "Stability Threshold",
            "How steady hand must be before capture (higher = stricter)",
            70, 100, getattr(config, 'calibration_stability_threshold', 90),
            "%", self.set_cal_stability
        )

        # Countdown Duration
        self.cal_countdown_slider = self._add_slider_setting(
            cal_sec, "Countdown Duration",
            "Seconds before auto-capture in countdown mode",
            1, 5, getattr(config, 'calibration_countdown_seconds', 3),
            "s", self.set_cal_countdown
        )

        # Point Count
        point_counts = ["4 Points (2×2)", "9 Points (3×3)", "16 Points (4×4)"]
        point_map = {4: 0, 9: 1, 16: 2}
        current_count = getattr(config, 'calibration_point_count', 4)
        point_idx = point_map.get(current_count, 0)
        
        self.point_count_combo = self._add_combo_setting(
            cal_sec, "Default Point Count",
            "Number of calibration points to capture",
            point_counts, self.set_point_count
        )
        self.point_count_combo.setCurrentIndex(point_idx)

        # Sound Toggle
        self.cal_sound_toggle = self._add_toggle_setting(
            cal_sec, "Calibration Sounds",
            "Play audio feedback during calibration",
            getattr(config, 'calibration_sound_enabled', True),
            self.toggle_cal_sound
        )

        # Volume Slider
        self.cal_volume_slider = self._add_slider_setting(
            cal_sec, "Calibration Volume",
            "Audio volume for countdown and capture sounds",
            0, 100, getattr(config, 'calibration_volume', 60),
            "%", self.set_cal_volume
        )

        # Skeleton Toggle
        self.cal_skeleton_toggle = self._add_toggle_setting(
            cal_sec, "Hand Skeleton Overlay",
            "Show hand landmarks during calibration",
            getattr(config, 'calibration_show_skeleton', True),
            self.toggle_cal_skeleton
        )

        # Grid Toggle
        self.cal_grid_toggle = self._add_toggle_setting(
            cal_sec, "Grid Overlay",
            "Display alignment grid on camera feed",
            getattr(config, 'calibration_show_grid', False),
            self.toggle_cal_grid
        )

        # Calibration Status Display
        self._add_calibration_status(cal_sec)

        # Finish
        self.content_layout.addSpacerItem(
            QSpacerItem(0, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        self.scroll.setWidget(container)
        self.main_layout.addWidget(self.scroll)

        self._apply_styles()

    # ─── SECTION BUILDER ─────────────────────────────────────────
    def _create_section(self, icon, title, description):
        group = QFrame()
        group.setObjectName("settingsSection")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(4)

        # Section header
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            "font-size: 20px; border: none; background: transparent;"
        )
        icon_label.setFixedWidth(28)
        header_row.addWidget(icon_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet("""
            font-size: 16px; font-weight: 700; color: #e2e8f0;
            border: none; background: transparent;
        """)
        title_col.addWidget(t)

        d = QLabel(description)
        d.setStyleSheet("""
            font-size: 11px; color: #64748b;
            border: none; background: transparent;
        """)
        title_col.addWidget(d)

        header_row.addLayout(title_col)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            "background: rgba(255,255,255,0.06); border: none; margin: 8px 0;"
        )
        layout.addWidget(divider)
        layout.addSpacing(6)

        self.content_layout.addWidget(group)
        self.groups.append(group)
        return layout

    # ─── SETTING ROW BUILDERS ────────────────────────────────────
    def _add_toggle_setting(self, layout, name, desc, checked, callback):
        toggle = ToggleSwitch(checked)
        toggle.toggled.connect(callback)
        self._add_setting_row(layout, name, desc, toggle)
        return toggle

    def _add_slider_setting(self, layout, name, desc, min_v, max_v,
                            curr, suffix, callback):
        slider = StyledSlider(min_v, max_v, curr, suffix)
        slider.valueChanged.connect(callback)
        self._add_setting_row(layout, name, desc, slider)
        return slider

    def _add_combo_setting(self, layout, name, desc, items, callback):
        combo = StyledCombo(items)
        combo.currentIndexChanged.connect(callback)
        self._add_setting_row(layout, name, desc, combo)
        return combo

    def _add_setting_row(self, layout, name, desc, widget):
        row = QFrame()
        row.setObjectName("settingRow")
        row.setFixedHeight(56)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 8, 12, 8)
        row_layout.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        n = QLabel(name)
        n.setStyleSheet("""
            font-weight: 600; font-size: 13px; color: #e2e8f0;
            border: none; background: transparent;
        """)

        d = QLabel(desc)
        d.setStyleSheet("""
            color: #64748b; font-size: 11px;
            border: none; background: transparent;
        """)

        text_col.addWidget(n)
        text_col.addWidget(d)

        row_layout.addLayout(text_col)
        row_layout.addStretch()
        row_layout.addWidget(widget)

        layout.addWidget(row)

    def _add_calibration_status(self, layout):
        """Add calibration status display."""
        status_frame = QFrame()
        status_frame.setObjectName("calibrationStatus")
        status_frame.setStyleSheet("""
            #calibrationStatus {
                background: rgba(0, 212, 255, 0.05);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(14, 10, 14, 10)
        status_layout.setSpacing(8)
        
        # Status header
        header = QHBoxLayout()
        status_title = QLabel("📊 Calibration Status")
        status_title.setStyleSheet("color: #00d4ff; font-weight: 600; font-size: 12px; background: transparent;")
        header.addWidget(status_title)
        header.addStretch()
        
        self.calibrated_badge = QLabel("✓ Calibrated" if config.is_calibrated() else "⚠ Not Calibrated")
        badge_color = "#00ff88" if config.is_calibrated() else "#ffa500"
        self.calibrated_badge.setStyleSheet(f"""
            color: {badge_color}; font-weight: 600; font-size: 11px;
            background: rgba(255,255,255,0.05); padding: 4px 10px;
            border-radius: 8px;
        """)
        header.addWidget(self.calibrated_badge)
        status_layout.addLayout(header)
        
        # Margins info
        margins = config.get_calibration_margins()
        self.margins_label = QLabel(
            f"X: {margins['x_min']:.0f} → {margins['x_max']:.0f}  |  "
            f"Y: {margins['y_min']:.0f} → {margins['y_max']:.0f}"
        )
        self.margins_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; background: transparent;")
        status_layout.addWidget(self.margins_label)
        
        layout.addWidget(status_frame)

    # ─── NAVIGATION ──────────────────────────────────────────────
    def scroll_to_section(self, index):
        if index < len(self.groups):
            widget = self.groups[index]
            self.scroll.ensureWidgetVisible(widget, 0, 50)

    # ─── SETTINGS CALLBACKS (CONFIG + SAVE + SIGNAL) ─────────────
    def set_pen_color(self, i):
        """Handle pen color change."""
        colors = [(0, 0, 255), (255, 0, 0), (0, 255, 0), (255, 0, 255)]
        if i < len(colors):
            config.draw_color = colors[i]
            config.save_config()
            self.penColorChanged.emit(i)

    def set_thickness(self, v):
        """Handle pen thickness change."""
        config.draw_thickness = v
        config.save_config()
        self.thicknessChanged.emit(v)

    def set_autoclear(self, i):
        """Handle auto-clear timer change."""
        vals = [0, 5, 10, 30]
        if i < len(vals):
            config.auto_clear_sec = vals[i]
            config.save_config()
            self.autoclearChanged.emit(i)

    def set_camera(self, i):
        """Handle camera switch."""
        config.camera_index = i
        config.save_config()
        if hasattr(hand_tracker, 'needs_camera_restart'):
            hand_tracker.needs_camera_restart = True
        self.cameraChanged.emit(i)

    def toggle_startup(self, checked):
        """Handle startup toggle."""
        self.startupChanged.emit(checked)

    def toggle_tray(self, checked):
        """Handle tray toggle."""
        config.minimize_to_tray = checked
        config.save_config()
        self.trayChanged.emit(checked)

    def toggle_popups(self, checked):
        """Handle popups toggle."""
        config.show_popups = checked
        config.save_config()
        self.popupsChanged.emit(checked)

    def set_theme(self, i):
        """Handle theme change."""
        config.theme = "dark" if i == 0 else "light"
        config.save_config()
        self.themeChanged.emit(config.theme)

    def toggle_skeleton(self, checked):
        """Handle skeleton overlay toggle."""
        config.show_skeleton = checked
        config.save_config()
        self.skeletonChanged.emit(checked)

    def set_fps(self, v):
        """Handle FPS cap change."""
        config.fps_limit = v
        config.save_config()
        self.fpsChanged.emit(v)

    def toggle_left_hand(self, checked):
        """Handle left-handed mode toggle."""
        config.left_handed_mode = checked
        config.save_config()
        self.leftHandChanged.emit(checked)

    def set_click_sense(self, v):
        """Handle click sensitivity change."""
        config.click_sensitivity = v
        config.save_config()
        self.clickSensChanged.emit(v)

    # ─── CALIBRATION CALLBACKS ───────────────────────────────────
    def set_capture_mode(self, i):
        """Handle calibration capture mode change."""
        config.calibration_capture_mode = i
        config.save_config()
        self.calibrationModeChanged.emit(i)
        print(f"📍 Calibration mode: {['Manual', 'Stability', 'Countdown'][i]}")

    def set_cal_stability(self, v):
        """Handle stability threshold change."""
        config.calibration_stability_threshold = v
        config.save_config()
        self.calibrationStabilityChanged.emit(v)

    def set_cal_countdown(self, v):
        """Handle countdown duration change."""
        config.calibration_countdown_seconds = v
        config.save_config()
        self.calibrationCountdownChanged.emit(v)

    def set_point_count(self, i):
        """Handle point count change."""
        counts = [4, 9, 16]
        if i < len(counts):
            config.calibration_point_count = counts[i]
            config.save_config()
            self.calibrationPointCountChanged.emit(counts[i])
            print(f"📍 Default point count: {counts[i]}")

    def toggle_cal_sound(self, checked):
        """Handle calibration sound toggle."""
        config.calibration_sound_enabled = checked
        config.save_config()
        self.calibrationSoundChanged.emit(checked)

    def set_cal_volume(self, v):
        """Handle calibration volume change."""
        config.calibration_volume = v
        config.save_config()
        self.calibrationVolumeChanged.emit(v)

    def toggle_cal_skeleton(self, checked):
        """Handle calibration skeleton toggle."""
        config.calibration_show_skeleton = checked
        config.save_config()
        self.calibrationSkeletonChanged.emit(checked)

    def toggle_cal_grid(self, checked):
        """Handle calibration grid toggle."""
        config.calibration_show_grid = checked
        config.save_config()
        self.calibrationGridChanged.emit(checked)

    # ─── SYNC UI TO CONFIG (EXTERNAL CHANGES) ────────────────────
    def _sync_ui_to_config(self):
        """Sync all UI elements to current config values.
        Called when config changes externally (keyboard shortcuts,
        settings panel, or config file reload)."""

        # ══════════════════════════════════════════════════════════
        # DRAWING SECTION
        # ══════════════════════════════════════════════════════════
        
        # Thickness slider
        target = getattr(config, 'draw_thickness', 5)
        if self.thickness_slider.value() != target:
            self.thickness_slider.slider.blockSignals(True)
            self.thickness_slider.setValue(target)
            self.thickness_slider.slider.blockSignals(False)

        # Pen color combo
        draw_color = getattr(config, 'draw_color', (0, 0, 255))
        color_map = {
            (0, 0, 255): 0,
            (255, 0, 0): 1,
            (0, 255, 0): 2,
            (255, 0, 255): 3
        }
        color_idx = color_map.get(tuple(draw_color), 0)
        if self.pen_color_combo.currentIndex() != color_idx:
            self.pen_color_combo.blockSignals(True)
            self.pen_color_combo.setCurrentIndex(color_idx)
            self.pen_color_combo.blockSignals(False)

        # Auto-clear combo
        auto_clear = getattr(config, 'auto_clear_sec', 0)
        clear_map = {0: 0, 5: 1, 10: 2, 30: 3}
        clear_idx = clear_map.get(auto_clear, 0)
        if self.autoclear_combo.currentIndex() != clear_idx:
            self.autoclear_combo.blockSignals(True)
            self.autoclear_combo.setCurrentIndex(clear_idx)
            self.autoclear_combo.blockSignals(False)

        # ══════════════════════════════════════════════════════════
        # SYSTEM SECTION
        # ══════════════════════════════════════════════════════════
        
        # Camera combo
        cam_idx = getattr(config, 'camera_index', 0)
        if cam_idx < self.camera_combo.count():
            if self.camera_combo.currentIndex() != cam_idx:
                self.camera_combo.blockSignals(True)
                self.camera_combo.setCurrentIndex(cam_idx)
                self.camera_combo.blockSignals(False)

        # Tray toggle
        target = getattr(config, 'minimize_to_tray', True)
        if self.tray_toggle.isChecked() != target:
            self.tray_toggle.blockSignals(True)
            self.tray_toggle.setChecked(target)
            self.tray_toggle.blockSignals(False)

        # Popup toggle
        target = getattr(config, 'show_popups', True)
        if self.popup_toggle.isChecked() != target:
            self.popup_toggle.blockSignals(True)
            self.popup_toggle.setChecked(target)
            self.popup_toggle.blockSignals(False)

        # ══════════════════════════════════════════════════════════
        # VISUALS SECTION
        # ══════════════════════════════════════════════════════════
        
        # Theme combo
        theme = getattr(config, 'theme', 'dark')
        theme_idx = 0 if theme == "dark" else 1
        if self.theme_combo.currentIndex() != theme_idx:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(theme_idx)
            self.theme_combo.blockSignals(False)

        # Skeleton toggle
        target = getattr(config, 'show_skeleton', True)
        if self.skeleton_toggle.isChecked() != target:
            self.skeleton_toggle.blockSignals(True)
            self.skeleton_toggle.setChecked(target)
            self.skeleton_toggle.blockSignals(False)

        # FPS slider
        target = getattr(config, 'fps_limit', 30)
        if self.fps_slider.value() != target:
            self.fps_slider.slider.blockSignals(True)
            self.fps_slider.setValue(target)
            self.fps_slider.slider.blockSignals(False)

        # ══════════════════════════════════════════════════════════
        # LOGIC SECTION
        # ══════════════════════════════════════════════════════════
        
        # Left-handed toggle
        target = getattr(config, 'left_handed_mode', False)
        if self.lefthand_toggle.isChecked() != target:
            self.lefthand_toggle.blockSignals(True)
            self.lefthand_toggle.setChecked(target)
            self.lefthand_toggle.blockSignals(False)

        # Click sensitivity slider
        target = getattr(config, 'click_sensitivity', 5)
        if self.click_slider.value() != target:
            self.click_slider.slider.blockSignals(True)
            self.click_slider.setValue(target)
            self.click_slider.slider.blockSignals(False)

        # ══════════════════════════════════════════════════════════
        # CALIBRATION SECTION
        # ══════════════════════════════════════════════════════════
        
        # Capture mode combo
        mode_idx = getattr(config, 'calibration_capture_mode', 2)
        if self.capture_mode_combo.currentIndex() != mode_idx:
            self.capture_mode_combo.blockSignals(True)
            self.capture_mode_combo.setCurrentIndex(mode_idx)
            self.capture_mode_combo.blockSignals(False)

        # Stability slider
        target = getattr(config, 'calibration_stability_threshold', 90)
        if self.cal_stability_slider.value() != target:
            self.cal_stability_slider.slider.blockSignals(True)
            self.cal_stability_slider.setValue(target)
            self.cal_stability_slider.slider.blockSignals(False)

        # Countdown slider
        target = getattr(config, 'calibration_countdown_seconds', 3)
        if self.cal_countdown_slider.value() != target:
            self.cal_countdown_slider.slider.blockSignals(True)
            self.cal_countdown_slider.setValue(target)
            self.cal_countdown_slider.slider.blockSignals(False)

        # Point count combo
        count = getattr(config, 'calibration_point_count', 4)
        count_map = {4: 0, 9: 1, 16: 2}
        idx = count_map.get(count, 0)
        if self.point_count_combo.currentIndex() != idx:
            self.point_count_combo.blockSignals(True)
            self.point_count_combo.setCurrentIndex(idx)
            self.point_count_combo.blockSignals(False)

        # Sound toggle
        target = getattr(config, 'calibration_sound_enabled', True)
        if self.cal_sound_toggle.isChecked() != target:
            self.cal_sound_toggle.blockSignals(True)
            self.cal_sound_toggle.setChecked(target)
            self.cal_sound_toggle.blockSignals(False)

        # Volume slider
        target = getattr(config, 'calibration_volume', 60)
        if self.cal_volume_slider.value() != target:
            self.cal_volume_slider.slider.blockSignals(True)
            self.cal_volume_slider.setValue(target)
            self.cal_volume_slider.slider.blockSignals(False)

        # Skeleton toggle
        target = getattr(config, 'calibration_show_skeleton', True)
        if self.cal_skeleton_toggle.isChecked() != target:
            self.cal_skeleton_toggle.blockSignals(True)
            self.cal_skeleton_toggle.setChecked(target)
            self.cal_skeleton_toggle.blockSignals(False)

        # Grid toggle
        target = getattr(config, 'calibration_show_grid', False)
        if self.cal_grid_toggle.isChecked() != target:
            self.cal_grid_toggle.blockSignals(True)
            self.cal_grid_toggle.setChecked(target)
            self.cal_grid_toggle.blockSignals(False)

        # Update calibration status
        self._update_calibration_status()

    def _update_calibration_status(self):
        """Update calibration status display."""
        if hasattr(self, 'calibrated_badge'):
            is_cal = config.is_calibrated()
            self.calibrated_badge.setText("✓ Calibrated" if is_cal else "⚠ Not Calibrated")
            badge_color = "#00ff88" if is_cal else "#ffa500"
            self.calibrated_badge.setStyleSheet(f"""
                color: {badge_color}; font-weight: 600; font-size: 11px;
                background: rgba(255,255,255,0.05); padding: 4px 10px;
                border-radius: 8px;
            """)
        
        if hasattr(self, 'margins_label'):
            margins = config.get_calibration_margins()
            self.margins_label.setText(
                f"X: {margins['x_min']:.0f} → {margins['x_max']:.0f}  |  "
                f"Y: {margins['y_min']:.0f} → {margins['y_max']:.0f}"
            )

    # ─── RESET ───────────────────────────────────────────────────
    def reset_defaults(self):
        """Reset all preferences to defaults."""
        
        # ══════════════════════════════════════════════════════════
        # RESET CONFIG VALUES
        # ══════════════════════════════════════════════════════════
        
        # Drawing
        config.draw_thickness = 5
        config.draw_color = (0, 0, 255)
        config.auto_clear_sec = 0
        
        # Visuals
        config.fps_limit = 30
        config.show_skeleton = True
        config.theme = "dark"
        
        # Logic
        config.click_sensitivity = 5
        config.left_handed_mode = False
        
        # System
        config.show_popups = True
        config.minimize_to_tray = True
        
        # Calibration
        config.calibration_capture_mode = 2
        config.calibration_stability_threshold = 90
        config.calibration_countdown_seconds = 3
        config.calibration_sound_enabled = True
        config.calibration_volume = 60
        config.calibration_show_skeleton = True
        config.calibration_show_grid = False
        config.calibration_point_count = 4
        
        config.save_config()

        # ══════════════════════════════════════════════════════════
        # RESET UI WIDGETS
        # ══════════════════════════════════════════════════════════

        # Drawing
        self.thickness_slider.slider.blockSignals(True)
        self.thickness_slider.setValue(5)
        self.thickness_slider.slider.blockSignals(False)

        self.pen_color_combo.blockSignals(True)
        self.pen_color_combo.setCurrentIndex(0)
        self.pen_color_combo.blockSignals(False)

        self.autoclear_combo.blockSignals(True)
        self.autoclear_combo.setCurrentIndex(0)
        self.autoclear_combo.blockSignals(False)

        # Visuals
        self.fps_slider.slider.blockSignals(True)
        self.fps_slider.setValue(30)
        self.fps_slider.slider.blockSignals(False)

        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.blockSignals(False)

        self.skeleton_toggle.blockSignals(True)
        self.skeleton_toggle.setChecked(True)
        self.skeleton_toggle.blockSignals(False)

        # Logic
        self.click_slider.slider.blockSignals(True)
        self.click_slider.setValue(5)
        self.click_slider.slider.blockSignals(False)

        self.lefthand_toggle.blockSignals(True)
        self.lefthand_toggle.setChecked(False)
        self.lefthand_toggle.blockSignals(False)

        # System
        self.camera_combo.blockSignals(True)
        self.camera_combo.setCurrentIndex(0)
        self.camera_combo.blockSignals(False)

        self.startup_toggle.blockSignals(True)
        self.startup_toggle.setChecked(False)
        self.startup_toggle.blockSignals(False)

        self.tray_toggle.blockSignals(True)
        self.tray_toggle.setChecked(True)
        self.tray_toggle.blockSignals(False)

        self.popup_toggle.blockSignals(True)
        self.popup_toggle.setChecked(True)
        self.popup_toggle.blockSignals(False)

        # Calibration
        self.capture_mode_combo.blockSignals(True)
        self.capture_mode_combo.setCurrentIndex(2)
        self.capture_mode_combo.blockSignals(False)

        self.cal_stability_slider.slider.blockSignals(True)
        self.cal_stability_slider.setValue(90)
        self.cal_stability_slider.slider.blockSignals(False)

        self.cal_countdown_slider.slider.blockSignals(True)
        self.cal_countdown_slider.setValue(3)
        self.cal_countdown_slider.slider.blockSignals(False)

        self.point_count_combo.blockSignals(True)
        self.point_count_combo.setCurrentIndex(0)
        self.point_count_combo.blockSignals(False)

        self.cal_sound_toggle.blockSignals(True)
        self.cal_sound_toggle.setChecked(True)
        self.cal_sound_toggle.blockSignals(False)

        self.cal_volume_slider.slider.blockSignals(True)
        self.cal_volume_slider.setValue(60)
        self.cal_volume_slider.slider.blockSignals(False)

        self.cal_skeleton_toggle.blockSignals(True)
        self.cal_skeleton_toggle.setChecked(True)
        self.cal_skeleton_toggle.blockSignals(False)

        self.cal_grid_toggle.blockSignals(True)
        self.cal_grid_toggle.setChecked(False)
        self.cal_grid_toggle.blockSignals(False)

        # ══════════════════════════════════════════════════════════
        # EMIT ALL SIGNALS
        # ══════════════════════════════════════════════════════════
        
        self.themeChanged.emit("dark")
        self.penColorChanged.emit(0)
        self.thicknessChanged.emit(5)
        self.autoclearChanged.emit(0)
        self.fpsChanged.emit(30)
        self.clickSensChanged.emit(5)
        self.skeletonChanged.emit(True)
        self.leftHandChanged.emit(False)
        self.popupsChanged.emit(True)
        self.trayChanged.emit(True)
        
        # Calibration signals
        self.calibrationModeChanged.emit(2)
        self.calibrationStabilityChanged.emit(90)
        self.calibrationCountdownChanged.emit(3)
        self.calibrationSoundChanged.emit(True)
        self.calibrationVolumeChanged.emit(60)
        self.calibrationSkeletonChanged.emit(True)
        self.calibrationGridChanged.emit(False)
        self.calibrationPointCountChanged.emit(4)

        # Update status
        self._update_calibration_status()

        print("🔄 Preferences reset to defaults")

    # ─── CAMERA DETECTION ────────────────────────────────────────
    def get_available_cameras(self):
        """Show ALL camera options with connection status."""
        arr = []
    
        for index in range(3):  # Always show 3 options
            # Get name from config
            base_name = config.CAMERA_SOURCES.get(index, f"Camera {index}")
        
            # Check if camera is connected
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if cap.isOpened() and cap.read()[0]:
                    name = f"{base_name} ✅"  # Connected
                else:
                    name = f"{base_name} ❌"  # Not connected
                cap.release()
            except Exception:
                name = f"{base_name} ❌"  # Error = not connected
        
            arr.append(name)
    
        return arr

    # ─── SHOW EVENT ──────────────────────────────────────────────
    def showEvent(self, event):
        """Sync UI when page is shown."""
        super().showEvent(event)
        self._sync_ui_to_config()

    # ─── STYLESHEET ──────────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            PreferencesPage {
                background: transparent;
            }

            #settingsSection {
                background: rgba(255, 255, 255, 0.025);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }
            #settingsSection:hover {
                border: 1px solid rgba(255, 255, 255, 0.1);
                background: rgba(255, 255, 255, 0.035);
            }

            #settingRow {
                background: rgba(255, 255, 255, 0.02);
                border: none;
                border-radius: 10px;
            }
            #settingRow:hover {
                background: rgba(255, 255, 255, 0.05);
            }

            #navPill {
                background: transparent;
                border: none;
                padding: 6px 16px;
                border-radius: 8px;
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
            }
            #navPill:hover {
                background: rgba(255, 255, 255, 0.06);
                color: #e2e8f0;
            }
            #navPill:checked {
                background: rgba(37, 99, 235, 0.15);
                color: #60a5fa;
                font-weight: 700;
                border: 1px solid rgba(37, 99, 235, 0.3);
            }

            #resetBtn {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 8px;
                color: #f87171;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 16px;
            }
            #resetBtn:hover {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            #resetBtn:pressed {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
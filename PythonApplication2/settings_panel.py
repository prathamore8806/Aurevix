import os
import cv2
import time
import math
import threading
import numpy as np
import config
import mode_manager

from PySide6.QtWidgets import (
    QWidget, QLabel, QSlider, QCheckBox, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
    QScrollArea, QSizePolicy, QMessageBox, QSpacerItem,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QLinearGradient

try:
    import pyaudio
    import struct
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️ pyaudio not installed. Run: pip install pyaudio")


# ═══════════════════════════════════════════════════════════════
#                         AUDIO METER
# ═══════════════════════════════════════════════════════════════

class AudioMeter(QFrame):
    """Visual audio level meter widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setObjectName("audioMeter")
        self.level = 0.0
        self.peak = 0.0
        self.peak_hold = 0
        self.setStyleSheet("""
            #audioMeter {
                background: rgba(13, 17, 23, 0.8);
                border-radius: 6px;
                border: 1px solid rgba(48, 54, 61, 0.6);
            }
        """)

    def set_level(self, level):
        self.level = max(0.0, min(1.0, level))
        if self.level > self.peak:
            self.peak = self.level
            self.peak_hold = 30
        else:
            self.peak_hold -= 1
            if self.peak_hold <= 0:
                self.peak = max(0, self.peak - 0.02)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width() - 4
        h = self.height() - 4
        x, y = 2, 2

        # Background
        painter.setBrush(QColor(13, 17, 23))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(x, y, w, h, 5, 5)

        # Level bar with gradient
        bar_width = int(w * self.level)
        if bar_width > 0:
            gradient = QLinearGradient(x, 0, x + w, 0)
            if self.level < 0.5:
                gradient.setColorAt(0.0, QColor(34, 197, 94))
                gradient.setColorAt(1.0, QColor(34, 197, 94))
            elif self.level < 0.8:
                gradient.setColorAt(0.0, QColor(34, 197, 94))
                gradient.setColorAt(0.7, QColor(250, 204, 21))
                gradient.setColorAt(1.0, QColor(249, 115, 22))
            else:
                gradient.setColorAt(0.0, QColor(34, 197, 94))
                gradient.setColorAt(0.5, QColor(250, 204, 21))
                gradient.setColorAt(0.8, QColor(249, 115, 22))
                gradient.setColorAt(1.0, QColor(239, 68, 68))

            painter.setBrush(gradient)
            painter.drawRoundedRect(x, y, bar_width, h, 5, 5)

        # Peak indicator
        peak_x = int(x + w * self.peak)
        if peak_x > x + 2:
            painter.setPen(QColor(255, 255, 255, 180))
            painter.drawLine(peak_x, y + 2, peak_x, y + h - 2)

        painter.end()


# ═══════════════════════════════════════════════════════════════
#                         AUDIO ENGINE
# ═══════════════════════════════════════════════════════════════

class AudioEngine:
    """Audio capture and level monitoring."""

    def __init__(self):
        self.stream = None
        self.pa = None
        self.running = False
        self.level = 0.0
        self.device_index = None
        self.volume = 0.8
        self.muted = False

    def get_devices(self):
        devices = []
        if PYAUDIO_AVAILABLE:
            try:
                pa = pyaudio.PyAudio()
                for i in range(pa.get_device_count()):
                    info = pa.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        devices.append({
                            'index': i,
                            'name': info['name'],
                            'channels': info['maxInputChannels'],
                            'rate': int(info['defaultSampleRate'])
                        })
                pa.terminate()
            except Exception as e:
                print(f"❌ Audio scan error: {e}")
        return devices

    def start(self, device_index=None, rate=44100):
        if not PYAUDIO_AVAILABLE:
            return False
        try:
            self.pa = pyaudio.PyAudio()
            kwargs = {
                'format': pyaudio.paInt16,
                'channels': 1,
                'rate': rate,
                'input': True,
                'frames_per_buffer': 1024,
            }
            if device_index is not None:
                kwargs['input_device_index'] = device_index

            self.stream = self.pa.open(**kwargs)
            self.running = True
            self.device_index = device_index
            print(f"🎤 Audio started (device: {device_index})")
            return True
        except Exception as e:
            print(f"❌ Audio error: {e}")
            self.running = False
            return False

    def read_level(self):
        if not self.running or not self.stream or self.muted:
            return 0.0
        try:
            data = self.stream.read(1024, exception_on_overflow=False)
            samples = struct.unpack(f'{len(data) // 2}h', data)
            if samples:
                rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                level = min(1.0, rms / 16000.0) * self.volume
                self.level = level
                return level
        except Exception:
            pass
        return 0.0

    def stop(self):
        self.running = False
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.pa:
                self.pa.terminate()
        except Exception:
            pass
        self.stream = None
        self.pa = None
        print("🎤 Audio stopped")


# ═══════════════════════════════════════════════════════════════
#                      CALIBRATION STATUS CARD
# ═══════════════════════════════════════════════════════════════

class CalibrationStatusCard(QFrame):
    """Compact calibration status display with proper status detection."""
    
    calibrateClicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("calibrationCard")
        self._build_ui()
        self._apply_style()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        
        # Header row
        header = QHBoxLayout()
        header.setSpacing(6)
        
        title = QLabel("🎯 Calibration")
        title.setStyleSheet("color: white; font-weight: 600; font-size: 11px; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        
        self.status_badge = QLabel("...")
        header.addWidget(self.status_badge)
        layout.addLayout(header)
        
        # Info row - single line
        self.info_label = QLabel("X: -- | Y: -- | Mode: --")
        self.info_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 9px; background: transparent;")
        layout.addWidget(self.info_label)
        
        # Calibrate button
        self.calibrate_btn = QPushButton("🎯 Open Calibration")
        self.calibrate_btn.setObjectName("calibrateBtn")
        self.calibrate_btn.setCursor(Qt.PointingHandCursor)
        self.calibrate_btn.clicked.connect(self.calibrateClicked.emit)
        layout.addWidget(self.calibrate_btn)
        
        # Initial refresh
        self.refresh()
        
    def _apply_style(self):
        self.setStyleSheet("""
            #calibrationCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 212, 255, 0.08), stop:1 rgba(0, 180, 220, 0.03));
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 10px;
            }
            #calibrateBtn {
                background: rgba(0, 212, 255, 0.15);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
                color: #00d4ff;
                font-weight: 600;
                font-size: 10px;
                padding: 6px 10px;
            }
            #calibrateBtn:hover {
                background: rgba(0, 212, 255, 0.25);
                border-color: rgba(0, 212, 255, 0.5);
            }
        """)
    
    def _check_calibration_status(self):
        """
        Check if calibration is valid.
        Returns True if calibrated, False otherwise.
        """
        try:
            # Method 1: Use config.is_calibrated() if it exists and works
            if hasattr(config, 'is_calibrated') and callable(config.is_calibrated):
                result = config.is_calibrated()
                if result:
                    return True
            
            # Method 2: Check calibration margins directly
            if hasattr(config, 'get_calibration_margins') and callable(config.get_calibration_margins):
                margins = config.get_calibration_margins()
                if margins:
                    x_min = margins.get('x_min', 0)
                    x_max = margins.get('x_max', 0)
                    y_min = margins.get('y_min', 0)
                    y_max = margins.get('y_max', 0)
                    
                    # Valid calibration: has non-zero range
                    if x_max > x_min and y_max > y_min:
                        return True
                    if x_max > 0 and y_max > 0:
                        return True
            
            # Method 3: Check individual config attributes
            x_max = getattr(config, 'calibration_x_max', 0)
            y_max = getattr(config, 'calibration_y_max', 0)
            x_min = getattr(config, 'calibration_x_min', 0)
            y_min = getattr(config, 'calibration_y_min', 0)
            
            if x_max > 0 and y_max > 0:
                return True
            if x_max > x_min and y_max > y_min:
                return True
            
            # Method 4: Check screen mapping values
            screen_x_min = getattr(config, 'screen_x_min', None)
            screen_x_max = getattr(config, 'screen_x_max', None)
            if screen_x_min is not None and screen_x_max is not None:
                if screen_x_max > screen_x_min:
                    return True
            
            # Method 5: Check for calibration points
            if hasattr(config, 'calibration_points'):
                points = config.calibration_points
                if points and len(points) >= 4:
                    return True
            
        except Exception as e:
            print(f"⚠️ Calibration check error: {e}")
        
        return False
    
    def _get_calibration_margins(self):
        """Safely get calibration margins."""
        margins = {'x_min': 0, 'x_max': 0, 'y_min': 0, 'y_max': 0}
        
        try:
            # Try get_calibration_margins function
            if hasattr(config, 'get_calibration_margins') and callable(config.get_calibration_margins):
                result = config.get_calibration_margins()
                if result:
                    margins.update(result)
                    return margins
            
            # Try direct attributes
            margins['x_min'] = getattr(config, 'calibration_x_min', 0)
            margins['x_max'] = getattr(config, 'calibration_x_max', 0)
            margins['y_min'] = getattr(config, 'calibration_y_min', 0)
            margins['y_max'] = getattr(config, 'calibration_y_max', 0)
            
            # Check alternative naming
            if margins['x_max'] == 0:
                margins['x_min'] = getattr(config, 'cal_x_min', margins['x_min'])
                margins['x_max'] = getattr(config, 'cal_x_max', margins['x_max'])
                margins['y_min'] = getattr(config, 'cal_y_min', margins['y_min'])
                margins['y_max'] = getattr(config, 'cal_y_max', margins['y_max'])
            
            # Check screen mapping values
            if margins['x_max'] == 0:
                margins['x_min'] = getattr(config, 'screen_x_min', margins['x_min'])
                margins['x_max'] = getattr(config, 'screen_x_max', margins['x_max'])
                margins['y_min'] = getattr(config, 'screen_y_min', margins['y_min'])
                margins['y_max'] = getattr(config, 'screen_y_max', margins['y_max'])
                
        except Exception as e:
            print(f"⚠️ Error getting margins: {e}")
        
        return margins
        
    def _update_badge(self):
        """Update the status badge based on calibration state."""
        is_cal = self._check_calibration_status()
        
        if is_cal:
            self.status_badge.setText("✓ Calibrated")
            self.status_badge.setStyleSheet("""
                color: #00ff88; 
                font-weight: 600; 
                font-size: 9px;
                background: rgba(0, 255, 136, 0.15); 
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid rgba(0, 255, 136, 0.3);
            """)
            self.calibrate_btn.setText("🎯 Recalibrate")
        else:
            self.status_badge.setText("⚠ Not Set")
            self.status_badge.setStyleSheet("""
                color: #ffa500; 
                font-weight: 600; 
                font-size: 9px;
                background: rgba(255, 165, 0, 0.15); 
                padding: 2px 8px;
                border-radius: 4px;
                border: 1px solid rgba(255, 165, 0, 0.3);
            """)
            self.calibrate_btn.setText("🎯 Open Calibration")
    
    def refresh(self):
        """Refresh display from config."""
        self._update_badge()
        
        # Get margins safely
        margins = self._get_calibration_margins()
        
        # Get capture mode name
        modes = {0: "Manual", 1: "Stability", 2: "Countdown"}
        mode_val = getattr(config, 'calibration_capture_mode', 0)
        mode_name = modes.get(mode_val, "Manual")
        
        # Format display
        x_min = margins.get('x_min', 0)
        x_max = margins.get('x_max', 0)
        y_min = margins.get('y_min', 0)
        y_max = margins.get('y_max', 0)
        
        # Check if we have valid data
        has_data = (x_max > 0 or y_max > 0) or (x_max > x_min or y_max > y_min)
        
        if has_data:
            self.info_label.setText(
                f"X: {x_min:.0f}-{x_max:.0f} | "
                f"Y: {y_min:.0f}-{y_max:.0f} | "
                f"{mode_name}"
            )
            self.info_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 9px; background: transparent;")
        else:
            self.info_label.setText("No calibration data • Click to calibrate")
            self.info_label.setStyleSheet("color: rgba(255,200,100,0.6); font-size: 9px; background: transparent;")


# ═══════════════════════════════════════════════════════════════
#                      SETTINGS PANEL
# ═══════════════════════════════════════════════════════════════

class SettingsPanel(QWidget):
    """Settings panel that shares camera feed from hand_tracker."""

    # ── Signals for main window ──
    mirrorChanged = Signal(bool)
    faceBlurChanged = Signal(bool)
    faceFocusChanged = Signal(bool)
    scrollSpeedChanged = Signal(int)
    brightnessChanged = Signal(int)
    contrastChanged = Signal(int)
    saturationChanged = Signal(int)
    blurIntensityChanged = Signal(int)
    audioEnabledChanged = Signal(bool)
    audioVolumeChanged = Signal(int)
    audioMutedChanged = Signal(bool)
    noiseGateChanged = Signal(int)
    sensitivityChanged = Signal(int)
    mouseSpeedChanged = Signal(int)
    smoothChanged = Signal(float)
    cameraChanged = Signal(int)
    fpsChanged = Signal(int)
    openCalibrationRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

        # ═══════════════════════════════════════════════════════
        # STATE
        # ═══════════════════════════════════════════════════════
        self.camera_index = config.camera_index
        self.preview_enabled = False
        self.fps = 30
        self.brightness_val = config.brightness
        self.contrast_val = config.contrast
        self.saturation_val = config.saturation
        self.face_blur_on = config.face_blur
        self.face_focus_on = config.face_focus
        self.full_mask_on = False
        self.blur_intensity = config.blur_intensity
        self.last_frame = None

        # Thread-safe shared frame from hand_tracker
        self._shared_frame = None
        self._frame_lock = threading.Lock()

        # Audio
        self.audio_engine = AudioEngine()
        self.audio_enabled = False
        self.audio_devices = []
        self.noise_gate = config.noise_gate

        # Face cascade for preview-only face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # ═══════════════════════════════════════════════════════
        # STYLE
        # ═══════════════════════════════════════════════════════
        self.setStyleSheet(self._get_styles())

        # ═══════════════════════════════════════════════════════
        # MAIN LAYOUT
        # ═══════════════════════════════════════════════════════
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(12)

        # ═══════════════════════════════════════════════════════
        # LEFT PANEL (SCROLL)
        # ═══════════════════════════════════════════════════════
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(self._scroll_style())

        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left = QVBoxLayout(left_widget)
        left.setSpacing(12)
        left.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("⚙️ Settings")
        title.setObjectName("pageTitle")
        left.addWidget(title)

        subtitle = QLabel("Camera, Audio, Gestures, Privacy & more")
        subtitle.setObjectName("pageSubtitle")
        left.addWidget(subtitle)

        left.addSpacing(5)

        # ═══════════════════════════════════════════════════════
        # SECTION 1: CAMERA CONTROL
        # ═══════════════════════════════════════════════════════
        cam_card = self._create_card("📷 Camera Control")
        cam_layout = cam_card.layout()

        # Preview toggle
        cam_row = QHBoxLayout()
        self.camera_toggle = QCheckBox("Settings Preview")
        self.camera_toggle.setObjectName("toggleSwitch")
        self.camera_toggle.stateChanged.connect(self.toggle_preview)
        cam_row.addWidget(self.camera_toggle)
        cam_row.addStretch()
        self.cam_status = QLabel("⚫ OFF")
        self.cam_status.setObjectName("statusBadge")
        cam_row.addWidget(self.cam_status)
        cam_layout.addLayout(cam_row)

        # Shared camera info
        shared_info = QLabel("ℹ️ Preview uses hand tracker camera feed (no extra camera)")
        shared_info.setObjectName("infoText")
        shared_info.setStyleSheet("color: #58a6ff; font-size: 10px; background: transparent;")
        cam_layout.addWidget(shared_info)

        # Camera source
        cam_layout.addWidget(self._field_label("Camera Source"))
        src_row = QHBoxLayout()
        self.camera_select = QComboBox()
        self.camera_select.addItems([
            "📷  Camera 0 (Default)",
            "📷  Camera 1 (External)",
            "📷  Camera 2 (USB)"
        ])
        self.camera_select.setCurrentIndex(config.camera_index)
        self.camera_select.setObjectName("settingsCombo")
        self.camera_select.currentIndexChanged.connect(self.switch_camera)
        src_row.addWidget(self.camera_select)

        detect_btn = QPushButton("🔍")
        detect_btn.setObjectName("smallBtn")
        detect_btn.setFixedWidth(36)
        detect_btn.clicked.connect(self.detect_cameras)
        src_row.addWidget(detect_btn)
        cam_layout.addLayout(src_row)

        # FPS
        cam_layout.addWidget(self._field_label("Frame Rate"))
        fps_row = QHBoxLayout()
        self.fps_select = QComboBox()
        self.fps_select.addItems(["15 FPS", "24 FPS", "30 FPS", "60 FPS"])
        self.fps_select.setCurrentIndex(2)
        self.fps_select.setObjectName("settingsCombo")
        self.fps_select.currentIndexChanged.connect(self.switch_fps)
        fps_row.addWidget(self.fps_select)
        fps_row.addStretch()
        self.fps_display = QLabel("FPS: --")
        self.fps_display.setObjectName("fpsLabel")
        fps_row.addWidget(self.fps_display)
        cam_layout.addLayout(fps_row)

        # Resolution
        self.res_label = QLabel("Resolution: -- × --")
        self.res_label.setObjectName("infoText")
        cam_layout.addWidget(self.res_label)

        # Mirror
        self.mirror_toggle = QCheckBox("Mirror Camera (Flip Horizontal)")
        self.mirror_toggle.setObjectName("toggleSwitch")
        self.mirror_toggle.setChecked(config.mirror)
        self.mirror_toggle.stateChanged.connect(self._on_mirror_change)
        cam_layout.addWidget(self.mirror_toggle)

        left.addWidget(cam_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 2: AUDIO INPUT
        # ═══════════════════════════════════════════════════════
        audio_card = self._create_card("🎤 Audio Input")
        audio_layout = audio_card.layout()

        audio_row = QHBoxLayout()
        self.audio_toggle = QCheckBox("Microphone Power")
        self.audio_toggle.setObjectName("toggleSwitch")
        self.audio_toggle.stateChanged.connect(self.toggle_audio)
        audio_row.addWidget(self.audio_toggle)
        audio_row.addStretch()
        self.audio_status = QLabel("⚫ OFF")
        self.audio_status.setObjectName("statusBadge")
        audio_row.addWidget(self.audio_status)
        audio_layout.addLayout(audio_row)

        audio_layout.addWidget(self._field_label("Microphone Source"))
        mic_row = QHBoxLayout()
        self.mic_select = QComboBox()
        self.mic_select.setObjectName("settingsCombo")
        self.mic_select.addItem("🎤  Default Microphone")
        mic_row.addWidget(self.mic_select)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("smallBtn")
        refresh_btn.setFixedWidth(36)
        refresh_btn.clicked.connect(self.refresh_audio_devices)
        mic_row.addWidget(refresh_btn)
        audio_layout.addLayout(mic_row)

        audio_layout.addWidget(self._field_label("Input Level"))
        self.audio_meter = AudioMeter()
        audio_layout.addWidget(self.audio_meter)

        level_row = QHBoxLayout()
        self.audio_level_label = QLabel("Level: 0%")
        self.audio_level_label.setObjectName("infoText")
        level_row.addWidget(self.audio_level_label)
        level_row.addStretch()
        self.audio_db_label = QLabel("0 dB")
        self.audio_db_label.setObjectName("dbLabel")
        level_row.addWidget(self.audio_db_label)
        audio_layout.addLayout(level_row)

        self.volume_slider, self.volume_val_label = self._create_slider(
            audio_layout, "🔊 Input Volume", 0, 100,
            config.audio_volume, self._on_volume_change
        )

        self.mute_toggle = QCheckBox("🔇 Mute Microphone")
        self.mute_toggle.setObjectName("toggleSwitch")
        self.mute_toggle.setChecked(config.audio_muted)
        self.mute_toggle.stateChanged.connect(self._on_mute_change)
        audio_layout.addWidget(self.mute_toggle)

        self.audio_info = QLabel("Audio: Not started")
        self.audio_info.setObjectName("infoText")
        audio_layout.addWidget(self.audio_info)

        self.noise_gate_slider, self.noise_val_label = self._create_slider(
            audio_layout, "🚫 Noise Gate", 0, 50,
            config.noise_gate, self._on_noise_gate_change
        )

        test_row = QHBoxLayout()
        self.test_mic_btn = QPushButton("🎙️ Test Microphone")
        self.test_mic_btn.setObjectName("settingsBtn")
        self.test_mic_btn.clicked.connect(self.test_microphone)
        test_row.addWidget(self.test_mic_btn)
        test_row.addStretch()
        audio_layout.addLayout(test_row)

        left.addWidget(audio_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 3: IMAGE ADJUSTMENTS
        # ═══════════════════════════════════════════════════════
        img_card = self._create_card("🎨 Image Adjustments")
        img_layout = img_card.layout()

        self.brightness, self.brightness_val_label = self._create_slider(
            img_layout, "☀️ Brightness", 0, 100,
            config.brightness, self._on_brightness_change
        )
        self.contrast, self.contrast_val_label = self._create_slider(
            img_layout, "🔲 Contrast", 0, 100,
            config.contrast, self._on_contrast_change
        )
        self.saturation, self.saturation_val_label = self._create_slider(
            img_layout, "🌈 Saturation", 0, 100,
            config.saturation, self._on_saturation_change
        )

        reset_row = QHBoxLayout()
        reset_row.addStretch()
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setObjectName("smallBtn")
        reset_btn.clicked.connect(self.reset_adjustments)
        reset_row.addWidget(reset_btn)
        img_layout.addLayout(reset_row)

        left.addWidget(img_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 4: PRIVACY
        # ═══════════════════════════════════════════════════════
        privacy_card = self._create_card("🔒 Privacy & Face Detection")
        priv_layout = privacy_card.layout()

        self.face_blur_toggle = QCheckBox("Enable Face Blur")
        self.face_blur_toggle.setObjectName("toggleSwitch")
        self.face_blur_toggle.setChecked(config.face_blur)
        self.face_blur_toggle.stateChanged.connect(self._on_face_blur_change)
        priv_layout.addWidget(self.face_blur_toggle)

        self.blur_slider, self.blur_val_label = self._create_slider(
            priv_layout, "Blur Intensity", 5, 51,
            config.blur_intensity, self._on_blur_change
        )

        self.face_focus_toggle = QCheckBox("Face Focus (Blur Background)")
        self.face_focus_toggle.setObjectName("toggleSwitch")
        self.face_focus_toggle.setChecked(config.face_focus)
        self.face_focus_toggle.stateChanged.connect(self._on_face_focus_change)
        priv_layout.addWidget(self.face_focus_toggle)

        self.full_mask_toggle = QCheckBox("Debug Overlay Mask")
        self.full_mask_toggle.setObjectName("toggleSwitch")
        self.full_mask_toggle.stateChanged.connect(
            lambda s: setattr(self, 'full_mask_on', bool(s))
        )
        priv_layout.addWidget(self.full_mask_toggle)

        left.addWidget(privacy_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 5: GESTURE SETTINGS
        # ═══════════════════════════════════════════════════════
        gesture_card = self._create_card("✋ Gesture Settings")
        gest_layout = gesture_card.layout()

        self.sensitivity_slider, self.sens_val_label = self._create_slider(
            gest_layout, "🎯 Gesture Sensitivity", 1, 10,
            config.gesture_sensitivity, self._on_sensitivity_change
        )
        self.mouse_speed_slider, self.mouse_val_label = self._create_slider(
            gest_layout, "🖱️ Mouse Speed", 1, 20,
            config.mouse_speed, self._on_mouse_speed_change
        )
        self.scroll_speed_slider, self.scroll_val_label = self._create_slider(
            gest_layout, "📜 Scroll Speed", 1, 20,
            config.scroll_speed, self._on_scroll_speed_change
        )
        self.smooth_slider, self.smooth_val_label = self._create_slider(
            gest_layout, "🔄 Cursor Smoothing", 1, 10,
            int(config.smooth_factor * 10), self._on_smooth_change
        )

        left.addWidget(gesture_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 6: SHORTCUTS
        # ═══════════════════════════════════════════════════════
        shortcut_card = self._create_card("⌨️ Keyboard Shortcuts")
        short_layout = shortcut_card.layout()

        self.shortcuts_enabled_toggle = QCheckBox("Enable Shortcuts")
        self.shortcuts_enabled_toggle.setObjectName("toggleSwitch")
        self.shortcuts_enabled_toggle.setChecked(config.shortcuts_enabled)
        self.shortcuts_enabled_toggle.stateChanged.connect(
            self._on_shortcuts_toggle
        )
        short_layout.addWidget(self.shortcuts_enabled_toggle)

        self.show_shortcuts_btn = QPushButton("👁 Show / Hide Shortcuts")
        self.show_shortcuts_btn.setObjectName("settingsBtn")
        self.show_shortcuts_btn.clicked.connect(self.toggle_shortcuts)
        short_layout.addWidget(self.show_shortcuts_btn)

        self.shortcut_panel = QFrame()
        self.shortcut_panel.setMaximumHeight(0)
        self.shortcut_panel.setObjectName("shortcutPanel")
        sp_layout = QVBoxLayout(self.shortcut_panel)
        sp_layout.setContentsMargins(12, 8, 12, 8)
        sp_layout.setSpacing(6)

        shortcuts_list = [
            ("1", "Desktop Mode"), ("2", "Gaming Mode"), ("3", "Draw Mode"),
            ("C", "Clear Canvas"), ("M", "Toggle Mirror"), ("B", "Face Blur"),
            ("F", "Face Focus"), ("+", "↑ Scroll"), ("-", "↓ Scroll"),
            ("H", "Hide Tracker"), ("Q", "Quit"),
        ]

        for key, desc in shortcuts_list:
            row = QHBoxLayout()
            kl = QLabel(key)
            kl.setObjectName("keyBadge")
            kl.setFixedWidth(30)
            kl.setAlignment(Qt.AlignCenter)
            row.addWidget(kl)
            dl = QLabel(desc)
            dl.setObjectName("shortcutText")
            row.addWidget(dl)
            row.addStretch()
            sp_layout.addLayout(row)

        short_layout.addWidget(self.shortcut_panel)

        self.shortcut_anim = QPropertyAnimation(
            self.shortcut_panel, b"maximumHeight"
        )
        self.shortcut_anim.setDuration(300)
        self.shortcut_anim.setEasingCurve(QEasingCurve.OutCubic)

        left.addWidget(shortcut_card)

        # ═══════════════════════════════════════════════════════
        # SECTION 7: ABOUT
        # ═══════════════════════════════════════════════════════
        about_card = self._create_card("ℹ️ About Aurevix")
        about_layout = about_card.layout()
        about_text = QLabel(
            "Aurevix v1.0\n"
            "Built with: PySide6 · OpenCV · MediaPipe\n"
            "© 2026 Aurevix Team"
        )
        about_text.setObjectName("aboutText")
        about_layout.addWidget(about_text)
        left.addWidget(about_card)

        left.addStretch()
        scroll.setWidget(left_widget)
        main.addWidget(scroll, 42)

        # ═══════════════════════════════════════════════════════
        # RIGHT PANEL — PREVIEW (FIXED LAYOUT)
        # ═══════════════════════════════════════════════════════
        right_panel = QFrame()
        right_panel.setObjectName("previewCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(12, 12, 12, 12)

        # ─── Preview Header ───
        ph = QHBoxLayout()
        pt = QLabel("📺 Live Preview")
        pt.setObjectName("previewTitle")
        ph.addWidget(pt)
        ph.addStretch()
        self.preview_live = QLabel("⚫ OFF")
        self.preview_live.setObjectName("liveIndicator")
        ph.addWidget(self.preview_live)
        right_layout.addLayout(ph)

        # Source indicator
        self.source_label = QLabel("📡 Source: Hand Tracker (shared)")
        self.source_label.setObjectName("infoText")
        self.source_label.setStyleSheet("color: #58a6ff; font-size: 10px;")
        right_layout.addWidget(self.source_label)

        # ─── Camera Preview Container ───
        self.preview_container = QFrame()
        self.preview_container.setObjectName("previewContainer")
        self.preview_container.setStyleSheet("""
            #previewContainer {
                background: #000000;
                border-radius: 10px;
                border: 2px solid rgba(48, 54, 61, 0.5);
            }
        """)
        self.preview_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_container.setMinimumHeight(180)
        self.preview_container.setMaximumHeight(320)
        
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        
        self.camera_label = QLabel()
        self.camera_label.setObjectName("cameraDisplay")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera_label.setText("📷 Preview Off\n\nEnable 'Settings Preview'")
        self.camera_label.setStyleSheet("""
            #cameraDisplay {
                background: transparent;
                color: #8b949e;
                font-size: 12px;
            }
        """)
        preview_layout.addWidget(self.camera_label)
        
        right_layout.addWidget(self.preview_container)

        # ─── Camera Info Row ───
        cam_info_row = QHBoxLayout()
        self.cam_info = QLabel("Waiting for feed...")
        self.cam_info.setObjectName("camInfo")
        cam_info_row.addWidget(self.cam_info)
        cam_info_row.addStretch()
        self.face_info = QLabel("Face: --")
        self.face_info.setObjectName("faceInfo")
        cam_info_row.addWidget(self.face_info)
        right_layout.addLayout(cam_info_row)

        # ─── Quick Controls ───
        qr = QHBoxLayout()
        qr.setSpacing(6)
        
        self.quick_start = QPushButton("▶️ On")
        self.quick_start.setObjectName("greenBtn")
        self.quick_start.clicked.connect(lambda: self.camera_toggle.setChecked(True))
        qr.addWidget(self.quick_start)

        self.quick_stop = QPushButton("⏹ Off")
        self.quick_stop.setObjectName("redBtn")
        self.quick_stop.setEnabled(False)
        self.quick_stop.clicked.connect(lambda: self.camera_toggle.setChecked(False))
        qr.addWidget(self.quick_stop)

        self.quick_screenshot = QPushButton("📸")
        self.quick_screenshot.setObjectName("smallBtn")
        self.quick_screenshot.setFixedWidth(36)
        self.quick_screenshot.setEnabled(False)
        self.quick_screenshot.clicked.connect(self.take_screenshot)
        qr.addWidget(self.quick_screenshot)
        
        qr.addStretch()
        right_layout.addLayout(qr)

        # ─── Separator ───
        right_layout.addWidget(self._separator())

        # ─── Audio Monitor (Compact) ───
        audio_preview = QFrame()
        audio_preview.setObjectName("compactCard")
        ap_layout = QVBoxLayout(audio_preview)
        ap_layout.setSpacing(4)
        ap_layout.setContentsMargins(10, 8, 10, 8)

        ap_header = QHBoxLayout()
        ap_title = QLabel("🎤 Audio")
        ap_title.setStyleSheet("color: #e6edf3; font-weight: 600; font-size: 11px;")
        ap_header.addWidget(ap_title)
        ap_header.addStretch()
        self.audio_preview_status = QLabel("⚫ OFF")
        self.audio_preview_status.setStyleSheet("color: #8b949e; font-size: 10px; font-weight: bold;")
        ap_header.addWidget(self.audio_preview_status)
        ap_layout.addLayout(ap_header)

        self.preview_meter = AudioMeter()
        ap_layout.addWidget(self.preview_meter)

        ai_row = QHBoxLayout()
        self.preview_level = QLabel("Level: --")
        self.preview_level.setStyleSheet("color: #8b949e; font-size: 10px;")
        ai_row.addWidget(self.preview_level)
        ai_row.addStretch()
        self.preview_db = QLabel("-- dB")
        self.preview_db.setStyleSheet("color: #58a6ff; font-size: 10px; font-weight: 600;")
        ai_row.addWidget(self.preview_db)
        ap_layout.addLayout(ai_row)

        self.preview_device = QLabel("Device: None")
        self.preview_device.setStyleSheet("font-size: 9px; color: #6e7681;")
        ap_layout.addWidget(self.preview_device)

        right_layout.addWidget(audio_preview)

        # ─── Separator ───
        right_layout.addWidget(self._separator())

        # ─── Calibration Card ───
        self.calibration_card = CalibrationStatusCard()
        self.calibration_card.calibrateClicked.connect(self._on_calibrate_clicked)
        right_layout.addWidget(self.calibration_card)

        # ─── Separator ───
        right_layout.addWidget(self._separator())

        # ─── Live Config (Compact) ───
        config_card = QFrame()
        config_card.setObjectName("compactCard")
        cl = QVBoxLayout(config_card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(4)

        ct = QLabel("📊 Live Config")
        ct.setStyleSheet("color: #e6edf3; font-weight: 600; font-size: 11px;")
        cl.addWidget(ct)

        self.config_display = QLabel("Loading...")
        self.config_display.setStyleSheet("color: #8b949e; font-size: 10px;")
        self.config_display.setWordWrap(True)
        cl.addWidget(self.config_display)

        right_layout.addWidget(config_card)

        main.addWidget(right_panel, 58)

        # ═══════════════════════════════════════════════════════
        # TIMERS
        # ═══════════════════════════════════════════════════════
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_preview)

        self.fps_counter = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps_display)
        self.fps_timer.start(1000)

        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self._update_audio_level)

        self.config_timer = QTimer()
        self.config_timer.timeout.connect(self._update_config_display)
        self.config_timer.start(500)

        self.calibration_timer = QTimer()
        self.calibration_timer.timeout.connect(self._refresh_calibration_status)
        self.calibration_timer.start(2000)

        QTimer.singleShot(500, self.refresh_audio_devices)

    # ═══════════════════════════════════════════════════════════════
    #    CALIBRATION NAVIGATION
    # ═══════════════════════════════════════════════════════════════

    def _on_calibrate_clicked(self):
        """Handle calibration button click - emit signal to main window."""
        print("🎯 Calibration button clicked - emitting signal")
        self.openCalibrationRequested.emit()

    # ═══════════════════════════════════════════════════════════════
    #    HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _separator(self):
        """Create a visual separator line."""
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.06);")
        return sep

    def _scroll_style(self):
        return """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.03);
                width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(96,165,250,0.3);
                border-radius: 3px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(96,165,250,0.5);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0; }
        """

    # ═══════════════════════════════════════════════════════════════
    #    SHARED FRAME API
    # ═══════════════════════════════════════════════════════════════

    def receive_frame(self, frame):
        """Called by hand_tracker to push each raw camera frame."""
        with self._frame_lock:
            self._shared_frame = frame.copy()

    def _get_shared_frame(self):
        """Thread-safe read of the latest shared frame."""
        with self._frame_lock:
            if self._shared_frame is not None:
                return self._shared_frame.copy()
            return None

    # ═══════════════════════════════════════════════════════════════
    #                   CARD BUILDERS
    # ═══════════════════════════════════════════════════════════════

    def _create_card(self, title_text):
        card = QFrame()
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.08);")
        layout.addWidget(sep)

        return card

    def _field_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _create_slider(self, parent_layout, label_text, min_val, max_val,
                       default_val, callback=None):
        if label_text:
            parent_layout.addWidget(self._field_label(label_text))

        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setObjectName("settingsSlider")
        row.addWidget(slider)

        val_label = QLabel(str(default_val))
        val_label.setObjectName("sliderValue")
        val_label.setFixedWidth(36)
        val_label.setAlignment(Qt.AlignCenter)
        row.addWidget(val_label)

        def handle(v):
            val_label.setText(str(v))
            if callback:
                callback(v)

        slider.valueChanged.connect(handle)
        parent_layout.addLayout(row)
        return slider, val_label

    # ═══════════════════════════════════════════════════════════════
    #          PREVIEW CONTROLS
    # ═══════════════════════════════════════════════════════════════

    def toggle_preview(self, state):
        if state:
            self.start_preview()
        else:
            self.stop_preview()

    def start_preview(self):
        """Start preview display using shared tracker frames."""
        self.preview_enabled = True
        self.preview_timer.start(1000 // self.fps)

        self.cam_status.setText("🟢 PREVIEW")
        self.cam_status.setStyleSheet(
            "color:#3fb950; background:rgba(63,185,80,0.1);"
            "padding:4px 12px; border-radius:12px; "
            "font-weight:bold; font-size:11px;"
        )
        self.preview_live.setText("🔴 LIVE")
        self.preview_live.setStyleSheet("color:#f85149; font-weight:bold; font-size:11px;")
        self.quick_start.setEnabled(False)
        self.quick_stop.setEnabled(True)
        self.quick_screenshot.setEnabled(True)
        self.cam_info.setText("Receiving from tracker...")
        print("📺 Settings preview started")

    def stop_preview(self):
        """Stop preview display."""
        self.preview_enabled = False
        self.preview_timer.stop()

        self.cam_status.setText("⚫ OFF")
        self.cam_status.setStyleSheet(
            "color:#8b949e; background:rgba(139,148,158,0.1);"
            "padding:4px 12px; border-radius:12px; "
            "font-weight:bold; font-size:11px;"
        )
        self.preview_live.setText("⚫ OFF")
        self.preview_live.setStyleSheet("color:#8b949e; font-weight:bold; font-size:11px;")
        self.camera_label.clear()
        self.camera_label.setText("📷 Preview Off\n\nEnable 'Settings Preview'")
        self.quick_start.setEnabled(True)
        self.quick_stop.setEnabled(False)
        self.quick_screenshot.setEnabled(False)
        self.cam_info.setText("Preview stopped")
        self.fps_display.setText("FPS: --")
        self.face_info.setText("Face: --")
        print("📺 Settings preview stopped")

    def switch_camera(self, index):
        config.camera_index = index
        config.save_config()
        self.cameraChanged.emit(index)

    def switch_fps(self, index):
        fps_map = {0: 15, 1: 24, 2: 30, 3: 60}
        self.fps = fps_map.get(index, 30)
        config.fps_limit = self.fps
        config.save_config()
        self.fpsChanged.emit(self.fps)
        if self.preview_enabled:
            self.preview_timer.start(1000 // self.fps)

    def detect_cameras(self):
        available = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()

        if available:
            QMessageBox.information(
                self, "Camera Detection",
                f"✅ Found {len(available)} camera(s): {available}"
            )
        else:
            QMessageBox.warning(self, "Camera Detection", "❌ No cameras found!")

    def take_screenshot(self):
        if self.last_frame is not None:
            os.makedirs("screenshots", exist_ok=True)
            fn = f"screenshots/settings_{int(time.time())}.png"
            cv2.imwrite(fn, self.last_frame)
            self.quick_screenshot.setText("✅")
            QTimer.singleShot(2000, lambda: self.quick_screenshot.setText("📸"))

    # ═══════════════════════════════════════════════════════════════
    #    PREVIEW UPDATE — RESPONSIVE SIZING
    # ═══════════════════════════════════════════════════════════════

    def _update_preview(self):
        """Read shared frame and display with effects, responsive to container size."""
        if not self.preview_enabled:
            return

        frame = self._get_shared_frame()
        if frame is None:
            self.cam_info.setText("⏳ Waiting for feed...")
            self.face_info.setText("Face: --")
            self.face_info.setStyleSheet("color:#f9a825; font-size:10px;")
            return

        self.fps_counter += 1
        fh, fw = frame.shape[:2]
        self.res_label.setText(f"Resolution: {fw} × {fh}")
        self.cam_info.setText(f"Cam {config.camera_index} · {fw}×{fh}")

        # Work on a COPY
        preview = frame.copy()

        # Mirror
        if self.mirror_toggle.isChecked():
            preview = cv2.flip(preview, 1)

        # Brightness & Contrast
        if self.brightness_val != 50 or self.contrast_val != 50:
            alpha = 1 + (self.contrast_val - 50) / 50.0
            beta = (self.brightness_val - 50) * 2
            preview = cv2.convertScaleAbs(preview, alpha=alpha, beta=beta)

        # Saturation
        if self.saturation_val != 50:
            hsv = cv2.cvtColor(preview, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] *= self.saturation_val / 50.0
            hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
            preview = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # Face detection
        gray = cv2.cvtColor(preview, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        fc = len(faces)

        if fc > 0:
            self.face_info.setText(f"Face: {fc}")
            self.face_info.setStyleSheet("color:#3fb950; font-size:10px; font-weight:600;")
        else:
            self.face_info.setText("Face: 0")
            self.face_info.setStyleSheet("color:#8b949e; font-size:10px;")

        # Face Focus
        if self.face_focus_on and fc > 0:
            blurred = cv2.GaussianBlur(preview, (31, 31), 0)
            for (x, y, w, h) in faces:
                mask = np.zeros(preview.shape[:2], dtype=np.uint8)
                cv2.ellipse(mask, (x + w // 2, y + h // 2),
                           (w // 2 + 20, h // 2 + 20), 0, 0, 360, 255, -1)
                mask = cv2.GaussianBlur(mask, (21, 21), 0)
                m3d = mask[:, :, np.newaxis] / 255.0
                preview = (preview * m3d + blurred * (1 - m3d)).astype(np.uint8)

        # Face Blur
        elif self.face_blur_on and fc > 0:
            bk = self.blur_intensity | 1
            for (x, y, w, h) in faces:
                preview[y:y + h, x:x + w] = cv2.GaussianBlur(
                    preview[y:y + h, x:x + w], (bk, bk), 0
                )

        # Debug overlay
        if self.full_mask_on:
            overlay = np.full_like(preview, (15, 15, 25))
            preview = cv2.addWeighted(overlay, 0.35, preview, 0.65, 0)
            for i in range(0, fw, 40):
                cv2.line(preview, (i, 0), (i, fh), (30, 30, 45), 1)
            for i in range(0, fh, 40):
                cv2.line(preview, (0, i), (fw, i), (30, 30, 45), 1)

        # Draw face boxes
        if not self.face_blur_on and not self.face_focus_on:
            for (x, y, w, h) in faces:
                cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

        self.last_frame = preview.copy()

        # Convert to Qt pixmap and scale to fit container
        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        
        # Get the available size from the camera label
        available_size = self.camera_label.size()
        
        pix = QPixmap.fromImage(img).scaled(
            available_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.camera_label.setPixmap(pix)

    def _update_fps_display(self):
        if self.preview_enabled:
            self.fps_display.setText(f"FPS: {self.fps_counter}")
            self.fps_counter = 0

    # ═══════════════════════════════════════════════════════════════
    #                   AUDIO CONTROLS
    # ═══════════════════════════════════════════════════════════════

    def toggle_audio(self, state):
        if state:
            self.start_audio()
        else:
            self.stop_audio()
        self.audioEnabledChanged.emit(bool(state))

    def start_audio(self):
        device_idx = self.mic_select.currentIndex()
        actual_idx = None

        if self.audio_devices and device_idx < len(self.audio_devices):
            actual_idx = self.audio_devices[device_idx].get('index')

        success = self.audio_engine.start(device_index=actual_idx)

        if success:
            self.audio_enabled = True
            config.audio_enabled = True
            config.save_config()
            self.audio_timer.start(50)

            self.audio_status.setText("🟢 ON")
            self.audio_status.setStyleSheet(
                "color:#3fb950; background:rgba(63,185,80,0.1);"
                "padding:4px 12px; border-radius:12px; font-weight:bold; font-size:11px;"
            )
            self.audio_preview_status.setText("🔴 LIVE")
            self.audio_preview_status.setStyleSheet("color:#f85149; font-weight:bold; font-size:10px;")

            device_name = "Default"
            if self.audio_devices and device_idx < len(self.audio_devices):
                device_name = self.audio_devices[device_idx].get('name', 'Unknown')[:20]

            self.audio_info.setText("Audio: Active")
            self.preview_device.setText(f"Device: {device_name}")
        else:
            self.audio_toggle.setChecked(False)
            self.audio_status.setText("❌ FAILED")
            self.audio_status.setStyleSheet(
                "color:#f85149; background:rgba(248,81,73,0.1);"
                "padding:4px 12px; border-radius:12px; font-weight:bold; font-size:11px;"
            )

    def stop_audio(self):
        self.audio_enabled = False
        config.audio_enabled = False
        config.save_config()
        self.audio_timer.stop()
        self.audio_engine.stop()

        self.audio_status.setText("⚫ OFF")
        self.audio_status.setStyleSheet(
            "color:#8b949e; background:rgba(139,148,158,0.1);"
            "padding:4px 12px; border-radius:12px; font-weight:bold; font-size:11px;"
        )
        self.audio_preview_status.setText("⚫ OFF")
        self.audio_preview_status.setStyleSheet("color:#8b949e; font-weight:bold; font-size:10px;")
        self.audio_meter.set_level(0)
        self.preview_meter.set_level(0)
        self.audio_level_label.setText("Level: 0%")
        self.audio_db_label.setText("0 dB")
        self.preview_level.setText("Level: --")
        self.preview_db.setText("-- dB")
        self.audio_info.setText("Audio: Not started")
        self.preview_device.setText("Device: None")

    def refresh_audio_devices(self):
        self.audio_devices = self.audio_engine.get_devices()
        self.mic_select.clear()

        if self.audio_devices:
            for dev in self.audio_devices:
                name = dev['name']
                if len(name) > 35:
                    name = name[:32] + "..."
                self.mic_select.addItem(f"🎤  {name}")
        else:
            self.mic_select.addItem("🎤  Default Microphone")

    def test_microphone(self):
        if self.audio_enabled:
            QMessageBox.information(self, "Test", "🎤 Mic working! Watch the level meter.")
        else:
            result = self.audio_engine.start()
            if result:
                max_level = 0
                for _ in range(20):
                    level = self.audio_engine.read_level()
                    max_level = max(max_level, level)
                    time.sleep(0.05)
                self.audio_engine.stop()

                if max_level > 0.01:
                    QMessageBox.information(self, "Test", f"✅ Mic works! Peak: {int(max_level * 100)}%")
                else:
                    QMessageBox.warning(self, "Test", "⚠️ Very low audio!")
            else:
                QMessageBox.warning(self, "Test", "❌ Could not open mic!")

    def _update_audio_level(self):
        if not self.audio_enabled:
            return

        level = self.audio_engine.read_level()
        if level * 100 < self.noise_gate:
            level = 0.0

        self.audio_meter.set_level(level)
        self.preview_meter.set_level(level)

        percent = int(level * 100)
        self.audio_level_label.setText(f"Level: {percent}%")
        self.preview_level.setText(f"Level: {percent}%")

        if level > 0:
            db = 20 * math.log10(max(level, 0.001))
            db_text = f"{db:.1f} dB"
        else:
            db_text = "-∞ dB"

        self.audio_db_label.setText(db_text)
        self.preview_db.setText(db_text)

    # ═══════════════════════════════════════════════════════════════
    #     ALL CALLBACKS
    # ═══════════════════════════════════════════════════════════════

    def _on_brightness_change(self, v):
        self.brightness_val = v
        config.brightness = v
        config.save_config()
        self.brightnessChanged.emit(v)

    def _on_contrast_change(self, v):
        self.contrast_val = v
        config.contrast = v
        config.save_config()
        self.contrastChanged.emit(v)

    def _on_saturation_change(self, v):
        self.saturation_val = v
        config.saturation = v
        config.save_config()
        self.saturationChanged.emit(v)

    def _on_blur_change(self, v):
        self.blur_intensity = v
        config.blur_intensity = v
        config.save_config()
        self.blurIntensityChanged.emit(v)

    def _on_mirror_change(self, state):
        config.mirror = bool(state)
        config.save_config()
        self.mirrorChanged.emit(config.mirror)

    def _on_face_blur_change(self, state):
        self.face_blur_on = bool(state)
        config.face_blur = bool(state)
        config.save_config()
        self.faceBlurChanged.emit(config.face_blur)

    def _on_face_focus_change(self, state):
        self.face_focus_on = bool(state)
        config.face_focus = bool(state)
        config.save_config()
        self.faceFocusChanged.emit(config.face_focus)

    def _on_sensitivity_change(self, v):
        config.gesture_sensitivity = v
        config.save_config()
        self.sensitivityChanged.emit(v)

    def _on_mouse_speed_change(self, v):
        config.mouse_speed = v
        config.save_config()
        self.mouseSpeedChanged.emit(v)

    def _on_scroll_speed_change(self, v):
        config.scroll_speed = v
        config.save_config()
        self.scrollSpeedChanged.emit(v)

    def _on_smooth_change(self, v):
        config.smooth_factor = v / 10.0
        config.save_config()
        self.smoothChanged.emit(config.smooth_factor)

    def _on_volume_change(self, v):
        self.audio_engine.volume = v / 100.0
        config.audio_volume = v
        config.save_config()
        self.audioVolumeChanged.emit(v)

    def _on_mute_change(self, state):
        self.audio_engine.muted = bool(state)
        config.audio_muted = bool(state)
        config.save_config()
        self.audioMutedChanged.emit(config.audio_muted)
        if state:
            self.audio_meter.set_level(0)
            self.preview_meter.set_level(0)

    def _on_noise_gate_change(self, v):
        self.noise_gate = v
        config.noise_gate = v
        config.save_config()
        self.noiseGateChanged.emit(v)

    def _on_shortcuts_toggle(self, state):
        config.shortcuts_enabled = bool(state)
        config.save_config()

    def reset_adjustments(self):
        self.brightness.setValue(50)
        self.contrast.setValue(50)
        self.saturation.setValue(50)
        config.brightness = 50
        config.contrast = 50
        config.saturation = 50
        config.save_config()

    def toggle_shortcuts(self):
        target = self.shortcut_panel.layout().sizeHint().height() + 20
        if self.shortcut_panel.maximumHeight() == 0:
            self.shortcut_anim.setStartValue(0)
            self.shortcut_anim.setEndValue(target)
        else:
            self.shortcut_anim.setStartValue(target)
            self.shortcut_anim.setEndValue(0)
        self.shortcut_anim.start()

    # ═══════════════════════════════════════════════════════════════
    #              CONFIG DISPLAY UPDATE
    # ═══════════════════════════════════════════════════════════════

    def _update_config_display(self):
        mirror = "✓" if config.mirror else "✗"
        blur = "✓" if config.face_blur else "✗"
        focus = "✓" if config.face_focus else "✗"
        feed = "✅" if self._shared_frame is not None else "❌"

        self.config_display.setText(
            f"Mirror:{mirror} Blur:{blur} Focus:{focus} | "
            f"Sens:{config.gesture_sensitivity} Speed:{config.mouse_speed} | "
            f"Mode:{mode_manager.mode} Feed:{feed}"
        )

    def _refresh_calibration_status(self):
        if hasattr(self, 'calibration_card'):
            self.calibration_card.refresh()

    # ═══════════════════════════════════════════════════════════════
    #           SYNC UI TO CONFIG
    # ═══════════════════════════════════════════════════════════════

    def _sync_ui_to_config(self):
        """Sync all UI elements to current config values."""
        
        self.mirror_toggle.blockSignals(True)
        self.mirror_toggle.setChecked(config.mirror)
        self.mirror_toggle.blockSignals(False)

        self.face_blur_toggle.blockSignals(True)
        self.face_blur_toggle.setChecked(config.face_blur)
        self.face_blur_toggle.blockSignals(False)

        self.face_focus_toggle.blockSignals(True)
        self.face_focus_toggle.setChecked(config.face_focus)
        self.face_focus_toggle.blockSignals(False)

        self.blur_slider.blockSignals(True)
        self.blur_slider.setValue(config.blur_intensity)
        self.blur_slider.blockSignals(False)
        self.blur_val_label.setText(str(config.blur_intensity))

        self.brightness.blockSignals(True)
        self.brightness.setValue(config.brightness)
        self.brightness.blockSignals(False)
        self.brightness_val_label.setText(str(config.brightness))

        self.contrast.blockSignals(True)
        self.contrast.setValue(config.contrast)
        self.contrast.blockSignals(False)
        self.contrast_val_label.setText(str(config.contrast))

        self.saturation.blockSignals(True)
        self.saturation.setValue(config.saturation)
        self.saturation.blockSignals(False)
        self.saturation_val_label.setText(str(config.saturation))

        self.scroll_speed_slider.blockSignals(True)
        self.scroll_speed_slider.setValue(config.scroll_speed)
        self.scroll_speed_slider.blockSignals(False)
        self.scroll_val_label.setText(str(config.scroll_speed))

        self.sensitivity_slider.blockSignals(True)
        self.sensitivity_slider.setValue(config.gesture_sensitivity)
        self.sensitivity_slider.blockSignals(False)
        self.sens_val_label.setText(str(config.gesture_sensitivity))

        self.mouse_speed_slider.blockSignals(True)
        self.mouse_speed_slider.setValue(config.mouse_speed)
        self.mouse_speed_slider.blockSignals(False)
        self.mouse_val_label.setText(str(config.mouse_speed))

        self.smooth_slider.blockSignals(True)
        self.smooth_slider.setValue(int(config.smooth_factor * 10))
        self.smooth_slider.blockSignals(False)
        self.smooth_val_label.setText(str(int(config.smooth_factor * 10)))

        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(config.audio_volume)
        self.volume_slider.blockSignals(False)
        self.volume_val_label.setText(str(config.audio_volume))

        self.mute_toggle.blockSignals(True)
        self.mute_toggle.setChecked(config.audio_muted)
        self.mute_toggle.blockSignals(False)

        self.noise_gate_slider.blockSignals(True)
        self.noise_gate_slider.setValue(config.noise_gate)
        self.noise_gate_slider.blockSignals(False)
        self.noise_val_label.setText(str(config.noise_gate))

        self.shortcuts_enabled_toggle.blockSignals(True)
        self.shortcuts_enabled_toggle.setChecked(config.shortcuts_enabled)
        self.shortcuts_enabled_toggle.blockSignals(False)

        if config.camera_index < self.camera_select.count():
            self.camera_select.blockSignals(True)
            self.camera_select.setCurrentIndex(config.camera_index)
            self.camera_select.blockSignals(False)

        fps_map = {15: 0, 24: 1, 30: 2, 60: 3}
        fps_idx = fps_map.get(config.fps_limit, 2)
        self.fps_select.blockSignals(True)
        self.fps_select.setCurrentIndex(fps_idx)
        self.fps_select.blockSignals(False)

        self.brightness_val = config.brightness
        self.contrast_val = config.contrast
        self.saturation_val = config.saturation
        self.face_blur_on = config.face_blur
        self.face_focus_on = config.face_focus
        self.blur_intensity = config.blur_intensity
        self.noise_gate = config.noise_gate
        self.audio_engine.volume = config.audio_volume / 100.0
        self.audio_engine.muted = config.audio_muted

        self._refresh_calibration_status()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_ui_to_config()

    # ═══════════════════════════════════════════════════════════════
    #                   STYLES
    # ═══════════════════════════════════════════════════════════════

    def _get_styles(self):
        return """
        QLabel {
            color: #e6edf3;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            font-size: 12px;
            background: transparent;
        }
        #pageTitle {
            font-size: 24px; font-weight: 700;
            color: #ffffff;
        }
        #pageSubtitle {
            font-size: 12px; color: #8b949e;
        }
        #settingsCard {
            background: rgba(22, 27, 34, 0.75);
            border-radius: 16px;
            border: 1px solid rgba(48, 54, 61, 0.6);
        }
        #cardTitle {
            font-size: 14px; font-weight: 700;
            color: #e6edf3;
        }
        #fieldLabel {
            font-size: 11px; font-weight: 600;
            color: #8b949e; padding: 4px 0 0 2px;
        }
        #toggleSwitch {
            color: #c9d1d9; font-size: 12px;
            spacing: 8px;
        }
        #toggleSwitch::indicator {
            width: 16px; height: 16px; border-radius: 4px;
            border: 2px solid rgba(139, 148, 158, 0.5);
            background: rgba(22, 27, 34, 0.8);
        }
        #toggleSwitch::indicator:checked {
            background: rgba(56, 139, 253, 0.6);
            border: 2px solid rgba(56, 139, 253, 0.8);
        }
        #settingsCombo {
            padding: 8px 12px; border-radius: 8px;
            background: rgba(22, 27, 34, 0.9);
            color: #e6edf3;
            border: 1px solid rgba(48, 54, 61, 0.8);
            font-size: 12px;
        }
        #settingsCombo:focus {
            border: 1px solid rgba(56, 139, 253, 0.5);
        }
        #settingsCombo QAbstractItemView {
            background: #161b22; color: #e6edf3;
            border: 1px solid rgba(48, 54, 61, 0.8);
            selection-background-color: rgba(56, 139, 253, 0.3);
        }
        #settingsSlider::groove:horizontal {
            height: 5px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
        }
        #settingsSlider::handle:horizontal {
            width: 14px; height: 14px;
            background: #58a6ff; border-radius: 7px;
            margin: -5px 0;
            border: 2px solid rgba(56, 139, 253, 0.3);
        }
        #settingsSlider::handle:horizontal:hover {
            background: #79c0ff;
        }
        #settingsSlider::sub-page:horizontal {
            background: rgba(56, 139, 253, 0.4);
            border-radius: 2px;
        }
        #sliderValue {
            color: #58a6ff; font-weight: 700; font-size: 12px;
            background: rgba(56, 139, 253, 0.08);
            border-radius: 6px; padding: 3px;
        }
        #settingsBtn {
            padding: 8px 14px; border-radius: 8px;
            background: rgba(48, 54, 61, 0.6);
            border: 1px solid rgba(48, 54, 61, 0.8);
            color: #c9d1d9; font-weight: 600; font-size: 12px;
        }
        #settingsBtn:hover {
            background: rgba(56, 139, 253, 0.15);
            color: #58a6ff;
        }
        #smallBtn {
            padding: 6px 10px; border-radius: 6px;
            background: rgba(48, 54, 61, 0.5);
            border: 1px solid rgba(48, 54, 61, 0.7);
            color: #8b949e; font-size: 11px;
        }
        #smallBtn:hover {
            background: rgba(56, 139, 253, 0.15);
            color: #58a6ff;
        }
        #greenBtn {
            padding: 6px 12px; border-radius: 6px;
            background: rgba(34, 197, 94, 0.2);
            border: 1px solid rgba(34, 197, 94, 0.4);
            color: #3fb950; font-weight: 700; font-size: 11px;
        }
        #greenBtn:hover { background: rgba(34, 197, 94, 0.35); }
        #greenBtn:disabled {
            background: rgba(50,50,50,0.3);
            border-color: rgba(50,50,50,0.3);
            color: #484f58;
        }
        #redBtn {
            padding: 6px 12px; border-radius: 6px;
            background: rgba(248, 81, 73, 0.2);
            border: 1px solid rgba(248, 81, 73, 0.4);
            color: #f85149; font-weight: 700; font-size: 11px;
        }
        #redBtn:hover { background: rgba(248, 81, 73, 0.35); }
        #redBtn:disabled {
            background: rgba(50,50,50,0.3);
            border-color: rgba(50,50,50,0.3);
            color: #484f58;
        }
        #previewCard {
            background: rgba(22, 27, 34, 0.6);
            border-radius: 16px;
            border: 1px solid rgba(48, 54, 61, 0.5);
        }
        #previewTitle {
            font-size: 14px; font-weight: 700;
            color: #e6edf3;
        }
        #liveIndicator {
            font-size: 10px; font-weight: bold;
            color: #8b949e;
        }
        #camInfo, #faceInfo {
            color: #8b949e; font-size: 10px;
        }
        #fpsLabel {
            color: #3fb950; font-weight: 700;
            font-size: 11px;
        }
        #infoText {
            color: #8b949e; font-size: 10px;
        }
        #statusBadge {
            color: #8b949e;
            background: rgba(139, 148, 158, 0.1);
            padding: 4px 10px; border-radius: 10px;
            font-weight: bold; font-size: 10px;
        }
        #compactCard {
            background: rgba(22, 27, 34, 0.6);
            border-radius: 10px;
            border: 1px solid rgba(48, 54, 61, 0.4);
        }
        #dbLabel {
            color: #58a6ff; font-weight: 600;
            font-size: 10px;
        }
        #shortcutPanel {
            background: rgba(13, 17, 23, 0.8);
            border-radius: 10px;
            border: 1px solid rgba(48, 54, 61, 0.4);
        }
        #keyBadge {
            background: rgba(56, 139, 253, 0.15);
            color: #58a6ff; font-weight: 800; font-size: 11px;
            border-radius: 5px; padding: 3px;
            border: 1px solid rgba(56, 139, 253, 0.3);
        }
        #shortcutText {
            color: #c9d1d9; font-size: 11px;
        }
        #aboutText {
            color: #8b949e; font-size: 11px;
        }
        """

    # ═══════════════════════════════════════════════════════════════
    #                   CLEANUP
    # ═══════════════════════════════════════════════════════════════

    def cleanup(self):
        """Stop everything on shutdown."""
        self.preview_timer.stop()
        self.fps_timer.stop()
        self.audio_timer.stop()
        self.config_timer.stop()
        self.calibration_timer.stop()
        self.audio_engine.stop()
        print("⚙️ Settings panel cleaned up")
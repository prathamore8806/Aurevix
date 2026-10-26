# dashboard_page.py - WITH PRESENTATION MODE BUTTON

import cv2
import os
import time
import numpy as np
import mode_manager
import config
import hand_tracker

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap


class DashboardPage(QWidget):
    """
    Dashboard Page with Camera Feed and Quick Mode Controls
    
    Features:
    - Live camera feed
    - Quick mode switching (Desktop, Gaming, Draw)
    - Camera controls
    - Presentation Mode button (NEW!)
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SIGNALS
    # ═══════════════════════════════════════════════════════════════
    presentationModeRequested = Signal()  # NEW: Signal to open Presentation Mode
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.last_frame = None
        self.frame_count = 0
        self.fps = 0
        self.camera_active = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ================= TITLE =================
        title = QLabel("Dashboard")
        title.setObjectName("title")
        layout.addWidget(title)

        # ================= TOP ROW =================
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # ---------- CAMERA CARD ----------
        cam_card = QFrame()
        cam_card.setObjectName("card")
        cam_card.setMinimumSize(820, 520)
        cam_layout = QVBoxLayout(cam_card)

        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("📷 Camera Feed")
        cam_title.setObjectName("cardTitle")
        cam_header.addWidget(cam_title)

        self.live_dot = QLabel("⚫ OFF")
        self.live_dot.setStyleSheet(
            "color: #6b7280; font-size: 12px; font-weight: bold;"
        )
        cam_header.addStretch()
        cam_header.addWidget(self.live_dot)
        cam_layout.addLayout(cam_header)

        # Display
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(780, 450)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("""
            background: #000000;
            border-radius: 12px;
            border: 2px solid rgba(255,255,255,0.1);
        """)
        self.camera_label.setText(
            "📷 Camera Off\n\nClick 'Start Camera' to begin"
        )
        cam_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)

        # Controls Row 1
        ctrl1 = QHBoxLayout()
        ctrl1.setSpacing(8)

        # Camera Selector
        self.cam_selector = QComboBox()

        # Show ALL camera options with status
        for idx, base_name in config.CAMERA_SOURCES.items():
            # Check if camera is connected
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened() and cap.read()[0]:
                    name = f"{base_name} ✅"
                    enabled = True
                else:
                    name = f"{base_name} ❌"
                    enabled = False
                cap.release()
            except Exception:
                name = f"{base_name} ❌"
                enabled = False
            
            self.cam_selector.addItem(name, idx)

        # Set current selection
        current_cam = getattr(config, 'camera_index', 0)
        self.cam_selector.setCurrentIndex(current_cam)

        self.cam_selector.setStyleSheet("""
            QComboBox {
                padding: 8px; 
                border-radius: 10px;
                background: rgba(255,255,255,0.1);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
                font-size: 13px;
                min-width: 220px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #60a5fa;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background: #1e1e2e;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: #2563eb;
                padding: 4px;
            }
        """)
        ctrl1.addWidget(self.cam_selector)

        self.start_btn = QPushButton("▶️ Start Camera")
        self.start_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 16px; border-radius: 12px;
                background: rgba(34, 197, 94, 0.3);
                border: 1px solid rgba(34, 197, 94, 0.6);
                color: white; font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(34, 197, 94, 0.5);
            }
        """)
        self.start_btn.clicked.connect(self.start_camera)
        ctrl1.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop Camera")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 16px; border-radius: 12px;
                background: rgba(239, 68, 68, 0.3);
                border: 1px solid rgba(239, 68, 68, 0.6);
                color: white; font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.5);
            }
            QPushButton:disabled {
                background: rgba(100,100,100,0.2);
                border: 1px solid rgba(100,100,100,0.3);
                color: #666;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_camera)
        ctrl1.addWidget(self.stop_btn)

        cam_layout.addLayout(ctrl1)

        # Controls Row 2 - WITH ICONS
        ctrl2 = QHBoxLayout()
        ctrl2.setSpacing(8)

        # Screenshot Button
        self.screenshot_btn = QPushButton("📸")
        self.screenshot_btn.setFixedSize(40, 40)
        self.screenshot_btn.setCursor(Qt.PointingHandCursor)
        self.screenshot_btn.setEnabled(False)
        self.screenshot_btn.setToolTip("Screenshot")
        self.screenshot_btn.setStyleSheet("""
            QPushButton {
                background: rgba(99, 102, 241, 0.2);
                border: 2px solid rgba(99, 102, 241, 0.4);
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.4);
                border: 2px solid rgba(99, 102, 241, 0.7);
            }
            QPushButton:disabled {
                background: rgba(100,100,100,0.1);
                border: 1px solid rgba(100,100,100,0.2);
            }
        """)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        ctrl2.addWidget(self.screenshot_btn)

        # Volume Button
        self.volume_btn = QPushButton("🔊")
        self.volume_btn.setFixedSize(40, 40)
        self.volume_btn.setCursor(Qt.PointingHandCursor)
        self.volume_btn.setToolTip("Volume Control")
        self.volume_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 107, 53, 0.2);
                border: 2px solid rgba(255, 107, 53, 0.4);
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(255, 107, 53, 0.4);
                border: 2px solid rgba(255, 107, 53, 0.7);
            }
        """)
        self.volume_btn.clicked.connect(self.handle_volume)
        ctrl2.addWidget(self.volume_btn)

        # Voice Button
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(40, 40)
        self.voice_btn.setCursor(Qt.PointingHandCursor)
        self.voice_btn.setToolTip("Voice Control")
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 193, 7, 0.2);
                border: 2px solid rgba(255, 193, 7, 0.4);
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(255, 193, 7, 0.4);
                border: 2px solid rgba(255, 193, 7, 0.7);
            }
        """)
        self.voice_btn.clicked.connect(self.handle_voice)
        ctrl2.addWidget(self.voice_btn)

        # Lock Button
        self.lock_btn = QPushButton("🔒")
        self.lock_btn.setFixedSize(40, 40)
        self.lock_btn.setCursor(Qt.PointingHandCursor)
        self.lock_btn.setToolTip("Lock Screen")
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 230, 118, 0.2);
                border: 2px solid rgba(0, 230, 118, 0.4);
                border-radius: 12px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(0, 230, 118, 0.4);
                border: 2px solid rgba(0, 230, 118, 0.7);
            }
        """)
        self.lock_btn.clicked.connect(self.handle_lock)
        ctrl2.addWidget(self.lock_btn)

        ctrl2.addStretch()

        # Tracking Status Label (Right Side)
        self.tracking_status = QLabel("⚫ Tracking Off")
        self.tracking_status.setStyleSheet(
            "color: #6b7280; font-size: 13px; font-weight: bold;"
        )
        ctrl2.addWidget(self.tracking_status)

        cam_layout.addLayout(ctrl2)
        top_row.addWidget(cam_card)

        # ---------- INFO COLUMN ----------
        info_col = QVBoxLayout()
        info_col.setSpacing(10)

        # Hand Status
        self.hand_card = QFrame()
        self.hand_card.setObjectName("card")
        hl = QVBoxLayout(self.hand_card)

        ht = QLabel("✋ Hand Detection")
        ht.setObjectName("cardTitle")
        hl.addWidget(ht)

        self.hand_status_label = QLabel("⚫ Camera Off")
        self.hand_status_label.setStyleSheet(
            "color: #6b7280; font-size: 16px; font-weight: bold;"
        )
        hl.addWidget(self.hand_status_label)

        self.hand_detail = QLabel("Start camera to detect")
        self.hand_detail.setStyleSheet(
            "color: #94a3b8; font-size: 12px;"
        )
        hl.addWidget(self.hand_detail)

        info_col.addWidget(self.hand_card)

        # Mode Status
        mode_card = QFrame()
        mode_card.setObjectName("card")
        ml = QVBoxLayout(mode_card)

        mtt = QLabel("🎯 Active Mode")
        mtt.setObjectName("cardTitle")
        ml.addWidget(mtt)

        self.mode_label = QLabel("🖥 DESKTOP")
        self.mode_label.setStyleSheet(
            "color: #60a5fa; font-size: 18px; font-weight: bold;"
        )
        ml.addWidget(self.mode_label)

        self.mode_detail = QLabel("Mouse control")
        self.mode_detail.setStyleSheet(
            "color: #94a3b8; font-size: 12px;"
        )
        ml.addWidget(self.mode_detail)

        info_col.addWidget(mode_card)

        # Engine Status
        eng_card = QFrame()
        eng_card.setObjectName("card")
        el = QVBoxLayout(eng_card)

        ett = QLabel("⚙️ Engine")
        ett.setObjectName("cardTitle")
        el.addWidget(ett)

        self.engine_label = QLabel("⚫ Idle")
        self.engine_label.setStyleSheet(
            "color: #6b7280; font-size: 16px; font-weight: bold;"
        )
        el.addWidget(self.engine_label)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet(
            "color: #94a3b8; font-size: 12px;"
        )
        el.addWidget(self.fps_label)

        info_col.addWidget(eng_card)
        info_col.addStretch()

        top_row.addLayout(info_col)
        layout.addLayout(top_row)

        # ================= BOTTOM ROW =================
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        # ═══════════════════════════════════════════════════════════════
        # Quick Mode Switch Card
        # ═══════════════════════════════════════════════════════════════
        qc = QFrame()
        qc.setObjectName("card")
        ql = QVBoxLayout(qc)

        ql.addWidget(QLabel("⚡ Quick Mode Switch"))

        mb = QHBoxLayout()

        self.q_desktop = QPushButton("🖥 Desktop")
        self.q_desktop.setObjectName("modeBtn")
        self.q_desktop.setCheckable(True)
        self.q_desktop.setChecked(True)
        self.q_desktop.clicked.connect(
            lambda: self.switch_mode("DESKTOP")
        )
        mb.addWidget(self.q_desktop)

        self.q_gaming = QPushButton("🎮 Gaming")
        self.q_gaming.setObjectName("modeBtn")
        self.q_gaming.setCheckable(True)
        self.q_gaming.clicked.connect(
            lambda: self.switch_mode("GAMING")
        )
        mb.addWidget(self.q_gaming)

        self.q_draw = QPushButton("✏️ Draw")
        self.q_draw.setObjectName("modeBtn")
        self.q_draw.setCheckable(True)
        self.q_draw.clicked.connect(
            lambda: self.switch_mode("DRAW")
        )
        mb.addWidget(self.q_draw)

        ql.addLayout(mb)
        bottom.addWidget(qc, 1)

        # ═══════════════════════════════════════════════════════════════
        # 📽️ NEW: PRESENTATION MODE CARD
        # ═══════════════════════════════════════════════════════════════
        pres_card = QFrame()
        pres_card.setObjectName("card")
        pres_layout = QVBoxLayout(pres_card)
        
        pres_title = QLabel("📽️ Presentation Mode")
        pres_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #e0e8f0;")
        pres_layout.addWidget(pres_title)
        
        pres_desc = QLabel("Load slides & annotate with gestures")
        pres_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        pres_layout.addWidget(pres_desc)
        
        self.presentation_btn = QPushButton("🎥 Open Presentation")
        self.presentation_btn.setCursor(Qt.PointingHandCursor)
        self.presentation_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;
                border-radius: 12px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(139, 92, 246, 0.3),
                    stop:1 rgba(168, 85, 247, 0.3)
                );
                border: 2px solid rgba(168, 85, 247, 0.5);
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(139, 92, 246, 0.5),
                    stop:1 rgba(168, 85, 247, 0.5)
                );
                border: 2px solid rgba(168, 85, 247, 0.8);
            }
            QPushButton:pressed {
                background: rgba(139, 92, 246, 0.7);
            }
        """)
        self.presentation_btn.clicked.connect(self._on_presentation_clicked)
        pres_layout.addWidget(self.presentation_btn)
        
        bottom.addWidget(pres_card, 1)

        # Hints Card
        hc = QFrame()
        hc.setObjectName("card")
        hcl = QVBoxLayout(hc)

        hcl.addWidget(QLabel("💡 Gestures"))
        self.hints = QLabel(
            "☝️ Index → Cursor\n"
            "👍 Thumbs Up → Click\n"
            "👎 Thumbs Down → Right Click"
        )
        self.hints.setStyleSheet(
            "color: #cbd5f5; font-size: 12px;"
        )
        hcl.addWidget(self.hints)

        bottom.addWidget(hc, 1)
        layout.addLayout(bottom)

        # ================= TIMERS =================
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.read_shared_frame)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)

        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.calc_fps)
        self.fps_timer.start(1000)

    # ═══════════════════════════════════════════════════════════════
    # 📽️ PRESENTATION MODE HANDLER (NEW)
    # ═══════════════════════════════════════════════════════════════
    
    def _on_presentation_clicked(self):
        """Handle Presentation Mode button click"""
        print("\n" + "="*60)
        print("📽️ PRESENTATION MODE BUTTON CLICKED!")
        print("   Emitting presentationModeRequested signal...")
        print("   This will open presentation_mode_page.py")
        print("="*60 + "\n")
        
        self.presentationModeRequested.emit()

    # ================= ICON HANDLERS =================
    def handle_volume(self):
        """Handle volume control button click."""
        print("🔊 Volume Control clicked")
        # Add your volume control logic here

    def handle_voice(self):
        """Handle voice control button click."""
        print("🎤 Voice Control clicked")
        # Add your voice control logic here

    def handle_lock(self):
        """Handle lock screen button click."""
        print("🔒 Lock Screen clicked")
        # Uncomment below for Windows lock screen:
        # import ctypes
        # ctypes.windll.user32.LockWorkStation()

    # ================= CAMERA CONTROLS =================
    def start_camera(self):
        self.camera_active = True
    
        # Get selected camera index (from combobox userData)
        selected_idx = self.cam_selector.currentIndex()
        config.camera_index = selected_idx
        config.save_config()  # Save to settings.json
    
        hand_tracker.set_camera_state(True)
        hand_tracker.set_gesture_state(True)
    
        self.frame_timer.start(33)

        self.start_btn.setEnabled(False)
        self.start_btn.setText("✅ Running")
        self.stop_btn.setEnabled(True)
        self.screenshot_btn.setEnabled(True)
        self.cam_selector.setEnabled(False)

        self.live_dot.setText("🔴 LIVE")
        self.live_dot.setStyleSheet(
            "color: #ef4444; font-size: 12px; font-weight: bold;"
        )

        # Update tracking status
        self.tracking_status.setText("🟢 Tracking On")
        self.tracking_status.setStyleSheet(
            "color: #22c55e; font-size: 13px; font-weight: bold;"
        )

        self.engine_label.setText("✅ Running")
        self.engine_label.setStyleSheet(
            "color: #22c55e; font-size: 16px; font-weight: bold;"
        )

        parent = self.parent_window
        if parent and hasattr(parent, '_tracking_active'):
            parent._tracking_active = True
            if hasattr(parent, 'activate_btn'):
                parent.activate_btn.set_active(True)
            if hasattr(parent, 'ai_status'):
                parent.ai_status.set_active(True)
            if hasattr(parent, 'start_tracking_btn'):
                parent.start_tracking_btn.setEnabled(False)
                parent.start_tracking_btn.setText("✅ Running")
            if hasattr(parent, 'stop_tracking_btn'):
                parent.stop_tracking_btn.setEnabled(True)
            if hasattr(parent, 'screenshot_btn_cam'):
                parent.screenshot_btn_cam.setEnabled(True)
            if hasattr(parent, 'cam_status_text'):
                parent.cam_status_text.setText("🟢 Tracking Active")
                parent.cam_status_text.setStyleSheet(
                    "color: #00e676; font-size: 11px;"
                    " background: transparent; font-weight: 600;"
                )
            if hasattr(parent, 'frame_timer'):
                parent.frame_timer.start(33)

        print("📷 Dashboard: Camera ENABLED")

    def stop_camera(self):
        self.camera_active = False

        hand_tracker.set_camera_state(False)
        hand_tracker.set_gesture_state(False)

        self.frame_timer.stop()

        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶️ Start Camera")
        self.stop_btn.setEnabled(False)
        self.screenshot_btn.setEnabled(False)
        self.cam_selector.setEnabled(True)

        self.live_dot.setText("⚫ OFF")
        self.live_dot.setStyleSheet(
            "color: #6b7280; font-size: 12px; font-weight: bold;"
        )

        # Update tracking status
        self.tracking_status.setText("⚫ Tracking Off")
        self.tracking_status.setStyleSheet(
            "color: #6b7280; font-size: 13px; font-weight: bold;"
        )

        self.camera_label.clear()
        self.camera_label.setText(
            "📷 Camera Off\n\nClick 'Start Camera' to begin"
        )

        self.engine_label.setText("⚫ Stopped")
        self.engine_label.setStyleSheet(
            "color: #6b7280; font-size: 16px; font-weight: bold;"
        )
        self.fps_label.setText("FPS: --")

        self.hand_status_label.setText("⚫ Camera Off")
        self.hand_status_label.setStyleSheet(
            "color: #6b7280; font-size: 16px; font-weight: bold;"
        )
        self.hand_detail.setText("Start camera to detect")
        self.hand_card.setStyleSheet("")

        parent = self.parent_window
        if parent and hasattr(parent, '_tracking_active'):
            parent._tracking_active = False
            if hasattr(parent, 'activate_btn'):
                parent.activate_btn.set_active(False)
            if hasattr(parent, 'ai_status'):
                parent.ai_status.set_active(False)
            if hasattr(parent, 'start_tracking_btn'):
                parent.start_tracking_btn.setEnabled(True)
                parent.start_tracking_btn.setText("▶  Start Tracking")
            if hasattr(parent, 'stop_tracking_btn'):
                parent.stop_tracking_btn.setEnabled(False)
            if hasattr(parent, 'cam_status_text'):
                parent.cam_status_text.setText("⚫ Tracking Off")
                parent.cam_status_text.setStyleSheet(
                    "color: #556677; font-size: 11px;"
                    " background: transparent; font-weight: 600;"
                )
            if hasattr(parent, 'frame_timer'):
                parent.frame_timer.stop()
            if hasattr(parent, 'camera_preview'):
                parent.camera_preview.clear()
                parent.camera_preview.setText(
                    "📹 Camera Preview\n"
                    "Click 'Start Tracking' to begin"
                )

        print("📷 Dashboard: Camera DISABLED")

    def read_shared_frame(self):
        frame = mode_manager.shared_frame

        if frame is None:
            return

        self.last_frame = frame.copy()
        self.frame_count += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (780, 450))

        h, w, ch = resized.shape
        bpl = ch * w
        qimg = QImage(resized.data, w, h, bpl, QImage.Format_RGB888)

        self.camera_label.setPixmap(
            QPixmap.fromImage(qimg).scaled(
                780, 450, Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def calc_fps(self):
        if not self.camera_active:
            return
        self.fps = self.frame_count
        self.frame_count = 0
        self.fps_label.setText(f"FPS: {self.fps}")

        if self.fps >= 25:
            self.fps_label.setStyleSheet("color: #22c55e; font-size: 12px;")
        elif self.fps >= 15:
            self.fps_label.setStyleSheet("color: #eab308; font-size: 12px;")
        else:
            self.fps_label.setStyleSheet("color: #ef4444; font-size: 12px;")

    def update_status(self):
        mode = mode_manager.mode
        detected = mode_manager.hand_detected

        if not self.camera_active:
            pass
        elif detected:
            self.hand_status_label.setText("✅ Hand Detected")
            self.hand_status_label.setStyleSheet(
                "color: #22c55e; font-size: 16px; font-weight: bold;"
            )
            self.hand_detail.setText("Tracking active")
            self.hand_card.setStyleSheet("""
                background: rgba(34,197,94,0.08);
                border-radius: 22px; padding: 18px;
                border: 1px solid rgba(34,197,94,0.3);
            """)
        else:
            self.hand_status_label.setText("❌ No Hand")
            self.hand_status_label.setStyleSheet(
                "color: #ef4444; font-size: 16px; font-weight: bold;"
            )
            self.hand_detail.setText("Show your hand")
            self.hand_card.setStyleSheet("""
                background: rgba(239,68,68,0.08);
                border-radius: 22px; padding: 18px;
                border: 1px solid rgba(239,68,68,0.3);
            """)

        info = {
            "DESKTOP": ("🖥 DESKTOP", "#60a5fa", "Mouse control"),
            "GAMING": ("🎮 GAMING", "#f97316", "WASD controls"),
            "DRAW": ("✏️ DRAW", "#ef4444", "Screen drawing")
        }
        txt, col, det = info.get(mode, ("?", "#fff", ""))
        self.mode_label.setText(txt)
        self.mode_label.setStyleSheet(
            f"color: {col}; font-size: 18px; font-weight: bold;"
        )
        self.mode_detail.setText(det)

        self.q_desktop.setChecked(mode == "DESKTOP")
        self.q_gaming.setChecked(mode == "GAMING")
        self.q_draw.setChecked(mode == "DRAW")

        h = {
            "DESKTOP": (
                "☝️ Index → Cursor\n"
                "👍 Thumbs Up → Click\n"
                "👎 Thumbs Down → Right Click\n"
                "✌️ Two → Scroll\n"
                "🖐 Five → Dbl Click"
            ),
            "GAMING": (
                "☝️ Dir → WASD\n"
                "🖐 Open → Jump\n"
                "👍 Thumbs Up → Attack\n"
                "✊ Fist → Sprint"
            ),
            "DRAW": (
                "☝️ Index → Draw\n"
                "✌️ Two → Color\n"
                "🖐 Five → Clear\n"
                "✊ Fist → Pen Up"
            )
        }
        self.hints.setText(h.get(mode, ""))

    def switch_mode(self, mode):
        mode_manager.set_mode(mode)
        if self.parent_window and hasattr(self.parent_window, 'set_mode'):
            self.parent_window.set_mode(mode)

    def take_screenshot(self):
        if self.last_frame is not None:
            os.makedirs("screenshots", exist_ok=True)
            fn = f"screenshots/cap_{int(time.time())}.png"
            cv2.imwrite(fn, self.last_frame)
            self.screenshot_btn.setText("✅")
            QTimer.singleShot(
                2000,
                lambda: self.screenshot_btn.setText("📸")
            )

    def cleanup(self):
        self.stop_camera()
        self.status_timer.stop()
        self.fps_timer.stop()
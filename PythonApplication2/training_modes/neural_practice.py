"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         NEURAL PRACTICE MODE                                 ║
║                    🧠 Basic Gesture Training System 🧠                        ║
║                         Version 2.0 - FIXED FLOW                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  CORRECT FLOW:                                                                ║
║  1. Open Neural → MAIN cam stays ON → Neural cam idle                        ║
║  2. Select gesture → Click START                                             ║
║  3. On START → PAUSE main cam → Neural cam starts                            ║
║  4. Perform gesture → SUCCESS!                                               ║
║  5. SUCCESS/STOP → Neural cam stops → Main cam resumes                       ║
║  6. Select next gesture → Repeat                                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar, QScrollArea,
    QGridLayout, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot
from PySide6.QtGui import QFont, QPixmap, QImage
import cv2
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import hand_tracker
    import config
    import mode_manager
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    hand_tracker = None
    config = None
    mode_manager = None


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


# ═══════��═══════════════════════════════════════════════════════════════════════
# 📷 NEURAL CAMERA THREAD - Independent Training Camera
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralCameraThread(QThread):
    """Independent camera thread for Neural Practice"""
    frame_ready = Signal(object, str, bool, float)
    camera_error = Signal(str)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        self.tracker = None
    
    def run(self):
        """Main camera loop"""
        print(f"📷 Neural Camera Thread starting (index {self.camera_index})...")
        
        try:
            # Import tracker
            from training_tracker import TrainingGestureTracker
            
            # Create tracker
            self.tracker = TrainingGestureTracker(camera_index=self.camera_index)
            
            if not self.tracker.start():
                self.camera_error.emit("Failed to start camera")
                print("❌ Neural camera failed to start!")
                return
            
            print("✅ Neural camera started!")
            self.running = True
            
            # Main loop
            while self.running:
                try:
                    frame, gesture, hand_detected, dwell = self.tracker.get_frame()
                    
                    if frame is not None:
                        self.frame_ready.emit(frame, gesture, hand_detected, dwell)
                    
                    self.msleep(30)  # ~33 FPS
                    
                except Exception as e:
                    print(f"⚠️ Frame error: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Neural camera error: {e}")
            import traceback
            traceback.print_exc()
            self.camera_error.emit(str(e))
        
        finally:
            self._cleanup()
    
    def stop(self):
        """Stop camera thread"""
        print("🛑 Stopping Neural camera...")
        self.running = False
        self.wait(2000)
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.tracker:
            try:
                self.tracker.stop()
            except:
                pass
            self.tracker = None
        print("✅ Neural camera cleaned up")


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 NEURAL PRACTICE MODE - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class NeuralPracticeMode(QWidget):
    """
    🧠 Neural Practice Mode - Fixed Camera Flow (Updated)
    
    FLOW:
    1. Mode opens → main cam stays ON, neural cam OFF
    2. User selects gesture → START TRAINING
    3. On START → main cam PAUSES → neural cam STARTS
    4. User performs gesture → 2 second hold → SUCCESS!
    5. On SUCCESS or STOP → neural cam STOPS → main cam RESUMES
    6. User selects next gesture → Repeat
    7. EXIT → Ensure neural cam STOPPED → main cam RESUMED
    """
    
    mode_closed = Signal()
    
    def __init__(self, parent=None, tracker=None):
        super().__init__(parent)
        self.setWindowTitle("◈ NEURAL PRACTICE MODE")
        self.setMinimumSize(1300, 900)
        
        print("\n" + "🧠"*30)
        print("🧠 INITIALIZING NEURAL PRACTICE MODE")
        print("🧠"*30)
        
        # ═══ STATE ═══
        self.is_training = False
        self.camera_thread = None
        self.current_gesture = None
        self.current_gesture_emoji = ""
        self.current_gesture_color = Neon.CYAN
        self.gesture_hold_start = None
        self.hold_duration = 2.0
        
        # Stats
        self.practice_count = 0
        self.success_count = 0
        
        # UI references
        self.selected_button = None
        self.gesture_buttons = {}
        
        # Gesture patterns [thumb, index, middle, ring, pinky]
        self.gesture_patterns = {
            "INDEX": [0, 1, 0, 0, 0],
            "PEACE": [0, 1, 1, 0, 0],
            "THREE": [0, 1, 1, 1, 0],
            "PALM": [1, 1, 1, 1, 1],
            "FIST": [0, 0, 0, 0, 0],
            "THUMB": [1, 0, 0, 0, 0],
            "SHAKA": [1, 0, 0, 0, 1],
        }
        
        # ═══ BUILD UI ═══
        self.setup_ui()
        self.apply_theme()
        
        # ═══ FPS TIMER ═══
        self.frame_count = 0
        self.current_fps = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._calculate_fps)
        self.fps_timer.start(1000)

        # Initial camera/system status (main cam assumed active)
        if hasattr(self, "cam_status"):
            self.cam_status.setText("● IDLE")
            self.cam_status.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        if hasattr(self, "sys_status"):
            self.sys_status.setText("◉ MAIN CAMERA ACTIVE - READY TO TRAIN")
            self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        
        print("🧠"*30)
        print("✅ Neural Practice Mode initialized!")
        print("🧠"*30 + "\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📷 CAMERA CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _pause_main_camera(self):
        """Pause main/desktop camera to free up resource"""
        try:
            if hand_tracker:
                hand_tracker.set_camera_state(False)
                hand_tracker.set_gesture_state(False)
                print("  ✅ Main camera paused")
        except Exception as e:
            print(f"  ⚠️ Could not pause main camera: {e}")
    
    def _resume_main_camera(self):
        """Resume main/desktop camera"""
        try:
            if hand_tracker:
                hand_tracker.set_camera_state(True)
                hand_tracker.set_gesture_state(True)
                print("  ✅ Main camera resumed")
        except Exception as e:
            print(f"  ⚠️ Could not resume main camera: {e}")
    
    def _start_neural_camera(self):
        """Start neural practice camera"""
        # If already running, don't start another
        if self.camera_thread is not None:
            print("📷 Neural camera already running, start skipped")
            return

        print("\n📷 Starting Neural camera thread...")
        
        # Get camera index
        camera_idx = 0
        if config:
            camera_idx = getattr(config, 'camera_index', 0)
        
        print(f"  📷 Using camera index: {camera_idx}")
        
        # Create and start thread
        self.camera_thread = NeuralCameraThread(camera_index=camera_idx)
        self.camera_thread.frame_ready.connect(self._on_frame_ready)
        self.camera_thread.camera_error.connect(self._on_camera_error)
        self.camera_thread.start()
        
        # Update UI
        self.cam_status.setText("● LIVE")
        self.cam_status.setStyleSheet(f"color: {Neon.GREEN};")
        self.sys_status.setText("◉ NEURAL CAMERA ACTIVE")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
    
    def _stop_neural_camera(self):
        """Stop neural camera"""
        print("📷 Stopping Neural camera...")
        
        if self.camera_thread is not None:
            try:
                self.camera_thread.stop()
            except Exception as e:
                print(f"  ⚠️ Stop error: {e}")
            self.camera_thread = None
        
        # Update UI to idle (neural off, main can be active)
        self.cam_status.setText("● IDLE")
        self.cam_status.setStyleSheet(f"color: {Neon.TEXT_DIM};")
    
    @Slot(object, str, bool, float)
    def _on_frame_ready(self, frame, gesture, hand_detected, dwell):
        """Handle frame from camera thread"""
        if frame is None:
            return
        
        self.frame_count += 1
        
        # Resize and convert
        resized = cv2.resize(frame, (480, 320))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # To QImage
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Display
        self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
        
        # Process gesture if training
        if self.is_training:
            self._process_gesture(gesture, hand_detected)
    
    @Slot(str)
    def _on_camera_error(self, error_msg):
        """Handle camera error"""
        print(f"❌ Camera Error: {error_msg}")
        self.training_status.setText(f"❌ CAMERA ERROR\n{error_msg}")
        self.training_status.setStyleSheet(f"""
            color: {Neon.RED};
            background: rgba(255, 0, 85, 0.1);
            border: 1px solid {Neon.RED};
            border-radius: 10px;
            padding: 15px;
        """)
    
    def _calculate_fps(self):
        """Calculate FPS"""
        self.current_fps = self.frame_count
        self.frame_count = 0
        
        val = self.stat_fps.findChild(QLabel, "val")
        if val:
            val.setText(str(self.current_fps))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎯 TRAINING LOGIC
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _toggle_training(self):
        """Toggle training on/off"""
        if not self.is_training:
            self._start_training()
        else:
            self._stop_training()
    
    def _start_training(self):
        """Start training for selected gesture"""
        if not self.current_gesture:
            self.training_status.setText("⚠ SELECT A GESTURE FIRST!")
            self.training_status.setStyleSheet(f"""
                color: {Neon.RED};
                background: rgba(255, 0, 85, 0.1);
                border: 1px solid {Neon.RED};
                border-radius: 10px;
                padding: 15px;
            """)
            return

        # Make sure we start with a clean neural camera session
        if self.camera_thread is not None:
            self._stop_neural_camera()

        print("  📡 Pausing main camera for training...")
        self._pause_main_camera()

        print("  📷 Starting Neural camera for training...")
        self._start_neural_camera()
        
        print(f"\n🎯 Starting training for: {self.current_gesture}")
        
        self.is_training = True
        self.gesture_hold_start = None
        
        # Update UI
        self.start_btn.setText("■  STOP")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 0, 85, 0.15);
                color: {Neon.RED};
                border: 2px solid {Neon.RED};
                border-radius: 15px;
            }}
            QPushButton:hover {{ background: rgba(255, 0, 85, 0.3); }}
        """)
        
        self.training_status.setText(f"SHOW: {self.current_gesture_emoji} {self.current_gesture}")
        self.training_status.setStyleSheet(f"""
            color: {self.current_gesture_color};
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid {self.current_gesture_color};
            border-radius: 10px;
            padding: 15px;
        """)
        
        self.sys_status.setText("◉ TRAINING ACTIVE")
        self.sys_status.setStyleSheet(f"color: {Neon.YELLOW};")
    
    def _stop_training(self):
        """Stop current training (manual STOP or on close)"""
        print("⏹ Stopping training...")
        
        # Stop neural camera and resume main camera
        self._stop_neural_camera()
        print("  📡 Resuming main camera after training stop...")
        self._resume_main_camera()
        
        self.is_training = False
        self.gesture_hold_start = None
        
        # Reset UI
        self.hold_bar.setValue(0)
        self.hold_pct.setText("0%")
        
        self.start_btn.setText("▶  START")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 245, 255, 0.1);
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 15px;
            }}
            QPushButton:hover {{ background: rgba(0, 245, 255, 0.25); }}
        """)
        
        self.training_status.setText("👆 Select gesture & click START")
        self.training_status.setStyleSheet(f"""
            color: {Neon.CYAN};
            background: rgba(0, 245, 255, 0.05);
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
        """)
        
        self.sys_status.setText("◉ MAIN CAMERA ACTIVE - READY")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
    
    def _process_gesture(self, detected_gesture, hand_detected):
        """Process gesture during training"""
        if not hand_detected:
            self.gesture_hold_start = None
            self.hold_bar.setValue(0)
            self.hold_pct.setText("0%")
            
            self.training_status.setText("⚠ SHOW YOUR HAND")
            self.training_status.setStyleSheet(f"""
                color: {Neon.ORANGE};
                background: rgba(255, 107, 0, 0.1);
                border: 1px solid {Neon.ORANGE};
                border-radius: 10px;
                padding: 15px;
            """)
            return
        
        # Check match
        gesture_map = {
            "INDEX": "INDEX", "PEACE": "PEACE", "THREE": "THREE",
            "PALM": "PALM", "OPEN": "PALM", "FIST": "FIST",
            "THUMB": "THUMB", "SHAKA": "SHAKA"
        }
        
        target = gesture_map.get(self.current_gesture.upper(), self.current_gesture.upper())
        matched = (detected_gesture == target)
        
        if matched:
            now = time.time()
            
            if self.gesture_hold_start is None:
                self.gesture_hold_start = now
            
            elapsed = now - self.gesture_hold_start
            progress = min(1.0, elapsed / self.hold_duration)
            
            self.hold_bar.setValue(int(progress * 100))
            self.hold_pct.setText(f"{int(progress * 100)}%")
            
            remaining = max(0, self.hold_duration - elapsed)
            
            self.training_status.setText(f"✓ HOLD: {remaining:.1f}s")
            self.training_status.setStyleSheet(f"""
                color: {Neon.GREEN};
                background: rgba(0, 255, 159, 0.1);
                border: 1px solid {Neon.GREEN};
                border-radius: 10px;
                padding: 15px;
            """)
            
            # SUCCESS!
            if progress >= 1.0:
                self._on_success()
        else:
            self.gesture_hold_start = None
            self.hold_bar.setValue(0)
            self.hold_pct.setText("0%")
            
            self.training_status.setText(f"✗ SHOW: {self.current_gesture_emoji} {self.current_gesture}")
            self.training_status.setStyleSheet(f"""
                color: {Neon.RED};
                background: rgba(255, 0, 85, 0.1);
                border: 1px solid {Neon.RED};
                border-radius: 10px;
                padding: 15px;
            """)
    
    def _on_success(self):
        """Handle successful gesture"""
        print(f"\n✅ SUCCESS! {self.current_gesture}")
        
        # Stop neural camera and resume main camera
        self._stop_neural_camera()
        print("  📡 Resuming main camera after success...")
        self._resume_main_camera()
        
        # Update stats
        self.practice_count += 1
        self.success_count += 1
        self._update_stats()
        
        # Mark training stopped
        self.is_training = False
        self.gesture_hold_start = None
        
        # Show success
        self.training_status.setText(f"★ SUCCESS! {self.current_gesture_emoji}")
        self.training_status.setStyleSheet(f"""
            color: {Neon.YELLOW};
            background: rgba(240, 255, 0, 0.15);
            border: 2px solid {Neon.YELLOW};
            border-radius: 10px;
            padding: 15px;
        """)
        
        self.hold_bar.setValue(100)
        self.hold_pct.setText("100%")
        
        # Reset button
        self.start_btn.setText("▶  START")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 245, 255, 0.1);
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 15px;
            }}
            QPushButton:hover {{ background: rgba(0, 245, 255, 0.25); }}
        """)
        
        # Update system status for success
        self.sys_status.setText("◉ SUCCESS - MAIN CAMERA ACTIVE")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        
        # After 1.5s, reset for next gesture
        QTimer.singleShot(1500, self._ready_for_next)
    
    def _ready_for_next(self):
        """Ready for next gesture"""
        print("🔄 Ready for next gesture...")
        
        self.hold_bar.setValue(0)
        self.hold_pct.setText("0%")
        
        self.training_status.setText("✅ GREAT!\n\n👆 Select next gesture & click START")
        self.training_status.setStyleSheet(f"""
            color: {Neon.GREEN};
            background: rgba(0, 255, 159, 0.1);
            border: 1px solid {Neon.GREEN};
            border-radius: 10px;
            padding: 15px;
        """)
        
        self.sys_status.setText("◉ MAIN CAMERA ACTIVE - SELECT NEXT GESTURE")
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎮 GESTURE SELECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _select_gesture(self, card):
        """Select gesture to practice"""
        # Uncheck previous
        if self.selected_button and self.selected_button != card:
            self.selected_button.setChecked(False)
        
        self.selected_button = card
        self.current_gesture = card.g_name
        self.current_gesture_emoji = card.g_emoji
        self.current_gesture_color = card.g_color
        card.setChecked(True)
        
        # Update UI
        self.training_status.setText(f"READY: {card.g_emoji} {card.g_name}\n\n▶ Click START to begin")
        self.training_status.setStyleSheet(f"""
            color: {card.g_color};
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid {card.g_color};
            border-radius: 10px;
            padding: 15px;
        """)
        
        self.curr_gesture.setText(f"◈ {card.g_emoji} {card.g_name}")
        self.curr_gesture.setStyleSheet(f"color: {card.g_color};")
        
        self.sel_info.setText(f"▸ {card.g_name}\n▸ {card.g_action}")
        self.sel_info.setStyleSheet(f"color: {card.g_color};")
        
        print(f"🎯 Selected: {card.g_name}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📊 STATS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update_stats(self):
        """Update statistics display"""
        accuracy = (self.success_count / self.practice_count * 100) if self.practice_count > 0 else 0
        
        pv = self.stat_practiced.findChild(QLabel, "val")
        if pv:
            pv.setText(str(self.practice_count))
        
        sv = self.stat_success.findChild(QLabel, "val")
        if sv:
            sv.setText(str(self.success_count))
        
        av = self.stat_accuracy.findChild(QLabel, "val")
        if av:
            av.setText(f"{accuracy:.0f}%")
        
        self.acc_bar.setValue(int(accuracy))
        self.acc_pct.setText(f"{accuracy:.0f}%")
    
    def _reset_stats(self):
        """Reset statistics"""
        self.practice_count = 0
        self.success_count = 0
        
        pv = self.stat_practiced.findChild(QLabel, "val")
        if pv:
            pv.setText("0")
        
        sv = self.stat_success.findChild(QLabel, "val")
        if sv:
            sv.setText("0")
        
        av = self.stat_accuracy.findChild(QLabel, "val")
        if av:
            av.setText("0%")
        
        self.acc_bar.setValue(0)
        self.acc_pct.setText("0%")
        
        print("🔄 Stats reset")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🚪 CLOSE & CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _close_mode(self):
        """Close neural practice and return"""
        print("\n🚪 Closing Neural Practice...")
        
        # Stop training if active (this will also stop neural + resume main)
        if self.is_training:
            self._stop_training()
        else:
            # Safety: ensure neural stopped and main resumed
            self._stop_neural_camera()
            print("  📡 Ensuring main camera resumed on close...")
            self._resume_main_camera()
        
        # Emit close signal
        self.mode_closed.emit()
        
        print("✅ Neural Practice closed\n")
    
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Neural Practice cleanup...")
        
        # Stop timers
        if hasattr(self, 'fps_timer'):
            self.fps_timer.stop()
        
        # Stop camera
        self._stop_neural_camera()
        
        # Resume main
        self._resume_main_camera()
        
        print("✅ Cleanup complete")
    
    def closeEvent(self, event):
        """Handle close event"""
        self.cleanup()
        event.accept()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🏗️ UI BUILDING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_ui(self):
        """Build complete UI"""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        
        # Header
        self.header = self._build_header()
        main.addWidget(self.header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("scrollArea")
        
        content = QWidget()
        content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(25)
        
        # Sections
        content_layout.addWidget(self._build_camera_section())
        content_layout.addWidget(self._build_gesture_section())
        content_layout.addWidget(self._build_instructions_section())
        content_layout.addSpacing(50)
        
        scroll.setWidget(content)
        main.addWidget(scroll, 1)
        
        # Footer
        self.footer = self._build_footer()
        main.addWidget(self.footer)
    
    def _build_header(self):
        """Build header"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(25)
        
        # Back button
        back_btn = QPushButton("◄  BACK")
        back_btn.setFixedSize(100, 45)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        back_btn.setObjectName("backBtn")
        back_btn.clicked.connect(self._close_mode)
        layout.addWidget(back_btn)
        
        # Logo
        logo = QLabel("🧠")
        logo.setFont(QFont("Segoe UI Emoji", 28))
        layout.addWidget(logo)
        
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("NEURAL PRACTICE")
        title.setFont(QFont("Consolas", 20, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.CYAN};")
        title_box.addWidget(title)
        subtitle = QLabel("GESTURE TRAINING MODE")
        subtitle.setFont(QFont("Consolas", 9))
        subtitle.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)
        
        layout.addStretch()
        
        # Stats
        self.stat_practiced = self._make_stat("PRACTICED", "0", Neon.CYAN)
        layout.addWidget(self.stat_practiced)
        self.stat_success = self._make_stat("SUCCESS", "0", Neon.GREEN)
        layout.addWidget(self.stat_success)
        self.stat_accuracy = self._make_stat("ACCURACY", "0%", Neon.YELLOW)
        layout.addWidget(self.stat_accuracy)
        self.stat_fps = self._make_stat("FPS", "0", Neon.MAGENTA)
        layout.addWidget(self.stat_fps)
        
        layout.addStretch()
        
        # Reset button
        reset_btn = QPushButton("⟲  RESET")
        reset_btn.setFixedSize(130, 45)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFont(QFont("Consolas", 11, QFont.Bold))
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_stats)
        layout.addWidget(reset_btn)
        
        return header
    
    def _make_stat(self, label, value, color):
        """Make stat box"""
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
        
        r, g, b = self._hex_rgb(color)
        box.setStyleSheet(f"""
            QFrame {{
                background: rgba({r}, {g}, {b}, 0.1);
                border: 1px solid {color};
                border-radius: 8px;
            }}
        """)
        
        return box
    
    def _build_camera_section(self):
        """Build camera section"""
        container = QFrame()
        container.setMinimumHeight(420)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(25)
        
        # Camera panel
        cam_panel = QFrame()
        cam_panel.setFixedWidth(520)
        cam_panel.setObjectName("camPanel")
        
        cam_layout = QVBoxLayout(cam_panel)
        cam_layout.setContentsMargins(20, 20, 20, 20)
        cam_layout.setSpacing(15)
        
        # Header
        cam_header = QHBoxLayout()
        cam_title = QLabel("◉ NEURAL CAMERA")
        cam_title.setFont(QFont("Consolas", 13, QFont.Bold))
        cam_title.setStyleSheet(f"color: {Neon.CYAN};")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        self.cam_status = QLabel("● IDLE")
        self.cam_status.setFont(QFont("Consolas", 10, QFont.Bold))
        self.cam_status.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        cam_header.addWidget(self.cam_status)
        cam_layout.addLayout(cam_header)
        
        # Camera display
        self.camera_label = QLabel("⟨ NEURAL CAMERA IDLE ⟩")
        self.camera_label.setFixedSize(480, 320)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setObjectName("camDisplay")
        cam_layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(cam_panel)
        
        # Control panel
        ctrl_panel = QFrame()
        ctrl_panel.setObjectName("ctrlPanel")
        
        ctrl_layout = QVBoxLayout(ctrl_panel)
        ctrl_layout.setContentsMargins(25, 25, 25, 25)
        ctrl_layout.setSpacing(20)
        
        # Title
        ctrl_title = QLabel("◈ CONTROL CENTER")
        ctrl_title.setFont(QFont("Consolas", 15, QFont.Bold))
        ctrl_title.setAlignment(Qt.AlignCenter)
        ctrl_title.setStyleSheet(f"color: {Neon.YELLOW};")
        ctrl_layout.addWidget(ctrl_title)
        
        # Status
        self.training_status = QLabel("👆 Select a gesture to begin")
        self.training_status.setFont(QFont("Consolas", 14, QFont.Bold))
        self.training_status.setAlignment(Qt.AlignCenter)
        self.training_status.setWordWrap(True)
        self.training_status.setMinimumHeight(80)
        self.training_status.setStyleSheet(f"""
            color: {Neon.CYAN};
            background: rgba(0, 245, 255, 0.05);
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 10px;
            padding: 15px;
        """)
        ctrl_layout.addWidget(self.training_status)
        
        # Hold Progress
        hold_box = QVBoxLayout()
        hold_box.setSpacing(8)
        hold_header = QHBoxLayout()
        hold_lbl = QLabel("⏱ HOLD PROGRESS")
        hold_lbl.setFont(QFont("Consolas", 10, QFont.Bold))
        hold_lbl.setStyleSheet(f"color: {Neon.MAGENTA};")
        hold_header.addWidget(hold_lbl)
        hold_header.addStretch()
        self.hold_pct = QLabel("0%")
        self.hold_pct.setFont(QFont("Consolas", 10, QFont.Bold))
        self.hold_pct.setStyleSheet(f"color: {Neon.MAGENTA};")
        hold_header.addWidget(self.hold_pct)
        hold_box.addLayout(hold_header)
        
        self.hold_bar = QProgressBar()
        self.hold_bar.setRange(0, 100)
        self.hold_bar.setValue(0)
        self.hold_bar.setFixedHeight(22)
        self.hold_bar.setTextVisible(False)
        self.hold_bar.setObjectName("holdBar")
        hold_box.addWidget(self.hold_bar)
        ctrl_layout.addLayout(hold_box)
        
        # Accuracy
        acc_box = QVBoxLayout()
        acc_box.setSpacing(8)
        acc_header = QHBoxLayout()
        acc_lbl = QLabel("◈ ACCURACY")
        acc_lbl.setFont(QFont("Consolas", 10, QFont.Bold))
        acc_lbl.setStyleSheet(f"color: {Neon.GREEN};")
        acc_header.addWidget(acc_lbl)
        acc_header.addStretch()
        self.acc_pct = QLabel("0%")
        self.acc_pct.setFont(QFont("Consolas", 10, QFont.Bold))
        self.acc_pct.setStyleSheet(f"color: {Neon.GREEN};")
        acc_header.addWidget(self.acc_pct)
        acc_box.addLayout(acc_header)
        
        self.acc_bar = QProgressBar()
        self.acc_bar.setRange(0, 100)
        self.acc_bar.setValue(0)
        self.acc_bar.setFixedHeight(22)
        self.acc_bar.setTextVisible(False)
        self.acc_bar.setObjectName("accBar")
        acc_box.addWidget(self.acc_bar)
        ctrl_layout.addLayout(acc_box)
        
        ctrl_layout.addStretch()
        
        # Start button
        self.start_btn = QPushButton("▶  START")
        self.start_btn.setFixedHeight(60)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFont(QFont("Consolas", 14, QFont.Bold))
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self._toggle_training)
        ctrl_layout.addWidget(self.start_btn)
        
        layout.addWidget(ctrl_panel, 1)
        
        return container
    
    def _build_gesture_section(self):
        """Build gesture selection grid"""
        section = QFrame()
        section.setMinimumHeight(400)
        section.setObjectName("gestureSection")
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        icon = QLabel("◈")
        icon.setFont(QFont("Consolas", 22))
        icon.setStyleSheet(f"color: {Neon.YELLOW};")
        header.addWidget(icon)
        title = QLabel("GESTURE MATRIX")
        title.setFont(QFont("Consolas", 18, QFont.Bold))
        title.setStyleSheet(f"color: {Neon.YELLOW};")
        header.addWidget(title)
        header.addStretch()
        hint = QLabel("Select a gesture to practice")
        hint.setFont(QFont("Consolas", 11))
        hint.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        header.addWidget(hint)
        layout.addLayout(header)
        
        # Grid
        grid = QGridLayout()
        grid.setSpacing(20)
        
        gestures = [
            ("☝️", "INDEX", "Move Cursor", "1 finger", Neon.CYAN),
            ("✌️", "PEACE", "Scroll", "2 fingers", Neon.GREEN),
            ("🤟", "THREE", "Drag", "3 fingers", Neon.PURPLE),
            ("✋", "PALM", "Double Click", "5 fingers", Neon.ORANGE),
            ("✊", "FIST", "Pause", "0 fingers", Neon.RED),
            ("👍", "THUMB", "Volume", "Thumb only", Neon.YELLOW),
            ("🤙", "SHAKA", "Play/Pause", "Thumb+Pinky", Neon.MAGENTA),
        ]
        
        for i, (emoji, name, action, fingers, color) in enumerate(gestures):
            card = self._make_gesture_card(emoji, name, action, fingers, color)
            grid.addWidget(card, i // 4, i % 4)
            self.gesture_buttons[name] = card
        
        layout.addLayout(grid)
        
        return section
    
    def _make_gesture_card(self, emoji, name, action, fingers, color):
        """Make gesture card"""
        card = QPushButton()
        card.setFixedSize(240, 170)
        card.setCursor(Qt.PointingHandCursor)
        card.setCheckable(True)
        
        card.g_name = name
        card.g_emoji = emoji
        card.g_color = color
        card.g_action = action
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(8)
        
        e_lbl = QLabel(emoji)
        e_lbl.setFont(QFont("Segoe UI Emoji", 48))
        e_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(e_lbl)
        
        n_lbl = QLabel(name)
        n_lbl.setFont(QFont("Consolas", 14, QFont.Bold))
        n_lbl.setAlignment(Qt.AlignCenter)
        n_lbl.setStyleSheet(f"color: {color};")
        layout.addWidget(n_lbl)
        
        a_lbl = QLabel(action)
        a_lbl.setFont(QFont("Consolas", 10))
        a_lbl.setAlignment(Qt.AlignCenter)
        a_lbl.setStyleSheet(f"color: {Neon.TEXT};")
        layout.addWidget(a_lbl)
        
        f_lbl = QLabel(fingers)
        f_lbl.setFont(QFont("Consolas", 9))
        f_lbl.setAlignment(Qt.AlignCenter)
        f_lbl.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(f_lbl)
        
        r, g, b = self._hex_rgb(color)
        card.setStyleSheet(f"""
            QPushButton {{
                background: rgba(8, 12, 25, 0.9);
                border: 2px solid rgba({r}, {g}, {b}, 0.4);
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background: rgba({r}, {g}, {b}, 0.12);
                border: 2px solid {color};
            }}
            QPushButton:checked {{
                background: rgba({r}, {g}, {b}, 0.2);
                border: 3px solid {color};
            }}
        """)
        
        card.clicked.connect(lambda: self._select_gesture(card))
        
        return card
    
    def _build_instructions_section(self):
        """Build instructions"""
        section = QFrame()
        section.setMinimumHeight(150)
        section.setObjectName("instructionsSection")
        
        layout = QHBoxLayout(section)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(50)
        
        # How to
        how_box = QVBoxLayout()
        how_title = QLabel("⟨ HOW TO TRAIN ⟩")
        how_title.setFont(QFont("Consolas", 13, QFont.Bold))
        how_title.setStyleSheet(f"color: {Neon.CYAN};")
        how_box.addWidget(how_title)
        how_text = QLabel("1. Select gesture\n2. Click START\n3. Show gesture\n4. Hold 2 seconds")
        how_text.setFont(QFont("Consolas", 10))
        how_text.setStyleSheet(f"color: {Neon.TEXT};")
        how_box.addWidget(how_text)
        layout.addLayout(how_box, 1)
        
        # Selected
        sel_box = QVBoxLayout()
        sel_title = QLabel("⟨ SELECTED ⟩")
        sel_title.setFont(QFont("Consolas", 13, QFont.Bold))
        sel_title.setStyleSheet(f"color: {Neon.YELLOW};")
        sel_box.addWidget(sel_title)
        self.sel_info = QLabel("No gesture selected")
        self.sel_info.setFont(QFont("Consolas", 10))
        self.sel_info.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        sel_box.addWidget(self.sel_info)
        layout.addLayout(sel_box, 1)
        
        # Tips
        tip_box = QVBoxLayout()
        tip_title = QLabel("⟨ TIPS ⟩")
        tip_title.setFont(QFont("Consolas", 13, QFont.Bold))
        tip_title.setStyleSheet(f"color: {Neon.GREEN};")
        tip_box.addWidget(tip_title)
        tip_text = QLabel("• Good lighting\n• Center hand\n• Hold steady")
        tip_text.setFont(QFont("Consolas", 10))
        tip_text.setStyleSheet(f"color: {Neon.TEXT};")
        tip_box.addWidget(tip_text)
        layout.addLayout(tip_box, 1)
        
        return section
    
    def _build_footer(self):
        """Build footer"""
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.sys_status = QLabel("◉ MAIN CAMERA ACTIVE - READY TO TRAIN")
        self.sys_status.setFont(QFont("Consolas", 11, QFont.Bold))
        self.sys_status.setStyleSheet(f"color: {Neon.GREEN};")
        layout.addWidget(self.sys_status)
        
        layout.addStretch()
        
        self.curr_gesture = QLabel("◈ No gesture selected")
        self.curr_gesture.setFont(QFont("Consolas", 11))
        self.curr_gesture.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(self.curr_gesture)
        
        layout.addStretch()
        
        version = QLabel("NEURAL PRACTICE v2.0")
        version.setFont(QFont("Consolas", 10))
        version.setStyleSheet(f"color: {Neon.TEXT_DIM};")
        layout.addWidget(version)
        
        return footer
    
    def _hex_rgb(self, hex_color):
        """Convert hex to RGB"""
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎨 THEME
    # ═══════════════════════════════════════════════════════════════════════════
    
    def apply_theme(self):
        """Apply cyberpunk theme"""
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000510, stop:0.5 #050a18, stop:1 #0a1225);
                color: {Neon.TEXT};
                font-family: 'Consolas', monospace;
            }}
            #scrollArea {{ background: transparent; border: none; }}
            #scrollContent {{ background: transparent; }}
            QScrollBar:vertical {{
                background: rgba(0, 30, 60, 0.4);
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Neon.CYAN}, stop:1 {Neon.MAGENTA});
                border-radius: 5px;
                min-height: 50px;
            }}
            #header {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 245, 255, 0.1), stop:1 rgba(0, 0, 0, 0.9));
                border-bottom: 3px solid {Neon.CYAN};
            }}
            #backBtn {{
                background: rgba(0, 245, 255, 0.15);
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 12px;
            }}
            #backBtn:hover {{ background: rgba(0, 245, 255, 0.35); }}
            #resetBtn {{
                background: rgba(255, 107, 0, 0.15);
                color: {Neon.ORANGE};
                border: 2px solid {Neon.ORANGE};
                border-radius: 12px;
            }}
            #resetBtn:hover {{ background: rgba(255, 107, 0, 0.35); }}
            #camPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.CYAN};
                border-radius: 20px;
            }}
            #camDisplay {{
                background: #000;
                border: 2px solid rgba(0, 245, 255, 0.4);
                border-radius: 12px;
                color: {Neon.TEXT_DIM};
                font-size: 14px;
            }}
            #ctrlPanel {{
                background: rgba(5, 10, 25, 0.85);
                border: 2px solid {Neon.YELLOW};
                border-radius: 20px;
            }}
            #holdBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {Neon.MAGENTA};
                border-radius: 11px;
            }}
            #holdBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.MAGENTA}, stop:1 {Neon.CYAN});
                border-radius: 10px;
            }}
            #accBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {Neon.GREEN};
                border-radius: 11px;
            }}
            #accBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Neon.GREEN}, stop:1 {Neon.CYAN});
                border-radius: 10px;
            }}
            #startBtn {{
                background: rgba(0, 245, 255, 0.1);
                color: {Neon.CYAN};
                border: 2px solid {Neon.CYAN};
                border-radius: 15px;
            }}
            #startBtn:hover {{ background: rgba(0, 245, 255, 0.25); }}
            #gestureSection {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(240, 255, 0, 0.4);
                border-radius: 20px;
            }}
            #instructionsSection {{
                background: rgba(5, 10, 25, 0.7);
                border: 2px solid rgba(0, 245, 255, 0.3);
                border-radius: 20px;
            }}
            #footer {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba(255, 0, 255, 0.1), stop:1 rgba(0, 0, 0, 0.9));
                border-top: 3px solid {Neon.MAGENTA};
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🧪 NEURAL PRACTICE - Standalone Test\n")
    
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    
    window = NeuralPracticeMode()
    window.showMaximized()
    
    sys.exit(app.exec())
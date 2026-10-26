"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              AUREVIX MAIN                                    ║
║                      Gesture Control Application                             ║
║              🎤 WITH VOICE COMMAND & ACTIVE AI ENGINE                        ║
║              📽️ WITH PRESENTATION MODE SUPPORT (FIXED)                       ║
║         🎮 GAMING MODE - CAMERA STATE PRESERVED (ON→ON, OFF→OFF)             ║
║         🖼️ WITH CUSTOM WINDOW ICON (LOGO)                                    ║
║         🚀 WITH SPLASH SCREEN INTEGRATION (12 SECONDS)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import threading
import gc
import config
import mode_manager

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QMessageBox, QDialog,
    QFileDialog, QPushButton, QListWidget,
    QListWidgetItem, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, Slot, QPoint
from PySide6.QtGui import QPixmap, QFont, QImage, QIcon, QGuiApplication

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 SPLASH SCREEN IMPORT
# ═══════════════════════════════════════════════════════════════════════════════
from splash_screen import SplashScreen 

# ═══════════════════════════════════════════════════════════════════════════════
# 🎤 VOICE COMMAND & AI ENGINE IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════
from voice_selector import VoiceGenderSelector
from voice_command_processor import VoiceCommandProcessor, CommandResult
from active_ai_engine import ActiveAIEngine

# Import separated components
from circular_button import CircularActivateButton
from glowing_button import GlowingButton
from fps_graph import FPSGraphWidget
from ai_status_indicator import AIStatusIndicator
from glass_card import GlassCard
from mode_card import ModeCard
from gesture_mapping_row import GestureMappingRow
from profile_badge import ProfileBadge
from ui_helpers import apply_neon_glow

# Import separated pages
from shortcuts_page import ShortcutsPage
from gestures_page import GesturesPage
from futuristic_dashboard import FuturisticDashboard
from top_navigation import TopNavigation
from sidebar import Sidebar
from placeholder_page import PlaceholderPage
from styles import get_styles

# Import existing modules
from user_gestures import save_gesture, load_gestures, get_gesture_count
from gesture_dialog import GestureRecordDialog, GestureConfigDialog
from dashboard_page import DashboardPage
from settings_panel import SettingsPanel
from draw_canvas import DrawCanvas
from preferences_page import PreferencesPage
from calibration_page import CalibrationPage
from auth_pages import AuthManager
from profile_widget import ProfileWidget, ProfileEditDialog
from logs_page import LogsPage
import hand_tracker
import database

# Notification System Import
from notification_manager import get_notification_manager
from notification_popup import get_toast_manager
from notification_page import NotificationPage

# Gaming Mode Import
from gaming_mode_page import GamingModePage
from gaming_gesture_controller import game_controller

# Training Mode Import
from training_mode_page import TrainingModePage
from ai_trainer import AITrainerPage


# ═══════════════════════════════════════════════════════════════════════════════
# 📽️ PRESENTATION MODE IMPORT
# ═════════════════════════════════════════════��═════════════════════════════════
from presentation_mode import PresentationDialog, PresentationViewer

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not installed.")

# ════════════════════════════════════════════════════════════════════════════════
#                          MAIN GESTURE PANEL
# ════════════════════════════════════════════════════════════════════════════════
class GesturePanel(QMainWindow):
    """
    Main Application Window for Aurevix Gesture Control System

    🎤 FEATURES:
    ─────────────────────
    - Active AI Engine Integration
    - Voice Command Processing
    - Dual Sensor Control (Vision + Voice)
    - Real-time Command Execution
    - Custom Window Icon (Logo)
    - Presentation Mode with Gestures
    - Gaming Mode with Camera State Preservation

    Page Index Reference:
    ─────────────────────
    0  = FuturisticDashboard (Home)
    1  = GesturesPage
    2  = ShortcutsPage
    3  = LogsPage
    4  = SettingsPanel
    5  = PreferencesPage
    6  = AI Trainer (Placeholder)
    7  = CalibrationPage
    8  = GamingModePage (Hidden - Dashboard access only)
    9  = TrainingModePage (Hidden - Dashboard access only)
    10 = Performance (Placeholder)
    11 = Profiles (Placeholder)
    12 = Cloud Sync (Placeholder)
    13 = Privacy Center (Placeholder)
    14 = NotificationPage

    ✅ GAMING EXIT BEHAVIOR (CAMERA STATE PRESERVED):
    - Camera ON before gaming → Camera ON after exit
    - Camera OFF before gaming → Camera OFF after exit
    - Desktop mode activates on exit
    """

    # Page index constants
    PAGE_DASHBOARD = 0
    PAGE_GESTURES = 1
    PAGE_SHORTCUTS = 2
    PAGE_LOGS = 3
    PAGE_SETTINGS = 4
    PAGE_PREFERENCES = 5
    PAGE_AI_TRAINER = 6

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurevix")
        self.resize(1400, 820)
        self.setMinimumSize(1200, 700)

        # ═══════════════════════════════════════════════════════════════
        # 🖼️ SET WINDOW ICON (LOGO IN TOP-LEFT CORNER)
        # ═══════════════════════════════════════════════════════════════
        self._set_window_icon()

        self.current_mode = mode_manager.mode
        self.current_user = None
        self._dark_mode = True
        self._tracking_active = False
       
        # Track state for camera management
        self._was_tracking_before_calibration = False
        self._was_tracking_before_gaming = False
        self._was_tracking_before_training = False
        self._was_tracking_before_draw = False
        self._was_tracking_before_presentation = False
        self._current_page_index = 0
       
        # Page indices - Will be set dynamically
        self.GAMING_PAGE_INDEX = -1
        self.TRAINING_PAGE_INDEX = -1
        self.CALIBRATION_PAGE_INDEX = -1
        self.NOTIFICATION_PAGE_INDEX = -1
        self.AI_TRAINER_PAGE_INDEX = -1

        # 📽️ Presentation mode state
        self.presentation_viewer = None
        self._is_presenting = False
        self._last_gesture = None
        self._last_hand_position = (0, 0)

        # ═══════════════════════════════════════════════════════════════
        # 🎤 VOICE COMMAND & AI ENGINE INITIALIZATION
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "🎤"*30)
        print("🎤 INITIALIZING ACTIVE AI ENGINE (NOVA)...")
        print("🎤"*30)

        # ✅ Initialize AI Engine
        self.ai_engine = ActiveAIEngine(camera_index=0)

        # Connect AI Engine signals
        self.ai_engine.voice_command.connect(self._on_voice_command)
        self.ai_engine.command_result.connect(self._on_command_result)
        self.ai_engine.listening_started.connect(self._on_listening_started)
        self.ai_engine.listening_stopped.connect(self._on_listening_stopped)
        self.ai_engine.error_occurred.connect(self._on_ai_error)

        # Start AI Engine (voice off by default, camera handled by hand_tracker)
        self.ai_engine.set_camera(False)  # Don't use AI engine camera, use hand_tracker
        self.ai_engine.start()

        print("✅ Active AI Engine Started (Nova Ready)!")
        print("🎤"*30 + "\n")

        # ═══════════════════════════════════════════════════════════════
        # 🎤 VOICE GENDER SELECTOR
        # ═══════════════════════════════════════════════════════════════
        self.voice_selector = VoiceGenderSelector(self)
        self.voice_selector.voice_selected.connect(self._on_voice_gender_selected)
        self._selected_voice_gender = "female"  # Default
        print("🎤 Voice Gender Selector initialized (Default: Female)")

        # Voice control state
        self._voice_active = False

        # Initialize Notification System
        self.notification_manager = get_notification_manager()
        self.toast_manager = get_toast_manager()

        # ================= BACKGROUND =================
        self._setup_background()

        # ================= DRAW CANVAS =================
        self.draw_canvas = DrawCanvas()
        self.draw_canvas.set_exit_callback(self._on_draw_canvas_exit)
        self.draw_canvas.exitToDesktop.connect(self._on_draw_exit_signal)

        # ================= ROOT =================
        main = QWidget(self)
        main.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(main)

        self.root_stack = QStackedWidget()

        # Auth Screen (index 0)
        self.auth_manager = AuthManager()
        self.auth_manager.authenticated.connect(self._on_login_success)
        self.root_stack.addWidget(self.auth_manager)

        # Main App Screen (index 1)
        self.app_widget = QWidget()
        self._build_app_ui(self.app_widget)
        self.root_stack.addWidget(self.app_widget)

        # Add root_stack to main widget layout
        root_layout = QVBoxLayout(main)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.root_stack)

        self.root_stack.setCurrentIndex(0)
        self._apply_futuristic_styles()

        # ================= TIMERS =================
        self._setup_timers()

    

    # ════════════════════════════════════════════════════════════════════
    #                    🖼️ WINDOW ICON METHOD
    # ════════════════════════════════════════════════════════════════════

    def _set_window_icon(self):
        """
        🖼️ Set window icon (logo in top-left corner and taskbar)
       
        This replaces the default "Aurevix" text with your custom logo.
        The icon will appear in:
        - Window title bar (top-left corner)
        - Taskbar
        - Alt+Tab window switcher
        - All child windows/dialogs
        """
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
       
        # Search for icon in multiple locations
        icon_paths = [
            os.path.join(BASE_DIR, "GCVM", "Asset", "logo.png"),
            os.path.join(BASE_DIR, "GCVM", "Asset", "icon.png"),
            os.path.join(BASE_DIR, "GCVM", "Asset", "aurevix_icon.png"),
            os.path.join(BASE_DIR, "GCVM", "Asset", "app_icon.png"),
            os.path.join(BASE_DIR, "assets", "logo.png"),
            os.path.join(BASE_DIR, "assets", "icon.png"),
            os.path.join(BASE_DIR, "assets", "aurevix_icon.png"),
            os.path.join(BASE_DIR, "logo.png"),
            os.path.join(BASE_DIR, "icon.png"),
            os.path.join(BASE_DIR, "aurevix_icon.png"),
            os.path.join(BASE_DIR, "app_icon.png"),
        ]
       
        for path in icon_paths:
            if os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    # Set for this window
                    self.setWindowIcon(icon)
                    # Set for entire application (all windows)
                    QApplication.setWindowIcon(icon)
                    print(f"✅ Window icon set: {os.path.basename(path)}")
                    return
       
        print("⚠️ No icon file found - using default system icon")
        print("   Expected locations:")
        print("   - GCVM/Asset/logo.png")
        print("   - assets/logo.png")
        print("   - logo.png (in project root)")

    # ════════════════════════════════════════════════════════════════════
    #                    🎤 VOICE COMMAND HANDLERS
    # ════════════════════════════════════════════════════════════════════

    def _on_voice_command(self, command_text):
        """Handle raw voice command detected by AI Engine"""
        print(f"\n🗣️ VOICE COMMAND: '{command_text}'")
       
        if self.current_user:
            self.logs_page.add_log_entry("VOICE", f"Command: '{command_text}'")

    def _on_command_result(self, result):
        """Handle command execution result from AI Engine"""
        print(f"✅ COMMAND RESULT: {result}")
       
        if self.current_user:
            status = "SUCCESS" if result.success else "FAILED"
            self.logs_page.add_log_entry("VOICE_CMD", f"{status}: {result.message}")
       
        if result.action == "STOP_LISTEN":
            self._toggle_voice_listening(False)

    def _on_listening_started(self):
        """
        🎤 Handle voice listening started signal
        ✅ FIXED: Async greeting with selected voice gender
        """
        print("\n" + "🎤"*30)
        print("🎤 VOICE LISTENING ACTIVATED")
        print("🎤"*30)
    
        self._voice_active = True
    
        # ═══════════════════════════════════════════════════════════════
        # ✅ ASYNC GREETING WITH SELECTED VOICE
        # ═══════════════════════════════════════════════════════════════
        selected_gender = getattr(self, '_selected_voice_gender', 'female')
    
        def speak_greeting_async():
            """Run TTS in background thread with selected voice"""
            try:
                import subprocess
                import platform
                from datetime import datetime
            
                # Get time-based greeting
                hour = datetime.now().hour
                if 5 <= hour < 12:
                    time_greet = "Good morning"
                elif 12 <= hour < 17:
                    time_greet = "Good afternoon"
                elif 17 <= hour < 24:
                    time_greet = "Good evening"
                else:
                    time_greet = "Hello"
            
                # ✅ Name based on gender
                assistant_name = "Nova" if selected_gender == "female" else "Nick"
                greeting_text = f"{time_greet}! I'm {assistant_name}. How may I help you?"
                
            
                if platform.system() == "Windows":
                    # ═══════════════════════════════════════════════════
                    # ✅ SELECT VOICE BASED ON GENDER
                    # ═══════════════════════════════════════════════════
                    if selected_gender == "male":
                        voice_select = (
                            "foreach ($v in $speak.GetInstalledVoices()) { "
                            "  if ($v.VoiceInfo.Name -like '*David*') { "
                            "    $speak.SelectVoice($v.VoiceInfo.Name); break "
                            "  } "
                            "}; "
                        )
                    else:
                        voice_select = (
                            "foreach ($v in $speak.GetInstalledVoices()) { "
                            "  if ($v.VoiceInfo.Name -like '*Zira*') { "
                            "    $speak.SelectVoice($v.VoiceInfo.Name); break "
                            "  } "
                            "}; "
                        )
                
                    ps_cmd = (
                        f'Add-Type -AssemblyName System.Speech; '
                        f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                        f'$speak.Rate = 1; '
                        f'{voice_select}'
                        f'$speak.Speak("{greeting_text}")'
                    )
                
                    process = subprocess.Popen(
                        ['powershell', '-Command', ps_cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    process.wait()
                
                elif platform.system() == "Darwin":
                    voice = "Samantha" if selected_gender == "female" else "Alex"
                    process = subprocess.Popen(
                        ['say', '-v', voice, greeting_text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    process.wait()
                else:
                    pitch = "80" if selected_gender == "female" else "50"
                    try:
                        process = subprocess.Popen(
                            ['espeak', '-p', pitch, greeting_text],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        process.wait()
                    except:
                        pass
                    
            except Exception as e:
                print(f"  ⚠️ Greeting error: {e}")
        
            finally:
                print("  ✅ Greeting done - waiting for audio to clear...")
                time.sleep(2.0)  # ← 2 SECONDS wait after speech ends
    
                if hasattr(self, 'ai_engine'):
                    self.ai_engine.is_speaking = False
                    self.ai_engine.mic_paused = False
                    self.ai_engine._greeting_done = True
                    self.ai_engine._greeting_time = time.time()
        
                    if hasattr(self.ai_engine, 'cmd_processor'):
                        self.ai_engine.cmd_processor._greeting_cooldown = time.time()
        
                    print("  🎤 Mic RESUMED!")
    
        # ✅ Start greeting in BACKGROUND THREAD
        threading.Thread(target=speak_greeting_async, daemon=True).start()
    
        # ═══════════════════════════════════════════════════════════════
        # ✅ UI UPDATES (immediate)
        # ═══════════════════════════════════════════════════════════════
        if hasattr(self, 'futuristic_dashboard') and hasattr(self.futuristic_dashboard, 'voice_btn'):
            self._set_voice_button_active(self.futuristic_dashboard.voice_btn, True)
    
        if self.current_user:
            gender_text = "Female" if selected_gender == "female" else "Male"
            self.logs_page.add_log_entry("VOICE", f"Voice activated ({gender_text} voice)")
    
        print(f"\n✅ Voice active - {'👩 Female' if selected_gender == 'female' else '👨 Male'} voice")
        print("🎤"*30 + "\n")

    def _on_listening_stopped(self):
        """Handle voice listening stopped - Update UI"""
        print("🔇 Voice listening STOPPED")
        self._voice_active = False
       
        # Update voice button style in dashboard
        if hasattr(self, 'futuristic_dashboard') and hasattr(self.futuristic_dashboard, 'voice_btn'):
            self._set_voice_button_active(self.futuristic_dashboard.voice_btn, False)
       
        if self.current_user:
            self.logs_page.add_log_entry("VOICE", "Voice listening deactivated")

    def _on_ai_error(self, error_message):
        """Handle AI Engine errors"""
        print(f"⚠️ AI ENGINE ERROR: {error_message}")
       
        if self.current_user:
            self.logs_page.add_log_entry("ERROR", f"AI Engine: {error_message}")
       
        self.toast_manager.show_toast(
            "⚠️ AI Engine Error",
            error_message,
            duration=4000
        )

    def _toggle_voice_listening(self, enabled=None):
        """
        Toggle voice listening on/off.
        ✅ FIXED: Shows voice gender dropdown before starting
        """
        print(f"\n{'='*50}")
        print(f"🎤 TOGGLE VOICE CALLED")
        print(f"   Current: {self._voice_active}")
        print(f"   Requested: {enabled}")
        print(f"{'='*50}")

        if enabled is None:
            enabled = not self._voice_active

        if enabled:
            # ═══════════════════════════════════════════════════════
            # ✅ SHOW VOICE GENDER DROPDOWN
            # ═══════════════════════════════════════════════════════
            try:
                if hasattr(self, 'futuristic_dashboard') and hasattr(self.futuristic_dashboard, 'voice_btn'):
                    btn = self.futuristic_dashboard.voice_btn
                    btn_pos = btn.mapToGlobal(QPoint(btn.width() // 2, 0))
                    print(f"  📍 Showing dropdown at: {btn_pos.x()}, {btn_pos.y()}")
                    self.voice_selector.show_at(btn_pos)
                else:
                    print("  ⚠️ No voice button found - starting directly")
                    self._start_voice_with_gender(self._selected_voice_gender)
            except Exception as e:
                print(f"  ❌ Dropdown error: {e}")
                import traceback
                traceback.print_exc()
                # Fallback: start directly without dropdown
                self._start_voice_with_gender(self._selected_voice_gender)
        else:
            print("🔇 Stopping voice...")
            self.ai_engine.stop_voice()
    def _on_voice_gender_selected(self, gender):
        """
        Handle voice gender selection from dropdown.
    
        Args:
            gender: "male" or "female"
        """
        print(f"\n🎤 Voice Gender Selected: {'👩 Female' if gender == 'female' else '👨 Male'}")
    
        self._selected_voice_gender = gender
    
        # ✅ Update AudioManager voice in command processor
        if hasattr(self, 'ai_engine') and hasattr(self.ai_engine, 'cmd_processor'):
            self.ai_engine.cmd_processor.audio.set_voice_gender(gender)
            print(f"  🔊 Command Processor voice: {gender}")
    
        # ✅ Start voice listening with selected gender
        self._start_voice_with_gender(gender)

    def _start_voice_with_gender(self, gender):
        print(f"\n🚀 Starting voice with {'👩 Female' if gender == 'female' else '👨 Male'} voice...")
    
        # Set voice gender in AudioManager
        if hasattr(self, 'ai_engine') and hasattr(self.ai_engine, 'cmd_processor'):
            self.ai_engine.cmd_processor.audio.set_voice_gender(gender)
        
            # ✅ NEW: Connect page switcher so voice can navigate tabs
            self.ai_engine.cmd_processor.set_page_switcher(self.switch_page)
            print("  🔗 Page switcher connected to voice processor")
    
        # Start AI Engine voice
        self.ai_engine.start_voice()

    def _set_voice_button_active(self, button, is_active):
        """Update voice button visual style"""
        if is_active:
            button.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 230, 118, 0.4);
                    border: 2px solid rgba(0, 230, 118, 0.8);
                    border-radius: 10px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(0, 230, 118, 0.6);
                }
            """)
            button.setToolTip("🎤 Voice Active (Nova) - Click to stop")
        else:
            button.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 193, 7, 0.15);
                    border: 1px solid rgba(255, 193, 7, 0.4);
                    border-radius: 10px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 193, 7, 0.3);
                    border: 1px solid rgba(255, 193, 7, 0.7);
                }
            """)
            button.setToolTip("🎤 Voice Control (Nova) - Click to start")

    # ════════════════════════════════════════════════════════════════════
    #                    SETUP METHODS
    # ════════════════════════════════════════════════════════════════════

    def _setup_background(self):
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(self.rect())
        self.bg_label.lower()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(BASE_DIR, "GCVM", "Asset", "Aurevix.jpeg")

        if os.path.exists(self.bg_path):
            self.original_pixmap = QPixmap(self.bg_path)
        else:
            self.original_pixmap = None

        self._update_background()

    def resizeEvent(self, event):
        self.bg_label.setGeometry(self.rect())
        self._update_background()
        super().resizeEvent(event)

    def _update_background(self):
        if self.original_pixmap:
            scaled = self.original_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.bg_label.setPixmap(scaled)
        else:
            self.bg_label.setStyleSheet("""
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a1a,
                    stop:0.3 #0d1025,
                    stop:0.6 #10122a,
                    stop:1 #0a0a1a);
            """)

    def _setup_timers(self):
        """Initialize all application timers"""
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("statusLabel")

        # Dashboard status update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard_status)
        self.timer.start(1500)

        # Frame reading timer
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self._read_shared_frame)

        # FPS calculation
        self._frame_count = 0
        self._current_fps = 0
        self.fps_calc_timer = QTimer()
        self.fps_calc_timer.timeout.connect(self._calc_fps)
        self.fps_calc_timer.start(1000)

        # Usage tracking
        self.session_start = None
        self.usage_timer = QTimer()
        self.usage_timer.timeout.connect(self._track_usage)
        self.usage_timer.start(60000)

        self.autoclear_timer = None
       
        # 📽️ Gesture polling timer for presentation mode
        self.gesture_poll_timer = QTimer()
        self.gesture_poll_timer.timeout.connect(self._poll_gestures_for_presentation)
        self.gesture_poll_timer.setInterval(100)

    def _build_app_ui(self, container):
        """Build the main application UI"""
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════════
        # TOP NAVIGATION
        # ═══════════════════════════════════════════════════════════════
        self.top_nav = TopNavigation()
        self.top_nav.pageRequested.connect(self.switch_page)
        self.top_nav.themeToggled.connect(self._toggle_theme)
        self.top_nav.logoutRequested.connect(self._on_logout)
        self.top_nav.profileEditRequested.connect(self._edit_profile)
        self.top_nav.notificationPageRequested.connect(self._show_notification_page)
        main_layout.addWidget(self.top_nav)

        # ═══════════════════════════════════════════════════════════════
        # BODY (Sidebar + Content Stack)
        # ═══════════════════════════════════════════════════════════════
        body = QHBoxLayout()
        body.setContentsMargins(10, 5, 10, 10)
        body.setSpacing(10)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.pageRequested.connect(self.switch_page)
        self.sidebar.logoutRequested.connect(self._on_logout)
        self.sidebar.profileEditRequested.connect(self._edit_profile)
        self.sidebar.exitRequested.connect(self.close)
        body.addWidget(self.sidebar)

        # ═══════════════════════════════════════════════════════════════
        # CONTENT STACK
        # ═══════════════════════════════════════════════════════════════
        self.stack = QStackedWidget()
        self._build_stack_pages()

        body.addWidget(self.stack, 1)
        main_layout.addLayout(body, 1)

        # Connect settings and preferences
        self._connect_settings()
        self._connect_preferences()
        mode_manager.set_settings(self.settings_page)

        # Start on dashboard
        self.switch_page(0)

    def _build_stack_pages(self):
        """Build all stack pages with correct indices"""
        print("\n" + "═"*60)
        print("📋 BUILDING STACK PAGES IN ORDER...")
        print("═"*60)

        # ═══════════════════════════════════════════════════════════════
        # INDEX 0 - FUTURISTIC DASHBOARD (Home)
        # ═══════════════════════════════════════════════════════════════
        self.futuristic_dashboard = FuturisticDashboard()
        self.futuristic_dashboard.startTrackingRequested.connect(self._start_tracking)
        self.futuristic_dashboard.stopTrackingRequested.connect(self._stop_tracking)
        self.futuristic_dashboard.modeChanged.connect(self.set_mode)
        self.futuristic_dashboard.mirrorChanged.connect(self._set_mirror)
        self.futuristic_dashboard.screenshotRequested.connect(self._take_screenshot)
        self.futuristic_dashboard.gamingPageRequested.connect(self._open_gaming_mode)
        self.futuristic_dashboard.trainingModeRequested.connect(self._open_training_mode)
       
        if hasattr(self.futuristic_dashboard, 'presentationModeRequested'):
            self.futuristic_dashboard.presentationModeRequested.connect(self._open_presentation_dialog)
       
        # 🎤 Connect voice button to toggle function
        if hasattr(self.futuristic_dashboard, 'voice_btn'):
            try:
                self.futuristic_dashboard.voice_btn.clicked.disconnect()
            except:
                pass
            self.futuristic_dashboard.voice_btn.clicked.connect(lambda: self._toggle_voice_listening())
       
        self.stack.addWidget(self.futuristic_dashboard)
        print(f"  ✅ Index {self.stack.count()-1}: Futuristic Dashboard (🎤 Voice Connected)")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 1 - GESTURES PAGE
        # ═══════════════════════════════════════════════════════════════
        self.gestures_page = GesturesPage(self.draw_canvas, self)
        self.gestures_page.modeChanged.connect(self.set_mode)
        self.gestures_page.gestureAdded.connect(self._on_gesture_added)
        self.gestures_page.gestureDeleted.connect(self._on_gesture_changed)
        self.gestures_page.gestureToggled.connect(self._on_gesture_changed)  
        self.stack.addWidget(self.gestures_page)
        print(f"  ✅ Index {self.stack.count()-1}: Gestures Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 2 - SHORTCUTS PAGE
        # ═══════════════════════════════════════════════════════════════
        self.shortcuts_page = ShortcutsPage()
        self.shortcuts_page.shortcutsToggled.connect(self._on_shortcuts_toggled)
        self.stack.addWidget(self.shortcuts_page)
        print(f"  ✅ Index {self.stack.count()-1}: Shortcuts Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 3 - LOGS PAGE
        # ═══════════════════════════════════════════════════════════════
        self.logs_page = LogsPage()
        self.stack.addWidget(self.logs_page)
        print(f"  ✅ Index {self.stack.count()-1}: Logs Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 4 - SETTINGS PAGE
        # ═══════════════════════════════════════════════════════════════
        self.settings_page = SettingsPanel(self)
        self.settings_page.openCalibrationRequested.connect(self._open_calibration_from_settings)
        self.stack.addWidget(self.settings_page)
        print(f"  ✅ Index {self.stack.count()-1}: Settings Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 5 - PREFERENCES PAGE
        # ═══════════════════════════════════════════════════════════════
        self.preferences_page = PreferencesPage()
        self.stack.addWidget(self.preferences_page)
        print(f"  ✅ Index {self.stack.count()-1}: Preferences Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 6 - AI TRAINER (Placeholder)
        # ═══════════════════════════════════════════════════════════════
        self.ai_trainer_page = AITrainerPage()
        self.ai_trainer_page.back_clicked.connect(lambda: self.switch_page(0))
        self.stack.addWidget(self.ai_trainer_page)
        self.AI_TRAINER_PAGE_INDEX = self.stack.count() - 1
        print(f"  🤖 Index {self.AI_TRAINER_PAGE_INDEX}: AI TRAINER PAGE (Full Analytics)")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 7 - CALIBRATION PAGE
        # ═══════════════════════════════════════════════════════════════
        self.calibration_page = CalibrationPage()
        self.calibration_page.calibrationComplete.connect(self._on_calibration_complete)
        self.calibration_page.openPreferencesRequested.connect(self._open_preferences_from_calibration)
        self.stack.addWidget(self.calibration_page)
        self.CALIBRATION_PAGE_INDEX = self.stack.count() - 1
        print(f"  🔧 Index {self.CALIBRATION_PAGE_INDEX}: Calibration Page")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 8 - 🎮 GAMING MODE PAGE (CAMERA STATE PRESERVED)
        # ═══════════════════════════════════════════════════════════════
        self.gaming_page = GamingModePage()
        self.gaming_page.mode_closed.connect(self._on_gaming_mode_closed)
       
        # ✅ FIXED: Connect switch_to_desktop signal with bool parameter
        if hasattr(self.gaming_page, 'switch_to_desktop'):
            print("  🔌 Connecting Gaming Mode → Desktop Exit (Camera State Preserved)...")
            self.gaming_page.switch_to_desktop.connect(self._activate_desktop_from_gaming)
        else:
            print("  ⚠️ Gaming page missing 'switch_to_desktop' signal!")
       
        self.stack.addWidget(self.gaming_page)
        self.GAMING_PAGE_INDEX = self.stack.count() - 1
        print(f"  🎮 Index {self.GAMING_PAGE_INDEX}: GAMING MODE (ON→ON, OFF→OFF)")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 9 - 🎯 TRAINING MODE PAGE
        # ═══════════════════════════════════════════════════════════════
        self.training_page = TrainingModePage()
        self.training_page.mode_closed.connect(self._on_training_mode_closed)
        self.stack.addWidget(self.training_page)
        self.TRAINING_PAGE_INDEX = self.stack.count() - 1
        print(f"  🎯 Index {self.TRAINING_PAGE_INDEX}: TRAINING MODE PAGE")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 10-13 - PLACEHOLDERS
        # ═══════════════════════════════════════════════════════════════
        placeholders = [
            ("📊 Performance", "View performance metrics"),
            ("👤 Profiles", "Manage gesture profiles"),
            ("☁️ Cloud Sync", "Sync settings across devices"),
            ("🔒 Privacy Center", "Manage privacy settings"),
        ]
        for title, desc in placeholders:
            self.stack.addWidget(PlaceholderPage(title, desc))
            print(f"  ⬜ Index {self.stack.count()-1}: {title}")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 14 - 🔔 NOTIFICATION PAGE
        # ═══════════════════════════════════════════════════════════════
        self.notification_page = NotificationPage()
        self.notification_page.notificationClicked.connect(self._on_notification_clicked)
        self.stack.addWidget(self.notification_page)
        self.NOTIFICATION_PAGE_INDEX = self.stack.count() - 1
        print(f"  🔔 Index {self.NOTIFICATION_PAGE_INDEX}: NOTIFICATION PAGE")

        # ═══════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════
        print("═"*60)
        print(f"📊 TOTAL PAGES: {self.stack.count()}")
        print(f"🎮 GAMING_PAGE_INDEX = {self.GAMING_PAGE_INDEX}")
        print(f"🎯 TRAINING_PAGE_INDEX = {self.TRAINING_PAGE_INDEX}")
        print(f"🔧 CALIBRATION_PAGE_INDEX = {self.CALIBRATION_PAGE_INDEX}")
        print(f"🔔 NOTIFICATION_PAGE_INDEX = {self.NOTIFICATION_PAGE_INDEX}")
        print("═"*60 + "\n")

    # ════════════════════════════════════════════════════════════════════
    #                    📽️ PRESENTATION MODE METHODS (FIXED)
    # ════════════════════════════════════════════════════════════════════

    def _open_presentation_dialog(self):
        """Open Presentation Dialog to add media"""
        print("\n" + "📽️"*20)
        print("📽️ OPENING PRESENTATION DIALOG")
        print("📽️"*20 + "\n")
       
        # Save tracking state
        self._was_tracking_before_presentation = self._tracking_active
       
        # Open dialog
        dialog = PresentationDialog(self)
        dialog.presentation_started.connect(self._start_presentation_viewer)
        dialog.exec()
       
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("PRESENTATION", "Presentation dialog opened")

    def _start_presentation_viewer(self, slides):
        """
        ✅ FIXED: Start the fullscreen presentation viewer with gesture control
        - Hides main window
        - Stops main tracking
        - Starts dedicated presentation tracking
        - Adds WindowStaysOnTopHint
        """
        print(f"\n📽️ Starting Presentation with {len(slides)} slides")
       
        # ✅ FIX 1: HIDE MAIN WINDOW
        print("  🔹 Hiding main window...")
        self.hide()
       
        # ✅ FIX 2: STOP MAIN TRACKING
        if self._tracking_active:
            print("  🔹 Stopping main tracking...")
            self._stop_tracking()
       
        # Set presentation flag
        self._is_presenting = True
       
        # ✅ FIX 3: CLEAN UP OLD VIEWER
        if self.presentation_viewer is not None:
            print("  🔹 Cleaning up old viewer...")
            self.presentation_viewer.close()
            self.presentation_viewer.deleteLater()
            self.presentation_viewer = None
            QApplication.processEvents()
       
        # Create viewer
        self.presentation_viewer = PresentationViewer(slides, self)
        self.presentation_viewer.closed.connect(self._on_presentation_closed)
        self.presentation_viewer.draw_requested.connect(self._start_presentation_draw_mode)
       
        # ✅ FIX 4: ADD WINDOW FLAGS
        self.presentation_viewer.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint  # ← CRITICAL
        )
       
        # Show fullscreen
        self.presentation_viewer.showFullScreen()
        self.presentation_viewer.raise_()
        self.presentation_viewer.activateWindow()
       
        # ✅ FIX 5: START DEDICATED PRESENTATION TRACKING
        QTimer.singleShot(500, self._start_presentation_tracking)
       
        # Log
        if self.current_user:
            self.logs_page.add_log_entry("PRESENTATION", f"Started with {len(slides)} slides")
       
        # Toast
        self.toast_manager.show_toast(
            "📽️ Presentation Started",
            "Use gestures: 👉 Next, 👈 Prev, ✌️ Draw, ✊ Exit",
            duration=4000
        )
       
        print("✅ Presentation viewer active!")

    def _start_presentation_tracking(self):
        """
        ✅ NEW: Start lightweight tracking ONLY for presentation gestures
        """
        print("▶️ Starting presentation-specific tracking...")
       
        # Use EXISTING hand_tracker thread, just enable gesture detection
        hand_tracker.set_camera_state(True)
        hand_tracker.set_gesture_state(True)
       
        # Start gesture polling ONLY (not full frame processing)
        self.gesture_poll_timer.start(100)
       
        print("✅ Presentation tracking active")

    def _stop_presentation_tracking(self):
        """
        ✅ NEW: Stop presentation tracking
        """
        print("⏹ Stopping presentation tracking...")
       
        self.gesture_poll_timer.stop()
        hand_tracker.set_camera_state(False)
        hand_tracker.set_gesture_state(False)
       
        print("✅ Presentation tracking stopped")

    def _poll_gestures_for_presentation(self):
        """
        ✅ FIXED: Poll for gestures and forward to presentation viewer
        - Added tracking state check
        - Removed camera mini-view (causes lag)
        """
        if not self._is_presenting or not self.presentation_viewer:
            self.gesture_poll_timer.stop()
            return
       
        # ✅ FIX: CHECK IF TRACKING IS ACTUALLY ACTIVE
        if not hand_tracker.camera_active or not hand_tracker.gesture_active:
            return  # Don't process if tracking is off
       
        # Get current gesture from mode_manager
        current_gesture = getattr(mode_manager, 'current_gesture', None)
       
        # Only process if gesture changed
        if current_gesture and current_gesture != self._last_gesture:
            print(f"📽️ Gesture: {current_gesture}")
           
            if hasattr(self.presentation_viewer, 'handle_gesture'):
                self.presentation_viewer.handle_gesture(current_gesture)
           
            self._last_gesture = current_gesture
       
        # Get hand position for pointer
        hand_pos = getattr(mode_manager, 'hand_position', None)
        if hand_pos and hand_pos != self._last_hand_position:
            if hasattr(self.presentation_viewer, 'update_pointer'):
                norm_x = hand_pos[0] / 640.0 if len(hand_pos) > 0 else 0
                norm_y = hand_pos[1] / 480.0 if len(hand_pos) > 1 else 0
                self.presentation_viewer.update_pointer(norm_x, norm_y)
            self._last_hand_position = hand_pos

    def _on_presentation_closed(self):
        """
        ✅ FIXED: Handle presentation viewer closed
        - Stops tracking
        - Shows main window
        - Flushes event queue
        - Forces garbage collection
        """
        print("\n📤 Presentation Viewer closed\n")
       
        # Stop tracking
        self._stop_presentation_tracking()
       
        # Clean up viewer
        if self.presentation_viewer:
            self.presentation_viewer.close()
            self.presentation_viewer.deleteLater()
            self.presentation_viewer = None
       
        # Reset state
        self._is_presenting = False
        self._last_gesture = None
        self._last_hand_position = (0, 0)
       
        # ✅ FIX: FORCE GARBAGE COLLECTION
        gc.collect()
       
        # ✅ FIX: SHOW MAIN WINDOW BACK
        self.show()
        self.raise_()
        self.activateWindow()
       
        # ✅ FIX: FLUSH EVENT QUEUE
        QApplication.processEvents()
       
        # Resume normal tracking if it was active
        if self._was_tracking_before_presentation:
            QTimer.singleShot(500, self._start_tracking)  # ← Delay to prevent conflict
            self._was_tracking_before_presentation = False
       
        # Log
        if self.current_user:
            self.logs_page.add_log_entry("PRESENTATION", "Presentation ended")
       
        # Toast
        self.toast_manager.show_toast(
            "🏠 Presentation Ended",
            "Returned to dashboard",
            duration=2000
        )

    def _start_presentation_draw_mode(self):
        """
        ✅ FIXED: Start draw mode over the presentation
        - Stops presentation tracking
        - Starts draw canvas
        """
        print("\n🎨 STARTING DRAW ANNOTATION ON PRESENTATION\n")
       
        # ✅ FIX: STOP PRESENTATION TRACKING
        self._stop_presentation_tracking()
       
        # Apply draw settings from preferences
        if hasattr(self, 'preferences_page'):
            try:
                if hasattr(self.preferences_page, 'get_pen_color'):
                    pen_color = self.preferences_page.get_pen_color()
                    if pen_color:
                        self.draw_canvas.set_color(pen_color)
               
                if hasattr(self.preferences_page, 'get_pen_thickness'):
                    thickness = self.preferences_page.get_pen_thickness()
                    if thickness:
                        self.draw_canvas.set_pen_size(thickness)
            except Exception as e:
                print(f"  ⚠️ Could not load preferences: {e}")
       
        # Start draw canvas
        self.draw_canvas.start_draw()
       
        # Log
        if self.current_user:
            self.logs_page.add_log_entry("PRESENTATION", "Draw annotation started")
       
        # Toast
        self.toast_manager.show_toast(
            "🎨 Annotation Mode",
            "Draw on slides! ✊ Fist to exit",
            duration=2500
        )

    # ════════════════════════════════════════════════════════════════════
    #                    🎨 DRAW CANVAS METHODS (FIXED)
    # ════════════════════════════════════════════════════════════════════

    def _on_draw_canvas_exit(self, target_mode="DESKTOP"):
        """
        ✅ FIXED: Called when Draw Canvas exits
        - Restarts presentation tracking if presentation is active
        - Flushes event queue
        """
        print(f"\n🎨 DRAW CANVAS EXITED - Mode: {target_mode}\n")
       
        # Check if presentation is active
        if self._is_presenting and self.presentation_viewer is not None:
            print("  📽️ Presentation still active - returning to viewer")
           
            # ✅ FIX: RESTART PRESENTATION TRACKING
            QTimer.singleShot(300, self._start_presentation_tracking)
           
            # ✅ FIX: FLUSH EVENT QUEUE
            QApplication.processEvents()
           
            # Bring presentation back to front
            self.presentation_viewer.raise_()
            self.presentation_viewer.activateWindow()
           
            if self.current_user:
                self.logs_page.add_log_entry("PRESENTATION", "Draw overlay closed")
           
            self.toast_manager.show_toast(
                "📽️ Back to Presentation",
                "Annotation closed. Continue presenting!",
                duration=2000
            )
            return
       
        # Normal draw mode exit
        self.current_mode = target_mode
        mode_manager.set_mode(target_mode)
       
        if hasattr(self, 'futuristic_dashboard'):
            self.futuristic_dashboard.update_mode_cards(target_mode)
       
        if hasattr(self, 'gestures_page'):
            self.gestures_page.update_mode_buttons(target_mode)
       
        if self._was_tracking_before_draw:
            print("  ▶️  Restoring main tracking...")
            QTimer.singleShot(300, self._start_tracking)
            self._was_tracking_before_draw = False
       
        if self.current_user:
            self.logs_page.add_log_entry("DRAW", f"Draw Canvas closed - switched to {target_mode} mode")
       
        self.toast_manager.show_toast(
            f"🖥️ {target_mode} Mode Active",
            "Draw mode exited.",
            duration=2500
        )

    def _on_draw_exit_signal(self):
        """Signal handler for exitToDesktop signal"""
        print("📡 exitToDesktop signal received")

    # ════════════════════════════════════════════════════════════════════
    #                    🔔 NOTIFICATION METHODS
    # ════════════════════════════════════════════════════════════════════

    def _show_notification_page(self):
        """Show notification page"""
        print(f"🔔 Opening Notification Page (Index {self.NOTIFICATION_PAGE_INDEX})...")
        self.switch_page(self.NOTIFICATION_PAGE_INDEX)
        if hasattr(self.notification_page, 'refresh'):
            self.notification_page.refresh()

    def _on_notification_clicked(self, notification):
        """Handle notification click"""
        print(f"🔔 Notification clicked: {notification.title}")
       
        if notification.type.value == "calibration":
            self.switch_page(self.CALIBRATION_PAGE_INDEX)
        elif notification.type.value == "gesture":
            self.switch_page(self.PAGE_GESTURES)
        elif notification.type.value == "system":
            self.switch_page(self.PAGE_SETTINGS)
        else:
            self.switch_page(0)

    # ════════════════════════════════════════════════════════════════════
    #                    🔧 CALIBRATION METHODS
    # ════════════════════════════════════════════════════════════════════

    def _open_calibration_from_settings(self):
        """Open calibration page from settings panel"""
        self.switch_page(self.CALIBRATION_PAGE_INDEX)
        if self.current_user:
            self.logs_page.add_log_entry("NAVIGATION", "Opened Calibration from Settings")

    def _on_calibration_complete(self):
        """Handle calibration completion"""
        print("✅ Calibration complete")
        if hasattr(self.settings_page, 'calibration_card'):
            QTimer.singleShot(100, self.settings_page.calibration_card.refresh)
        if self.current_user:
            self.logs_page.add_log_entry("CALIBRATION", "Calibration completed successfully")
        self.toast_manager.show_toast("✅ Calibration Complete", "Hand tracking margins calibrated!", duration=3000)

    def _open_preferences_from_calibration(self):
        """Navigate to preferences page from calibration page"""
        self.switch_page(self.PAGE_PREFERENCES)

    # ════════════════════════════════════════════════════════════════════
    #                    🎮 GAMING MODE METHODS (✅ CAMERA STATE PRESERVED)
    # ════════════════════════════════════════════════════════════════════

    def _open_gaming_mode(self):
        """
        ✅ FIXED: Open Gaming Mode - CAMERA STAYS ON
        """
        print("\n" + "🎮"*30)
        print(f"🎮 OPENING GAMING MODE PAGE (Index {self.GAMING_PAGE_INDEX})")
        print("🎮"*30 + "\n")
   
        # Save tracking state
        self._was_tracking_before_gaming = self._tracking_active
        print(f"  📸 Camera state: {'ON ✅' if self._tracking_active else 'OFF ❌'}")
   
        # ═══════════════════════════════════════════════════════════════
        # ✅ FIX: DO NOT STOP TRACKING! Just pause dashboard frame display
        # ═══════════════════════════════════════════════════════════════
        print("  ⏸️ Pausing dashboard frame timer ONLY...")
        self.frame_timer.stop()  # Stop dashboard UI updates only
   
        # ═══════════════════════════════════════════════════════════════
        # ✅ FIX: MANUALLY switch page WITHOUT calling switch_page()
        # This bypasses the tracking stop code in switch_page()
        # ═══════════════════════════════════════════════════════════════
        print("  📄 Switching to gaming page...")
        self._current_page_index = self.GAMING_PAGE_INDEX
        self.stack.setCurrentIndex(self.GAMING_PAGE_INDEX)
        self.sidebar.set_active_page(self.GAMING_PAGE_INDEX)
   
        # Start game controller
        print("  🎮 Starting game controller...")
        game_controller.start()
   
        # ═══════════════════════════════════════════════════════════════
        # ✅ VERIFY: Camera should still be running
        # ═══════════════════════════════════════════════════════════════
        cam_state = hand_tracker.get_camera_state() if hasattr(hand_tracker, 'get_camera_state') else "unknown"
        gest_state = hand_tracker.get_gesture_state() if hasattr(hand_tracker, 'get_gesture_state') else "unknown"
        print(f"  📷 Camera after switch: {cam_state}")
        print(f"  ✋ Gestures after switch: {gest_state}")
   
        # Log
        if self.current_user:
            self.logs_page.add_log_entry("GAMING", "Gaming Mode opened")
   
        print("✅ Gaming Mode Active!\n")

    def _on_gaming_mode_closed(self):
        """
        Handle gaming mode exit (legacy method - kept for backward compatibility)
        Called when gaming page emits mode_closed signal
        """
        print("\n📤 Gaming Mode Closed (Legacy Exit)...\n")
       
        # Stop gaming controller
        game_controller.stop()
       
        # Return to dashboard
        self.switch_page(0)
       
        # Restore tracking if it was active before
        if self._was_tracking_before_gaming:
            print("  ▶️ Restoring main tracking...")
            QTimer.singleShot(300, self._start_tracking)
            self._was_tracking_before_gaming = False
       
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("GAMING", "Gaming Mode closed (legacy)")
       
        print("✅ Exited Gaming Mode (Legacy)\n")

    @Slot(bool)
    def _activate_desktop_from_gaming(self, camera_was_on):
        """
        ✅ FIXED: Handle EXIT TO DESKTOP from Gaming Mode
       
        CAMERA STATE PRESERVED:
        - Camera ON before gaming → Camera ON after exit
        - Camera OFF before gaming → Camera OFF after exit
       
        Args:
            camera_was_on (bool): Whether camera was active before entering gaming mode
        """
        print("\n" + "🖥️"*30)
        print("🖥️ ACTIVATING DESKTOP MODE FROM GAMING...")
        print(f"🖥️ Camera was: {'ON ✅' if camera_was_on else 'OFF ❌'} before gaming")
        print("🖥️"*30 + "\n")
       
        # ─────────────────────────────────────────────────────────────
        # STEP 1: STOP GAMING MODE
        # ─────────────────────────────────────────────────────────────
        print("  🎮 Stopping game controller...")
        game_controller.stop()
       
        # ─────────────────────────────────────────────────────────────
        # STEP 2: SWITCH TO DASHBOARD
        # ─────────────────────────────────────────────────────────────
        print("  🏠 Returning to dashboard...")
        self.switch_page(0)  # Dashboard = Index 0
       
        # ─────────────────────────────────────────────────────────────
        # STEP 3: SET DESKTOP MODE
        # ─────────────────────────────────────────────────────────────
        print("  🖥️ Setting DESKTOP mode...")
        self.current_mode = "DESKTOP"
        mode_manager.set_mode("DESKTOP")
       
        # ─────────────────────────────────────────────────────────────
        # STEP 4: UPDATE UI TO DESKTOP MODE
        # ─────────────────────────────────────────────────────────────
        print("  🎨 Updating UI for DESKTOP mode...")
       
        if hasattr(self, 'futuristic_dashboard'):
            self.futuristic_dashboard.update_mode_cards("DESKTOP")
       
        if hasattr(self, 'gestures_page'):
            self.gestures_page.update_mode_buttons("DESKTOP")
       
        # ─────────────────────────────────────────────────────────────
        # STEP 5: ✅ RESTORE CAMERA STATE (ON→ON, OFF→OFF)
        # ─────────────────────────────────────────────────────────────
        if camera_was_on:
            print("\n  📷 Camera was ON before → Restoring camera...")
            # Delay to prevent camera conflict with gaming cleanup
            QTimer.singleShot(300, self._start_tracking)
        else:
            print("\n  📷 Camera was OFF before → Camera stays OFF")
            # Ensure camera is stopped
            self._tracking_active = False
       
        # Reset gaming tracking state
        self._was_tracking_before_gaming = False
       
        # ─────────────────────────────────────────────────────────────
        # STEP 6: LOG ACTIVITY & NOTIFY USER
        # ─────────────────────────────────────────────────────────────
        camera_status = "ON (restored)" if camera_was_on else "OFF (unchanged)"
       
        if self.current_user:
            self.logs_page.add_log_entry("GAMING", f"Exited to Desktop Mode - Camera: {camera_status}")
       
        self.toast_manager.show_toast(
            "🖥️ Desktop Mode Active",
            f"Camera: {camera_status}",
            duration=3000
        )
       
        print(f"✅ Desktop Mode Activated! Camera: {camera_status}")
        print("🖥️"*30 + "\n")

    # ════════════════════════════════════════════════════════════════════
    #                    🎯 TRAINING MODE METHODS
    # ════════════════════════════════════════════════════════════════════

    def _open_training_mode(self):
        """
        🎯 Open Training Mode Page DIRECTLY (REUSE existing instance)
        """
        print("\n" + "🎯"*30)
        print("🎯 OPENING TRAINING MODE PAGE (DIRECT)")
        print("🎯"*30 + "\n")

        # ✅✅✅ CHECK IF ALREADY ON TRAINING PAGE ✅✅✅
        if self._current_page_index == self.TRAINING_PAGE_INDEX:
            print("⚠️ Already on Training Mode page!")
            return
        # ✅✅✅ END ✅✅✅

        # Save tracking state
        self._was_tracking_before_training = self._tracking_active
        print(f"  📸 Camera state: {'ON ✅' if self._tracking_active else 'OFF ❌'}")

        # Pause dashboard frame timer only
        print("  ⏸️ Pausing dashboard frame timer...")
        self.frame_timer.stop()

        # ═══════════════════════════════════════════════════════════════
        # 🎯 HIDE SIDEBAR WHEN ENTERING TRAINING MODE
        # ═══════════════════════════════════════════════════════════════
        print("  🔒 Hiding sidebar...")
        self.sidebar.hide()  # ← ADD THIS LINE
        # ═══════════════════════════════════════════════════════════════

        # ✅✅✅ CRITICAL FIX: DON'T RECREATE - Just switch to existing page ✅✅✅
        print(f"  📄 Switching to Training Mode Page (Index {self.TRAINING_PAGE_INDEX})...")
   
        # ✅ IMPORTANT: Use switch_page() to properly handle page transitions
        # This ensures proper cleanup of previous page
        self.switch_page(self.TRAINING_PAGE_INDEX)
        # ✅✅✅ END FIX ✅✅✅

        # Log
        if self.current_user:
            self.logs_page.add_log_entry("TRAINING", "Training Mode opened")

        print("✅ Training Mode Active!\n")

    def _on_training_mode_closed(self):
        """
        ✅ FIXED: Handle training mode close signal
        - Training page handles its own camera cleanup
        - Just return to dashboard and restore main camera
        """
        print("\n" + "🏠"*30)
        print("🏠 TRAINING MODE CLOSED - RETURNING TO DASHBOARD")
        print("🏠"*30 + "\n")

        # ═══════════════════════════════════════════════════════════════
        # 🔓 SHOW SIDEBAR WHEN EXITING TRAINING MODE
        # ═══════════════════════════════════════════════════════════════
        print("  🔓 Showing sidebar...")
        self.sidebar.show()  # ← ADD THIS LINE
        # ═══════════════════════════════════════════════════════════════

        # Return to dashboard
        self.switch_page(0)

        # Restore main camera if it was running before
        if self._was_tracking_before_training:
            print("  ▶️ Restoring main camera...")
            QTimer.singleShot(500, self._start_tracking)  # ← Delay to prevent conflict
            self._was_tracking_before_training = False

        # Log
        if self.current_user:
            self.logs_page.add_log_entry("TRAINING", "Training Mode closed")

        # Toast
        self.toast_manager.show_toast(
            "🏠 Welcome Back",
            "Training Mode closed",
            duration=2000
        )

        print("✅ Returned to Dashboard\n")

    # ════════════════════════════════════════════════════════════════════════
    #                    🤖 AI TRAINER DATA METHODS
    # ════════════════════════════════════════════════════════════════════════

    def save_training_session(self, session_data):
        """
        Save training session data for AI Trainer analytics
        Called from TrainingModePage/AdaptiveTrainer when session ends
        """
        import json
   
        data_file = "adaptive_training_data.json"
   
        # Load existing data
        try:
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {
                    "total_sessions": 0,
                    "total_attempts": 0,
                    "total_success": 0,
                    "best_streak": 0,
                    "highest_level": 1,
                    "total_time": 0,
                    "sessions": [],
                    "gesture_stats": {}
                }
        except:
            data = {
                "total_sessions": 0,
                "total_attempts": 0,
                "total_success": 0,
                "best_streak": 0,
                "highest_level": 1,
                "total_time": 0,
                "sessions": [],
                "gesture_stats": {}
            }
   
        # Update totals
        data["total_sessions"] += 1
        data["total_attempts"] += session_data.get("attempts", 0)
        data["total_success"] += session_data.get("success", 0)
        data["total_time"] += session_data.get("duration", 0)
   
        if session_data.get("best_streak", 0) > data["best_streak"]:
            data["best_streak"] = session_data["best_streak"]
   
        if session_data.get("level", 1) > data["highest_level"]:
            data["highest_level"] = session_data["level"]
   
        # Add session to history
        from datetime import datetime
        session_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": session_data.get("duration", 0),
            "attempts": session_data.get("attempts", 0),
            "success": session_data.get("success", 0),
            "accuracy": session_data.get("accuracy", 0),
            "level": session_data.get("level", 1),
        }
        data["sessions"].append(session_record)
   
        # Keep only last 50 sessions
        if len(data["sessions"]) > 50:
            data["sessions"] = data["sessions"][-50:]
   
        # Update gesture stats
        gesture_stats = session_data.get("gesture_stats", {})
        for gesture, stats in gesture_stats.items():
            if gesture not in data["gesture_stats"]:
                data["gesture_stats"][gesture] = {"attempts": 0, "success": 0, "accuracy": 0}
       
            data["gesture_stats"][gesture]["attempts"] += stats.get("attempts", 0)
            data["gesture_stats"][gesture]["success"] += stats.get("success", 0)
       
            # Recalculate accuracy
            total_attempts = data["gesture_stats"][gesture]["attempts"]
            total_success = data["gesture_stats"][gesture]["success"]
            if total_attempts > 0:
                data["gesture_stats"][gesture]["accuracy"] = (total_success / total_attempts) * 100
   
        # Save to file
        try:
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Training session saved to {data_file}")
        except Exception as e:
            print(f"❌ Failed to save training data: {e}")

    # ════════════════════════════════════════════════════════════════════
    #                    TRACKING METHODS
    # ════════════════════════════════════════════════════════════════════

    def _start_tracking(self):
        """Start hand_tracker camera + gesture processing."""
        cam_idx = self.futuristic_dashboard.get_selected_camera()
        if cam_idx is not None:
            config.camera_index = cam_idx
        self._tracking_active = True
        hand_tracker.set_camera_state(True)
        hand_tracker.set_gesture_state(True)
        self.frame_timer.start(33)
        self.futuristic_dashboard.set_tracking_active(True)
        if self.current_user:
            self.logs_page.add_log_entry("TRACKING", "Hand tracking started")
        print("✅ Hand tracking started")

    def _stop_tracking(self):
        """Stop hand_tracker camera & gesture processing."""
        self._tracking_active = False
        hand_tracker.set_camera_state(False)
        hand_tracker.set_gesture_state(False)
        self.frame_timer.stop()
        self.futuristic_dashboard.set_tracking_active(False)
        self._current_fps = 0
        self._frame_count = 0
        if self.current_user:
            self.logs_page.add_log_entry("TRACKING", "Hand tracking stopped")
        print("⏹ Hand tracking stopped")

    def _read_shared_frame(self):
        """Read the processed frame and send to the active page."""
        frame = mode_manager.shared_frame
        self._frame_count += 1
        current_idx = self.stack.currentIndex()
       
        if current_idx == 0:
            if frame is not None:
                self.futuristic_dashboard.update_frame(frame)
        elif current_idx == self.GAMING_PAGE_INDEX:
            if frame is not None and hasattr(self, 'gaming_page'):
                self.gaming_page.update_camera_feed()
        elif current_idx == self.TRAINING_PAGE_INDEX:
            if frame is not None and hasattr(self, 'training_page'):
                self.training_page.update_camera_feed()
       
        if hasattr(self, 'settings_page') and current_idx == self.PAGE_SETTINGS:
            if frame is not None:
                self.settings_page.receive_frame(frame)

    def _calc_fps(self):
        """Calculate FPS from frame count."""
        if self._tracking_active:
            self._current_fps = self._frame_count
            self._frame_count = 0
            self.futuristic_dashboard.update_fps(self._current_fps)

    def _set_mirror(self, checked):
        """Set mirror mode"""
        config.mirror = checked
        config.save_config()

    def _take_screenshot(self):
        """Take a screenshot of current camera feed"""
        if not CV2_AVAILABLE:
            return
        frame = self.futuristic_dashboard.get_last_frame()
        if frame is None:
            return
        os.makedirs("screenshots", exist_ok=True)
        fn = f"screenshots/cap_{int(time.time())}.png"
        cv2.imwrite(fn, frame)
        print(f"📸 Screenshot saved: {fn}")
        if self.current_user:
            self.logs_page.add_log_entry("SCREENSHOT", f"Saved: {fn}")

    # ════════════════════════════════════════════════════════════════════
    #                    THEME & UI METHODS
    # ════════════════════════════════════════════════════════════════════

    def _toggle_theme(self):
        """Toggle between dark and light theme"""
        self._dark_mode = not self._dark_mode
        self.top_nav.set_theme_icon(self._dark_mode)
        config.theme = "dark" if self._dark_mode else "light"
        self.load_styles()
        config.save_config()
        if self.current_user:
            self.logs_page.add_log_entry("THEME", f"Switched to {'dark' if self._dark_mode else 'light'} mode")

    def _apply_futuristic_styles(self):
        self.load_styles()

    def load_styles(self):
        self.setStyleSheet(get_styles())

    # ════════════════════════════════════════════════════════════════════
    #                    SETTINGS & PREFERENCES CONNECTIONS
    # ════════════════════════════════════════════════════════════════════

    def _on_shortcuts_toggled(self, enabled):
        if self.current_user:
            self.logs_page.add_log_entry("SETTING", f"Shortcuts {'enabled' if enabled else 'disabled'}")

    def _on_gesture_added(self, gesture):
        if self.current_user:
            database.update_user_stats(self.current_user["id"], gestures=1)
            self.logs_page.add_log_entry("GESTURE", f"Gesture saved: {gesture['name']} ({gesture['points_count']} pts)")
        hand_tracker.reload_custom_gestures()

    def _on_gesture_changed(self, *args):
        hand_tracker.reload_custom_gestures()
        if self.current_user:
            self.logs_page.add_log_entry("GESTURE", "Gesture list updated")

    def _connect_settings(self):
        sp = self.settings_page
        sp.mirrorChanged.connect(self._on_setting_mirror)
        sp.faceBlurChanged.connect(lambda x: None)
        sp.faceFocusChanged.connect(lambda x: None)
        sp.blurIntensityChanged.connect(lambda x: None)
        sp.cameraChanged.connect(lambda x: None)
        sp.fpsChanged.connect(lambda x: None)
        sp.brightnessChanged.connect(lambda x: None)
        sp.contrastChanged.connect(lambda x: None)
        sp.saturationChanged.connect(lambda x: None)
        sp.sensitivityChanged.connect(lambda x: None)
        sp.mouseSpeedChanged.connect(lambda x: None)
        sp.scrollSpeedChanged.connect(lambda x: None)
        sp.smoothChanged.connect(lambda x: None)
        sp.audioEnabledChanged.connect(lambda x: None)
        sp.audioVolumeChanged.connect(lambda x: None)
        sp.audioMutedChanged.connect(lambda x: None)
        sp.noiseGateChanged.connect(lambda x: None)

    def _on_setting_mirror(self, checked):
        self.futuristic_dashboard.mirror_btn.setChecked(checked)

    def _connect_preferences(self):
        prefs = self.preferences_page
        prefs.themeChanged.connect(lambda x: self.load_styles())
        prefs.penColorChanged.connect(self._on_pen_color_changed)
        prefs.thicknessChanged.connect(self._on_pen_thickness_changed)
        prefs.autoclearChanged.connect(lambda x: None)
        prefs.cameraChanged.connect(lambda x: None)
        prefs.startupChanged.connect(lambda x: None)
        prefs.trayChanged.connect(lambda x: None)
        prefs.popupsChanged.connect(lambda x: None)
        prefs.skeletonChanged.connect(lambda x: None)
        prefs.fpsChanged.connect(lambda x: None)
        prefs.leftHandChanged.connect(lambda x: None)
        prefs.clickSensChanged.connect(lambda x: None)

    def _on_pen_color_changed(self, color):
        if hasattr(self, 'draw_canvas'):
            self.draw_canvas.set_color(color)

    def _on_pen_thickness_changed(self, thickness):
        if hasattr(self, 'draw_canvas'):
            self.draw_canvas.set_pen_size(thickness)

    def _sync_settings(self):
        if hasattr(self, 'settings_page') and hasattr(self.settings_page, '_sync_ui_to_config'):
            self.settings_page._sync_ui_to_config()

    def _sync_preferences(self):
        if hasattr(self, 'preferences_page') and hasattr(self.preferences_page, '_sync_ui_to_config'):
            self.preferences_page._sync_ui_to_config()

    # ════════════════════════════════════════════════════════════════════
    #                    USER AUTHENTICATION
    # ════════════════════════════════════════════════════════════════════

    def _on_login_success(self, user_data):
        self.current_user = user_data
        self.session_start = time.time()
        self.sidebar.set_user(user_data)
        self.top_nav.set_user(user_data)
        self.logs_page.set_user(user_data["id"])
        config.load_config()
        self._sync_settings()
        self._sync_preferences()
        self.root_stack.setCurrentIndex(1)
        if not hasattr(self, 'tracker_thread') or not self.tracker_thread.is_alive():
            hand_tracker.set_gui(self)
            self.tracker_thread = threading.Thread(target=hand_tracker.run_tracker, daemon=True)
            self.tracker_thread.start()
        database.log_activity(user_data["id"], "APP_START", "Application started")
        print(f"✅ Logged in as: {user_data['display_name']}")

    def _on_logout(self):
        print("🚪 Logging out...")
   
        # 🎤 Stop voice listening
        if self._voice_active:
            self._toggle_voice_listening(False)
   
        # Close presentation if active
        if self._is_presenting and self.presentation_viewer:
            self.presentation_viewer.close()
            self.presentation_viewer = None
            self._is_presenting = False
            self.gesture_poll_timer.stop()
   
        if self.current_mode == "DRAW":
            self.draw_canvas.drawing = False
            self.draw_canvas.timer.stop()
            self.draw_canvas._release_resources()
            self.draw_canvas._lift_pen()
            self.draw_canvas.hide()
   
        if self._current_page_index == self.CALIBRATION_PAGE_INDEX:
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()
   
        if self._current_page_index == self.GAMING_PAGE_INDEX:
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()
   
        # ✅ KEEP THIS - Training Page cleanup
        if self._current_page_index == self.TRAINING_PAGE_INDEX:
            if hasattr(self.training_page, 'stop_training_mode'):
                self.training_page.stop_training_mode()
   
        # ✅ REMOVED: training_hub cleanup (not needed anymore)
   
        if self._tracking_active:
            self._stop_tracking()

        config.save_config()
        database.clear_remember_me()

        self.current_user = None
        self.session_start = None
        self.sidebar.set_guest()
        self.top_nav.set_guest()
        self.logs_page.set_user(None)
        self.auth_manager.show_login()
        self.root_stack.setCurrentIndex(0)
        print("🚪 User logged out.")

    def _edit_profile(self):
        if not self.current_user:
            return
        dialog = ProfileEditDialog(self.current_user, self)
        dialog.profileUpdated.connect(self._on_profile_updated)
        dialog.exec()

    def _on_profile_updated(self, updated_data):
        self.current_user = updated_data
        self.sidebar.set_user(updated_data)
        self.top_nav.set_user(updated_data)
        if self.current_user:
            self.logs_page.add_log_entry("PROFILE", "Profile updated")

    def _track_usage(self):
        if self.current_user and self.session_start:
            database.update_user_stats(self.current_user["id"], minutes=1.0)

    # ════════════════════════════════════════════════════════════════════
    #                    DASHBOARD STATUS
    # ════════════════════════════════════════════════════════════════════

    def update_dashboard_status(self):
        if self.root_stack.currentIndex() != 1:
            return
        special_pages = [self.CALIBRATION_PAGE_INDEX, self.GAMING_PAGE_INDEX, self.TRAINING_PAGE_INDEX]
        if self._current_page_index not in special_pages:
            self.futuristic_dashboard.update_mode_cards(mode_manager.mode)
            self._sync_settings()

    def set_mode(self, mode):
        """Set current gesture mode with Draw Canvas integration"""
        previous_mode = self.current_mode
        print(f"\n🔄 MODE CHANGE: {previous_mode} → {mode}")
       
        self.current_mode = mode
        mode_manager.set_mode(mode)
       
        if hasattr(self, 'gestures_page'):
            self.gestures_page.update_mode_buttons(mode)
        if hasattr(self, 'futuristic_dashboard'):
            self.futuristic_dashboard.update_mode_cards(mode)

        if mode == "DRAW":
            print("🎨 Entering DRAW MODE...")
            self._was_tracking_before_draw = self._tracking_active
            if self._tracking_active:
                self._stop_tracking()
           
            if hasattr(self, 'preferences_page'):
                try:
                    if hasattr(self.preferences_page, 'get_pen_color'):
                        pen_color = self.preferences_page.get_pen_color()
                        if pen_color:
                            self.draw_canvas.set_color(pen_color)
                    if hasattr(self.preferences_page, 'get_pen_thickness'):
                        thickness = self.preferences_page.get_pen_thickness()
                        if thickness:
                            self.draw_canvas.set_pen_size(thickness)
                except:
                    pass
           
            self.draw_canvas.start_draw()
            if self.current_user:
                self.logs_page.add_log_entry("DRAW", "Draw Canvas started")
            self.toast_manager.show_toast("🎨 Draw Mode Active", "✊ Hold fist to exit", duration=3000)
       
        elif previous_mode == "DRAW" and mode != "DRAW":
            self.draw_canvas.drawing = False
            self.draw_canvas.timer.stop()
            self.draw_canvas._release_resources()
            self.draw_canvas._lift_pen()
            self.draw_canvas.hide()
           
            if self._was_tracking_before_draw:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_draw = False
           
            if self.current_user:
                self.logs_page.add_log_entry("DRAW", f"Draw Canvas stopped - switched to {mode}")
            self.toast_manager.show_toast(f"🔄 Switched to {mode} Mode", "Draw mode exited", duration=2000)
       
        if self.current_user and previous_mode != mode:
            self.logs_page.add_log_entry("MODE", f"Mode changed: {previous_mode} → {mode}")

    # ════════════════════════════════════════════════════════════════════
    #                    PAGE SWITCHING
    # ════════════════════════════════════════════════════════════════════

    def switch_page(self, index):
        """Switch between pages"""
        previous_index = self._current_page_index
        print(f"📄 switch_page({index}) - Previous: {previous_index}")
       
        if previous_index == self.PAGE_PREFERENCES and index != self.PAGE_PREFERENCES:
            if hasattr(self, 'calibration_page'):
                self.calibration_page.apply_config_changes()
            if self.current_user:
                self.logs_page.add_log_entry("PREFERENCES", "Preferences changes applied")
       
        if index == self.NOTIFICATION_PAGE_INDEX:
            if hasattr(self, 'notification_page') and hasattr(self.notification_page, 'refresh'):
                self.notification_page.refresh()
       
        if index == self.PAGE_SETTINGS and previous_index != self.PAGE_SETTINGS:
            if hasattr(self.settings_page, 'calibration_card'):
                QTimer.singleShot(100, self.settings_page.calibration_card.refresh)
       
        if previous_index == self.CALIBRATION_PAGE_INDEX and index != self.CALIBRATION_PAGE_INDEX:
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()
            if hasattr(self.settings_page, 'calibration_card'):
                QTimer.singleShot(200, self.settings_page.calibration_card.refresh)
            if self._was_tracking_before_calibration:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_calibration = False
       
        elif index == self.CALIBRATION_PAGE_INDEX and previous_index != self.CALIBRATION_PAGE_INDEX:
            self._was_tracking_before_calibration = self._tracking_active
            if self._tracking_active:
                self._stop_tracking()
            QTimer.singleShot(400, self._start_calibration_camera)
       
        elif previous_index == self.GAMING_PAGE_INDEX and index != self.GAMING_PAGE_INDEX:
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()
            # ✅ Camera state is handled by _activate_desktop_from_gaming
            # Only restore if using legacy exit (not EXIT TO DESKTOP button)
            if self._was_tracking_before_gaming:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_gaming = False
       
        elif index == self.GAMING_PAGE_INDEX and previous_index != self.GAMING_PAGE_INDEX:
            # ✅ FIXED: DON'T stop tracking - camera must stay ON for gestures
            self._was_tracking_before_gaming = self._tracking_active
            print(f"  🎮 switch_page → Gaming (Camera: {'ON' if self._tracking_active else 'OFF'})")
            # Camera keeps running!
            game_controller.start()
       
        elif previous_index == self.TRAINING_PAGE_INDEX and index != self.TRAINING_PAGE_INDEX:
            # ═══════════════════════════════════════════════════════════════
            # 🎯 EXITING TRAINING MODE
            # ═══════════════════════════════════════════════════════════════
            print("  🎯 Exiting Training Mode...")

            # ✅ IMPORTANT: Training mode handles its own camera cleanup
            # Don't interfere with training_tracker here - let training_page.cleanup() handle it
   
            # Just restore main camera if it was running before
            if self._was_tracking_before_training:
                print("  ▶️ Restoring main camera...")
                QTimer.singleShot(500, self._start_tracking)  # ← Increased delay to 500ms
                self._was_tracking_before_training = False

        elif index == self.TRAINING_PAGE_INDEX and previous_index != self.TRAINING_PAGE_INDEX:
            # ✅✅✅ ENTERING TRAINING MODE ✅✅✅
            self._was_tracking_before_training = self._tracking_active
            print(f"  🎯 switch_page → Training (Camera: {'ON' if self._tracking_active else 'OFF'})")
   
            # ✅ IMPORTANT: Don't stop main tracking!
            # Training mode uses independent camera (training_tracker.py)
            # Desktop tracker can keep running in background (gestures disabled in training)
        # ✅✅✅ END ✅✅✅
       
        self._current_page_index = index
        self.stack.setCurrentIndex(index)
        self.sidebar.set_active_page(index)
       
        if index not in [self.GAMING_PAGE_INDEX, self.TRAINING_PAGE_INDEX, self.NOTIFICATION_PAGE_INDEX]:
            self.top_nav.set_active_page(index)
       
        print(f"✅ Now on page index {index}")

    def _start_calibration_camera(self):
        if hasattr(self.calibration_page, 'start_calibration_camera'):
            self.calibration_page.start_calibration_camera()
        if hasattr(self.calibration_page, 'reset_calibration'):
            self.calibration_page.reset_calibration()


    # ════════════════════════════════════════════════════════════════════
    #                    APPLICATION CLEANUP
    # ════════════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        print("👋 Shutting down Aurevix...")
        config.save_config()
       
        # 🎤 Stop AI Engine
        if hasattr(self, 'ai_engine'):
            print("🎤 Stopping AI Engine...")
            self.ai_engine.stop()
       
        # Close presentation viewer
        if self._is_presenting and self.presentation_viewer:
            self.presentation_viewer.close()
            self.presentation_viewer = None
            self._is_presenting = False
            self.gesture_poll_timer.stop()
       
        if self.current_mode == "DRAW":
            self.draw_canvas.drawing = False
            self.draw_canvas.timer.stop()
            self.draw_canvas._release_resources()
            self.draw_canvas._lift_pen()
            self.draw_canvas.hide()
       
        try:
            self.draw_canvas.close()
        except:
            pass

        if self._current_page_index == self.CALIBRATION_PAGE_INDEX:
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()

        if self._current_page_index == self.GAMING_PAGE_INDEX:
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()

        if self._current_page_index == self.TRAINING_PAGE_INDEX:
            if hasattr(self.training_page, 'stop_training_mode'):
                print("🎯 Stopping training mode...")
                self.training_page.stop_training_mode()
        # ✅✅✅ END ✅✅✅

        if self._tracking_active:
            self._stop_tracking()

        if hasattr(self, 'futuristic_dashboard'):
            self.futuristic_dashboard.cleanup()
        if hasattr(self, 'settings_page') and hasattr(self.settings_page, 'cleanup'):
            self.settings_page.cleanup()
        if hasattr(self, 'gaming_page') and hasattr(self.gaming_page, 'cleanup'):
            self.gaming_page.cleanup()
        if hasattr(self, 'training_page') and hasattr(self.training_page, 'cleanup'):
            self.training_page.cleanup()

        self.timer.stop()
        self.frame_timer.stop()
        self.fps_calc_timer.stop()
        self.usage_timer.stop()
        self.gesture_poll_timer.stop()

        print("✅ Shutdown complete")
        event.accept()


# ════════════════════════════════════════════════════════════════════════════════
#                    🚀🚀🚀 MAIN ENTRY POINT WITH SPLASH 🚀🚀🚀
# ════════════════════════════════════════════════════════════════════════════════
#
#   ✅ CHANGES MADE HERE FOR SPLASH INTEGRATION:
#
#   1. Splash screen shows FIRST (fullscreen, 12 seconds)
#   2. Main window is created but HIDDEN during splash
#   3. After splash finishes → Main window SHOWS
#   4. Splash closes automatically
#
# ════════════════════════════════════════════════════════════════════════════════

if __name__ in ("__main__", "main"):
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: CREATE APPLICATION
    # ═══════════════════════════════════════════════════════════════════════════
    app = QApplication(sys.argv)
    app.setApplicationName("Aurevix")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Aurevix")

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: SET APPLICATION ICON (FOR TASKBAR/DOCK)
    # ═══════════════════════════════════════════════════════════════════════════
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app_icon_paths = [
        os.path.join(BASE_DIR, "GCVM", "Asset", "logo.png"),
        os.path.join(BASE_DIR, "GCVM", "Asset", "icon.png"),
        os.path.join(BASE_DIR, "assets", "logo.png"),
        os.path.join(BASE_DIR, "logo.png"),
        os.path.join(BASE_DIR, "icon.png"),
    ]
   
    for icon_path in app_icon_paths:
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                print(f"✅ Application icon set: {os.path.basename(icon_path)}")
                break

    # Set font
    font = app.font()
    font.setFamily("Inter")
    app.setFont(font)

    print("\n" + "🚀"*30)
    print("🚀 AUREVIX - Starting Application")
    print("🚀 🖼️ CUSTOM WINDOW ICON (LOGO)")
    print("🚀 🎤 VOICE COMMAND & AI ENGINE ENABLED")
    print("🚀 📽️ PRESENTATION MODE ENABLED (FIXED)")
    print("🚀 🎮 GAMING MODE: Camera State Preserved (ON→ON, OFF→OFF)")
    print("🚀 ✨ SPLASH SCREEN: 12 Seconds Cyberpunk Hologram")
    print("🚀"*30 + "\n")

    # ═══════════════════════════════════════════════════════════════════════════
    # 🚀🚀🚀 STEP 3: CREATE SPLASH SCREEN 🚀🚀🚀
    # ═══════════════════════════════════════════════════════════════════════════
    print("🎬 Creating Splash Screen...")
    splash = SplashScreen(duration=12000)  # 12 seconds
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🚀🚀🚀 STEP 4: CREATE MAIN WINDOW (HIDDEN) 🚀🚀🚀
    # ═══════════════════════════════════════════════════════════════════════════
    # ✅ IMPORTANT: Create main window NOW but don't show it yet!
    # This allows heavy initialization to happen during splash screen
    print("🔧 Creating Main Window (hidden during splash)...")
    main_window = GesturePanel()
    # ❌ DON'T call main_window.show() here!
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🚀🚀🚀 STEP 5: CONNECT SPLASH FINISHED SIGNAL 🚀🚀🚀
    # ═══════════════════════════════════════════════════════════════════════════
    def on_splash_finished():
        """
        ✅ Called when splash animation completes (after 12 seconds)
        This shows the main window and brings it to front
        """
        print("\n" + "✅"*30)
        print("✅ SPLASH FINISHED - SHOWING MAIN WINDOW")
        print("✅"*30 + "\n")
        
        # Show main window
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        
        # Force focus
        QApplication.processEvents()
        
        print("🏠 Main Window Active!")
    
    # Connect the signal
    splash.splashFinished.connect(on_splash_finished)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🚀🚀🚀 STEP 6: SHOW SPLASH SCREEN 🚀🚀🚀
    # ═══════════════════════════════════════════════════════════════════════════
    print("🎬 Showing Splash Screen (12 seconds)...")
    splash.show()
    splash.raise_()
    splash.activateWindow()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 7: RUN APPLICATION
    # ═══════════════════════════════════════════════════════════════════════════
    print("▶️ Starting Event Loop...\n")
    sys.exit(app.exec())
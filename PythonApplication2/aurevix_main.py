"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              AUREVIX MAIN                                     ║
║                    Gesture Control Application                                ║
║                         With Splash Screen                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import threading
import config
import mode_manager

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont

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

# Splash Screen Import
from splash_screen import SplashScreen

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV not installed.")


class GesturePanel(QMainWindow):
    """
    Main Application Window for Aurevix Gesture Control System
    
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
        self.resize(1400, 820)   # sirf starting size set karega
        self.setMinimumSize(1200, 700)  # optional safety

        self.current_mode = mode_manager.mode
        self.current_user = None
        self._dark_mode = True
        self._tracking_active = False
        
        # Track state for camera management
        self._was_tracking_before_calibration = False
        self._was_tracking_before_gaming = False
        self._was_tracking_before_training = False
        self._current_page_index = 0
        
        # Page indices - Will be set dynamically
        self.GAMING_PAGE_INDEX = -1
        self.TRAINING_PAGE_INDEX = -1
        self.CALIBRATION_PAGE_INDEX = -1
        self.NOTIFICATION_PAGE_INDEX = -1

        # Initialize Notification System
        self.notification_manager = get_notification_manager()
        self.toast_manager = get_toast_manager()

        # ================= BACKGROUND =================
        self._setup_background()

        # ================= DRAW CANVAS =================
        self.draw_canvas = DrawCanvas()

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

        root_layout = QVBoxLayout(main)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.root_stack)

        self.root_stack.setCurrentIndex(0)
        self._apply_futuristic_styles()

        # ================= TIMERS =================
        self._setup_timers()

    def _setup_background(self):
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(self.rect())
        self.bg_label.lower()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.bg_path = os.path.join(BASE_DIR, "GCVM", "Asset", "Aurevix.jpeg")

        if os.path.exists(self.bg_path):
            self.original_pixmap = QPixmap(self.bg_path)  # load once
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
        self.dashboard = DashboardPage(self)
        self.futuristic_dashboard = FuturisticDashboard()
        self.futuristic_dashboard.startTrackingRequested.connect(self._start_tracking)
        self.futuristic_dashboard.stopTrackingRequested.connect(self._stop_tracking)
        self.futuristic_dashboard.modeChanged.connect(self.set_mode)
        self.futuristic_dashboard.mirrorChanged.connect(self._set_mirror)
        self.futuristic_dashboard.screenshotRequested.connect(self._take_screenshot)
        self.futuristic_dashboard.gamingPageRequested.connect(self._open_gaming_mode)
        self.futuristic_dashboard.trainingModeRequested.connect(self._open_training_mode)
        self.stack.addWidget(self.futuristic_dashboard)
        print(f"  ✅ Index {self.stack.count()-1}: Futuristic Dashboard")

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
        # 🔧 CONNECT CALIBRATION SIGNAL
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
        self.stack.addWidget(PlaceholderPage("🤖 AI Trainer", "Train custom gestures"))
        print(f"  ✅ Index {self.stack.count()-1}: AI Trainer Placeholder")

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
        # INDEX 8 - 🎮 GAMING MODE PAGE (Hidden - Dashboard access only)
        # ═══════════════════════════════════════════════════════════════
        self.gaming_page = GamingModePage()
        self.gaming_page.mode_closed.connect(self._on_gaming_mode_closed)
        self.stack.addWidget(self.gaming_page)
        self.GAMING_PAGE_INDEX = self.stack.count() - 1
        print(f"  🎮 Index {self.GAMING_PAGE_INDEX}: GAMING MODE PAGE")

        # ═══════════════════════════════════════════════════════════════
        # INDEX 9 - 🎯 TRAINING MODE PAGE (Hidden - Dashboard access only)
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
    #                    🔔 NOTIFICATION METHODS
    # ════════════════════════════════════════════════════════════════════

    def _show_notification_page(self):
        """Show notification page"""
        print(f"🔔 Opening Notification Page (Index {self.NOTIFICATION_PAGE_INDEX})...")
        self.switch_page(self.NOTIFICATION_PAGE_INDEX)
        if hasattr(self.notification_page, 'refresh'):
            self.notification_page.refresh()
    
    def _on_notification_clicked(self, notification):
        """Handle notification click - navigate to relevant page"""
        print(f"🔔 Notification clicked: {notification.title}")
        
        # Handle different notification types
        if notification.type.value == "calibration":
            self.switch_page(self.CALIBRATION_PAGE_INDEX)
        elif notification.type.value == "gesture":
            self.switch_page(self.PAGE_GESTURES)
        elif notification.type.value == "system":
            self.switch_page(self.PAGE_SETTINGS)
        else:
            # Default: go to dashboard
            self.switch_page(0)

    # ════════════════════════════════════════════════════════════════════
    #                    🔧 CALIBRATION METHODS
    # ════════════════════════════════════════════════════════════════════

    def _open_calibration_from_settings(self):
        """
        🔧 Open calibration page from settings panel
        Triggered when user clicks "Open Calibration" button in settings
        """
        print("\n" + "🔧"*20)
        print("🔧 CALIBRATION REQUESTED FROM SETTINGS")
        print(f"   Current page: {self._current_page_index}")
        print(f"   Target page: {self.CALIBRATION_PAGE_INDEX}")
        print("🔧"*20 + "\n")
        
        # Navigate to calibration page
        self.switch_page(self.CALIBRATION_PAGE_INDEX)
        
        # Log the action
        if self.current_user:
            self.logs_page.add_log_entry("NAVIGATION", "Opened Calibration from Settings")

    def _on_calibration_complete(self):
        """Handle calibration completion"""
        print("✅ Calibration complete - margins saved to config")
        
        # Update settings panel to show new calibration status
        if hasattr(self.settings_page, 'calibration_card'):
            QTimer.singleShot(100, self.settings_page.calibration_card.refresh)
        
        if self.current_user:
            self.logs_page.add_log_entry("CALIBRATION", "Calibration completed successfully")
            
        # Show toast notification
        self.toast_manager.show_toast(
            "✅ Calibration Complete",
            "Hand tracking margins have been calibrated successfully!",
            duration=3000
        )
    
    def _open_preferences_from_calibration(self):
        """Navigate to preferences page from calibration page"""
        print("📋 Calibration → Opening Preferences Page (index 5)...")
        self.switch_page(self.PAGE_PREFERENCES)

    # ════════════════════════════════════════════════════════════════════
    #                    🎮 GAMING MODE METHODS
    # ════════════════════════════════════════════════════════════════════
    
    def _open_gaming_mode(self):
        """Open Gaming Mode page from dashboard"""
        print("\n" + "🎮"*20)
        print(f"🎮 OPENING GAMING MODE PAGE")
        print(f"   Target Index: {self.GAMING_PAGE_INDEX}")
        print(f"   Current Index: {self._current_page_index}")
        print("🎮"*20 + "\n")
        
        # Save tracking state
        self._was_tracking_before_gaming = self._tracking_active
        
        # Stop main tracking before entering gaming mode
        if self._tracking_active:
            self._stop_tracking()
        
        # Switch to gaming page
        self.switch_page(self.GAMING_PAGE_INDEX)
        
        # Start gaming controller
        game_controller.start()
        
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("GAMING", "Gaming Mode opened")

    def _on_gaming_mode_closed(self):
        """Handle gaming mode exit"""
        print("📤 Exiting Gaming Mode...")
        
        # Stop gaming controller
        game_controller.stop()
        
        # Return to dashboard
        self.switch_page(0)
        
        # Restore tracking if it was active before
        if self._was_tracking_before_gaming:
            QTimer.singleShot(300, self._start_tracking)
            self._was_tracking_before_gaming = False
        
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("GAMING", "Gaming Mode closed")

    # ════════════════════════════════════════════════════════════════════
    #                    🎯 TRAINING MODE METHODS
    # ════════════════════════════════════════════════════════════════════
    
    def _open_training_mode(self):
        """Open Training Mode page from dashboard"""
        print("\n" + "🎯"*20)
        print(f"🎯 OPENING TRAINING MODE PAGE")
        print(f"   Target Index: {self.TRAINING_PAGE_INDEX}")
        print(f"   Current Index: {self._current_page_index}")
        print("🎯"*20 + "\n")
        
        # Save tracking state
        self._was_tracking_before_training = self._tracking_active
        
        # Switch to training page
        self.switch_page(self.TRAINING_PAGE_INDEX)
        
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("TRAINING", "Training Mode opened")

    def _on_training_mode_closed(self):
        """Handle training mode exit"""
        print("📤 Exiting Training Mode...")
        
        # Return to dashboard
        self.switch_page(0)
        
        # Restore tracking if needed
        if self._was_tracking_before_training:
            QTimer.singleShot(300, self._start_tracking)
            self._was_tracking_before_training = False
        
        # Log activity
        if self.current_user:
            self.logs_page.add_log_entry("TRAINING", "Training Mode closed")

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

        if hasattr(self, 'dashboard'):
            self.dashboard.start_camera()

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

        if hasattr(self, 'dashboard'):
            self.dashboard.stop_camera()

        print("⏹ Hand tracking stopped")

    def _read_shared_frame(self):
        """Read the processed frame and send to the active page."""
        frame = mode_manager.shared_frame
        
        self._frame_count += 1
        
        current_idx = self.stack.currentIndex()
        
        # Route frame to appropriate page
        if current_idx == 0:  # Dashboard
            if frame is not None:
                self.futuristic_dashboard.update_frame(frame)
        elif current_idx == self.GAMING_PAGE_INDEX:
            if frame is not None and hasattr(self, 'gaming_page'):
                self.gaming_page.update_camera_feed()
        elif current_idx == self.TRAINING_PAGE_INDEX:
            if frame is not None and hasattr(self, 'training_page'):
                self.training_page.update_camera_feed()
        
        # Send frame to settings preview if enabled
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
            print("❌ OpenCV not available for screenshots")
            return
            
        frame = self.futuristic_dashboard.get_last_frame()
        if frame is None:
            print("❌ No frame available for screenshot")
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
        """Apply futuristic styles to application"""
        self.load_styles()

    def load_styles(self):
        """Load and apply stylesheet"""
        self.setStyleSheet(get_styles())

    # ════════════════════════════════════════════════════════════════════
    #                    SETTINGS & PREFERENCES CONNECTIONS
    # ════════════════════════════════════════════════════════════════════

    def _on_shortcuts_toggled(self, enabled):
        """Handle shortcuts toggle"""
        if self.current_user:
            self.logs_page.add_log_entry("SETTING", f"Shortcuts {'enabled' if enabled else 'disabled'}")

    def _on_gesture_added(self, gesture):
        """Handle new gesture added"""
        if self.current_user:
            database.update_user_stats(self.current_user["id"], gestures=1)
            self.logs_page.add_log_entry("GESTURE", f"Gesture saved: {gesture['name']} ({gesture['points_count']} pts)")
        hand_tracker.reload_custom_gestures()
    
    def _on_gesture_changed(self, *args):
        """Handle gesture list changed"""
        hand_tracker.reload_custom_gestures()
        if self.current_user:
            self.logs_page.add_log_entry("GESTURE", "Gesture list updated")

    def _connect_settings(self):
        """Connect settings panel signals"""
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
        """Sync mirror setting with dashboard"""
        self.futuristic_dashboard.mirror_btn.setChecked(checked)

    def _connect_preferences(self):
        """Connect preferences page signals"""
        prefs = self.preferences_page
        prefs.themeChanged.connect(lambda x: self.load_styles())
        prefs.penColorChanged.connect(lambda x: None)
        prefs.thicknessChanged.connect(lambda x: None)
        prefs.autoclearChanged.connect(lambda x: None)
        prefs.cameraChanged.connect(lambda x: None)
        prefs.startupChanged.connect(lambda x: None)
        prefs.trayChanged.connect(lambda x: None)
        prefs.popupsChanged.connect(lambda x: None)
        prefs.skeletonChanged.connect(lambda x: None)
        prefs.fpsChanged.connect(lambda x: None)
        prefs.leftHandChanged.connect(lambda x: None)
        prefs.clickSensChanged.connect(lambda x: None)

    def _sync_settings(self):
        """Sync settings UI with config"""
        if hasattr(self, 'settings_page') and hasattr(self.settings_page, '_sync_ui_to_config'):
            self.settings_page._sync_ui_to_config()

    def _sync_preferences(self):
        """Sync preferences UI with config"""
        if hasattr(self, 'preferences_page') and hasattr(self.preferences_page, '_sync_ui_to_config'):
            self.preferences_page._sync_ui_to_config()

    # ════════════════════════════════════════════════════════════════════
    #                    USER AUTHENTICATION
    # ════════════════════════════════════════════════════════════════════

    def _on_login_success(self, user_data):
        """Handle successful user login"""
        self.current_user = user_data
        self.session_start = time.time()
        
        # Update UI with user info
        self.sidebar.set_user(user_data)
        self.top_nav.set_user(user_data)
        self.logs_page.set_user(user_data["id"])
        
        # Load user config
        config.load_config()
        self._sync_settings()
        self._sync_preferences()
        
        # Switch to main app
        self.root_stack.setCurrentIndex(1)

        # Start hand tracker thread
        if not hasattr(self, 'tracker_thread') or not self.tracker_thread.is_alive():
            hand_tracker.set_gui(self)
            self.tracker_thread = threading.Thread(target=hand_tracker.run_tracker, daemon=True)
            self.tracker_thread.start()

        # Log activity
        database.log_activity(user_data["id"], "APP_START", "Application started")
        print(f"✅ Logged in as: {user_data['display_name']}")

    def _on_logout(self):
        """Handle user logout"""
        print("🚪 Logging out...")
        
        # Stop any active special pages
        if self._current_page_index == self.CALIBRATION_PAGE_INDEX:
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()
        
        if self._current_page_index == self.GAMING_PAGE_INDEX:
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()
        
        if self._current_page_index == self.TRAINING_PAGE_INDEX:
            if hasattr(self.training_page, 'stop_training_mode'):
                self.training_page.stop_training_mode()
        
        # Stop tracking
        if self._tracking_active:
            self._stop_tracking()

        # Save config and clear session
        config.save_config()
        database.clear_remember_me()
        
        # Reset user state
        self.current_user = None
        self.session_start = None
        
        # Update UI
        self.sidebar.set_guest()
        self.top_nav.set_guest()
        self.logs_page.set_user(None)
        
        # Show login screen
        self.auth_manager.show_login()
        self.root_stack.setCurrentIndex(0)
        
        print("🚪 User logged out.")

    def _edit_profile(self):
        """Open profile edit dialog"""
        if not self.current_user:
            return
        dialog = ProfileEditDialog(self.current_user, self)
        dialog.profileUpdated.connect(self._on_profile_updated)
        dialog.exec()

    def _on_profile_updated(self, updated_data):
        """Handle profile update"""
        self.current_user = updated_data
        self.sidebar.set_user(updated_data)
        self.top_nav.set_user(updated_data)
        
        if self.current_user:
            self.logs_page.add_log_entry("PROFILE", "Profile updated")

    def _track_usage(self):
        """Track usage time (called every minute)"""
        if self.current_user and self.session_start:
            database.update_user_stats(self.current_user["id"], minutes=1.0)

    # ════════════════════════════════════════════════════════════════════
    #                    DASHBOARD STATUS
    # ════════════════════════════════════════════════════════════════════

    def update_dashboard_status(self):
        """Update dashboard status (called by timer)"""
        if self.root_stack.currentIndex() != 1:
            return
        
        # Skip updates when on special pages
        special_pages = [
            self.CALIBRATION_PAGE_INDEX, 
            self.GAMING_PAGE_INDEX, 
            self.TRAINING_PAGE_INDEX
        ]
        
        if self._current_page_index not in special_pages:
            self.futuristic_dashboard.update_mode_cards(mode_manager.mode)
            self._sync_settings()

    def set_mode(self, mode):
        """Set current gesture mode"""
        self.current_mode = mode
        mode_manager.set_mode(mode)
        
        # Update UI
        self.gestures_page.update_mode_buttons(mode)
        self.futuristic_dashboard.update_mode_cards(mode)

        # Handle draw mode
        if mode == "DRAW":
            self.draw_canvas.start_draw()
        else:
            self.draw_canvas.stop_draw()
        
        if self.current_user:
            self.logs_page.add_log_entry("MODE", f"Mode changed to {mode}")

    # ════════════════════════════════════════════════════════════════════
    #                    PAGE SWITCHING - MAIN NAVIGATION
    # ════════════════════════════════════════════════════════════════════

    def switch_page(self, index):
        """
        Switch between pages with correct index handling
        
        Handles special cases for:
        - Calibration page (camera management)
        - Gaming mode (game controller)
        - Training mode
        - Preferences page (notify calibration on return)
        - Notification page (refresh on enter)
        """
        previous_index = self._current_page_index
        
        print(f"📄 switch_page({index}) - Previous: {previous_index}")
        
        # ══════════════════════════════════════════════════════════════
        # LEAVING PREFERENCES PAGE → Notify calibration page
        # ══════════════════════════════════════════════════════════════
        if previous_index == self.PAGE_PREFERENCES and index != self.PAGE_PREFERENCES:
            print("📤 Leaving Preferences page - syncing changes...")
            if hasattr(self, 'calibration_page'):
                self.calibration_page.apply_config_changes()
            if self.current_user:
                self.logs_page.add_log_entry("PREFERENCES", "Preferences changes applied")
        
        # ══════════════════════════════════════════════════════════════
        # ENTERING NOTIFICATION PAGE
        # ══════════════════════════════════════════════════════════════
        if index == self.NOTIFICATION_PAGE_INDEX:
            print("📥 Entering Notification Page...")
            if hasattr(self, 'notification_page') and hasattr(self.notification_page, 'refresh'):
                self.notification_page.refresh()
        
        # ══════════════════════════════════════════════════════════════
        # LEAVING SETTINGS PAGE → Update calibration card
        # ══════════════════════════════════════════════════════════════
        if previous_index == self.PAGE_SETTINGS and index != self.PAGE_SETTINGS:
            print("📤 Leaving Settings page...")
            # Settings panel will auto-cleanup
        
        # ══════════════════════════════════════════════════════════════
        # ENTERING SETTINGS PAGE → Refresh calibration status
        # ══════════════════════════════════════════════════════════════
        if index == self.PAGE_SETTINGS and previous_index != self.PAGE_SETTINGS:
            print("📥 Entering Settings page...")
            if hasattr(self.settings_page, 'calibration_card'):
                QTimer.singleShot(100, self.settings_page.calibration_card.refresh)
        
        # ══════════════════════════════════════════════════════════════
        # LEAVING CALIBRATION PAGE
        # ══════════════════════════════════════════════════════════════
        if previous_index == self.CALIBRATION_PAGE_INDEX and index != self.CALIBRATION_PAGE_INDEX:
            print("📤 Leaving Calibration page...")
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()
            
            # Update settings panel calibration card
            if hasattr(self.settings_page, 'calibration_card'):
                QTimer.singleShot(200, self.settings_page.calibration_card.refresh)
            
            if self._was_tracking_before_calibration:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_calibration = False
        
        # ══════════════════════════════════════════════════════════════
        # ENTERING CALIBRATION PAGE
        # ══════════════════════════════════════════════════════════════
        elif index == self.CALIBRATION_PAGE_INDEX and previous_index != self.CALIBRATION_PAGE_INDEX:
            print("📥 Entering Calibration page...")
            self._was_tracking_before_calibration = self._tracking_active
            if self._tracking_active:
                self._stop_tracking()
            QTimer.singleShot(400, self._start_calibration_camera)
        
        # ══════════════════════════════════════════════════════════════
        # LEAVING GAMING MODE
        # ══════════════════════════════════════════════════════════════
        elif previous_index == self.GAMING_PAGE_INDEX and index != self.GAMING_PAGE_INDEX:
            print("📤 Leaving Gaming Mode page...")
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()
            if self._was_tracking_before_gaming:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_gaming = False
        
        # ══════════════════════════════════════════════════════════════
        # ENTERING GAMING MODE
        # ══════════════════════════════════════════════════════════════
        elif index == self.GAMING_PAGE_INDEX and previous_index != self.GAMING_PAGE_INDEX:
            print("📥 Entering Gaming Mode page...")
            self._was_tracking_before_gaming = self._tracking_active
            if self._tracking_active:
                self._stop_tracking()
            game_controller.start()
        
        # ══════════════════════════════════════════════════════════════
        # LEAVING TRAINING MODE
        # ══════════════════════════════════════════════════════════════
        elif previous_index == self.TRAINING_PAGE_INDEX and index != self.TRAINING_PAGE_INDEX:
            print("📤 Leaving Training Mode page...")
            if hasattr(self.training_page, 'stop_training_mode'):
                self.training_page.stop_training_mode()
            if self._was_tracking_before_training:
                QTimer.singleShot(300, self._start_tracking)
                self._was_tracking_before_training = False
        
        # ══════════════════════════════════════════════════════════════
        # ENTERING TRAINING MODE
        # ══════════════════════════════════════════════════════════════
        elif index == self.TRAINING_PAGE_INDEX and previous_index != self.TRAINING_PAGE_INDEX:
            print("📥 Entering Training Mode page...")
            self._was_tracking_before_training = self._tracking_active
        
        # ══════════════════════════════════════════════════════════════
        # UPDATE UI STATE
        # ══════════════════════════════════════════════════════════════
        self._current_page_index = index
        self.stack.setCurrentIndex(index)
        self.sidebar.set_active_page(index)
        
        # Don't update top nav for hidden pages
        if index not in [self.GAMING_PAGE_INDEX, self.TRAINING_PAGE_INDEX, self.NOTIFICATION_PAGE_INDEX]:
            self.top_nav.set_active_page(index)
        
        print(f"✅ Now on page index {index}")

    def _start_calibration_camera(self):
        """Start calibration camera"""
        if hasattr(self.calibration_page, 'start_calibration_camera'):
            self.calibration_page.start_calibration_camera()
        if hasattr(self.calibration_page, 'reset_calibration'):
            self.calibration_page.reset_calibration()

    # ════════════════════════════════════════════════════════════════════
    #                    APPLICATION CLEANUP
    # ════════════════════════════════════════════════════════════════════

    def closeEvent(self, event):
        """Handle application close"""
        print("👋 Shutting down Aurevix...")
        
        # Save configuration
        config.save_config()

        # Stop special pages
        if self._current_page_index == self.CALIBRATION_PAGE_INDEX:
            if hasattr(self.calibration_page, 'stop_calibration_camera'):
                self.calibration_page.stop_calibration_camera()

        if self._current_page_index == self.GAMING_PAGE_INDEX:
            if hasattr(self.gaming_page, 'stop_gaming_mode'):
                self.gaming_page.stop_gaming_mode()
            game_controller.stop()

        if self._current_page_index == self.TRAINING_PAGE_INDEX:
            if hasattr(self.training_page, 'stop_training_mode'):
                self.training_page.stop_training_mode()

        # Stop tracking
        if self._tracking_active:
            self._stop_tracking()

        # Stop draw canvas
        self.draw_canvas.stop_draw()
        self.draw_canvas.close()

        # Cleanup pages
        if hasattr(self, 'futuristic_dashboard'):
            self.futuristic_dashboard.cleanup()
        if hasattr(self, 'settings_page') and hasattr(self.settings_page, 'cleanup'):
            self.settings_page.cleanup()
        if hasattr(self, 'gaming_page') and hasattr(self.gaming_page, 'cleanup'):
            self.gaming_page.cleanup()
        if hasattr(self, 'training_page') and hasattr(self.training_page, 'cleanup'):
            self.training_page.cleanup()

        # Stop all timers
        self.timer.stop()
        self.frame_timer.stop()
        self.fps_calc_timer.stop()
        self.usage_timer.stop()

        print("✅ Shutdown complete")
        event.accept()


# ════════════════════════════════════════════════════════════════════════
#                    APPLICATION ENTRY POINT WITH SPLASH SCREEN
# ════════════════════════════════════════════════════════════════════════

def run_application():
    """
    🚀 Application Entry Point with Splash Screen
    
    Flow:
    1. Show splash screen with animations
    2. Initialize main window in background
    3. After splash duration, hide splash and show main window
    """
    app = QApplication(sys.argv)
    
    # ═══════════════════════════════════════════════════════════════════
    # SET APPLICATION PROPERTIES
    # ═══════════════════════════════════════════════════════════════════
    app.setApplicationName("Aurevix")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Aurevix")
    
    # Set application font
    font = app.font()
    font.setFamily("Inter")
    app.setFont(font)
    
    # ═══════════════════════════════════════════════════════════════════
    # SHOW SPLASH SCREEN
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "🚀"*30)
    print("🚀 AUREVIX - Starting Application")
    print("🚀"*30 + "\n")
    
    # Create splash screen (4 seconds duration)
    splash = SplashScreen(duration=4000)
    splash.show()
    
    # Process events to show splash immediately
    app.processEvents()
    
    # ═══════════════════════════════════════════════════════════════════
    # INITIALIZE MAIN WINDOW (while splash is showing)
    # ═══════════════════════════════════════════════════════════════════
    print("📦 Initializing main application...")
    main_window = GesturePanel()
    
    def on_splash_finished():
        """Called when splash animation completes"""
        print("✨ Splash complete - showing main window")
        splash.close()
        splash.deleteLater()
        
        # Center main window on screen
        screen = app.primaryScreen().geometry()
        x = (screen.width() - main_window.width()) // 2
        y = (screen.height() - main_window.height()) // 2
        main_window.move(x, y)
        
        # Show main window
        main_window.show()
    
    # Connect splash finish signal
    splash.splashFinished.connect(on_splash_finished)
    
    # ═══════════════════════════════════════════════════════════════════
    # RUN APPLICATION
    # ═══════════════════════════════════════════════════════════════════
    sys.exit(app.exec())


# ════════════════════════════════════════════════════════════════════════
#                    ALTERNATIVE: QUICK START (NO SPLASH)
# ════════════════════════════════════════════════════════════════════════

def run_without_splash():
    """
    Quick start without splash screen (for development/testing)
    """
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setFamily("Inter")
    app.setFont(font)
    
    win = GesturePanel()
    win.show()
    
    sys.exit(app.exec())


# ════════════════════════════════════════════════════════════════════════
#                    MAIN ENTRY POINT
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # ═══════════════════════════════════════════════════════════════════
    # CHOOSE STARTUP MODE
    # ═══════════════════════════════════════════════════════════════════
    
    # Check for command line arguments
    SKIP_SPLASH = "--no-splash" in sys.argv or "-q" in sys.argv
    
    if SKIP_SPLASH:
        print("⚡ Quick start mode (no splash)")
        run_without_splash()
    else:
        # Normal startup with splash screen
        run_application()

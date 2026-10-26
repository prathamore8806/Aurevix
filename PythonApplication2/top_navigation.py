# top_navigation.py - With Notification Badge

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QFont

from profile_widget import ProfileWidget
from notification_manager import get_notification_manager


class NotificationBadge(QLabel):
    """Notification count badge"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self.setFixedSize(18, 18)
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        self._update_style()
    
    def set_count(self, count: int):
        self._count = count
        if count > 0:
            self.setText(str(min(count, 99)) if count < 100 else "99+")
            self.show()
        else:
            self.hide()
        self._update_style()
    
    def _update_style(self):
        self.setStyleSheet("""
            QLabel {
                background: #ff4757;
                color: white;
                font-size: 9px;
                font-weight: bold;
                border-radius: 9px;
            }
        """)


class TopNavigation(QFrame):
    pageRequested = Signal(int)
    themeToggled = Signal()
    logoutRequested = Signal()
    profileEditRequested = Signal()
    notificationPageRequested = Signal()  # NEW SIGNAL
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setObjectName("topNav")
        self._current_page = 0
        self.setStyleSheet("""
            #topNav {
                background: rgba(8, 8, 25, 0.85);
                border-bottom: 1px solid rgba(0, 212, 255, 0.15);
            }
        """)
        self._build_ui()
        self._connect_notifications()
    
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        # ═══════════════════════════════════════════════════════════
        # LOGO
        # ═══════════════════════════════════════════════════════════
        logo = QLabel("⚡ Aurevix")
        logo.setStyleSheet("""
            font-size: 18px; 
            font-weight: 800; 
            color: #00d4ff; 
            background: transparent; 
            letter-spacing: 2px;
        """)
        layout.addWidget(logo)
        layout.addSpacing(30)

        # ═══════════════════════════════════════════════════════════
        # NAVIGATION BUTTONS
        # ═══════════════════════════════════════════════════════════
        self.nav_buttons = {}
        
        nav_items = [
            ("Dashboard", 0),
            ("Gestures", 1),
            ("Shortcuts", 2),
            ("Settings", 4),
            ("Preferences", 5),
        ]
        
        for label, page_idx in nav_items:
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("page_index", page_idx)
            btn.setCheckable(True)
            btn.setStyleSheet(self._get_nav_button_style())
            btn.clicked.connect(lambda checked, idx=page_idx: self._on_nav_clicked(idx))
            self.nav_buttons[page_idx] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # ═══════════════════════════════════════════════════════════
        # UTILITY BUTTONS
        # ═══════════════════════════════════════════════════════════
        
        # Theme Toggle
        self.theme_toggle = QPushButton("🌙")
        self.theme_toggle.setFixedSize(36, 36)
        self.theme_toggle.setCursor(Qt.PointingHandCursor)
        self.theme_toggle.setToolTip("Toggle Theme")
        self.theme_toggle.setStyleSheet(self._get_icon_button_style())
        self.theme_toggle.clicked.connect(self.themeToggled.emit)
        layout.addWidget(self.theme_toggle)

        # Notifications Button with Badge
        self.notif_container = QWidget()
        self.notif_container.setFixedSize(44, 44)
        
        self.notif_btn = QPushButton("🔔", self.notif_container)
        self.notif_btn.setFixedSize(36, 36)
        self.notif_btn.move(4, 4)
        self.notif_btn.setCursor(Qt.PointingHandCursor)
        self.notif_btn.setToolTip("Notifications")
        self.notif_btn.setStyleSheet(self._get_icon_button_style())
        self.notif_btn.clicked.connect(self._on_notification_clicked)
        
        self.notif_badge = NotificationBadge(self.notif_container)
        self.notif_badge.move(26, 0)
        
        layout.addWidget(self.notif_container)

        layout.addSpacing(8)

        # ═══════════════════════════════════════════════════════════
        # PROFILE WIDGET
        # ═══════════════════════════════════════════════════════════
        self.nav_profile = ProfileWidget()
        self.nav_profile.logoutClicked.connect(self.logoutRequested.emit)
        self.nav_profile.profileClicked.connect(self.profileEditRequested.emit)
        self.nav_profile.setMinimumWidth(190)
        self.nav_profile.setMaximumWidth(250)
        layout.addWidget(self.nav_profile)
    
    def _connect_notifications(self):
        """Connect to notification manager"""
        self.notification_manager = get_notification_manager()
        self.notification_manager.unreadCountChanged.connect(self._update_badge)
        
        # Initial badge update
        QTimer.singleShot(100, lambda: self._update_badge(self.notification_manager.get_unread_count()))
    
    def _update_badge(self, count: int):
        """Update notification badge count"""
        self.notif_badge.set_count(count)
    
    def _on_notification_clicked(self):
        """Handle notification button click"""
        self.notificationPageRequested.emit()

    def _get_nav_button_style(self):
        return """
            QPushButton {
                background: transparent;
                color: #7788aa;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                color: #00d4ff;
                background: rgba(0, 212, 255, 0.08);
            }
            QPushButton:checked {
                color: #00d4ff;
                background: rgba(0, 212, 255, 0.15);
                border: 1px solid rgba(0, 212, 255, 0.3);
            }
        """

    def _get_icon_button_style(self):
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 18px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: #00d4ff;
            }
        """

    def _on_nav_clicked(self, index):
        """Handle navigation button click"""
        self.set_active_page(index)
        self.pageRequested.emit(index)

    def set_active_page(self, index):
        """Update active state of navigation buttons"""
        self._current_page = index
        for page_idx, btn in self.nav_buttons.items():
            btn.setChecked(page_idx == index)

    def set_theme_icon(self, dark_mode):
        """Update theme toggle icon"""
        self.theme_toggle.setText("🌙" if dark_mode else "☀️")

    def set_user(self, user_data):
        """Set logged-in user info"""
        self.nav_profile.set_user(user_data)

    def set_guest(self):
        """Set guest mode"""
        self.nav_profile.set_guest()
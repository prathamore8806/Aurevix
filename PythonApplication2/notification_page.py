
# notification_page.py - Notification History Page

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QStackedWidget, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush

from datetime import datetime
from notification_manager import (
    NotificationManager, get_notification_manager, 
    Notification, NotificationType
)


class NotificationCard(QFrame):
    """Individual notification card"""
    
    clicked = Signal(object)  # Notification
    deleteClicked = Signal(str)  # notification_id
    
    def __init__(self, notification: Notification, parent=None):
        super().__init__(parent)
        self.notification = notification
        self.setObjectName("notificationCard")
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()
        self._apply_style()
        
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)
        
        # Icon
        icon_label = QLabel(self.notification.icon)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            background: {self._get_type_color(0.15)};
            border-radius: 22px;
            font-size: 20px;
        """)
        layout.addWidget(icon_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        # Title row
        title_row = QHBoxLayout()
        
        title = QLabel(self.notification.title)
        title.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {'white' if not self.notification.read else 'rgba(255,255,255,0.7)'};
            background: transparent;
        """)
        title_row.addWidget(title)
        
        # Unread indicator
        if not self.notification.read:
            unread_dot = QLabel("●")
            unread_dot.setStyleSheet(f"color: {self._get_type_color(1)}; font-size: 10px; background: transparent;")
            title_row.addWidget(unread_dot)
        
        title_row.addStretch()
        
        # Time
        time_label = QLabel(self._format_time())
        time_label.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; background: transparent;")
        title_row.addWidget(time_label)
        
        content.addLayout(title_row)
        
        # Message
        message = QLabel(self.notification.message)
        message.setWordWrap(True)
        message.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px; background: transparent;")
        content.addWidget(message)
        
        # Type badge
        type_badge = QLabel(self.notification.type.value.upper())
        type_badge.setStyleSheet(f"""
            color: {self._get_type_color(1)};
            background: {self._get_type_color(0.15)};
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 600;
        """)
        type_badge.setFixedWidth(type_badge.sizeHint().width() + 16)
        content.addWidget(type_badge)
        
        layout.addLayout(content, stretch=1)
        
        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 85, 85, 0.1);
                border: none;
                border-radius: 14px;
                color: rgba(255, 85, 85, 0.6);
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.3);
                color: #ff5555;
            }
        """)
        delete_btn.clicked.connect(lambda: self.deleteClicked.emit(self.notification.id))
        layout.addWidget(delete_btn, alignment=Qt.AlignTop)
    
    def _get_type_color(self, alpha: float = 1.0) -> str:
        colors = {
            NotificationType.SUCCESS: f"rgba(0, 255, 136, {alpha})",
            NotificationType.ERROR: f"rgba(255, 85, 85, {alpha})",
            NotificationType.WARNING: f"rgba(255, 170, 0, {alpha})",
            NotificationType.INFO: f"rgba(0, 212, 255, {alpha})",
            NotificationType.CALIBRATION: f"rgba(138, 43, 226, {alpha})",
            NotificationType.GESTURE: f"rgba(255, 105, 180, {alpha})",
            NotificationType.SYSTEM: f"rgba(100, 149, 237, {alpha})",
        }
        return colors.get(self.notification.type, f"rgba(0, 212, 255, {alpha})")
    
    def _format_time(self) -> str:
        try:
            dt = datetime.fromisoformat(self.notification.timestamp)
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                if diff.seconds < 60:
                    return "Just now"
                elif diff.seconds < 3600:
                    return f"{diff.seconds // 60}m ago"
                else:
                    return f"{diff.seconds // 3600}h ago"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days}d ago"
            else:
                return dt.strftime("%b %d")
        except:
            return ""
    
    def _apply_style(self):
        read_opacity = "0.06" if self.notification.read else "0.1"
        self.setStyleSheet(f"""
            #notificationCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, {read_opacity}),
                    stop:1 rgba(255, 255, 255, 0.03));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
            }}
            #notificationCard:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 212, 255, 0.1),
                    stop:1 rgba(0, 212, 255, 0.05));
                border-color: rgba(0, 212, 255, 0.3);
            }}
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.notification)
        super().mousePressEvent(event)


class EmptyState(QFrame):
    """Empty state when no notifications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        self._build_ui()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        icon = QLabel("🔔")
        icon.setStyleSheet("font-size: 64px; background: transparent;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("No Notifications")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: white; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        message = QLabel("You're all caught up! New notifications will appear here.")
        message.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.5); background: transparent;")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        self.setStyleSheet("""
            #emptyState {
                background: transparent;
            }
        """)


class FilterButton(QPushButton):
    """Filter button for notification types"""
    
    def __init__(self, text: str, filter_type: str = "all", parent=None):
        super().__init__(text, parent)
        self.filter_type = filter_type
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.1);
                border-color: rgba(0, 212, 255, 0.3);
                color: #00d4ff;
            }
            QPushButton:checked {
                background: rgba(0, 212, 255, 0.2);
                border-color: rgba(0, 212, 255, 0.5);
                color: #00d4ff;
            }
        """)


class NotificationPage(QWidget):
    """Main Notification Page - Shows all notifications"""
    
    notificationClicked = Signal(object)  # Notification
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_manager = get_notification_manager()
        self.current_filter = "all"
        self._build_ui()
        self._connect_signals()
        self._load_notifications()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header = QHBoxLayout()
        
        title_block = QVBoxLayout()
        title = QLabel("🔔 Notifications")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        title_block.addWidget(title)
        
        self.subtitle = QLabel("0 notifications")
        self.subtitle.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 13px;")
        title_block.addWidget(self.subtitle)
        
        header.addLayout(title_block)
        header.addStretch()
        
        # Action buttons
        self.mark_all_btn = QPushButton("✓ Mark All Read")
        self.mark_all_btn.setCursor(Qt.PointingHandCursor)
        self.mark_all_btn.clicked.connect(self._mark_all_read)
        self.mark_all_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 212, 255, 0.15);
                color: #00d4ff;
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.25);
            }
        """)
        header.addWidget(self.mark_all_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_all)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 85, 85, 0.15);
                color: #ff5555;
                border: 1px solid rgba(255, 85, 85, 0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 85, 85, 0.25);
            }
        """)
        header.addWidget(self.clear_btn)
        
        layout.addLayout(header)
        
        # ═══════════════════════════════════════════════════════════
        # FILTERS
        # ═══════════════════════════════════════════════════════════
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        self.filter_buttons = {}
        filters = [
            ("All", "all"),
            ("🎯 Calibration", "calibration"),
            ("👋 Gestures", "gesture"),
            ("✅ Success", "success"),
            ("❌ Errors", "error"),
            ("⚠️ Warnings", "warning"),
            ("⚙️ System", "system"),
        ]
        
        for label, filter_type in filters:
            btn = FilterButton(label, filter_type)
            btn.setChecked(filter_type == "all")
            btn.clicked.connect(lambda checked, ft=filter_type: self._set_filter(ft))
            self.filter_buttons[filter_type] = btn
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # ═══════════════════════════════════════════════════════════
        # NOTIFICATION LIST
        # ═══════════════════════════════════════════════════════════
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.03);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 212, 255, 0.4);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 212, 255, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)
        
        # Empty state
        self.empty_state = EmptyState()
        self.empty_state.hide()
        layout.addWidget(self.empty_state)
    
    def _connect_signals(self):
        self.notification_manager.notificationAdded.connect(self._on_notification_added)
        self.notification_manager.notificationsCleared.connect(self._load_notifications)
    
    def _load_notifications(self):
        """Load and display notifications"""
        # Clear existing
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        notifications = self.notification_manager.get_all()
        
        # Filter
        if self.current_filter != "all":
            try:
                filter_type = NotificationType(self.current_filter)
                notifications = [n for n in notifications if n.type == filter_type]
            except:
                pass
        
        # Update subtitle
        unread = self.notification_manager.get_unread_count()
        total = len(self.notification_manager.get_all())
        self.subtitle.setText(f"{total} notifications • {unread} unread")
        
        if not notifications:
            self.scroll_area.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.scroll_area.show()
            
            for notif in notifications:
                card = NotificationCard(notif)
                card.clicked.connect(self._on_notification_clicked)
                card.deleteClicked.connect(self._delete_notification)
                self.list_layout.addWidget(card)
            
            # Add spacer at bottom
            self.list_layout.addStretch()
    
    def _set_filter(self, filter_type: str):
        self.current_filter = filter_type
        for ft, btn in self.filter_buttons.items():
            btn.setChecked(ft == filter_type)
        self._load_notifications()
    
    def _on_notification_added(self, notification: Notification):
        """Handle new notification"""
        self._load_notifications()
    
    def _on_notification_clicked(self, notification: Notification):
        """Handle notification click"""
        self.notification_manager.mark_read(notification.id)
        self._load_notifications()
        self.notificationClicked.emit(notification)
    
    def _delete_notification(self, notification_id: str):
        """Delete a notification"""
        self.notification_manager.delete(notification_id)
        self._load_notifications()
    
    def _mark_all_read(self):
        """Mark all notifications as read"""
        self.notification_manager.mark_all_read()
        self._load_notifications()
    
    def _clear_all(self):
        """Clear all notifications"""
        self.notification_manager.clear_all()
        self._load_notifications()
    
    def refresh(self):
        """Refresh notifications"""
        self._load_notifications()
    
    def showEvent(self, event):
        super().showEvent(event)
        self._load_notifications()
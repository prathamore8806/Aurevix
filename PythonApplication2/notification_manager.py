
# notification_manager.py - Global Notification System

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable
from enum import Enum

from PySide6.QtCore import QObject, Signal


class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CALIBRATION = "calibration"
    GESTURE = "gesture"
    SYSTEM = "system"


@dataclass
class Notification:
    id: str
    title: str
    message: str
    type: NotificationType
    timestamp: str
    read: bool = False
    icon: str = ""
    action: str = ""  # Optional action identifier
    data: dict = None  # Optional extra data
    
    def __post_init__(self):
        if not self.icon:
            icons = {
                NotificationType.SUCCESS: "✅",
                NotificationType.ERROR: "❌",
                NotificationType.WARNING: "⚠️",
                NotificationType.INFO: "ℹ️",
                NotificationType.CALIBRATION: "🎯",
                NotificationType.GESTURE: "👋",
                NotificationType.SYSTEM: "⚙️",
            }
            self.icon = icons.get(self.type, "📢")
        if self.data is None:
            self.data = {}
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "read": self.read,
            "icon": self.icon,
            "action": self.action,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        return cls(
            id=data["id"],
            title=data["title"],
            message=data["message"],
            type=NotificationType(data["type"]),
            timestamp=data["timestamp"],
            read=data.get("read", False),
            icon=data.get("icon", ""),
            action=data.get("action", ""),
            data=data.get("data", {})
        )


class NotificationManager(QObject):
    """
    Global Notification Manager - Singleton Pattern
    Handles all app notifications with persistence
    """
    
    # Signals
    notificationAdded = Signal(object)  # Notification
    notificationRead = Signal(str)  # notification_id
    notificationsCleared = Signal()
    unreadCountChanged = Signal(int)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        self.notifications: List[Notification] = []
        self.max_notifications = 100
        self._notification_counter = 0
        
        # Persistence
        self.storage_dir = Path.home() / ".gesture_control" / "notifications"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "notifications.json"
        
        self._load_notifications()
    
    def _generate_id(self) -> str:
        self._notification_counter += 1
        return f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._notification_counter}"
    
    def _load_notifications(self):
        """Load notifications from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.notifications = [Notification.from_dict(n) for n in data]
                    self._notification_counter = len(self.notifications)
            except Exception as e:
                print(f"⚠️ Error loading notifications: {e}")
                self.notifications = []
    
    def _save_notifications(self):
        """Save notifications to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump([n.to_dict() for n in self.notifications], f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving notifications: {e}")
    
    def add(self, title: str, message: str, 
            type: NotificationType = NotificationType.INFO,
            icon: str = "", action: str = "", data: dict = None) -> Notification:
        """Add a new notification"""
        notification = Notification(
            id=self._generate_id(),
            title=title,
            message=message,
            type=type,
            timestamp=datetime.now().isoformat(),
            icon=icon,
            action=action,
            data=data or {}
        )
        
        # Add to beginning (newest first)
        self.notifications.insert(0, notification)
        
        # Limit total notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[:self.max_notifications]
        
        self._save_notifications()
        self.notificationAdded.emit(notification)
        self.unreadCountChanged.emit(self.get_unread_count())
        
        print(f"🔔 Notification: {title} - {message}")
        return notification
    
    def add_success(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.SUCCESS, **kwargs)
    
    def add_error(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.ERROR, **kwargs)
    
    def add_warning(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.WARNING, **kwargs)
    
    def add_info(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.INFO, **kwargs)
    
    def add_calibration(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.CALIBRATION, icon="🎯", **kwargs)
    
    def add_gesture(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.GESTURE, icon="👋", **kwargs)
    
    def add_system(self, title: str, message: str, **kwargs) -> Notification:
        return self.add(title, message, NotificationType.SYSTEM, icon="⚙️", **kwargs)
    
    def mark_read(self, notification_id: str):
        """Mark a notification as read"""
        for notif in self.notifications:
            if notif.id == notification_id:
                notif.read = True
                self._save_notifications()
                self.notificationRead.emit(notification_id)
                self.unreadCountChanged.emit(self.get_unread_count())
                break
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        for notif in self.notifications:
            notif.read = True
        self._save_notifications()
        self.unreadCountChanged.emit(0)
    
    def delete(self, notification_id: str):
        """Delete a notification"""
        self.notifications = [n for n in self.notifications if n.id != notification_id]
        self._save_notifications()
        self.unreadCountChanged.emit(self.get_unread_count())
    
    def clear_all(self):
        """Clear all notifications"""
        self.notifications.clear()
        self._save_notifications()
        self.notificationsCleared.emit()
        self.unreadCountChanged.emit(0)
    
    def get_all(self) -> List[Notification]:
        """Get all notifications"""
        return self.notifications.copy()
    
    def get_unread(self) -> List[Notification]:
        """Get unread notifications"""
        return [n for n in self.notifications if not n.read]
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return len([n for n in self.notifications if not n.read])
    
    def get_by_type(self, type: NotificationType) -> List[Notification]:
        """Get notifications by type"""
        return [n for n in self.notifications if n.type == type]
    
    def get_recent(self, count: int = 10) -> List[Notification]:
        """Get recent notifications"""
        return self.notifications[:count]


# Global instance getter
def get_notification_manager() -> NotificationManager:
    return NotificationManager()
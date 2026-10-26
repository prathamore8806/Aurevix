"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📁 FUTURISTIC FILE ITEM                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ...config.colors import FuturisticColors


class FuturisticFileItem(QFrame):
    """
    Futuristic file list item with HUD-style design.
    
    Features:
    - Thumbnail preview
    - File name and metadata
    - Remove button
    - Accent color bar
    
    Usage:
        item = FuturisticFileItem("/path/to/file.pdf", thumbnail_pixmap, "Page 1 of 5")
        item.removeRequested.connect(on_remove)
    """
    
    removeRequested = Signal(str)
    
    def __init__(self, file_path: str, thumbnail: QPixmap, page_info: str = "", parent=None):
        super().__init__(parent)
        
        self.file_path = file_path
        self.setFixedHeight(75)
        
        self._setup_ui(thumbnail, page_info)
        self._apply_style()
    
    def _setup_ui(self, thumbnail: QPixmap, page_info: str):
        """Set up the file item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(15)
        
        # ═══════════════════════════════════════════════════════════════════
        # Accent color bar
        # ═══════════════════════════════════════════════════════════════════
        accent = QFrame()
        accent.setFixedSize(4, 75)
        accent.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {FuturisticColors.CYAN},
                stop:0.5 {FuturisticColors.ELECTRIC_BLUE},
                stop:1 {FuturisticColors.CYAN});
        """)
        layout.addWidget(accent)
        
        # ═══════════════════════════════════════════════════════════════════
        # Thumbnail frame
        # ═══════════════════════════════════════════════════════════════════
        thumb_frame = QFrame()
        thumb_frame.setFixedSize(80, 55)
        thumb_frame.setStyleSheet(f"""
            background: {FuturisticColors.NAVY_DARKER};
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 4px;
        """)
        thumb_layout = QVBoxLayout(thumb_frame)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        
        thumb_label = QLabel()
        if thumbnail and not thumbnail.isNull():
            thumb_label.setPixmap(
                thumbnail.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setStyleSheet("background: transparent;")
        thumb_layout.addWidget(thumb_label)
        layout.addWidget(thumb_frame)
        
        # ═══════════════════════════════════════════════════════════════════
        # File info section
        # ═══════════════════════════════════════════════════════════════════
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Filename
        filename = os.path.basename(self.file_path.split("#")[0])
        if len(filename) > 40:
            filename = filename[:37] + "..."
        
        name_label = QLabel(filename)
        name_label.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: {FuturisticColors.TEXT_PRIMARY};
            background: transparent;
        """)
        info_layout.addWidget(name_label)
        
        # Metadata row
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(15)
        
        # Page info
        if page_info:
            page_label = QLabel(f"◆ {page_info}")
            page_label.setStyleSheet(f"""
                font-family: 'Consolas', monospace;
                font-size: 10px;
                color: {FuturisticColors.CYAN};
                background: transparent;
            """)
            meta_layout.addWidget(page_label)
        
        # File size
        try:
            real_path = self.file_path.split("#")[0]
            if os.path.exists(real_path):
                size = os.path.getsize(real_path)
                if size < 1024 * 1024:
                    size_str = f"◆ {size / 1024:.1f} KB"
                else:
                    size_str = f"◆ {size / (1024 * 1024):.1f} MB"
                
                size_label = QLabel(size_str)
                size_label.setStyleSheet(f"""
                    font-family: 'Consolas', monospace;
                    font-size: 10px;
                    color: {FuturisticColors.TEXT_MUTED};
                    background: transparent;
                """)
                meta_layout.addWidget(size_label)
        except:
            pass
        
        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)
        layout.addLayout(info_layout, 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # Remove button
        # ═══════════════════════════════════════════════════════════════════
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(32, 32)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 4px;
                color: {FuturisticColors.RED};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid {FuturisticColors.RED};
                color: white;
            }}
        """)
        remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(remove_btn)
    
    def _apply_style(self):
        """Apply item styling"""
        self.setStyleSheet(f"""
            FuturisticFileItem {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(10, 22, 40, 0.9),
                    stop:1 rgba(15, 32, 56, 0.7));
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-left: none;
                border-radius: 0px 6px 6px 0px;
            }}
            FuturisticFileItem:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(15, 32, 56, 0.95),
                    stop:1 rgba(22, 42, 74, 0.8));
                border: 1px solid rgba(0, 212, 255, 0.4);
                border-left: none;
            }}
        """)
    
    def _on_remove_clicked(self):
        """Handle remove button click"""
        self.removeRequested.emit(self.file_path)
    
    def get_file_path(self) -> str:
        """Get the file path"""
        return self.file_path
    
    def get_base_path(self) -> str:
        """Get the base file path without page/slide info"""
        return self.file_path.split("#")[0]
    
    def update_thumbnail(self, thumbnail: QPixmap):
        """
        Update the thumbnail image.
        
        Args:
            thumbnail: New thumbnail pixmap
        """
        # Find and update the thumbnail label
        try:
            thumb_frame = self.findChild(QFrame)
            if thumb_frame:
                thumb_label = thumb_frame.findChild(QLabel)
                if thumb_label and thumbnail and not thumbnail.isNull():
                    thumb_label.setPixmap(
                        thumbnail.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )
        except:
            pass
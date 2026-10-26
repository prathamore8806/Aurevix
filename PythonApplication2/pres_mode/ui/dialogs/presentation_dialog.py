"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⬡ FUTURISTIC PRESENTATION DIALOG                         ║
║                    Full PPT/PDF/Image Support                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import shutil
import tempfile
import subprocess
import traceback
from typing import List, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QWidget, QFileDialog,
    QMessageBox, QGraphicsDropShadowEffect, QApplication,
    QProgressDialog
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPixmap, QColor, QImage, QPainter, QFont, QPen, QBrush

from ...config.colors import FuturisticColors
from ...config.dependencies import (
    PDF_AVAILABLE, PPTX_AVAILABLE, COMTYPES_AVAILABLE,
    LIBREOFFICE_AVAILABLE, LIBREOFFICE_PATH,
    fitz, PPTXPresentation, PP_ALIGN
)
from ...utils.cleanup import register_temp_directory, cleanup_single_directory

from ..widgets.buttons import FuturisticButton
from ..widgets.cards import FuturisticCard
from ..widgets.decorations import HexagonDecor, ScanLineOverlay
from ..widgets.file_item import FuturisticFileItem


class PresentationDialog(QDialog):
    """
    Futuristic Presentation Dialog with Full PPT Support.
    
    Features:
    - Load images, PDFs, PPT/PPTX files
    - Media type filtering
    - Thumbnail previews
    - Save/Load presets
    - LibreOffice, COM, python-pptx support
    
    Usage:
        dialog = PresentationDialog()
        dialog.presentation_started.connect(on_start)
        dialog.exec()
    """
    
    presentation_started = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("⬡ Presentation Studio")
        self.setFixedSize(1000, 750)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.slides: List[QPixmap] = []
        self.file_paths: List[str] = []
        self.slide_info: List[str] = []
        self.selected_media_type = "all"
        self._drag_pos = None
        self._destroyed = False
        
        self._build_ui()
        self._add_decorations()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main container
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 1000, 750)
        self.container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {FuturisticColors.NAVY_DARKEST},
                    stop:0.5 {FuturisticColors.NAVY_DARK},
                    stop:1 {FuturisticColors.NAVY_DARKER});
                border: 2px solid rgba(0, 212, 255, 0.4);
                border-radius: 12px;
            }}
        """)
        
        # Container glow
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(50)
        glow.setColor(QColor(0, 212, 255, 80))
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)
        
        layout = QVBoxLayout(self.container)
        layout.setSpacing(20)
        layout.setContentsMargins(35, 25, 35, 30)
        
        # ═══════════════════════════════════════════════════════════════════
        # Header
        # ═══════════════════════════════════════════════════════════════════
        header = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        
        hex_icon = QLabel("⬡")
        hex_icon.setStyleSheet(f"font-size: 32px; color: {FuturisticColors.CYAN}; background: transparent;")
        title_row.addWidget(hex_icon)
        
        title = QLabel("PRESENTATION STUDIO")
        title.setStyleSheet(f"""
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 24px;
            font-weight: bold;
            color: {FuturisticColors.TEXT_PRIMARY};
            background: transparent;
            letter-spacing: 4px;
        """)
        title_row.addWidget(title)
        title_row.addStretch()
        title_section.addLayout(title_row)
        
        subtitle = QLabel("◆ SWIPE = NAVIGATE • FIST = LOCK ZOOM • PINCH = ZOOM")
        subtitle.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {FuturisticColors.TEXT_MUTED};
            background: transparent;
            letter-spacing: 2px;
            padding-left: 46px;
        """)
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        header.addStretch()
        
        # Status indicators
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 22, 40, 0.8);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 6px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 8, 15, 8)
        status_layout.setSpacing(15)
        
        pdf_color = FuturisticColors.GREEN if PDF_AVAILABLE else FuturisticColors.RED
        pdf_status = QLabel("● PDF")
        pdf_status.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {pdf_color};
            background: transparent;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(pdf_status)
        
        lo_color = FuturisticColors.GREEN if LIBREOFFICE_AVAILABLE else FuturisticColors.ORANGE
        lo_status = QLabel("● LIBRE")
        lo_status.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {lo_color};
            background: transparent;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(lo_status)
        
        ppt_color = FuturisticColors.GREEN if (LIBREOFFICE_AVAILABLE or COMTYPES_AVAILABLE) else FuturisticColors.RED
        ppt_status = QLabel("● PPT")
        ppt_status.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {ppt_color};
            background: transparent;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(ppt_status)

        # ── NAYA: Microsoft PowerPoint COM status ──
        com_color = FuturisticColors.GREEN if COMTYPES_AVAILABLE else FuturisticColors.RED
        com_status = QLabel("● MS-PPT")
        com_status.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 10px;
            color: {com_color};
            background: transparent;
            letter-spacing: 1px;
        """)
        status_layout.addWidget(com_status)
        
        header.addWidget(status_frame)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(42, 42)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 6px;
                color: {FuturisticColors.TEXT_MUTED};
                font-size: 18px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid {FuturisticColors.RED};
                color: {FuturisticColors.RED};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)
        layout.addLayout(header)
        
        # ═══════════════════════════════════════════════════════════════════
        # Separator
        # ═══════════════════════════════════════════════════════════════════
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.2 rgba(0, 212, 255, 0.5),
                stop:0.8 rgba(0, 212, 255, 0.5),
                stop:1 transparent);
        """)
        layout.addWidget(sep)
        
        # ═══════════════════════════════════════════════════════════════════
        # Media type selection
        # ═══════════════════════════════════════════════════════════════════
        type_section = QFrame()
        type_section.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15, 32, 56, 0.5),
                    stop:1 rgba(10, 22, 40, 0.6));
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 8px;
            }}
        """)
        type_layout = QVBoxLayout(type_section)
        type_layout.setSpacing(15)
        type_layout.setContentsMargins(25, 18, 25, 18)
        
        type_header = QHBoxLayout()
        type_label = QLabel("◆ SELECT MEDIA TYPE")
        type_label.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: {FuturisticColors.TEXT_SECONDARY};
            background: transparent;
            letter-spacing: 2px;
        """)
        type_header.addWidget(type_label)
        type_header.addStretch()
        type_layout.addLayout(type_header)
        
        # Media type cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(18)
        
        self.card_all = FuturisticCard("🌐", "ALL", "Any Media", "all")
        self.card_images = FuturisticCard("🖼", "IMAGES", "PNG JPG BMP", "images")
        self.card_pdf = FuturisticCard("📄", "PDF", "Documents", "pdf")
        self.card_ppt = FuturisticCard("📊", "PPT", "Slides", "ppt")
        
        for card in [self.card_all, self.card_images, self.card_pdf, self.card_ppt]:
            card.clicked.connect(self._on_card_clicked)
            cards_layout.addWidget(card)
        
        cards_layout.addStretch()
        type_layout.addLayout(cards_layout)
        layout.addWidget(type_section)
        
        # Set initial selection
        self.card_all.set_selected(True)
        
        # ═══════════════════════════════════════════════════════════════════
        # File list section
        # ═══════════════════════════════════════════════════════════════════
        files_section = QFrame()
        files_section.setStyleSheet(f"""
            QFrame {{
                background: rgba(5, 16, 32, 0.6);
                border: 1px solid rgba(0, 212, 255, 0.15);
                border-radius: 8px;
            }}
        """)
        files_layout = QVBoxLayout(files_section)
        files_layout.setSpacing(12)
        files_layout.setContentsMargins(25, 18, 25, 18)
        
        files_header = QHBoxLayout()
        files_title = QLabel("◆ LOADED MEDIA FILES")
        files_title.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 12px;
            font-weight: bold;
            color: {FuturisticColors.TEXT_SECONDARY};
            background: transparent;
            letter-spacing: 2px;
        """)
        files_header.addWidget(files_title)
        
        self.files_count = QLabel("[ 0 SLIDES ]")
        self.files_count.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 11px;
            color: {FuturisticColors.CYAN};
            background: transparent;
            letter-spacing: 1px;
        """)
        files_header.addWidget(self.files_count)
        files_header.addStretch()
        files_layout.addLayout(files_header)
        
        # Scroll area for files
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: rgba(10, 22, 40, 0.5);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {FuturisticColors.CYAN}80,
                    stop:1 {FuturisticColors.ELECTRIC_BLUE}80);
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {FuturisticColors.CYAN};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.files_container = QWidget()
        self.files_container.setStyleSheet("background: transparent;")
        self.files_list_layout = QVBoxLayout(self.files_container)
        self.files_list_layout.setSpacing(8)
        self.files_list_layout.setContentsMargins(0, 5, 5, 5)
        self.files_list_layout.setAlignment(Qt.AlignTop)
        
        # Placeholder
        self.placeholder = QFrame()
        self.placeholder.setFixedHeight(150)
        self.placeholder.setStyleSheet(f"""
            QFrame {{
                background: rgba(10, 22, 40, 0.5);
                border: 2px dashed rgba(0, 212, 255, 0.3);
                border-radius: 8px;
            }}
        """)
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(10)
        
        placeholder_icon = QLabel("⬡")
        placeholder_icon.setStyleSheet(f"font-size: 48px; color: rgba(0, 212, 255, 0.4); background: transparent;")
        placeholder_icon.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_icon)
        
        placeholder_text = QLabel("DROP FILES HERE OR CLICK ADD FILES")
        placeholder_text.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 12px;
            color: {FuturisticColors.TEXT_MUTED};
            background: transparent;
            letter-spacing: 2px;
        """)
        placeholder_text.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_text)
        
        placeholder_sub = QLabel("SUPPORTED: PNG • JPG • PDF • PPT • PPTX")
        placeholder_sub.setStyleSheet(f"""
            font-family: 'Consolas', monospace;
            font-size: 9px;
            color: {FuturisticColors.TEXT_DARK};
            background: transparent;
            letter-spacing: 1px;
        """)
        placeholder_sub.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(placeholder_sub)
        
        self.files_list_layout.addWidget(self.placeholder)
        scroll.setWidget(self.files_container)
        scroll.setMinimumHeight(160)
        files_layout.addWidget(scroll)
        layout.addWidget(files_section, 1)
        
        # ═══════════════════════════════════════════════════════════════════
        # Action buttons row 1
        # ═══════════════════════════════════════════════════════════════════
        actions1 = QHBoxLayout()
        actions1.setSpacing(12)
        
        add_btn = FuturisticButton("+ ADD FILES", FuturisticColors.CYAN)
        add_btn.setFixedHeight(46)
        add_btn.clicked.connect(self._add_files)
        actions1.addWidget(add_btn)
        
        clear_btn = FuturisticButton("⌫ CLEAR ALL", FuturisticColors.ORANGE)
        clear_btn.setFixedHeight(46)
        clear_btn.clicked.connect(self._clear_all)
        actions1.addWidget(clear_btn)
        
        actions1.addStretch()
        
        save_btn = FuturisticButton("◇ SAVE PRESET", FuturisticColors.ELECTRIC_BLUE)
        save_btn.setFixedHeight(46)
        save_btn.clicked.connect(self._save_presentation)
        actions1.addWidget(save_btn)
        
        load_btn = FuturisticButton("◈ LOAD PRESET", FuturisticColors.TEAL)
        load_btn.setFixedHeight(46)
        load_btn.clicked.connect(self._load_presentation)
        actions1.addWidget(load_btn)
        layout.addLayout(actions1)
        
        # ═══════════════════════════════════════════════════════════════════
        # Action buttons row 2
        # ═══════════════════════════════════════════════════════════════════
        actions2 = QHBoxLayout()
        actions2.setSpacing(20)
        
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setFixedHeight(52)
        cancel_btn.setFixedWidth(150)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(30, 58, 95, 0.4);
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                color: {FuturisticColors.TEXT_SECONDARY};
                font-family: 'Consolas', monospace;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: rgba(30, 58, 95, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.5);
                color: white;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        actions2.addWidget(cancel_btn)
        actions2.addStretch()
        
        # Launch button
        self.start_btn = QPushButton("▶  LAUNCH PRESENTATION")
        self.start_btn.setFixedHeight(58)
        self.start_btn.setFixedWidth(320)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 0.2),
                    stop:0.5 rgba(59, 130, 246, 0.2),
                    stop:1 rgba(0, 212, 255, 0.2));
                border: 2px solid {FuturisticColors.CYAN};
                border-radius: 6px;
                color: {FuturisticColors.CYAN};
                font-family: 'Consolas', monospace;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 0.4),
                    stop:0.5 rgba(59, 130, 246, 0.4),
                    stop:1 rgba(0, 212, 255, 0.4));
                color: white;
            }}
            QPushButton:disabled {{
                background: rgba(30, 58, 95, 0.2);
                border: 2px solid rgba(100, 116, 139, 0.3);
                color: rgba(100, 116, 139, 0.5);
            }}
        """)
        
        start_glow = QGraphicsDropShadowEffect()
        start_glow.setBlurRadius(25)
        start_glow.setColor(QColor(0, 212, 255, 100))
        start_glow.setOffset(0, 0)
        self.start_btn.setGraphicsEffect(start_glow)
        self.start_btn.clicked.connect(self._start_presentation)
        actions2.addWidget(self.start_btn)
        layout.addLayout(actions2)
        
        # Add scanlines
        self.scanlines = ScanLineOverlay(self.container)
        self.scanlines.setGeometry(0, 0, 1000, 750)
        self.scanlines.lower()
    
    def _add_decorations(self):
        """Add hexagon decorations"""
        positions = [(920, 50, 30), (880, 680, 25), (50, 650, 35), (30, 100, 20)]
        self.hex_decorations = []
        for x, y, size in positions:
            hex_decor = HexagonDecor(size, FuturisticColors.CYAN, self.container)
            hex_decor.move(x, y)
            self.hex_decorations.append(hex_decor)
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📋 CARD SELECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _on_card_clicked(self, card_id: str):
        """Handle card selection"""
        if self._destroyed:
            return
        
        self.selected_media_type = card_id
        self.card_all.set_selected(card_id == "all")
        self.card_images.set_selected(card_id == "images")
        self.card_pdf.set_selected(card_id == "pdf")
        self.card_ppt.set_selected(card_id == "ppt")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📁 FILE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _add_files(self):
        """Open file dialog to add files"""
        if self._destroyed:
            return
        
        filters = {
            "all": "All Media (*.png *.jpg *.jpeg *.bmp *.gif *.pdf *.ppt *.pptx);;All Files (*)",
            "images": "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
            "pdf": "PDF Documents (*.pdf);;All Files (*)",
            "ppt": "PowerPoint (*.ppt *.pptx);;All Files (*)"
        }
        
        file_filter = filters.get(self.selected_media_type, filters["all"])
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", file_filter)
        
        if files:
            self._process_files(files)
    
    def _process_files(self, files: List[str]):
        """Process selected files"""
        if self._destroyed:
            return
        
        for file_path in files:
            try:
                if file_path not in [fp.split("#")[0] for fp in self.file_paths]:
                    self._process_single_file(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        self._update_ui()
    
    def _process_single_file(self, file_path: str):
        """Process a single file"""
        if self._destroyed:
            return
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                self._add_image_file(file_path)
            elif ext == '.pdf':
                if PDF_AVAILABLE:
                    self._add_pdf_file(file_path)
                else:
                    self._show_message(
                        "PDF NOT SUPPORTED",
                        "Install PyMuPDF for PDF support:\n\npip install PyMuPDF",
                        "warning"
                    )
            elif ext in ['.ppt', '.pptx']:
                self._add_ppt_file(file_path)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            traceback.print_exc()
    
    def _add_image_file(self, file_path: str):
        """Add an image file"""
        if self._destroyed:
            return
        
        try:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.slides.append(pixmap)
                self.file_paths.append(file_path)
                self.slide_info.append("")
                
                thumb = pixmap.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._add_file_widget(file_path, thumb, "IMAGE")
        except Exception as e:
            print(f"Error adding image: {e}")
    
    def _add_pdf_file(self, file_path: str):
        """Add PDF file - FIXED: Proper memory handling"""
        if self._destroyed:
            return
        
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    mat = fitz.Matrix(2.5, 2.5)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # FIXED: Copy the image data to prevent memory issues
                    img = QImage(
                        pix.samples, pix.width, pix.height, pix.stride,
                        QImage.Format_RGB888
                    ).copy()
                    pixmap = QPixmap.fromImage(img)
                    
                    if not pixmap.isNull():
                        self.slides.append(pixmap)
                        path_with_page = f"{file_path}#page{page_num + 1}"
                        self.file_paths.append(path_with_page)
                        self.slide_info.append(f"Page {page_num + 1} of {total_pages}")
                        
                        thumb = pixmap.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self._add_file_widget(path_with_page, thumb, f"PAGE {page_num + 1}/{total_pages}")
                except Exception as e:
                    print(f"Error processing PDF page {page_num}: {e}")
            
            doc.close()
            print(f"✅ Loaded {total_pages} pages from PDF")
        except Exception as e:
            self._show_message("PDF ERROR", f"Failed to load PDF:\n{str(e)}", "error")
    
    def _add_ppt_file(self, file_path: str):
        """Handle PPT/PPTX files - MS PowerPoint COM pehle try hoga"""
        if self._destroyed:
            return

        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        errors = []

        print(f"📊 Processing: {filename}")

        # ── Method 1: Microsoft PowerPoint COM (Windows, best quality) ──
        if COMTYPES_AVAILABLE and sys.platform == 'win32':
            try:
                print(f"  → Method 1: Microsoft PowerPoint COM...")
                self._add_ppt_via_com(file_path)
                print(f"  ✅ PowerPoint COM success!")
                return
            except Exception as e:
                errors.append(f"MS PowerPoint COM: {e}")
                print(f"  ✗ COM failed: {e}")

        # ── Method 2: LibreOffice (cross-platform, good quality) ──
        if LIBREOFFICE_AVAILABLE and PDF_AVAILABLE:
            try:
                print(f"  → Method 2: LibreOffice conversion...")
                self._add_ppt_via_libreoffice(file_path)
                print(f"  ✅ LibreOffice success!")
                return
            except Exception as e:
                errors.append(f"LibreOffice: {e}")
                print(f"  ✗ LibreOffice failed: {e}")

        # ── Method 3: python-pptx (sirf .pptx, basic rendering) ──
        if PPTX_AVAILABLE and ext == '.pptx':
            try:
                print(f"  → Method 3: python-pptx rendering...")
                self._add_pptx_rendered(file_path)
                print(f"  ✅ python-pptx success!")
                return
            except Exception as e:
                errors.append(f"python-pptx: {e}")
                print(f"  ✗ python-pptx failed: {e}")

        # ── Koi method kaam nahi aaya ──
        self._show_ppt_install_help(file_path, errors)

    def _add_ppt_via_libreoffice(self, file_path: str):
        """Convert PPT/PPTX to PDF using LibreOffice"""
        if self._destroyed:
            return
        
        temp_dir = tempfile.mkdtemp(prefix="presentation_")
        register_temp_directory(temp_dir)
        
        try:
            progress = QProgressDialog("Converting PPT to slides...", None, 0, 0, self)
            progress.setWindowTitle("⬡ Converting")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()
            
            cmd = [
                LIBREOFFICE_PATH,
                '--headless',
                '--invisible',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                file_path
            ]
            
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=180, startupinfo=startupinfo
            )
            
            if result.returncode != 0:
                raise Exception(f"Conversion failed: {result.stderr}")
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
            
            if not os.path.exists(pdf_path):
                pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
                if pdf_files:
                    pdf_path = os.path.join(temp_dir, pdf_files[0])
                else:
                    raise Exception("No PDF generated")
            
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            progress.setMaximum(total_pages)
            progress.setLabelText(f"Loading {total_pages} slides...")
            
            for page_num in range(total_pages):
                try:
                    progress.setValue(page_num + 1)
                    QApplication.processEvents()
                    
                    page = doc[page_num]
                    mat = fitz.Matrix(2.5, 2.5)
                    pix = page.get_pixmap(matrix=mat)
                    
                    img = QImage(
                        pix.samples, pix.width, pix.height, pix.stride,
                        QImage.Format_RGB888
                    ).copy()
                    pixmap = QPixmap.fromImage(img)
                    
                    if not pixmap.isNull():
                        self.slides.append(pixmap)
                        path_with_page = f"{file_path}#slide{page_num + 1}"
                        self.file_paths.append(path_with_page)
                        self.slide_info.append(f"Slide {page_num + 1} of {total_pages}")
                        
                        thumb = pixmap.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self._add_file_widget(path_with_page, thumb, f"SLIDE {page_num + 1}/{total_pages}")
                        
                except Exception as e:
                    print(f"  ⚠ Error on slide {page_num + 1}: {e}")
            
            doc.close()
            progress.close()
            
            print(f"  ✅ Successfully loaded {total_pages} slides from PPT!")
            
        finally:
            cleanup_single_directory(temp_dir)

    def _add_ppt_via_com(self, file_path: str):
        """
        Convert PPT/PPTX using Microsoft PowerPoint COM Automation.
        Requirements: Windows + Microsoft Office installed + pip install comtypes
        """
        if self._destroyed:
            return

        try:
            import comtypes.client
            import pythoncom
        except ImportError:
            raise Exception("comtypes not installed. Run: pip install comtypes")

        pythoncom.CoInitialize()

        powerpoint = None
        presentation = None
        temp_dir = None

        try:
            # ── Progress Dialog ──
            progress = QProgressDialog(
                "Opening Microsoft PowerPoint...",
                None, 0, 0, self
            )
            progress.setWindowTitle("⬡ MS PowerPoint COM")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            # ── PowerPoint application banana ──
            try:
                powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            except Exception as e:
                raise Exception(
                    f"Microsoft PowerPoint nahi mila.\n"
                    f"Microsoft Office install karo.\nError: {e}"
                )

            try:
                powerpoint.Visible = False
            except:
                try:
                    powerpoint.Visible = True
                except:
                    pass

            QApplication.processEvents()

            # ── File open karo ──
            progress.setLabelText("Loading presentation file...")
            QApplication.processEvents()

            abs_path = os.path.abspath(file_path)

            try:
                presentation = powerpoint.Presentations.Open(
                    abs_path,
                    ReadOnly=True,
                    Untitled=False,
                    WithWindow=False
                )
            except Exception as e:
                raise Exception(f"File open nahi hui: {e}")

            total_slides = presentation.Slides.Count
            print(f"     📊 Total slides: {total_slides}")

            if total_slides == 0:
                raise Exception("Presentation mein koi slide nahi hai!")

            # ── Temp directory ──
            temp_dir = tempfile.mkdtemp(prefix="ppt_com_")
            register_temp_directory(temp_dir)

            # ── Har slide PNG mein export karo ──
            progress.setMaximum(total_slides)
            progress.setLabelText(f"Exporting {total_slides} slides...")
            QApplication.processEvents()

            success_count = 0

            for slide_num in range(1, total_slides + 1):
                try:
                    progress.setValue(slide_num)
                    progress.setLabelText(
                        f"Exporting slide {slide_num} of {total_slides}..."
                    )
                    QApplication.processEvents()

                    slide = presentation.Slides(slide_num)
                    temp_png = os.path.join(temp_dir, f"slide_{slide_num:04d}.png")

                    slide.Export(temp_png, "PNG", 1920, 1080)

                    if not os.path.exists(temp_png):
                        print(f"     ⚠ Slide {slide_num}: PNG nahi bana")
                        continue

                    pixmap = QPixmap(temp_png)

                    if pixmap.isNull():
                        print(f"     ⚠ Slide {slide_num}: Invalid image")
                        try:
                            os.remove(temp_png)
                        except:
                            pass
                        continue

                    self.slides.append(pixmap)
                    path_with_slide = f"{file_path}#slide{slide_num}"
                    self.file_paths.append(path_with_slide)
                    self.slide_info.append(f"Slide {slide_num} of {total_slides}")

                    thumb = pixmap.scaled(
                        72, 47,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self._add_file_widget(
                        path_with_slide,
                        thumb,
                        f"SLIDE {slide_num}/{total_slides}"
                    )

                    try:
                        os.remove(temp_png)
                    except:
                        pass

                    success_count += 1

                    if slide_num % 5 == 0:
                        self._update_ui()
                        QApplication.processEvents()

                except Exception as e:
                    print(f"     ⚠ Slide {slide_num} error: {e}")
                    continue

            progress.close()
            print(f"     ✅ COM Export: {success_count}/{total_slides} slides")

            if success_count == 0:
                raise Exception("Koi bhi slide export nahi hua!")

        except Exception as e:
            try:
                progress.close()
            except:
                pass
            raise e

        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except:
                    pass

            if powerpoint is not None:
                try:
                    powerpoint.Quit()
                except:
                    pass

            try:
                pythoncom.CoUninitialize()
            except:
                pass

            if temp_dir and os.path.exists(temp_dir):
                try:
                    cleanup_single_directory(temp_dir)
                except:
                    pass
    
    def _add_pptx_rendered(self, file_path: str):
        """Load PPTX with python-pptx"""
        if self._destroyed:
            return
        
        try:
            prs = PPTXPresentation(file_path)
            total_slides = len(prs.slides)
            
            try:
                slide_width = prs.slide_width
                slide_height = prs.slide_height
                dpi = 150
                px_width = int(slide_width / 914400 * dpi)
                px_height = int(slide_height / 914400 * dpi)
            except:
                px_width = 960
                px_height = 720
            
            px_width = max(px_width, 800)
            px_height = max(px_height, 600)
            
            for idx, slide in enumerate(prs.slides):
                try:
                    pixmap = self._render_pptx_slide(
                        slide, px_width, px_height, idx + 1, total_slides, file_path
                    )
                    
                    if pixmap and not pixmap.isNull():
                        self.slides.append(pixmap)
                        path_with_page = f"{file_path}#slide{idx + 1}"
                        self.file_paths.append(path_with_page)
                        self.slide_info.append(f"Slide {idx + 1} of {total_slides}")
                        
                        thumb = pixmap.scaled(72, 47, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self._add_file_widget(path_with_page, thumb, f"SLIDE {idx + 1}/{total_slides}")
                        
                except Exception as e:
                    print(f"  ⚠ Error rendering slide {idx + 1}: {e}")
            
            self._show_message(
                "PPTX LOADED",
                f"Loaded {total_slides} slides.\n\nFor best results, install LibreOffice.",
                "info"
            )
            
        except Exception as e:
            raise Exception(f"python-pptx rendering failed: {e}")
    
    def _render_pptx_slide(self, slide, width: int, height: int, slide_num: int, total: int, file_path: str) -> QPixmap:
        """Render a PPTX slide"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(255, 255, 255))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        try:
            # Grid
            pen = QPen(QColor(245, 245, 245))
            painter.setPen(pen)
            for x in range(0, width, 50):
                painter.drawLine(x, 0, x, height)
            for y in range(0, height, 50):
                painter.drawLine(0, y, width, y)
            
            # Shapes
            for shape in slide.shapes:
                try:
                    self._draw_pptx_shape(painter, shape, width, height)
                except:
                    pass
            
            # Slide number
            painter.setPen(QPen(QColor(180, 180, 180)))
            font = QFont("Consolas", 8)
            painter.setFont(font)
            painter.drawText(
                width - 60, height - 25, 55, 20,
                Qt.AlignRight | Qt.AlignVCenter,
                f"{slide_num}/{total}"
            )
            
        finally:
            painter.end()
        
        return pixmap
    
    def _draw_pptx_shape(self, painter: QPainter, shape, slide_w: int, slide_h: int):
        """Draw a PPTX shape"""
        try:
            dpi = 150
            emu_per_px = 914400 / dpi
            
            x = int(shape.left / emu_per_px) if shape.left else 0
            y = int(shape.top / emu_per_px) if shape.top else 0
            w = int(shape.width / emu_per_px) if shape.width else 100
            h = int(shape.height / emu_per_px) if shape.height else 50
        except:
            return
        
        shape_rect = QRect(x, y, w, h)
        
        # Fill
        try:
            if hasattr(shape, 'fill') and shape.fill and shape.fill.type is not None:
                painter.setBrush(QBrush(QColor(240, 240, 250)))
                painter.setPen(QPen(QColor(220, 220, 230), 1))
                painter.drawRect(shape_rect)
        except:
            pass
        
        # Text
        if shape.has_text_frame:
            try:
                current_y = y + 8
                
                for paragraph in shape.text_frame.paragraphs:
                    font_size = 14
                    font_bold = False
                    font_color = QColor(0, 0, 0)
                    full_text = ""
                    
                    for run in paragraph.runs:
                        full_text += run.text
                        
                        if run.font:
                            if run.font.size:
                                try:
                                    font_size = int(run.font.size.pt)
                                except:
                                    pass
                            if run.font.bold:
                                font_bold = True
                            if run.font.color and run.font.color.rgb:
                                try:
                                    rgb_str = str(run.font.color.rgb)
                                    font_color = QColor(f"#{rgb_str}")
                                except:
                                    pass
                    
                    if not full_text.strip():
                        current_y += font_size + 4
                        continue
                    
                    render_size = max(8, min(font_size, 48))
                    
                    font = QFont("Arial", render_size)
                    font.setBold(font_bold)
                    painter.setFont(font)
                    painter.setPen(QPen(font_color))
                    
                    align = Qt.AlignLeft
                    if PP_ALIGN:
                        try:
                            if paragraph.alignment == PP_ALIGN.CENTER:
                                align = Qt.AlignHCenter
                            elif paragraph.alignment == PP_ALIGN.RIGHT:
                                align = Qt.AlignRight
                        except:
                            pass
                    
                    text_rect = QRect(x + 8, current_y, w - 16, render_size + 10)
                    painter.drawText(text_rect, align | Qt.AlignTop | Qt.TextWordWrap, full_text)
                    
                    current_y += render_size + 10
                    
            except:
                pass
        
                # Images
        try:
            if hasattr(shape, 'shape_type') and shape.shape_type == 13:
                image = shape.image
                img_bytes = image.blob
                
                qimg = QImage()
                qimg.loadFromData(img_bytes)
                
                if not qimg.isNull():
                    pix = QPixmap.fromImage(qimg)
                    scaled = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    painter.drawPixmap(x, y, scaled)
        except:
            pass

    def _show_ppt_install_help(self, file_path: str, errors: list = None):
        """Show installation help for PPT support"""
        if self._destroyed:
            return

        methods = []

        if sys.platform == 'win32':
            if not COMTYPES_AVAILABLE:
                methods.append(
                    "① Microsoft PowerPoint COM (Best Quality):\n"
                    "   • Microsoft Office install karo\n"
                    "   • pip install comtypes"
                )
            else:
                methods.append(
                    "① PowerPoint COM available hai but failed\n"
                    "   • Microsoft Office properly install karo\n"
                    "   • File corrupt na ho"
                )

        if not LIBREOFFICE_AVAILABLE:
            methods.append(
                "② LibreOffice (FREE):\n"
                "   https://www.libreoffice.org/download/"
            )

        if not PDF_AVAILABLE:
            methods.append(
                "③ PyMuPDF:\n"
                "   pip install PyMuPDF"
            )

        if not PPTX_AVAILABLE:
            methods.append(
                "④ python-pptx:\n"
                "   pip install python-pptx"
            )

        methods.append(
            "⑤ Manual:\n"
            "   PowerPoint → File → Export → PDF"
        )

        method_text = "\n\n".join(methods)

        error_text = ""
        if errors:
            error_text = "\n\n─── ERRORS ───\n"
            error_text += "\n".join(f"• {e}" for e in errors)

        self._show_message(
            "PPT SUPPORT NEEDED",
            f"Cannot open: {os.path.basename(file_path)}\n\n"
            f"{method_text}{error_text}",
            "warning"
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🗂️ FILE LIST MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _add_file_widget(self, file_path: str, thumbnail: QPixmap, page_info: str):
        """Add a file item widget to the list"""
        if self._destroyed:
            return
        
        try:
            if self.placeholder.isVisible():
                self.placeholder.hide()
            
            widget = FuturisticFileItem(file_path, thumbnail, page_info)
            widget.removeRequested.connect(self._remove_file)
            self.files_list_layout.addWidget(widget)
        except Exception as e:
            print(f"Error adding file widget: {e}")
    
    def _remove_file(self, file_path: str):
        """Remove a file from the list"""
        if self._destroyed:
            return
        
        try:
            if file_path in self.file_paths:
                idx = self.file_paths.index(file_path)
                self.file_paths.pop(idx)
                if idx < len(self.slides):
                    self.slides.pop(idx)
                if idx < len(self.slide_info):
                    self.slide_info.pop(idx)
            
            for i in range(self.files_list_layout.count()):
                item = self.files_list_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, FuturisticFileItem) and widget.file_path == file_path:
                        widget.deleteLater()
                        break
            
            self._update_ui()
        except Exception as e:
            print(f"Error removing file: {e}")
    
    def _clear_all(self):
        """Clear all loaded files"""
        if self._destroyed:
            return
        
        try:
            self.slides.clear()
            self.file_paths.clear()
            self.slide_info.clear()
            
            for i in reversed(range(self.files_list_layout.count())):
                item = self.files_list_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if isinstance(widget, FuturisticFileItem):
                        widget.deleteLater()
            
            self._update_ui()
        except Exception as e:
            print(f"Error clearing: {e}")
    
    def _update_ui(self):
        """Update UI state based on loaded files"""
        if self._destroyed:
            return
        
        try:
            count = len(self.slides)
            self.files_count.setText(f"[ {count} SLIDE{'S' if count != 1 else ''} ]")
            self.start_btn.setEnabled(count > 0)
            
            if count == 0:
                self.placeholder.show()
            else:
                self.placeholder.hide()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         💾 SAVE/LOAD PRESETS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _save_presentation(self):
        """Save presentation preset to JSON"""
        if self._destroyed:
            return
        
        if not self.file_paths:
            self._show_message("NO FILES", "Add files first.", "warning")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Preset", "presentation.json", "JSON (*.json)"
            )
            
            if file_path:
                original_paths = list(set([fp.split("#")[0] for fp in self.file_paths]))
                data = {
                    "version": "5.1",
                    "type": "futuristic_presentation",
                    "files": original_paths,
                    "created": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self._show_message("SAVED", "Preset saved!", "info")
        except Exception as e:
            self._show_message("ERROR", f"Failed to save:\n{str(e)}", "error")
    
    def _load_presentation(self):
        """Load presentation preset from JSON"""
        if self._destroyed:
            return
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load Preset", "", "JSON (*.json)"
            )
            
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                files = data.get("files", [])
                self._clear_all()
                
                valid_files = [f for f in files if os.path.exists(f)]
                
                if valid_files:
                    self._process_files(valid_files)
                    self._show_message("LOADED", f"Loaded {len(valid_files)} file(s)!", "info")
                else:
                    self._show_message("NO FILES", "No valid files found.", "warning")
        except Exception as e:
            self._show_message("ERROR", f"Failed to load:\n{str(e)}", "error")
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🚀 START PRESENTATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _start_presentation(self):
        """Start the presentation"""
        if self._destroyed:
            return
        
        if self.slides:
            print(f"▶ Launching presentation with {len(self.slides)} slides")
            slides_copy = [slide.copy() for slide in self.slides if slide and not slide.isNull()]
            self.presentation_started.emit(slides_copy)
            self.accept()
    
    def get_slides(self) -> List[QPixmap]:
        """Get the loaded slides"""
        return self.slides
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         💬 MESSAGE DIALOG
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_message(self, title: str, message: str, msg_type: str = "info"):
        """Show a styled message dialog"""
        if self._destroyed:
            return
        
        try:
            msg = QMessageBox(self)
            msg.setWindowTitle(f"⬡ {title}")
            msg.setText(message)
            
            if msg_type == "error":
                msg.setIcon(QMessageBox.Critical)
            elif msg_type == "warning":
                msg.setIcon(QMessageBox.Warning)
            else:
                msg.setIcon(QMessageBox.Information)
            
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background: {FuturisticColors.NAVY_DARK};
                }}
                QMessageBox QLabel {{
                    color: {FuturisticColors.TEXT_PRIMARY};
                    font-family: 'Consolas', monospace;
                    font-size: 11px;
                }}
                QPushButton {{
                    background: rgba(0, 212, 255, 0.2);
                    border: 1px solid {FuturisticColors.CYAN};
                    border-radius: 4px;
                    color: {FuturisticColors.CYAN};
                    font-family: 'Consolas', monospace;
                    padding: 8px 25px;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background: rgba(0, 212, 255, 0.4);
                    color: white;
                }}
            """)
            msg.exec()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🧹 CLEANUP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _cleanup(self):
        """Cleanup resources"""
        self._destroyed = True
        
        try:
            for card in [self.card_all, self.card_images, self.card_pdf, self.card_ppt]:
                if card:
                    card.cleanup()
        except:
            pass
        
        try:
            if hasattr(self, 'scanlines') and self.scanlines:
                self.scanlines.stop_animation()
        except:
            pass
        
        try:
            if hasattr(self, 'hex_decorations'):
                for hex_decor in self.hex_decorations:
                    if hex_decor:
                        hex_decor.stop_animation()
        except:
            pass
    
    def reject(self):
        """Handle dialog rejection"""
        self._cleanup()
        super().reject()
    
    def accept(self):
        """Handle dialog acceptance"""
        self._cleanup()
        super().accept()
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🖱️ WINDOW DRAGGING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self._drag_pos = None
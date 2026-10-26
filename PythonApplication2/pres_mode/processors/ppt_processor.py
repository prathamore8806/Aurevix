"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📊 PPT PROCESSOR                                     ║
║                    Handle PowerPoint Files (PPT/PPTX)                        ║
║                    Multiple Conversion Methods Supported                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess
import tempfile
from typing import List, Optional
from enum import Enum, auto

from PySide6.QtWidgets import QApplication, QProgressDialog
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen, QBrush
from PySide6.QtCore import Qt, QRect

from .base import BaseProcessor, ProcessorResult, ProcessorStatus
from ..config.dependencies import (
    PDF_AVAILABLE, PPTX_AVAILABLE, COMTYPES_AVAILABLE,
    LIBREOFFICE_AVAILABLE, LIBREOFFICE_PATH,
    fitz, PPTXPresentation, PP_ALIGN
)
from ..utils.cleanup import register_temp_directory, cleanup_single_directory


class ConversionMethod(Enum):
    """Available PPT conversion methods"""
    LIBREOFFICE = auto()
    COM = auto()
    PYTHON_PPTX = auto()
    NONE = auto()


class PPTProcessor(BaseProcessor):
    """
    Processor for PowerPoint files using multiple conversion methods.
    
    Conversion Methods (in priority order):
    1. LibreOffice (best quality, cross-platform)
    2. COM Automation (Windows only, requires PowerPoint)
    3. python-pptx (limited rendering, no images)
    
    Requirements (at least one):
    - LibreOffice: https://www.libreoffice.org/download/
    - PyMuPDF: pip install PyMuPDF (for LibreOffice method)
    - python-pptx: pip install python-pptx
    - comtypes: pip install comtypes (Windows only)
    
    Usage:
        processor = PPTProcessor()
        result = processor.process("presentation.pptx")
        
        if result.is_success:
            for slide in result.slides:
                display(slide)
    """
    
    supported_extensions: List[str] = ['.ppt', '.pptx']
    processor_name: str = "PPT"
    
    def __init__(self, preferred_method: ConversionMethod = None):
        """
        Initialize PPT processor.
        
        Args:
            preferred_method: Force a specific conversion method
        """
        super().__init__()
        self.preferred_method = preferred_method
        self._progress_dialog: Optional[QProgressDialog] = None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if any conversion method is available"""
        return LIBREOFFICE_AVAILABLE or COMTYPES_AVAILABLE or PPTX_AVAILABLE
    
    @classmethod
    def get_available_methods(cls) -> List[ConversionMethod]:
        """Get list of available conversion methods"""
        methods = []
        
        if LIBREOFFICE_AVAILABLE and PDF_AVAILABLE:
            methods.append(ConversionMethod.LIBREOFFICE)
        
        if COMTYPES_AVAILABLE and sys.platform == 'win32':
            methods.append(ConversionMethod.COM)
        
        if PPTX_AVAILABLE:
            methods.append(ConversionMethod.PYTHON_PPTX)
        
        return methods
    
    @classmethod
    def get_best_method(cls) -> ConversionMethod:
        """Get the best available conversion method"""
        methods = cls.get_available_methods()
        return methods[0] if methods else ConversionMethod.NONE
    
    def process(
        self,
        file_path: str,
        method: ConversionMethod = None,
        show_progress: bool = True
    ) -> ProcessorResult:
        """
        Process a PowerPoint file.
        
        Args:
            file_path: Path to the PPT/PPTX file
            method: Force a specific conversion method
            show_progress: Show progress dialog
            
        Returns:
            ProcessorResult with slides
        """
        result = ProcessorResult()
        
        # Validate file
        if not file_path:
            result.status = ProcessorStatus.FAILED
            result.message = "No file path provided"
            self._set_error(result.message)
            return result
        
        if not os.path.exists(file_path):
            result.status = ProcessorStatus.FAILED
            result.message = f"File not found: {file_path}"
            self._set_error(result.message)
            return result
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            result.status = ProcessorStatus.UNSUPPORTED
            result.message = f"Unsupported format: {ext}"
            self._set_error(result.message)
            return result
        
        # Determine conversion method
        use_method = method or self.preferred_method or self.get_best_method()
        
        if use_method == ConversionMethod.NONE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = self._get_install_help()
            self._set_error("No conversion method available")
            return result
        
        filename = os.path.basename(file_path)
        self._log(f"Processing: {filename} (method: {use_method.name})")
        
        # Try conversion methods
        if use_method == ConversionMethod.LIBREOFFICE:
            return self._process_via_libreoffice(file_path, show_progress)
        elif use_method == ConversionMethod.COM:
            return self._process_via_com(file_path, show_progress)
        elif use_method == ConversionMethod.PYTHON_PPTX:
            return self._process_via_pptx(file_path, show_progress)
        else:
            result.status = ProcessorStatus.FAILED
            result.message = "No valid conversion method"
            return result
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🔷 LIBREOFFICE METHOD
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _process_via_libreoffice(
        self,
        file_path: str,
        show_progress: bool = True
    ) -> ProcessorResult:
        """Convert PPT to PDF using LibreOffice, then render pages"""
        result = ProcessorResult()
        
        if not LIBREOFFICE_AVAILABLE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = "LibreOffice not found"
            return result
        
        if not PDF_AVAILABLE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = "PyMuPDF not installed"
            return result
        
        temp_dir = tempfile.mkdtemp(prefix="ppt_convert_")
        register_temp_directory(temp_dir)
        
        try:
            # Show progress
            if show_progress:
                self._show_progress("Converting PPT to slides...", 0, 0)
            
            # Build command
            cmd = [
                LIBREOFFICE_PATH,
                '--headless',
                '--invisible',
                '--convert-to', 'pdf',
                '--outdir', temp_dir,
                file_path
            ]
            
            # Windows: hide console window
            startupinfo = None
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # Run conversion
            proc_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                startupinfo=startupinfo
            )
            
            if proc_result.returncode != 0:
                raise Exception(f"Conversion failed: {proc_result.stderr}")
            
            # Find generated PDF
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
            
            if not os.path.exists(pdf_path):
                pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
                if pdf_files:
                    pdf_path = os.path.join(temp_dir, pdf_files[0])
                else:
                    raise Exception("No PDF generated")
            
            # Open and render PDF
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            if show_progress:
                self._update_progress(f"Loading {total_pages} slides...", 0, total_pages)
            
            mat = fitz.Matrix(2.5, 2.5)
            
            for page_num in range(total_pages):
                try:
                    if show_progress:
                        self._update_progress(None, page_num + 1, total_pages)
                        QApplication.processEvents()
                    
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Copy image data
                    img = QImage(
                        pix.samples,
                        pix.width,
                        pix.height,
                        pix.stride,
                        QImage.Format_RGB888
                    ).copy()
                    
                    pixmap = QPixmap.fromImage(img)
                    
                    if not pixmap.isNull():
                        thumbnail = self.generate_thumbnail(pixmap)
                        path_with_slide = f"{file_path}#slide{page_num + 1}"
                        
                        result.add_slide(
                            pixmap=pixmap,
                            file_path=path_with_slide,
                            info=f"Slide {page_num + 1} of {total_pages}",
                            thumbnail=thumbnail
                        )
                        
                except Exception as e:
                    self._log(f"⚠️ Error on slide {page_num + 1}: {e}")
            
            doc.close()
            
            if show_progress:
                self._close_progress()
            
            if result.has_slides:
                result.status = ProcessorStatus.SUCCESS
                result.message = f"Loaded {result.total_pages} slides via LibreOffice"
                self._log(f"✅ {result.message}")
            else:
                result.status = ProcessorStatus.FAILED
                result.message = "No slides could be loaded"
            
        except subprocess.TimeoutExpired:
            result.status = ProcessorStatus.FAILED
            result.message = "Conversion timed out (180s)"
            self._set_error(result.message)
            
        except Exception as e:
            result.status = ProcessorStatus.FAILED
            result.message = f"LibreOffice conversion failed: {str(e)}"
            self._set_error(result.message)
            
        finally:
            if show_progress:
                self._close_progress()
            cleanup_single_directory(temp_dir)
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🪟 COM METHOD (Windows)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _process_via_com(
        self,
        file_path: str,
        show_progress: bool = True
    ) -> ProcessorResult:
        """Convert PPT using PowerPoint COM automation (Windows only)"""
        result = ProcessorResult()
        
        if not COMTYPES_AVAILABLE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = "comtypes not installed"
            return result
        
        if sys.platform != 'win32':
            result.status = ProcessorStatus.UNSUPPORTED
            result.message = "COM automation only available on Windows"
            return result
        
        from ..config.dependencies import comtypes, pythoncom
        
        temp_dir = os.path.join(os.path.dirname(file_path), "_temp_slides")
        os.makedirs(temp_dir, exist_ok=True)
        register_temp_directory(temp_dir)
        
        pythoncom.CoInitialize()
        powerpoint = None
        presentation = None
        
        try:
            if show_progress:
                self._show_progress("Opening PowerPoint...", 0, 0)
            
            powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
            powerpoint.Visible = True
            
            presentation = powerpoint.Presentations.Open(
                file_path,
                ReadOnly=True,
                WithWindow=False
            )
            total_slides = presentation.Slides.Count
            
            if show_progress:
                self._update_progress(f"Exporting {total_slides} slides...", 0, total_slides)
            
            for i in range(1, total_slides + 1):
                try:
                    if show_progress:
                        self._update_progress(None, i, total_slides)
                        QApplication.processEvents()
                    
                    slide = presentation.Slides(i)
                    temp_path = os.path.join(temp_dir, f"slide_{i}.png")
                    slide.Export(temp_path, "PNG", 1920, 1080)
                    
                    pixmap = QPixmap(temp_path)
                    
                    if not pixmap.isNull():
                        thumbnail = self.generate_thumbnail(pixmap)
                        path_with_slide = f"{file_path}#slide{i}"
                        
                        result.add_slide(
                            pixmap=pixmap,
                            file_path=path_with_slide,
                            info=f"Slide {i} of {total_slides}",
                            thumbnail=thumbnail
                        )
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                        
                except Exception as e:
                    self._log(f"⚠️ Error exporting slide {i}: {e}")
            
            if show_progress:
                self._close_progress()
            
            if result.has_slides:
                result.status = ProcessorStatus.SUCCESS
                result.message = f"Loaded {result.total_pages} slides via PowerPoint"
                self._log(f"✅ {result.message}")
            else:
                result.status = ProcessorStatus.FAILED
                result.message = "No slides could be exported"
            
        except Exception as e:
            result.status = ProcessorStatus.FAILED
            result.message = f"COM automation failed: {str(e)}"
            self._set_error(result.message)
            
        finally:
            if show_progress:
                self._close_progress()
            
            try:
                if presentation:
                    presentation.Close()
                if powerpoint:
                    powerpoint.Quit()
            except:
                pass
            
            pythoncom.CoUninitialize()
            cleanup_single_directory(temp_dir)
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         🐍 PYTHON-PPTX METHOD
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _process_via_pptx(
        self,
        file_path: str,
        show_progress: bool = True
    ) -> ProcessorResult:
        """Render PPTX using python-pptx (limited quality)"""
        result = ProcessorResult()
        
        if not PPTX_AVAILABLE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = "python-pptx not installed"
            return result
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext != '.pptx':
            result.status = ProcessorStatus.UNSUPPORTED
            result.message = "python-pptx only supports .pptx files"
            return result
        
        try:
            if show_progress:
                self._show_progress("Loading PPTX...", 0, 0)
            
            prs = PPTXPresentation(file_path)
            total_slides = len(prs.slides)
            
            # Calculate dimensions
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
            
            if show_progress:
                self._update_progress(f"Rendering {total_slides} slides...", 0, total_slides)
            
            for idx, slide in enumerate(prs.slides):
                try:
                    if show_progress:
                        self._update_progress(None, idx + 1, total_slides)
                        QApplication.processEvents()
                    
                    pixmap = self._render_pptx_slide(
                        slide, px_width, px_height, idx + 1, total_slides
                    )
                    
                    if pixmap and not pixmap.isNull():
                        thumbnail = self.generate_thumbnail(pixmap)
                        path_with_slide = f"{file_path}#slide{idx + 1}"
                        
                        result.add_slide(
                            pixmap=pixmap,
                            file_path=path_with_slide,
                            info=f"Slide {idx + 1} of {total_slides}",
                            thumbnail=thumbnail
                        )
                        
                except Exception as e:
                    self._log(f"⚠️ Error rendering slide {idx + 1}: {e}")
            
            if show_progress:
                self._close_progress()
            
            if result.has_slides:
                result.status = ProcessorStatus.SUCCESS
                result.message = f"Loaded {result.total_pages} slides (basic rendering)"
                self._log(f"✅ {result.message}")
            else:
                result.status = ProcessorStatus.FAILED
                result.message = "No slides could be rendered"
            
        except Exception as e:
            result.status = ProcessorStatus.FAILED
            result.message = f"python-pptx rendering failed: {str(e)}"
            self._set_error(result.message)
            
        finally:
            if show_progress:
                self._close_progress()
        
        return result
    
    def _render_pptx_slide(
        self,
        slide,
        width: int,
        height: int,
        slide_num: int,
        total: int
    ) -> QPixmap:
        """Render a PPTX slide to QPixmap"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(255, 255, 255))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        try:
            # Draw grid
            pen = QPen(QColor(245, 245, 245))
            painter.setPen(pen)
            for x in range(0, width, 50):
                painter.drawLine(x, 0, x, height)
            for y in range(0, height, 50):
                painter.drawLine(0, y, width, y)
            
            # Draw shapes
            for shape in slide.shapes:
                try:
                    self._draw_pptx_shape(painter, shape, width, height)
                except:
                    pass
            
            # Draw slide number
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
    
    def _draw_pptx_shape(
        self,
        painter: QPainter,
        shape,
        slide_w: int,
        slide_h: int
    ):
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
                    painter.drawText(
                        text_rect,
                        align | Qt.AlignTop | Qt.TextWordWrap,
                        full_text
                    )
                    
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
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📊 PROGRESS DIALOG
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_progress(self, text: str, value: int, maximum: int):
        """Show progress dialog"""
        try:
            self._progress_dialog = QProgressDialog(text, None, value, maximum)
            self._progress_dialog.setWindowTitle("⬡ Processing")
            self._progress_dialog.setWindowModality(Qt.WindowModal)
            self._progress_dialog.setMinimumDuration(0)
            self._progress_dialog.setValue(value)
            self._progress_dialog.show()
            QApplication.processEvents()
        except:
            pass
    
    def _update_progress(self, text: Optional[str], value: int, maximum: int):
        """Update progress dialog"""
        try:
            if self._progress_dialog:
                if text:
                    self._progress_dialog.setLabelText(text)
                self._progress_dialog.setMaximum(maximum)
                self._progress_dialog.setValue(value)
        except:
            pass
    
    def _close_progress(self):
        """Close progress dialog"""
        try:
            if self._progress_dialog:
                self._progress_dialog.close()
                self._progress_dialog = None
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    #                         📋 HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _get_install_help(self) -> str:
        """Get installation help message"""
        methods = []
        
        if not LIBREOFFICE_AVAILABLE:
            methods.append("① Install LibreOffice (FREE):\n   https://www.libreoffice.org/download/")
        
        if not PDF_AVAILABLE:
            methods.append("② Install PyMuPDF:\n   pip install PyMuPDF")
        
        if not PPTX_AVAILABLE:
            methods.append("③ Install python-pptx:\n   pip install python-pptx")
        
        if sys.platform == 'win32' and not COMTYPES_AVAILABLE:
            methods.append("④ Install comtypes (Windows):\n   pip install comtypes")
        
        methods.append("⑤ Export as PDF from PowerPoint")
        
        return "\n\n".join(methods)
    
    def get_slide_count(self, file_path: str) -> int:
        """
        Get slide count without fully processing.
        
        Args:
            file_path: Path to PPT/PPTX file
            
        Returns:
            Number of slides, or -1 on error
        """
        if not PPTX_AVAILABLE:
            return -1
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext != '.pptx':
            return -1
        
        try:
            prs = PPTXPresentation(file_path)
            return len(prs.slides)
        except:
            return -1
    
    @staticmethod
    def is_ppt_file(file_path: str) -> bool:
        """
        Check if a file is a PowerPoint file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is PPT/PPTX
        """
        if not file_path:
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.ppt', '.pptx']
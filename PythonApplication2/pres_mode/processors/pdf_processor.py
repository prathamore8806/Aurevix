"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📄 PDF PROCESSOR                                     ║
║                    Handle PDF Documents with PyMuPDF                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from typing import List, Optional

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from .base import BaseProcessor, ProcessorResult, ProcessorStatus
from ..config.dependencies import PDF_AVAILABLE, fitz


class PDFProcessor(BaseProcessor):
    """
    Processor for PDF documents using PyMuPDF (fitz).
    
    Features:
    - Convert PDF pages to high-quality images
    - Configurable DPI/scale
    - Page range selection
    - Memory-safe image handling
    
    Requirements:
    - PyMuPDF: pip install PyMuPDF
    
    Usage:
        processor = PDFProcessor()
        result = processor.process("document.pdf")
        
        if result.is_success:
            for slide in result.slides:
                display(slide)
    """
    
    supported_extensions: List[str] = ['.pdf']
    processor_name: str = "PDF"
    
    # Default rendering settings
    DEFAULT_SCALE = 2.5  # Render at 2.5x for high quality
    DEFAULT_DPI = 150
    
    def __init__(self, scale: float = None, dpi: int = None):
        """
        Initialize PDF processor.
        
        Args:
            scale: Render scale factor (default: 2.5)
            dpi: Alternative DPI setting (overrides scale if provided)
        """
        super().__init__()
        
        self.scale = scale or self.DEFAULT_SCALE
        self.dpi = dpi
        
        # Calculate scale from DPI if provided
        if dpi:
            self.scale = dpi / 72.0  # PDF base is 72 DPI
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if PyMuPDF is available"""
        return PDF_AVAILABLE
    
    def process(
        self,
        file_path: str,
        page_range: Optional[tuple] = None,
        scale: Optional[float] = None
    ) -> ProcessorResult:
        """
        Process a PDF file.
        
        Args:
            file_path: Path to the PDF file
            page_range: Optional (start, end) tuple for page range (1-indexed)
            scale: Optional scale override
            
        Returns:
            ProcessorResult with slides for each page
        """
        result = ProcessorResult()
        
        # Check availability
        if not PDF_AVAILABLE:
            result.status = ProcessorStatus.DEPENDENCY_MISSING
            result.message = "PyMuPDF not installed. Run: pip install PyMuPDF"
            self._set_error(result.message)
            return result
        
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
        
        # Use provided scale or default
        render_scale = scale or self.scale
        
        doc = None
        try:
            self._log(f"Opening PDF: {os.path.basename(file_path)}")
            
            # Open document
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            if total_pages == 0:
                result.status = ProcessorStatus.FAILED
                result.message = "PDF has no pages"
                self._set_error(result.message)
                return result
            
            self._log(f"Total pages: {total_pages}")
            
            # Determine page range
            start_page = 0
            end_page = total_pages
            
            if page_range:
                start_page = max(0, page_range[0] - 1)  # Convert to 0-indexed
                end_page = min(total_pages, page_range[1])
            
            # Create transformation matrix
            mat = fitz.Matrix(render_scale, render_scale)
            
            # Process each page
            success_count = 0
            fail_count = 0
            
            for page_num in range(start_page, end_page):
                try:
                    page = doc[page_num]
                    
                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to QImage (COPY data to prevent memory issues)
                    img = QImage(
                        pix.samples,
                        pix.width,
                        pix.height,
                        pix.stride,
                        QImage.Format_RGB888
                    ).copy()  # IMPORTANT: Copy to own the data
                    
                    # Convert to QPixmap
                    pixmap = QPixmap.fromImage(img)
                    
                    if not pixmap.isNull():
                        # Generate thumbnail
                        thumbnail = self.generate_thumbnail(pixmap)
                        
                        # Create file path with page info
                        path_with_page = f"{file_path}#page{page_num + 1}"
                        
                        # Add to result
                        result.add_slide(
                            pixmap=pixmap,
                            file_path=path_with_page,
                            info=f"Page {page_num + 1} of {total_pages}",
                            thumbnail=thumbnail
                        )
                        
                        success_count += 1
                    else:
                        fail_count += 1
                        self._log(f"⚠️ Failed to render page {page_num + 1}")
                        
                except Exception as e:
                    fail_count += 1
                    self._log(f"⚠️ Error on page {page_num + 1}: {e}")
            
            # Set final status
            if success_count == 0:
                result.status = ProcessorStatus.FAILED
                result.message = f"Failed to render any pages from PDF"
            elif fail_count > 0:
                result.status = ProcessorStatus.PARTIAL
                result.message = f"Loaded {success_count} pages, {fail_count} failed"
            else:
                result.status = ProcessorStatus.SUCCESS
                result.message = f"Loaded {success_count} pages from PDF"
            
            self._log(f"✅ {result.message}")
            
        except Exception as e:
            result.status = ProcessorStatus.FAILED
            result.message = f"Error processing PDF: {str(e)}"
            self._set_error(result.message)
            
        finally:
            # Always close the document
            if doc:
                try:
                    doc.close()
                except:
                    pass
        
        return result
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get the number of pages in a PDF without fully processing it.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Number of pages, or -1 on error
        """
        if not PDF_AVAILABLE:
            return -1
        
        if not os.path.exists(file_path):
            return -1
        
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return -1
    
    def get_pdf_info(self, file_path: str) -> dict:
        """
        Get information about a PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict with PDF information
        """
        info = self.get_file_info(file_path)
        
        if not PDF_AVAILABLE:
            info["error"] = "PyMuPDF not installed"
            return info
        
        if info.get("error"):
            return info
        
        try:
            doc = fitz.open(file_path)
            
            info["page_count"] = len(doc)
            info["metadata"] = doc.metadata
            info["is_encrypted"] = doc.is_encrypted
            info["is_pdf"] = doc.is_pdf
            
            # Get first page dimensions
            if len(doc) > 0:
                page = doc[0]
                rect = page.rect
                info["page_width"] = rect.width
                info["page_height"] = rect.height
                info["page_size"] = f"{rect.width:.0f}x{rect.height:.0f}"
            
            doc.close()
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def extract_page(
        self,
        file_path: str,
        page_number: int,
        scale: Optional[float] = None
    ) -> Optional[QPixmap]:
        """
        Extract a single page from a PDF.
        
        Args:
            file_path: Path to PDF file
            page_number: Page number (1-indexed)
            scale: Optional scale override
            
        Returns:
            QPixmap of the page, or None on error
        """
        if not PDF_AVAILABLE:
            return None
        
        if not os.path.exists(file_path):
            return None
        
        render_scale = scale or self.scale
        
        try:
            doc = fitz.open(file_path)
            
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return None
            
            page = doc[page_number - 1]
            mat = fitz.Matrix(render_scale, render_scale)
            pix = page.get_pixmap(matrix=mat)
            
            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format_RGB888
            ).copy()
            
            pixmap = QPixmap.fromImage(img)
            
            doc.close()
            
            return pixmap if not pixmap.isNull() else None
            
        except:
            return None
    
    def set_quality(self, quality: str):
        """
        Set rendering quality preset.
        
        Args:
            quality: "low", "medium", "high", or "ultra"
        """
        presets = {
            "low": 1.0,
            "medium": 1.5,
            "high": 2.5,
            "ultra": 4.0
        }
        
        self.scale = presets.get(quality.lower(), self.DEFAULT_SCALE)
        self._log(f"Quality set to {quality} (scale: {self.scale})")
    
    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        """
        Check if a file is a PDF.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is a PDF
        """
        if not file_path:
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext == '.pdf'
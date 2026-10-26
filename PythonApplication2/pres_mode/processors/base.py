"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         📦 BASE PROCESSOR                                    ║
║                    Foundation for All File Processors                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from PySide6.QtGui import QPixmap


class ProcessorStatus(Enum):
    """Status of processing operation"""
    SUCCESS = auto()
    PARTIAL = auto()
    FAILED = auto()
    UNSUPPORTED = auto()
    DEPENDENCY_MISSING = auto()


@dataclass
class ProcessorResult:
    """
    Result of a file processing operation.
    
    Attributes:
        status: Processing status
        slides: List of QPixmap slides
        file_paths: List of file paths with page/slide info
        slide_info: List of slide info strings
        thumbnails: List of thumbnail QPixmaps
        message: Status/error message
        total_pages: Total number of pages/slides processed
    """
    status: ProcessorStatus = ProcessorStatus.SUCCESS
    slides: List[QPixmap] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    slide_info: List[str] = field(default_factory=list)
    thumbnails: List[QPixmap] = field(default_factory=list)
    message: str = ""
    total_pages: int = 0
    
    @property
    def is_success(self) -> bool:
        """Check if processing was successful"""
        return self.status in [ProcessorStatus.SUCCESS, ProcessorStatus.PARTIAL]
    
    @property
    def has_slides(self) -> bool:
        """Check if any slides were produced"""
        return len(self.slides) > 0
    
    def add_slide(
        self,
        pixmap: QPixmap,
        file_path: str,
        info: str = "",
        thumbnail: Optional[QPixmap] = None
    ):
        """
        Add a slide to the result.
        
        Args:
            pixmap: Slide pixmap
            file_path: File path with page/slide info
            info: Slide info string
            thumbnail: Optional thumbnail (auto-generated if None)
        """
        if pixmap and not pixmap.isNull():
            self.slides.append(pixmap)
            self.file_paths.append(file_path)
            self.slide_info.append(info)
            
            if thumbnail and not thumbnail.isNull():
                self.thumbnails.append(thumbnail)
            else:
                # Auto-generate thumbnail
                thumb = pixmap.scaled(72, 47, aspectMode=1, mode=1)  # KeepAspectRatio, SmoothTransformation
                self.thumbnails.append(thumb)
            
            self.total_pages = len(self.slides)


class BaseProcessor:
    """
    Base class for all file processors.
    
    Subclasses should implement:
    - supported_extensions: List of supported file extensions
    - process(): Main processing method
    - is_available(): Check if dependencies are available
    
    Usage:
        class MyProcessor(BaseProcessor):
            supported_extensions = ['.xyz']
            
            def process(self, file_path):
                result = ProcessorResult()
                # Process file...
                return result
    """
    
    # Override in subclasses
    supported_extensions: List[str] = []
    processor_name: str = "Base"
    
    def __init__(self):
        self._last_error: Optional[str] = None
    
    @classmethod
    def can_process(cls, file_path: str) -> bool:
        """
        Check if this processor can handle the given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file extension is supported
        """
        if not file_path:
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.supported_extensions
    
    @classmethod
    def is_available(cls) -> bool:
        """
        Check if required dependencies are available.
        Override in subclasses.
        
        Returns:
            True if processor can be used
        """
        return True
    
    def process(self, file_path: str) -> ProcessorResult:
        """
        Process a file and return slides.
        Override in subclasses.
        
        Args:
            file_path: Path to the file
            
        Returns:
            ProcessorResult with slides and metadata
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file without fully processing it.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict with file information
        """
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "size": stat.st_size,
            "size_str": self._format_size(stat.st_size),
            "exists": True
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size as human-readable string"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @staticmethod
    def generate_thumbnail(pixmap: QPixmap, width: int = 72, height: int = 47) -> QPixmap:
        """
        Generate a thumbnail from a pixmap.
        
        Args:
            pixmap: Source pixmap
            width: Thumbnail width
            height: Thumbnail height
            
        Returns:
            Scaled thumbnail pixmap
        """
        if pixmap and not pixmap.isNull():
            from PySide6.QtCore import Qt
            return pixmap.scaled(
                width, height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        return QPixmap()
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    def _set_error(self, message: str):
        """Set error message"""
        self._last_error = message
        print(f"❌ [{self.processor_name}] {message}")
    
    def _log(self, message: str):
        """Log a message"""
        print(f"📄 [{self.processor_name}] {message}")


def get_processor_for_file(file_path: str) -> Optional[BaseProcessor]:
    """
    Get the appropriate processor for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Processor instance or None if unsupported
    """
    from .image_processor import ImageProcessor
    from .pdf_processor import PDFProcessor
    from .ppt_processor import PPTProcessor
    
    processors = [
        ImageProcessor,
        PDFProcessor,
        PPTProcessor
    ]
    
    for processor_class in processors:
        if processor_class.can_process(file_path):
            if processor_class.is_available():
                return processor_class()
            else:
                print(f"⚠️ {processor_class.processor_name} not available (missing dependencies)")
    
    return None


def process_file(file_path: str) -> ProcessorResult:
    """
    Process a file using the appropriate processor.
    
    Args:
        file_path: Path to the file
        
    Returns:
        ProcessorResult with slides or error status
    """
    processor = get_processor_for_file(file_path)
    
    if processor is None:
        ext = os.path.splitext(file_path)[1].lower()
        return ProcessorResult(
            status=ProcessorStatus.UNSUPPORTED,
            message=f"Unsupported file type: {ext}"
        )
    
    return processor.process(file_path)
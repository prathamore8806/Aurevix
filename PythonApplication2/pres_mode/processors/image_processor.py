"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🖼️ IMAGE PROCESSOR                                   ║
║                    Handle Image Files (PNG, JPG, BMP, GIF)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from typing import List

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from .base import BaseProcessor, ProcessorResult, ProcessorStatus


class ImageProcessor(BaseProcessor):
    """
    Processor for image files.
    
    Supported formats:
    - PNG
    - JPG/JPEG
    - BMP
    - GIF (first frame only)
    - WEBP
    - TIFF
    
    Usage:
        processor = ImageProcessor()
        result = processor.process("image.png")
        
        if result.is_success:
            pixmap = result.slides[0]
    """
    
    supported_extensions: List[str] = [
        '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'
    ]
    processor_name: str = "Image"
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def is_available(cls) -> bool:
        """Images are always supported via Qt"""
        return True
    
    def process(self, file_path: str) -> ProcessorResult:
        """
        Process an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            ProcessorResult with single slide
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
        
        # Check extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            result.status = ProcessorStatus.UNSUPPORTED
            result.message = f"Unsupported image format: {ext}"
            self._set_error(result.message)
            return result
        
        try:
            self._log(f"Loading image: {os.path.basename(file_path)}")
            
            # Load image
            pixmap = QPixmap(file_path)
            
            if pixmap.isNull():
                result.status = ProcessorStatus.FAILED
                result.message = f"Failed to load image: {file_path}"
                self._set_error(result.message)
                return result
            
            # Generate thumbnail
            thumbnail = self.generate_thumbnail(pixmap)
            
            # Add to result
            result.add_slide(
                pixmap=pixmap,
                file_path=file_path,
                info="IMAGE",
                thumbnail=thumbnail
            )
            
            result.status = ProcessorStatus.SUCCESS
            result.message = f"Loaded image: {os.path.basename(file_path)}"
            
            self._log(f"✅ Loaded: {pixmap.width()}x{pixmap.height()}")
            
        except Exception as e:
            result.status = ProcessorStatus.FAILED
            result.message = f"Error loading image: {str(e)}"
            self._set_error(result.message)
        
        return result
    
    def process_multiple(self, file_paths: List[str]) -> ProcessorResult:
        """
        Process multiple image files.
        
        Args:
            file_paths: List of image file paths
            
        Returns:
            ProcessorResult with all slides
        """
        result = ProcessorResult()
        
        if not file_paths:
            result.status = ProcessorStatus.FAILED
            result.message = "No files provided"
            return result
        
        success_count = 0
        fail_count = 0
        
        for file_path in file_paths:
            single_result = self.process(file_path)
            
            if single_result.is_success:
                # Copy slides to combined result
                for i in range(len(single_result.slides)):
                    result.add_slide(
                        pixmap=single_result.slides[i],
                        file_path=single_result.file_paths[i],
                        info=single_result.slide_info[i],
                        thumbnail=single_result.thumbnails[i] if i < len(single_result.thumbnails) else None
                    )
                success_count += 1
            else:
                fail_count += 1
        
        # Set final status
        if success_count == 0:
            result.status = ProcessorStatus.FAILED
            result.message = f"Failed to load any images ({fail_count} failed)"
        elif fail_count > 0:
            result.status = ProcessorStatus.PARTIAL
            result.message = f"Loaded {success_count} images, {fail_count} failed"
        else:
            result.status = ProcessorStatus.SUCCESS
            result.message = f"Loaded {success_count} images"
        
        return result
    
    def get_image_info(self, file_path: str) -> dict:
        """
        Get information about an image without fully loading it.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dict with image information
        """
        info = self.get_file_info(file_path)
        
        if info.get("error"):
            return info
        
        try:
            # Load image to get dimensions
            pixmap = QPixmap(file_path)
            
            if not pixmap.isNull():
                info["width"] = pixmap.width()
                info["height"] = pixmap.height()
                info["aspect_ratio"] = pixmap.width() / pixmap.height() if pixmap.height() > 0 else 0
                info["dimensions"] = f"{pixmap.width()}x{pixmap.height()}"
            else:
                info["error"] = "Could not read image dimensions"
                
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """
        Check if a file is a supported image.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is a supported image
        """
        if not file_path:
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ImageProcessor.supported_extensions
"""
Processors module for Presentation Mode.
Contains file format processors for images, PDFs, and PowerPoint files.
"""

from .base import BaseProcessor, ProcessorResult
from .image_processor import ImageProcessor
from .pdf_processor import PDFProcessor
from .ppt_processor import PPTProcessor

__all__ = [
    "BaseProcessor",
    "ProcessorResult",
    "ImageProcessor",
    "PDFProcessor",
    "PPTProcessor"
]
"""
Configuration module for Presentation Mode.
Contains color schemes and dependency checks.
"""

from .colors import FuturisticColors
from .dependencies import (
    PDF_AVAILABLE,
    PPTX_AVAILABLE,
    COMTYPES_AVAILABLE,
    LIBREOFFICE_AVAILABLE,
    LIBREOFFICE_PATH,
    PP_ALIGN,
    fitz,
    PPTXPresentation,
    Inches,
    Pt,
    Emu,
    MSO_SHAPE_TYPE,
    comtypes,
    pythoncom
)

__all__ = [
    "FuturisticColors",
    "PDF_AVAILABLE",
    "PPTX_AVAILABLE",
    "COMTYPES_AVAILABLE",
    "LIBREOFFICE_AVAILABLE",
    "LIBREOFFICE_PATH",
    "PP_ALIGN",
    "fitz",
    "PPTXPresentation",
    "Inches",
    "Pt",
    "Emu",
    "MSO_SHAPE_TYPE",
    "comtypes",
    "pythoncom"
]
"""
Utility module for Presentation Mode.
Contains helper functions and cleanup utilities.
"""

from .cleanup import (
    temp_directories,
    register_temp_directory,
    cleanup_temp_directories
)

from .libreoffice import (
    find_libreoffice,
    convert_to_pdf
)

__all__ = [
    # Cleanup utilities
    "temp_directories",
    "register_temp_directory",
    "cleanup_temp_directories",
    
    # LibreOffice utilities
    "find_libreoffice",
    "convert_to_pdf"
]
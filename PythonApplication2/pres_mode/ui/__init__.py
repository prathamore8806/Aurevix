"""
UI module for Presentation Mode.
Contains all user interface components including widgets, dialogs, and viewer.
"""

# Widgets
from .widgets.buttons import FuturisticButton
from .widgets.cards import FuturisticCard
from .widgets.decorations import HexagonDecor, ScanLineOverlay
from .widgets.file_item import FuturisticFileItem
from .widgets.indicators import GestureIndicator

# Dialogs
from .dialogs.presentation_dialog import PresentationDialog

# Viewer
from .viewer.presentation_viewer import PresentationViewer

__all__ = [
    # Widgets
    "FuturisticButton",
    "FuturisticCard",
    "HexagonDecor",
    "ScanLineOverlay",
    "FuturisticFileItem",
    "GestureIndicator",
    
    # Dialogs
    "PresentationDialog",
    
    # Viewer
    "PresentationViewer"
]
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⬡ PRESENTATION MODE MODULE V5.1 ⬡                         ║
║              Futuristic Navy Blue Design • Cyberpunk Aesthetic               ║
║                    ✅ FIXED: Swipe Gestures Now Working                      ║
║                    ✅ NEW: Fist Gesture = Lock Zoom                          ║
║                    ✅ FIXED: Logarithmic Zoom Scaling                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

__version__ = "5.1"
__author__ = "Presentation Mode"

# Main exports for easy importing
from .config.colors import FuturisticColors
from .config.dependencies import (
    PDF_AVAILABLE,
    PPTX_AVAILABLE,
    COMTYPES_AVAILABLE,
    LIBREOFFICE_AVAILABLE,
    LIBREOFFICE_PATH
)

from .core.zoom_controller import SmoothZoomController, ZoomLockState
from .core.swipe_detector import SwipeDetector, SwipeState

from .ui.widgets.buttons import FuturisticButton
from .ui.widgets.cards import FuturisticCard
from .ui.widgets.decorations import HexagonDecor, ScanLineOverlay
from .ui.widgets.file_item import FuturisticFileItem
from .ui.widgets.indicators import GestureIndicator

from .ui.dialogs.presentation_dialog import PresentationDialog
from .ui.viewer.presentation_viewer import PresentationViewer

from .gestures.integration import GestureIntegration
from .gestures.simulator import GestureSimulator

__all__ = [
    # Config
    "FuturisticColors",
    "PDF_AVAILABLE",
    "PPTX_AVAILABLE", 
    "COMTYPES_AVAILABLE",
    "LIBREOFFICE_AVAILABLE",
    "LIBREOFFICE_PATH",
    
    # Core
    "SmoothZoomController",
    "ZoomLockState",
    "SwipeDetector",
    "SwipeState",
    
    # UI Widgets
    "FuturisticButton",
    "FuturisticCard",
    "HexagonDecor",
    "ScanLineOverlay",
    "FuturisticFileItem",
    "GestureIndicator",
    
    # UI Main
    "PresentationDialog",
    "PresentationViewer",
    
    # Gestures
    "GestureIntegration",
    "GestureSimulator",
]
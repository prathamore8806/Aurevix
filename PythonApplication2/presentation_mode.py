"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⬡ PRESENTATION MODE MODULE V5.1 ⬡                         ║
║              Futuristic Navy Blue Design • Cyberpunk Aesthetic               ║
║                    ✅ FIXED: Swipe Gestures Now Working                      ║
║                    ✅ NEW: Fist Gesture = Lock Zoom                          ║
║                    ✅ FIXED: Logarithmic Zoom Scaling                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

MAIN ENTRY POINT - Run this file to start the presentation mode.

Usage:
    python presentation_mode.py
    
Or import in your project:
    from presentation_mode import PresentationDialog, PresentationViewer
"""

import sys
import os
from typing import Optional, List

# ═══════════════════════════════════════════════════════════════════════════════
#                         🔧 PATH SETUP
# ═══════════════════════════════════════════════════════════════════════════════

# Ensure the script directory is in path
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 IMPORTS FROM SUBMODULES
# ═══════════════════════════════════════════════════════════════════════════════

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import QTimer

# Config - Import from package 'pres_mode'
from pres_mode.config.colors import FuturisticColors
from pres_mode.config.dependencies import (
    PDF_AVAILABLE,
    PPTX_AVAILABLE,
    COMTYPES_AVAILABLE,
    LIBREOFFICE_AVAILABLE,
    LIBREOFFICE_PATH
)

# Core
from pres_mode.core.zoom_controller import SmoothZoomController, ZoomLockState
from pres_mode.core.swipe_detector import SwipeDetector, SwipeState

# UI Widgets
from pres_mode.ui.widgets.buttons import FuturisticButton
from pres_mode.ui.widgets.cards import FuturisticCard
from pres_mode.ui.widgets.decorations import HexagonDecor, ScanLineOverlay
from pres_mode.ui.widgets.file_item import FuturisticFileItem
from pres_mode.ui.widgets.indicators import GestureIndicator

# UI Dialogs & Viewer
from pres_mode.ui.dialogs.presentation_dialog import PresentationDialog
from pres_mode.ui.viewer.presentation_viewer import PresentationViewer

# Gestures
from pres_mode.gestures.integration import GestureIntegration
from pres_mode.gestures.simulator import GestureSimulator

# Processors
from pres_mode.processors.base import (
    BaseProcessor,
    ProcessorResult,
    ProcessorStatus,
    get_processor_for_file,
    process_file
)
from pres_mode.processors.image_processor import ImageProcessor
from pres_mode.processors.pdf_processor import PDFProcessor
from pres_mode.processors.ppt_processor import PPTProcessor, ConversionMethod


# ═══════════════════════════════════════════════════════════════════════════════
#                         📋 PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

__version__ = "5.1"
__author__ = "Presentation Mode"

__all__ = [
    # Version
    "__version__",
    
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
    
    # Processors
    "BaseProcessor",
    "ProcessorResult",
    "ProcessorStatus",
    "ImageProcessor",
    "PDFProcessor",
    "PPTProcessor",
    "ConversionMethod",
    "get_processor_for_file",
    "process_file",
    
    # Main function
    "main",
    "run_presentation",
]


# ═══════════════════════════════════════════════════════════════════════════════
#                         🖨️ BANNER
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("⬡ PRESENTATION MODULE V5.1 - SWIPE + FIST ZOOM LOCK")
    print("=" * 70)
    print("\n📋 FEATURES:")
    print("  👋 SWIPE GESTURES:")
    print("     • Swipe hand RIGHT → Next slide")
    print("     • Swipe hand LEFT  → Previous slide")
    print("")
    print("  ✊ FIST = LOCK/UNLOCK ZOOM:")
    print("     • Make a fist to LOCK zoom at current level")
    print("     • Make a fist again to UNLOCK")
    print("     • Locked zoom persists across slide changes")
    print("")
    print("  🔍 IMPROVED ZOOM:")
    print("     • Logarithmic scaling for natural feel")
    print("     • Reduced sensitivity")
    print("     • Visual lock indicator in UI")
    print("")
    print("📦 DEPENDENCIES:")
    print(f"  {'✅' if PDF_AVAILABLE else '❌'} PDF: PyMuPDF")
    print(f"  {'✅' if LIBREOFFICE_AVAILABLE else '❌'} LibreOffice: PPT conversion")
    print(f"  {'✅' if PPTX_AVAILABLE else '❌'} python-pptx: PPTX support")
    print(f"  {'✅' if COMTYPES_AVAILABLE else '❌'} comtypes: Windows COM support")
    print("\n")


# ═══════════════════════════════════════════════════════════════════════════════
#                         🚀 MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def run_presentation(slides: List[QPixmap], run_demo: bool = False) -> PresentationViewer:
    """
    Create and show a presentation viewer with the given slides.
    
    Args:
        slides: List of QPixmap slides to display
        run_demo: Whether to run gesture demo sequence
        
    Returns:
        PresentationViewer instance
    """
    viewer = PresentationViewer(slides)
    
    # Create gesture integration
    integration = GestureIntegration(viewer)
    
    # Store references on viewer for access
    viewer._gesture_integration = integration
    
    if run_demo:
        # Create simulator and run demo
        simulator = GestureSimulator(integration)
        viewer._gesture_simulator = simulator
        
        # Run demo after viewer is shown
        QTimer.singleShot(1000, simulator.run_demo_sequence)
    
    viewer.showFullScreen()
    return viewer


def main():
    """Main entry point for presentation mode"""
    print_banner()
    
    app = QApplication(sys.argv)
    
    # Set default font
    font = QFont("Consolas", 10)
    app.setFont(font)
    
    # Global references
    viewer: Optional[PresentationViewer] = None
    gesture_integration: Optional[GestureIntegration] = None
    gesture_simulator: Optional[GestureSimulator] = None
    
    # Create and show dialog
    dialog = PresentationDialog()
    
    def on_presentation_started(slides: List[QPixmap]):
        nonlocal viewer, gesture_integration, gesture_simulator
        
        print(f"\n▶ Presentation launched with {len(slides)} slides")
        print("=" * 50)
        
        # Create viewer
        viewer = PresentationViewer(slides)
        
        # Create gesture integration
        gesture_integration = GestureIntegration(viewer)
        
        # Create simulator for testing
        gesture_simulator = GestureSimulator(gesture_integration)
        
        def on_viewer_closed():
            nonlocal viewer, gesture_integration, gesture_simulator
            print("\n✅ Viewer closed")
            
            if gesture_simulator:
                gesture_simulator.stop()
                gesture_simulator = None
            
            if gesture_integration:
                gesture_integration.disconnect_from_viewer()
                gesture_integration = None
            
            viewer = None
        
        viewer.closed.connect(on_viewer_closed)
        viewer.showFullScreen()
        
        # ═══════════════════════════════════════════════════════════════════
        # DEMO: Run gesture simulations
        # ═══════════════════════════════════════════════════════════════════
        
        print("\n🎮 DEMO SEQUENCE:")
        print("   2s  → Swipe RIGHT (next slide)")
        print("   4s  → Swipe LEFT (previous slide)")
        print("   6s  → FIST (lock zoom)")
        print("   8s  → Pinch zoom in (blocked - locked)")
        print("   10s → FIST (unlock zoom)")
        print("   12s → Pinch zoom in (working)")
        print("   14s → Pinch zoom out")
        print("")
        
        # Schedule demo gestures
        QTimer.singleShot(2000, gesture_simulator.simulate_swipe_right)
        QTimer.singleShot(4000, gesture_simulator.simulate_swipe_left)
        QTimer.singleShot(6000, gesture_simulator.simulate_fist)  # Lock
        QTimer.singleShot(8000, gesture_simulator.simulate_pinch_zoom_in)  # Blocked
        QTimer.singleShot(10000, gesture_simulator.simulate_fist)  # Unlock
        QTimer.singleShot(12000, gesture_simulator.simulate_pinch_zoom_in)  # Works
        QTimer.singleShot(14000, gesture_simulator.simulate_pinch_zoom_out)
    
    dialog.presentation_started.connect(on_presentation_started)
    dialog.show()
    
    print("\n💡 TIP: Load some images/PDFs and click 'LAUNCH PRESENTATION'")
    print("        to see the demo gestures in action!\n")
    
    sys.exit(app.exec())


# ═══════════════════════════════════════════════════════════════════════════════
#                         🎯 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
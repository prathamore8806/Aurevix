"""
Core module for Presentation Mode.
Contains business logic for zoom control and swipe detection.
"""

from .zoom_controller import SmoothZoomController, ZoomLockState
from .swipe_detector import SwipeDetector, SwipeState

__all__ = [
    # Zoom Controller
    "SmoothZoomController",
    "ZoomLockState",
    
    # Swipe Detector
    "SwipeDetector",
    "SwipeState"
]
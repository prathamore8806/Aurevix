"""
Hand Tracking Package
"""

from .tracker import (
    run_tracker,
    set_camera_state,
    get_camera_state,
    set_gesture_state,
    get_gesture_state,
    set_gui,
    stop_tracker,
    reset_states,
    get_last_index_pos,
    reload_custom_gestures,
    update_gesture_settings,
)

__version__ = "3.2.0"

__all__ = [
    'run_tracker',
    'set_camera_state',
    'get_camera_state',
    'set_gesture_state',
    'get_gesture_state',
    'set_gui',
    'stop_tracker',
    'reset_states',
    'get_last_index_pos',
    'reload_custom_gestures',
    'update_gesture_settings',
]
"""
Hand Tracker V3.2 - Entry Point
Backward compatible wrapper
"""

from hand_tracking import (
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

if __name__ == "__main__":
    from hand_tracking.core.state import state
    state.camera_enabled = True
    state.gesture_enabled = True
    run_tracker()
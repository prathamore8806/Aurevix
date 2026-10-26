"""
═══════════════════════════════════════════════════════════════════════════════
                            MODE MANAGER
                    Aurevix Gesture Control System
              ✅ ENHANCED FOR GAMING MODE INTEGRATION
              ✅ DESKTOP DOUBLE CLICK TRACKING ADDED
              ✅ CASE-INSENSITIVE MODE HANDLING
═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════════════

mode = "DESKTOP"
hand_detected = False
tracker_running = False

# ✅ Shared frame for dashboard/gaming
shared_frame = None

# ✅ Gesture detection state
current_gesture = None
previous_gesture = None  # For change detection

# ✅ Hand position tracking
hand_position = (0, 0)
normalized_hand_position = (0.5, 0.5)  # Normalized 0-1 range

# ✅ Direction tracking for gaming
current_direction = "NONE"  # UP, DOWN, LEFT, RIGHT, NONE

# ✅ Settings connection
settings_ref = None

# ✅ Gaming page reference
gaming_page_ref = None

# ✅ Desktop page reference (NEW - for double click feedback)
desktop_page_ref = None

# ✅ Gesture cooldown (prevent spam)
_last_gesture_time = 0
_gesture_cooldown = 0.3  # seconds

# ✅ Gaming mode active flag (NEW - for reliable mode tracking)
_gaming_mode_active = False


# ═══════════════════════════════════════════════════════════════════════════════
# MODE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def set_mode(new_mode):
    """Set current application mode (case-insensitive)"""
    global mode, _gaming_mode_active
    
    # ✅ Normalize to uppercase
    new_mode = str(new_mode).upper()
    
    valid = ["DESKTOP", "GAMING", "DRAW", "PRESENTATION"]
    
    if new_mode in valid:
        old_mode = mode
        mode = new_mode
        
        # ✅ Update gaming flag
        _gaming_mode_active = (mode == "GAMING")
        
        print(f"🔄 Mode: {old_mode} → {mode}")
        
        # ✅ Notify gaming page if transitioning
        if old_mode == "GAMING" and mode != "GAMING":
            # Leaving gaming mode
            set_gaming_mode(False)
        elif old_mode != "GAMING" and mode == "GAMING":
            # Entering gaming mode
            set_gaming_mode(True)
    else:
        print(f"⚠️ Invalid mode: {new_mode} (valid: {', '.join(valid)})")


def get_mode():
    """Get current mode (always uppercase)"""
    return mode


def is_gaming_mode():
    """Check if gaming mode is active"""
    return _gaming_mode_active


def is_desktop_mode():
    """Check if desktop mode is active"""
    return mode == "DESKTOP"


def is_draw_mode():
    """Check if draw mode is active"""
    return mode == "DRAW"


def set_gaming_mode(active):
    """
    Explicitly set/unset gaming mode
    Called by gaming_mode.py activate/deactivate
    """
    global _gaming_mode_active, mode
    
    _gaming_mode_active = bool(active)
    
    if active:
        mode = "GAMING"
        print("🎮 Gaming mode ENABLED")
        
        # Notify gaming page
        if gaming_page_ref and hasattr(gaming_page_ref, 'on_mode_activated'):
            try:
                gaming_page_ref.on_mode_activated()
            except Exception as e:
                print(f"⚠️ Gaming page activation error: {e}")
    else:
        # Don't change mode here - let set_mode() handle it
        print("🎮 Gaming mode DISABLED")
        
        # Notify gaming page
        if gaming_page_ref and hasattr(gaming_page_ref, 'on_mode_deactivated'):
            try:
                gaming_page_ref.on_mode_deactivated()
            except Exception as e:
                print(f"⚠️ Gaming page deactivation error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# HAND DETECTION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def set_hand_detected(status):
    """Set hand detection status"""
    global hand_detected
    hand_detected = bool(status)


def is_hand_detected():
    """Check if hand is detected"""
    return hand_detected


def set_tracker_running(status):
    """Set tracker running status"""
    global tracker_running
    tracker_running = bool(status)


def is_tracker_running():
    """Check if tracker is running"""
    return tracker_running


# ═══════════════════════════════════════════════════════════════════════════════
# FRAME MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def set_shared_frame(frame):
    """Update shared frame (called by hand_tracker)"""
    global shared_frame
    shared_frame = frame


def get_shared_frame():
    """Get current shared frame"""
    return shared_frame


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def set_current_gesture(gesture_name):
    """
    Update current gesture (called by hand_tracker)
    Also routes to gaming page if in gaming mode
    """
    global current_gesture, previous_gesture, _last_gesture_time
    import time
    
    # Store previous for change detection
    previous_gesture = current_gesture
    current_gesture = gesture_name
    
    # Route to gaming if active and gesture changed
    if gesture_name and gesture_name != "NONE":
        if gesture_name != previous_gesture:
            # Check cooldown
            current_time = time.time()
            if current_time - _last_gesture_time >= _gesture_cooldown:
                _last_gesture_time = current_time
                
                # Route to gaming page
                if _gaming_mode_active and gaming_page_ref is not None:
                    try:
                        gaming_page_ref.handle_gesture(gesture_name)
                    except Exception as e:
                        print(f"⚠️ Gaming gesture error: {e}")


def get_current_gesture():
    """Get current gesture"""
    return current_gesture


def clear_gesture():
    """Clear current gesture"""
    global current_gesture, previous_gesture
    previous_gesture = current_gesture
    current_gesture = None


# ═══════════════════════════════════════════════════════════════════════════════
# HAND POSITION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def set_hand_position(x, y, frame_width=640, frame_height=480):
    """
    Update hand position (called by hand_tracker)
    Also calculates normalized position and direction
    """
    global hand_position, normalized_hand_position, current_direction
    
    hand_position = (x, y)
    
    # Calculate normalized position (0-1 range)
    norm_x = x / frame_width if frame_width > 0 else 0.5
    norm_y = y / frame_height if frame_height > 0 else 0.5
    
    # Clamp to 0-1
    norm_x = max(0.0, min(1.0, norm_x))
    norm_y = max(0.0, min(1.0, norm_y))
    
    normalized_hand_position = (norm_x, norm_y)
    
    # Calculate direction for gaming
    new_direction = _calculate_direction(norm_x, norm_y)
    
    if new_direction != current_direction:
        current_direction = new_direction
        
        # Route to gaming page
        if _gaming_mode_active and gaming_page_ref is not None:
            try:
                gaming_page_ref.handle_direction(new_direction)
            except Exception as e:
                print(f"⚠️ Gaming direction error: {e}")


def get_hand_position():
    """Get hand position in pixels"""
    return hand_position


def get_normalized_hand_position():
    """Get hand position normalized (0-1)"""
    return normalized_hand_position


def _calculate_direction(norm_x, norm_y, threshold=0.15):
    """
    Calculate direction based on normalized hand position
    Center is 0.5, 0.5
    """
    dx = norm_x - 0.5
    dy = norm_y - 0.5
    
    # Check if movement is significant
    if abs(dx) < threshold and abs(dy) < threshold:
        return "NONE"
    
    # Determine primary direction
    if abs(dx) > abs(dy):
        # Horizontal movement
        if dx > threshold:
            return "RIGHT"
        elif dx < -threshold:
            return "LEFT"
    else:
        # Vertical movement
        if dy > threshold:
            return "DOWN"
        elif dy < -threshold:
            return "UP"
    
    return "NONE"


def get_current_direction():
    """Get current direction"""
    return current_direction


def set_current_direction(direction):
    """Manually set direction"""
    global current_direction
    valid = ["NONE", "UP", "DOWN", "LEFT", "RIGHT"]
    if direction in valid:
        current_direction = direction


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS & PAGE REFERENCES
# ═══════════════════════════════════════════════════════════════════════════════

def set_settings(ref):
    """Set settings panel reference"""
    global settings_ref
    settings_ref = ref


def get_settings():
    """Get settings panel reference"""
    return settings_ref


def set_gaming_page(page_ref):
    """Register gaming mode page for gesture/direction routing"""
    global gaming_page_ref
    gaming_page_ref = page_ref
    if page_ref:
        print("✅ Gaming page registered in mode_manager")
    else:
        print("🔌 Gaming page unregistered")


def get_gaming_page():
    """Get gaming page reference"""
    return gaming_page_ref


def set_desktop_page(page_ref):
    """Register desktop page for gesture feedback (NEW)"""
    global desktop_page_ref
    desktop_page_ref = page_ref
    if page_ref:
        print("✅ Desktop page registered in mode_manager")
    else:
        print("🔌 Desktop page unregistered")


def get_desktop_page():
    """Get desktop page reference"""
    return desktop_page_ref


# ═══════════════════════════════════════════════════════════════════════════════
# GAMING MODE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def send_gaming_gesture(gesture_name):
    """
    Route gesture to gaming page AND store for polling
    Called by hand_tracker.py when gesture is detected in gaming mode
    """
    global current_gesture
    
    if not gesture_name or gesture_name == "NONE":
        return
    
    # Store gesture
    current_gesture = gesture_name
    
    # Route to gaming page if registered
    if gaming_page_ref is not None:
        try:
            gaming_page_ref.handle_gesture(gesture_name)
            print(f"🎮 Gesture → Gaming: {gesture_name}")
        except Exception as e:
            print(f"❌ Gesture routing error: {e}")


def send_gaming_direction(direction):
    """
    Route direction to gaming page
    Called when direction changes
    """
    global current_direction
    
    current_direction = direction
    
    if gaming_page_ref is not None:
        try:
            gaming_page_ref.handle_direction(direction)
        except Exception as e:
            print(f"❌ Direction routing error: {e}")


def get_gaming_state():
    """Get all gaming-related state in one call"""
    return {
        "mode": mode,
        "is_gaming": _gaming_mode_active,
        "gesture": current_gesture,
        "direction": current_direction,
        "hand_position": hand_position,
        "normalized_position": normalized_hand_position,
        "hand_detected": hand_detected,
        "gaming_page_active": gaming_page_ref is not None
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ✅ DESKTOP MODE HELPERS (NEW)
# ═══════════════════════════════════════════════════════════════════════════════

def send_desktop_action(action_type, details=None):
    """
    Route desktop actions to desktop page for UI feedback
    
    Args:
        action_type: "click", "double_click", "scroll", "drag_start", "drag_end"
        details: Optional dict with action details
    """
    if desktop_page_ref is not None:
        try:
            desktop_page_ref.handle_action(action_type, details or {})
        except AttributeError:
            # Desktop page doesn't have handle_action method (optional feature)
            pass
        except Exception as e:
            print(f"❌ Desktop action error: {e}")


def notify_double_click():
    """Notify desktop page of double click (called by hand_tracker)"""
    send_desktop_action("double_click", {"gesture": "palm_open"})
    print("✅ Double click notification sent")


def notify_single_click():
    """Notify desktop page of single click"""
    send_desktop_action("click", {"gesture": "fist"})


def notify_scroll(direction, amount):
    """Notify desktop page of scroll"""
    send_desktop_action("scroll", {"direction": direction, "amount": amount})


def notify_drag(state):
    """Notify desktop page of drag state change"""
    action = "drag_start" if state else "drag_end"
    send_desktop_action(action)


# ═══════════════════════════════════════════════════════════════════════════════
# RESET & CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

def reset_state():
    """Reset all state to defaults"""
    global mode, hand_detected, tracker_running, shared_frame
    global current_gesture, previous_gesture, hand_position
    global normalized_hand_position, current_direction
    global gaming_page_ref, desktop_page_ref, _gaming_mode_active
    
    mode = "DESKTOP"
    _gaming_mode_active = False
    hand_detected = False
    tracker_running = False
    shared_frame = None
    current_gesture = None
    previous_gesture = None
    hand_position = (0, 0)
    normalized_hand_position = (0.5, 0.5)
    current_direction = "NONE"
    gaming_page_ref = None
    desktop_page_ref = None
    
    print("🔄 Mode manager state reset")


def cleanup():
    """Cleanup before shutdown"""
    global gaming_page_ref, desktop_page_ref, settings_ref, shared_frame
    
    gaming_page_ref = None
    desktop_page_ref = None
    settings_ref = None
    shared_frame = None
    
    print("🧹 Mode manager cleanup complete")


# ═══════════════════════════════════════════════════════════════════════════════
# DEBUG
# ═══════════════════════════════════════════════════════════════════════════════

def print_state():
    """Print current state for debugging"""
    print("\n" + "═" * 50)
    print("📊 MODE MANAGER STATE")
    print("═" * 50)
    print(f"  Mode:           {mode}")
    print(f"  Gaming Active:  {_gaming_mode_active}")
    print(f"  Hand Detected:  {hand_detected}")
    print(f"  Tracker:        {'Running' if tracker_running else 'Stopped'}")
    print(f"  Gesture:        {current_gesture}")
    print(f"  Direction:      {current_direction}")
    print(f"  Hand Position:  {hand_position}")
    print(f"  Normalized:     {normalized_hand_position}")
    print(f"  Gaming Page:    {'Active' if gaming_page_ref else 'None'}")
    print(f"  Desktop Page:   {'Active' if desktop_page_ref else 'None'}")
    print(f"  Frame:          {'Available' if shared_frame is not None else 'None'}")
    print("═" * 50 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

print("✅ Mode Manager loaded (Gaming Mode + Desktop Actions + Case Fix)")
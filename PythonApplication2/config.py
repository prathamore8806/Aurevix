import json
import os

# ═══════════════════════════════════════════════════════════════
#                        GESTURE & MOUSE
# ═══════════════════════════════════════════════════════════════
gesture_sensitivity = 5
mouse_speed = 10
scroll_speed = 10

# ═══════════════════════════════════════════════════════════════
#                           DRAWING
# ═══════════════════════════════════════════════════════════════
draw_color = (0, 0, 255)
draw_thickness = 4
auto_clear_sec = 0

# ═══════════════════════════════════════════════════════════════
#                           CAMERA
# ═══════════════════════════════════════════════════════════════
camera_index = 0
smooth_factor = 0.5

# Camera Source Names
CAMERA_SOURCES = {
    0: "📷 Camera 0 (Built-in)",
    1: "📷 Camera 1 (External)",
    2: "📷 Camera 2 (USB)"
}

# OLD Margins (legacy support)
margin_x = 0.1
margin_y = 0.12

# 🔥 NEW: Calibration Margins (pixel-based, set by calibration)
margin_x_min = 100
margin_x_max = 540
margin_y_min = 100
margin_y_max = 380

# AGGRESSIVE TRACKING MARGINS (Bottom Access Fix)
tracking_margin_x = 0.20        # 20% left/right margin
tracking_margin_top = 0.20      # 20% top margin
tracking_margin_bottom = 0.60   # 60% = bottom of screen ✅

# How it works:
# ┌─────────────────────────────┐
# │     0% - 20%  (ignored)     │ 
# │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│ ← 20% = Screen TOP
# │                             │
# │     ACTIVE TRACKING ZONE    │ ← This small zone = FULL SCREEN
# │                             │
# │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│ ← 60% = Screen BOTTOM
# │     60% - 100% (ignored)    │ ← Extra room - hand stays visible!
# └─────────────────────────────┘

brightness = 50
contrast = 50
saturation = 50
mirror = True
face_blur = False
face_focus = False
blur_intensity = 25

# ═══════════════════════════════════════════════════════════════
#                           AUDIO
# ═══════════════════════════════════════════════════════════════
audio_enabled = False
audio_volume = 80
audio_muted = False
noise_gate = 5

# ═══════════════════════════════════════════════════════════════
#                         SHORTCUTS
# ═══════════════════════════════════════════════════════════════
shortcuts_enabled = True

# ═══════════════════════════════════════════════════════════════
#                   VISUALS & PERFORMANCE
# ═══════════════════════════════════════════════════════════════
show_skeleton = True
fps_limit = 30
theme = "dark"

# ═══════════════════════════════════════════════════════════════
#                   LOGIC & CALIBRATION
# ═══════════════════════════════════════════════════════════════
left_handed_mode = False
click_sensitivity = 5

# ═══════════════════════════════════════════════════════════════
#                    CALIBRATION SETTINGS
# ═══════════════════════════════════════════════════════════════

# Calibration capture mode
calibration_capture_mode = 2  # 0=Manual, 1=Stability, 2=Countdown
calibration_stability_threshold = 90  # Percentage (70-100)
calibration_countdown_seconds = 3  # Seconds (1-5)
calibration_sound_enabled = True
calibration_volume = 60  # Percentage (0-100)
calibration_show_skeleton = True
calibration_show_grid = False
calibration_point_count = 4  # Default point count (4, 9, or 16)

# ═══════════════════════════════════════════════════════════════
#                          SYSTEM
# ═══════════════════════════════════════════════════════════════
minimize_to_tray = True
show_popups = True

# ═══════════════════════════════════════════════════════════════
#                      SETTINGS FILE
# ═══════════════════════════════════════════════════════════════
SETTINGS_FILE = "settings.json"


# ═══════════════════════════════════════════════════════════════
#                      SAVE CONFIGURATION
# ═══════════════════════════════════════════════════════════════

def save_config():
    """Save all settings to JSON file."""
    settings = {
        # Gesture & Mouse
        "gesture_sensitivity": gesture_sensitivity,
        "mouse_speed": mouse_speed,
        "scroll_speed": scroll_speed,
        
        # Drawing
        "draw_color": list(draw_color) if isinstance(draw_color, tuple) else draw_color,
        "draw_thickness": draw_thickness,
        "auto_clear_sec": auto_clear_sec,
        
        # Camera
        "camera_index": camera_index,
        "smooth_factor": smooth_factor,
        
        # Margins (legacy)
        "margin_x": margin_x,
        "margin_y": margin_y,
        
        # Calibration Margins (NEW)
        "margin_x_min": margin_x_min,
        "margin_x_max": margin_x_max,
        "margin_y_min": margin_y_min,
        "margin_y_max": margin_y_max,
        
        # Tracking Margins
        "tracking_margin_x": tracking_margin_x,
        "tracking_margin_top": tracking_margin_top,
        "tracking_margin_bottom": tracking_margin_bottom,
        
        # Image Adjustments
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "mirror": mirror,
        "face_blur": face_blur,
        "face_focus": face_focus,
        "blur_intensity": blur_intensity,
        
        # Audio
        "audio_enabled": audio_enabled,
        "audio_volume": audio_volume,
        "audio_muted": audio_muted,
        "noise_gate": noise_gate,
        
        # Shortcuts
        "shortcuts_enabled": shortcuts_enabled,
        
        # Visuals & Performance
        "show_skeleton": show_skeleton,
        "fps_limit": fps_limit,
        "theme": theme,
        
        # Logic
        "left_handed_mode": left_handed_mode,
        "click_sensitivity": click_sensitivity,
        
        # Calibration Settings
        "calibration_capture_mode": calibration_capture_mode,
        "calibration_stability_threshold": calibration_stability_threshold,
        "calibration_countdown_seconds": calibration_countdown_seconds,
        "calibration_sound_enabled": calibration_sound_enabled,
        "calibration_volume": calibration_volume,
        "calibration_show_skeleton": calibration_show_skeleton,
        "calibration_show_grid": calibration_show_grid,
        "calibration_point_count": calibration_point_count,
        
        # System
        "minimize_to_tray": minimize_to_tray,
        "show_popups": show_popups,
    }

    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        print("💾 Settings saved.")
        return True
    except Exception as e:
        print(f"❌ Failed to save settings: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
#                      LOAD CONFIGURATION
# ═══════════════════════════════════════════════════════════════

def load_config():
    """Load all settings from JSON file."""
    global gesture_sensitivity, mouse_speed, scroll_speed
    global draw_color, draw_thickness, auto_clear_sec
    global camera_index, smooth_factor, margin_x, margin_y
    global margin_x_min, margin_x_max, margin_y_min, margin_y_max
    global tracking_margin_x, tracking_margin_top, tracking_margin_bottom
    global brightness, contrast, saturation, mirror
    global face_blur, face_focus, blur_intensity
    global audio_enabled, audio_volume, audio_muted, noise_gate
    global shortcuts_enabled
    global show_skeleton, fps_limit, theme
    global left_handed_mode, click_sensitivity
    global calibration_capture_mode, calibration_stability_threshold
    global calibration_countdown_seconds, calibration_sound_enabled
    global calibration_volume, calibration_show_skeleton
    global calibration_show_grid, calibration_point_count
    global minimize_to_tray, show_popups

    if not os.path.exists(SETTINGS_FILE):
        print("📁 No settings file found. Using defaults.")
        save_config()  # Create default settings file
        return

    try:
        with open(SETTINGS_FILE, 'r') as f:
            s = json.load(f)

        # Gesture & Mouse
        gesture_sensitivity = s.get("gesture_sensitivity", gesture_sensitivity)
        mouse_speed = s.get("mouse_speed", mouse_speed)
        scroll_speed = s.get("scroll_speed", scroll_speed)

        # Drawing
        dc = s.get("draw_color", draw_color)
        draw_color = tuple(dc) if isinstance(dc, list) else dc
        draw_thickness = s.get("draw_thickness", draw_thickness)
        auto_clear_sec = s.get("auto_clear_sec", auto_clear_sec)

        # Camera
        camera_index = s.get("camera_index", camera_index)
        smooth_factor = s.get("smooth_factor", smooth_factor)
        
        # Margins (legacy)
        margin_x = s.get("margin_x", margin_x)
        margin_y = s.get("margin_y", margin_y)
        
        # Calibration Margins (NEW)
        margin_x_min = s.get("margin_x_min", 100)
        margin_x_max = s.get("margin_x_max", 540)
        margin_y_min = s.get("margin_y_min", 100)
        margin_y_max = s.get("margin_y_max", 380)
        
        # Tracking Margins
        tracking_margin_x = s.get("tracking_margin_x", 0.20)
        tracking_margin_top = s.get("tracking_margin_top", 0.20)
        tracking_margin_bottom = s.get("tracking_margin_bottom", 0.60)
        
        # Image Adjustments
        brightness = s.get("brightness", brightness)
        contrast = s.get("contrast", contrast)
        saturation = s.get("saturation", saturation)
        mirror = s.get("mirror", mirror)
        face_blur = s.get("face_blur", face_blur)
        face_focus = s.get("face_focus", face_focus)
        blur_intensity = s.get("blur_intensity", blur_intensity)

        # Audio
        audio_enabled = s.get("audio_enabled", audio_enabled)
        audio_volume = s.get("audio_volume", audio_volume)
        audio_muted = s.get("audio_muted", audio_muted)
        noise_gate = s.get("noise_gate", noise_gate)

        # Shortcuts
        shortcuts_enabled = s.get("shortcuts_enabled", shortcuts_enabled)

        # Visuals & Performance
        show_skeleton = s.get("show_skeleton", show_skeleton)
        fps_limit = s.get("fps_limit", fps_limit)
        theme = s.get("theme", theme)

        # Logic
        left_handed_mode = s.get("left_handed_mode", left_handed_mode)
        click_sensitivity = s.get("click_sensitivity", click_sensitivity)

        # Calibration Settings
        calibration_capture_mode = s.get("calibration_capture_mode", 2)
        calibration_stability_threshold = s.get("calibration_stability_threshold", 90)
        calibration_countdown_seconds = s.get("calibration_countdown_seconds", 3)
        calibration_sound_enabled = s.get("calibration_sound_enabled", True)
        calibration_volume = s.get("calibration_volume", 60)
        calibration_show_skeleton = s.get("calibration_show_skeleton", True)
        calibration_show_grid = s.get("calibration_show_grid", False)
        calibration_point_count = s.get("calibration_point_count", 4)

        # System
        minimize_to_tray = s.get("minimize_to_tray", minimize_to_tray)
        show_popups = s.get("show_popups", show_popups)

        print("✅ Settings loaded from file.")

    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Failed to load settings: {e}. Using defaults.")
        save_config()


# ═══════════════════════════════════════════════════════════════
#                      RESET TO DEFAULTS
# ═══════════════════════════════════════════════════════════════

def reset_defaults():
    """Reset all settings to factory defaults."""
    global gesture_sensitivity, mouse_speed, scroll_speed
    global draw_color, draw_thickness, auto_clear_sec
    global camera_index, smooth_factor, margin_x, margin_y
    global margin_x_min, margin_x_max, margin_y_min, margin_y_max
    global tracking_margin_x, tracking_margin_top, tracking_margin_bottom
    global brightness, contrast, saturation, mirror
    global face_blur, face_focus, blur_intensity
    global audio_enabled, audio_volume, audio_muted, noise_gate
    global shortcuts_enabled
    global show_skeleton, fps_limit, theme
    global left_handed_mode, click_sensitivity
    global calibration_capture_mode, calibration_stability_threshold
    global calibration_countdown_seconds, calibration_sound_enabled
    global calibration_volume, calibration_show_skeleton
    global calibration_show_grid, calibration_point_count
    global minimize_to_tray, show_popups

    # Gesture & Mouse
    gesture_sensitivity = 5
    mouse_speed = 10
    scroll_speed = 10

    # Drawing
    draw_color = (0, 0, 255)
    draw_thickness = 4
    auto_clear_sec = 0

    # Camera
    camera_index = 0
    smooth_factor = 0.5
    
    # Margins (legacy)
    margin_x = 0.1
    margin_y = 0.12
    
    # Calibration Margins
    margin_x_min = 100
    margin_x_max = 540
    margin_y_min = 100
    margin_y_max = 380
    
    # Tracking Margins
    tracking_margin_x = 0.20
    tracking_margin_top = 0.20
    tracking_margin_bottom = 0.60
    
    # Image Adjustments
    brightness = 50
    contrast = 50
    saturation = 50
    mirror = True
    face_blur = False
    face_focus = False
    blur_intensity = 25

    # Audio
    audio_enabled = False
    audio_volume = 80
    audio_muted = False
    noise_gate = 5

    # Shortcuts
    shortcuts_enabled = True

    # Visuals & Performance
    show_skeleton = True
    fps_limit = 30
    theme = "dark"

    # Logic
    left_handed_mode = False
    click_sensitivity = 5

    # Calibration Settings
    calibration_capture_mode = 2
    calibration_stability_threshold = 90
    calibration_countdown_seconds = 3
    calibration_sound_enabled = True
    calibration_volume = 60
    calibration_show_skeleton = True
    calibration_show_grid = False
    calibration_point_count = 4

    # System
    minimize_to_tray = True
    show_popups = True

    save_config()
    print("🔄 All settings reset to defaults.")


# ═══════════════════════════════════════════════════════════════
#                      HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_calibration_margins():
    """Get calibration margins as dict."""
    return {
        'x_min': margin_x_min,
        'x_max': margin_x_max,
        'y_min': margin_y_min,
        'y_max': margin_y_max
    }

def set_calibration_margins(x_min, x_max, y_min, y_max):
    """Set calibration margins and save."""
    global margin_x_min, margin_x_max, margin_y_min, margin_y_max
    
    margin_x_min = x_min
    margin_x_max = x_max
    margin_y_min = y_min
    margin_y_max = y_max
    
    save_config()
    print(f"✅ Calibration margins updated: X({x_min}-{x_max}) Y({y_min}-{y_max})")

def get_tracking_zone():
    """Get active tracking zone as percentage dict."""
    return {
        'margin_x': tracking_margin_x,
        'margin_top': tracking_margin_top,
        'margin_bottom': tracking_margin_bottom
    }

def is_calibrated():
    """Check if system has been calibrated."""
    # Simple check: if margins differ from defaults
    return not (
        margin_x_min == 100 and 
        margin_x_max == 540 and 
        margin_y_min == 100 and 
        margin_y_max == 380
    )

def get_config_summary():
    """Get human-readable config summary."""
    return f"""
╔══════════════════════════════════════════════════════════╗
║              SGCC CONFIGURATION SUMMARY                  ║
╠══════════════════════════════════════════════════════════╣
║ 🎮 GESTURE                                               ║
║   Sensitivity: {gesture_sensitivity} | Mouse Speed: {mouse_speed} | Scroll: {scroll_speed}      ║
║                                                          ║
║ 🎨 DRAWING                                               ║
║   Color: {draw_color} | Thickness: {draw_thickness}                    ║
║   Auto-clear: {auto_clear_sec}s                                      ║
║                                                          ║
║ 📷 CAMERA                                                ║
║   Index: {camera_index} | Mirror: {mirror} | Smooth: {smooth_factor}           ║
║   Brightness: {brightness} | Contrast: {contrast} | Saturation: {saturation}      ║
║                                                          ║
║ 🎯 CALIBRATION                                           ║
║   Mode: {['Manual', 'Stability', 'Countdown'][calibration_capture_mode]} | Points: {calibration_point_count}                        ║
║   Stability: {calibration_stability_threshold}% | Countdown: {calibration_countdown_seconds}s              ║
║   Sound: {calibration_sound_enabled} | Volume: {calibration_volume}%                    ║
║   Margins: X({margin_x_min}-{margin_x_max}) Y({margin_y_min}-{margin_y_max})       ║
║                                                          ║
║ 🔊 AUDIO                                                 ║
║   Enabled: {audio_enabled} | Volume: {audio_volume}% | Muted: {audio_muted}        ║
║   Noise Gate: {noise_gate}%                                     ║
║                                                          ║
║ ⚙️ SYSTEM                                                ║
║   Theme: {theme} | FPS Limit: {fps_limit} | Skeleton: {show_skeleton}       ║
║   Shortcuts: {shortcuts_enabled} | Tray: {minimize_to_tray}                 ║
║   Calibrated: {is_calibrated()}                                      ║
╚══════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════
#                      AUTO-LOAD ON IMPORT
# ═══════════════════════════════════════════════════════════════

# Automatically load settings when module is imported
load_config()

# Optional: Print summary on load (comment out if too verbose)
# print(get_config_summary())

# ═══════════════════════════════════════════════════════════════
#                      TEXT-TO-SPEECH
# ═══════════════════════════════════════════════════════════════
tts_enabled = True
tts_rate = 150  # Words per minute (100-200)
tts_volume = 90  # Percentage (0-100)
tts_voice_index = 0  # Voice selection

"""
Hand Tracker V3.2 - Main Orchestrator
FIXED: Memory leaks, proper cleanup, GC, TRACKING STABILITY
"""

import cv2
import mediapipe as mp
import time
import gc
import math
import numpy as np

import config
import mode_manager

from .core.camera import ThreadedCamera
from .core.filters import LandmarkSmoother
from .core.state import state
from .core.hud import HologramHUD, HoloColors

from .modes.desktop_mode import DesktopMode
from .modes.gaming_mode import GamingMode
from .modes.draw_mode import DrawMode


mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

CAM_W, CAM_H = 640, 480


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════════════════════

threaded_cam = None
mp_hands = None
hands = None
hud = None
landmark_smoother = None
modes = {}
current_mode = None
_last_index_pos = (0.5, 0.5)

# 🔥 NEW: Tracking stability
hand_lost_counter = 0
hand_detected_counter = 0
HAND_LOST_THRESHOLD = 3  # Lose tracking after 3 consecutive failures
HAND_FOUND_THRESHOLD = 2  # Regain tracking after 2 consecutive detections

# Custom gestures
CUSTOM_GESTURES_ENABLED = False
recognizer = None
executor = None

try:
    from gesture_recognizer import recognizer as _recognizer
    from gesture_executor import executor as _executor
    recognizer = _recognizer
    executor = _executor
    CUSTOM_GESTURES_ENABLED = True
    print("✅ Custom gesture recognition loaded")
except ImportError:
    print("⚠️ Custom gesture modules not found")


# ═══════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_components():
    global hud, landmark_smoother, modes, mp_hands, hands
    
    hud = HologramHUD(CAM_W, CAM_H)
    landmark_smoother = LandmarkSmoother()
    
    # 🔥 FIXED: Better MediaPipe settings for tracking stability
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,      # Lower = easier to detect initially
        min_tracking_confidence=0.4,       # 🔥 REDUCED from 0.5 to 0.4 - more forgiving
        model_complexity=0                 # 0 = fastest, less CPU
    )
    
    modes["DESKTOP"] = DesktopMode(state, hud)
    modes["GAMING"] = GamingMode(state, hud)
    modes["DRAW"] = DrawMode(state, hud)


def cleanup_components():
    global hands, hud, landmark_smoother, modes
    
    # FIXED: Properly close MediaPipe
    if hands is not None:
        hands.close()
        hands = None
    
    if hud is not None:
        hud.cleanup()
        hud = None
    
    if landmark_smoother is not None:
        landmark_smoother.reset()
    landmark_smoother = None
    
    for mode in modes.values():
        mode.reset()
    modes.clear()
    
    # FIXED: Force GC
    gc.collect()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_fingers(lm, handed="Right"):
    """
    🔥 IMPROVED: Better finger detection with stricter thresholds
    """
    f = []
    left = getattr(config, 'left_handed_mode', False)
    
    # Thumb detection
    thumb_tip = lm[4]
    thumb_ip = lm[3]
    thumb_mcp = lm[2]
    
    if left:
        thumb_extended = thumb_tip.x > thumb_ip.x if handed == "Right" else thumb_tip.x < thumb_ip.x
    else:
        thumb_extended = thumb_tip.x < thumb_ip.x if handed == "Right" else thumb_tip.x > thumb_ip.x
    
    # 🔥 IMPROVED: Stricter thumb distance check
    thumb_dist = math.sqrt((thumb_tip.x - thumb_mcp.x)**2 + (thumb_tip.y - thumb_mcp.y)**2)
    thumb_extended = thumb_extended and thumb_dist > 0.10  # 🔥 INCREASED from 0.08 to 0.10
    f.append(thumb_extended)
    
    # 🔥 IMPROVED: Stricter margin for other fingers
    margin = 0.03  # 🔥 INCREASED from 0.02 to 0.03 - less false positives
    
    # Index finger (most important - extra strict)
    index_extended = lm[8].y < (lm[6].y - margin * 1.5)  # 🔥 50% stricter for index
    f.append(index_extended)
    
    # Other fingers
    f.append(lm[12].y < (lm[10].y - margin))
    f.append(lm[16].y < (lm[14].y - margin))
    f.append(lm[20].y < (lm[18].y - margin))
    
    return f


def get_gesture(fingers, lm):
    """
    🔥 IMPROVED: More strict gesture detection
    """
    i, m, r, p, t = fingers[1], fingers[2], fingers[3], fingers[4], fingers[0]
    n = sum(fingers)
    
    # 🔥 STRICT: Only index, explicitly no others
    if i and not m and not r and not p and not t:
        return "MOVE"
    
    # 🔥 STRICT: Index + Middle, no others
    if i and m and not r and not p and not t:
        return "SCROLL"
    
    # Fist
    if n == 0:
        return "FIST"
    
    # 🔥 STRICT: Three fingers for drag (no thumb, no pinky)
    if i and m and r and not p and not t:
        return "DRAG"
    
    # Open palm
    if n == 5:
        return "OPEN"
    
    return "NONE"


def apply_settings(frame):
    if config.mirror:
        frame = cv2.flip(frame, 1)
    
    b, c = config.brightness, config.contrast
    if b != 50 or c != 50:
        alpha = 1.0 + (c - 50) / 50.0
        beta = (b - 50) * 2
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    
    s = config.saturation
    if s != 50:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= s / 50.0
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    return frame


def update_last_pos(pos):
    global _last_index_pos
    _last_index_pos = pos


def try_custom_gesture(lm, frame):
    if not CUSTOM_GESTURES_ENABLED:
        return False
    try:
        landmarks = [{"x": l.x, "y": l.y, "z": l.z} for l in lm]
        matched = recognizer.match_gesture(landmarks)
        if matched:
            if executor.execute(matched):
                state.show_action(f"◈ {matched['name']}", HoloColors.NEON_PURPLE)
                return True
    except Exception as e:
        print(f"Custom gesture error: {e}")
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_last_index_pos():
    return _last_index_pos


def set_camera_state(enabled):
    state.camera_enabled = enabled
    if not enabled:
        state.reset()
        if landmark_smoother:
            landmark_smoother.reset()
        for mode in modes.values():
            mode.reset()


def set_gesture_state(enabled):
    state.gesture_enabled = enabled
    if not enabled:
        state.reset()


def get_camera_state():
    return state.camera_enabled


def get_gesture_state():
    return state.gesture_enabled


def set_gui(gui_ref):
    state.gui = gui_ref
    if CUSTOM_GESTURES_ENABLED:
        reload_custom_gestures()
        update_gesture_settings()


def stop_tracker():
    state.running = False
    state.reset()


def reset_states():
    global hand_lost_counter, hand_detected_counter
    state.reset()
    hand_lost_counter = 0
    hand_detected_counter = 0
    if landmark_smoother:
        landmark_smoother.reset()
    for mode in modes.values():
        mode.reset()


def reload_custom_gestures():
    if CUSTOM_GESTURES_ENABLED and recognizer:
        try:
            recognizer.reload_gestures()
        except:
            pass


def update_gesture_settings():
    if CUSTOM_GESTURES_ENABLED:
        try:
            if executor:
                executor.set_cooldown(getattr(config, 'gesture_cooldown', 500))
            if recognizer:
                recognizer.set_threshold(getattr(config, 'gesture_match_threshold', 75))
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run_tracker():
    global threaded_cam, current_mode
    
    state.running = True
    threaded_cam = None
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⬡ HAND TRACKER V3.2 — ENHANCED STABILITY                                    ║
║  🎮 THREADED CAMERA • MODE SEPARATION • TRACKING FIX                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    init_components()
    
    try:
        _main_loop()
    finally:
        if threaded_cam is not None:
            threaded_cam.stop()
            threaded_cam = None
        
        cleanup_components()
        state.running = False
        print("🛑 Tracker stopped")


def _main_loop():
    global threaded_cam, current_mode, hand_lost_counter, hand_detected_counter
    
    last_mode = None
    
    while state.running:
        # FIXED: Periodic cleanup
        state.tick()
        
        # Camera disabled
        if not state.camera_enabled:
            if threaded_cam is not None:
                threaded_cam.stop()
                threaded_cam = None
            mode_manager.set_shared_frame(None)
            mode_manager.set_hand_detected(False)
            time.sleep(0.05)
            continue
        
        # Start camera
        if threaded_cam is None:
            threaded_cam = ThreadedCamera(config.camera_index)
            if not threaded_cam.start():
                time.sleep(0.5)
                continue
            time.sleep(0.3)
        
        if not threaded_cam.isOpened():
            time.sleep(0.1)
            continue
        
        # Read frame
        ret, frame = threaded_cam.read()
        if not ret or frame is None:
            time.sleep(0.001)
            continue
        
        mode = mode_manager.mode
        fps = threaded_cam.get_fps()
        
        # Mode change
        if mode != last_mode:
            print(f"🔄 Switching: {last_mode} → {mode}")
    
            # Deactivate old mode
            if last_mode in modes and last_mode is not None:
                try:
                    modes[last_mode].deactivate()
                except Exception as e:
                    print(f"⚠️ Deactivate {last_mode} error: {e}")
    
            # Activate new mode
            if mode in modes:
                try:
                    modes[mode].activate()
                except Exception as e:
                    print(f"⚠️ Activate {mode} error: {e}")
    
            last_mode = mode
            current_mode = modes.get(mode)
        
        # Gesture disabled
        if not state.gesture_enabled:
            frame = apply_settings(frame)
            frame = hud.draw_disabled(frame)
            mode_manager.set_shared_frame(frame)
            mode_manager.set_hand_detected(False)
            time.sleep(0.01)
            continue
        
        # Process frame
        frame = apply_settings(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 🔥 FIXED: Better exception handling for MediaPipe
        try:
            results = hands.process(rgb)
        except Exception as e:
            print(f"⚠️ MediaPipe error: {e}")
            results = None
        
        # 🔥 NEW: Stable hand detection with hysteresis
        raw_hand_detected = results and results.multi_hand_landmarks is not None
        
        if raw_hand_detected:
            hand_detected_counter += 1
            hand_lost_counter = 0
            
            # Need 2 consecutive detections to confirm
            hand_detected = hand_detected_counter >= HAND_FOUND_THRESHOLD
        else:
            hand_lost_counter += 1
            hand_detected_counter = 0
            
            # Need 3 consecutive losses to lose tracking
            hand_detected = hand_lost_counter < HAND_LOST_THRESHOLD
        
        # HUD
        if mode != "GAMING":
            hud.update()
            frame = hud.draw_scanlines(frame, 0.02)
            frame = hud.draw_corner_brackets(frame)
            frame = hud.draw_top_bar(frame, mode, fps, hand_detected)
            
            mx = getattr(config, 'tracking_margin_x', 0.15)
            mt = getattr(config, 'tracking_margin_top', 0.15)
            mb = getattr(config, 'tracking_margin_bottom', 0.80)
            frame = hud.draw_tracking_zone(frame, mx, mt, mb)
        else:
            cv2.putText(frame, f"FPS: {fps}", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)
            
            # 🔥 IMPROVED: Show tracking stability
            status = f"TRACKING ({hand_detected_counter})" if hand_detected else f"LOST ({hand_lost_counter})"
            status_color = (0, 255, 0) if hand_detected else (0, 100, 255)
            cv2.putText(frame, status, (100, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        # Action popup
        feedback = state.get_action_feedback()
        if feedback:
            frame = hud.draw_action_popup(frame, feedback["text"], feedback["color"])
        
        # Process hands - only if stable detection
        if raw_hand_detected and hand_detected and results.multi_handedness:
            mode_manager.set_hand_detected(True)
            
            for hand_lm, hand_info in zip(results.multi_hand_landmarks, results.multi_handedness):
                handed = hand_info.classification[0].label
                
                if mode == "GAMING":
                    lm = hand_lm.landmark
                else:
                    lm = landmark_smoother.smooth(hand_lm.landmark)
                
                fingers = get_fingers(lm, handed)
                gesture = get_gesture(fingers, lm)
                
                # Custom gestures for desktop/draw
                if mode in ["DESKTOP", "DRAW"]:
                    if try_custom_gesture(lm, frame):
                        continue
                
                # ✅ FIXED: Draw cyberpunk hand in ALL modes (including GAMING)
                if getattr(config, 'show_skeleton', True):
                    frame = hud.draw_cyberpunk_hand(frame, hand_lm, mp_hands.HAND_CONNECTIONS, fingers)
                    
                    # Only show hand panel in Desktop/Draw (not Gaming - keeps it clean)
                    if mode != "GAMING":
                        frame = hud.draw_hand_panel(frame, fingers, handed, gesture)
                
                if len(lm) > 8:
                    update_last_pos((lm[8].x, lm[8].y))
                
                if current_mode:
                    current_mode.process(lm, fingers, frame, handed)
        else:
            # 🔥 IMPROVED: Only reset after confirmed loss
            if hand_lost_counter >= HAND_LOST_THRESHOLD:
                mode_manager.set_hand_detected(False)
                
                if mode != "GAMING":
                    landmark_smoother.reset()
                
                update_last_pos((0.5, 0.5))
        
        # Bottom bar
        if mode != "GAMING":
            hints = {
                "DESKTOP": "🤌=Move | ✋=Click | 2=Scroll | 3=Drag",
                "DRAW": "1=Draw | 2=Pick | 3=Wheel | 5=Clear"
            }
            frame = hud.draw_bottom_bar(frame, hints.get(mode, ""))
        
        # Share frame
        mode_manager.set_shared_frame(frame)
        
        # FIXED: Always sleep
        if mode == "GAMING":
            time.sleep(0.001)
        else:
            time.sleep(0.005)


if __name__ == "__main__":
    state.camera_enabled = True
    state.gesture_enabled = True
    run_tracker()
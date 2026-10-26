"""
Gaming Mode - Zone-based gesture detection
✅ OK 👌 gesture = TOGGLE CURSOR CONTROL (andar hi)
✅ GAMING GESTURES = UP, DOWN, LEFT, RIGHT, FIST, PALM (6 TOTAL)
✅ CURSOR GESTURES = Desktop-like controls (jab OK karke enable karo)
✅ NO CAMERA FREEZE - CURSOR BLOCK FIX
✅ DWELL TIME = 1.5 seconds
✅ MODE SWITCH COOLDOWN = 2.5 seconds
"""

import time
import cv2
import numpy as np
import math
from collections import deque

from .base_mode import BaseMode

# Safe pyautogui import
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# Safe mode_manager import
try:
    import mode_manager
    MODE_MANAGER_AVAILABLE = True
except ImportError:
    MODE_MANAGER_AVAILABLE = False

# Safe game controller import
try:
    from gaming_gesture_controller import game_controller
    GAME_CONTROLLER_AVAILABLE = True
except ImportError:
    GAME_CONTROLLER_AVAILABLE = False

# Safe config import
try:
    import config
    CONFIG_AVAILABLE = True
except ImportError:
    config = None
    CONFIG_AVAILABLE = False


class SimpleCursorSmoother:
    """Simple cursor smoother"""
    
    def __init__(self):
        self.prev_x = 0
        self.prev_y = 0
        self.smoothing = 0.25  # ⬅️ REDUCED for smoother movement
        self.initialized = False
    
    def smooth(self, x, y, freeze=False):
        if freeze:
            return self.prev_x, self.prev_y
        
        if not self.initialized:
            self.prev_x = x
            self.prev_y = y
            self.initialized = True
            return x, y
        
        self.prev_x = self.prev_x + (x - self.prev_x) * self.smoothing
        self.prev_y = self.prev_y + (y - self.prev_y) * self.smoothing
        
        return self.prev_x, self.prev_y
    
    def reset(self):
        self.prev_x = 0
        self.prev_y = 0
        self.initialized = False


class GamingMode(BaseMode):
    """Gaming mode - zone gestures + internal cursor toggle"""
    
    def __init__(self, state, hud):
        super().__init__(state, hud)
        
        # ═══════════════════════════════════════════════════════════════════
        # GAMING MODE - Zone thresholds
        # ═══════════════════════════════════════════════════════════════════
        self.TOP_THRESHOLD = 0.40
        self.BOTTOM_THRESHOLD = 0.60
        self.LEFT_THRESHOLD = 0.35
        self.RIGHT_THRESHOLD = 0.65
        
        # Zone state
        self.zone_history = deque(maxlen=5)
        self.current_zone = "CENTER"
        self.last_confirmed_zone = "CENTER"
        self.last_gaming_time = 0
        self.last_gaming_gesture = None
        self.gesture_flash_time = 0
        
        # Smoothing
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.smooth_factor = 0.6
        
        # Overlay
        self.overlay = None
        
        # Game controller
        self.game_controller = None
        if GAME_CONTROLLER_AVAILABLE:
            self.game_controller = game_controller
        
        # Debug
        self.debug = False
        self.gesture_count = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # OK GESTURE - Toggle cursor (INTERNAL)
        # ═══════════════════════════════════════════════════════════════════
        self._last_ok_time = 0
        self._ok_cooldown = 2.5  # ⬅️ INCREASED from 1.5 to 2.5
        self._ok_gesture_frames = 0
        self._ok_required_frames = 4  # ⬅️ INCREASED from 3 to 4
        
        # Cursor enabled state (INTERNAL TO GAMING MODE)
        self.cursor_enabled = False
        
        # ═══════════════════════════════════════════════════════════════════
        # CURSOR MODE - Components (INTERNAL)
        # ═══════════════════════════════════════════════════════════════════
        self.cursor_smoother = SimpleCursorSmoother()
        self.prev_scroll_y = None
        self.click_held = False
        self.palm_freeze_time = None
        
        # Dwell click
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_radius = 25
        self.dwell_time = 1.5
        self.dwell_triggered = False
        
        # Volume
        self.last_volume_time = 0
        self.volume_cooldown = 0.4
        
        # Play/Pause
        self.last_playpause_time = 0
        self.playpause_cooldown = 0.6
        
        # Gesture stability
        self._cursor_gesture_buffer = []
        self._last_cursor_gesture = "NONE"
        
        print("✅ GamingMode [6 ZONES + INTERNAL CURSOR TOGGLE]")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def activate(self):
        """Called when entering Gaming Mode from main menu"""
        self.active = True
        self.cursor_enabled = False  # Always start in gaming zone mode
        self.reset()
        
        # ✅ NOTIFY MODE_MANAGER - CURSOR IS DISABLED
        self._update_cursor_state(False)
        
        print("🎮 Gaming Mode ACTIVATED - 6 Zones Ready")
    
    def deactivate(self):
        """Called when leaving Gaming Mode"""
        self.active = False
        self._safe_release_drag()
        
        # ✅ NOTIFY MODE_MANAGER - CURSOR IS DISABLED
        self._update_cursor_state(False)
        
        print("🎮 Gaming Mode DEACTIVATED")
        self.reset()
    
    def reset(self):
        """Reset all state"""
        # Gaming state
        self.zone_history.clear()
        self.current_zone = "CENTER"
        self.last_confirmed_zone = "CENTER"
        self.last_gaming_time = 0
        self.last_gaming_gesture = None
        self.gesture_flash_time = 0
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        self.gesture_count = 0
        self._ok_gesture_frames = 0
        
        # Cursor state
        self.prev_scroll_y = None
        self._safe_release_drag()
        self.palm_freeze_time = None
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_triggered = False
        self._cursor_gesture_buffer = []
        self._last_cursor_gesture = "NONE"
        
        if self.cursor_smoother:
            self.cursor_smoother.reset()
    
    # ✅✅✅ NEW METHOD - UPDATE MODE_MANAGER ABOUT CURSOR STATE
    def _update_cursor_state(self, enabled):
        """Notify mode_manager about cursor state"""
        if MODE_MANAGER_AVAILABLE:
            try:
                # Set internal cursor flag in mode_manager
                if hasattr(mode_manager, 'set_gaming_cursor_active'):
                    mode_manager.set_gaming_cursor_active(enabled)
                    print(f"✅ Mode Manager Notified: Cursor={'ON' if enabled else 'OFF'}")
            except Exception as e:
                print(f"⚠️ Mode manager update failed: {e}")
    
    def _safe_release_drag(self):
        """Release mouse drag safely"""
        if self.click_held:
            try:
                if PYAUTOGUI_AVAILABLE:
                    pyautogui.mouseUp(_pause=False)
            except:
                pass
            self.click_held = False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SAFE PYAUTOGUI WRAPPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _safe_move(self, x, y):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.moveTo(int(x), int(y), _pause=False)
        except Exception as e:
            if self.debug:
                print(f"Move error: {e}")
    
    def _safe_click(self):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.click(_pause=False)
        except:
            pass
    
    def _safe_double_click(self):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.doubleClick(_pause=False)
        except:
            pass
    
    def _safe_scroll(self, amount):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.scroll(int(amount), _pause=False)
        except:
            pass
    
    def _safe_mouse_down(self):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.mouseDown(_pause=False)
        except:
            pass
    
    def _safe_key(self, key):
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press(key, _pause=False)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # OK GESTURE - INTERNAL CURSOR TOGGLE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _detect_ok_gesture(self, lm):
        """Detect OK 👌 gesture"""
        try:
            if lm is None or len(lm) < 21:
                return False
            
            thumb_tip = lm[4]
            index_tip = lm[8]
            
            distance = math.sqrt(
                (thumb_tip.x - index_tip.x)**2 + 
                (thumb_tip.y - index_tip.y)**2
            )
            
            if distance >= 0.06:
                return False
            
            margin = 0.02
            middle_extended = lm[12].y < (lm[10].y - margin)
            ring_extended = lm[16].y < (lm[14].y - margin)
            pinky_extended = lm[20].y < (lm[18].y - margin)
            
            return middle_extended and ring_extended and pinky_extended
        except:
            return False
    
    def _handle_ok_gesture(self, frame, now):
        """Handle OK gesture - toggle internal cursor"""
        try:
            if now - self._last_ok_time < self._ok_cooldown:
                self._draw_ok_cooldown(frame, now)
                return False
            
            self._ok_gesture_frames += 1
            self._draw_ok_progress(frame)
            
            if self._ok_gesture_frames < self._ok_required_frames:
                return False
            
            # TOGGLE CONFIRMED
            self._last_ok_time = now
            self._ok_gesture_frames = 0
            
            self.cursor_enabled = not self.cursor_enabled
            
            # ✅ NOTIFY MODE_MANAGER IMMEDIATELY
            self._update_cursor_state(self.cursor_enabled)
            
            # Reset cursor state
            self._safe_release_drag()
            self.prev_scroll_y = None
            self.palm_freeze_time = None
            self.dwell_start_time = None
            self.dwell_triggered = False
            
            if self.cursor_enabled:
                print("👌 CURSOR CONTROL ON (inside Gaming Mode)")
            else:
                print("👌 GAMING ZONES ON")
            
            return True
        except:
            return False
    
    def _draw_ok_progress(self, frame):
        """Draw OK progress bar"""
        try:
            h, w = frame.shape[:2]
            
            progress = self._ok_gesture_frames / self._ok_required_frames
            bar_w, bar_h = 150, 20
            bar_x = w // 2 - bar_w // 2
            bar_y = h // 2 + 50
            
            color = (0, 255, 0) if self.cursor_enabled else (0, 255, 255)
            target = "GAMING" if self.cursor_enabled else "CURSOR"
            
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_w * progress), bar_y + bar_h), color, -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), color, 2)
            
            cv2.putText(frame, f"OK -> {target}", (w // 2 - 60, bar_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, "OK", (w // 2 - 25, h // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        except:
            pass
    
    def _draw_ok_cooldown(self, frame, now):
        """Draw cooldown text"""
        try:
            h, w = frame.shape[:2]
            remaining = self._ok_cooldown - (now - self._last_ok_time)
            cv2.putText(frame, f"WAIT {remaining:.1f}s", (w // 2 - 80, h // 2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)
        except:
            pass
    
    def _draw_ok_hint(self, frame):
        """Draw OK hint in corner"""
        try:
            h, w = frame.shape[:2]
            
            if self.cursor_enabled:
                color, hint, mode = (0, 255, 255), "OK=GAMING", "CURSOR"
            else:
                color, hint, mode = (0, 255, 0), "OK=CURSOR", "GAMING"
            
            cv2.rectangle(frame, (w - 150, 10), (w - 10, 65), (30, 30, 30), -1)
            cv2.rectangle(frame, (w - 150, 10), (w - 10, 65), color, 2)
            cv2.putText(frame, mode, (w - 140, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, hint, (w - 140, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CURSOR MODE - GESTURE CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _classify_cursor_gesture(self, fingers, lm):
        """Classify cursor gestures"""
        try:
            thumb, index, middle, ring, pinky = fingers
            n = sum(fingers)
            
            # Thumb only - volume
            if thumb and not index and not middle and not ring and not pinky:
                thumb_tip_y = lm[4].y
                thumb_mcp_y = lm[2].y
                diff = thumb_mcp_y - thumb_tip_y
                
                if diff > 0.08:
                    return "VOLUME_UP"
                elif diff < -0.08:
                    return "VOLUME_DOWN"
                return "THUMB"
            
            # Thumb + Pinky = Play/Pause
            if thumb and pinky and not index and not middle and not ring:
                return "PLAY_PAUSE"
            
            # Fist
            if n == 0:
                return "FIST"
            
            # Open palm
            if n == 5:
                return "DOUBLE_CLICK"
            
            # Index only
            if index and not middle and not ring and not pinky:
                return "MOVE"
            
            # Index + Middle
            if index and middle and not ring and not pinky:
                return "SCROLL"
            
            # Index + Middle + Ring
            if index and middle and ring and not pinky:
                return "DRAG"
            
            return "NONE"
        except:
            return "NONE"
    
    def _get_stable_cursor_gesture(self, gesture):
        """Stabilize cursor gesture"""
        self._cursor_gesture_buffer.append(gesture)
        if len(self._cursor_gesture_buffer) > 3:
            self._cursor_gesture_buffer.pop(0)
        
        if len(self._cursor_gesture_buffer) >= 2:
            if self._cursor_gesture_buffer[-1] == self._cursor_gesture_buffer[-2]:
                self._last_cursor_gesture = gesture
        
        return self._last_cursor_gesture
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CURSOR MODE - HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _get_screen_pos(self, lx, ly):
        """Convert hand to screen position"""
        try:
            mx, mt, mb = 0.15, 0.15, 0.80
            
            if CONFIG_AVAILABLE and config:
                mx = getattr(config, 'tracking_margin_x', 0.15)
                mt = getattr(config, 'tracking_margin_top', 0.15)
                mb = getattr(config, 'tracking_margin_bottom', 0.80)
                
                if getattr(config, 'left_handed_mode', False):
                    lx = 1.0 - lx
            
            nx = max(0, min(1, (lx - mx) / (1 - 2 * mx)))
            ny = max(0, min(1, (ly - mt) / (mb - mt)))
            
            tx = nx * self.state.SCREEN_W
            ty = ny * self.state.SCREEN_H
            
            return tx, ty
        except:
            return self.state.SCREEN_W // 2, self.state.SCREEN_H // 2
    
    def _handle_cursor_move(self, lm, frame, now):
        """Handle cursor move with dwell click"""
        try:
            index = lm[8]
            tx, ty = self._get_screen_pos(index.x, index.y)
            sx, sy = self.cursor_smoother.smooth(tx, ty, freeze=False)
            
            sx = max(0, min(self.state.SCREEN_W - 1, sx))
            sy = max(0, min(self.state.SCREEN_H - 1, sy))
            
            # ✅ MOVE CURSOR (without pyautogui blocking)
            self._safe_move(sx, sy)
            
            h, w = frame.shape[:2]
            cx, cy = int(index.x * w), int(index.y * h)
            
            # Dwell click logic
            if self.dwell_position is None:
                self.dwell_position = (sx, sy)
                self.dwell_start_time = now
                self.dwell_triggered = False
            else:
                dist = math.sqrt((sx - self.dwell_position[0])**2 + (sy - self.dwell_position[1])**2)
                
                if dist > self.dwell_radius:
                    self.dwell_position = (sx, sy)
                    self.dwell_start_time = now
                    self.dwell_triggered = False
                else:
                    elapsed = now - self.dwell_start_time
                    progress = min(1.0, elapsed / self.dwell_time)
                    
                    if progress > 0.1:
                        self._draw_dwell_ring(frame, cx, cy, progress)
                    
                    if elapsed >= self.dwell_time and not self.dwell_triggered:
                        self._safe_click()
                        self.dwell_triggered = True
                        print("🖱️ DWELL CLICK")
            
            # Draw cursor indicator
            cv2.circle(frame, (cx, cy), 12, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
            
            self._draw_cursor_label(frame, f"MOVE ({int(sx)},{int(sy)})")
        except Exception as e:
            if self.debug:
                print(f"Cursor move error: {e}")
    
    def _handle_cursor_scroll(self, lm, frame):
        """Handle scroll"""
        try:
            index = lm[8]
            
            h, w = frame.shape[:2]
            cx, cy = int(index.x * w), int(index.y * h)
            
            if self.prev_scroll_y is not None:
                delta = self.prev_scroll_y - index.y
                scroll_speed = 5
                if CONFIG_AVAILABLE and config:
                    scroll_speed = getattr(config, 'scroll_speed', 5)
                
                scroll = int(delta * scroll_speed * 150)
                if abs(scroll) > 0:
                    self._safe_scroll(scroll)
            
            self.prev_scroll_y = index.y
            
            # Draw indicator
            cv2.circle(frame, (cx, cy), 18, (255, 255, 0), 2)
            cv2.line(frame, (cx, cy - 20), (cx, cy - 8), (255, 255, 0), 3)
            cv2.line(frame, (cx, cy + 8), (cx, cy + 20), (255, 255, 0), 3)
            
            self._draw_cursor_label(frame, "SCROLL")
            self._reset_dwell()
        except:
            pass
    
    def _handle_cursor_drag(self, lm, frame):
        """Handle drag"""
        try:
            index = lm[8]
            
            if not self.click_held:
                self._safe_mouse_down()
                self.click_held = True
                print("🖱️ DRAG START")
            
            tx, ty = self._get_screen_pos(index.x, index.y)
            sx, sy = self.cursor_smoother.smooth(tx, ty, freeze=False)
            sx = max(0, min(self.state.SCREEN_W - 1, sx))
            sy = max(0, min(self.state.SCREEN_H - 1, sy))
            
            self._safe_move(sx, sy)
            
            h, w = frame.shape[:2]
            cx, cy = int(index.x * w), int(index.y * h)
            
            cv2.circle(frame, (cx, cy), 18, (255, 0, 255), 3)
            self._draw_cursor_label(frame, f"DRAG ({int(sx)},{int(sy)})")
            self._reset_dwell()
        except:
            pass
    
    def _handle_cursor_double_click(self, lm, frame, now):
        """Handle double click"""
        try:
            h, w = frame.shape[:2]
            px = int((lm[0].x + lm[9].x) / 2 * w)
            py = int((lm[0].y + lm[9].y) / 2 * h)
            
            if self.palm_freeze_time is None:
                self.palm_freeze_time = now
            
            elapsed = now - self.palm_freeze_time
            
            if elapsed >= 0.2:
                self._safe_double_click()
                print("🖱️ DOUBLE CLICK")
                self.palm_freeze_time = now + 0.8
            else:
                progress = int((elapsed / 0.2) * 100)
                self._draw_cursor_label(frame, f"HOLD {progress}%")
            
            cv2.circle(frame, (px, py), 25, (0, 255, 255), 3)
            self._reset_dwell()
        except:
            pass
    
    def _handle_cursor_volume(self, direction, frame, now):
        """Handle volume"""
        try:
            if now - self.last_volume_time < self.volume_cooldown:
                return
            
            self.last_volume_time = now
            
            if direction == "UP":
                self._safe_key('volumeup')
                self._safe_key('volumeup')
                print("🔊 VOLUME UP")
                self._draw_cursor_label(frame, "👍 VOL UP")
            else:
                self._safe_key('volumedown')
                self._safe_key('volumedown')
                print("🔉 VOLUME DOWN")
                self._draw_cursor_label(frame, "👎 VOL DOWN")
        except:
            pass
    
    def _handle_cursor_playpause(self, frame, now):
        """Handle play/pause"""
        try:
            if now - self.last_playpause_time < self.playpause_cooldown:
                return
            
            self.last_playpause_time = now
            self._safe_key('space')
            print("⏯️ PLAY/PAUSE")
            self._draw_cursor_label(frame, "🤙 PLAY/PAUSE")
        except:
            pass
    
    def _handle_cursor_fist(self, lm, frame):
        """Handle fist - pause"""
        try:
            index = lm[8]
            tx, ty = self._get_screen_pos(index.x, index.y)
            self.cursor_smoother.smooth(tx, ty, freeze=True)
            
            h, w = frame.shape[:2]
            cx, cy = int(index.x * w), int(index.y * h)
            
            cv2.circle(frame, (cx, cy), 20, (0, 0, 255), 3)
            self._draw_cursor_label(frame, "✊ PAUSED")
            self._reset_dwell()
        except:
            pass
    
    def _reset_dwell(self):
        """Reset dwell state"""
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_triggered = False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CURSOR MODE - DRAWING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _draw_dwell_ring(self, frame, cx, cy, progress):
        """Draw dwell progress ring"""
        try:
            r = 28
            cv2.circle(frame, (cx, cy), r, (50, 50, 50), 3)
            
            angle = int(360 * progress)
            if angle > 0:
                cv2.ellipse(frame, (cx, cy), (r, r), -90, 0, angle, (0, 255, 255), 3)
            
            pct = int(progress * 100)
            cv2.putText(frame, f"{pct}%", (cx - 12, cy + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        except:
            pass
    
    def _draw_cursor_label(self, frame, text):
        """Draw cursor label"""
        try:
            h, w = frame.shape[:2]
            
            bw, bh = 200, 35
            bx = w // 2 - bw // 2
            by = h - 50
            
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (30, 30, 30), -1)
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), 2)
            
            ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            tx = w // 2 - ts[0] // 2
            cv2.putText(frame, text, (tx, by + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        except:
            pass
    
    def _draw_cursor_mode_header(self, frame):
        """Draw cursor mode header"""
        try:
            h, w = frame.shape[:2]
            
            cv2.rectangle(frame, (w//2 - 100, 10), (w//2 + 100, 50), (0, 180, 180), -1)
            cv2.rectangle(frame, (w//2 - 100, 10), (w//2 + 100, 50), (255, 255, 255), 2)
            cv2.putText(frame, "CURSOR MODE", (w//2 - 75, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CURSOR MODE - MAIN PROCESSOR
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _process_cursor_mode(self, lm, fingers, frame, now):
        """Process cursor mode"""
        try:
            self._draw_cursor_mode_header(frame)
            
            raw = self._classify_cursor_gesture(fingers, lm)
            gesture = self._get_stable_cursor_gesture(raw)
            
            # Release drag if needed
            if gesture != "DRAG" and self.click_held:
                self._safe_release_drag()
                print("🖱️ DRAG END")
            
            # Reset states
            if gesture != "SCROLL":
                self.prev_scroll_y = None
            if gesture != "DOUBLE_CLICK":
                self.palm_freeze_time = None
            
            # Handle gesture
            if gesture == "MOVE":
                self._handle_cursor_move(lm, frame, now)
            elif gesture == "SCROLL":
                self._handle_cursor_scroll(lm, frame)
            elif gesture == "DRAG":
                self._handle_cursor_drag(lm, frame)
            elif gesture == "DOUBLE_CLICK":
                self._handle_cursor_double_click(lm, frame, now)
            elif gesture == "VOLUME_UP":
                self._handle_cursor_volume("UP", frame, now)
            elif gesture == "VOLUME_DOWN":
                self._handle_cursor_volume("DOWN", frame, now)
            elif gesture == "PLAY_PAUSE":
                self._handle_cursor_playpause(frame, now)
            elif gesture == "FIST":
                self._handle_cursor_fist(lm, frame)
            else:
                self._draw_cursor_label(frame, "READY")
                self._reset_dwell()
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAMING MODE - ZONE DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _detect_zone(self, x, y, num_fingers):
        """Detect zone (6 total zones)"""
        if num_fingers == 0:
            return "FIST"
        
        if num_fingers == 5:
            return "PALM"
        
        if 1 <= num_fingers <= 4:
            if y < self.TOP_THRESHOLD:
                return "UP"
            if y > self.BOTTOM_THRESHOLD:
                return "DOWN"
            if x < self.LEFT_THRESHOLD:
                return "LEFT"
            if x > self.RIGHT_THRESHOLD:
                return "RIGHT"
        
        return "CENTER"
    
    def _confirm_zone(self):
        """Confirm zone with history"""
        if len(self.zone_history) == 0:
            return self.last_confirmed_zone
        
        counts = {}
        for z in self.zone_history:
            counts[z] = counts.get(z, 0) + 1
        
        best = max(counts, key=counts.get)
        return best if counts[best] >= 3 else self.last_confirmed_zone  # ⬅️ CHANGED from 2 to 3
    
    def _zone_to_gesture(self, zone):
        """Map zone to gesture"""
        is_external = False
        try:
            if MODE_MANAGER_AVAILABLE and hasattr(mode_manager, 'get_gaming_page'):
                gp = mode_manager.get_gaming_page()
                if gp and hasattr(gp, 'current_mode'):
                    is_external = (gp.current_mode == "EXTERNAL")
        except:
            pass
        
        mapping = {
            "UP": "swipe_up",
            "DOWN": "swipe_down",
            "LEFT": "swipe_left",
            "RIGHT": "swipe_right",
        }
        
        if not is_external:
            mapping["FIST"] = "fist"
            mapping["PALM"] = "palm_open"
        
        return mapping.get(zone)
    
    def _execute_gesture(self, gesture, now):
        """Execute gaming gesture"""
        try:
            # Check external block
            if gesture in ["fist", "palm_open"]:
                try:
                    if MODE_MANAGER_AVAILABLE and hasattr(mode_manager, 'get_gaming_page'):
                        gp = mode_manager.get_gaming_page()
                        if gp and hasattr(gp, 'current_mode') and gp.current_mode == "EXTERNAL":
                            return
                except:
                    pass
            
            self.last_gaming_gesture = gesture
            self.last_gaming_time = now
            self.gesture_flash_time = now + 0.25
            self.gesture_count += 1
            
            # Execute via controller
            if self.game_controller and GAME_CONTROLLER_AVAILABLE:
                try:
                    self.game_controller.execute_game_action(gesture)
                except:
                    pass
            
            # Send to mode_manager
            if MODE_MANAGER_AVAILABLE:
                try:
                    if hasattr(mode_manager, 'send_gaming_gesture'):
                        mode_manager.send_gaming_gesture(gesture)
                except:
                    pass
            
            print(f"🎮 [{self.gesture_count}] {gesture.upper()}")
        except:
            pass
    
    def _update_hand_position(self, x, y, w, h):
        """Update hand position in mode_manager"""
        if MODE_MANAGER_AVAILABLE:
            try:
                if hasattr(mode_manager, 'set_hand_position'):
                    mode_manager.set_hand_position(x, y, w, h)
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAMING MODE - DRAWING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _draw_zones(self, frame, confirmed_zone):
        """Draw zone overlays"""
        try:
            h, w = frame.shape[:2]
            
            up = int(self.TOP_THRESHOLD * h)
            down = int(self.BOTTOM_THRESHOLD * h)
            left = int(self.LEFT_THRESHOLD * w)
            right = int(self.RIGHT_THRESHOLD * w)
            
            if self.overlay is None or self.overlay.shape != frame.shape:
                self.overlay = np.zeros_like(frame)
            else:
                self.overlay.fill(0)
            
            zone_colors = {
                "UP": ((0, 0), (w, up), (0, 255, 0)),
                "DOWN": ((0, down), (w, h), (0, 255, 0)),
                "LEFT": ((0, up), (left, down), (0, 255, 255)),
                "RIGHT": ((right, up), (w, down), (0, 255, 255)),
                "FIST": ((0, 0), (w, h), (0, 0, 255)),
                "PALM": ((0, 0), (w, h), (255, 0, 255))
            }
            
            if confirmed_zone in zone_colors:
                pt1, pt2, color = zone_colors[confirmed_zone]
                cv2.rectangle(self.overlay, pt1, pt2, color, -1)
                alpha = 0.15 if confirmed_zone in ["FIST", "PALM"] else 0.20
                cv2.addWeighted(self.overlay, alpha, frame, 1 - alpha, 0, frame)
            
            # Zone lines
            lc = (80, 80, 80)
            cv2.line(frame, (0, up), (w, up), lc, 2)
            cv2.line(frame, (0, down), (w, down), lc, 2)
            cv2.line(frame, (left, up), (left, down), lc, 2)
            cv2.line(frame, (right, up), (right, down), lc, 2)
            
            # Labels
            tc = (150, 150, 150)
            cv2.putText(frame, "UP", (w//2 - 15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, tc, 2)
            cv2.putText(frame, "DOWN", (w//2 - 30, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, tc, 2)
            cv2.putText(frame, "LEFT", (10, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tc, 2)
            cv2.putText(frame, "RIGHT", (w - 70, h//2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tc, 2)
        except:
            pass
    
    def _draw_hand_indicator(self, frame, x, y, num):
        """Draw hand indicator"""
        try:
            h, w = frame.shape[:2]
            ix, iy = int(x * w), int(y * h)
            
            cv2.circle(frame, (ix, iy), 18, (0, 60, 30), -1)
            cv2.circle(frame, (ix, iy), 12, (0, 180, 90), -1)
            cv2.circle(frame, (ix, iy), 6, (0, 255, 120), -1)
            cv2.circle(frame, (ix, iy), 15, (255, 255, 255), 2)
            
            cv2.putText(frame, str(num), (ix - 5, iy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)
        except:
            pass
    
    def _draw_zone_box(self, frame, zone):
        """Draw zone status box"""
        try:
            h, w = frame.shape[:2]
            
            colors = {
                "UP": (0, 255, 0), "DOWN": (0, 255, 0),
                "LEFT": (0, 255, 255), "RIGHT": (0, 255, 255),
                "FIST": (0, 0, 255), "PALM": (255, 0, 255),
                "CENTER": (100, 100, 100)
            }
            
            c = colors.get(zone, (100, 100, 100))
            t = zone if zone != "CENTER" else "READY"
            
            bw = 110
            bx = w // 2 - bw // 2
            
            cv2.rectangle(frame, (bx, 50), (bx + bw, 85), (0, 0, 0), -1)
            cv2.rectangle(frame, (bx, 50), (bx + bw, 85), c, 3)
            
            ts = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)[0]
            tx = w // 2 - ts[0] // 2
            cv2.putText(frame, t, (tx, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.65, c, 2)
        except:
            pass
    
    def _draw_gesture_flash(self, frame, now):
        """Draw gesture flash"""
        try:
            if now < self.gesture_flash_time and self.last_gaming_gesture:
                h, w = frame.shape[:2]
                
                text = self.last_gaming_gesture.upper().replace("_", " ")
                ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.8, 4)[0]
                tx = (w - ts[0]) // 2
                ty = h // 2 + 15
                
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 0), 10)
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 120), 3)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAMING MODE - MAIN PROCESSOR
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _process_gaming_mode(self, lm, fingers, frame, now):
        """Process gaming zone mode"""
        try:
            num = sum(fingers)
            
            # Smooth position
            idx = lm[8]
            rx, ry = idx.x, idx.y
            
            self.smooth_x = self.smooth_x * (1 - self.smooth_factor) + rx * self.smooth_factor
            self.smooth_y = self.smooth_y * (1 - self.smooth_factor) + ry * self.smooth_factor
            
            x, y = self.smooth_x, self.smooth_y
            
            # Update hand position
            h, w = frame.shape[:2]
            self._update_hand_position(x * w, y * h, w, h)
            
            # Detect zone
            detected = self._detect_zone(x, y, num)
            self.zone_history.append(detected)
            confirmed = self._confirm_zone()
            
            # Execute on zone change
            if confirmed != self.current_zone and confirmed != "CENTER":
                cooldown = 0.5 if confirmed in ["FIST", "PALM"] else 0.18  # ⬅️ INCREASED cooldowns
                
                if now - self.last_gaming_time > cooldown:
                    gesture = self._zone_to_gesture(confirmed)
                    if gesture:
                        self._execute_gesture(gesture, now)
                        self.current_zone = confirmed
                        self.last_confirmed_zone = confirmed
            
            if confirmed == "CENTER":
                self.current_zone = "CENTER"
                self.last_confirmed_zone = "CENTER"
            
            # Draw
            self._draw_zones(frame, confirmed)
            self._draw_hand_indicator(frame, x, y, num)
            self._draw_zone_box(frame, confirmed)
            self._draw_gesture_flash(frame, now)
        except:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN PROCESS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def process(self, lm, fingers, frame, handed):
        """Main process - routes to gaming or cursor"""
        if not self.active:
            return
        
        if lm is None or len(lm) < 21:
            return
        
        if frame is None:
            return
        
        now = time.time()
        
        # Check OK gesture FIRST
        is_ok = self._detect_ok_gesture(lm)
        
        if is_ok:
            self._handle_ok_gesture(frame, now)
            self._draw_ok_hint(frame)
            return
        else:
            self._ok_gesture_frames = 0
        
        # Draw hint
        self._draw_ok_hint(frame)
        
        # Route to mode
        if self.cursor_enabled:
            self._process_cursor_mode(lm, fingers, frame, now)
        else:
            self._process_gaming_mode(lm, fingers, frame, now)


if __name__ == "__main__":
    print("🎮 Gaming Mode - COMPLETE v2.0")
    print("")
    print("✅ FIXES:")
    print("   - OK cooldown: 1.5s → 2.5s")
    print("   - OK frames: 3 → 4")
    print("   - Cursor smoothing: 0.3 → 0.25")
    print("   - Zone confirmation: 2 → 3 frames")
    print("   - Gesture cooldowns increased")
    print("   - Mode manager cursor state sync")
    print("")
    print("GAMING MODE (6 ZONES):")
    print("   ⬆️ UP    - swipe_up")
    print("   ⬇️ DOWN  - swipe_down")
    print("   ⬅️ LEFT  - swipe_left")
    print("   ➡️ RIGHT - swipe_right")
    print("   ✊ FIST  - fist")
    print("   ✋ PALM  - palm_open")
    print("")
    print("CURSOR MODE (internal, toggle with OK):")
    print("   ☝️ Index = Move")
    print("   ✌️ Index+Middle = Scroll")
    print("   🤟 3 fingers = Drag")
    print("   ✋ Open palm = Double click")
    print("   👍 Thumb up = Volume up")
    print("   👎 Thumb down = Volume down")
    print("   🤙 Thumb+Pinky = Play/Pause")
    print("   ☝️ 1.5s hold = Dwell click")
    print("")
    print("👌 OK gesture = Toggle GAMING ↔ CURSOR (internal)")
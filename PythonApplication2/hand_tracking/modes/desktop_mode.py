"""
Desktop Mode - Cursor control, clicks, scroll, drag, VOLUME, PLAY/PAUSE
GESTURES:
- 👍 Thumb Up/Down = Volume
- 🤙 Pinky + Thumb = Play/Pause
"""

import time
import math
import numpy as np
import pyautogui
import cv2
import threading
import queue
import mode_manager

from .base_mode import BaseMode
from ..core.filters import CursorSmoother
from ..core.hud import HoloColors
import config

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MEDIA CONTROLLER - PLAY/PAUSE
# ═══════════════════════════════════════════════════════════════════════════════

class MediaController:
    """
    ZERO-LAG media control
    
    🤙 Pinky + Thumb = Play/Pause (spacebar)
    
    Uses background thread - never blocks camera
    """
    
    def __init__(self):
        self.last_action_time = 0
        self.cooldown = 0.8  # 800ms between toggles (prevent double-tap)
        
        # Background execution
        self._action_queue = queue.Queue(maxsize=2)
        self._worker_running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        
        # Visual feedback
        self.feedback_until = 0
        self.is_playing = True  # Assume playing initially
        
        print("✅ MediaController [ZERO-LAG]")
        print("   └── 🤙 Pinky + Thumb = Play/Pause")
    
    def _worker(self):
        """Background worker - executes media keys"""
        while self._worker_running:
            try:
                action = self._action_queue.get(timeout=0.1)
            
                try:
                    if action == "playpause":
                        # ✅ Use playpause media key instead of spacebar
                        # This won't trigger UI buttons
                        pyautogui.press('playpause', _pause=False)
                except Exception as e:
                    # Fallback: try media key alternatives
                    try:
                        pyautogui.hotkey('ctrl', 'space', _pause=False)
                    except:
                        pass
                
                time.sleep(0.05)
                
            except queue.Empty:
                continue
            except Exception:
                time.sleep(0.1)
    
    def toggle_play_pause(self):
        """Queue play/pause toggle - returns immediately"""
        now = time.time()
        
        if now - self.last_action_time < self.cooldown:
            return False
        
        try:
            self._action_queue.put_nowait("playpause")
            self.last_action_time = now
            self.feedback_until = now + 0.5
            self.is_playing = not self.is_playing
            print(f"🎬 {'▶️ PLAY' if self.is_playing else '⏸️ PAUSE'}")
            return True
        except queue.Full:
            return False
    
    def cleanup(self):
        """Stop worker thread"""
        try:
            self._worker_running = False
            if self._worker_thread.is_alive():
                self._worker_thread.join(timeout=0.5)
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# 🔊 THUMB VOLUME DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class ThumbVolumeDetector:
    """
    ZERO-LAG volume control using thumb gestures
    
    👍 Thumb UP = Volume UP
    👎 Thumb DOWN = Volume DOWN
    """
    
    def __init__(self):
        self.last_action_time = 0
        self.cooldown = 0.5
        self.feedback_until = 0
        self.feedback_type = None
        self._last_thumb_x = 0
        self._last_thumb_y = 0
        print("✅ ThumbVolumeDetector [SAFE]")
    
    def detect(self, landmarks, fingers):
        """Detect thumb up/down gesture"""
        try:
            now = time.time()
            
            if now - self.last_action_time < self.cooldown:
                return None
            
            if landmarks is None or len(landmarks) < 21:
                return None
            
            thumb, index, middle, ring, pinky = fingers
            
            # Only thumb extended
            if not (thumb and not index and not middle and not ring and not pinky):
                return None
            
            try:
                thumb_tip_y = landmarks[4].y
                thumb_mcp_y = landmarks[2].y
                self._last_thumb_x = landmarks[4].x
                self._last_thumb_y = landmarks[4].y
            except (IndexError, AttributeError):
                return None
            
            thumb_vertical = thumb_mcp_y - thumb_tip_y
            
            if thumb_vertical > 0.08:
                self.last_action_time = now
                self.feedback_until = now + 0.3
                self.feedback_type = "UP"
                return "UP"
            
            elif thumb_vertical < -0.08:
                self.last_action_time = now
                self.feedback_until = now + 0.3
                self.feedback_type = "DOWN"
                return "DOWN"
            
            return None
            
        except Exception:
            return None
    
    def draw(self, frame, cam_w, cam_h):
        """Draw feedback"""
        try:
            now = time.time()
            
            if now >= self.feedback_until or not self.feedback_type:
                return frame
            
            x = int(self._last_thumb_x * cam_w)
            y = int(self._last_thumb_y * cam_h)
            x = max(30, min(cam_w - 30, x))
            y = max(30, min(cam_h - 30, y))
            
            if self.feedback_type == "UP":
                color = (0, 255, 255)
                cv2.circle(frame, (x, y - 30), 20, color, -1)
                cv2.putText(frame, "+", (x - 8, y - 22),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            else:
                color = (255, 0, 255)
                cv2.circle(frame, (x, y + 30), 20, color, -1)
                cv2.putText(frame, "-", (x - 6, y + 38),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        except:
            pass
        
        return frame
    
    def reset(self):
        self.feedback_type = None


# ═══════════════════════════════════════════════════════════════════════════════
# 🔊 VOLUME CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class VolumeController:
    """System volume controller with background thread"""
    
    def __init__(self):
        self._volume = 50
        self._action_queue = queue.Queue(maxsize=2)
        self._worker_running = True
        self._lock = threading.Lock()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        print("✅ VolumeController [ROBUST]")
    
    def _worker(self):
        """Background worker"""
        while self._worker_running:
            try:
                action = self._action_queue.get(timeout=0.1)
                try:
                    if action == "up":
                        pyautogui.press('volumeup', _pause=False)
                        pyautogui.press('volumeup', _pause=False)
                    elif action == "down":
                        pyautogui.press('volumedown', _pause=False)
                        pyautogui.press('volumedown', _pause=False)
                except:
                    pass
                time.sleep(0.05)
            except queue.Empty:
                continue
            except:
                time.sleep(0.1)
    
    def get_volume(self):
        with self._lock:
            return self._volume
    
    def increase(self):
        try:
            self._action_queue.put_nowait("up")
            with self._lock:
                self._volume = min(100, self._volume + 10)
            print(f"🔊 Volume UP → {self._volume}%")
            return True
        except:
            return False
    
    def decrease(self):
        try:
            self._action_queue.put_nowait("down")
            with self._lock:
                self._volume = max(0, self._volume - 10)
            print(f"🔉 Volume DOWN → {self._volume}%")
            return True
        except:
            return False
    
    def cleanup(self):
        try:
            self._worker_running = False
            if self._worker_thread.is_alive():
                self._worker_thread.join(timeout=0.5)
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

class DwellClickDetector:
    """Detect cursor dwell for auto-click"""
    
    def __init__(self, dwell_time=0.8, radius=15):
        self.dwell_time = dwell_time
        self.radius = radius
        self.reset()
    
    def reset(self):
        self.dwell_start = None
        self.dwell_pos = None
        self.is_dwelling = False
        self.progress = 0.0
    
    def update(self, x, y, enabled=True):
        if not enabled:
            self.reset()
            return False, 0.0
        
        now = time.time()
        
        if self.dwell_pos is not None:
            dist = math.sqrt((x - self.dwell_pos[0])**2 + (y - self.dwell_pos[1])**2)
            
            if dist > self.radius:
                self.reset()
                self.dwell_pos = (x, y)
                self.dwell_start = now
                return False, 0.0
        else:
            self.dwell_pos = (x, y)
            self.dwell_start = now
            return False, 0.0
        
        elapsed = now - self.dwell_start
        self.progress = min(1.0, elapsed / self.dwell_time)
        
        if elapsed >= self.dwell_time:
            if not self.is_dwelling:
                self.is_dwelling = True
                return True, 1.0
        
        return False, self.progress


class HandStillnessDetector:
    """Detect when hand is still"""
    
    def __init__(self, window_size=6, threshold=0.005):
        self.window_size = window_size
        self.threshold = threshold
        self._positions = np.zeros((window_size, 2), dtype=np.float32)
        self._count = 0
        self._head = 0
    
    def update(self, landmarks):
        try:
            if landmarks is None or len(landmarks) < 21:
                return False
            
            palm_x = (landmarks[0].x + landmarks[9].x) * 0.5
            palm_y = (landmarks[0].y + landmarks[9].y) * 0.5
            
            idx = self._head % self.window_size
            self._positions[idx, 0] = palm_x
            self._positions[idx, 1] = palm_y
            
            self._head += 1
            self._count = min(self._count + 1, self.window_size)
            
            if self._count < 4:
                return False
            
            valid = self._positions[:self._count]
            variance = np.var(valid, axis=0).sum()
            
            return variance < self.threshold
        except:
            return False
    
    def reset(self):
        self._count = 0
        self._head = 0


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DESKTOP MODE
# ═══════════════════════════════════════════════════════════════════════════════

class DesktopMode(BaseMode):
    """
    Desktop mode with media controls
    
    GESTURES:
    ☝️  Index only         = Move cursor
    ✌️  Index + Middle     = Scroll
    🤟 Index+Middle+Ring   = Drag
    ✋  All 5 fingers      = Double click
    ✊  Fist               = Pause cursor
    👍  Thumb only UP      = Volume UP
    👎  Thumb only DOWN    = Volume DOWN
    🤙  Pinky + Thumb      = Play/Pause
    """
    
    def __init__(self, state, hud):
        super().__init__(state, hud)
        
        self.cursor_smoother = CursorSmoother()
        self.dwell_detector = DwellClickDetector(
            dwell_time=getattr(config, 'dwell_click_time', 0.8),
            radius=getattr(config, 'dwell_click_radius', 15)
        )
        self.stillness_detector = HandStillnessDetector()
        
        # Volume control
        self.thumb_detector = ThumbVolumeDetector()
        self.volume_controller = VolumeController()
        self.volume_display_until = 0
        
        # Media control
        self.media_controller = MediaController()
        self.media_display_until = 0
        
        # State
        self.prev_scroll_y = None
        self.click_held = False
        self.palm_freeze_time = None
        
        # Gesture stability
        self._gesture_buffer = np.zeros(3, dtype=np.int8)
        self._gesture_head = 0
        self._last_gesture = "MOVE"
        
        print("✅ DesktopMode [MEDIA CONTROLS]")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MODE LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def activate(self):
        self.active = True
        self.reset()
    
    def deactivate(self):
        """Clean deactivation - no side effects"""
        self.active = False

        # Release any held mouse buttons
        try:
            if hasattr(self, 'click_held') and self.click_held:
                pyautogui.mouseUp(_pause=False)
                self.click_held = False
        except:
            pass

        # Clean reset
        try:
            self.reset()
        except:
            pass

        # ✅ DO NOT cleanup volume/media controllers
        # They need to stay alive for when we reactivate
    
        print("🖥️ Desktop Mode DEACTIVATED (clean)")
    
    def reset(self):
        """Safe reset - no crashes"""
        try:
            # Reset all components safely
            if hasattr(self, 'cursor_smoother') and self.cursor_smoother:
                self.cursor_smoother.reset()
        
            if hasattr(self, 'dwell_detector') and self.dwell_detector:
                self.dwell_detector.reset()
        
            if hasattr(self, 'stillness_detector') and self.stillness_detector:
                self.stillness_detector.reset()
        
            if hasattr(self, 'thumb_detector') and self.thumb_detector:
                self.thumb_detector.reset()
        
            # Reset states
            self.prev_scroll_y = None
            self.click_held = False
            self.palm_freeze_time = None
            self._gesture_head = 0
            self._last_gesture = "MOVE"
        
        except Exception as e:
            print(f"⚠️ Desktop reset error: {e}")
            pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CURSOR & GESTURE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _move_cursor(self, lx, ly, freeze=False):
        try:
            mx = getattr(config, 'tracking_margin_x', 0.15)
            mt = getattr(config, 'tracking_margin_top', 0.15)
            mb = getattr(config, 'tracking_margin_bottom', 0.80)
            
            if getattr(config, 'left_handed_mode', False):
                lx = 1.0 - lx
            
            nx = max(0, min(1, (lx - mx) / (1 - 2 * mx)))
            ny = max(0, min(1, (ly - mt) / (mb - mt)))
            
            tx = nx * self.state.SCREEN_W
            ty = ny * self.state.SCREEN_H
            sx, sy = self.cursor_smoother.smooth(tx, ty, freeze=freeze)
            
            sx = int(max(0, min(self.state.SCREEN_W - 1, sx)))
            sy = int(max(0, min(self.state.SCREEN_H - 1, sy)))
            
            if not freeze:
                pyautogui.moveTo(sx, sy, _pause=False)
            
            return sx, sy
        except:
            return 0, 0
    
    def _classify_gesture(self, fingers):
        """Classify gesture"""
        try:
            thumb, index, middle, ring, pinky = fingers
            n = sum(fingers)
            
            # SHAKA = Pinky + Thumb only (Play/Pause)
            if thumb and pinky and not index and not middle and not ring:
                code = 7  # SHAKA
            
            # THUMB ONLY = Volume gesture
            elif thumb and not index and not middle and not ring and not pinky:
                code = 6  # THUMB
            
            elif index and not middle and not ring and not pinky:
                code = 1  # MOVE
            
            elif index and middle and not ring and not pinky:
                code = 2  # SCROLL
            
            elif n == 0:
                code = 3  # FIST
            
            elif index and middle and ring and not pinky:
                code = 4  # DRAG
            
            elif n == 5:
                code = 5  # OPEN
            
            else:
                code = 0  # NONE
            
            idx = self._gesture_head % 3
            self._gesture_buffer[idx] = code
            self._gesture_head += 1
            
            if self._gesture_head < 2:
                return self._last_gesture
            
            prev_idx = (idx - 1) % 3
            if self._gesture_buffer[prev_idx] == code:
                gestures = ["NONE", "MOVE", "SCROLL", "FIST", "DRAG", "OPEN", "THUMB", "SHAKA"]
                self._last_gesture = gestures[code]
            
            return self._last_gesture
        except:
            return "NONE"
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN PROCESS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def process(self, lm, fingers, frame, handed):
        """Main processing - CRASH-PROOF"""
        try:
            if lm is None or len(lm) < 21:
                return
            if frame is None:
                return
            
            now = time.time()
            
            gesture = self._classify_gesture(fingers)
            
            try:
                index = lm[8]
                cx = int(index.x * self.state.CAM_W)
                cy = int(index.y * self.state.CAM_H)
            except:
                cx, cy = 320, 240
                index = None
            
            is_still = self.stillness_detector.update(lm)
            
            # ═══════════════════════════════════════════════════════════════
            # 🤙 SHAKA - PLAY/PAUSE
            # ═══════════════════════════════════════════════════════════════
            if gesture == "SHAKA":
                self._handle_shaka(frame, cx, cy, now)
            
            # ═══════════════════════════════════════════════════════════════
            # 👍 THUMB VOLUME
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "THUMB":
                self._handle_thumb(lm, fingers, frame, cx, cy, now)
            
            # ═══════════════════════════════════════════════════════════════
            # NORMAL GESTURES
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "MOVE":
                if index:
                    self._handle_move(lm, index, frame, cx, cy, is_still, now)
            
            elif gesture == "FIST":
                if index:
                    self._handle_fist(index, frame, cx, cy)
            
            elif gesture == "SCROLL":
                if index:
                    self._handle_scroll(index, frame)
            
            elif gesture == "OPEN":
                self._handle_open(frame, cx, cy, now)
            
            elif gesture == "DRAG":
                if index:
                    self._handle_drag(index, frame, cx, cy)
            
            else:
                self._handle_idle()
            
            # ═══════════════════════════════════════════════════════════════
            # STATE CLEANUP
            # ═══════════════════════════════════════════════════════════════
            if gesture != "SCROLL":
                self.prev_scroll_y = None
            if gesture != "OPEN":
                self.palm_freeze_time = None
            if gesture not in ["DRAG"]:
                if self.click_held:
                    try:
                        pyautogui.mouseUp(_pause=False)
                    except:
                        pass
                    self.click_held = False
        
        except Exception as e:
            print(f"⚠️ Process error: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # GESTURE HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _handle_shaka(self, frame, cx, cy, now):
        """Handle Shaka gesture (Pinky + Thumb) = Play/Pause"""
        try:
            if self.media_controller.toggle_play_pause():
                if self.media_controller.is_playing:
                    self.state.show_action("▶️ PLAY", HoloColors.NEON_GREEN)
                else:
                    self.state.show_action("⏸️ PAUSE", HoloColors.NEON_YELLOW)
                self.media_display_until = now + 1.5
            
            if now < self.media_controller.feedback_until:
                icon = "▶" if self.media_controller.is_playing else "||"
                color = (0, 255, 0) if self.media_controller.is_playing else (0, 255, 255)
                
                cv2.circle(frame, (cx, cy), 35, color, 3)
                cv2.putText(frame, icon, (cx - 15, cy + 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            
            status = "▶️ PLAY" if self.media_controller.is_playing else "⏸️ PAUSE"
            self.hud.draw_gesture_box(frame, f"🤙 {status}")
            self.hud.draw_cursor(frame, cx, cy, "ready")
            
        except Exception as e:
            print(f"⚠️ Shaka handle error: {e}")
    
    def _handle_thumb(self, lm, fingers, frame, cx, cy, now):
        """Handle thumb gesture - Volume"""
        try:
            result = self.thumb_detector.detect(lm, fingers)
            
            if result == "UP":
                if self.volume_controller.increase():
                    vol = self.volume_controller.get_volume()
                    self.state.show_action(f"🔊 VOL: {vol}%", HoloColors.NEON_BLUE)
                    self.volume_display_until = now + 1.5
            
            elif result == "DOWN":
                if self.volume_controller.decrease():
                    vol = self.volume_controller.get_volume()
                    self.state.show_action(f"🔉 VOL: {vol}%", HoloColors.NEON_PURPLE)
                    self.volume_display_until = now + 1.5
            
            frame = self.thumb_detector.draw(frame, self.state.CAM_W, self.state.CAM_H)
            
            vol = self.volume_controller.get_volume()
            self.hud.draw_gesture_box(frame, f"👍 VOLUME: {vol}%")
            self.hud.draw_cursor(frame, cx, cy, "ready")
            
        except Exception as e:
            print(f"⚠️ Thumb handle error: {e}")
    
    def _handle_move(self, lm, index, frame, cx, cy, is_still, now):
        """Handle move gesture"""
        try:
            sx, sy = self._move_cursor(index.x, index.y, freeze=False)
            
            use_dwell = getattr(config, 'dwell_click_enabled', True)
            progress = 0
            
            if use_dwell and is_still:
                should_click, progress = self.dwell_detector.update(sx, sy, enabled=True)
                
                if progress > 0:
                    self.hud.draw_dwell_indicator(frame, cx, cy, progress)
                    self.hud.draw_gesture_box(frame, f"DWELL {int(progress*100)}%")
                
                if should_click and self.state.click_ready:
                    pyautogui.click(_pause=False)
                    self.state.click_ready = False
                    self.state.click_cooldown_time = now
                    self.state.show_action("⬡ DWELL CLICK!", HoloColors.NEON_GREEN)
                    self.dwell_detector.reset()
                    self.state.click_ready = True
            else:
                self.dwell_detector.reset()
            
            if progress == 0:
                if now < self.volume_display_until:
                    vol = self.volume_controller.get_volume()
                    self.hud.draw_gesture_box(frame, f"🔊 VOL: {vol}%")
                elif now < self.media_display_until:
                    status = "▶️ PLAY" if self.media_controller.is_playing else "⏸️ PAUSE"
                    self.hud.draw_gesture_box(frame, status)
                else:
                    self.hud.draw_gesture_box(frame, f"MOVE ({sx},{sy})")
            
            self.hud.draw_cursor(frame, cx, cy, "move")
            
            self.state.click_ready = True
            self.state.rclick_ready = True
            
        except Exception as e:
            print(f"⚠️ Move handle error: {e}")
    
    def _handle_fist(self, index, frame, cx, cy):
        """Handle fist gesture"""
        try:
            self.dwell_detector.reset()
            self._move_cursor(index.x, index.y, freeze=True)
            self.hud.draw_cursor(frame, cx, cy, "ready")
            self.hud.draw_gesture_box(frame, "FIST (PAUSE)")
        except Exception as e:
            print(f"⚠️ Fist handle error: {e}")
    
    def _handle_scroll(self, index, frame):
        """Handle scroll gesture"""
        try:
            self.dwell_detector.reset()
            
            if self.prev_scroll_y is not None:
                delta = self.prev_scroll_y - index.y
                scroll = int(delta * getattr(config, 'scroll_speed', 5) * 150)
                if abs(scroll) > 0:
                    pyautogui.scroll(scroll, _pause=False)
                    arrow = "▲" if scroll > 0 else "▼"
                    self.hud.draw_gesture_box(frame, f"SCROLL {arrow}")
            
            self.prev_scroll_y = index.y
            self.state.click_ready = True
        except Exception as e:
            print(f"⚠️ Scroll handle error: {e}")
    
    def _handle_open(self, frame, cx, cy, now):
        """Handle open palm gesture"""
        try:
            if self.palm_freeze_time is None:
                self.palm_freeze_time = now
            
            elapsed = now - self.palm_freeze_time
            
            if elapsed >= 0.15:
                if (now - self.state.last_gesture_time) > self.state.COOLDOWN:
                    pyautogui.doubleClick(_pause=False)
                    self.state.last_gesture_time = now
                    self.state.show_action("⬡ DOUBLE CLICK!", HoloColors.NEON_GREEN)
                self.hud.draw_gesture_box(frame, "DOUBLE CLICKED! ✅")
            else:
                progress = int((elapsed / 0.15) * 100)
                self.hud.draw_gesture_box(frame, f"HOLD {progress}%")
            
            self.hud.draw_cursor(frame, cx, cy, "ready")
        except Exception as e:
            print(f"⚠️ Open handle error: {e}")
    
    def _handle_drag(self, index, frame, cx, cy):
        """Handle drag gesture"""
        try:
            self.dwell_detector.reset()
            
            if not self.click_held:
                pyautogui.mouseDown(_pause=False)
                self.click_held = True
            
            sx, sy = self._move_cursor(index.x, index.y, freeze=False)
            self.hud.draw_gesture_box(frame, f"DRAG ({sx},{sy})")
            self.hud.draw_cursor(frame, cx, cy, "drawing")
        except Exception as e:
            print(f"⚠️ Drag handle error: {e}")
    
    def _handle_idle(self):
        """Handle idle state"""
        try:
            self.dwell_detector.reset()
        except:
            pass
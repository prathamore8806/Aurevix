"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    TRAINING MODE GESTURE TRACKER                              ║
║              🎯 ONLY 5 GESTURES - WITH CURSOR/SCROLL/CLICK                   ║
║                         Lightweight & Independent                             ║
║                              VERSION 2.0                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

ALLOWED GESTURES:
    1. ☝️  INDEX      - Cursor Move
    2. ✌️  PEACE      - Scroll
    3. 🤟 THREE      - Drag
    4. ✋  PALM       - Double Click
    5. ⏱️  DWELL      - 3 sec hold click
    
BLOCKED (Desktop Mode Only):
    ❌ FIST, THUMB, SHAKA, PINCH, etc.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math

# ═══════════════════════════════════════════════════════════════════════════════
# PYAUTOGUI FOR GESTURE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════
import pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


# ═══════════════════════════════════════════════════════════════════════════════
# 🖱️ GESTURE EXECUTOR - Handles Cursor, Scroll, Click, Drag
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingGestureExecutor:
    """
    Execute actual cursor/scroll/click actions for training mode
    
    Handles:
    - INDEX: Move cursor
    - PEACE: Scroll
    - THREE: Drag (mouse down + move)
    - PALM: Double click (after 300ms hold)
    - DWELL: Single click (after 3s hold)
    """
    
    def __init__(self):
        # Screen dimensions
        self.screen_w = pyautogui.size()[0]
        self.screen_h = pyautogui.size()[1]
        
        # Cursor state
        self.last_cursor_pos = (self.screen_w // 2, self.screen_h // 2)
        self.cursor_history = []
        self.history_size = 5  # Smoothing buffer
        
        # Drag state
        self.is_dragging = False
        
        # Scroll state
        self.last_scroll_y = None
        self.scroll_sensitivity = 800  # Higher = faster scroll
        
        # Palm/Double-click state
        self.last_palm_time = None
        self.palm_hold_duration = 0.3  # 300ms hold for double click
        self.palm_clicked = False
        
        # Dwell click state
        self.dwell_click_done = False
        
        # Tracking zone margins (same as desktop mode)
        self.margin_x = 0.15
        self.margin_top = 0.15
        self.margin_bottom = 0.85
        
        print("✅ TrainingGestureExecutor initialized")
        print(f"   Screen: {self.screen_w}x{self.screen_h}")
    
    def execute(self, gesture, landmarks, frame_width=640, frame_height=480, dwell_progress=0.0):
        """
        Execute gesture action
        
        Args:
            gesture: Detected gesture name (INDEX, PEACE, THREE, PALM, FIST)
            landmarks: Hand landmarks from MediaPipe
            frame_width: Camera frame width
            frame_height: Camera frame height
            dwell_progress: Dwell click progress (0.0 to 1.0)
        
        Returns:
            str: Action performed (for logging)
        """
        action = None
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # INDEX - Move Cursor
            # ═══════════════════════════════════════════════════════════════
            if gesture == "INDEX":
                action = self._handle_cursor(landmarks, frame_width, frame_height)
                
                # Check for dwell click
                if dwell_progress >= 1.0 and not self.dwell_click_done:
                    pyautogui.click(_pause=False)
                    self.dwell_click_done = True
                    action = "DWELL_CLICK"
                    print("🖱️ Dwell Click!")
                elif dwell_progress < 0.5:
                    self.dwell_click_done = False
            
            # ═══════════════════════════════════════════════════════════════
            # PEACE - Scroll
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "PEACE":
                action = self._handle_scroll(landmarks)
            
            # ═══════════════════════════════════════════════════════════════
            # THREE - Drag
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "THREE":
                action = self._handle_drag(landmarks, frame_width, frame_height)
            
            # ═══════════════════════════════════════════════════════════════
            # PALM - Double Click
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "PALM":
                action = self._handle_double_click()
            
            # ═══════════════════════════════════════════════════════════════
            # FIST - Pause (no action)
            # ═══════════════════════════════════════════════════════════════
            elif gesture == "FIST":
                action = "PAUSE"
            
            # ═══════════════════════════════════════════════════════════════
            # Reset states when gesture changes
            # ═══════════════════════════════════════════════════════════════
            
            # Reset scroll when not PEACE
            if gesture != "PEACE":
                self.last_scroll_y = None
            
            # Release drag when not THREE
            if gesture != "THREE" and self.is_dragging:
                pyautogui.mouseUp(_pause=False)
                self.is_dragging = False
                print("🖱️ Drag ended")
            
            # Reset palm state when not PALM
            if gesture != "PALM":
                self.last_palm_time = None
                self.palm_clicked = False
            
            # Reset dwell when not INDEX
            if gesture != "INDEX":
                self.dwell_click_done = False
                
        except Exception as e:
            print(f"⚠️ Executor error: {e}")
        
        return action
    
    def _handle_cursor(self, landmarks, fw, fh):
        """Move cursor based on index finger position"""
        try:
            # Get index finger tip (landmark 8)
            index_tip = landmarks[8]
            
            # Apply tracking zone margins
            # Clamp to tracking zone
            raw_x = index_tip.x
            raw_y = index_tip.y
            
            # Normalize within tracking zone
            norm_x = (raw_x - self.margin_x) / (1 - 2 * self.margin_x)
            norm_y = (raw_y - self.margin_top) / (self.margin_bottom - self.margin_top)
            
            # Clamp to 0-1
            norm_x = max(0.0, min(1.0, norm_x))
            norm_y = max(0.0, min(1.0, norm_y))
            
            # Map to screen coordinates
            target_x = int(norm_x * self.screen_w)
            target_y = int(norm_y * self.screen_h)
            
            # Smooth cursor movement using history
            self.cursor_history.append((target_x, target_y))
            if len(self.cursor_history) > self.history_size:
                self.cursor_history.pop(0)
            
            # Calculate smoothed position
            if self.cursor_history:
                avg_x = sum(p[0] for p in self.cursor_history) // len(self.cursor_history)
                avg_y = sum(p[1] for p in self.cursor_history) // len(self.cursor_history)
                
                # Clamp to screen bounds
                final_x = max(0, min(self.screen_w - 1, avg_x))
                final_y = max(0, min(self.screen_h - 1, avg_y))
                
                # Move cursor
                pyautogui.moveTo(final_x, final_y, _pause=False)
                self.last_cursor_pos = (final_x, final_y)
            
            return "CURSOR_MOVE"
        
        except Exception as e:
            print(f"⚠️ Cursor error: {e}")
            return None
    
    def _handle_scroll(self, landmarks):
        """Scroll based on hand vertical movement"""
        try:
            # Get index finger tip Y position
            index_tip = landmarks[8]
            current_y = index_tip.y
            
            if self.last_scroll_y is not None:
                # Calculate vertical delta
                delta = self.last_scroll_y - current_y
                
                # Convert to scroll amount (positive = scroll up, negative = scroll down)
                scroll_amount = int(delta * self.scroll_sensitivity)
                
                if abs(scroll_amount) > 2:  # Minimum threshold
                    pyautogui.scroll(scroll_amount, _pause=False)
                    direction = "UP" if scroll_amount > 0 else "DOWN"
                    return f"SCROLL_{direction}"
            
            self.last_scroll_y = current_y
            return "SCROLL_READY"
        
        except Exception as e:
            print(f"⚠️ Scroll error: {e}")
            return None
    
    def _handle_drag(self, landmarks, fw, fh):
        """Drag with mouse down"""
        try:
            # Start drag if not already dragging
            if not self.is_dragging:
                pyautogui.mouseDown(_pause=False)
                self.is_dragging = True
                print("🖱️ Drag started")
            
            # Move cursor while dragging (reuse cursor logic)
            self._handle_cursor(landmarks, fw, fh)
            
            return "DRAGGING"
        
        except Exception as e:
            print(f"⚠️ Drag error: {e}")
            return None
    
    def _handle_double_click(self):
        """Double click with hold detection"""
        try:
            now = time.time()
            
            # First time seeing PALM
            if self.last_palm_time is None:
                self.last_palm_time = now
                return "PALM_HOLD"
            
            elapsed = now - self.last_palm_time
            
            # If held for required duration and haven't clicked yet
            if elapsed >= self.palm_hold_duration and not self.palm_clicked:
                pyautogui.doubleClick(_pause=False)
                self.palm_clicked = True
                print("🖱️ Double Click!")
                return "DOUBLE_CLICK"
            
            return "PALM_HOLD"
        
        except Exception as e:
            print(f"⚠️ Double click error: {e}")
            return None
    
    def reset(self):
        """Reset all executor state"""
        # Release mouse if dragging
        if self.is_dragging:
            try:
                pyautogui.mouseUp(_pause=False)
            except:
                pass
        
        self.is_dragging = False
        self.last_scroll_y = None
        self.last_palm_time = None
        self.palm_clicked = False
        self.dwell_click_done = False
        self.cursor_history.clear()
        
        print("🔄 Executor reset")


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 TRAINING GESTURE TRACKER - Main Class
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingGestureTracker:
    """
    Lightweight gesture tracker for Training Mode ONLY
    
    ✅ Independent camera - NOT using mode_manager.shared_frame
    ✅ Only 5 basic gestures
    ✅ Executes cursor/scroll/click actions
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ALLOWED GESTURES
    # ═══════════════════════════════════════════════════════════════════════════
    
    GESTURE_MAP = {
        "INDEX": {"emoji": "☝️", "action": "Move Cursor", "fingers": [0, 1, 0, 0, 0]},
        "PEACE": {"emoji": "✌️", "action": "Scroll", "fingers": [0, 1, 1, 0, 0]},
        "THREE": {"emoji": "🤟", "action": "Drag", "fingers": [0, 1, 1, 1, 0]},
        "PALM":  {"emoji": "✋", "action": "Double Click", "fingers": [1, 1, 1, 1, 1]},
        "FIST":  {"emoji": "✊", "action": "Pause", "fingers": [0, 0, 0, 0, 0]},
    }
    
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.hands = None
        self.mp_hands = None
        self.mp_draw = None
        
        # State
        self.is_running = False
        self.hand_detected = False
        self.current_gesture = "NONE"
        self.finger_states = [False] * 5
        
        # Dwell click state (3 second hold)
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_threshold = 3.0  # 3 seconds
        self.dwell_radius = 30  # pixels
        self.dwell_triggered = False
        
        # Smoothing
        self.gesture_buffer = []
        self.buffer_size = 3
        
        # Frame info
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 0
        self.frame_count = 0
        self.fps_time = time.time()
        
        # ═══════════════════════════════════════════════════════════════════════
        # GESTURE EXECUTOR - Handles actual cursor/scroll/click
        # ═══════════════════════════════════════════════════════════════════════
        self.executor = TrainingGestureExecutor()
        
        print("✅ TrainingGestureTracker initialized")
        print("   Allowed: INDEX, PEACE, THREE, PALM, DWELL")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CAMERA CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start(self):
        """Start camera and MediaPipe"""
        try:
            # Initialize MediaPipe
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5,
                model_complexity=0  # Fastest
            )
            
            # Initialize Camera
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"❌ Camera {self.camera_index} failed, trying 0...")
                self.cap = cv2.VideoCapture(0)
            
            if not self.cap.isOpened():
                print("❌ No camera available!")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.is_running = True
            print(f"✅ Training camera started: {self.frame_width}x{self.frame_height}")
            return True
            
        except Exception as e:
            print(f"❌ Start error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """Stop camera and cleanup"""
        self.is_running = False
        
        # Release camera
        if self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        # Close MediaPipe
        if self.hands is not None:
            try:
                self.hands.close()
            except:
                pass
            self.hands = None
        
        # Reset executor
        if hasattr(self, 'executor') and self.executor is not None:
            self.executor.reset()
        
        self.reset_state()
        print("⏹️ Training camera stopped")
    
    def reset_state(self):
        """Reset all tracking state"""
        self.hand_detected = False
        self.current_gesture = "NONE"
        self.finger_states = [False] * 5
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_triggered = False
        self.gesture_buffer.clear()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FRAME PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_frame(self):
        """
        Get processed frame with gesture detection AND EXECUTION
        
        Returns:
            tuple: (frame, gesture_name, hand_detected, dwell_progress)
        """
        if not self.is_running or self.cap is None:
            return None, "NONE", False, 0.0
        
        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None, "NONE", False, 0.0
        
        # Mirror frame
        frame = cv2.flip(frame, 1)
        
        # Update FPS
        self.frame_count += 1
        if time.time() - self.fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_time = time.time()
        
        # Process with MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        
        gesture = "NONE"
        dwell_progress = 0.0
        
        if results.multi_hand_landmarks:
            self.hand_detected = True
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw hand skeleton
            frame = self.draw_hand(frame, hand_landmarks)
            
            # Get finger states
            self.finger_states = self.get_fingers(hand_landmarks.landmark)
            
            # Classify gesture
            gesture = self.classify_gesture(self.finger_states)
            
            # Check dwell click progress
            dwell_progress = self.check_dwell_click(hand_landmarks.landmark, frame)
            
            # ═══════════════════════════════════════════════════════════════
            # 🖱️ EXECUTE GESTURE ACTION (Cursor/Scroll/Click/Drag)
            # ═══════════════════════════════════════════════════════════════
            if gesture != "NONE":
                action = self.executor.execute(
                    gesture,
                    hand_landmarks.landmark,
                    self.frame_width,
                    self.frame_height,
                    dwell_progress
                )
                
                # Show action on frame
                if action:
                    self._draw_action_feedback(frame, action)
            
            # Draw gesture info
            frame = self.draw_gesture_info(frame, gesture, dwell_progress)
        else:
            self.hand_detected = False
            self.reset_dwell()
            
            # Reset executor when no hand
            if hasattr(self, 'executor'):
                if self.executor.is_dragging:
                    self.executor.reset()
        
        self.current_gesture = gesture
        
        # Draw HUD
        frame = self.draw_hud(frame)
        
        return frame, gesture, self.hand_detected, dwell_progress
    
    def _draw_action_feedback(self, frame, action):
        """Draw action feedback on frame"""
        if action is None:
            return
        
        # Action colors
        colors = {
            "CURSOR_MOVE": (0, 255, 0),
            "SCROLL_UP": (255, 255, 0),
            "SCROLL_DOWN": (255, 255, 0),
            "DRAGGING": (255, 0, 255),
            "DOUBLE_CLICK": (0, 255, 255),
            "DWELL_CLICK": (0, 255, 255),
            "PAUSE": (100, 100, 100),
        }
        
        color = colors.get(action, (255, 255, 255))
        
        # Draw action text
        cv2.putText(
            frame, action,
            (self.frame_width - 150, 80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FINGER DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_fingers(self, landmarks):
        """
        Detect which fingers are extended
        Returns: [thumb, index, middle, ring, pinky]
        """
        fingers = [False] * 5
        
        try:
            # Thumb (special case - horizontal movement)
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            thumb_mcp = landmarks[2]
            
            # Thumb is extended if tip is far from palm
            thumb_dist = math.sqrt(
                (thumb_tip.x - thumb_mcp.x)**2 + 
                (thumb_tip.y - thumb_mcp.y)**2
            )
            fingers[0] = thumb_dist > 0.1
            
            # Other fingers (vertical comparison - tip above PIP joint)
            # Index
            fingers[1] = landmarks[8].y < landmarks[6].y - 0.02
            # Middle
            fingers[2] = landmarks[12].y < landmarks[10].y - 0.02
            # Ring
            fingers[3] = landmarks[16].y < landmarks[14].y - 0.02
            # Pinky
            fingers[4] = landmarks[20].y < landmarks[18].y - 0.02
            
        except Exception as e:
            print(f"⚠️ Finger detection error: {e}")
        
        return fingers
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GESTURE CLASSIFICATION (ONLY 5 GESTURES)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def classify_gesture(self, fingers):
        """
        Classify into ONLY 5 allowed gestures
        
        ✅ INDEX - Only index finger up
        ✅ PEACE - Index + Middle up
        ✅ THREE - Index + Middle + Ring up
        ✅ PALM  - All 5 fingers up
        ✅ FIST  - No fingers up (for dwell detection)
        """
        thumb, index, middle, ring, pinky = fingers
        count = sum(fingers)
        
        # Smooth gesture detection
        gesture = "NONE"
        
        # ✅ INDEX - Only index finger (thumb can be either)
        if index and not middle and not ring and not pinky:
            gesture = "INDEX"
        
        # ✅ PEACE - Index + Middle (no ring, no pinky)
        elif index and middle and not ring and not pinky:
            gesture = "PEACE"
        
        # ✅ THREE - Index + Middle + Ring (no pinky)
        elif index and middle and ring and not pinky:
            gesture = "THREE"
        
        # ✅ PALM - All 5 fingers (open hand)
        elif count == 5:
            gesture = "PALM"
        
        # ✅ FIST - No fingers (0 or just thumb)
        elif count == 0 or (count == 1 and thumb):
            gesture = "FIST"
        
        # Apply smoothing buffer
        self.gesture_buffer.append(gesture)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)
        
        # Return most common gesture in buffer
        if self.gesture_buffer:
            return max(set(self.gesture_buffer), key=self.gesture_buffer.count)
        
        return gesture
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DWELL CLICK DETECTION (3 SECOND HOLD)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def check_dwell_click(self, landmarks, frame):
        """
        Detect 3-second index finger hold for dwell click
        
        Returns: progress (0.0 to 1.0)
        """
        try:
            # Get index finger tip position
            index_tip = landmarks[8]
            x = int(index_tip.x * self.frame_width)
            y = int(index_tip.y * self.frame_height)
            
            # Only check dwell for INDEX gesture
            if self.current_gesture != "INDEX":
                self.reset_dwell()
                return 0.0
            
            now = time.time()
            
            # Check if position is stable
            if self.dwell_position is not None:
                dx = abs(x - self.dwell_position[0])
                dy = abs(y - self.dwell_position[1])
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > self.dwell_radius:
                    # Position changed - reset
                    self.dwell_start_time = now
                    self.dwell_position = (x, y)
                    self.dwell_triggered = False
                    return 0.0
            else:
                # First detection
                self.dwell_start_time = now
                self.dwell_position = (x, y)
                return 0.0
            
            # Calculate progress
            elapsed = now - self.dwell_start_time
            progress = min(1.0, elapsed / self.dwell_threshold)
            
            # Draw dwell indicator
            self.draw_dwell_indicator(frame, x, y, progress)
            
            # Check if dwell completed
            if progress >= 1.0 and not self.dwell_triggered:
                self.dwell_triggered = True
                print("🎯 DWELL CLICK TRIGGERED!")
                # Reset after trigger to allow next dwell
                self.dwell_start_time = now + 1.0  # 1 second cooldown
                return 1.0
            
            return progress
            
        except Exception as e:
            print(f"⚠️ Dwell check error: {e}")
            return 0.0
    
    def reset_dwell(self):
        """Reset dwell state"""
        self.dwell_start_time = None
        self.dwell_position = None
        self.dwell_triggered = False
    
    def draw_dwell_indicator(self, frame, x, y, progress):
        """Draw circular progress indicator for dwell"""
        if progress <= 0:
            return
        
        # Background circle
        cv2.circle(frame, (x, y), 40, (50, 50, 50), 2)
        
        # Progress arc
        angle = int(360 * progress)
        color = (0, 255, 255) if progress < 1.0 else (0, 255, 0)
        
        cv2.ellipse(
            frame, (x, y), (40, 40), -90, 0, angle, color, 4
        )
        
        # Center percentage text
        pct = int(progress * 100)
        text = f"{pct}%"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        text_x = x - text_size[0] // 2
        text_y = y + text_size[1] // 2
        cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DRAWING FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def draw_hand(self, frame, hand_landmarks):
        """Draw hand skeleton with custom style"""
        # Draw connections
        self.mp_draw.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2),
            self.mp_draw.DrawingSpec(color=(255, 0, 255), thickness=2)
        )
        
        # Highlight fingertips with status color
        tips = [4, 8, 12, 16, 20]
        for i, tip_id in enumerate(tips):
            tip = hand_landmarks.landmark[tip_id]
            x = int(tip.x * self.frame_width)
            y = int(tip.y * self.frame_height)
            
            # Green = extended, Red = not extended
            color = (0, 255, 0) if self.finger_states[i] else (0, 0, 255)
            cv2.circle(frame, (x, y), 10, color, -1)
            cv2.circle(frame, (x, y), 12, (255, 255, 255), 2)
        
        return frame
    
    def draw_gesture_info(self, frame, gesture, dwell_progress):
        """Draw current gesture info box"""
        if gesture in self.GESTURE_MAP:
            info = self.GESTURE_MAP[gesture]
            emoji = info["emoji"]
            action = info["action"]
        else:
            emoji = "❓"
            action = "Unknown"
        
        # Gesture box (bottom left)
        box_x, box_y = 10, self.frame_height - 90
        box_w, box_h = 220, 80
        
        # Background
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (20, 20, 20), -1)
        cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 255, 255), 2)
        
        # Gesture name
        cv2.putText(
            frame, f"{gesture}", (box_x + 15, box_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2
        )
        
        # Action description
        cv2.putText(
            frame, action, (box_x + 15, box_y + 55),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
        )
        
        # Dwell progress bar
        if dwell_progress > 0:
            bar_w = int((box_w - 30) * dwell_progress)
            cv2.rectangle(frame, (box_x + 15, box_y + 65), (box_x + 15 + bar_w, box_y + 72), (0, 255, 255), -1)
        
        return frame
    
    def draw_hud(self, frame):
        """Draw top HUD bar"""
        # Top bar background
        cv2.rectangle(frame, (0, 0), (self.frame_width, 45), (15, 15, 15), -1)
        
        # Hand detection status
        status = "HAND DETECTED" if self.hand_detected else "NO HAND"
        color = (0, 255, 0) if self.hand_detected else (100, 100, 100)
        cv2.circle(frame, (20, 25), 8, color, -1)
        cv2.putText(frame, status, (35, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Mode indicator (center)
        cv2.putText(
            frame, "TRAINING MODE", (self.frame_width // 2 - 70, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2
        )
        
        # FPS (right)
        cv2.putText(
            frame, f"FPS: {self.fps}", (self.frame_width - 90, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1
        )
        
        # Separator line
        cv2.line(frame, (0, 45), (self.frame_width, 45), (0, 255, 255), 2)
        
        # Finger status indicators (top right)
        finger_names = ["T", "I", "M", "R", "P"]
        for i, (name, state) in enumerate(zip(finger_names, self.finger_states)):
            x = self.frame_width - 170 + (i * 32)
            y = 25
            color = (0, 255, 0) if state else (60, 60, 60)
            cv2.circle(frame, (x, y), 10, color, -1)
            cv2.putText(frame, name, (x - 4, y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        
        return frame
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GESTURE MATCHING FOR TRAINING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def check_gesture_match(self, target_gesture):
        """
        Check if current gesture matches target
        
        Args:
            target_gesture: "INDEX", "PEACE", "THREE", "PALM", "FIST"
        
        Returns:
            bool: True if matches
        """
        # Map training names to our gesture names
        name_map = {
            "INDEX": "INDEX",
            "PEACE": "PEACE",
            "THREE": "THREE",
            "PALM": "PALM",
            "FIST": "FIST",
            # Alternative names
            "MOVE": "INDEX",
            "SCROLL": "PEACE",
            "DRAG": "THREE",
            "DOUBLE CLICK": "PALM",
            "OPEN": "PALM",
        }
        
        target = name_map.get(target_gesture.upper(), target_gesture.upper())
        return self.current_gesture == target
    
    def get_state(self):
        """Get current tracker state"""
        return {
            "running": self.is_running,
            "hand_detected": self.hand_detected,
            "gesture": self.current_gesture,
            "fingers": self.finger_states,
            "fps": self.fps
        }


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 Testing Training Gesture Tracker with Execution")
    print("="*60)
    print("\nGestures:")
    print("  ☝️  INDEX  → Move cursor")
    print("  ✌️  PEACE  → Scroll")
    print("  🤟 THREE  → Drag")
    print("  ✋  PALM   → Double click")
    print("  ⏱️  DWELL  → Hold 3s for click")
    print("\nPress 'q' to quit\n")
    
    tracker = TrainingGestureTracker(camera_index=0)
    
    if tracker.start():
        while True:
            frame, gesture, hand_detected, dwell = tracker.get_frame()
            
            if frame is not None:
                cv2.imshow("Training Mode - Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        
        tracker.stop()
        cv2.destroyAllWindows()
        print("\n✅ Test complete!")
    else:
        print("❌ Failed to start tracker")

# hand_visualizer.py - Color-coded hand skeleton with state-based colors
import cv2
import numpy as np
import math
import time
from enum import Enum
from collections import deque


class HandState(Enum):
    """Hand tracking states with associated colors"""
    NOT_DETECTED = 0   # Gray
    DETECTED = 1       # Blue/Cyan
    STABLE = 2         # GREEN - Ready!
    CAPTURING = 3      # Yellow - Countdown active
    CAPTURED = 4       # Bright Green - Success flash


class HandVisualizer:
    """Advanced hand skeleton visualization with state-based colors and effects"""
    
    # MediaPipe hand landmark connections
    HAND_CONNECTIONS = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index finger
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle finger
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring finger
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20),
        # Palm connections
        (5, 9), (9, 13), (13, 17)
    ]
    
    # Fingertip indices
    FINGERTIPS = [4, 8, 12, 16, 20]
    
    # State-based color schemes (BGR format for OpenCV)
    COLORS = {
        HandState.NOT_DETECTED: {
            'skeleton': (128, 128, 128),    # Gray
            'joints': (100, 100, 100),
            'fingertip': (150, 150, 150),
            'glow': (80, 80, 80),
            'index_tip': (150, 150, 150),
            'text': (128, 128, 128),
            'name': 'Gray'
        },
        HandState.DETECTED: {
            'skeleton': (255, 200, 0),      # Cyan/Blue
            'joints': (255, 150, 0),
            'fingertip': (255, 255, 0),
            'glow': (255, 100, 0),
            'index_tip': (255, 255, 0),
            'text': (255, 200, 0),
            'name': 'Blue'
        },
        HandState.STABLE: {
            'skeleton': (0, 255, 0),        # GREEN
            'joints': (0, 200, 0),
            'fingertip': (0, 255, 100),
            'glow': (0, 255, 50),
            'index_tip': (0, 255, 0),
            'text': (0, 255, 0),
            'name': 'Green'
        },
        HandState.CAPTURING: {
            'skeleton': (0, 255, 255),      # Yellow
            'joints': (0, 200, 255),
            'fingertip': (0, 255, 255),
            'glow': (0, 255, 200),
            'index_tip': (0, 255, 255),
            'text': (0, 255, 255),
            'name': 'Yellow'
        },
        HandState.CAPTURED: {
            'skeleton': (0, 255, 0),        # Bright Green
            'joints': (100, 255, 100),
            'fingertip': (150, 255, 150),
            'glow': (50, 255, 50),
            'index_tip': (0, 255, 0),
            'text': (0, 255, 0),
            'name': 'Green'
        }
    }
    
    def __init__(self):
        self.state = HandState.NOT_DETECTED
        self.stability_history = deque(maxlen=30)
        self.position_history = deque(maxlen=10)
        self.stability_threshold = 12  # pixels
        self.stability_frames_needed = 25
        self.pulse_phase = 0
        self.last_position = None
        self.capture_flash = 0
        self.detection_count = 0
        self.total_frames = 0
        
    def update_state(self, landmarks, finger_pos, is_capturing=False, just_captured=False):
        """Update hand state based on detection and stability"""
        self.total_frames += 1
        
        if landmarks is None or len(landmarks) < 21:
            self.state = HandState.NOT_DETECTED
            self.stability_history.clear()
            self.position_history.clear()
            self.last_position = None
            return
        
        self.detection_count += 1
        
        if just_captured:
            self.state = HandState.CAPTURED
            self.capture_flash = 15  # Flash frames
            return
            
        if is_capturing:
            self.state = HandState.CAPTURING
            return
        
        # Check stability based on position movement
        if finger_pos and self.last_position:
            dx = finger_pos[0] - self.last_position[0]
            dy = finger_pos[1] - self.last_position[1]
            movement = math.sqrt(dx*dx + dy*dy)
            
            self.position_history.append(finger_pos)
            self.stability_history.append(movement < self.stability_threshold)
            
            # Check if stable
            if len(self.stability_history) >= self.stability_frames_needed:
                stable_count = sum(self.stability_history)
                if stable_count >= self.stability_frames_needed * 0.9:
                    self.state = HandState.STABLE
                else:
                    self.state = HandState.DETECTED
            else:
                self.state = HandState.DETECTED
        else:
            self.state = HandState.DETECTED
            
        self.last_position = finger_pos
        
        # Decay capture flash
        if self.capture_flash > 0:
            self.capture_flash -= 1
    
    def get_stability_percentage(self):
        """Returns stability as percentage (0-100)"""
        if not self.stability_history:
            return 0
        return (sum(self.stability_history) / len(self.stability_history)) * 100
    
    def get_detection_rate(self):
        """Returns detection rate as percentage"""
        if self.total_frames == 0:
            return 0
        return (self.detection_count / self.total_frames) * 100
    
    def get_state_name(self):
        """Get human-readable state name"""
        state_names = {
            HandState.NOT_DETECTED: "Not Detected",
            HandState.DETECTED: "Tracking",
            HandState.STABLE: "Stable ✓",
            HandState.CAPTURING: "Capturing...",
            HandState.CAPTURED: "Captured!"
        }
        return state_names.get(self.state, "Unknown")
    
    def get_state_color_name(self):
        """Get color name for current state"""
        return self.COLORS[self.state]['name']
    
    def draw_skeleton(self, frame, landmarks, cam_w, cam_h):
        """Draw the hand skeleton with current state colors"""
        if landmarks is None or len(landmarks) < 21:
            return frame
            
        colors = self.COLORS[self.state]
        
        # Apply capture flash effect
        if self.capture_flash > 0:
            overlay = frame.copy()
            alpha = min(0.4, self.capture_flash / 30)
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), 
                         (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Convert landmarks to pixel coordinates
        points = []
        for lm in landmarks:
            x = int(lm.x * cam_w)
            y = int(lm.y * cam_h)
            points.append((x, y))
        
        # Create overlay for glow effects
        overlay = frame.copy()
        
        # 1. Draw glow layer (thick lines)
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(overlay, points[start_idx], points[end_idx], 
                        colors['glow'], 10)
        
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # 2. Draw main skeleton lines
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(frame, points[start_idx], points[end_idx], 
                        colors['skeleton'], 3)
        
        # 3. Draw joints
        for i, point in enumerate(points):
            if i == 8:  # Index fingertip - special treatment
                self._draw_index_tip(frame, point, colors)
            elif i in self.FINGERTIPS:  # Other fingertips
                cv2.circle(frame, point, 10, colors['glow'], -1)
                cv2.circle(frame, point, 7, colors['fingertip'], -1)
                cv2.circle(frame, point, 10, colors['skeleton'], 2)
            elif i == 0:  # Wrist
                cv2.circle(frame, point, 12, colors['glow'], -1)
                cv2.circle(frame, point, 8, colors['joints'], -1)
                cv2.circle(frame, point, 12, colors['skeleton'], 2)
            else:  # Regular joints
                cv2.circle(frame, point, 5, colors['joints'], -1)
                cv2.circle(frame, point, 6, colors['skeleton'], 1)
        
        return frame
    
    def _draw_index_tip(self, frame, pos, colors):
        """Draw special animated index fingertip indicator"""
        # Pulse animation
        self.pulse_phase = (self.pulse_phase + 0.15) % (2 * math.pi)
        pulse = int(4 + 3 * math.sin(self.pulse_phase))
        
        # Outer glow rings
        for i in range(3):
            alpha = 0.25 - (i * 0.08)
            size = 18 + (i * 6) + pulse
            overlay = frame.copy()
            cv2.circle(overlay, pos, size, colors['glow'], -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Main circle
        cv2.circle(frame, pos, 14, colors['index_tip'], -1)
        cv2.circle(frame, pos, 17, colors['skeleton'], 3)
        
        # Center dot
        cv2.circle(frame, pos, 4, (255, 255, 255), -1)
        
        # Crosshair
        line_length = 22
        gap = 8
        thickness = 2
        
        cv2.line(frame, (pos[0] - line_length, pos[1]), 
                (pos[0] - gap, pos[1]), colors['skeleton'], thickness)
        cv2.line(frame, (pos[0] + gap, pos[1]), 
                (pos[0] + line_length, pos[1]), colors['skeleton'], thickness)
        cv2.line(frame, (pos[0], pos[1] - line_length), 
                (pos[0], pos[1] - gap), colors['skeleton'], thickness)
        cv2.line(frame, (pos[0], pos[1] + gap), 
                (pos[0], pos[1] + line_length), colors['skeleton'], thickness)
    
    def draw_stability_bar(self, frame, pos=(10, 50), width=150):
        """Draw stability meter on frame"""
        stability = self.get_stability_percentage()
        
        # Background
        bar_height = 20
        cv2.rectangle(frame, (pos[0] - 2, pos[1] - 2), 
                     (pos[0] + width + 2, pos[1] + bar_height + 2), 
                     (40, 40, 40), -1)
        cv2.rectangle(frame, (pos[0], pos[1]), 
                     (pos[0] + width, pos[1] + bar_height), 
                     (30, 30, 30), -1)
        
        # Fill
        fill_width = int((width - 4) * (stability / 100))
        
        # Gradient color based on stability
        if stability < 40:
            color = (0, 0, 255)      # Red
        elif stability < 70:
            color = (0, 165, 255)    # Orange
        elif stability < 90:
            color = (0, 255, 255)    # Yellow
        else:
            color = (0, 255, 0)      # Green
            
        if fill_width > 0:
            cv2.rectangle(frame, (pos[0] + 2, pos[1] + 2), 
                         (pos[0] + 2 + fill_width, pos[1] + bar_height - 2), 
                         color, -1)
        
        # Border
        cv2.rectangle(frame, (pos[0], pos[1]), 
                     (pos[0] + width, pos[1] + bar_height), 
                     (100, 100, 100), 1)
        
        # Text
        cv2.putText(frame, f"Stability: {int(stability)}%", 
                   (pos[0] + 5, pos[1] + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def draw_state_badge(self, frame, pos=(10, 80)):
        """Draw current state badge"""
        colors = self.COLORS[self.state]
        text = self.get_state_name()
        
        # Calculate text size
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        # Badge background
        padding = 6
        cv2.rectangle(frame, 
                     (pos[0] - padding, pos[1] - text_height - padding), 
                     (pos[0] + text_width + padding, pos[1] + padding), 
                     (20, 20, 20), -1)
        cv2.rectangle(frame, 
                     (pos[0] - padding, pos[1] - text_height - padding), 
                     (pos[0] + text_width + padding, pos[1] + padding), 
                     colors['skeleton'], 2)
        
        # Text
        cv2.putText(frame, text, (pos[0], pos[1]), 
                   font, font_scale, colors['text'], thickness)
        
        return frame
    
    def reset(self):
        """Reset all state"""
        self.state = HandState.NOT_DETECTED
        self.stability_history.clear()
        self.position_history.clear()
        self.last_position = None
        self.capture_flash = 0
        self.detection_count = 0
        self.total_frames = 0
    
    def reset_stats(self):
        """Reset only stats, keep tracking state"""
        self.detection_count = 0
        self.total_frames = 0
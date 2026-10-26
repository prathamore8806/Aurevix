"""
Holographic HUD - Clean Cyberpunk UI
FIXED: Removed ugly scanlines, cleaner look
"""

import cv2
import math
import time
import numpy as np


class HoloColors:
    """Cyberpunk color palette (BGR)"""
    CYAN = (255, 255, 0)
    CYAN_DARK = (180, 150, 0)
    CYAN_GLOW = (255, 212, 0)
    NEON_GREEN = (0, 255, 100)
    NEON_RED = (0, 0, 255)
    NEON_ORANGE = (0, 149, 255)
    NEON_YELLOW = (0, 255, 255)
    NEON_PURPLE = (255, 0, 191)
    HUD_BG = (30, 30, 30)
    HUD_BORDER = (255, 200, 0)
    TEXT_PRIMARY = (255, 255, 255)
    TEXT_SECONDARY = (200, 200, 200)
    ACTIVE = (0, 255, 100)
    INACTIVE = (100, 100, 100)
    WARNING = (0, 100, 255)
    DESKTOP = (255, 200, 0)
    GAMING = (0, 165, 255)
    DRAW = (255, 0, 191)


class HologramHUD:
    """Clean holographic HUD overlay"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.frame_count = 0
        self.start_time = time.time()
        self.pulse_phase = 0
    
    def update(self):
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        self.pulse_phase = (math.sin(elapsed * 3) + 1) / 2
    
    def draw_scanlines(self, frame, intensity=0.03):
        """DISABLED - No more ugly lines"""
        # Just return frame without scanlines
        return frame
    
    def draw_corner_brackets(self, frame, margin=15, length=40, thickness=2):
        """Draw corner brackets"""
        w, h = self.width, self.height
        color = HoloColors.CYAN
        
        # Top-left
        cv2.line(frame, (margin, margin), (margin + length, margin), color, thickness)
        cv2.line(frame, (margin, margin), (margin, margin + length), color, thickness)
        # Top-right
        cv2.line(frame, (w - margin, margin), (w - margin - length, margin), color, thickness)
        cv2.line(frame, (w - margin, margin), (w - margin, margin + length), color, thickness)
        # Bottom-left
        cv2.line(frame, (margin, h - margin), (margin + length, h - margin), color, thickness)
        cv2.line(frame, (margin, h - margin), (margin, h - margin - length), color, thickness)
        # Bottom-right
        cv2.line(frame, (w - margin, h - margin), (w - margin - length, h - margin), color, thickness)
        cv2.line(frame, (w - margin, h - margin), (w - margin, h - margin - length), color, thickness)
        
        return frame
    
    def draw_top_bar(self, frame, mode, fps, hand_detected):
        """Draw top status bar"""
        bar_height = 40
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, bar_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Bottom border line
        cv2.line(frame, (0, bar_height), (self.width, bar_height), HoloColors.CYAN, 2)
        
        # Mode colors
        mode_colors = {
            "DESKTOP": HoloColors.DESKTOP,
            "GAMING": HoloColors.GAMING,
            "DRAW": HoloColors.DRAW
        }
        mode_color = mode_colors.get(mode, HoloColors.CYAN)
        
        # Mode text (left)
        cv2.putText(frame, f"[{mode}]", (15, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        
        # Status (center)
        if hand_detected:
            status_text = "HAND DETECTED"
            status_color = HoloColors.NEON_GREEN
        else:
            status_text = "NO HAND"
            status_color = HoloColors.WARNING
        
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = (self.width - text_size[0]) // 2
        cv2.putText(frame, status_text, (text_x, 26), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        # FPS (right)
        fps_text = f"FPS: {fps}"
        cv2.putText(frame, fps_text, (self.width - 90, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, HoloColors.CYAN, 1)
        
        return frame
    
    def draw_bottom_bar(self, frame, info_text=""):
        """Draw bottom info bar"""
        bar_height = 30
        y_start = self.height - bar_height
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, y_start), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Top border line
        cv2.line(frame, (0, y_start), (self.width, y_start), HoloColors.CYAN, 1)
        
        # Info text
        if info_text:
            cv2.putText(frame, info_text, (15, y_start + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.TEXT_SECONDARY, 1)
        
        return frame
    
    def draw_tracking_zone(self, frame, mx, mt, mb):
        """Draw tracking zone rectangle"""
        x1 = int(mx * self.width)
        y1 = int(mt * self.height)
        x2 = int((1 - mx) * self.width)
        y2 = int(mb * self.height)
        
        # Simple dotted rectangle
        color = HoloColors.CYAN_DARK
        
        # Draw corners only (cleaner look)
        cs = 20  # Corner size
        thickness = 2
        
        # Top-left corner
        cv2.line(frame, (x1, y1), (x1 + cs, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + cs), color, thickness)
        
        # Top-right corner
        cv2.line(frame, (x2, y1), (x2 - cs, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + cs), color, thickness)
        
        # Bottom-left corner
        cv2.line(frame, (x1, y2), (x1 + cs, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - cs), color, thickness)
        
        # Bottom-right corner
        cv2.line(frame, (x2, y2), (x2 - cs, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - cs), color, thickness)
        
        return frame
    
    def draw_gesture_box(self, frame, gesture, x=10, y=90):
        """Draw gesture indicator"""
        if not gesture or gesture == "NONE":
            return frame
        
        text = gesture
        size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # Background box
        padding = 10
        box_x1 = x
        box_y1 = y - size[1] - padding
        box_x2 = x + size[0] + padding * 2
        box_y2 = y + padding
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Border
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), HoloColors.CYAN, 1)
        
        # Text
        cv2.putText(frame, text, (x + padding, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, HoloColors.NEON_GREEN, 2)
        
        return frame
    
    def draw_action_popup(self, frame, text, color=None):
        """Draw centered action popup"""
        if not text:
            return frame
        
        if color is None:
            color = HoloColors.NEON_GREEN
        
        size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        x = (self.width - size[0]) // 2
        y = self.height // 2
        
        # Background
        padding = 20
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (x - padding, y - size[1] - padding), 
                     (x + size[0] + padding, y + padding), 
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Border
        cv2.rectangle(frame, 
                     (x - padding, y - size[1] - padding), 
                     (x + size[0] + padding, y + padding), 
                     color, 2)
        
        # Text
        cv2.putText(frame, text, (x, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        
        return frame
    
    def draw_hand_panel(self, frame, fingers, handed, gesture):
        """Draw hand info panel"""
        px = self.width - 140
        py = 50
        pw = 130
        ph = 80
        
        # Background
        overlay = frame.copy()
        cv2.rectangle(overlay, (px, py), (px + pw, py + ph), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Border
        cv2.rectangle(frame, (px, py), (px + pw, py + ph), HoloColors.CYAN, 1)
        
        # Title
        cv2.putText(frame, "HAND", (px + 10, py + 18), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.CYAN, 1)
        
        # Hand type
        cv2.putText(frame, handed, (px + 60, py + 18), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.TEXT_SECONDARY, 1)
        
        # Finger indicators
        names = ['T', 'I', 'M', 'R', 'P']
        for i, (n, up) in enumerate(zip(names, fingers)):
            fx = px + 15 + i * 24
            fy = py + 45
            
            if up:
                cv2.circle(frame, (fx, fy), 8, HoloColors.NEON_GREEN, -1)
            else:
                cv2.circle(frame, (fx, fy), 8, HoloColors.INACTIVE, 1)
            
            cv2.putText(frame, n, (fx - 4, fy + 4), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, HoloColors.TEXT_PRIMARY, 1)
        
        # Gesture
        cv2.putText(frame, gesture[:10], (px + 10, py + 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.NEON_YELLOW, 1)
        
        return frame
    
    def draw_dwell_indicator(self, frame, cx, cy, progress):
        """Draw circular dwell progress"""
        radius = 30
        
        # Background circle
        cv2.circle(frame, (cx, cy), radius, HoloColors.INACTIVE, 2)
        
        # Progress arc
        if progress > 0:
            angle = int(360 * progress)
            cv2.ellipse(frame, (cx, cy), (radius, radius), -90, 0, angle, 
                       HoloColors.NEON_GREEN, 3)
        
        # Center dot
        cv2.circle(frame, (cx, cy), 5, HoloColors.NEON_GREEN, -1)
        
        # Progress text
        pct = int(progress * 100)
        cv2.putText(frame, f"{pct}%", (cx - 15, cy + radius + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.TEXT_PRIMARY, 1)
        
        return frame
    
    def draw_cyberpunk_hand(self, frame, hand_landmarks, connections, fingers):
        """Draw hand skeleton"""
        if hand_landmarks is None:
            return frame
        
        h, w = frame.shape[:2]
        lm = hand_landmarks.landmark
        
        # Draw connections (bones)
        for conn in connections:
            s, e = conn
            x1, y1 = int(lm[s].x * w), int(lm[s].y * h)
            x2, y2 = int(lm[e].x * w), int(lm[e].y * h)
            
            # Glow effect
            cv2.line(frame, (x1, y1), (x2, y2), HoloColors.CYAN_DARK, 4)
            cv2.line(frame, (x1, y1), (x2, y2), HoloColors.CYAN, 2)
        
        # Draw landmarks (joints)
        tips = [4, 8, 12, 16, 20]
        for i, l in enumerate(lm):
            x, y = int(l.x * w), int(l.y * h)
            
            if i in tips:
                # Fingertip
                idx = tips.index(i)
                is_up = fingers[idx] if idx < len(fingers) else False
                
                if is_up:
                    # Active fingertip - glowing
                    cv2.circle(frame, (x, y), 10, HoloColors.CYAN_GLOW, 2)
                    cv2.circle(frame, (x, y), 6, HoloColors.NEON_GREEN, -1)
                else:
                    # Inactive fingertip
                    cv2.circle(frame, (x, y), 6, HoloColors.INACTIVE, -1)
            elif i == 0:
                # Wrist
                cv2.circle(frame, (x, y), 8, HoloColors.NEON_PURPLE, -1)
            else:
                # Other joints
                cv2.circle(frame, (x, y), 4, HoloColors.CYAN, -1)
        
        return frame
    
    def draw_cursor(self, frame, cx, cy, mode="move"):
        """Draw cursor indicator"""
        if mode == "drawing":
            # Drawing mode - red pulsing
            cv2.circle(frame, (cx, cy), 12, HoloColors.NEON_RED, 2)
            cv2.circle(frame, (cx, cy), 4, HoloColors.NEON_RED, -1)
        
        elif mode == "ready":
            # Ready mode - green
            cv2.circle(frame, (cx, cy), 12, HoloColors.NEON_GREEN, 2)
            cv2.circle(frame, (cx, cy), 4, HoloColors.NEON_GREEN, -1)
        
        elif mode == "pick":
            # Color pick mode - crosshair
            size = 15
            cv2.line(frame, (cx - size, cy), (cx - 5, cy), HoloColors.NEON_YELLOW, 2)
            cv2.line(frame, (cx + 5, cy), (cx + size, cy), HoloColors.NEON_YELLOW, 2)
            cv2.line(frame, (cx, cy - size), (cx, cy - 5), HoloColors.NEON_YELLOW, 2)
            cv2.line(frame, (cx, cy + 5), (cx, cy + size), HoloColors.NEON_YELLOW, 2)
            cv2.circle(frame, (cx, cy), 3, HoloColors.NEON_YELLOW, -1)
        
        else:
            # Default move mode - cyan
            cv2.circle(frame, (cx, cy), 12, HoloColors.CYAN, 2)
            cv2.circle(frame, (cx, cy), 4, HoloColors.NEON_GREEN, -1)
        
        return frame
    
    def draw_disabled(self, frame, msg="GESTURES DISABLED"):
        """Draw disabled overlay"""
        # Top bar background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, 40), (0, 0, 50), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Warning stripes
        for x in range(0, self.width, 50):
            cv2.line(frame, (x, 38), (x + 25, 38), HoloColors.WARNING, 3)
        
        # Warning text
        cv2.putText(frame, f"! {msg}", (20, 28), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, HoloColors.WARNING, 2)
        
        return frame
    
    def cleanup(self):
        """Cleanup - nothing needed"""
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# 📹 NEW: Preview Helper Methods (Add to end of HologramHUD class)
# ═══════════════════════════════════════════════════════════════════════════════

    def get_hand_data_for_preview(self, hand_landmarks, fingers, handed, gesture):
        """
        Package hand data for preview widget
        Returns dict with all visualization data
        """
        return {
            'hand_landmarks': hand_landmarks,
            'fingers': fingers,
            'handed': handed,
            'gesture': gesture,
            'connections': None  # Will use default in preview
        }
    
    def draw_preview_indicator(self, frame, is_preview_active=False):
        """Draw small indicator showing preview is active"""
        if not is_preview_active:
            return frame
        
        # Small camera icon in top-right
        x = self.width - 50
        y = 50
        
        # Background
        overlay = frame.copy()
        cv2.rectangle(overlay, (x - 5, y - 12), (x + 35, y + 8), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Border
        cv2.rectangle(frame, (x - 5, y - 12), (x + 35, y + 8), HoloColors.NEON_PURPLE, 1)
        
        # Text
        cv2.putText(frame, "REC", (x, y + 3),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, HoloColors.NEON_RED, 1)
        
        # Pulsing dot
        pulse = int((self.pulse_phase) * 255)
        color = (0, 0, min(255, 100 + pulse))
        cv2.circle(frame, (x + 28, y - 2), 4, color, -1)
        
        return frame
import numpy as np
from typing import Optional, Dict, List
from user_gestures import get_active_gestures
import mode_manager
import config

class GestureRecognizer:
    """Recognize user-defined gestures in real-time"""
    
    def __init__(self):
        self.user_gestures = []
        self.last_matched_gesture = None
        self.match_threshold = getattr(config, 'gesture_match_threshold', 75)  # percentage
        self.reload_gestures()
        
    def reload_gestures(self):
        """Reload user gestures from file"""
        current_mode = getattr(mode_manager, 'mode', 'DESKTOP')
        self.user_gestures = get_active_gestures(current_mode)
        print(f"🔄 Loaded {len(self.user_gestures)} gestures for {current_mode} mode")
        
    def match_gesture(self, current_landmarks: List) -> Optional[Dict]:
        """Try to match current hand pose with saved gestures"""
        if not current_landmarks or len(current_landmarks) == 0:
            return None
            
        if not self.user_gestures:
            return None
            
        best_match = None
        best_score = 0
        
        for gesture in self.user_gestures:
            if not gesture.get('enabled', True):
                continue
            score = self._calculate_similarity(current_landmarks, gesture['signature'])
            
            if score > best_score and score >= self.match_threshold:
                best_score = score
                best_match = gesture
                
        if best_match:
            print(f"🎯 Matched: {best_match['name']} ({best_score:.1f}%)")
            
        return best_match
    
    def _calculate_similarity(self, landmarks1: List, landmarks2: List) -> float:
        """Calculate similarity between two landmark sets (0-100)"""
        try:
            # Normalize both landmark sets
            norm1 = self._normalize_landmarks(landmarks1)
            norm2 = self._normalize_landmarks(landmarks2)
            
            # Make sure they have the same shape
            min_len = min(len(norm1), len(norm2))
            norm1 = norm1[:min_len]
            norm2 = norm2[:min_len]
            
            # Calculate Euclidean distance
            distance = np.linalg.norm(norm1 - norm2)
            
            # Convert to similarity score (0-100)
            max_distance = 2.0  # Approximate max distance after normalization
            similarity = max(0, 100 * (1 - distance / max_distance))
            
            return similarity
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0
    
    def _normalize_landmarks(self, landmarks: List) -> np.ndarray:
        """Normalize landmarks to be scale and position invariant"""
        # Convert to numpy array
        if isinstance(landmarks[0], dict):
            # If landmarks are dicts with 'x', 'y', 'z'
            points = np.array([[lm['x'], lm['y'], lm.get('z', 0)] for lm in landmarks])
        elif isinstance(landmarks[0], (list, tuple)):
            # If landmarks are already lists/tuples
            points = np.array(landmarks)
        else:
            # If landmarks are MediaPipe objects
            points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
        
        # Center around wrist (first point)
        centered = points - points[0]
        
        # Scale to unit size
        distances = np.linalg.norm(centered, axis=1)
        scale = np.max(distances)
        
        if scale > 0:
            normalized = centered / scale
        else:
            normalized = centered
            
        return normalized.flatten()
    
    def set_threshold(self, threshold: int):
        """Set match threshold (0-100)"""
        self.match_threshold = max(0, min(100, threshold))

# Global recognizer instance
recognizer = GestureRecognizer()

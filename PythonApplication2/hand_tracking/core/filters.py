"""
Signal Filters - Smoothing and Stabilization
FIXED: Numerical drift, periodic reset
"""

import math
import time
import numpy as np
from collections import deque


class KalmanFilter2D:
    """Kalman filter with drift prevention"""
    
    def __init__(self, process_variance=0.001, measurement_variance=0.1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.update_count = 0
        self.max_covariance = 1e6
        self.reset()
    
    def reset(self):
        self.state = np.array([0.0, 0.0, 0.0, 0.0])
        self.covariance = np.eye(4) * 1000
        self.initialized = False
        self.update_count = 0
        
        self.transition = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float64)
        
        self.measurement = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float64)
    
    def update(self, measurement_x, measurement_y, freeze=False):
        if not self.initialized:
            self.state[0] = measurement_x
            self.state[1] = measurement_y
            self.initialized = True
            return measurement_x, measurement_y
        
        if freeze:
            return self.state[0], self.state[1]
        
        self.update_count += 1
        
        # FIXED: Periodic reset to prevent drift
        if self.update_count % 300 == 0:
            self.covariance = np.clip(self.covariance, -self.max_covariance, self.max_covariance)
            diag = np.diag(self.covariance)
            if np.any(diag > 1e4):
                self.covariance = np.eye(4) * 100
        
        # Prediction
        self.state = self.transition @ self.state
        self.covariance = (self.transition @ self.covariance @ self.transition.T +
                          np.eye(4) * self.process_variance)
        
        # Measurement
        z = np.array([measurement_x, measurement_y])
        y = z - (self.measurement @ self.state)
        
        S = (self.measurement @ self.covariance @ self.measurement.T +
             np.eye(2) * self.measurement_variance)
        
        try:
            K = self.covariance @ self.measurement.T @ np.linalg.inv(S)
        except np.linalg.LinAlgError:
            self.reset()
            self.state[0] = measurement_x
            self.state[1] = measurement_y
            self.initialized = True
            return measurement_x, measurement_y
        
        self.state = self.state + (K @ y)
        self.covariance = (np.eye(4) - K @ self.measurement) @ self.covariance
        
        return self.state[0], self.state[1]


class OneEuroFilter:
    """One Euro Filter with drift prevention"""
    
    def __init__(self, freq=60.0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.update_count = 0
        self.reset()
    
    def reset(self):
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None
        self.update_count = 0
    
    def _alpha(self, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)
    
    def filter(self, x, t=None):
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t or time.time()
            return x
        
        t_now = t or time.time()
        dt = max(t_now - self.t_prev, 1e-6)
        self.freq = min(1.0 / dt, 120.0)
        self.t_prev = t_now
        
        dx = (x - self.x_prev) / dt
        a_d = self._alpha(self.d_cutoff)
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        self.dx_prev = dx_hat
        
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff)
        x_hat = a * x + (1 - a) * self.x_prev
        self.x_prev = x_hat
        
        # FIXED: Periodic soft reset
        self.update_count += 1
        if self.update_count % 500 == 0:
            self.x_prev = x_hat
            self.dx_prev = 0.0
        
        return x_hat


class LandmarkSmoother:
    """Smooths all 21 hand landmarks"""
    
    def __init__(self):
        self.filters = []
        for _ in range(21):
            self.filters.append({
                'x': OneEuroFilter(60, 1.5, 0.01),
                'y': OneEuroFilter(60, 1.5, 0.01),
                'z': OneEuroFilter(60, 1.5, 0.005)
            })
        self.frame_count = 0
    
    def smooth(self, landmarks):
        t = time.time()
        self.frame_count += 1
        
        # FIXED: Periodic reset every 30 seconds
        if self.frame_count % 900 == 0:
            self.reset()
            self.frame_count = 1
        
        class SmoothLandmark:
            def __init__(self, x, y, z):
                self.x, self.y, self.z = x, y, z
        
        result = []
        for i, lm in enumerate(landmarks):
            sx = self.filters[i]['x'].filter(lm.x, t)
            sy = self.filters[i]['y'].filter(lm.y, t)
            sz = self.filters[i]['z'].filter(lm.z, t)
            result.append(SmoothLandmark(sx, sy, sz))
        return result
    
    def reset(self):
        for f in self.filters:
            f['x'].reset()
            f['y'].reset()
            f['z'].reset()


class CursorSmoother:
    """Cursor smoother with Kalman filter"""
    
    def __init__(self):
        self.kalman = KalmanFilter2D(
            process_variance=0.001,
            measurement_variance=0.05
        )
        self.freeze_mode = False
        self.last_pos = (0, 0)
    
    def smooth(self, x, y, freeze=False):
        self.freeze_mode = freeze
        
        if freeze:
            return self.last_pos
        
        sx, sy = self.kalman.update(x, y, freeze=False)
        self.last_pos = (sx, sy)
        return sx, sy
    
    def reset(self):
        self.kalman.reset()
        self.freeze_mode = False
        self.last_pos = (0, 0)


class MovementDetector:
    """Detect hand movement"""
    
    def __init__(self):
        self.history = deque(maxlen=10)
        self.times = deque(maxlen=10)
        self.is_moving = False
        self.move_start = None
        self.still_start = None
        self.velocity = 0.0
        
    def update(self, x, y):
        now = time.time()
        self.history.append((x, y))
        self.times.append(now)
        
        if len(self.history) < 2:
            return False, 0.0, (0, 0)
        
        px, py = self.history[-2]
        dt = max(now - self.times[-2], 1e-6)
        dx, dy = x - px, y - py
        dist = math.sqrt(dx*dx + dy*dy)
        self.velocity = dist / dt
        
        direction = (dx/dist, dy/dist) if dist > 0.01 else (0, 0)
        avg_vel = self._avg_velocity()
        
        if avg_vel > 3.0:
            if not self.is_moving:
                if self.move_start is None:
                    self.move_start = now
                elif now - self.move_start > 0.02:
                    self.is_moving = True
                    self.still_start = None
            else:
                self.still_start = None
        elif avg_vel < 1.5:
            if self.is_moving:
                if self.still_start is None:
                    self.still_start = now
                elif now - self.still_start > 0.08:
                    self.is_moving = False
                    self.move_start = None
            else:
                self.move_start = None
        
        return self.is_moving, self.velocity, direction
    
    def _avg_velocity(self):
        if len(self.history) < 3:
            return 0.0
        total = 0.0
        for i in range(1, len(self.history)):
            x1, y1 = self.history[i-1]
            x2, y2 = self.history[i]
            total += math.sqrt((x2-x1)**2 + (y2-y1)**2)
        dt = self.times[-1] - self.times[0]
        return total / dt if dt > 0 else 0.0
    
    def reset(self):
        self.history.clear()
        self.times.clear()
        self.is_moving = False
        self.move_start = None
        self.still_start = None
        self.velocity = 0.0
    
    def force_stop(self):
        self.is_moving = False
        self.move_start = None


class DrawResult:
    def __init__(self):
        self.state = "IDLE"
        self.should_draw = False
        self.smooth_x = 0
        self.smooth_y = 0
        self.velocity = 0.0
        self.direction = (0, 0)
        self.draw_points = []
        self.was_drawing = False


class DrawModeTracker:
    """Tracks drawing state"""
    
    def __init__(self):
        self.is_drawing = False
        self.pen_down = False
        self.last_x = None
        self.last_y = None
        self.detector = MovementDetector()
        self.fx = OneEuroFilter(60, 1.8, 0.08)
        self.fy = OneEuroFilter(60, 1.8, 0.08)
        
    def reset(self):
        self.is_drawing = False
        self.pen_down = False
        self.last_x = None
        self.last_y = None
        self.detector.reset()
        self.fx.reset()
        self.fy.reset()
    
    def lift_pen(self):
        self.is_drawing = False
        self.pen_down = False
        self.last_x = None
        self.last_y = None
        self.detector.force_stop()
    
    def update(self, sx, sy, finger_up):
        result = DrawResult()
        
        if not finger_up:
            was = self.is_drawing
            self.lift_pen()
            result.state = "IDLE"
            result.was_drawing = was
            return result
        
        self.pen_down = True
        t = time.time()
        
        smooth_x = self.fx.filter(sx, t)
        smooth_y = self.fy.filter(sy, t)
        
        is_moving, vel, direction = self.detector.update(smooth_x, smooth_y)
        
        result.smooth_x = int(smooth_x)
        result.smooth_y = int(smooth_y)
        result.velocity = vel
        result.direction = direction
        
        if is_moving:
            if not self.is_drawing:
                self.is_drawing = True
                self.last_x = result.smooth_x
                self.last_y = result.smooth_y
                result.state = "START"
                result.should_draw = False
            else:
                result.state = "DRAWING"
                result.should_draw = True
                
                if self.last_x is not None:
                    result.draw_points = self._interpolate(
                        self.last_x, self.last_y,
                        result.smooth_x, result.smooth_y
                    )
                else:
                    result.draw_points = [(result.smooth_x, result.smooth_y)]
                
                self.last_x = result.smooth_x
                self.last_y = result.smooth_y
        else:
            if self.is_drawing:
                result.state = "STOPPED"
                result.was_drawing = True
                self.is_drawing = False
            else:
                result.state = "READY"
            
            result.should_draw = False
            self.last_x = result.smooth_x
            self.last_y = result.smooth_y
        
        return result
    
    def _interpolate(self, x1, y1, x2, y2):
        dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if dist < 1:
            return [(x2, y2)]
        
        n = max(1, int(dist / 3))
        points = []
        for i in range(1, n + 1):
            t = i / n
            t = t * t * (3 - 2 * t)
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            points.append((x, y))
        return points
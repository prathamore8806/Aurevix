# calibration_analytics.py - Session analytics and history
import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any


@dataclass
class CalibrationSession:
    """Record of a calibration session"""
    timestamp: str
    duration_seconds: float
    points_captured: int
    accuracy_score: float
    stability_avg: float
    fps_avg: float
    retries: int
    profile_used: Optional[str]
    camera_index: int
    success: bool
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CalibrationSession':
        return cls(**data)


@dataclass  
class LiveStats:
    """Real-time statistics"""
    fps: float = 0.0
    detection_rate: float = 0.0
    stability: float = 0.0
    quality: str = "Unknown"
    session_duration: float = 0.0
    points_captured: int = 0
    retries: int = 0
    state: str = "Idle"


class CalibrationAnalytics:
    """Track calibration performance"""
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path.home() / ".gesture_control" / "calibration_analytics"
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "history.json"
        
        self.history: List[CalibrationSession] = []
        self.current_session: Optional[dict] = None
        self.live_stats = LiveStats()
        
        # Tracking buffers
        self.fps_samples: List[float] = []
        self.stability_samples: List[float] = []
        self.detection_samples: List[bool] = []
        
        self._load_history()
        
    def _load_history(self):
        """Load history from disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [CalibrationSession.from_dict(s) for s in data]
                print(f"📊 Loaded {len(self.history)} calibration sessions")
            except Exception as e:
                print(f"⚠️ Error loading history: {e}")
                self.history = []
                
    def _save_history(self):
        """Save history to disk"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump([s.to_dict() for s in self.history], f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
            
    def start_session(self, camera_index: int = 0, profile_name: str = None):
        """Start tracking new session"""
        self.current_session = {
            'start_time': datetime.now(),
            'points': 0,
            'stability_samples': [],
            'fps_samples': [],
            'retries': 0,
            'camera_index': camera_index,
            'profile': profile_name
        }
        
        self.fps_samples.clear()
        self.stability_samples.clear()
        self.detection_samples.clear()
        
        self.live_stats = LiveStats()
        print("📊 Calibration session started")
        
    def record_point(self, stability: float):
        """Record captured point"""
        if self.current_session:
            self.current_session['points'] += 1
            self.current_session['stability_samples'].append(stability)
            self.live_stats.points_captured = self.current_session['points']
            
    def record_retry(self):
        """Record retry attempt"""
        if self.current_session:
            self.current_session['retries'] += 1
            self.live_stats.retries = self.current_session['retries']
            
    def update_live_stats(self, fps: float, hand_detected: bool, stability: float, state: str = ""):
        """Update real-time stats"""
        # FPS
        self.live_stats.fps = fps
        self.fps_samples.append(fps)
        if len(self.fps_samples) > 60:
            self.fps_samples.pop(0)
        
        # Detection rate
        self.detection_samples.append(hand_detected)
        if len(self.detection_samples) > 100:
            self.detection_samples.pop(0)
        self.live_stats.detection_rate = (sum(self.detection_samples) / len(self.detection_samples)) * 100
        
        # Stability
        if hand_detected:
            self.stability_samples.append(stability)
            if len(self.stability_samples) > 50:
                self.stability_samples.pop(0)
        if self.stability_samples:
            self.live_stats.stability = statistics.mean(self.stability_samples)
            
        # Quality assessment
        self.live_stats.quality = self._assess_quality()
        
        # State
        if state:
            self.live_stats.state = state
        
        # Session duration
        if self.current_session:
            elapsed = (datetime.now() - self.current_session['start_time']).total_seconds()
            self.live_stats.session_duration = elapsed
            
    def _assess_quality(self) -> str:
        """Assess tracking quality"""
        detection = self.live_stats.detection_rate
        stability = self.live_stats.stability
        
        if detection >= 95 and stability >= 90:
            return "Excellent ⭐⭐⭐"
        elif detection >= 85 and stability >= 75:
            return "Good ⭐⭐"
        elif detection >= 70 and stability >= 60:
            return "Fair ⭐"
        elif detection >= 50:
            return "Poor ⚠️"
        else:
            return "Bad ❌"
            
    def end_session(self, success: bool, accuracy: float = 0) -> Optional[CalibrationSession]:
        """End session and save"""
        if not self.current_session:
            return None
            
        duration = (datetime.now() - self.current_session['start_time']).total_seconds()
        
        fps_avg = statistics.mean(self.fps_samples) if self.fps_samples else 0
        stability_avg = statistics.mean(self.current_session['stability_samples']) if self.current_session['stability_samples'] else 0
        
        session = CalibrationSession(
            timestamp=self.current_session['start_time'].isoformat(),
            duration_seconds=round(duration, 2),
            points_captured=self.current_session['points'],
            accuracy_score=round(accuracy, 2),
            stability_avg=round(stability_avg, 2),
            fps_avg=round(fps_avg, 1),
            retries=self.current_session['retries'],
            profile_used=self.current_session['profile'],
            camera_index=self.current_session['camera_index'],
            success=success
        )
        
        self.history.append(session)
        self._save_history()
        
        self.current_session = None
        print(f"📊 Session ended - Success: {success}, Accuracy: {accuracy:.1f}%")
        return session
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        if not self.history:
            return {
                'total_sessions': 0,
                'success_rate': 0,
                'avg_accuracy': 0,
                'avg_duration': 0,
                'best_accuracy': 0
            }
            
        successful = [s for s in self.history if s.success]
        
        return {
            'total_sessions': len(self.history),
            'success_rate': round(len(successful) / len(self.history) * 100, 1),
            'avg_accuracy': round(statistics.mean([s.accuracy_score for s in successful]), 1) if successful else 0,
            'avg_duration': round(statistics.mean([s.duration_seconds for s in self.history]), 1),
            'best_accuracy': round(max([s.accuracy_score for s in successful]), 1) if successful else 0,
            'avg_retries': round(statistics.mean([s.retries for s in self.history]), 1)
        }
        
    def get_recent_history(self, limit: int = 10) -> List[CalibrationSession]:
        """Get recent sessions"""
        return self.history[-limit:][::-1]
        
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self._save_history()
        print("🗑️ History cleared")
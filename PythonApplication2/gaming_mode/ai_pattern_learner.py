"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 AI PATTERN LEARNER - MACHINE LEARNING                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  📊 Learns user gesture patterns and performance                             ║
║  🎯 Adapts difficulty based on skill level                                   ║
║  💾 Saves/loads training progress                                            ║
║  📈 Provides personalized recommendations                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import time
from pathlib import Path
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# GESTURE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class GestureDirection(Enum):
    """Gesture directions for AI Trainer"""
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    NONE = "NONE"


class DifficultyLevel(Enum):
    """Difficulty levels"""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GestureStats:
    """Statistics for a single gesture direction"""
    direction: str
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    avg_reaction_time: float = 0.0
    fastest_reaction: float = float('inf')
    slowest_reaction: float = 0.0
    consecutive_successes: int = 0
    max_streak: int = 0
    last_practiced: float = field(default_factory=time.time)
    
    # Learning metrics
    difficulty_rating: float = 0.5  # 0.0 = easy, 1.0 = hard
    mastery_level: float = 0.0      # 0.0 = beginner, 1.0 = expert
    
    def update_success(self, reaction_time: float):
        """Update stats on successful gesture"""
        self.total_attempts += 1
        self.successful_attempts += 1
        self.consecutive_successes += 1
        self.max_streak = max(self.max_streak, self.consecutive_successes)
        
        # Update reaction times
        total = self.total_attempts
        self.avg_reaction_time = (self.avg_reaction_time * (total - 1) + reaction_time) / total
        self.fastest_reaction = min(self.fastest_reaction, reaction_time)
        self.slowest_reaction = max(self.slowest_reaction, reaction_time)
        
        # Update mastery
        self._update_mastery()
        self.last_practiced = time.time()
    
    def update_failure(self):
        """Update stats on failed gesture"""
        self.total_attempts += 1
        self.failed_attempts += 1
        self.consecutive_successes = 0
        
        # Update mastery
        self._update_mastery()
        self.last_practiced = time.time()
    
    def _update_mastery(self):
        """Calculate mastery level based on performance"""
        if self.total_attempts == 0:
            self.mastery_level = 0.0
            return
        
        # Success rate component (40%)
        success_rate = self.successful_attempts / self.total_attempts
        
        # Streak component (30%)
        streak_score = min(1.0, self.max_streak / 10.0)
        
        # Reaction time component (30%)
        if self.avg_reaction_time > 0:
            # Faster = better (under 1 second is good)
            reaction_score = max(0.0, 1.0 - (self.avg_reaction_time / 2.0))
        else:
            reaction_score = 0.0
        
        # Calculate mastery
        self.mastery_level = (
            success_rate * 0.4 +
            streak_score * 0.3 +
            reaction_score * 0.3
        )
        
        # Calculate difficulty (inverse of mastery)
        self.difficulty_rating = 1.0 - self.mastery_level
    
    def success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_attempts == 0:
            return 0.0
        return self.successful_attempts / self.total_attempts
    
    def needs_practice(self) -> bool:
        """Check if this gesture needs more practice"""
        return (
            self.mastery_level < 0.6 or
            self.success_rate() < 0.7 or
            self.total_attempts < 10
        )


@dataclass
class TrainingSession:
    """Single training session data"""
    session_id: str
    start_time: float
    end_time: float = 0.0
    gestures_performed: Dict[str, int] = field(default_factory=dict)
    total_score: int = 0
    max_streak: int = 0
    difficulty_level: str = "BEGINNER"
    duration_seconds: float = 0.0
    
    def finalize(self):
        """Finalize the session"""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time


@dataclass
class LearningProfile:
    """User's overall learning profile"""
    total_sessions: int = 0
    total_gestures: int = 0
    total_score: int = 0
    overall_success_rate: float = 0.0
    current_difficulty: str = "BEGINNER"
    strongest_gesture: str = "NONE"
    weakest_gesture: str = "NONE"
    total_playtime_seconds: float = 0.0
    created_at: float = field(default_factory=time.time)
    last_played: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════════════════════════════════════
# AI PATTERN LEARNER - MAIN CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AIPatternLearner:
    """
    🤖 AI Pattern Learning System
    
    Learns user's gesture performance patterns and adapts training accordingly.
    
    Features:
    - Tracks accuracy for each gesture direction
    - Learns reaction time patterns
    - Adapts difficulty based on skill level
    - Identifies weak areas for focused practice
    - Saves/loads training progress
    """
    
    def __init__(self, save_dir: str = "gaming_mode/ai_training_data"):
        """Initialize AI Pattern Learner"""
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Gesture statistics
        self.gesture_stats: Dict[str, GestureStats] = {}
        self._initialize_stats()
        
        # Session tracking
        self.current_session: Optional[TrainingSession] = None
        self.session_history: List[TrainingSession] = []
        
        # Learning profile
        self.profile = LearningProfile()
        
        # Real-time tracking
        self.recent_performance = deque(maxlen=50)  # Last 50 attempts
        self.gesture_queue = deque(maxlen=10)  # Upcoming gestures
        
        # Timing
        self.last_instruction_time = 0.0
        
        # Load existing data
        self.load_progress()
        
        print("🤖 AI Pattern Learner initialized")
        print(f"   Save directory: {self.save_dir}")
        print(f"   Total sessions: {self.profile.total_sessions}")
        print(f"   Current difficulty: {self.profile.current_difficulty}")
    
    def _initialize_stats(self):
        """Initialize stats for all gesture directions"""
        for direction in GestureDirection:
            if direction != GestureDirection.NONE:
                self.gesture_stats[direction.value] = GestureStats(direction.value)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_session(self):
        """Start a new training session"""
        session_id = f"session_{int(time.time())}"
        self.current_session = TrainingSession(
            session_id=session_id,
            start_time=time.time(),
            difficulty_level=self.profile.current_difficulty
        )
        self.profile.total_sessions += 1
        print(f"🎓 Training session started: {session_id}")
    
    def end_session(self):
        """End current training session"""
        if not self.current_session:
            return
        
        self.current_session.finalize()
        
        # Update profile
        self.profile.total_playtime_seconds += self.current_session.duration_seconds
        self.profile.last_played = time.time()
        
        # Save session
        self.session_history.append(self.current_session)
        
        # Update overall stats
        self._update_profile()
        
        # Save progress
        self.save_progress()
        
        duration = self.current_session.duration_seconds
        print(f"✅ Session ended")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Score: {self.current_session.total_score}")
        print(f"   Max streak: {self.current_session.max_streak}")
        
        self.current_session = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GESTURE TRACKING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def record_gesture(
        self,
        direction: str,
        success: bool,
        reaction_time: float = 0.0
    ):
        """
        Record a gesture attempt
        
        Args:
            direction: Gesture direction (UP/DOWN/LEFT/RIGHT)
            success: Whether gesture was correct
            reaction_time: Time taken to perform gesture
        """
        if direction not in self.gesture_stats:
            self.gesture_stats[direction] = GestureStats(direction)
        
        stats = self.gesture_stats[direction]
        
        # Update stats
        if success:
            stats.update_success(reaction_time)
        else:
            stats.update_failure()
        
        # Update profile
        self.profile.total_gestures += 1
        
        # Track in session
        if self.current_session:
            self.current_session.gestures_performed[direction] = \
                self.current_session.gestures_performed.get(direction, 0) + 1
        
        # Track recent performance
        self.recent_performance.append({
            'direction': direction,
            'success': success,
            'reaction_time': reaction_time,
            'timestamp': time.time()
        })
        
        print(f"  📊 Recorded {direction}: {'✅' if success else '❌'} "
              f"({reaction_time:.2f}s) - Mastery: {stats.mastery_level:.1%}")
    
    def start_gesture_timing(self):
        """Mark the start of a gesture instruction"""
        self.last_instruction_time = time.time()
    
    def get_reaction_time(self) -> float:
        """Get reaction time since instruction was shown"""
        if self.last_instruction_time == 0:
            return 0.0
        return time.time() - self.last_instruction_time
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ADAPTIVE DIFFICULTY
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_next_gesture(self) -> str:
        """
        Get next gesture to practice (AI-selected based on performance)
        
        Returns:
            str: Gesture direction that needs practice
        """
        # Get gestures sorted by difficulty (hardest first)
        gestures_by_difficulty = sorted(
            self.gesture_stats.items(),
            key=lambda x: (x[1].mastery_level, -x[1].total_attempts)
        )
        
        # Weight selection towards weaker gestures
        weights = []
        gestures = []
        
        for direction, stats in gestures_by_difficulty:
            # Higher weight for gestures that need practice
            weight = 1.0 + (1.0 - stats.mastery_level) * 2.0
            
            # Boost weight if not practiced recently
            time_since = time.time() - stats.last_practiced
            if time_since > 60:  # Not practiced in last minute
                weight *= 1.5
            
            weights.append(weight)
            gestures.append(direction)
        
        # Weighted random selection
        import random
        total_weight = sum(weights)
        rand = random.uniform(0, total_weight)
        
        cumulative = 0
        for gesture, weight in zip(gestures, weights):
            cumulative += weight
            if rand <= cumulative:
                return gesture
        
        # Fallback
        return gestures[0] if gestures else "UP"
    
    def get_recommended_difficulty(self) -> DifficultyLevel:
        """Get recommended difficulty level based on performance"""
        avg_mastery = sum(s.mastery_level for s in self.gesture_stats.values()) / len(self.gesture_stats)
        
        if avg_mastery < 0.4:
            return DifficultyLevel.BEGINNER
        elif avg_mastery < 0.6:
            return DifficultyLevel.INTERMEDIATE
        elif avg_mastery < 0.8:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT
    
    def should_increase_difficulty(self) -> bool:
        """Check if difficulty should be increased"""
        # Need at least 20 total gestures
        if self.profile.total_gestures < 20:
            return False
        
        # Check recent performance (last 20 attempts)
        recent = list(self.recent_performance)[-20:]
        if len(recent) < 20:
            return False
        
        success_count = sum(1 for p in recent if p['success'])
        success_rate = success_count / len(recent)
        
        # If 90%+ success rate, increase difficulty
        return success_rate >= 0.9
    
    def should_decrease_difficulty(self) -> bool:
        """Check if difficulty should be decreased"""
        # Check recent performance
        recent = list(self.recent_performance)[-20:]
        if len(recent) < 20:
            return False
        
        success_count = sum(1 for p in recent if p['success'])
        success_rate = success_count / len(recent)
        
        # If below 50% success rate, decrease difficulty
        return success_rate < 0.5
    
    def get_speed_multiplier(self) -> float:
        """Get game speed multiplier based on skill level"""
        avg_mastery = sum(s.mastery_level for s in self.gesture_stats.values()) / len(self.gesture_stats)
        
        # Speed ranges from 0.6 (beginner) to 1.5 (expert)
        return 0.6 + (avg_mastery * 0.9)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_weakest_gestures(self, count: int = 3) -> List[Tuple[str, float]]:
        """
        Get weakest gestures that need practice
        
        Returns:
            List of (gesture, mastery_level) tuples
        """
        sorted_gestures = sorted(
            self.gesture_stats.items(),
            key=lambda x: x[1].mastery_level
        )
        return [(g, s.mastery_level) for g, s in sorted_gestures[:count]]
    
    def get_strongest_gestures(self, count: int = 3) -> List[Tuple[str, float]]:
        """Get strongest gestures"""
        sorted_gestures = sorted(
            self.gesture_stats.items(),
            key=lambda x: x[1].mastery_level,
            reverse=True
        )
        return [(g, s.mastery_level) for g, s in sorted_gestures[:count]]
    
    def get_overall_stats(self) -> Dict:
        """Get comprehensive statistics"""
        total_attempts = sum(s.total_attempts for s in self.gesture_stats.values())
        total_successes = sum(s.successful_attempts for s in self.gesture_stats.values())
        
        avg_mastery = sum(s.mastery_level for s in self.gesture_stats.values()) / len(self.gesture_stats)
        
        weakest = self.get_weakest_gestures(1)
        strongest = self.get_strongest_gestures(1)
        
        return {
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'success_rate': total_successes / total_attempts if total_attempts > 0 else 0,
            'avg_mastery': avg_mastery,
            'weakest_gesture': weakest[0][0] if weakest else "NONE",
            'weakest_mastery': weakest[0][1] if weakest else 0.0,
            'strongest_gesture': strongest[0][0] if strongest else "NONE",
            'strongest_mastery': strongest[0][1] if strongest else 0.0,
            'total_sessions': self.profile.total_sessions,
            'total_playtime': self.profile.total_playtime_seconds,
            'current_difficulty': self.profile.current_difficulty,
        }
    
    def get_gesture_report(self) -> Dict[str, Dict]:
        """Get detailed report for each gesture"""
        report = {}
        for direction, stats in self.gesture_stats.items():
            report[direction] = {
                'total_attempts': stats.total_attempts,
                'success_rate': stats.success_rate(),
                'mastery_level': stats.mastery_level,
                'avg_reaction_time': stats.avg_reaction_time,
                'fastest_reaction': stats.fastest_reaction if stats.fastest_reaction != float('inf') else 0,
                'max_streak': stats.max_streak,
                'needs_practice': stats.needs_practice(),
            }
        return report
    
    def get_recent_performance_trend(self, window: int = 20) -> str:
        """Analyze recent performance trend"""
        recent = list(self.recent_performance)[-window:]
        
        if len(recent) < 10:
            return "INSUFFICIENT_DATA"
        
        # Compare first half vs second half
        mid = len(recent) // 2
        first_half = recent[:mid]
        second_half = recent[mid:]
        
        first_success = sum(1 for p in first_half if p['success']) / len(first_half)
        second_success = sum(1 for p in second_half if p['success']) / len(second_half)
        
        diff = second_success - first_success
        
        if diff > 0.15:
            return "IMPROVING"
        elif diff < -0.15:
            return "DECLINING"
        else:
            return "STABLE"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PROFILE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update_profile(self):
        """Update learning profile with current stats"""
        stats = self.get_overall_stats()
        
        self.profile.overall_success_rate = stats['success_rate']
        self.profile.total_score = sum(s.total_score for s in self.session_history)
        self.profile.weakest_gesture = stats['weakest_gesture']
        self.profile.strongest_gesture = stats['strongest_gesture']
        
        # Update difficulty
        recommended = self.get_recommended_difficulty()
        self.profile.current_difficulty = recommended.value
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DATA PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_progress(self, filename: str = "ai_learning_progress.json"):
        """Save all learning data"""
        try:
            data = {
                'gesture_stats': {
                    direction: asdict(stats)
                    for direction, stats in self.gesture_stats.items()
                },
                'session_history': [
                    asdict(session) for session in self.session_history[-50:]  # Keep last 50 sessions
                ],
                'profile': asdict(self.profile),
                'last_updated': time.time()
            }
            
            save_path = self.save_dir / filename
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Progress saved to {save_path}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to save progress: {e}")
            return False
    
    def load_progress(self, filename: str = "ai_learning_progress.json"):
        """Load learning data"""
        try:
            load_path = self.save_dir / filename
            
            if not load_path.exists():
                print(f"ℹ️  No existing progress found")
                return False
            
            with open(load_path, 'r') as f:
                data = json.load(f)
            
            # Load gesture stats
            for direction, stats_dict in data.get('gesture_stats', {}).items():
                self.gesture_stats[direction] = GestureStats(**stats_dict)
            
            # Load session history
            for session_dict in data.get('session_history', []):
                self.session_history.append(TrainingSession(**session_dict))
            
            # Load profile
            profile_data = data.get('profile', {})
            if profile_data:
                self.profile = LearningProfile(**profile_data)
            
            print(f"📂 Progress loaded")
            print(f"   Sessions: {len(self.session_history)}")
            print(f"   Total gestures: {self.profile.total_gestures}")
            
            return True
        
        except Exception as e:
            print(f"❌ Failed to load progress: {e}")
            return False
    
    def reset_progress(self):
        """Reset all learning data"""
        self.gesture_stats.clear()
        self._initialize_stats()
        self.session_history.clear()
        self.recent_performance.clear()
        self.profile = LearningProfile()
        print("🔄 Progress reset")
    
    def export_report(self, filename: str = "training_report.txt"):
        """Export human-readable report"""
        try:
            report_path = self.save_dir / filename
            
            with open(report_path, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("AI PATTERN LEARNER - TRAINING REPORT\n")
                f.write("=" * 70 + "\n\n")
                
                # Overall stats
                stats = self.get_overall_stats()
                f.write("OVERALL PERFORMANCE\n")
                f.write("-" * 70 + "\n")
                f.write(f"Total Attempts:     {stats['total_attempts']}\n")
                f.write(f"Success Rate:       {stats['success_rate']:.1%}\n")
                f.write(f"Average Mastery:    {stats['avg_mastery']:.1%}\n")
                f.write(f"Total Sessions:     {stats['total_sessions']}\n")
                f.write(f"Total Playtime:     {stats['total_playtime']:.0f}s\n")
                f.write(f"Current Difficulty: {stats['current_difficulty']}\n")
                f.write("\n")
                
                # Gesture breakdown
                f.write("GESTURE PERFORMANCE\n")
                f.write("-" * 70 + "\n")
                report = self.get_gesture_report()
                for direction, data in sorted(report.items()):
                    f.write(f"\n{direction}:\n")
                    f.write(f"  Attempts:        {data['total_attempts']}\n")
                    f.write(f"  Success Rate:    {data['success_rate']:.1%}\n")
                    f.write(f"  Mastery Level:   {data['mastery_level']:.1%}\n")
                    f.write(f"  Avg Reaction:    {data['avg_reaction_time']:.2f}s\n")
                    f.write(f"  Fastest:         {data['fastest_reaction']:.2f}s\n")
                    f.write(f"  Max Streak:      {data['max_streak']}\n")
                    f.write(f"  Needs Practice:  {'YES' if data['needs_practice'] else 'NO'}\n")
                
                f.write("\n" + "=" * 70 + "\n")
            
            print(f"📄 Report exported to {report_path}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to export report: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

ai_learner = AIPatternLearner()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def start_training_session():
    """Start a training session"""
    ai_learner.start_session()

def end_training_session():
    """End training session"""
    ai_learner.end_session()

def record_gesture(direction: str, success: bool, reaction_time: float = 0.0):
    """Quick record a gesture"""
    ai_learner.record_gesture(direction, success, reaction_time)

def get_next_challenge() -> str:
    """Get next gesture to practice"""
    return ai_learner.get_next_gesture()

def print_stats():
    """Print current statistics"""
    stats = ai_learner.get_overall_stats()
    print("\n" + "=" * 70)
    print("AI LEARNER STATISTICS")
    print("=" * 70)
    for key, value in stats.items():
        if isinstance(value, float) and 'rate' in key or 'mastery' in key:
            print(f"{key:20}: {value:.1%}")
        elif isinstance(value, float):
            print(f"{key:20}: {value:.2f}")
        else:
            print(f"{key:20}: {value}")
    print("=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (FOR TESTING)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🤖 AI Pattern Learner - Standalone Test\n")
    
    # Simulate training
    ai_learner.start_session()
    
    import random
    directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    
    for i in range(50):
        direction = random.choice(directions)
        success = random.random() > 0.3
        reaction_time = random.uniform(0.5, 2.0)
        
        ai_learner.record_gesture(direction, success, reaction_time)
    
    ai_learner.end_session()
    
    # Print stats
    print_stats()
    
    # Show recommendations
    print("\nWEAKEST GESTURES (need practice):")
    for gesture, mastery in ai_learner.get_weakest_gestures():
        print(f"  {gesture}: {mastery:.1%} mastery")
    
    print("\nSTRONGEST GESTURES:")
    for gesture, mastery in ai_learner.get_strongest_gestures():
        print(f"  {gesture}: {mastery:.1%} mastery")
    
    print(f"\nRECOMMENDED DIFFICULTY: {ai_learner.get_recommended_difficulty().value}")
    print(f"NEXT GESTURE TO PRACTICE: {ai_learner.get_next_gesture()}")
    
    # Export reports
    ai_learner.save_progress()
    ai_learner.export_report()
    
    print("\n✅ Test complete!")
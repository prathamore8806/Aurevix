"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 AI TRAINER GAME - ENHANCED VERSION                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🧠 AI-Powered Adaptive Learning                                             ║
║  📊 Real-time Performance Analytics                                          ║
║  🎯 Personalized Training Focus                                              ║
║  📈 Progressive Difficulty System                                            ║
║  💾 Saves Learning Progress                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Signal, QRectF, Slot
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath
)
import random
import math
import time
from enum import Enum
from collections import deque


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS - AI PATTERN LEARNER
# ═══════════════════════════════════════════════════════════════════════════════

AI_LEARNER_AVAILABLE = False
ai_learner = None

try:
    from gaming_mode.ai_pattern_learner import AIPatternLearner, ai_learner as global_ai_learner
    ai_learner = global_ai_learner
    AI_LEARNER_AVAILABLE = True
    print("  ✅ AI Pattern Learner loaded")
except ImportError as e:
    print(f"  ⚠️ AI Pattern Learner not available: {e}")
except Exception as e:
    print(f"  ⚠️ AI Learner error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Direction(Enum):
    NONE = "NONE"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class TrainerState(Enum):
    WELCOME = "welcome"
    RUNNING = "running"
    INSTRUCTION = "instruction"
    SUCCESS = "success"
    GAME_OVER = "game_over"
    ANALYTICS = "analytics"  # NEW: Show analytics screen


class ObstacleType(Enum):
    JUMP = "jump"
    SLIDE = "slide"
    LEFT = "left"
    RIGHT = "right"


class DifficultyMode(Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"
    AI_ADAPTIVE = "AI_ADAPTIVE"  # NEW: AI-controlled difficulty


# ═══════════════════════════════════════════════════════════════════════════════
# INSTRUCTION DATA
# ═══════════════════════════════════════════════════════════════════════════════

INSTRUCTIONS = {
    ObstacleType.JUMP: {
        "icon": "▲",
        "text": "JUMP UP!",
        "hint": "Move your hand UP",
        "direction": "UP",
        "color": QColor(0, 255, 136),
    },
    ObstacleType.SLIDE: {
        "icon": "▼",
        "text": "SLIDE DOWN!",
        "hint": "Move your hand DOWN",
        "direction": "DOWN",
        "color": QColor(255, 165, 0),
    },
    ObstacleType.LEFT: {
        "icon": "◀",
        "text": "MOVE LEFT!",
        "hint": "Move your hand LEFT",
        "direction": "LEFT",
        "color": QColor(0, 200, 255),
    },
    ObstacleType.RIGHT: {
        "icon": "▶",
        "text": "MOVE RIGHT!",
        "hint": "Move your hand RIGHT",
        "direction": "RIGHT",
        "color": QColor(255, 100, 200),
    },
}

# Map direction to obstacle type
DIRECTION_TO_OBSTACLE = {
    "UP": ObstacleType.JUMP,
    "DOWN": ObstacleType.SLIDE,
    "LEFT": ObstacleType.LEFT,
    "RIGHT": ObstacleType.RIGHT,
}


# ═══════════════════════════════════════════════════════════════════════════════
# TRAINER OBSTACLE
# ═══════════════════════════════════════════════════════════════════════════════

class TrainerObstacle:
    """Obstacle in the AI Trainer game"""
    
    def __init__(self, obs_type, y=-80):
        self.type = obs_type
        self.y = y
        self.cleared = False
        self.instruction_shown = False
        self.spawn_time = time.time()
    
    def update(self, speed):
        self.y += speed
    
    def get_direction(self) -> str:
        """Get the direction needed to clear this obstacle"""
        return INSTRUCTIONS[self.type]['direction']


# ═══════════════════════════════════════════════════════════════════════════════
# TRAINER PLAYER
# ═══════════════════════════════════════════════════════════════════════════════

class TrainerPlayer:
    """Player character for AI Trainer"""
    
    def __init__(self):
        self.lane = 1
        self.x_offset = 0
        self.y_offset = 0
        self.is_jumping = False
        self.is_sliding = False
        self.jump_frame = 0
        self.slide_frame = 0
        self.action_animation = 0
    
    def update(self):
        target_x = (self.lane - 1) * 100
        self.x_offset += (target_x - self.x_offset) * 0.3
        
        if self.is_jumping:
            self.jump_frame += 1
            progress = self.jump_frame / 20
            self.y_offset = -80 * math.sin(progress * math.pi)
            if self.jump_frame >= 20:
                self.is_jumping = False
                self.jump_frame = 0
                self.y_offset = 0
        
        if self.is_sliding:
            self.slide_frame += 1
            if self.slide_frame >= 15:
                self.is_sliding = False
                self.slide_frame = 0
    
    def jump(self):
        if not self.is_jumping and not self.is_sliding:
            self.is_jumping = True
            self.jump_frame = 0
    
    def slide(self):
        if not self.is_sliding and not self.is_jumping:
            self.is_sliding = True
            self.slide_frame = 0
    
    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
    
    def move_right(self):
        if self.lane < 2:
            self.lane += 1


# ═══════════════════════════════════════════════════════════════════════════════
# AI TRAINER GAME - ENHANCED VERSION
# ═══════════════════════════════════════════════════════════════════════════════

class AITrainerGame(QWidget):
    """
    🤖 AI TRAINER GAME - ENHANCED VERSION
    
    A Temple Run style game with AI-powered adaptive learning.
    
    NEW FEATURES:
    - AI learns your gesture performance patterns
    - Adapts obstacle spawning to focus on weak gestures
    - Tracks reaction times for each gesture
    - Progressive difficulty based on skill level
    - Real-time performance analytics
    - Saves and loads your learning progress
    """
    
    game_over = Signal(str, int)
    game_started = Signal(str)
    score_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # ═══════════════════════════════════════════════════════════════════════
        # AI INTEGRATION
        # ═══════════════════════════════════════════════════════════════════════
        self.ai_learner = ai_learner
        self.ai_enabled = AI_LEARNER_AVAILABLE
        self.adaptive_mode = True  # Use AI to select obstacles
        
        # ═══════════════════════════════════════════════════════════════════════
        # GAME STATE
        # ═══════════════════════════════════════════════════════════════════════
        self.state = TrainerState.WELCOME
        self.player = TrainerPlayer()
        self.obstacles = []
        self.current_obstacle = None
        
        # ═══════════════════════════════════════════════════════════════════════
        # STATS
        # ═══════════════════════════════════════════════════════════════════════
        self.score = 0
        self.high_score = 0
        self.speed = 6
        self.base_speed = 6
        self.obstacles_cleared = 0
        self.correct_gestures = 0
        self.wrong_attempts = 0
        self.streak = 0
        self.best_streak = 0
        
        # ═══════════════════════════════════════════════════════════════════════
        # TIMING
        # ═══════════════════════════════════════════════════════════════════════
        self.spawn_timer = 0
        self.spawn_interval = 120
        self.instruction_zone_y = 200
        self.instruction_start_time = 0  # NEW: Track when instruction shown
        self.last_reaction_time = 0      # NEW: Track reaction time
        
        # ═══════════════════════════════════════════════════════════════════════
        # ANIMATION
        # ═══════════════════════════════════════════════════════════════════════
        self.frame = 0
        self.track_offset = 0
        self.instruction_pulse = 0
        self.success_timer = 0
        self.analytics_frame = 0
        
        # ═══════════════════════════════════════════════════════════════════════
        # DIFFICULTY PROGRESSION
        # ═══════════════════════════════════════════════════════════════════════
        self.difficulty_level = 1
        self.obstacles_per_level = 5
        self.difficulty_mode = DifficultyMode.AI_ADAPTIVE if self.ai_enabled else DifficultyMode.BEGINNER
        
        # ═══════════════════════════════════════════════════════════════════════
        # PERFORMANCE TRACKING (LOCAL)
        # ═══════════════════════════════════════════════════════════════════════
        self.session_stats = {
            "UP": {"attempts": 0, "successes": 0, "total_reaction": 0},
            "DOWN": {"attempts": 0, "successes": 0, "total_reaction": 0},
            "LEFT": {"attempts": 0, "successes": 0, "total_reaction": 0},
            "RIGHT": {"attempts": 0, "successes": 0, "total_reaction": 0},
        }
        self.recent_results = deque(maxlen=20)  # Last 20 results for trend
        
        # ═══════════════════════════════════════════════════════════════════════
        # UI STATE
        # ═══════════════════════════════════════════════════════════════════════
        self.show_mini_analytics = True
        self.show_reaction_time = True
        
        # ═══════════════════════════════════════════════════════════════════════
        # TIMER
        # ═══════════════════════════════════════════════════════════════════════
        self.timer = QTimer()
        self.timer.timeout.connect(self._update)
        self.timer.start(33)  # 30 FPS
        
        print("  🤖 AI Trainer Game Initialized")
        print(f"     AI Learning: {'✅ ENABLED' if self.ai_enabled else '❌ DISABLED'}")
        print(f"     Adaptive Mode: {'✅ ON' if self.adaptive_mode else '❌ OFF'}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # UPDATE LOOP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update(self):
        self.frame += 1
        self.instruction_pulse = (self.instruction_pulse + 5) % 360
        
        if self.state == TrainerState.RUNNING:
            self._update_running()
        elif self.state == TrainerState.INSTRUCTION:
            self._update_instruction()
        elif self.state == TrainerState.SUCCESS:
            self._update_success()
        elif self.state == TrainerState.ANALYTICS:
            self.analytics_frame += 1
        
        self.update()
    
    def _update_running(self):
        """Update game while running"""
        self.track_offset = (self.track_offset + self.speed) % 50
        self.player.update()
        
        # Spawn new obstacles
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_obstacle()
            self.spawn_timer = 0
        
        # Update obstacles
        for obs in self.obstacles[:]:
            obs.update(self.speed)
            
            if not obs.instruction_shown and obs.y >= self.instruction_zone_y:
                self._show_instruction(obs)
                return
            
            if obs.cleared and obs.y > self.height() + 50:
                self.obstacles.remove(obs)
                self.score += 100
                self.obstacles_cleared += 1
                
                if self.obstacles_cleared % self.obstacles_per_level == 0:
                    self._level_up()
        
        self.score += 1
    
    def _update_instruction(self):
        """Update while showing instruction"""
        pass
    
    def _update_success(self):
        """Update success animation"""
        self.success_timer += 1
        self.player.update()
        
        if self.success_timer >= 30:
            self.state = TrainerState.RUNNING
            self.success_timer = 0
            if self.current_obstacle:
                self.current_obstacle.cleared = True
                self.current_obstacle = None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # AI-POWERED OBSTACLE SPAWNING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _spawn_obstacle(self):
        """Spawn obstacle - AI selects based on performance"""
        if self.adaptive_mode and self.ai_enabled and self.ai_learner:
            # AI selects which gesture to practice
            direction = self.ai_learner.get_next_gesture()
            obs_type = DIRECTION_TO_OBSTACLE.get(direction, ObstacleType.JUMP)
        else:
            # Standard random selection based on difficulty
            obs_type = self._get_random_obstacle()
        
        self.obstacles.append(TrainerObstacle(obs_type, -80))
    
    def _get_random_obstacle(self) -> ObstacleType:
        """Get random obstacle based on difficulty level"""
        if self.difficulty_level == 1:
            return random.choice([ObstacleType.JUMP, ObstacleType.SLIDE])
        elif self.difficulty_level == 2:
            return random.choice([ObstacleType.JUMP, ObstacleType.SLIDE, ObstacleType.LEFT])
        else:
            return random.choice(list(ObstacleType))
    
    def _show_instruction(self, obstacle):
        """Pause and show instruction"""
        self.state = TrainerState.INSTRUCTION
        self.current_obstacle = obstacle
        obstacle.instruction_shown = True
        
        # Start timing for reaction
        self.instruction_start_time = time.time()
        
        # Tell AI learner instruction started
        if self.ai_enabled and self.ai_learner:
            self.ai_learner.start_gesture_timing()
        
        direction = obstacle.get_direction()
        print(f"  📚 Instruction: {INSTRUCTIONS[obstacle.type]['text']} ({direction})")
    
    def _level_up(self):
        """Increase difficulty - AI adjusts based on skill"""
        self.difficulty_level += 1
        
        if self.ai_enabled and self.ai_learner:
            # AI determines speed based on skill
            speed_mult = self.ai_learner.get_speed_multiplier()
            self.speed = self.base_speed * speed_mult
            
            # Adjust spawn interval
            avg_reaction = self._get_avg_reaction_time()
            if avg_reaction > 0:
                # Faster reactions = shorter spawn intervals
                self.spawn_interval = max(60, int(120 - (1.0 / avg_reaction) * 20))
        else:
            self.speed = min(12, self.speed + 0.5)
            self.spawn_interval = max(60, self.spawn_interval - 10)
        
        print(f"  ⬆️ Level Up! Level {self.difficulty_level} | Speed: {self.speed:.1f}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GESTURE HANDLING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _on_correct_gesture(self, direction: str):
        """Handle correct gesture - record to AI"""
        # Calculate reaction time
        reaction_time = time.time() - self.instruction_start_time
        self.last_reaction_time = reaction_time
        
        # Update local stats
        if direction in self.session_stats:
            self.session_stats[direction]["attempts"] += 1
            self.session_stats[direction]["successes"] += 1
            self.session_stats[direction]["total_reaction"] += reaction_time
        
        # Record to AI learner
        if self.ai_enabled and self.ai_learner:
            self.ai_learner.record_gesture(direction, True, reaction_time)
        
        # Track recent results
        self.recent_results.append({"success": True, "direction": direction, "time": reaction_time})
        
        # Update game state
        self.state = TrainerState.SUCCESS
        self.success_timer = 0
        self.correct_gestures += 1
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        self.score += 50 * self.streak
        
        # Execute player action
        if self.current_obstacle:
            obs_type = self.current_obstacle.type
            if obs_type == ObstacleType.JUMP:
                self.player.jump()
            elif obs_type == ObstacleType.SLIDE:
                self.player.slide()
            elif obs_type == ObstacleType.LEFT:
                self.player.move_left()
            elif obs_type == ObstacleType.RIGHT:
                self.player.move_right()
        
        print(f"  ✅ Correct! Reaction: {reaction_time:.2f}s | Streak: {self.streak}")
    
    def _on_wrong_gesture(self, direction: str, expected: str):
        """Handle wrong gesture - record to AI"""
        # Update local stats
        if expected in self.session_stats:
            self.session_stats[expected]["attempts"] += 1
        
        # Record to AI learner (failure for expected direction)
        if self.ai_enabled and self.ai_learner:
            self.ai_learner.record_gesture(expected, False, 0.0)
        
        # Track recent results
        self.recent_results.append({"success": False, "direction": expected, "time": 0})
        
        self.wrong_attempts += 1
        self.streak = 0
        
        print(f"  ❌ Wrong! Expected: {expected}, Got: {direction}")
    
    def _game_over(self):
        """End the game"""
        self.state = TrainerState.GAME_OVER
        
        if self.score > self.high_score:
            self.high_score = self.score
        
        # End AI session
        if self.ai_enabled and self.ai_learner and hasattr(self.ai_learner, 'current_session'):
            if self.ai_learner.current_session:
                self.ai_learner.current_session.total_score = self.score
                self.ai_learner.current_session.max_streak = self.best_streak
        
        self.game_over.emit("AI Trainer", self.score)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYTICS HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _get_avg_reaction_time(self) -> float:
        """Get average reaction time from session"""
        total_time = 0
        total_count = 0
        for stats in self.session_stats.values():
            total_time += stats["total_reaction"]
            total_count += stats["successes"]
        return total_time / total_count if total_count > 0 else 0.0
    
    def _get_session_accuracy(self) -> float:
        """Get session accuracy percentage"""
        total_attempts = sum(s["attempts"] for s in self.session_stats.values())
        total_successes = sum(s["successes"] for s in self.session_stats.values())
        return total_successes / total_attempts if total_attempts > 0 else 0.0
    
    def _get_weakest_gesture(self) -> str:
        """Get weakest gesture in this session"""
        weakest = "UP"
        lowest_rate = 1.0
        
        for direction, stats in self.session_stats.items():
            if stats["attempts"] > 0:
                rate = stats["successes"] / stats["attempts"]
                if rate < lowest_rate:
                    lowest_rate = rate
                    weakest = direction
        
        return weakest
    
    def _get_recent_trend(self) -> str:
        """Get recent performance trend"""
        if len(self.recent_results) < 6:
            return "LOADING"
        
        recent = list(self.recent_results)
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        first_rate = sum(1 for r in first_half if r["success"]) / len(first_half)
        second_rate = sum(1 for r in second_half if r["success"]) / len(second_half)
        
        diff = second_rate - first_rate
        if diff > 0.15:
            return "IMPROVING"
        elif diff < -0.15:
            return "DECLINING"
        return "STABLE"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAINTING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Background
        bg = QLinearGradient(0, 0, 0, h)
        bg.setColorAt(0, QColor(5, 15, 30))
        bg.setColorAt(1, QColor(10, 25, 45))
        painter.fillRect(0, 0, w, h, bg)
        
        if self.state == TrainerState.WELCOME:
            self._draw_welcome(painter, w, h)
        elif self.state in [TrainerState.RUNNING, TrainerState.INSTRUCTION, TrainerState.SUCCESS]:
            self._draw_game(painter, w, h)
            
            # Mini analytics overlay
            if self.show_mini_analytics:
                self._draw_mini_analytics(painter, w, h)
            
            if self.state == TrainerState.INSTRUCTION:
                self._draw_instruction_overlay(painter, w, h)
            elif self.state == TrainerState.SUCCESS:
                self._draw_success_overlay(painter, w, h)
        elif self.state == TrainerState.GAME_OVER:
            self._draw_game(painter, w, h)
            self._draw_game_over(painter, w, h)
        elif self.state == TrainerState.ANALYTICS:
            self._draw_full_analytics(painter, w, h)
        
        # AI indicator
        if self.ai_enabled:
            self._draw_ai_indicator(painter, w, h)
        
        # Border
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(1, 1, w-2, h-2)
        
        painter.end()
    
    def _draw_welcome(self, painter, w, h):
        """Enhanced Welcome Screen - Perfectly Centered with Bottom Controls"""
    
        # ═══════════════════════════════════════════════════════════════════
        # CENTER CALCULATIONS
        # ═══════════════════════════════════════════════════════════════════
        center_x = w // 2
        center_y = h // 2
    
        # ═══════════════════════════════════════════════════════════════════
        # ANIMATED BACKGROUND PARTICLES
        # ═══════════════════════════════════════════════════════════════════
        painter.setPen(Qt.NoPen)
        for i in range(20):
            angle = (self.frame * 0.02 + i * 18) % 360
            radius = 100 + (i % 3) * 80
            x = center_x + int(radius * math.cos(math.radians(angle)))
            y = center_y + int(radius * math.sin(math.radians(angle)))
            alpha = 20 + int(30 * math.sin(self.frame * 0.05 + i))
            size = 3 + (i % 2) * 2
            painter.setBrush(QColor(0, 150, 255, alpha))  # Blue particles
            painter.drawEllipse(x - size, y - size, size * 2, size * 2)
    
        # ═══════════════════════════════════════════════════════════════════
        # LAYOUT CALCULATIONS (Card + Button + Progress below)
        # ═══════════════════════════════════════════════════════════════════
        card_width = min(550, w - 80)
        card_height = 380
        button_height = 50
        progress_height = 50
        spacing = 15
    
        total_height = card_height + spacing + button_height + spacing + progress_height
        start_y = center_y - total_height // 2
    
        card_x = center_x - card_width // 2
        card_y = start_y
    
        button_y = card_y + card_height + spacing
        progress_y = button_y + button_height + spacing
    
        # ═══════════════════════════════════════════════════════════════════
        # MAIN CARD BACKGROUND
        # ═══════════════════════════════════════════════════════════════════
        card_grad = QLinearGradient(card_x, card_y, card_x, card_y + card_height)
        card_grad.setColorAt(0, QColor(15, 30, 60, 245))
        card_grad.setColorAt(0.5, QColor(10, 25, 55, 245))
        card_grad.setColorAt(1, QColor(5, 20, 45, 245))
        painter.setBrush(card_grad)
    
        # Animated border glow
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.08)
        border_color = QColor(0, 150, 255, int(150 + 100 * pulse))
        painter.setPen(QPen(border_color, 3))
        painter.drawRoundedRect(card_x, card_y, card_width, card_height, 20, 20)
    
        # Inner glow
        painter.setPen(QPen(QColor(0, 100, 255, 40), 10))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_x + 5, card_y + 5, card_width - 10, card_height - 10, 18, 18)
    
        # ═══════════════════════════════════════════════════════════════════
        # TITLE WITH AI BADGE
        # ═══════════════════════════════════════════════════════════════════
        title_y = card_y + 25
    
        # Main title
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 32, QFont.Bold))
        title = "🤖 AI TRAINER"
        painter.drawText(QRectF(card_x, title_y, card_width, 50), Qt.AlignCenter, title)
    
        # Decorative line under title
        line_width = 140
        line_y = title_y + 50
    
        # Gradient line
        line_grad = QLinearGradient(center_x - line_width // 2, 0, center_x + line_width // 2, 0)
        line_grad.setColorAt(0, QColor(0, 100, 255, 0))
        line_grad.setColorAt(0.3, QColor(0, 200, 255, 255))
        line_grad.setColorAt(0.7, QColor(0, 200, 255, 255))
        line_grad.setColorAt(1, QColor(0, 100, 255, 0))
        painter.setPen(QPen(QBrush(line_grad), 2))
        painter.drawLine(center_x - line_width // 2, line_y, center_x + line_width // 2, line_y)
    
        # AI Status Badge
        if self.ai_enabled:
            badge_y = title_y + 58
        
            # Badge glow
            badge_glow = QRadialGradient(center_x, badge_y + 10, 80)
            badge_glow.setColorAt(0, QColor(0, 255, 136, 60))
            badge_glow.setColorAt(1, QColor(0, 255, 136, 0))
            painter.setBrush(badge_glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - 80, badge_y - 2, 160, 24)
        
            # Badge text
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(QRectF(card_x, badge_y, card_width, 20), Qt.AlignCenter,
                            "✨ AI ADAPTIVE LEARNING ENABLED ✨")
    
        # ═══════════════════════════════════════════════════════════════════
        # FEATURE BOXES (3 columns)
        # ═══════════════════════════════════════════════════════════════════
        features_y = title_y + 90
        box_width = (card_width - 60) // 3
        box_height = 85
    
        features = [
            {"icon": "🧠", "title": "AI LEARNS", "desc": "Tracks your\nweaknesses", "color": QColor(0, 200, 255)},
            {"icon": "🎯", "title": "ADAPTIVE", "desc": "Focuses on\nweak gestures", "color": QColor(0, 255, 136)},
            {"icon": "📊", "title": "ANALYTICS", "desc": "Real-time\ninsights", "color": QColor(255, 200, 0)},
        ]
    
        for i, feature in enumerate(features):
            box_x = card_x + 20 + i * (box_width + 10)
        
            # Feature box background
            feat_grad = QLinearGradient(box_x, features_y, box_x, features_y + box_height)
            feat_grad.setColorAt(0, QColor(20, 45, 80, 200))
            feat_grad.setColorAt(1, QColor(10, 30, 60, 200))
            painter.setBrush(feat_grad)
            painter.setPen(QPen(feature["color"].darker(150), 1))
            painter.drawRoundedRect(box_x, features_y, box_width, box_height, 10, 10)
        
            # Icon
            painter.setPen(feature["color"])
            painter.setFont(QFont("Segoe UI Emoji", 22))
            painter.drawText(QRectF(box_x, features_y + 8, box_width, 32), Qt.AlignCenter, feature["icon"])
        
            # Title
            painter.setPen(feature["color"])
            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            painter.drawText(QRectF(box_x, features_y + 44, box_width, 16), Qt.AlignCenter, feature["title"])
        
            # Description
            painter.setPen(QColor(150, 180, 220))
            painter.setFont(QFont("Consolas", 7))
            painter.drawText(QRectF(box_x, features_y + 60, box_width, 24), Qt.AlignCenter, feature["desc"])
    
        # ═══════════════════════════════════════════════════════════════════
        # HOW IT WORKS - HORIZONTAL FLOW
        # ═══════════════════════════════════════════════════════════════════
        flow_y = features_y + box_height + 20
    
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.drawText(QRectF(card_x, flow_y, card_width, 18), Qt.AlignCenter, "◢ HOW IT WORKS ◣")
    
        # Horizontal flow steps
        steps = [
            {"num": "1", "text": "Obstacle\nAppears", "color": QColor(0, 180, 255)},
            {"num": "2", "text": "Follow\nInstruction", "color": QColor(0, 255, 136)},
            {"num": "3", "text": "AI\nLearns", "color": QColor(180, 100, 255)},
            {"num": "4", "text": "Adapts\nTo You", "color": QColor(255, 165, 0)},
        ]
    
        step_row_y = flow_y + 25
        step_width = (card_width - 40) // 4
    
        for i, step in enumerate(steps):
            step_x = card_x + 20 + i * step_width
            step_center_x = step_x + step_width // 2
        
            # Step number circle
            painter.setBrush(step["color"])
            painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
            painter.drawEllipse(step_center_x - 14, step_row_y, 28, 28)
        
            # Number text
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Consolas", 12, QFont.Bold))
            painter.drawText(QRectF(step_center_x - 14, step_row_y, 28, 28), Qt.AlignCenter, step["num"])
        
            # Step description
            painter.setPen(QColor(180, 200, 230))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(QRectF(step_x, step_row_y + 32, step_width, 30), Qt.AlignCenter, step["text"])
        
            # Arrow between steps
            if i < len(steps) - 1:
                arrow_x = step_x + step_width - 3
                arrow_y = step_row_y + 14
                painter.setPen(QPen(QColor(0, 150, 200, 150), 2))
                painter.drawLine(arrow_x, arrow_y, arrow_x + 8, arrow_y)
                painter.drawLine(arrow_x + 5, arrow_y - 4, arrow_x + 8, arrow_y)
                painter.drawLine(arrow_x + 5, arrow_y + 4, arrow_x + 8, arrow_y)
    
        # ═══════════════════════════════════════════════════════════════════
        # AI STATS PREVIEW (Inside card - bottom)
        # ═══════════════════════════════════════════════════════════════════
        stats_shown = False
        if self.ai_enabled and self.ai_learner:
            try:
                stats = self.ai_learner.get_overall_stats()
                if stats.get('total_attempts', 0) > 0:
                    stats_shown = True
                    stats_y = card_y + card_height - 58
                
                    # Stats container
                    stats_width = card_width - 40
                    stats_x = card_x + 20
                
                    stats_grad = QLinearGradient(stats_x, stats_y, stats_x, stats_y + 42)
                    stats_grad.setColorAt(0, QColor(10, 40, 70, 220))
                    stats_grad.setColorAt(1, QColor(5, 25, 50, 220))
                    painter.setBrush(stats_grad)
                    painter.setPen(QPen(QColor(0, 150, 255, 100), 1))
                    painter.drawRoundedRect(stats_x, stats_y, stats_width, 42, 8, 8)
                
                    # Stats icon and label
                    painter.setPen(QColor(0, 255, 136))
                    painter.setFont(QFont("Consolas", 9, QFont.Bold))
                    painter.drawText(stats_x + 15, stats_y + 17, "📈 YOUR PROGRESS:")
                
                    # Mastery value
                    mastery = stats.get('avg_mastery', 0)
                    weak = stats.get('weakest_gesture', 'N/A')
                
                    painter.setPen(QColor(255, 215, 0))
                    painter.setFont(QFont("Consolas", 14, QFont.Bold))
                    painter.drawText(stats_x + 15, stats_y + 36, f"{mastery:.0%}")
                
                    painter.setPen(QColor(150, 180, 220))
                    painter.setFont(QFont("Consolas", 9))
                    painter.drawText(stats_x + 70, stats_y + 36, f"Mastery  |  Focus: {weak}")
            except:
                pass
    
        # High score inside card (bottom)
        if self.high_score > 0:
            hs_y = card_y + card_height - 18 if not stats_shown else card_y + card_height - 18
            if stats_shown:
                hs_y = card_y + card_height - 12
            painter.setPen(QColor(255, 215, 0, 200))
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(QRectF(card_x, hs_y - 5, card_width, 18), Qt.AlignCenter,
                            f"★ Best Score: {self.high_score} ★")
    
        # ═══════════════════════════════════════════════════════════════════
        # START BUTTON (Below Card) - FUTURISTIC BLUE
        # ═══════════════════════════════════════════════════════════════════
        button_width = min(320, card_width - 60)
        button_x = center_x - button_width // 2
    
        # Button outer glow
        glow_pulse = 0.5 + 0.5 * math.sin(self.frame * 0.1)
        glow = QRadialGradient(center_x, button_y + button_height // 2, button_width // 2 + 40)
        glow.setColorAt(0, QColor(0, 150, 255, int(80 * glow_pulse)))
        glow.setColorAt(0.5, QColor(0, 100, 200, int(40 * glow_pulse)))
        glow.setColorAt(1, QColor(0, 50, 150, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(button_x - 40, button_y - 20, button_width + 80, button_height + 40)
    
        # Button background gradient
        btn_grad = QLinearGradient(button_x, button_y, button_x, button_y + button_height)
        btn_grad.setColorAt(0, QColor(0, 80, 150, 230))
        btn_grad.setColorAt(0.5, QColor(0, 60, 120, 230))
        btn_grad.setColorAt(1, QColor(0, 40, 100, 230))
        painter.setBrush(btn_grad)
    
        # Animated border
        border_alpha = int(180 + 75 * glow_pulse)
        painter.setPen(QPen(QColor(0, 200, 255, border_alpha), 3))
        painter.drawRoundedRect(button_x, button_y, button_width, button_height, 12, 12)
    
        # Inner highlight line (top)
        highlight_grad = QLinearGradient(button_x + 20, 0, button_x + button_width - 20, 0)
        highlight_grad.setColorAt(0, QColor(0, 200, 255, 0))
        highlight_grad.setColorAt(0.5, QColor(100, 220, 255, 120))
        highlight_grad.setColorAt(1, QColor(0, 200, 255, 0))
        painter.setPen(QPen(QBrush(highlight_grad), 2))
        painter.drawLine(button_x + 20, button_y + 4, button_x + button_width - 20, button_y + 4)
    
        # Button text with glow
        text_alpha = int(200 + 55 * glow_pulse)
    
        # Text shadow/glow
        painter.setPen(QColor(0, 150, 255, 100))
        painter.setFont(QFont("Consolas", 18, QFont.Bold))
        painter.drawText(QRectF(button_x + 2, button_y + 2, button_width, button_height), 
                        Qt.AlignCenter, "▶  START TRAINING  ◀")
    
        # Main text
        painter.setPen(QColor(0, 255, 255, text_alpha))
        painter.drawText(QRectF(button_x, button_y, button_width, button_height), 
                        Qt.AlignCenter, "▶  START TRAINING  ◀")
    
        # Corner accents
        accent_size = 10
        accent_color = QColor(0, 220, 255, border_alpha)
        painter.setPen(QPen(accent_color, 2))
    
        # Top-left
        painter.drawLine(button_x - 2, button_y + accent_size, button_x - 2, button_y - 2)
        painter.drawLine(button_x - 2, button_y - 2, button_x + accent_size, button_y - 2)
    
        # Top-right
        painter.drawLine(button_x + button_width - accent_size, button_y - 2, button_x + button_width + 2, button_y - 2)
        painter.drawLine(button_x + button_width + 2, button_y - 2, button_x + button_width + 2, button_y + accent_size)
    
        # Bottom-left
        painter.drawLine(button_x - 2, button_y + button_height - accent_size, button_x - 2, button_y + button_height + 2)
        painter.drawLine(button_x - 2, button_y + button_height + 2, button_x + accent_size, button_y + button_height + 2)
    
        # Bottom-right
        painter.drawLine(button_x + button_width - accent_size, button_y + button_height + 2, button_x + button_width + 2, button_y + button_height + 2)
        painter.drawLine(button_x + button_width + 2, button_y + button_height - accent_size, button_x + button_width + 2, button_y + button_height + 2)
    
        # ═══════════════════════════════════════════════════════════════════
        # FUTURISTIC PROGRESS BAR (Below Button) - BLUE THEME
        # ═══════════════════════════════════════════════════════════════════
        progress_width = min(400, card_width - 40)
        progress_x = center_x - progress_width // 2
        bar_height = 14
    
        # Progress label
        painter.setPen(QColor(0, 180, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(QRectF(progress_x, progress_y, progress_width, 16), 
                        Qt.AlignCenter, "◈ TRAINING READINESS ◈")
    
        bar_y = progress_y + 18
    
        # Outer glow
        bar_glow = QRadialGradient(center_x, bar_y + bar_height // 2, progress_width // 2 + 20)
        bar_glow.setColorAt(0, QColor(0, 100, 200, 40))
        bar_glow.setColorAt(1, QColor(0, 50, 150, 0))
        painter.setBrush(bar_glow)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(progress_x - 20, bar_y - 10, progress_width + 40, bar_height + 20, 10, 10)
    
        # Outer container with tech border
        painter.setBrush(QColor(5, 15, 35, 230))
        painter.setPen(QPen(QColor(0, 100, 200, 180), 1))
        painter.drawRoundedRect(progress_x - 2, bar_y - 2, progress_width + 4, bar_height + 4, 5, 5)
    
        # Inner track (dark blue)
        track_grad = QLinearGradient(progress_x, bar_y, progress_x, bar_y + bar_height)
        track_grad.setColorAt(0, QColor(5, 20, 50))
        track_grad.setColorAt(0.5, QColor(10, 30, 65))
        track_grad.setColorAt(1, QColor(5, 20, 50))
        painter.setBrush(track_grad)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(progress_x, bar_y, progress_width, bar_height, 3, 3)
    
        # Grid lines inside track (tech effect)
        painter.setPen(QPen(QColor(0, 100, 200, 50), 1))
        for i in range(1, 10):
            line_x = progress_x + int(progress_width * i / 10)
            painter.drawLine(line_x, bar_y + 2, line_x, bar_y + bar_height - 2)
    
        # Animated fill (simulating loading)
        fill_progress = (self.frame % 180) / 180.0  # Loops 0 to 1
        if fill_progress < 0.65:
            # Growing phase
            fill_width = int(progress_width * (fill_progress / 0.65))
        else:
            # Full phase
            fill_width = progress_width
    
        if fill_width > 4:
            # ✨ FUTURISTIC BLUE GRADIENT (Deep Blue → Electric Blue → Cyan)
            fill_grad = QLinearGradient(progress_x, 0, progress_x + fill_width, 0)
            fill_grad.setColorAt(0, QColor(0, 60, 180))       # Deep Blue
            fill_grad.setColorAt(0.35, QColor(0, 120, 255))   # Electric Blue
            fill_grad.setColorAt(0.7, QColor(0, 180, 255))    # Bright Blue
            fill_grad.setColorAt(1, QColor(0, 240, 255))      # Cyan Blue
            painter.setBrush(fill_grad)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(progress_x + 2, bar_y + 2, fill_width - 4, bar_height - 4, 2, 2)
        
            # Shine effect on top (white-blue)
            shine_grad = QLinearGradient(progress_x, bar_y, progress_x, bar_y + bar_height // 2)
            shine_grad.setColorAt(0, QColor(150, 220, 255, 120))
            shine_grad.setColorAt(1, QColor(100, 200, 255, 0))
            painter.setBrush(shine_grad)
            painter.drawRoundedRect(progress_x + 2, bar_y + 2, fill_width - 4, bar_height // 2 - 1, 2, 2)
        
            # Moving scanner line (bright cyan)
            scanner_pos = (self.frame % 50) / 50.0
            scanner_x = progress_x + int(fill_width * scanner_pos)
            scanner_grad = QLinearGradient(scanner_x - 25, 0, scanner_x + 25, 0)
            scanner_grad.setColorAt(0, QColor(0, 200, 255, 0))
            scanner_grad.setColorAt(0.5, QColor(180, 250, 255, 220))
            scanner_grad.setColorAt(1, QColor(0, 200, 255, 0))
            painter.setBrush(scanner_grad)
            painter.drawRect(scanner_x - 25, bar_y + 2, 50, bar_height - 4)
        
            # Glowing edge at fill end
            if fill_width > 8:
                edge_glow = QRadialGradient(progress_x + fill_width - 2, bar_y + bar_height // 2, 18)
                edge_glow.setColorAt(0, QColor(0, 240, 255, 200))
                edge_glow.setColorAt(0.4, QColor(0, 180, 255, 100))
                edge_glow.setColorAt(1, QColor(0, 100, 255, 0))
                painter.setBrush(edge_glow)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(progress_x + fill_width - 20, bar_y - 6, 36, bar_height + 12)
    
        # Edge glow particles (blue)
        if fill_width > 15:
            import random
            for i in range(4):
                particle_x = progress_x + fill_width - 8 + random.randint(-6, 6)
                particle_y = bar_y + bar_height // 2 + random.randint(-6, 6)
                particle_alpha = random.randint(130, 230)
                particle_size = random.randint(2, 5)
                painter.setBrush(QColor(0, 220, 255, particle_alpha))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(particle_x, particle_y, particle_size, particle_size)
    
        # Tech corner brackets (cyan blue)
        bracket_color = QColor(0, 200, 255, 200)
        painter.setPen(QPen(bracket_color, 2))
        bracket_size = 8
    
        # Top-left bracket
        painter.drawLine(progress_x - 8, bar_y - 2, progress_x - 8, bar_y + bracket_size)
        painter.drawLine(progress_x - 8, bar_y - 2, progress_x - 8 + bracket_size, bar_y - 2)
    
        # Top-right bracket
        painter.drawLine(progress_x + progress_width + 8, bar_y - 2, progress_x + progress_width + 8, bar_y + bracket_size)
        painter.drawLine(progress_x + progress_width + 8, bar_y - 2, progress_x + progress_width + 8 - bracket_size, bar_y - 2)
    
        # Bottom-left bracket
        painter.drawLine(progress_x - 8, bar_y + bar_height + 2, progress_x - 8, bar_y + bar_height - bracket_size + 2)
        painter.drawLine(progress_x - 8, bar_y + bar_height + 2, progress_x - 8 + bracket_size, bar_y + bar_height + 2)
    
        # Bottom-right bracket
        painter.drawLine(progress_x + progress_width + 8, bar_y + bar_height + 2, progress_x + progress_width + 8, bar_y + bar_height - bracket_size + 2)
        painter.drawLine(progress_x + progress_width + 8, bar_y + bar_height + 2, progress_x + progress_width + 8 - bracket_size, bar_y + bar_height + 2)
    
        # Status text below
        status_y = bar_y + bar_height + 8
        if fill_progress >= 0.65:
            status_text = "◉ SYSTEM READY"
            status_color = QColor(0, 255, 200)
        
            # Ready glow
            ready_glow = QRadialGradient(center_x, status_y + 6, 60)
            ready_glow.setColorAt(0, QColor(0, 255, 200, 50))
            ready_glow.setColorAt(1, QColor(0, 255, 200, 0))
            painter.setBrush(ready_glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - 60, status_y - 2, 120, 16)
        else:
            percent = int(fill_progress / 0.65 * 100)
            status_text = f"◎ INITIALIZING... {percent}%"
            status_color = QColor(0, 180, 255)
    
        painter.setPen(status_color)
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(QRectF(progress_x, status_y, progress_width, 16), 
                        Qt.AlignCenter, status_text)
    
    def _draw_game(self, painter, w, h):
        """Draw the game world"""
        track_w = 300
        track_x = (w - track_w) // 2
        
        # Track background
        track_bg = QLinearGradient(track_x, 0, track_x + track_w, 0)
        track_bg.setColorAt(0, QColor(20, 40, 60))
        track_bg.setColorAt(0.5, QColor(25, 50, 75))
        track_bg.setColorAt(1, QColor(20, 40, 60))
        painter.fillRect(track_x, 0, track_w, h, track_bg)
        
        # Lane dividers
        painter.setPen(QPen(QColor(0, 200, 255, 60), 2, Qt.DashLine))
        for i in range(1, 3):
            x = track_x + i * 100
            painter.drawLine(x, 0, x, h)
        
        # Moving track lines
        painter.setPen(QPen(QColor(0, 150, 200, 30), 1))
        for y in range(-50, h + 50, 50):
            y_pos = (y + int(self.track_offset)) % (h + 50) - 50
            painter.drawLine(track_x + 10, y_pos, track_x + track_w - 10, y_pos)
        
        # Track borders
        glow_alpha = 150 + int(50 * math.sin(self.frame * 0.05))
        painter.setPen(QPen(QColor(0, 255, 255, glow_alpha), 4))
        painter.drawLine(track_x, 0, track_x, h)
        painter.drawLine(track_x + track_w, 0, track_x + track_w, h)
        
        # Instruction zone
        if self.state == TrainerState.RUNNING:
            painter.setPen(QPen(QColor(255, 255, 0, 30), 2, Qt.DashLine))
            painter.drawLine(track_x, self.instruction_zone_y, 
                           track_x + track_w, self.instruction_zone_y)
        
        # Draw obstacles
        for obs in self.obstacles:
            if not obs.cleared:
                self._draw_obstacle(painter, track_x, obs)
        
        # Draw player
        self._draw_player(painter, track_x, h)
        
        # HUD
        self._draw_hud(painter, w, h)
    
    def _draw_obstacle(self, painter, track_x, obs):
        """Draw obstacle"""
        info = INSTRUCTIONS[obs.type]
        color = info['color']
        
        if obs.type == ObstacleType.JUMP:
            ox = track_x + 100
            painter.setBrush(QColor(255, 60, 60))
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.drawRect(int(ox - 30), int(obs.y), 60, 45)
            
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            for i in range(3):
                y = obs.y + 10 + i * 12
                painter.drawLine(int(ox - 25), int(y), int(ox + 25), int(y))
        
        elif obs.type == ObstacleType.SLIDE:
            ox = track_x + 100
            painter.setBrush(QColor(255, 165, 0, 200))
            painter.setPen(QPen(QColor(255, 200, 0), 2))
            painter.drawRect(int(ox - 40), int(obs.y), 80, 25)
            painter.drawLine(int(ox - 30), int(obs.y + 25), int(ox - 30), int(obs.y + 60))
            painter.drawLine(int(ox + 30), int(obs.y + 25), int(ox + 30), int(obs.y + 60))
        
        elif obs.type == ObstacleType.LEFT:
            ox = track_x + 200
            painter.setBrush(QColor(255, 100, 200))
            painter.setPen(QPen(QColor(255, 150, 220), 2))
            painter.drawRect(int(ox - 35), int(obs.y), 70, 50)
        
        elif obs.type == ObstacleType.RIGHT:
            ox = track_x
            painter.setBrush(QColor(100, 200, 255))
            painter.setPen(QPen(QColor(150, 220, 255), 2))
            painter.drawRect(int(ox - 35), int(obs.y), 70, 50)
        
        # Show icon
        if obs.y < self.instruction_zone_y - 50 and not obs.instruction_shown:
            painter.setPen(color)
            painter.setFont(QFont("Consolas", 16, QFont.Bold))
            painter.drawText(QRectF(track_x, obs.y - 25, 300, 25), Qt.AlignCenter, info['icon'])
    
    def _draw_player(self, painter, track_x, h):
        """Draw player"""
        px = track_x + 150 + self.player.x_offset
        py = h - 120 + self.player.y_offset
        
        if self.player.is_sliding:
            painter.setBrush(QColor(0, 220, 255))
            painter.setPen(QPen(QColor(0, 255, 255), 3))
            painter.drawRoundedRect(int(px - 30), int(py - 15), 60, 25, 12, 12)
            
            painter.setPen(QPen(QColor(0, 255, 255, 100), 2))
            for i in range(3):
                ly = py - 5 + i * 8
                painter.drawLine(int(px - 50 - i * 10), int(ly), int(px - 35), int(ly))
        else:
            painter.setBrush(QColor(0, 220, 255))
            painter.setPen(QPen(QColor(0, 255, 255), 3))
            painter.drawRoundedRect(int(px - 18), int(py - 65), 36, 55, 8, 8)
            painter.drawEllipse(int(px - 14), int(py - 90), 28, 28)
            
            leg_offset = 8 * math.sin(self.frame * 0.3)
            painter.drawLine(int(px - 8), int(py - 10), int(px - 12 + leg_offset), int(py + 5))
            painter.drawLine(int(px + 8), int(py - 10), int(px + 12 - leg_offset), int(py + 5))
            
            if self.player.is_jumping:
                for i in range(3):
                    alpha = 100 - i * 30
                    trail_y = py + 20 + i * 15
                    painter.setPen(QPen(QColor(0, 255, 255, alpha), 2))
                    painter.drawLine(int(px - 15 + i * 5), int(trail_y), 
                                   int(px + 15 - i * 5), int(trail_y))
    
    def _draw_hud(self, painter, w, h):
        """Draw HUD"""
        # Score
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 14, QFont.Bold))
        painter.drawText(15, 30, f"SCORE: {self.score}")
        
        # Level
        painter.setPen(QColor(0, 255, 200))
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(15, 48, f"Level: {self.difficulty_level}")
        
        # Streak
        if self.streak > 0:
            streak_color = QColor(255, 100, 0) if self.streak >= 5 else QColor(0, 200, 255)
            painter.setPen(streak_color)
            painter.drawText(15, 66, f"🔥 Streak: {self.streak}")
        
        # Stats (top right)
        painter.setPen(QColor(150, 180, 220))
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(w - 140, 22, f"Cleared: {self.obstacles_cleared}")
        painter.drawText(w - 140, 38, f"Correct: {self.correct_gestures}")
        painter.drawText(w - 140, 54, f"Best Streak: {self.best_streak}")
        
        # Last reaction time
        if self.show_reaction_time and self.last_reaction_time > 0:
            rt_color = QColor(0, 255, 136) if self.last_reaction_time < 1.0 else QColor(255, 165, 0)
            painter.setPen(rt_color)
            painter.drawText(w - 140, 70, f"⚡ {self.last_reaction_time:.2f}s")
    
    def _draw_mini_analytics(self, painter, w, h):
        """Draw mini analytics panel"""
        # Background
        panel_x = w - 155
        panel_y = h - 115
        panel_w = 145
        panel_h = 105
        
        painter.fillRect(panel_x, panel_y, panel_w, panel_h, QColor(0, 20, 40, 200))
        painter.setPen(QPen(QColor(0, 150, 200, 150), 1))
        painter.drawRoundedRect(panel_x, panel_y, panel_w, panel_h, 4, 4)
        
        # Title
        painter.setPen(QColor(191, 0, 255))
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        painter.drawText(panel_x + 5, panel_y + 14, "◢ AI ANALYTICS")
        
        # Session accuracy
        accuracy = self._get_session_accuracy()
        acc_color = QColor(0, 255, 136) if accuracy >= 0.7 else QColor(255, 165, 0)
        painter.setPen(acc_color)
        painter.setFont(QFont("Consolas", 14, QFont.Bold))
        painter.drawText(panel_x + 8, panel_y + 38, f"{accuracy:.0%}")
        
        painter.setPen(QColor(150, 180, 220))
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(panel_x + 55, panel_y + 36, "accuracy")
        
        # Gesture bars
        directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}
        
        bar_y = panel_y + 48
        bar_w = 25
        
        for i, direction in enumerate(directions):
            stats = self.session_stats[direction]
            rate = stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0
            
            x = panel_x + 10 + i * 34
            
            # Icon
            painter.setPen(QColor(0, 200, 255))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(x + 8, bar_y + 8, icons[direction])
            
            # Bar background
            painter.fillRect(x, bar_y + 12, bar_w, 30, QColor(30, 50, 70))
            
            # Fill
            fill_h = int(30 * rate)
            fill_color = self._get_mastery_color(rate)
            painter.fillRect(x, bar_y + 12 + (30 - fill_h), bar_w, fill_h, fill_color)
            
            # Border
            painter.setPen(QPen(QColor(0, 150, 200), 1))
            painter.drawRect(x, bar_y + 12, bar_w, 30)
        
        # Trend indicator
        trend = self._get_recent_trend()
        trend_data = {
            "IMPROVING": ("↗", QColor(0, 255, 136)),
            "DECLINING": ("↘", QColor(255, 80, 80)),
            "STABLE": ("→", QColor(0, 200, 255)),
            "LOADING": ("◎", QColor(100, 100, 100)),
        }
        icon, color = trend_data.get(trend, ("?", QColor(100, 100, 100)))
        painter.setPen(color)
        painter.setFont(QFont("Consolas", 12, QFont.Bold))
        painter.drawText(panel_x + panel_w - 20, panel_y + 15, icon)
    
    def _draw_instruction_overlay(self, painter, w, h):
        """Enhanced Instruction Overlay - Perfectly Centered"""
        if not self.current_obstacle:
            return
    
        info = INSTRUCTIONS[self.current_obstacle.type]
        color = info['color']
    
        # ═══════════════════════════════════════════════════════════════════
        # DIM BACKGROUND WITH RADIAL FADE
        # ═══════════════════════════════════════════════════════════════════
        center_x = w // 2
        center_y = h // 2
    
        radial = QRadialGradient(center_x, center_y, max(w, h) // 2)
        radial.setColorAt(0, QColor(0, 0, 0, 120))
        radial.setColorAt(1, QColor(0, 0, 0, 200))
        painter.fillRect(0, 0, w, h, radial)
    
        # ═══════════════════════════════════════════════════════════════════
        # MAIN INSTRUCTION CARD
        # ═══════════════════════════════════════════════════════════════════
        card_width = min(480, w - 80)
        card_height = 340
        card_x = center_x - card_width // 2
        card_y = center_y - card_height // 2
    
        # Card background
        card_grad = QLinearGradient(card_x, card_y, card_x, card_y + card_height)
        card_grad.setColorAt(0, QColor(25, 45, 70, 250))
        card_grad.setColorAt(1, QColor(15, 30, 50, 250))
        painter.setBrush(card_grad)
    
        # Animated pulsing border
        pulse = 0.5 + 0.5 * math.sin(self.instruction_pulse * 0.05)
        border_alpha = int(150 + 100 * pulse)
        border_color = QColor(color.red(), color.green(), color.blue(), border_alpha)
        painter.setPen(QPen(border_color, 4))
        painter.drawRoundedRect(card_x, card_y, card_width, card_height, 18, 18)
    
        # Inner glow layers
        for i in range(3):
            glow_alpha = int((100 - i * 30) * pulse)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), glow_alpha), 10 - i * 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(card_x + 5 + i * 2, card_y + 5 + i * 2, 
                                   card_width - 10 - i * 4, card_height - 10 - i * 4, 16, 16)
    
        # ═══════════════════════════════════════════════════════════════════
        # TOP BADGES
        # ═══════════════════════════════════════════════════════════════════
        badge_y = card_y + 18
    
        # AI Badge (left)
        if self.ai_enabled:
            painter.setPen(QColor(191, 0, 255))
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.drawText(card_x + 20, badge_y, "🤖 AI")
    
        # Paused Badge (center)
        painter.setPen(QColor(255, 255, 0))
        painter.setFont(QFont("Consolas", 13, QFont.Bold))
        painter.drawText(QRectF(card_x, badge_y - 5, card_width, 25), Qt.AlignCenter,
                        "⏸ GAME PAUSED ⏸")
    
        # Timer Badge (right)
        elapsed = time.time() - self.instruction_start_time
        timer_color = QColor(0, 200, 255) if elapsed < 2.0 else QColor(255, 165, 0)
        painter.setPen(timer_color)
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        timer_text = f"⏱ {elapsed:.1f}s"
        painter.drawText(QRectF(card_x, badge_y - 2, card_width - 20, 20), Qt.AlignRight, timer_text)
    
        # ═══════════════════════════════════════════════════════════════════
        # MAIN ICON WITH ROTATING RING
        # ═══════════════════════════════════════════════════════════════════
        icon_y = card_y + 70
        icon_size = 100
    
        # Rotating outer ring
        ring_radius = 65
        ring_center_x = center_x
        ring_center_y = icon_y + 45
    
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 60), 3, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        rotation_angle = (self.instruction_pulse * 2) % 360
        painter.save()
        painter.translate(ring_center_x, ring_center_y)
        painter.rotate(rotation_angle)
        painter.drawEllipse(-ring_radius, -ring_radius, ring_radius * 2, ring_radius * 2)
        painter.restore()
    
        # Icon glow
        icon_glow = QRadialGradient(center_x, icon_y + 45, 50)
        icon_glow.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(100 * pulse)))
        icon_glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setBrush(icon_glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 50, icon_y - 5, 100, 100)
    
        # Main icon
        painter.setPen(color)
        painter.setFont(QFont("Consolas", 80, QFont.Bold))
        painter.drawText(QRectF(card_x, icon_y, card_width, icon_size), Qt.AlignCenter, info['icon'])
    
        # ═══════════════════════════════════════════════════════════════════
        # INSTRUCTION TEXT
        # ═══════════════════════════════════════════════════════════════════
        text_y = icon_y + 110
    
        # Main instruction
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 26, QFont.Bold))
        painter.drawText(QRectF(card_x, text_y, card_width, 42), Qt.AlignCenter, info['text'])
    
        # Decorative line
        line_width = 100
        line_y = text_y + 48
        painter.setPen(QPen(color, 2))
        painter.drawLine(center_x - line_width // 2, line_y, center_x + line_width // 2, line_y)
    
        # Hint text
        hint_y = line_y + 15
        painter.setPen(QColor(180, 200, 230))
        painter.setFont(QFont("Consolas", 13))
        painter.drawText(QRectF(card_x, hint_y, card_width, 28), Qt.AlignCenter, info['hint'])
    
        # ═══════════════════════════════════════════════════════════════════
        # WAITING INDICATOR (Animated dots)
        # ═══════════════════════════════════════════════════════════════════
        waiting_y = hint_y + 40
        dots_count = 1 + (self.frame // 15) % 3
        dots = "." * dots_count + " " * (3 - dots_count)
    
        alpha = int(150 + 100 * pulse)
        painter.setPen(QColor(0, 255, 200, alpha))
        painter.setFont(QFont("Consolas", 12))
        painter.drawText(QRectF(card_x, waiting_y, card_width, 28), Qt.AlignCenter,
                        f"⟳ Waiting for gesture{dots}")
    
        # ═══════════════════════════════════════════════════════════════════
        # ANIMATED DIRECTION ARROWS (Outside card)
        # ═══════════════════════════════════════════════════════════════════
        self._draw_direction_arrows(painter, w, h, info['direction'], color)
    
        # ═══════════════════════════════════════════════════════════════════
        # BOTTOM HINT
        # ═══════════════════════════════════════════════════════════════════
        bottom_y = card_y + card_height - 22
        painter.setPen(QColor(120, 140, 170))
        painter.setFont(QFont("Consolas", 9))
        painter.drawText(QRectF(card_x, bottom_y, card_width, 18), Qt.AlignCenter,
                        "Use hand gestures or arrow keys")
        # Direction arrows
        self._draw_direction_arrows(painter, w, h, info['direction'], color)
    
    def _draw_direction_arrows(self, painter, w, h, direction, color):
        """Draw animated direction arrows"""
        cx, cy = w // 2, h // 2
        
        pulse = 0.5 + 0.5 * math.sin(self.instruction_pulse * 0.08)
        arrow_color = QColor(color.red(), color.green(), color.blue(), int(100 + 100 * pulse))
        painter.setPen(QPen(arrow_color, 4))
        painter.setBrush(arrow_color)
        
        offset = int(20 * pulse)
        
        if direction == "UP":
            for i in range(3):
                y = cy - 200 - i * 25 - offset
                self._draw_arrow(painter, cx, y, "up")
        elif direction == "DOWN":
            for i in range(3):
                y = cy + 200 + i * 25 + offset
                self._draw_arrow(painter, cx, y, "down")
        elif direction == "LEFT":
            for i in range(3):
                x = cx - 300 - i * 25 - offset
                self._draw_arrow(painter, x, cy, "left")
        elif direction == "RIGHT":
            for i in range(3):
                x = cx + 300 + i * 25 + offset
                self._draw_arrow(painter, x, cy, "right")
    
    def _draw_arrow(self, painter, x, y, direction):
        """Draw single arrow"""
        path = QPainterPath()
        
        if direction == "up":
            path.moveTo(x, y)
            path.lineTo(x - 15, y + 20)
            path.lineTo(x + 15, y + 20)
        elif direction == "down":
            path.moveTo(x, y)
            path.lineTo(x - 15, y - 20)
            path.lineTo(x + 15, y - 20)
        elif direction == "left":
            path.moveTo(x, y)
            path.lineTo(x + 20, y - 15)
            path.lineTo(x + 20, y + 15)
        elif direction == "right":
            path.moveTo(x, y)
            path.lineTo(x - 20, y - 15)
            path.lineTo(x - 20, y + 15)
        
        path.closeSubpath()
        painter.drawPath(path)
    
    def _draw_success_overlay(self, painter, w, h):
        """Enhanced Success Animation - Perfectly Centered"""
        center_x = w // 2
        center_y = h // 2
    
        # ═══════════════════════════════════════════════════════════════════
        # FLASH EFFECT
        # ═══════════════════════════════════════════════════════════════════
        flash_alpha = max(0, 180 - self.success_timer * 6)
        flash_color = QColor(0, 255, 136, flash_alpha)
        painter.fillRect(0, 0, w, h, flash_color)
    
        # ═══════════════════════════════════════════════════════════════════
        # EXPANDING SUCCESS RING
        # ═══════════════════════════════════════════════════════════════════
        scale = min(1.0, self.success_timer / 15)
        ring_radius = int(80 * scale)
        ring_alpha = int(200 * (1 - scale))
    
        painter.setPen(QPen(QColor(0, 255, 136, ring_alpha), 6))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center_x - ring_radius, center_y - ring_radius,
                           ring_radius * 2, ring_radius * 2)
    
        # ═══════════════════════════════════════════════════════════════════
        # SUCCESS CHECKMARK
        # ═══════════════════════════════════════════════════════════════════
        check_scale = min(1.0, self.success_timer / 10)
    
        # Glow behind checkmark
        glow = QRadialGradient(center_x, center_y, 60)
        glow.setColorAt(0, QColor(0, 255, 136, int(120 * check_scale)))
        glow.setColorAt(1, QColor(0, 255, 136, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 60, center_y - 60, 120, 120)
    
        # Checkmark
        painter.setPen(QColor(0, 255, 136))
        font_size = int(70 * check_scale)
        painter.setFont(QFont("Consolas", font_size, QFont.Bold))
        painter.drawText(QRectF(center_x - 50, center_y - 55, 100, 110), Qt.AlignCenter, "✓")
    
        # ═══════════════════════════════════════════════════════════════════
        # SUCCESS TEXT
        # ═══════════════════════════════════════════════════════════════════
        text_y = center_y + 70
    
        if self.streak >= 5:
            text = f"⚡ {self.streak}x AMAZING!"
            text_color = QColor(255, 215, 0)
        elif self.streak >= 3:
            text = f"🔥 {self.streak}x STREAK!"
            text_color = QColor(255, 100, 0)
        else:
            text = "✓ PERFECT!"
            text_color = QColor(0, 255, 200)
    
        # Text shadow
        painter.setPen(QColor(0, 0, 0, 100))
        painter.setFont(QFont("Consolas", 28, QFont.Bold))
        painter.drawText(QRectF(center_x - 200 + 2, text_y + 2, 400, 45), Qt.AlignCenter, text)
    
        # Main text
        painter.setPen(text_color)
        painter.drawText(QRectF(center_x - 200, text_y, 400, 45), Qt.AlignCenter, text)
    
        # ═══════════════════════════════════════════════════════════════════
        # REACTION TIME BADGE
        # ═══════════════════════════════════════════════════════════════════
        if self.last_reaction_time > 0:
            rt_y = text_y + 50
        
            # Badge background
            badge_width = 180
            badge_x = center_x - badge_width // 2
            painter.fillRect(badge_x, rt_y, badge_width, 32, QColor(10, 30, 50, 200))
        
            # Reaction time color
            if self.last_reaction_time < 0.8:
                rt_color = QColor(0, 255, 136)
                rt_label = "LIGHTNING"
            elif self.last_reaction_time < 1.2:
                rt_color = QColor(0, 200, 255)
                rt_label = "FAST"
            else:
                rt_color = QColor(255, 165, 0)
                rt_label = "GOOD"
        
            painter.setPen(QPen(rt_color, 2))
            painter.drawRoundedRect(badge_x, rt_y, badge_width, 32, 6, 6)
        
            # Icon and time
            painter.setPen(rt_color)
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(badge_x + 10, rt_y + 21, f"⚡ {self.last_reaction_time:.2f}s")
        
            # Label
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(badge_x + 100, rt_y + 21, rt_label)
    
        # ═══════════════════════════════════════════════════════════════════
        # POINTS EARNED
        # ═══════════════════════════════════════════════════════════════════
        points_y = text_y + 95
        bonus = 50 * self.streak
    
        # Points with flying animation
        points_offset = -self.success_timer * 2
    
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 22, QFont.Bold))
        painter.drawText(QRectF(center_x - 150, points_y + points_offset, 300, 40), 
                        Qt.AlignCenter, f"+{bonus} POINTS!")
        
        # Bonus points
        bonus = 50 * self.streak
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 18, QFont.Bold))
        painter.drawText(QRectF(0, h * 0.55, w, 40), Qt.AlignCenter, f"+{bonus} points!")
    
    def _draw_game_over(self, painter, w, h):
        """Draw game over screen with analytics"""
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 200))
        
        box_w, box_h = 400, 380
        box_x, box_y = (w - box_w) // 2, (h - box_h) // 2
        
        painter.setBrush(QColor(15, 25, 45))
        painter.setPen(QPen(QColor(255, 60, 60), 3))
        painter.drawRoundedRect(box_x, box_y, box_w, box_h, 15, 15)
        
        # Game Over
        painter.setPen(QColor(255, 60, 60))
        painter.setFont(QFont("Consolas", 24, QFont.Bold))
        painter.drawText(QRectF(box_x, box_y + 15, box_w, 35), Qt.AlignCenter, "GAME OVER")
        
        # Score
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 36, QFont.Bold))
        painter.drawText(QRectF(box_x, box_y + 55, box_w, 50), Qt.AlignCenter, f"{self.score}")
        
        # Stats
        painter.setPen(QColor(180, 200, 220))
        painter.setFont(QFont("Consolas", 10))
        stats_y = box_y + 115
        painter.drawText(QRectF(box_x, stats_y, box_w, 18), Qt.AlignCenter, 
                        f"Obstacles Cleared: {self.obstacles_cleared}")
        painter.drawText(QRectF(box_x, stats_y + 18, box_w, 18), Qt.AlignCenter, 
                        f"Correct Gestures: {self.correct_gestures}")
        painter.drawText(QRectF(box_x, stats_y + 36, box_w, 18), Qt.AlignCenter, 
                        f"Best Streak: {self.best_streak}")
        painter.drawText(QRectF(box_x, stats_y + 54, box_w, 18), Qt.AlignCenter, 
                        f"Session Accuracy: {self._get_session_accuracy():.0%}")
        
        # Gesture breakdown
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(QRectF(box_x, stats_y + 80, box_w, 18), Qt.AlignCenter, 
                        "◢ GESTURE BREAKDOWN ◣")
        
        directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        icons = {"UP": "▲", "DOWN": "▼", "LEFT": "◀", "RIGHT": "▶"}
        
        for i, direction in enumerate(directions):
            stats = self.session_stats[direction]
            rate = stats["successes"] / stats["attempts"] if stats["attempts"] > 0 else 0
            avg_time = stats["total_reaction"] / stats["successes"] if stats["successes"] > 0 else 0
            
            x = box_x + 20 + i * 95
            y = stats_y + 100
            
            # Icon
            painter.setPen(self._get_mastery_color(rate))
            painter.setFont(QFont("Consolas", 18, QFont.Bold))
            painter.drawText(x + 30, y + 25, icons[direction])
            
            # Stats
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(x + 10, y + 45, f"{rate:.0%}")
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(x + 10, y + 58, f"{avg_time:.2f}s")
        
        # High score
        if self.score >= self.high_score:
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 12, QFont.Bold))
            painter.drawText(QRectF(box_x, box_y + box_h - 75, box_w, 25), Qt.AlignCenter, 
                           "★ NEW HIGH SCORE! ★")
        
        # Retry
        alpha = 150 + int(100 * math.sin(self.frame * 0.1))
        painter.setPen(QColor(0, 255, 255, alpha))
        painter.setFont(QFont("Consolas", 13, QFont.Bold))
        painter.drawText(QRectF(box_x, box_y + box_h - 45, box_w, 30), Qt.AlignCenter, 
                        "▶ CLICK TO RETRY ◀")
    
    def _draw_ai_indicator(self, painter, w, h):
        """Draw AI status indicator"""
        painter.setPen(QColor(191, 0, 255))
        painter.setFont(QFont("Consolas", 8))
        
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.1)
        alpha = int(150 + 100 * pulse)
        painter.setPen(QColor(191, 0, 255, alpha))
        
        painter.drawText(10, h - 10, "🤖 AI ACTIVE")
    
    def _draw_full_analytics(self, painter, w, h):
        """Draw full analytics screen"""
        # Background
        painter.fillRect(0, 0, w, h, QColor(5, 15, 30))
        
        # TODO: Implement full analytics screen
        # This would show detailed performance graphs
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 16, QFont.Bold))
        painter.drawText(QRectF(0, h*0.4, w, 40), Qt.AlignCenter, "📊 ANALYTICS")
        
        painter.setPen(QColor(150, 180, 220))
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(QRectF(0, h*0.5, w, 30), Qt.AlignCenter, "Coming soon...")
    
    def _get_mastery_color(self, mastery):
        """Get color based on mastery level"""
        if mastery >= 0.8:
            return QColor(0, 255, 136)
        elif mastery >= 0.6:
            return QColor(0, 200, 255)
        elif mastery >= 0.4:
            return QColor(255, 215, 0)
        elif mastery >= 0.2:
            return QColor(255, 165, 0)
        return QColor(255, 80, 80)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAME CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def load_game(self, game_id=None):
        """Load the AI Trainer game"""
        print("  🤖 Loading AI Trainer Game (Enhanced)")
        self._reset_game()
        self.state = TrainerState.WELCOME
        self.game_started.emit("AI Trainer")
    
    def _reset_game(self):
        """Reset all game state"""
        self.player = TrainerPlayer()
        self.obstacles = []
        self.current_obstacle = None
        self.score = 0
        self.speed = self.base_speed
        self.obstacles_cleared = 0
        self.correct_gestures = 0
        self.wrong_attempts = 0
        self.streak = 0
        self.spawn_timer = 0
        self.spawn_interval = 120
        self.difficulty_level = 1
        self.success_timer = 0
        self.last_reaction_time = 0
        self.instruction_start_time = 0
        
        # Reset session stats
        for direction in self.session_stats:
            self.session_stats[direction] = {"attempts": 0, "successes": 0, "total_reaction": 0}
        self.recent_results.clear()
    
    def _start_game(self):
        """Start playing"""
        print("  🎮 Starting AI Trainer!")
        self._reset_game()
        self.state = TrainerState.RUNNING
        
        # Start AI session
        if self.ai_enabled and self.ai_learner:
            self.ai_learner.start_session()
    
    def stop_game(self):
        """Stop the game"""
        # End AI session
        if self.ai_enabled and self.ai_learner:
            if hasattr(self.ai_learner, 'current_session') and self.ai_learner.current_session:
                self.ai_learner.end_session()
        
        self.state = TrainerState.WELCOME
        self.obstacles = []
    
    def restart_game(self):
        """Restart the game"""
        self._start_game()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INPUT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    @Slot(str)
    def handle_gesture(self, gesture):
        """Handle gesture input"""
        pass  # Uses direction, not gestures
    
    @Slot(object)
    def handle_direction(self, direction):
        """Handle direction input"""
        if hasattr(direction, 'value'):
            dir_val = direction.value
        else:
            dir_val = str(direction).upper()
        
        if dir_val == "NONE":
            return
        
        print(f"  🎓 AI Trainer received: {dir_val} | State: {self.state}")
        
        if self.state == TrainerState.INSTRUCTION and self.current_obstacle:
            expected = INSTRUCTIONS[self.current_obstacle.type]['direction']
            print(f"  🎯 Expected: {expected} | Got: {dir_val}")
            
            if dir_val == expected:
                self._on_correct_gesture(dir_val)
            else:
                self._on_wrong_gesture(dir_val, expected)
    
    def keyPressEvent(self, event):
        """Handle keyboard input"""
        key = event.key()
        
        if self.state == TrainerState.WELCOME:
            self._start_game()
            return
        
        if self.state == TrainerState.GAME_OVER:
            self.restart_game()
            return
        
        if self.state == TrainerState.INSTRUCTION:
            if key in (Qt.Key_Up, Qt.Key_W):
                self.handle_direction("UP")
            elif key in (Qt.Key_Down, Qt.Key_S):
                self.handle_direction("DOWN")
            elif key in (Qt.Key_Left, Qt.Key_A):
                self.handle_direction("LEFT")
            elif key in (Qt.Key_Right, Qt.Key_D):
                self.handle_direction("RIGHT")
        
        # Toggle analytics
        if key == Qt.Key_Tab:
            self.show_mini_analytics = not self.show_mini_analytics
    
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if self.state == TrainerState.WELCOME:
            self._start_game()
        elif self.state == TrainerState.GAME_OVER:
            self.restart_game()
    
    def cleanup(self):
        """Clean up resources"""
        self.timer.stop()
        
        # Save AI progress
        if self.ai_enabled and self.ai_learner:
            if hasattr(self.ai_learner, 'current_session') and self.ai_learner.current_session:
                self.ai_learner.end_session()
            self.ai_learner.save_progress()
        
        print("  ✅ AI Trainer cleanup complete")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN - STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    print("\n" + "=" * 70)
    print("  🤖 AI TRAINER GAME - Enhanced Version (Standalone Test)")
    print("=" * 70)
    print("  Controls:")
    print("    WASD / Arrow Keys = Directions")
    print("    Click = Start / Restart")
    print("    TAB = Toggle mini analytics")
    print("=" * 70)
    print(f"  AI Learning: {'✅ ENABLED' if AI_LEARNER_AVAILABLE else '❌ DISABLED'}")
    print("=" * 70 + "\n")
    
    app = QApplication(sys.argv)
    game = AITrainerGame()
    game.resize(850, 650)
    game.setWindowTitle("AI Trainer Game - Enhanced Test")
    game.show()
    
    sys.exit(app.exec())
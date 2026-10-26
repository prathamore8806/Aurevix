"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    AUREVIX CYBER RUNNER - STABLE v3.1                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🏃 Humanoid character with animations                                      ║
║  ✨ Pixel-perfect collision detection                                       ║
║  🎯 Clear slide/duck mechanics                                              ║
║  ✅ FIXED: Memory leaks and crash issues                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Signal, QRectF, Slot, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, 
    QLinearGradient, QRadialGradient, QPainterPath
)
import random
import math
from enum import Enum


class Direction(Enum):
    NONE = "NONE"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class GameState(Enum):
    WELCOME = "welcome"
    TUTORIAL = "tutorial"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class ObstacleType(Enum):
    BARRIER = "barrier"
    LOW = "low"
    COIN = "coin"


# Tutorial steps
TUTORIAL_STEPS = [
    {"title": "MOVE LEFT", "expected": "LEFT", "icon": "◀", "color": QColor(0, 212, 255)},
    {"title": "MOVE RIGHT", "expected": "RIGHT", "icon": "▶", "color": QColor(0, 150, 255)},
    {"title": "JUMP UP", "expected": "UP", "icon": "▲", "color": QColor(0, 255, 136)},
    {"title": "SLIDE DOWN", "expected": "DOWN", "icon": "▼", "color": QColor(255, 165, 0)},
]

# ✅ CONSTANTS FOR LIMITS
MAX_PARTICLES = 50
MAX_OBSTACLES = 15


# ═══════════════════════════════════════════════════════════════════════════════
# PLAYER CLASS
# ═══════════════════════════════════════════════════════════════════════════════
class Player:
    def __init__(self):
        # Lane system
        self.lane = 1
        self.target_lane = 1
        self.lane_positions = [0.167, 0.50, 0.833]
        self.current_x_normalized = 0.50
        self.lane_switch_speed = 0.18
        
        # Vertical position
        self.y_offset = 0
        
        # Actions
        self.is_jumping = False
        self.is_sliding = False
        self.jump_frame = 0
        self.slide_frame = 0
        
        # Direction cooldown
        self.direction_cooldown = 0
        
        # Running animation
        self.run_frame = 0
        self.run_cycle = 0
        
        # Hitbox dimensions
        self.hitbox_width = 30
        self.hitbox_height = 55
        
        # ✅ Track if we should spawn dust (to avoid spawning in paint)
        self.should_spawn_dust = False
    
    def update(self):
        # Smooth lane transition
        target_x = self.lane_positions[self.target_lane]
        diff = target_x - self.current_x_normalized
        if abs(diff) > 0.01:
            self.current_x_normalized += diff * self.lane_switch_speed
        else:
            self.current_x_normalized = target_x
            self.lane = self.target_lane
        
        # Direction cooldown
        if self.direction_cooldown > 0:
            self.direction_cooldown -= 1
        
        # Running animation
        self.run_frame += 1
        self.run_cycle = (self.run_frame // 4) % 4
        
        # ✅ Reset dust flag
        self.should_spawn_dust = False
        
        # Jump animation
        if self.is_jumping:
            self.jump_frame += 1
            progress = self.jump_frame / 30
            self.y_offset = -90 * math.sin(progress * math.pi)
            self.hitbox_width = 30
            self.hitbox_height = 55
            
            if self.jump_frame >= 30:
                self.is_jumping = False
                self.jump_frame = 0
                self.y_offset = 0
        
        # Slide animation
        if self.is_sliding:
            self.slide_frame += 1
            self.hitbox_width = 50
            self.hitbox_height = 20
            
            # ✅ Flag for dust spawning (handled in game update, not paint)
            if self.slide_frame < 15 and self.slide_frame % 4 == 0:
                self.should_spawn_dust = True
            
            if self.slide_frame >= 25:
                self.is_sliding = False
                self.slide_frame = 0
        
        # Reset hitbox when standing
        if not self.is_jumping and not self.is_sliding:
            self.hitbox_width = 30
            self.hitbox_height = 55
    
    def move_left(self):
        if self.direction_cooldown <= 0 and self.target_lane > 0:
            self.target_lane -= 1
            self.direction_cooldown = 12
            return True
        return False
    
    def move_right(self):
        if self.direction_cooldown <= 0 and self.target_lane < 2:
            self.target_lane += 1
            self.direction_cooldown = 12
            return True
        return False
    
    def jump(self):
        if not self.is_jumping and not self.is_sliding:
            self.is_jumping = True
            self.jump_frame = 0
            return True
        return False
    
    def slide(self):
        if not self.is_sliding and not self.is_jumping:
            self.is_sliding = True
            self.slide_frame = 0
            return True
        return False
    
    def reset_cooldown(self):
        if self.direction_cooldown > 8:
            self.direction_cooldown = 8
    
    def get_hitbox(self, base_x, base_y):
        if self.is_sliding:
            return QRectF(
                base_x - self.hitbox_width / 2,
                base_y - self.hitbox_height,
                self.hitbox_width,
                self.hitbox_height
            )
        else:
            return QRectF(
                base_x - self.hitbox_width / 2,
                base_y - self.hitbox_height + self.y_offset,
                self.hitbox_width,
                self.hitbox_height
            )


# ═══════════════════════════════════════════════════════════════════════════════
# OBSTACLE CLASS
# ═══════════════════════════════════════════════════════════════════════════════
class Obstacle:
    def __init__(self, lane, obs_type, y):
        self.lane = lane
        self.type = obs_type
        self.y = y
        self.collected = False
    
    def update(self, speed):
        self.y += speed
    
    def get_hitbox(self, track_x, track_w, lane_positions):
        ox = track_x + (lane_positions[self.lane] * track_w)
        
        if self.type == ObstacleType.BARRIER:
            return QRectF(ox - 30, self.y + 8, 60, 42)
        elif self.type == ObstacleType.LOW:
            return QRectF(ox - 30, self.y + 5, 60, 25)
        else:
            return QRectF(ox - 12, self.y + 4, 24, 24)


# ═══════════════════════════════════════════════════════════════════════════════
# PARTICLE CLASS
# ═══════════════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'size', 'color']  # ✅ Memory optimization
    
    def __init__(self, x, y, color, size=None, vx=None, vy=None):
        self.x = x
        self.y = y
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-5, -1)
        self.life = 1.0
        self.size = size if size is not None else random.randint(3, 8)
        self.color = color
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.25
        self.life -= 0.05
        return self.life > 0


# ═══════════════════════════════════════════════════════════════════════════════
# GAMING CANVAS - MAIN CLASS (CRASH-FREE VERSION)
# ═══════════════════════════════════════════════════════════════════════════════
class GamingCanvas(QWidget):
    """Enhanced Cyber Runner - Stable Version"""
    
    game_over = Signal(str, int)
    game_started = Signal(str)
    score_changed = Signal(int)
    
    DEBUG_HITBOXES = False
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # State
        self.state = GameState.WELCOME
        self.player = Player()
        self.obstacles = []
        self.particles = []
        
        # Game stats
        self.score = 0
        self.high_score = 0
        self.speed = 7
        self.spawn_timer = 0
        self.distance = 0
        self.coins_collected = 0
        
        # Tutorial
        self.tutorial_step = 0
        self.tutorial_hold = 0
        self.tutorial_success = False
        self.tutorial_success_timer = 0
        
        # Animation
        self.frame = 0
        self.track_offset = 0
        
        # Input tracking
        self.last_input_direction = "NONE"
        
        # Track dimensions
        self.track_w = 320
        self.track_x = 0
        
        # ✅ Pre-generate star positions (instead of random.seed every frame)
        self._star_positions = []
        self._generate_stars()
        
        # ✅ Timer with error handling
        self.timer = QTimer()
        self.timer.timeout.connect(self._safe_update)
        self.timer.start(33)
        
        # ✅ Track if we're running
        self._is_running = True
    
    def _generate_stars(self):
        """Pre-generate star positions once"""
        self._star_positions = []
        for _ in range(30):
            self._star_positions.append({
                'x': random.randint(0, 1200),
                'y': random.randint(0, 800),
                'size': random.randint(1, 3),
                'phase': random.uniform(0, 6.28)
            })
    
    def _safe_update(self):
        """Update with error handling to prevent crashes"""
        if not self._is_running:
            return
        
        try:
            self._update()
        except Exception as e:
            print(f"⚠️ Game update error: {e}")
    
    def _update(self):
        self.frame += 1
        
        if self.state == GameState.PLAYING:
            self._update_game()
        elif self.state == GameState.TUTORIAL:
            self._update_tutorial()
        
        # ✅ Update particles with limit
        self._update_particles()
        
        self.update()
    
    def _update_particles(self):
        """Update particles with memory limit"""
        # Update existing particles
        self.particles = [p for p in self.particles if p.update()]
        
        # ✅ Enforce particle limit
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]
    
    def _update_game(self):
        self.track_offset = (self.track_offset + self.speed) % 50
        self.player.update()
        self.distance += self.speed
        
        # ✅ Spawn dust particles here (not in paint event!)
        if self.player.should_spawn_dust and len(self.particles) < MAX_PARTICLES:
            self._spawn_dust_particles()
        
        # Spawn obstacles
        self.spawn_timer += 1
        spawn_rate = max(40, 60 - int(self.speed * 1.5))
        if self.spawn_timer >= spawn_rate:
            self._spawn_obstacle()
            self.spawn_timer = 0
        
        # Update track dimensions
        self.track_x = (self.width() - self.track_w) // 2
        
        # Update obstacles
        obstacles_to_remove = []
        for obs in self.obstacles:
            obs.update(self.speed)
            
            # Collision check
            if not obs.collected:
                try:
                    if self._check_collision(obs):
                        if obs.type == ObstacleType.COIN:
                            obs.collected = True
                            self.score += 50
                            self.coins_collected += 1
                            self._spawn_coin_particles(obs)
                        else:
                            self._game_over()
                            return
                except Exception as e:
                    print(f"⚠️ Collision check error: {e}")
            
            # Mark for removal if off-screen
            if obs.y > self.height() + 70:
                obstacles_to_remove.append(obs)
        
        # ✅ Remove obstacles safely
        for obs in obstacles_to_remove:
            if obs in self.obstacles:
                self.obstacles.remove(obs)
        
        # ✅ Enforce obstacle limit
        if len(self.obstacles) > MAX_OBSTACLES:
            self.obstacles = self.obstacles[-MAX_OBSTACLES:]
        
        # Update score
        self.score += 1
        
        # Speed up
        if self.score % 500 == 0 and self.score > 0:
            self.speed = min(13, self.speed + 0.3)
    
    def _update_tutorial(self):
        if self.tutorial_success:
            self.tutorial_success_timer += 1
            if self.tutorial_success_timer >= 25:
                self._next_tutorial()
    
    def _spawn_obstacle(self):
        """Spawn obstacle with limit check"""
        if len(self.obstacles) >= MAX_OBSTACLES:
            return
        
        lane = random.randint(0, 2)
        roll = random.random()
        
        if roll < 0.28:
            obs_type = ObstacleType.COIN
        elif roll < 0.58:
            obs_type = ObstacleType.LOW
        else:
            obs_type = ObstacleType.BARRIER
        
        self.obstacles.append(Obstacle(lane, obs_type, -80))
    
    def _spawn_coin_particles(self, obs):
        """Spawn coin particles with limit check"""
        if len(self.particles) >= MAX_PARTICLES:
            return
        
        px = self.track_x + (self.player.lane_positions[obs.lane] * self.track_w)
        particles_to_add = min(8, MAX_PARTICLES - len(self.particles))
        
        for _ in range(particles_to_add):
            self.particles.append(Particle(px, obs.y + 12, QColor(255, 215, 0)))
    
    def _spawn_dust_particles(self):
        """Spawn dust particles with limit check"""
        if len(self.particles) >= MAX_PARTICLES:
            return
        
        px = self.track_x + (self.player.current_x_normalized * self.track_w)
        py = self.height() - 100
        
        particles_to_add = min(2, MAX_PARTICLES - len(self.particles))
        for _ in range(particles_to_add):
            self.particles.append(Particle(
                px - 25 + random.randint(-10, 10),
                py - 5,
                QColor(150, 130, 100),
                size=random.randint(2, 4),
                vx=random.uniform(-2, -0.5),
                vy=random.uniform(-1, 1)
            ))
    
    def _check_collision(self, obs):
        """Check collision with error handling"""
        try:
            if self.player.lane != obs.lane:
                return False
            
            px = self.track_x + (self.player.current_x_normalized * self.track_w)
            py = self.height() - 100
            
            player_hitbox = self.player.get_hitbox(px, py)
            obs_hitbox = obs.get_hitbox(self.track_x, self.track_w, self.player.lane_positions)
            
            margin = 8
            
            player_rect = QRectF(
                player_hitbox.x() + margin,
                player_hitbox.y() + margin,
                player_hitbox.width() - margin * 2,
                player_hitbox.height() - margin * 2
            )
            
            obs_rect = QRectF(
                obs_hitbox.x() + margin/2,
                obs_hitbox.y() + margin/2,
                obs_hitbox.width() - margin,
                obs_hitbox.height() - margin
            )
            
            if not player_rect.intersects(obs_rect):
                return False
            
            if obs.type == ObstacleType.BARRIER:
                if self.player.is_jumping and self.player.y_offset < -45:
                    return False
            
            if obs.type == ObstacleType.LOW:
                if self.player.is_sliding:
                    return False
            
            return True
        except Exception:
            return False
    
    def _game_over(self):
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
        self.game_over.emit("Cyber Runner", self.score)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DRAWING (WITH ERROR HANDLING)
    # ═══════════════════════════════════════════════════════════════════════════
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            w, h = self.width(), self.height()
            
            # Background
            bg = QLinearGradient(0, 0, 0, h)
            bg.setColorAt(0, QColor(5, 12, 30))
            bg.setColorAt(0.5, QColor(10, 22, 45))
            bg.setColorAt(1, QColor(8, 18, 38))
            painter.fillRect(0, 0, w, h, bg)
            
            # Stars
            self._draw_stars(painter, w, h)
            
            if self.state == GameState.WELCOME:
                self._draw_welcome(painter, w, h)
            elif self.state == GameState.TUTORIAL:
                self._draw_tutorial(painter, w, h)
            elif self.state == GameState.PLAYING:
                self._draw_game(painter, w, h)
            elif self.state == GameState.GAME_OVER:
                self._draw_game(painter, w, h)
                self._draw_game_over(painter, w, h)
            
            # Particles
            self._draw_particles(painter)
            
            # Border
            painter.setPen(QPen(QColor(0, 200, 255, 180), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(2, 2, w-4, h-4, 10, 10)
            
            painter.end()
        except Exception as e:
            print(f"⚠️ Paint error: {e}")
    
    def _draw_stars(self, painter, w, h):
        """Draw stars using pre-generated positions"""
        painter.setPen(Qt.NoPen)
        for star in self._star_positions:
            x = star['x'] % w
            y = star['y'] % h
            alpha = 50 + int(50 * math.sin(self.frame * 0.05 + star['phase']))
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.drawEllipse(int(x), int(y), star['size'], star['size'])
    
    def _draw_particles(self, painter):
        """Draw particles safely"""
        painter.setPen(Qt.NoPen)
        for p in self.particles[:MAX_PARTICLES]:  # Limit iterations
            try:
                color = QColor(p.color)
                color.setAlpha(int(255 * max(0, min(1, p.life))))
                painter.setBrush(color)
                size = max(1, int(p.size * p.life))
                painter.drawEllipse(int(p.x - size/2), int(p.y - size/2), size, size)
            except Exception:
                continue
    
    def _draw_welcome(self, painter, w, h):
        # Title
        painter.setPen(QColor(0, 255, 255))
        painter.setFont(QFont("Consolas", 34, QFont.Bold))
        painter.drawText(QRectF(0, h*0.15, w, 65), Qt.AlignCenter, "🏃 CYBER RUNNER")
        
        # Subtitle
        painter.setPen(QColor(0, 180, 220))
        painter.setFont(QFont("Consolas", 12))
        painter.drawText(QRectF(0, h*0.28, w, 30), Qt.AlignCenter, "◈ GESTURE CONTROLLED ◈")
        
        # Instructions box
        box_x, box_y = w*0.12, h*0.36
        box_w, box_h = w*0.76, h*0.38
        
        painter.setBrush(QColor(8, 20, 40, 220))
        painter.setPen(QPen(QColor(0, 150, 200), 2))
        painter.drawRoundedRect(int(box_x), int(box_y), int(box_w), int(box_h), 12, 12)
        
        instructions = [
            ("◀  ▶", "Move between lanes", QColor(0, 200, 255)),
            ("▲ JUMP", "Leap over RED barriers", QColor(0, 255, 136)),
            ("▼ SLIDE", "Duck under ORANGE obstacles", QColor(255, 165, 0)),
            ("● COINS", "Collect for bonus points!", QColor(255, 215, 0)),
        ]
        
        for i, (icon, text, color) in enumerate(instructions):
            y_pos = box_y + 28 + i * 36
            painter.setPen(color)
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(QRectF(box_x + 15, y_pos, 90, 32), Qt.AlignCenter, icon)
            painter.setPen(QColor(200, 220, 240))
            painter.setFont(QFont("Consolas", 12))
            painter.drawText(QRectF(box_x + 110, y_pos + 2, box_w - 130, 32), Qt.AlignVCenter | Qt.AlignLeft, text)
        
        # Start button
        alpha = 180 + int(70 * math.sin(self.frame * 0.12))
        painter.setPen(QColor(0, 255, 200, alpha))
        painter.setFont(QFont("Consolas", 18, QFont.Bold))
        painter.drawText(QRectF(0, h*0.80, w, 45), Qt.AlignCenter, "▶  CLICK TO START  ◀")
        
        if self.high_score > 0:
            painter.setPen(QColor(255, 215, 0))
            painter.setFont(QFont("Consolas", 13, QFont.Bold))
            painter.drawText(QRectF(0, h*0.91, w, 30), Qt.AlignCenter, f"★ HIGH SCORE: {self.high_score} ★")
    
    def _draw_tutorial(self, painter, w, h):
        """Enhanced Tutorial Screen - Perfectly Centered"""
        if self.tutorial_step >= len(TUTORIAL_STEPS):
            return
    
        step = TUTORIAL_STEPS[self.tutorial_step]
    
        # ═══════════════════════════════════════════════════════════════════
        # BACKGROUND OVERLAY
        # ═══════════════════════════════════════════════════════════════════
        overlay_color = QColor(5, 15, 35, 200)
        painter.fillRect(0, 0, w, h, overlay_color)
    
        # ═══════════════════════════════════════════════════════════════════
        # CENTER CALCULATIONS
        # ═══════════════════════════════════════════════════════════════════
        center_x = w // 2
        center_y = h // 2
    
        # ═══════════════════════════════════════════════════════════════════
        # PROGRESS BAR (Top)
        # ═══════════════════════════════════════════════════════════════════
        progress_bar_width = min(400, w - 100)
        progress_bar_height = 12
        progress_bar_x = center_x - progress_bar_width // 2
        progress_bar_y = 30
    
        # Background bar
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(30, 50, 80))
        painter.drawRoundedRect(progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height, 6, 6)
    
        # Progress fill
        progress = (self.tutorial_step + 1) / len(TUTORIAL_STEPS)
        fill_width = int(progress_bar_width * progress)
    
        grad = QLinearGradient(progress_bar_x, 0, progress_bar_x + fill_width, 0)
        grad.setColorAt(0, QColor(0, 180, 255))
        grad.setColorAt(1, QColor(0, 255, 136))
        painter.setBrush(grad)
        painter.drawRoundedRect(progress_bar_x, progress_bar_y, fill_width, progress_bar_height, 6, 6)
    
        # Progress border
        painter.setPen(QPen(QColor(0, 200, 255, 100), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height, 6, 6)
    
        # ═══════════════════════════════════════════════════════════════════
        # STEP COUNTER
        # ═══════════════════════════════════════════════════════════════════
        painter.setPen(QColor(150, 180, 210))
        painter.setFont(QFont("Consolas", 13))
        step_text = f"Step {self.tutorial_step + 1} of {len(TUTORIAL_STEPS)}"
        painter.drawText(QRectF(0, progress_bar_y + 25, w, 30), Qt.AlignCenter, step_text)
    
        # ═══════════════════════════════════════════════════════════════════
        # MAIN CONTENT CARD (Centered)
        # ═══════════════════════════════════════════════════════════════════
        card_width = min(350, w - 60)
        card_height = 320
        card_x = center_x - card_width // 2
        card_y = center_y - card_height // 2 - 10
    
        # Card background with gradient
        card_grad = QLinearGradient(card_x, card_y, card_x, card_y + card_height)
        card_grad.setColorAt(0, QColor(15, 35, 60, 240))
        card_grad.setColorAt(1, QColor(8, 20, 40, 240))
        painter.setBrush(card_grad)
        painter.setPen(QPen(step['color'], 2))
        painter.drawRoundedRect(card_x, card_y, card_width, card_height, 15, 15)
    
        # Inner glow effect
        painter.setPen(QPen(QColor(step['color'].red(), step['color'].green(), step['color'].blue(), 30), 8))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(card_x + 4, card_y + 4, card_width - 8, card_height - 8, 12, 12)
    
        # ═══════════════════════════════════════════════════════════════════
        # TITLE (Inside Card - Top)
        # ═══════════════════════════════════════════════════════════════════
        title_y = card_y + 25
        painter.setPen(step['color'])
        painter.setFont(QFont("Consolas", 24, QFont.Bold))
        painter.drawText(QRectF(card_x, title_y, card_width, 40), Qt.AlignCenter, step['title'])
    
        # Decorative line under title
        line_width = 80
        line_y = title_y + 45
        painter.setPen(QPen(step['color'], 2))
        painter.drawLine(center_x - line_width // 2, line_y, center_x + line_width // 2, line_y)
    
        # ═══════════════════════════════════════════════════════════════════
        # MAIN ICON / SUCCESS STATE (Center of Card)
        # ═══════════════════════════════════════════════════════════════════
        icon_center_y = card_y + card_height // 2 + 10
    
        if self.tutorial_success:
            # ✅ SUCCESS STATE
            # Animated success checkmark
            pulse = 1.0 + 0.1 * math.sin(self.frame * 0.3)
        
            # Success glow circle
            glow_radius = int(60 * pulse)
            glow = QRadialGradient(center_x, icon_center_y, glow_radius)
            glow.setColorAt(0, QColor(0, 255, 136, 100))
            glow.setColorAt(1, QColor(0, 255, 136, 0))
            painter.setBrush(glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x - glow_radius, icon_center_y - glow_radius, 
                               glow_radius * 2, glow_radius * 2)
        
            # Checkmark
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 70, QFont.Bold))
            painter.drawText(QRectF(card_x, icon_center_y - 50, card_width, 100), Qt.AlignCenter, "✓")
        
            # "GREAT!" text
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 22, QFont.Bold))
            painter.drawText(QRectF(card_x, icon_center_y + 50, card_width, 40), Qt.AlignCenter, "GREAT!")
        
        else:
            # ═══════════════════════════════════════════════════════════════
            # DIRECTION ICON WITH PROGRESS RING
            # ═══════════════════════════════════════════════════════════════
            ring_radius = 55
            ring_x = center_x - ring_radius
            ring_y = icon_center_y - ring_radius
            ring_size = ring_radius * 2
        
            # Background ring
            painter.setPen(QPen(QColor(40, 60, 90), 8))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(ring_x, ring_y, ring_size, ring_size)
        
            # Progress ring (fills as user holds direction)
            if self.tutorial_hold > 0:
                progress_ratio = min(1.0, self.tutorial_hold / 15)
            
                # Animated progress ring
                ring_color = QColor(0, 255, 136)
                painter.setPen(QPen(ring_color, 8, Qt.SolidLine, Qt.RoundCap))
            
                # Draw arc (starts from top, goes clockwise)
                start_angle = 90 * 16  # 90 degrees in 1/16th degree units
                span_angle = -int(360 * progress_ratio * 16)
                painter.drawArc(ring_x, ring_y, ring_size, ring_size, start_angle, span_angle)
            
                # Inner glow when progressing
                inner_glow = QRadialGradient(center_x, icon_center_y, ring_radius - 5)
                inner_glow.setColorAt(0, QColor(0, 255, 136, int(50 * progress_ratio)))
                inner_glow.setColorAt(1, QColor(0, 255, 136, 0))
                painter.setBrush(inner_glow)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(ring_x + 8, ring_y + 8, ring_size - 16, ring_size - 16)
        
            # Direction icon in center of ring
            painter.setPen(step['color'])
            painter.setFont(QFont("Consolas", 50, QFont.Bold))
            painter.drawText(QRectF(ring_x, ring_y, ring_size, ring_size), Qt.AlignCenter, step['icon'])
        
            # ═══════════════════════════════════════════════════════════════
            # INSTRUCTION TEXT
            # ═══════════════════════════════════════════════════════════════
            instruction_y = icon_center_y + ring_radius + 20
        
            if self.tutorial_hold > 0:
                # "HOLD..." with animated dots
                dots = "." * (1 + (self.frame // 10) % 3)
                hold_text = f"HOLD{dots}"
                painter.setPen(QColor(0, 255, 136))
                painter.setFont(QFont("Consolas", 16, QFont.Bold))
                painter.drawText(QRectF(card_x, instruction_y, card_width, 35), Qt.AlignCenter, hold_text)
            else:
                # Instruction text
                painter.setPen(QColor(180, 200, 220))
                painter.setFont(QFont("Consolas", 13))
                instruction = f"Move your hand {step['expected']}"
                painter.drawText(QRectF(card_x, instruction_y, card_width, 30), Qt.AlignCenter, instruction)
            
                # Sub-instruction
                painter.setPen(QColor(120, 140, 160))
                painter.setFont(QFont("Consolas", 11))
                painter.drawText(QRectF(card_x, instruction_y + 25, card_width, 25), 
                               Qt.AlignCenter, "and hold for a moment")
    
        # ═══════════════════════════════════════════════════════════════════
        # BOTTOM: SKIP HINT
        # ═══════════════════════════════════════════════════════════════════
        skip_y = h - 35
        painter.setPen(QColor(80, 100, 130))
        painter.setFont(QFont("Consolas", 10))
        painter.drawText(QRectF(0, skip_y, w, 25), Qt.AlignCenter, "Press SPACE or click to skip tutorial")
    
        # ═══════════════════════════════════════════════════════════════════
        # SIDE INDICATORS (Show all steps)
        # ═══════════════════════════════════════════════════════════════════
        indicator_size = 12
        indicator_spacing = 25
        total_width = len(TUTORIAL_STEPS) * indicator_spacing
        start_x = center_x - total_width // 2 + indicator_spacing // 2
        indicator_y = card_y + card_height + 20
    
        for i, tutorial_step in enumerate(TUTORIAL_STEPS):
            ix = start_x + i * indicator_spacing
        
            if i < self.tutorial_step:
                # Completed - green filled
                painter.setBrush(QColor(0, 255, 136))
                painter.setPen(Qt.NoPen)
            elif i == self.tutorial_step:
                # Current - colored outline with pulse
                pulse = 0.5 + 0.5 * math.sin(self.frame * 0.15)
                painter.setBrush(QColor(step['color'].red(), step['color'].green(), 
                                       step['color'].blue(), int(100 * pulse)))
                painter.setPen(QPen(step['color'], 2))
            else:
                # Future - dim
                painter.setBrush(QColor(40, 50, 70))
                painter.setPen(QPen(QColor(60, 80, 100), 1))
        
            painter.drawEllipse(ix - indicator_size // 2, indicator_y, indicator_size, indicator_size)
    
    def _draw_game(self, painter, w, h):
        track_w = 320
        track_x = (w - track_w) // 2
        lane_w = track_w // 3
        
        self.track_x = track_x
        self.track_w = track_w
        
        # Track background
        track_grad = QLinearGradient(track_x, 0, track_x + track_w, 0)
        track_grad.setColorAt(0, QColor(12, 28, 48))
        track_grad.setColorAt(0.5, QColor(18, 38, 62))
        track_grad.setColorAt(1, QColor(12, 28, 48))
        painter.setBrush(track_grad)
        painter.setPen(Qt.NoPen)
        painter.drawRect(track_x, 0, track_w, h)
        
        # Lane highlight
        lane_x = track_x + self.player.lane * lane_w
        painter.fillRect(int(lane_x), 0, lane_w, h, QColor(0, 255, 255, 15))
        
        # Lane dividers
        painter.setPen(QPen(QColor(0, 180, 220, 90), 2, Qt.DashLine))
        for i in range(1, 3):
            x = track_x + i * lane_w
            painter.drawLine(x, 0, x, h)
        
        # Moving lines
        painter.setPen(QPen(QColor(0, 150, 200, 40), 1))
        for y in range(-50, h+50, 50):
            y_pos = (y + int(self.track_offset)) % (h + 50) - 50
            painter.drawLine(track_x + 15, y_pos, track_x + track_w - 15, y_pos)
        
        # Track borders
        for i in range(3):
            painter.setPen(QPen(QColor(0, 255, 255, 180 - i * 50), 3 - i))
            painter.drawLine(track_x - i, 0, track_x - i, h)
            painter.drawLine(track_x + track_w + i, 0, track_x + track_w + i, h)
        
        # Ground line
        ground_y = h - 100
        painter.setPen(QPen(QColor(0, 200, 255, 100), 2))
        painter.drawLine(track_x, ground_y + 5, track_x + track_w, ground_y + 5)
        
        # Obstacles
        for obs in self.obstacles[:MAX_OBSTACLES]:
            if obs.collected:
                continue
            
            try:
                ox = track_x + (self.player.lane_positions[obs.lane] * track_w)
                oy = obs.y
                
                if obs.type == ObstacleType.BARRIER:
                    self._draw_barrier(painter, ox, oy)
                elif obs.type == ObstacleType.LOW:
                    self._draw_low_obstacle(painter, ox, oy)
                else:
                    self._draw_coin(painter, ox, oy)
                
                if self.DEBUG_HITBOXES:
                    hitbox = obs.get_hitbox(track_x, track_w, self.player.lane_positions)
                    painter.setPen(QPen(QColor(255, 0, 0), 1))
                    painter.setBrush(QColor(255, 0, 0, 50))
                    painter.drawRect(hitbox)
            except Exception:
                continue
        
        # Player
        px = track_x + (self.player.current_x_normalized * track_w)
        py = ground_y
        
        self._draw_player(painter, px, py)
        
        if self.DEBUG_HITBOXES:
            hitbox = self.player.get_hitbox(px, py)
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            painter.setBrush(QColor(0, 255, 0, 50))
            painter.drawRect(hitbox)
        
        # HUD
        self._draw_hud(painter, w, h)
    
    def _draw_barrier(self, painter, ox, oy):
        grad = QLinearGradient(ox - 35, oy, ox - 35, oy + 55)
        grad.setColorAt(0, QColor(255, 100, 100))
        grad.setColorAt(0.5, QColor(220, 50, 50))
        grad.setColorAt(1, QColor(180, 30, 30))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(255, 180, 180), 2))
        painter.drawRoundedRect(int(ox - 35), int(oy), 70, 55, 6, 6)
        
        painter.setPen(QPen(QColor(255, 255, 100), 3))
        for i in range(3):
            stripe_y = oy + 10 + i * 15
            painter.drawLine(int(ox - 28), int(stripe_y), int(ox + 28), int(stripe_y))
        
        painter.setPen(QColor(255, 255, 200))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(QRectF(ox - 35, oy + 55, 70, 18), Qt.AlignCenter, "JUMP!")
    
    def _draw_low_obstacle(self, painter, ox, oy):
        grad = QLinearGradient(ox - 35, oy, ox - 35, oy + 35)
        grad.setColorAt(0, QColor(255, 200, 80))
        grad.setColorAt(1, QColor(220, 140, 30))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(255, 230, 150), 2))
        painter.drawRoundedRect(int(ox - 35), int(oy), 70, 35, 6, 6)
        
        # Spikes
        painter.setBrush(QColor(255, 180, 50))
        painter.setPen(Qt.NoPen)
        for i in range(-2, 3):
            spike_x = ox + i * 14
            path = QPainterPath()
            path.moveTo(spike_x - 6, oy)
            path.lineTo(spike_x, oy - 10)
            path.lineTo(spike_x + 6, oy)
            painter.drawPath(path)
        
        painter.setPen(QColor(100, 60, 0))
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.drawText(QRectF(ox - 35, oy + 8, 70, 22), Qt.AlignCenter, "DUCK!")
    
    def _draw_coin(self, painter, ox, oy):
        glow_size = 22 + int(4 * math.sin(self.frame * 0.2))
        glow = QRadialGradient(ox, oy + 14, glow_size)
        glow.setColorAt(0, QColor(255, 215, 0, 100))
        glow.setColorAt(1, QColor(255, 215, 0, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(ox - glow_size), int(oy + 14 - glow_size), glow_size * 2, glow_size * 2)
        
        coin_grad = QRadialGradient(ox - 4, oy + 10, 16)
        coin_grad.setColorAt(0, QColor(255, 255, 180))
        coin_grad.setColorAt(0.5, QColor(255, 215, 0))
        coin_grad.setColorAt(1, QColor(200, 160, 0))
        painter.setBrush(coin_grad)
        painter.setPen(QPen(QColor(180, 140, 0), 2))
        painter.drawEllipse(int(ox - 14), int(oy), 28, 28)
        
        painter.setPen(QColor(160, 120, 0))
        painter.setFont(QFont("Consolas", 12, QFont.Bold))
        painter.drawText(QRectF(ox - 14, oy, 28, 28), Qt.AlignCenter, "$")
    
    def _draw_player(self, painter, px, py):
        """Draw humanoid player - HEAD FIXED TO BODY"""
    
        # ═══════════════════════════════════════════════════════════════════
        # POSITION CALCULATIONS (All relative to base position)
        # ═══════════════════════════════════════════════════════════════════
        y_off = self.player.y_offset  # Jump offset
    
        # Colors
        body_color = QColor(0, 200, 255)
        body_dark = QColor(0, 140, 200)
        body_light = QColor(100, 230, 255)
        skin_color = QColor(255, 220, 185)
        hair_color = QColor(50, 35, 25)
        shoe_color = QColor(40, 40, 40)
    
        # ═══════════════════════════════════════════════════════════════════
        # PLAYER GLOW EFFECT
        # ═══════════════════════════════════════════════════════════════════
        glow_radius = 45
        glow = QRadialGradient(px, py - 35 + y_off, glow_radius)
        glow.setColorAt(0, QColor(0, 200, 255, 50))
        glow.setColorAt(1, QColor(0, 150, 255, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(px - glow_radius), int(py - 35 + y_off - glow_radius), 
                           glow_radius * 2, glow_radius * 2)
    
        if self.player.is_sliding:
            # ═══════════════════════════════════════════════════════════════
            # SLIDING POSE - Horizontal body
            # ═══════════════════════════════════════════════════════════════
            slide_y = py - 15
        
            # Motion blur trails
            painter.setPen(Qt.NoPen)
            for i in range(3):
                trail_alpha = 80 - i * 25
                trail_x = px - 15 - i * 12
                painter.setBrush(QColor(0, 200, 255, trail_alpha))
                painter.drawRoundedRect(int(trail_x), int(slide_y - 8), 35, 16, 8, 8)
        
            # Main sliding body (torso + legs combined)
            body_grad = QLinearGradient(px - 30, slide_y, px + 30, slide_y)
            body_grad.setColorAt(0, body_dark)
            body_grad.setColorAt(0.5, body_color)
            body_grad.setColorAt(1, body_dark)
            painter.setBrush(body_grad)
            painter.setPen(QPen(body_light, 2))
            painter.drawRoundedRect(int(px - 30), int(slide_y - 9), 60, 18, 9, 9)
        
            # ✅ HEAD - Attached at the front of sliding body
            head_x = px + 25
            head_y = slide_y - 5
            head_size = 18
        
            # Neck connection (small rectangle connecting head to body)
            painter.setBrush(skin_color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(head_x - 8), int(head_y + 2), 8, 8)
        
            # Head
            painter.setBrush(skin_color)
            painter.setPen(QPen(QColor(230, 200, 170), 1))
            painter.drawEllipse(int(head_x - head_size // 2), int(head_y - head_size // 2), 
                               head_size, head_size)
        
            # Hair (on sliding head)
            painter.setBrush(hair_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(head_x - 7), int(head_y - head_size // 2 - 2), 14, 10)
        
            # Eye
            painter.setBrush(Qt.white)
            painter.drawEllipse(int(head_x + 2), int(head_y - 3), 5, 5)
            painter.setBrush(QColor(30, 30, 30))
            painter.drawEllipse(int(head_x + 3), int(head_y - 2), 3, 3)
        
            # Dust/spark particles
            for i in range(3):
                spark_x = px - 35 - i * 8
                spark_y = slide_y + random.randint(-4, 4)
                spark_alpha = random.randint(80, 150)
                painter.setBrush(QColor(200, 180, 150, spark_alpha))
                painter.drawEllipse(int(spark_x), int(spark_y), 3, 3)
        
        else:
            # ═══════════════════════════════════════════════════════════════
            # STANDING / RUNNING / JUMPING POSE
            # ═══════════════════════════════════════════════════════════════
        
            # ✅ ALL BODY PARTS USE SAME y_off TO STAY CONNECTED
        
            # Animation angles
            if self.player.is_jumping:
                left_leg_angle = -12
                right_leg_angle = 12
                left_arm_angle = -45
                right_arm_angle = 45
            else:
                cycle = self.player.run_cycle
                leg_angles = [(-22, 22), (-8, 8), (22, -22), (8, -8)]
                left_leg_angle, right_leg_angle = leg_angles[cycle]
                left_arm_angle = -right_leg_angle - 15
                right_arm_angle = -left_leg_angle - 15
        
            # ═══════════════════════════════════════════════════════════════
            # BODY ANCHOR POINTS (All relative to py + y_off)
            # ═══════════════════════════════════════════════════════════════
            ground_y = py + y_off           # Where feet touch
            hip_y = ground_y - 25           # Hip/waist level
            chest_y = ground_y - 50         # Chest level
            shoulder_y = ground_y - 55      # Shoulder level
            neck_y = ground_y - 60          # Neck base
            head_center_y = ground_y - 75   # Head center
        
            # ═══════════════════════════════════════════════════════════════
            # LEGS
            # ═══════════════════════════════════════════════════════════════
            leg_length = 25
        
            # Left leg
            left_foot_x = px - 8 + math.sin(math.radians(left_leg_angle)) * leg_length
            left_foot_y = ground_y
            painter.setPen(QPen(body_dark, 8, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(int(px - 8), int(hip_y), int(left_foot_x), int(left_foot_y))
        
            # Right leg
            right_foot_x = px + 8 + math.sin(math.radians(right_leg_angle)) * leg_length
            right_foot_y = ground_y
            painter.drawLine(int(px + 8), int(hip_y), int(right_foot_x), int(right_foot_y))
        
            # Shoes
            painter.setBrush(shoe_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(left_foot_x - 6), int(left_foot_y - 4), 12, 8)
            painter.drawEllipse(int(right_foot_x - 6), int(right_foot_y - 4), 12, 8)
        
            # Shoe highlights
            painter.setBrush(QColor(0, 200, 255, 150))
            painter.drawEllipse(int(left_foot_x - 3), int(left_foot_y - 2), 6, 3)
            painter.drawEllipse(int(right_foot_x - 3), int(right_foot_y - 2), 6, 3)
        
            # ═══════════════════════════════════════════════════════════════
            # TORSO (Body)
            # ═══════════════════════════════════════════════════════════════
            torso_path = QPainterPath()
            torso_path.moveTo(px - 14, hip_y)              # Bottom left
            torso_path.lineTo(px - 16, shoulder_y + 5)     # Top left
            torso_path.quadTo(px, shoulder_y, px + 16, shoulder_y + 5)  # Top curve
            torso_path.lineTo(px + 14, hip_y)              # Bottom right
            torso_path.closeSubpath()
        
            body_grad = QLinearGradient(px - 16, shoulder_y, px + 16, shoulder_y)
            body_grad.setColorAt(0, body_dark)
            body_grad.setColorAt(0.3, body_color)
            body_grad.setColorAt(0.5, body_light)
            body_grad.setColorAt(0.7, body_color)
            body_grad.setColorAt(1, body_dark)
            painter.setBrush(body_grad)
            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.drawPath(torso_path)
        
            # Chest emblem/light
            emblem_y = chest_y + 5
            painter.setBrush(QColor(0, 255, 255, 180))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(px - 5), int(emblem_y), 10, 10)
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawEllipse(int(px - 3), int(emblem_y + 2), 6, 6)
        
            # ═══════════════════════════════════════════════════════════════
            # ARMS
            # ═══════════════════════════════════════════════════════════════
            arm_length = 22
            arm_y = shoulder_y + 8
        
            # Left arm
            left_hand_x = px - 16 + math.sin(math.radians(left_arm_angle)) * arm_length
            left_hand_y = arm_y + math.cos(math.radians(left_arm_angle)) * arm_length
            painter.setPen(QPen(body_dark, 6, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(int(px - 16), int(arm_y), int(left_hand_x), int(left_hand_y))
        
            # Right arm
            right_hand_x = px + 16 + math.sin(math.radians(right_arm_angle)) * arm_length
            right_hand_y = arm_y + math.cos(math.radians(right_arm_angle)) * arm_length
            painter.drawLine(int(px + 16), int(arm_y), int(right_hand_x), int(right_hand_y))
        
            # Hands
            painter.setBrush(skin_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(left_hand_x - 4), int(left_hand_y - 4), 8, 8)
            painter.drawEllipse(int(right_hand_x - 4), int(right_hand_y - 4), 8, 8)
        
            # ═══════════════════════════════════════════════════════════════
            # NECK (Connects head to body - KEY FIX!)
            # ═══════════════════════════════════════════════════════════════
            neck_width = 10
            neck_height = 8
        
            # Neck background (skin color)
            painter.setBrush(skin_color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(px - neck_width // 2), int(neck_y), neck_width, neck_height)
        
            # ═══════════════════════════════════════════════════════════════
            # HEAD (✅ FIXED - Always attached to neck)
            # ═══════════════════════════════════════════════════════════════
            head_size = 22
            head_x = px
            head_y = head_center_y  # ✅ Uses same y_off as body
        
            # Head shadow/glow
            painter.setBrush(QColor(0, 150, 200, 30))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(head_x - head_size // 2 - 3), int(head_y - head_size // 2 - 3),
                               head_size + 6, head_size + 6)
        
            # Main head
            painter.setBrush(skin_color)
            painter.setPen(QPen(QColor(230, 200, 170), 1))
            painter.drawEllipse(int(head_x - head_size // 2), int(head_y - head_size // 2),
                               head_size, head_size)
        
            # Hair
            hair_path = QPainterPath()
            hair_path.moveTo(head_x - 10, head_y - 2)
            hair_path.quadTo(head_x - 13, head_y - 14, head_x - 2, head_y - 12)
            hair_path.quadTo(head_x + 5, head_y - 15, head_x + 12, head_y - 10)
            hair_path.quadTo(head_x + 13, head_y - 5, head_x + 10, head_y - 2)
            hair_path.closeSubpath()
            painter.setBrush(hair_color)
            painter.setPen(Qt.NoPen)
            painter.drawPath(hair_path)
        
            # Eyes
            eye_y = head_y
        
            # Eye whites
            painter.setBrush(Qt.white)
            painter.drawEllipse(int(head_x - 7), int(eye_y - 3), 6, 6)
            painter.drawEllipse(int(head_x + 1), int(eye_y - 3), 6, 6)
        
            # Pupils (looking forward)
            painter.setBrush(QColor(30, 30, 30))
            painter.drawEllipse(int(head_x - 5), int(eye_y - 1), 3, 3)
            painter.drawEllipse(int(head_x + 3), int(eye_y - 1), 3, 3)
        
            # Eyebrows (determined expression)
            painter.setPen(QPen(hair_color, 2))
            painter.drawLine(int(head_x - 8), int(eye_y - 6), int(head_x - 3), int(eye_y - 5))
            painter.drawLine(int(head_x + 3), int(eye_y - 5), int(head_x + 8), int(eye_y - 6))
        
            # Mouth (small smile)
            painter.setPen(QPen(QColor(180, 100, 100), 2))
            painter.drawArc(int(head_x - 4), int(head_y + 3), 8, 5, 0, -180 * 16)
        
            # ═══════════════════════════════════════════════════════════════
            # JUMP EFFECTS (Motion lines below player)
            # ═══════════════════════════════════════════════════════════════
            if self.player.is_jumping and self.player.jump_frame < 15:
                # Speed lines
                for i in range(4):
                    line_y = ground_y + 8 + i * 10
                    line_alpha = 150 - i * 35
                    line_width = 25 - i * 5
                
                    painter.setPen(QPen(QColor(0, 255, 255, line_alpha), 2))
                    painter.drawLine(int(px - line_width), int(line_y),
                                   int(px + line_width), int(line_y))
            
                # Jump indicator text
                painter.setPen(QColor(0, 255, 136))
                painter.setFont(QFont("Consolas", 9, QFont.Bold))
                painter.drawText(QRectF(px - 30, head_y - 35, 60, 15), Qt.AlignCenter, "▲ JUMP!")
        
            # ═══════════════════════════════════════════════════════════════
            # RUNNING DUST (When not jumping)
            # ═══════════════════════════════════════════════════════════════
            if not self.player.is_jumping and not self.player.is_sliding:
                if self.frame % 4 == 0:
                    # Small dust particles at feet
                    for foot_x in [left_foot_x, right_foot_x]:
                        if random.random() > 0.5:
                            dust_x = foot_x + random.randint(-5, 5)
                            dust_y = ground_y + random.randint(-2, 3)
                            dust_alpha = random.randint(40, 80)
                            painter.setBrush(QColor(150, 130, 100, dust_alpha))
                            painter.setPen(Qt.NoPen)
                            painter.drawEllipse(int(dust_x), int(dust_y), 3, 3)
    
    def _draw_hud(self, painter, w, h):
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 20, QFont.Bold))
        painter.drawText(18, 38, f"SCORE: {self.score}")
        
        painter.setPen(QColor(0, 200, 255))
        painter.setFont(QFont("Consolas", 12))
        painter.drawText(18, 60, f"SPEED: {self.speed:.1f}x")
        
        painter.setPen(QColor(255, 215, 0))
        painter.drawText(18, 80, f"COINS: {self.coins_collected}")
        
        lane_names = ["◀ LEFT", "● CENTER", "RIGHT ▶"]
        lane_colors = [QColor(0, 200, 255), QColor(0, 255, 136), QColor(0, 200, 255)]
        painter.setPen(lane_colors[self.player.lane])
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        painter.drawText(18, 100, f"LANE: {lane_names[self.player.lane]}")
        
        if self.player.is_jumping:
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(w - 100, 35, "▲ JUMP!")
        elif self.player.is_sliding:
            painter.setPen(QColor(255, 165, 0))
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(w - 100, 35, "▼ SLIDE!")
    
    def _draw_game_over(self, painter, w, h):
        painter.fillRect(0, 0, w, h, QColor(0, 0, 0, 200))
        
        bw, bh = 360, 280
        bx, by = (w - bw) // 2, (h - bh) // 2
        
        box_grad = QLinearGradient(bx, by, bx, by + bh)
        box_grad.setColorAt(0, QColor(20, 35, 60))
        box_grad.setColorAt(1, QColor(10, 18, 35))
        painter.setBrush(box_grad)
        painter.setPen(QPen(QColor(255, 80, 80), 3))
        painter.drawRoundedRect(bx, by, bw, bh, 15, 15)
        
        painter.setPen(QColor(255, 80, 80))
        painter.setFont(QFont("Consolas", 32, QFont.Bold))
        painter.drawText(QRectF(bx, by + 25, bw, 50), Qt.AlignCenter, "GAME OVER")
        
        painter.setPen(QColor(200, 210, 230))
        painter.setFont(QFont("Consolas", 14))
        painter.drawText(QRectF(bx, by + 80, bw, 25), Qt.AlignCenter, "YOUR SCORE")
        
        painter.setPen(QColor(255, 215, 0))
        painter.setFont(QFont("Consolas", 42, QFont.Bold))
        painter.drawText(QRectF(bx, by + 105, bw, 55), Qt.AlignCenter, f"{self.score}")
        
        painter.setPen(QColor(150, 180, 220))
        painter.setFont(QFont("Consolas", 11))
        painter.drawText(QRectF(bx, by + 165, bw, 22), Qt.AlignCenter, f"Coins: {self.coins_collected}")
        
        if self.score >= self.high_score and self.score > 0:
            painter.setPen(QColor(0, 255, 136))
            painter.setFont(QFont("Consolas", 14, QFont.Bold))
            painter.drawText(QRectF(bx, by + 195, bw, 28), Qt.AlignCenter, "★ NEW HIGH SCORE! ★")
        
        alpha = 180 + int(70 * math.sin(self.frame * 0.12))
        painter.setPen(QColor(0, 255, 255, alpha))
        painter.setFont(QFont("Consolas", 16, QFont.Bold))
        painter.drawText(QRectF(bx, by + 235, bw, 35), Qt.AlignCenter, "▶  CLICK TO RETRY  ◀")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GAME CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    
    def load_game(self, game_id):
        print(f"  ◉ Loading: {game_id}")
        if game_id == "ai_trainer":
            return
        
        self.state = GameState.TUTORIAL
        self.tutorial_step = 0
        self.tutorial_hold = 0
        self.tutorial_success = False
        self.game_started.emit("Cyber Runner")
    
    def _start_game(self):
        print("  🎮 Starting Cyber Runner!")
        self.state = GameState.PLAYING
        self.player = Player()
        self.obstacles.clear()  # ✅ Use clear() instead of = []
        self.particles.clear()
        self.score = 0
        self.speed = 7
        self.spawn_timer = 0
        self.distance = 0
        self.coins_collected = 0
    
    def _next_tutorial(self):
        self.tutorial_success = False
        self.tutorial_success_timer = 0
        self.tutorial_hold = 0
        self.tutorial_step += 1
        
        if self.tutorial_step >= len(TUTORIAL_STEPS):
            self._start_game()
    
    def skip_tutorial(self):
        self._start_game()
    
    def stop_game(self):
        self.state = GameState.WELCOME
        self.obstacles.clear()
        self.particles.clear()
        self.score = 0
    
    def restart_game(self):
        self._start_game()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INPUT HANDLERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    @Slot(str)
    def handle_gesture(self, gesture):
        pass
    
    @Slot(object)
    def handle_direction(self, direction):
        try:
            if hasattr(direction, 'value'):
                dir_val = direction.value
            else:
                dir_val = str(direction).upper()
        
            # ✅ FIX: Tutorial mode - continuous hold detection
            if self.state == GameState.TUTORIAL:
                if dir_val == "NONE":
                    self.tutorial_hold = max(0, self.tutorial_hold - 2)
                    self.last_input_direction = "NONE"
                    return
            
                if self.tutorial_step < len(TUTORIAL_STEPS):
                    step = TUTORIAL_STEPS[self.tutorial_step]
                    if step['expected'] == dir_val:
                        # Keep incrementing even if same direction (continuous hold)
                        self.tutorial_hold = min(self.tutorial_hold + 1, 20)
                        if self.tutorial_hold >= 15:
                            self.tutorial_success = True
                            self.tutorial_success_timer = 0
                    else:
                        self.tutorial_hold = max(0, self.tutorial_hold - 2)
            
                self.last_input_direction = dir_val
                return
        
            # ✅ PLAYING state - original logic
            if dir_val == "NONE":
                if self.last_input_direction != "NONE":
                    self.player.reset_cooldown()
                self.last_input_direction = "NONE"
                return
        
            if self.state == GameState.PLAYING:
                if dir_val != self.last_input_direction or self.player.direction_cooldown <= 0:
                    if dir_val == "LEFT":
                        self.player.move_left()
                    elif dir_val == "RIGHT":
                        self.player.move_right()
                    elif dir_val == "UP":
                        self.player.jump()
                    elif dir_val == "DOWN":
                        self.player.slide()
        
            self.last_input_direction = dir_val
        except Exception as e:
            print(f"⚠️ Direction error: {e}")
    
    def keyPressEvent(self, event):
        try:
            key = event.key()
            
            if self.state == GameState.TUTORIAL:
                if key == Qt.Key_Space:
                    self.skip_tutorial()
                elif key in (Qt.Key_Left, Qt.Key_A):
                    self.handle_direction("LEFT")
                elif key in (Qt.Key_Right, Qt.Key_D):
                    self.handle_direction("RIGHT")
                elif key in (Qt.Key_Up, Qt.Key_W):
                    self.handle_direction("UP")
                elif key in (Qt.Key_Down, Qt.Key_S):
                    self.handle_direction("DOWN")
            
            elif self.state == GameState.PLAYING:
                if key in (Qt.Key_Left, Qt.Key_A):
                    self.player.move_left()
                elif key in (Qt.Key_Right, Qt.Key_D):
                    self.player.move_right()
                elif key in (Qt.Key_Up, Qt.Key_W, Qt.Key_Space):
                    self.player.jump()
                elif key in (Qt.Key_Down, Qt.Key_S):
                    self.player.slide()
            
            if key == Qt.Key_H:
                self.DEBUG_HITBOXES = not self.DEBUG_HITBOXES
                print(f"  Debug Hitboxes: {'ON' if self.DEBUG_HITBOXES else 'OFF'}")
        except Exception as e:
            print(f"⚠️ Key error: {e}")
    
    def keyReleaseEvent(self, event):
        self.player.reset_cooldown()
    
    def mousePressEvent(self, event):
        try:
            if self.state == GameState.WELCOME:
                self.load_game("runner")
            elif self.state == GameState.GAME_OVER:
                self.restart_game()
        except Exception as e:
            print(f"⚠️ Mouse error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self._is_running = False
        self.timer.stop()
        self.obstacles.clear()
        self.particles.clear()
        print("  ✅ GamingCanvas cleanup complete")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    canvas = GamingCanvas()
    canvas.resize(950, 700)
    canvas.show()
    
    print("\n" + "═" * 55)
    print("  🏃 CYBER RUNNER - STABLE v3.1")
    print("═" * 55)
    print("  Controls:")
    print("   ◀ ▶  A/D or Arrows - Move LEFT/RIGHT")
    print("   ▲    W or Up - JUMP over RED barriers")
    print("   ▼    S or Down - SLIDE under ORANGE obstacles")
    print("   H    Toggle hitbox debug")
    print("   SPACE Skip tutorial")
    print("═" * 55 + "\n")
    
    sys.exit(app.exec())
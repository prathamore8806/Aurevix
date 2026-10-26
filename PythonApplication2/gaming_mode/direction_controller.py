"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GAMING MODE - DIRECTION CONTROLLER                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

This file contains:
- CyberpunkDirectionController widget
- Hexagonal design with animations
- Particle system and data streams
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPoint, QPointF, QRect
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath
)
import math
import random

from gaming_mode.constants import CyberColors, Direction, PARTICLE_COUNT, DATA_STREAM_COUNT


# ═══════════════════════════════════════════════════════════════════════════════
# 🎮 CYBERPUNK DIRECTION CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════
class CyberpunkDirectionController(QWidget):
    """Cyberpunk Direction Controller with hexagonal design"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self.current_dir = "CENTER"
        self.animation_frame = 0
        
        # Particle system
        self.particles = []
        self.data_streams = []
        self._init_particles()
        self._init_data_streams()
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(100)
        
        # Glitch effect
        self.glitch_active = False
        self.glitch_timer = QTimer()
        self.glitch_timer.timeout.connect(self._trigger_glitch)
        self.glitch_timer.start(5000)
    
    def _init_particles(self):
        for _ in range(PARTICLE_COUNT):  # ✅ CHANGED: Fewer particles (was 20, now 5)
            self.particles.append({
                'x': random.randint(0, 220),
                'y': random.randint(0, 220),
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-1, 1),
                'size': random.randint(1, 3),
                'alpha': random.randint(50, 200),
                'color': random.choice([CyberColors.CYAN_BRIGHT, CyberColors.NEON_GREEN,
                                        CyberColors.NEON_PINK, CyberColors.HOLO_CYAN])
            })
    
    def _init_data_streams(self):
        for _ in range(DATA_STREAM_COUNT):  # ✅ CHANGED: Fewer streams (was 8, now 2)
            self.data_streams.append({
                'start_x': random.randint(0, 220),
                'y': random.randint(0, 220),
                'length': random.randint(20, 60),
                'speed': random.uniform(2, 5),
                'alpha': random.randint(30, 100)
            })
    
    def _trigger_glitch(self):
        if random.random() < 0.3:
            self.glitch_active = True
            QTimer.singleShot(100, lambda: setattr(self, 'glitch_active', False))
    
    def _animate(self):
        self.animation_frame = (self.animation_frame + 1) % 360
        
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            if p['x'] < 0 or p['x'] > 220:
                p['vx'] *= -1
            if p['y'] < 0 or p['y'] > 220:
                p['vy'] *= -1
            
            p['alpha'] = int(50 + 100 * abs(math.sin(self.animation_frame * 0.05 + p['x'] * 0.1)))
        
        for stream in self.data_streams:
            stream['start_x'] += stream['speed']
            if stream['start_x'] > 240:
                stream['start_x'] = -stream['length']
                stream['y'] = random.randint(0, 220)
        
        self.update()
    
    def set_direction(self, direction):
        if isinstance(direction, Direction):
            val = direction.value
        elif hasattr(direction, 'value'):
            val = direction.value
        else:
            val = str(direction)
        self.current_dir = "CENTER" if val == "NONE" else val
        self.update()
    
    def _draw_hexagon(self, painter, cx, cy, radius, rotation=0):
        path = QPainterPath()
        for i in range(6):
            angle = math.radians(60 * i + rotation)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        return path
    
    def _draw_circuit_pattern(self, painter, w, h):
        painter.setPen(QPen(QColor(0, 255, 255, 20), 1))
        
        for y in range(0, h, 15):
            if random.random() > 0.3:
                x_start = random.randint(0, w // 3)
                x_end = random.randint(2 * w // 3, w)
                painter.drawLine(x_start, y, x_end, y)
                if random.random() > 0.5:
                    painter.setBrush(QColor(0, 255, 255, 40))
                    painter.drawEllipse(QPoint(x_start, y), 2, 2)
                    painter.drawEllipse(QPoint(x_end, y), 2, 2)
        
        for x in range(0, w, 15):
            if random.random() > 0.3:
                y_start = random.randint(0, h // 3)
                y_end = random.randint(2 * h // 3, h)
                painter.drawLine(x, y_start, x, y_end)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        
        # Background
        outer_glow = QRadialGradient(cx, cy, max(w, h))
        outer_glow.setColorAt(0, QColor(0, 20, 40, 255))
        outer_glow.setColorAt(0.5, QColor(0, 10, 25, 255))
        outer_glow.setColorAt(1, QColor(0, 5, 15, 255))
        painter.fillRect(0, 0, w, h, outer_glow)
        
        self._draw_circuit_pattern(painter, w, h)
        
        # Data streams
        for stream in self.data_streams:
            gradient = QLinearGradient(stream['start_x'], 0,
                                        stream['start_x'] + stream['length'], 0)
            gradient.setColorAt(0, QColor(0, 255, 255, 0))
            gradient.setColorAt(0.5, QColor(0, 255, 255, stream['alpha']))
            gradient.setColorAt(1, QColor(0, 255, 255, 0))
            painter.setPen(QPen(QBrush(gradient), 2))
            painter.drawLine(int(stream['start_x']), int(stream['y']),
                            int(stream['start_x'] + stream['length']), int(stream['y']))
        
        # Hexagonal frame
        rotation_offset = self.animation_frame * 0.5
        
        hex_path = self._draw_hexagon(painter, cx, cy, 100, rotation_offset)
        glow_pen = QPen(QColor(0, 255, 255, 60), 8)
        painter.setPen(glow_pen)
        painter.drawPath(hex_path)
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
        hex_path = self._draw_hexagon(painter, cx, cy, 95, rotation_offset)
        border_color = QColor(0, 255, 255, int(150 + 100 * pulse))
        painter.setPen(QPen(border_color, 2))
        painter.drawPath(hex_path)
        
        hex_path_inner = self._draw_hexagon(painter, cx, cy, 85, rotation_offset)
        painter.setPen(QPen(QColor(0, 180, 220, 80), 1))
        painter.drawPath(hex_path_inner)
        
        # Grid
        painter.setPen(QPen(QColor(0, 255, 255, 15), 1))
        grid_size = 20
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)
        
        # Particles
        for p in self.particles:
            color = QColor(p['color'])
            color.setAlpha(p['alpha'])
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(p['x'], p['y']), p['size'], p['size'])
        
        # Title
        title_rect = QRect(10, 8, w - 20, 24)
        title_gradient = QLinearGradient(0, 8, w, 8)
        title_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        title_gradient.setColorAt(0.2, QColor(0, 40, 60, 200))
        title_gradient.setColorAt(0.5, QColor(0, 60, 80, 220))
        title_gradient.setColorAt(0.8, QColor(0, 40, 60, 200))
        title_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(title_rect, title_gradient)
        
        painter.setPen(QColor(CyberColors.CYAN_BRIGHT))
        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.drawText(title_rect, Qt.AlignCenter, "◢◤ VECTOR CONTROL ◢◤")
        
        # Direction buttons
        button_positions = {
            "UP": (cx, cy - 55),
            "DOWN": (cx, cy + 55),
            "LEFT": (cx - 55, cy),
            "RIGHT": (cx + 55, cy)
        }
        
        for dir_name, (bx, by) in button_positions.items():
            active = self.current_dir == dir_name
            self._draw_direction_button(painter, bx, by, dir_name, active)
        
        # Center core
        self._draw_center_core(painter, cx, cy)
        
        # Power lines
        self._draw_power_lines(painter, cx, cy)
        
        # Corners
        self._draw_corner_decorations(painter, w, h)
        
        # Status bar
        self._draw_status_bar(painter, w, h)
        
        # Glitch
        if self.glitch_active:
            self._draw_glitch_effect(painter, w, h)
        
        painter.end()
    
    def _draw_direction_button(self, painter, cx, cy, direction, active):
        btn_radius = 28
        
        if active:
            for i in range(4):
                glow_radius = btn_radius + 15 - i * 3
                glow_alpha = 40 + i * 20
                glow_gradient = QRadialGradient(cx, cy, glow_radius)
                glow_gradient.setColorAt(0, QColor(0, 255, 136, glow_alpha))
                glow_gradient.setColorAt(0.5, QColor(0, 255, 255, glow_alpha // 2))
                glow_gradient.setColorAt(1, QColor(0, 255, 136, 0))
                painter.setBrush(glow_gradient)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(cx, cy), glow_radius, glow_radius)
        
        hex_path = self._draw_hexagon(painter, cx, cy, btn_radius, 30)
        
        if active:
            btn_gradient = QRadialGradient(cx, cy, btn_radius)
            btn_gradient.setColorAt(0, QColor(0, 255, 200, 255))
            btn_gradient.setColorAt(0.3, QColor(0, 220, 180, 220))
            btn_gradient.setColorAt(0.7, QColor(0, 180, 200, 180))
            btn_gradient.setColorAt(1, QColor(0, 120, 160, 150))
            painter.setBrush(btn_gradient)
            painter.setPen(QPen(QColor(255, 255, 255, 255), 3))
        else:
            btn_gradient = QRadialGradient(cx, cy, btn_radius)
            btn_gradient.setColorAt(0, QColor(30, 60, 80, 200))
            btn_gradient.setColorAt(0.5, QColor(20, 40, 60, 180))
            btn_gradient.setColorAt(1, QColor(10, 25, 40, 160))
            painter.setBrush(btn_gradient)
            painter.setPen(QPen(QColor(0, 180, 220, 150), 2))
        
        painter.drawPath(hex_path)
        
        if active:
            inner_hex = self._draw_hexagon(painter, cx, cy, btn_radius - 8, 30)
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(inner_hex)
        
        painter.save()
        painter.translate(cx, cy)
        
        rotations = {"UP": 0, "DOWN": 180, "LEFT": 270, "RIGHT": 90}
        painter.rotate(rotations.get(direction, 0))
        
        arrow = QPainterPath()
        arrow.moveTo(0, -14)
        arrow.lineTo(-10, 5)
        arrow.lineTo(-5, 5)
        arrow.lineTo(-5, 12)
        arrow.lineTo(5, 12)
        arrow.lineTo(5, 5)
        arrow.lineTo(10, 5)
        arrow.closeSubpath()
        
        if active:
            arrow_gradient = QLinearGradient(0, -14, 0, 12)
            arrow_gradient.setColorAt(0, QColor(255, 255, 255, 255))
            arrow_gradient.setColorAt(0.4, QColor(0, 255, 200, 255))
            arrow_gradient.setColorAt(1, QColor(0, 200, 255, 200))
            painter.setBrush(arrow_gradient)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            arrow_gradient = QLinearGradient(0, -14, 0, 12)
            arrow_gradient.setColorAt(0, QColor(100, 180, 200, 180))
            arrow_gradient.setColorAt(1, QColor(60, 120, 150, 120))
            painter.setBrush(arrow_gradient)
            painter.setPen(QPen(QColor(80, 160, 200, 150), 1))
        
        painter.drawPath(arrow)
        painter.restore()
        
        if active:
            painter.setPen(QColor(255, 255, 255, 200))
            painter.setFont(QFont("Consolas", 7, QFont.Bold))
            
            label_offsets = {
                "UP": (cx - 10, cy + btn_radius + 12),
                "DOWN": (cx - 14, cy - btn_radius - 6),
                "LEFT": (cx + btn_radius + 4, cy + 4),
                "RIGHT": (cx - btn_radius - 24, cy + 4)
            }
            lx, ly = label_offsets.get(direction, (cx, cy))
            painter.drawText(int(lx), int(ly), direction)
    
    def _draw_center_core(self, painter, cx, cy):
        is_centered = self.current_dir == "CENTER"
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.15)
        
        if is_centered:
            for i in range(4):
                ring_radius = 15 + i * 8 + pulse * 3
                ring_alpha = int((120 - i * 25) * pulse)
                ring_rotation = self.animation_frame * (0.5 + i * 0.2)
                
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(ring_rotation)
                
                ring_color = QColor(0, 255, 255, ring_alpha)
                painter.setPen(QPen(ring_color, 2 - i * 0.3))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(0, 0), ring_radius, ring_radius * 0.4)
                
                painter.restore()
            
            core_radius = 18 + pulse * 4
            
            core_glow = QRadialGradient(cx, cy, core_radius * 2)
            core_glow.setColorAt(0, QColor(0, 255, 255, 150))
            core_glow.setColorAt(0.5, QColor(0, 200, 255, 80))
            core_glow.setColorAt(1, QColor(0, 150, 255, 0))
            painter.setBrush(core_glow)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), core_radius * 2, core_radius * 2)
            
            core_gradient = QRadialGradient(cx - 3, cy - 3, core_radius)
            core_gradient.setColorAt(0, QColor(255, 255, 255, 255))
            core_gradient.setColorAt(0.3, QColor(100, 255, 255, 255))
            core_gradient.setColorAt(0.7, QColor(0, 220, 255, 230))
            core_gradient.setColorAt(1, QColor(0, 150, 200, 200))
            painter.setBrush(core_gradient)
            painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            painter.drawEllipse(QPointF(cx, cy), core_radius, core_radius)
            
            painter.setBrush(QColor(255, 255, 255, 100))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx - 4, cy - 4), 6, 6)
            
        else:
            core_radius = 12
            
            core_gradient = QRadialGradient(cx, cy, core_radius)
            core_gradient.setColorAt(0, QColor(60, 100, 120, 200))
            core_gradient.setColorAt(0.7, QColor(30, 60, 80, 150))
            core_gradient.setColorAt(1, QColor(15, 30, 45, 100))
            painter.setBrush(core_gradient)
            painter.setPen(QPen(QColor(0, 180, 220, 100), 1))
            painter.drawEllipse(QPointF(cx, cy), core_radius, core_radius)
    
    def _draw_power_lines(self, painter, cx, cy):
        button_positions = {
            "UP": (cx, cy - 55),
            "DOWN": (cx, cy + 55),
            "LEFT": (cx - 55, cy),
            "RIGHT": (cx + 55, cy)
        }
        
        pulse = 0.5 + 0.5 * math.sin(self.animation_frame * 0.1)
        
        for dir_name, (bx, by) in button_positions.items():
            active = self.current_dir == dir_name
            
            if active:
                gradient = QLinearGradient(cx, cy, bx, by)
                gradient.setColorAt(0, QColor(0, 255, 200, 200))
                gradient.setColorAt(0.5, QColor(0, 255, 255, int(150 + 100 * pulse)))
                gradient.setColorAt(1, QColor(0, 255, 200, 200))
                painter.setPen(QPen(QBrush(gradient), 3))
            else:
                painter.setPen(QPen(QColor(0, 100, 130, 50), 1))
            
            dx = bx - cx
            dy = by - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                nx, ny = dx / dist, dy / dist
                start_x = cx + nx * 15
                start_y = cy + ny * 15
                end_x = bx - nx * 28
                end_y = by - ny * 28
                painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
                
                if active:
                    pulse_pos = (self.animation_frame % 30) / 30.0
                    px = start_x + (end_x - start_x) * pulse_pos
                    py = start_y + (end_y - start_y) * pulse_pos
                    
                    painter.setBrush(QColor(255, 255, 255, 255))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPointF(px, py), 4, 4)
    
    def _draw_corner_decorations(self, painter, w, h):
        corner_size = 25
        corner_color = QColor(0, 255, 255, 150)
        painter.setPen(QPen(corner_color, 2))
        
        corners = [
            [(8, 8 + corner_size), (8, 8), (8 + corner_size, 8)],
            [(w - 8 - corner_size, 8), (w - 8, 8), (w - 8, 8 + corner_size)],
            [(8, h - 8 - corner_size), (8, h - 8), (8 + corner_size, h - 8)],
            [(w - 8 - corner_size, h - 8), (w - 8, h - 8), (w - 8, h - 8 - corner_size)]
        ]
        
        for corner in corners:
            path = QPainterPath()
            path.moveTo(corner[0][0], corner[0][1])
            for point in corner[1:]:
                path.lineTo(point[0], point[1])
            painter.drawPath(path)
            
            painter.setBrush(corner_color)
            painter.drawEllipse(QPoint(corner[1][0], corner[1][1]), 3, 3)
    
    def _draw_status_bar(self, painter, w, h):
        status_rect = QRect(10, h - 30, w - 20, 22)
        status_gradient = QLinearGradient(0, h - 30, w, h - 30)
        status_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        status_gradient.setColorAt(0.2, QColor(0, 30, 50, 200))
        status_gradient.setColorAt(0.5, QColor(0, 50, 70, 220))
        status_gradient.setColorAt(0.8, QColor(0, 30, 50, 200))
        status_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(status_rect, status_gradient)
        
        dir_icons = {
            "UP": "▲ NORTH",
            "DOWN": "▼ SOUTH",
            "LEFT": "◀ WEST",
            "RIGHT": "▶ EAST",
            "CENTER": "◎ CENTER"
        }
        
        color = CyberColors.NEON_GREEN if self.current_dir != "CENTER" else CyberColors.CYAN_BRIGHT
        painter.setPen(QColor(color))
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        
        icon_text = dir_icons.get(self.current_dir, "◎ CENTER")
        painter.drawText(status_rect, Qt.AlignCenter, icon_text)
    
    def _draw_glitch_effect(self, painter, w, h):
        for _ in range(5):
            y = random.randint(0, h)
            height = random.randint(2, 8)
            offset = random.randint(-10, 10)
            
            painter.fillRect(offset, y, w, height, QColor(255, 0, 0, 80))
            painter.fillRect(-offset, y + 2, w, height, QColor(0, 255, 255, 80))
    
    def cleanup(self):
        self.timer.stop()
        self.glitch_timer.stop()
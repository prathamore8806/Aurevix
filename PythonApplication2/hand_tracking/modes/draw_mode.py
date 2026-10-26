"""
Draw Mode - Drawing, color picking, canvas control
"""

import time

from .base_mode import BaseMode
from ..core.filters import DrawModeTracker
from ..core.hud import HoloColors


class DrawMode(BaseMode):
    """Draw mode handler"""
    
    def __init__(self, state, hud):
        super().__init__(state, hud)
        self.draw_tracker = DrawModeTracker()
    
    def activate(self):
        self.active = True
        self.reset()
    
    def deactivate(self):
        self.active = False
        self.reset()
        if self.state.gui and hasattr(self.state.gui, 'draw_canvas'):
            try:
                self.state.gui.draw_canvas.lift_pen()
            except:
                pass
    
    def reset(self):
        self.draw_tracker.reset()
    
    def process(self, lm, fingers, frame, handed):
        if self.state.gui is None:
            return
        
        try:
            canvas = self.state.gui.draw_canvas
        except:
            return
        
        index = lm[8]
        i, m, r, p = fingers[1], fingers[2], fingers[3], fingers[4]
        
        raw_x, raw_y = self.get_screen_coords(index)
        cx, cy = int(index.x * self.state.CAM_W), int(index.y * self.state.CAM_H)
        
        # Index only - draw
        if i and not m and not r and not p:
            self._handle_draw(canvas, raw_x, raw_y, frame, cx, cy)
        
        # Index + middle - color pick
        elif i and m and not r and not p:
            self._handle_pick(canvas, raw_x, raw_y, frame, cx, cy)
        
        # Index + middle + ring - toggle wheel
        elif i and m and r and not p:
            self._handle_wheel(canvas, frame)
        
        # No index - lift pen
        elif not i:
            canvas.lift_pen()
            self.draw_tracker.lift_pen()
        
        # All fingers - clear
        if all(fingers):
            canvas.clear()
            self.draw_tracker.reset()
            self.state.show_action("⬡ CLEARED!", HoloColors.NEON_YELLOW)
    
    def _handle_draw(self, canvas, raw_x, raw_y, frame, cx, cy):
        if hasattr(canvas, 'stop_picking'):
            canvas.stop_picking()
        
        result = self.draw_tracker.update(raw_x, raw_y, True)
        
        if result.state == "DRAWING" and result.should_draw:
            for px, py in result.draw_points:
                canvas.draw_point(px, py)
            self.hud.draw_cursor(frame, cx, cy, "drawing")
            self.hud.draw_gesture_box(frame, f"DRAWING v:{int(result.velocity)}")
        elif result.state == "STOPPED":
            canvas.lift_pen()
            self.hud.draw_cursor(frame, cx, cy, "ready")
        else:
            self.hud.draw_cursor(frame, cx, cy, "ready")
            self.hud.draw_gesture_box(frame, "READY")
    
    def _handle_pick(self, canvas, raw_x, raw_y, frame, cx, cy):
        canvas.lift_pen()
        self.draw_tracker.lift_pen()
        
        if hasattr(canvas, 'pick_color_at'):
            canvas.pick_color_at(raw_x, raw_y)
        
        self.hud.draw_cursor(frame, cx, cy, "pick")
        self.hud.draw_gesture_box(frame, "COLOR PICK")
    
    def _handle_wheel(self, canvas, frame):
        canvas.lift_pen()
        self.draw_tracker.lift_pen()
        
        if hasattr(canvas, 'stop_picking'):
            canvas.stop_picking()
        
        now = time.time()
        if now - self.state.last_gesture_time > self.state.COOLDOWN:
            self.state.last_gesture_time = now
            if hasattr(canvas, 'toggle_wheel'):
                canvas.toggle_wheel()
            self.state.show_action("⬡ WHEEL", HoloColors.NEON_YELLOW)
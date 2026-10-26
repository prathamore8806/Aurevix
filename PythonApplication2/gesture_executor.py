import pyautogui
import keyboard
import time
from typing import Dict
import config

class GestureExecutor:
    """Execute actions based on recognized gestures"""
    
    def __init__(self):
        self.last_execution = {}
        self.cooldown = getattr(config, 'gesture_cooldown', 500)  # ms
        
    def can_execute(self, gesture_id: int) -> bool:
        """Check if enough time has passed since last execution"""
        now = time.time() * 1000
        last = self.last_execution.get(gesture_id, 0)
        return (now - last) >= self.cooldown
    
    def execute(self, gesture: Dict) -> bool:
        """Execute gesture action"""
        if not self.can_execute(gesture['id']):
            return False
            
        action = gesture['action']
        action_type = action['type']
        target = action['target']
        
        try:
            if action_type == "KEY_PRESS":
                self._execute_key_press(target)
            elif action_type == "KEY_HOLD":
                self._execute_key_hold(target)
            elif action_type == "MOUSE_CLICK":
                self._execute_mouse_click(target)
            elif action_type == "SCROLL":
                self._execute_scroll(target)
            elif action_type == "HOTKEY":
                self._execute_hotkey(target)
            elif action_type == "TEXT":
                self._execute_text(target)
                
            self.last_execution[gesture['id']] = time.time() * 1000
            print(f"✅ Executed: {gesture['name']} → {action_type}: {target}")
            return True
        except Exception as e:
            print(f"❌ Error executing gesture: {e}")
            return False
    
    def _execute_key_press(self, key: str):
        """Press and release a key"""
        keyboard.press_and_release(key)
    
    def _execute_key_hold(self, key: str):
        """Hold a key (will be released manually)"""
        keyboard.press(key)
    
    def _execute_mouse_click(self, button: str):
        """Click mouse button"""
        if button.lower() == "left":
            pyautogui.click()
        elif button.lower() == "right":
            pyautogui.rightClick()
        elif button.lower() == "middle":
            pyautogui.middleClick()
    
    def _execute_scroll(self, direction: str):
        """Scroll mouse wheel"""
        amount = 3
        if "up" in direction.lower():
            pyautogui.scroll(amount)
        elif "down" in direction.lower():
            pyautogui.scroll(-amount)
    
    def _execute_hotkey(self, keys: str):
        """Execute hotkey combination (e.g., 'ctrl+c')"""
        key_list = [k.strip() for k in keys.split('+')]
        keyboard.press_and_release('+'.join(key_list))
    
    def _execute_text(self, text: str):
        """Type text"""
        pyautogui.write(text, interval=0.05)
    
    def set_cooldown(self, ms: int):
        """Set cooldown between executions"""
        self.cooldown = ms

# Global executor instance
executor = GestureExecutor()

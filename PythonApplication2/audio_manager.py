# audio_manager.py - Fixed for GUI Applications (Fresh Engine Per Speech)
import os
import threading
import wave
import struct
import math
import queue
from pathlib import Path
from typing import Optional, Dict

# Audio libraries
AUDIO_AVAILABLE = False
TTS_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    AUDIO_AVAILABLE = True
except:
    print("⚠️ pygame not available - sound effects disabled")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except:
    print("⚠️ pyttsx3 not available - text-to-speech disabled")
    print("   Install with: pip install pyttsx3")


class AudioManager:
    """Enhanced Audio Manager with TTS support - Fresh Engine Per Speech"""
    
    SOUNDS = {
        'countdown_3': {'freq': 440, 'duration': 0.12},
        'countdown_2': {'freq': 523, 'duration': 0.12},
        'countdown_1': {'freq': 659, 'duration': 0.12},
        'capture': {'freq': 880, 'duration': 0.15},
        'success': {'freq': 1046, 'duration': 0.25},
        'error': {'freq': 220, 'duration': 0.2},
        'complete': {'freq': 1318, 'duration': 0.35},
        'click': {'freq': 1000, 'duration': 0.05},
        'ready': {'freq': 600, 'duration': 0.1},
    }
    
    def __init__(self, sounds_dir: str = None):
        if sounds_dir:
            self.sounds_dir = Path(sounds_dir)
        else:
            self.sounds_dir = Path.home() / ".gesture_control" / "sounds"
            
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Sound effects settings
        self.enabled = True
        self.volume = 0.6
        self.loaded_sounds: Dict = {}
        
        # ✅ TEXT-TO-SPEECH SETTINGS
        self.tts_enabled = True
        self.tts_rate = 175
        self.tts_volume = 0.9
        self.tts_voice_index = 0
        
        # ✅ TTS Queue System
        self._tts_queue = queue.Queue()
        self._tts_thread = None
        self._tts_running = False
        
        # Initialize components
        if AUDIO_AVAILABLE:
            self._generate_sounds()
            self._load_sounds()
        
        if TTS_AVAILABLE:
            self._start_tts_worker()
    
    # ══════════════════════════════════════════════════════════════
    #  TTS WORKER THREAD (Fresh Engine Per Speech - More Reliable)
    # ══════════════════════════════════════════════════════════════
    
    def _start_tts_worker(self):
        """Start background TTS worker thread"""
        self._tts_running = True
        self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._tts_thread.start()
        print("✅ TTS Worker thread started")
    
    def _tts_worker(self):
        """Background worker - Creates FRESH ENGINE for each speech"""
        print("✅ TTS Worker ready (fresh engine mode)")
        
        while self._tts_running:
            try:
                # Wait for text to speak
                text = self._tts_queue.get(timeout=0.5)
                
                if text is None:  # Shutdown signal
                    break
                
                if text and self.tts_enabled:
                    # ✅ CREATE FRESH ENGINE FOR EACH SPEECH
                    try:
                        engine = pyttsx3.init()
                        engine.setProperty('rate', self.tts_rate)
                        engine.setProperty('volume', self.tts_volume)
                        
                        # Set voice
                        voices = engine.getProperty('voices')
                        if voices and len(voices) > self.tts_voice_index:
                            engine.setProperty('voice', voices[self.tts_voice_index].id)
                        
                        print(f"🔊 TTS Speaking: '{text}'")
                        engine.say(text)
                        engine.runAndWait()
                        print(f"🔊 TTS Done: '{text}'")
                        
                        # ✅ CLEANUP ENGINE AFTER EACH USE
                        engine.stop()
                        del engine
                        
                    except Exception as e:
                        print(f"⚠️ TTS speak error: {e}")
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ TTS Worker error: {e}")
        
        print("🔇 TTS Worker thread stopped")
    
    def _stop_tts_worker(self):
        """Stop TTS worker thread"""
        self._tts_running = False
        self._tts_queue.put(None)
        if self._tts_thread and self._tts_thread.is_alive():
            self._tts_thread.join(timeout=2)
    
    # ══════════════════════════════════════════════════════════════
    #  TEXT-TO-SPEECH METHODS
    # ══════════════════════════════════════════════════════════════
    
    def speak(self, text: str, wait: bool = False):
        """Speak text using TTS"""
        if not self.tts_enabled or not TTS_AVAILABLE:
            print(f"🔇 TTS disabled: {text}")
            return
        
        if not text or not text.strip():
            return
        
        print(f"🔊 Queueing speech: '{text}'")
        self._tts_queue.put(text)
        
        if wait:
            import time
            wait_time = len(text) * 0.06 + 0.5
            time.sleep(wait_time)
    
    def speak_async(self, text: str):
        """Speak text asynchronously (non-blocking)"""
        self.speak(text, wait=False)
    
    def speak_sync(self, text: str):
        """Speak text with approximate wait"""
        self.speak(text, wait=True)
    
    def stop_speaking(self):
        """Clear speech queue"""
        try:
            while not self._tts_queue.empty():
                self._tts_queue.get_nowait()
        except:
            pass
    
    # ══════════════════════════════════════════════════════════════
    #  TTS CONFIGURATION
    # ══════════════════════════════════════════════════════════════
    
    def set_tts_rate(self, rate: int):
        """Set TTS speech rate (100-250)"""
        self.tts_rate = max(100, min(250, rate))
    
    def set_tts_volume(self, volume: float):
        """Set TTS volume (0.0 - 1.0)"""
        self.tts_volume = max(0.0, min(1.0, volume))
    
    def set_tts_voice(self, voice_index: int):
        """Set TTS voice by index"""
        self.tts_voice_index = voice_index
    
    def get_available_voices(self) -> list:
        """Get list of available TTS voices"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            result = [(i, v.name) for i, v in enumerate(voices)] if voices else []
            engine.stop()
            del engine
            return result
        except:
            return []
    
    def toggle_tts(self) -> bool:
        """Toggle TTS on/off"""
        self.tts_enabled = not self.tts_enabled
        print(f"🔊 TTS {'enabled' if self.tts_enabled else 'disabled'}")
        return self.tts_enabled
    
    # ══════════════════════════════════════════════════════════════
    #  SOUND EFFECTS
    # ══════════════════════════════════════════════════════════════
    
    def _generate_sounds(self):
        for name, params in self.SOUNDS.items():
            filepath = self.sounds_dir / f"{name}.wav"
            if not filepath.exists():
                self._create_sound(filepath, params['freq'], params['duration'])
                
    def _create_sound(self, filepath: Path, freq: float, duration: float):
        try:
            sample_rate = 44100
            num_samples = int(sample_rate * duration)
            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                fade = min(1.0, min(i, num_samples - i) / (sample_rate * 0.01))
                value = int(32767 * fade * math.sin(2 * math.pi * freq * t) * 0.7)
                samples.append(struct.pack('<h', max(-32767, min(32767, value))))
            with wave.open(str(filepath), 'w') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                f.writeframes(b''.join(samples))
        except Exception as e:
            print(f"⚠️ Could not create sound: {e}")
            
    def _load_sounds(self):
        for name in self.SOUNDS.keys():
            filepath = self.sounds_dir / f"{name}.wav"
            if filepath.exists():
                try:
                    sound = pygame.mixer.Sound(str(filepath))
                    sound.set_volume(self.volume)
                    self.loaded_sounds[name] = sound
                except:
                    pass
                    
    def play(self, sound_name: str):
        if not self.enabled or not AUDIO_AVAILABLE:
            return
        if sound_name in self.loaded_sounds:
            try:
                threading.Thread(
                    target=lambda: self.loaded_sounds[sound_name].play(),
                    daemon=True
                ).start()
            except:
                pass
            
    def play_countdown(self, number: int):
        if 1 <= number <= 3:
            self.play(f'countdown_{number}')
            
    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.loaded_sounds.values():
            try:
                sound.set_volume(self.volume)
            except:
                pass
                
    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled
    
    def cleanup(self):
        self._stop_tts_worker()


# ══════════════════════════════════════════════════════════════
#  GLOBAL INSTANCE
# ══════════════════════════════════════════════════════════════

_audio_manager_instance = None

def get_audio_manager() -> AudioManager:
    global _audio_manager_instance
    if _audio_manager_instance is None:
        _audio_manager_instance = AudioManager()
    return _audio_manager_instance
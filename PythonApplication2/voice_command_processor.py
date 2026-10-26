"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VOICE COMMAND PROCESSOR - ULTRA OPTIMIZED                 ║
║              Parse & Execute Voice Commands on Your Computer                 ║
║         🎤 Open Apps • Google Search • System Control • Type Text            ║
║                        ⚡ MAXIMUM PERFORMANCE VERSION ⚡                      ║
║                        🔊 WITH AUDIO FEEDBACK 🔊                             ║
║                        🤖 NOVA ASSISTANT 🤖                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

OPTIMIZATIONS APPLIED:
  ✅ Pre-compiled regex patterns
  ✅ Zero PyAutoGUI pause delay
  ✅ Faster volume control (single key hold)
  ✅ Optimized file search with glob + reduced timeout
  ✅ Module-level imports (no import inside functions)
  ✅ Removed unnecessary sleep() calls
  ✅ Limited command history size
  ✅ Background file indexing
  ✅ LRU caching for repeated commands
  ✅ Audio feedback for all commands
  ✅ Time-based greeting system (Nova)
"""

import os
import sys
import subprocess
import webbrowser
import platform
import re
import glob
from pathlib import Path
from datetime import datetime
from threading import Thread, Lock
import time
from functools import lru_cache

# ═════════════════════════════════════════════════════════════
#  AUDIO MANAGER (Built-in - No External Dependency)
# ═════════════════════════════════════════════════════════════

class AudioManager:
    """
    Text-to-Speech manager with Male/Female voice support.
    
    Windows Voices:
      👨 Male:   Microsoft David Desktop
      👩 Female: Microsoft Zira Desktop
    """
    
    # Voice constants
    VOICE_MALE = "male"
    VOICE_FEMALE = "female"
    
    def __init__(self):
        self.tts_enabled = True
        self.system = platform.system()
        self._speech_process = None
        self.voice_gender = self.VOICE_FEMALE  # Default: Female voice
        
    def set_voice_gender(self, gender):
        """
        Set voice gender.
        
        Args:
            gender: "male" or "female"
        """
        if gender in (self.VOICE_MALE, self.VOICE_FEMALE):
            self.voice_gender = gender
            print(f"🔊 Voice set to: {'👨 Male' if gender == self.VOICE_MALE else '👩 Female'}")
        else:
            print(f"⚠️ Invalid gender: {gender}. Use 'male' or 'female'")
    
    def get_voice_gender(self):
        """Get current voice gender."""
        return self.voice_gender
    
    def _get_powershell_voice_command(self, text):
        """
        Get PowerShell command for TTS with correct voice.
        
        👨 Male:   Microsoft David Desktop
        👩 Female: Microsoft Zira Desktop
        """
        if self.voice_gender == self.VOICE_MALE:
            # Male voice - David
            return (
                f'Add-Type -AssemblyName System.Speech; '
                f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$speak.Rate = 1; '
                f'foreach ($v in $speak.GetInstalledVoices()) {{ '
                f'  if ($v.VoiceInfo.Name -like "*David*") {{ '
                f'    $speak.SelectVoice($v.VoiceInfo.Name); break '
                f'  }} '
                f'}}; '
                f'$speak.Speak("{text}")'
            )
        else:
            # Female voice - Zira
            return (
                f'Add-Type -AssemblyName System.Speech; '
                f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$speak.Rate = 1; '
                f'foreach ($v in $speak.GetInstalledVoices()) {{ '
                f'  if ($v.VoiceInfo.Name -like "*Zira*") {{ '
                f'    $speak.SelectVoice($v.VoiceInfo.Name); break '
                f'  }} '
                f'}}; '
                f'$speak.Speak("{text}")'
            )
    
    def speak(self, text):
        """Speak text synchronously (blocking) with selected voice."""
        if not self.tts_enabled:
            return
        try:
            if self.system == "Windows":
                cmd = self._get_powershell_voice_command(text)
                subprocess.run(
                    ['powershell', '-Command', cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif self.system == "Darwin":
                # macOS - use different voice
                voice = "Samantha" if self.voice_gender == self.VOICE_FEMALE else "Alex"
                subprocess.run(
                    ['say', '-v', voice, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Linux espeak
                pitch = "80" if self.voice_gender == self.VOICE_FEMALE else "50"
                try:
                    subprocess.run(
                        ['espeak', '-p', pitch, text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except:
                    pass
        except Exception as e:
            print(f"⚠️ TTS Error: {e}")
    
    def speak_async(self, text):
        """Speak text asynchronously (non-blocking) with selected voice."""
        if not self.tts_enabled:
            return
        try:
            if self.system == "Windows":
                cmd = self._get_powershell_voice_command(text)
                self._speech_process = subprocess.Popen(
                    ['powershell', '-Command', cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif self.system == "Darwin":
                voice = "Samantha" if self.voice_gender == self.VOICE_FEMALE else "Alex"
                self._speech_process = subprocess.Popen(
                    ['say', '-v', voice, text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                pitch = "80" if self.voice_gender == self.VOICE_FEMALE else "50"
                try:
                    self._speech_process = subprocess.Popen(
                        ['espeak', '-p', pitch, text],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except:
                    pass
        except Exception as e:
            print(f"⚠️ TTS Error: {e}")
    
    def speak_greeting(self, assistant_name="Nova"):
        """
        ✅ DISABLED - main.py handles greeting
        Only returns text, does NOT speak
        """
        greeting = self.get_time_greeting(assistant_name)
        print(f"🤖 [TEXT ONLY] {greeting}")
        # ❌ REMOVED: self.speak_async(greeting)
        return greeting

    def speak_greeting_sync(self, assistant_name="Nova"):
        """
        ✅ DISABLED - main.py handles greeting  
        Only returns text, does NOT speak
        """
        greeting = self.get_time_greeting(assistant_name)
        print(f"🤖 [TEXT ONLY] {greeting}")
        # ❌ REMOVED: self.speak(greeting)
        return greeting
    
    @staticmethod
    def get_time_greeting(assistant_name="Nova"):
        """Get appropriate greeting based on current time."""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            time_greeting = "Good morning"
        elif 12 <= current_hour < 17:
            time_greeting = "Good afternoon"
        elif 17 <= current_hour < 24:
            time_greeting = "Good evening"
        else:
            time_greeting = "Hello"
        
        return f"{time_greeting}! I'm {assistant_name}. How may I help you?"
    
    def set_tts_rate(self, rate):
        """Set speech rate (not implemented for basic TTS)."""
        pass
    
    def set_tts_volume(self, volume):
        """Set speech volume (not implemented for basic TTS)."""
        pass
    
    def stop_speaking(self):
        """Stop current speech."""
        if self._speech_process:
            try:
                self._speech_process.terminate()
            except:
                pass



def get_audio_manager():
    """Return audio manager instance."""
    return AudioManager()


# ══════════════════════════════════════════════════════════════
#  MODULE-LEVEL IMPORTS (Optimized - no imports inside functions)
# ══════════════════════════════════════════════════════════════

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0  # ✅ ZERO DELAY - Maximum speed
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ pyautogui not installed. Some voice commands won't work.")
    print("   Install with: pip install pyautogui")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False


class CommandResult:
    """Holds the result of a processed voice command."""
    
    __slots__ = ['success', 'command', 'action', 'message', 'category', 'timestamp']
    
    def __init__(self, success, command, action, message, category="GENERAL"):
        self.success = success
        self.command = command
        self.action = action
        self.message = message
        self.category = category
        self.timestamp = datetime.now()

    def __str__(self):
        icon = "✅" if self.success else "❌"
        return f"{icon} [{self.category}] {self.message}"
    
    def __repr__(self):
        return f"CommandResult(success={self.success}, action='{self.action}', message='{self.message}')"


class VoiceCommandProcessor:
    """
    Parses natural language voice commands and executes OS-level actions.
    
    ULTRA OPTIMIZED FOR LOW LATENCY + AUDIO FEEDBACK:
    - Pre-compiled regex patterns
    - Zero PyAutoGUI delay
    - Optimized file search with glob
    - Background file indexing
    - LRU caching for repeated commands
    - Non-blocking subprocess calls
    - Text-to-Speech feedback for all commands
    - Time-based greeting system (Nova)
    
    Supported Categories:
      APP, WEB SEARCH, WEBSITE, FILE/FOLDER, TYPE, VOLUME,
      WINDOW, KEYBOARD, BROWSER, SCROLL, MEDIA, SYSTEM, INFO
    """

    # Class-level constants for performance
    MAX_HISTORY_SIZE = 100
    FILE_CACHE_TIMEOUT = 300  # 5 minutes
    FILE_SEARCH_TIMEOUT = 0.5  # 500ms max for file search
    ASSISTANT_NAME = "Nova"  # ✅ Assistant name constant

     # ✅ NEW: Tab switcher (connected from aurevix_main.py)
    _page_switcher = None

    def set_page_switcher(self, switcher_func):
        """
        Set callback for switching app pages via voice.
        Called from aurevix_main.py after initialization.
        """
        self._page_switcher = switcher_func
        print("✅ Voice Processor: Page switcher connected")
    
    def __init__(self, greet_on_start=False, assistant_name="Nova"):
        """
        Initialize the Voice Command Processor.
        
        Args:
            greet_on_start: If True, speak greeting immediately on initialization
            assistant_name: Name of the assistant (default: "Nova")
        """
        self.system = platform.system()
        self.command_history = []
        self.assistant_name = assistant_name
        VoiceCommandProcessor.ASSISTANT_NAME = assistant_name
        self.is_speaking = False
        self._greeting_cooldown = 0 
        
        # File search cache
        self._file_search_cache = {}
        self._file_index = {}
        self._index_lock = Lock()
        self._index_built = False
        
        # Build command maps
        self._build_app_map()
        self._build_website_map()
        self._build_patterns()
        
        # ✅ Pre-compile all regex patterns for speed
        self._compile_patterns()

        # ✅ Initialize audio manager for TTS
        self.audio = get_audio_manager()
        
        # ✅ Start background file indexing
        Thread(target=self._build_file_index, daemon=True).start()
        
        print(f"🖥️ Voice Command Processor initialized for {self.system}")
        print(f"   ⚡ Ultra-optimized mode enabled")
        print(f"   🔊 Audio feedback enabled")
        print(f"   🤖 Assistant: {self.assistant_name}")
        
        # ✅ Greet user on start if enabled
        if greet_on_start:
            self.greet_user()

    # ══════════════════════════════════════════════════════════════
    #  GREETING SYSTEM - TIME-BASED GREETING
    # ══════════════════════════════════════════════════════════════

    def greet_user(self, blocking=True):
        """
        ✅ DISABLED - main.py handles greeting
        """
        print("  🔇 greet_user() → text only")
        return self.audio.get_time_greeting(self.assistant_name)

    def on_mic_activated(self):
        print("  🔇 on_mic_activated() → text only")
        return self.get_greeting()

    def on_mic_activated_sync(self):
        print("  🔇 on_mic_activated_sync() → text only")
        return self.get_greeting()

    # ══════════════════════════════════════════════════════════════
    #  PATTERN COMPILATION (Pre-compile for speed)
    # ══════════════════════════════════════════════════════════════

    def _compile_patterns(self):
        """Pre-compile all regex patterns for faster matching."""
        self.compiled_patterns = []
        for pattern, handler in self.patterns:
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                self.compiled_patterns.append((compiled, handler))
            except re.error as e:
                print(f"⚠️ Invalid pattern '{pattern}': {e}")

    # ══════════════════════════════════════════════════════════════
    #  BACKGROUND FILE INDEXING
    # ══════════════════════════════════════════════════════════════

    def _build_file_index(self):
        """Build file index in background for faster searches."""
        search_dirs = [
            self._folder("Desktop"),
            self._folder("Documents"),
            self._folder("Downloads"),
        ]
        
        index = {}
        
        for search_dir in search_dirs:
            if not os.path.isdir(search_dir):
                continue
            
            try:
                # Index files up to 2 levels deep
                for pattern in [f"{search_dir}/*", f"{search_dir}/*/*"]:
                    for path in glob.glob(pattern):
                        if os.path.isfile(path):
                            name = os.path.basename(path).lower()
                            if name not in index:
                                index[name] = path
            except Exception:
                pass
        
        with self._index_lock:
            self._file_index = index
            self._index_built = True
        
        print(f"   📁 Indexed {len(index)} files")

    # ══════════════════════════════════════════════════════════════
    #  APP MAP - Applications that can be opened
    # ══════════════════════════════════════════════════════════════

    def _build_app_map(self):
        """Build OS-specific application mapping."""

        self.tab_map = {
            # Dashboard
            "dashboard":     0,
            "home":          0,
            "main":          0,

            # Gestures
            "gestures":      1,
            "gesture":       1,
            "gesture page":  1,

            # Shortcuts
            "shortcuts":     2,
            "shortcut":      2,

            # Logs
            "logs":          3,
            "log":           3,
            "history":       3,

            # Settings
            "settings":      4,
            "setting":       4,

            # Preferences
            "preferences":   5,
            "preference":    5,
            "prefs":         5,

            # AI Trainer
            "ai trainer":    6,
            "ai":            6,
            "trainer":       6,

            # Calibration
            "calibration":   7,
            "calibrate":     7,
            "calib":         7,

            # Gaming Mode
            "gaming":        8,
            "gaming mode":   8,
            "game":          8,

            # Training Mode
            "training":      9,
            "training mode": 9,
        }
        
        if self.system == "Windows":
            self.app_map = {
                # System Apps
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "paint": "mspaint.exe",
                "task manager": "taskmgr.exe",
                "command prompt": "cmd.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "terminal": "wt.exe",
                "snipping tool": "snippingtool.exe",
                "snip": "snippingtool.exe",
                "control panel": "control",
                "settings": "ms-settings:",
                "file explorer": "explorer.exe",
                "explorer": "explorer.exe",
                "files": "explorer.exe",
                
                # Browsers
                "chrome": "chrome",
                "google chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "microsoft edge": "msedge",
                "brave": "brave",
                "opera": "opera",
                
                # Microsoft Office
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "outlook": "outlook",
                "onenote": "onenote",
                
                # Development
                "vscode": "code",
                "visual studio code": "code",
                "visual studio": "devenv",
                "sublime": "sublime_text",
                "atom": "atom",
                
                # Communication
                "discord": "discord",
                "telegram": "telegram",
                "whatsapp": "whatsapp",
                "teams": "teams",
                "slack": "slack",
                "zoom": "zoom",
                "skype": "skype",
                
                # Media
                "vlc": "vlc",
                "spotify": "spotify",
                "media player": "wmplayer",
                "itunes": "itunes",
                
                # Gaming/Creative
                "steam": "steam",
                "obs": "obs64.exe",
                "audacity": "audacity",
                "gimp": "gimp",
                "blender": "blender",
                "photoshop": "photoshop",
                
                # Windows Store Apps
                "store": "ms-windows-store:",
                "camera": "microsoft.windows.camera:",
                "photos": "ms-photos:",
                "clock": "ms-clock:",
                "weather": "bingweather:",
                "calendar": "outlookcal:",
                "mail": "outlookmail:",
                "maps": "bingmaps:",
            }
            
        elif self.system == "Darwin":  # macOS
            self.app_map = {
                "finder": "Finder",
                "safari": "Safari",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "terminal": "Terminal",
                "iterm": "iTerm",
                "calculator": "Calculator",
                "notes": "Notes",
                "music": "Music",
                "photos": "Photos",
                "mail": "Mail",
                "messages": "Messages",
                "facetime": "FaceTime",
                "preview": "Preview",
                "textedit": "TextEdit",
                "pages": "Pages",
                "numbers": "Numbers",
                "keynote": "Keynote",
                "xcode": "Xcode",
                "vscode": "Visual Studio Code",
                "sublime": "Sublime Text",
                "discord": "Discord",
                "slack": "Slack",
                "zoom": "zoom.us",
                "spotify": "Spotify",
                "vlc": "VLC",
                "settings": "System Preferences",
                "preferences": "System Preferences",
            }
            
        else:  # Linux
            self.app_map = {
                "terminal": "gnome-terminal",
                "konsole": "konsole",
                "files": "nautilus",
                "file manager": "nautilus",
                "firefox": "firefox",
                "chrome": "google-chrome",
                "chromium": "chromium-browser",
                "calculator": "gnome-calculator",
                "text editor": "gedit",
                "gedit": "gedit",
                "vscode": "code",
                "sublime": "subl",
                "discord": "discord",
                "spotify": "spotify",
                "vlc": "vlc",
                "gimp": "gimp",
                "blender": "blender",
                "steam": "steam",
                "obs": "obs",
                "audacity": "audacity",
                "libreoffice": "libreoffice",
                "writer": "libreoffice --writer",
                "calc": "libreoffice --calc",
                "settings": "gnome-control-center",
            }

    # ══════════════════════════════════════════════════════════════
    #  WEBSITE MAP - Quick website shortcuts
    # ══════════════════════════════════════════════════════════════

    def _build_website_map(self):
        """Build website shortcut mapping."""
        
        self.website_map = {
            # Search Engines
            "google": "https://www.google.com",
            "bing": "https://www.bing.com",
            "duckduckgo": "https://duckduckgo.com",
            
            # Social Media
            "youtube": "https://www.youtube.com",
            "facebook": "https://www.facebook.com",
            "twitter": "https://www.twitter.com",
            "x": "https://www.x.com",
            "instagram": "https://www.instagram.com",
            "reddit": "https://www.reddit.com",
            "linkedin": "https://www.linkedin.com",
            "pinterest": "https://www.pinterest.com",
            "tiktok": "https://www.tiktok.com",
            "snapchat": "https://www.snapchat.com",
            "tumblr": "https://www.tumblr.com",
            
            # Development
            "github": "https://www.github.com",
            "gitlab": "https://www.gitlab.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
            "codepen": "https://codepen.io",
            "replit": "https://replit.com",
            "npm": "https://www.npmjs.com",
            "pypi": "https://pypi.org",
            
            # Shopping
            "amazon": "https://www.amazon.com",
            "ebay": "https://www.ebay.com",
            "flipkart": "https://www.flipkart.com",
            "alibaba": "https://www.alibaba.com",
            
            # Entertainment
            "netflix": "https://www.netflix.com",
            "prime video": "https://www.primevideo.com",
            "disney plus": "https://www.disneyplus.com",
            "hulu": "https://www.hulu.com",
            "twitch": "https://www.twitch.tv",
            "spotify web": "https://open.spotify.com",
            
            # Productivity
            "gmail": "https://mail.google.com",
            "google drive": "https://drive.google.com",
            "drive": "https://drive.google.com",
            "google docs": "https://docs.google.com",
            "google sheets": "https://sheets.google.com",
            "google slides": "https://slides.google.com",
            "google maps": "https://maps.google.com",
            "maps": "https://maps.google.com",
            "google calendar": "https://calendar.google.com",
            "translate": "https://translate.google.com",
            "google translate": "https://translate.google.com",
            "notion": "https://www.notion.so",
            "trello": "https://trello.com",
            "asana": "https://asana.com",
            "dropbox": "https://www.dropbox.com",
            "onedrive": "https://onedrive.live.com",
            
            # AI Tools
            "chatgpt": "https://chat.openai.com",
            "chat gpt": "https://chat.openai.com",
            "openai": "https://chat.openai.com",
            "claude": "https://claude.ai",
            "bard": "https://bard.google.com",
            "gemini": "https://gemini.google.com",
            "perplexity": "https://www.perplexity.ai",
            "midjourney": "https://www.midjourney.com",
            
            # Reference
            "wikipedia": "https://www.wikipedia.org",
            "wiki": "https://www.wikipedia.org",
            "quora": "https://www.quora.com",
            "medium": "https://medium.com",
            
            # Communication
            "whatsapp web": "https://web.whatsapp.com",
            "telegram web": "https://web.telegram.org",
            "discord web": "https://discord.com/app",
            "slack": "https://slack.com",
            "zoom": "https://zoom.us",
            
            # News
            "bbc": "https://www.bbc.com",
            "cnn": "https://www.cnn.com",
            "nytimes": "https://www.nytimes.com",
            "guardian": "https://www.theguardian.com",
            
            # Education (Custom)
            "msbte": "https://www.msbte.ac.in",
            "vartak website": "https://vcet.edu.in",
            "sjcem website": "https://sjcem.edu.in",
            "academic calendar": "https://msbte.ac.in/uploads/circular/1747917020137_A.Y._2025-26_Academic_Calander.pdf",
            "msbte hall ticket website": "https://online.msbte.co.in/msbte24/index.php?act=hall_ticket&sub=hallticket_s_public",
            "msbte result website": "https://result.msbte.ac.in/"
        }

    # ══════════════════════════════════════════════════════════════
    #  COMMAND PATTERNS - Ordered by frequency for speed
    # ══════════════════════════════════════════════════════════════

    def _build_patterns(self):
        """Build regex patterns for command matching - OPTIMIZED ORDER."""
        
        self.patterns = [
            # ══════════════════════════════════════════════════════
            # TIER 1: MOST FREQUENTLY USED (checked first)
            # ══════════════════════════════════════════════════════
            
            # ── OPEN APP/WEBSITE (most common) ──
            (r'^(?:open|launch|start|run)\s+(.+)', self._open_generic),

            # ── APP TAB NAVIGATION ✅ NEW ──
            (r'^(?:go\s+to|navigate\s+to|switch\s+to|open\s+tab)\s+(.+)$', self._switch_app_tab),
            (r'^(?:go\s+home|home\s+page|go\s+to\s+home)$',               self._go_dashboard),
            (r'^(?:show\s+gestures|gestures\s+page)$',                     self._go_gestures),
            
            # ── SEARCH (very common) ──
            (r'^(?:search|google|look\s*up)\s+(?:for\s+)?(?:on\s+google\s+)?(.+)',
             self._google_search),
            
            # ── GO TO WEBSITE ──
            (r'^(?:go\s+to|visit|browse)\s+(.+)', self._open_website),
            
            # ── TYPE TEXT ──
            (r'^(?:type|write|input)\s+(.+)', self._type_text),
            
            # ══════════════════════════════════════════════════════
            # TIER 2: QUICK ACTIONS (keyboard/volume)
            # ══════════════════════════════════════════════════════
            
            # ── VOLUME CONTROL ──
            (r'^(?:volume\s+up|increase\s+volume|louder|turn\s+(?:it\s+)?up)',
             self._vol_up),
            (r'^(?:volume\s+down|decrease\s+volume|quieter|softer|turn\s+(?:it\s+)?down)',
             self._vol_down),
            (r'^(?:mute|unmute|toggle\s+mute|silence)$', self._mute),
            
            # ── KEYBOARD SHORTCUTS (frequent) ──
            (r'^(?:copy|copy\s+that|copy\s+this)$', self._copy),
            (r'^(?:paste|paste\s+that|paste\s+this)$', self._paste),
            (r'^(?:cut|cut\s+that|cut\s+this)$', self._cut),
            (r'^(?:undo|ctrl\s*z)$', self._undo),
            (r'^(?:redo|ctrl\s*y)$', self._redo),
            (r'^(?:save|save\s+file|save\s+this)$', self._save),
            (r'^(?:select\s+all|select\s+everything)$', self._select_all),
            
            # ── ENTER/PRESS KEY ──
            (r'^(?:press\s+)?enter$', self._press_enter),
            (r'^press\s+(.+)', self._press_key),
            
            # ══════════════════════════════════════════════════════
            # TIER 3: BROWSER ACTIONS
            # ══════════════════════════════════════════════════════
            
            (r'^(?:new\s+tab|open\s+(?:new\s+)?tab)$', self._new_tab),
            (r'^(?:close\s+tab)$', self._close_tab),
            (r'^(?:refresh|reload|reload\s+page)$', self._refresh),
            (r'^(?:go\s+back|back|previous\s+page)$', self._go_back),
            (r'^(?:go\s+forward|forward|next\s+page)$', self._go_forward),
            (r'^(?:zoom\s+in)$', self._zoom_in),
            (r'^(?:zoom\s+out)$', self._zoom_out),
            (r'^(?:reset\s+zoom|normal\s+zoom|zoom\s+reset)$', self._zoom_reset),
            (r'^(?:address\s+bar|url\s+bar|go\s+to\s+address)$', self._address_bar),
            
            # ══════════════════════════════════════════════════════
            # TIER 4: SEARCH VARIANTS
            # ══════════════════════════════════════════════════════
            
            (r'^(?:search\s+on\s+youtube|youtube\s+search|youtube)\s+(.+)',
             self._youtube_search),
            (r'^(?:search\s+on\s+wikipedia|wikipedia|wiki)\s+(.+)',
             self._wiki_search),
            (r'^(?:search\s+on\s+amazon|amazon\s+search|amazon)\s+(.+)',
             self._amazon_search),
            (r'^(?:search\s+on\s+github|github\s+search|github)\s+(.+)',
             self._github_search),
            
            # ══════════════════════════════════════════════════════
            # TIER 5: WINDOW MANAGEMENT
            # ══════════════════════════════════════════════════════
            
            (r'^(?:minimize|minimize\s+window|hide\s+window)$', self._minimize),
            (r'^(?:maximize|maximize\s+window|full\s*screen)$', self._maximize),
            (r'^(?:close\s+window|close\s+this)$', self._close_window),
            (r'^(?:switch\s+window|alt\s+tab|next\s+window)$', self._alt_tab),
            (r'^(?:restore|restore\s+window)$', self._restore_window),
            (r'^(?:snap\s+left|move\s+left|left\s+half)$', self._snap_left),
            (r'^(?:snap\s+right|move\s+right|right\s+half)$', self._snap_right),
            (r'^(?:show\s+desktop|go\s+to\s+desktop|desktop)$', self._show_desktop),
            
            # ══════════════════════════════════════════════════════
            # TIER 6: FOLDER SHORTCUTS
            # ══════════════════════════════════════════════════════
            
            (r'^open\s+(?:my\s+)?downloads?(?:\s+folder)?$', self._open_downloads),
            (r'^open\s+(?:my\s+)?documents?(?:\s+folder)?$', self._open_documents),
            (r'^open\s+(?:my\s+)?desktop(?:\s+folder)?$', self._open_desktop),
            (r'^open\s+(?:my\s+)?pictures?(?:\s+folder)?$', self._open_pictures),
            (r'^open\s+(?:my\s+)?music(?:\s+folder)?$', self._open_music),
            (r'^open\s+(?:my\s+)?videos?(?:\s+folder)?$', self._open_videos),
            (r'^open\s+(?:my\s+)?home(?:\s+folder)?$', self._open_home),
            
            # ══════════════════════════════════════════════════════
            # TIER 7: SCROLL
            # ══════════════════════════════════════════════════════
            
            (r'^(?:scroll\s+up|page\s+up)$', self._scroll_up),
            (r'^(?:scroll\s+down|page\s+down)$', self._scroll_down),
            (r'^(?:scroll\s+(?:to\s+)?top|go\s+(?:to\s+)?top)$', self._scroll_top),
            (r'^(?:scroll\s+(?:to\s+)?bottom|go\s+(?:to\s+)?bottom)$', self._scroll_bottom),
            
            # ══════════════════════════════════════════════════════
            # TIER 8: MEDIA CONTROL
            # ══════════════════════════════════════════════════════
            
            (r'^(?:play|pause|play\s*pause)$', self._play_pause),
            (r'^(?:next\s+(?:track|song)|skip)$', self._next_track),
            (r'^(?:previous\s+(?:track|song)|prev)$', self._prev_track),
            (r'^(?:stop\s+(?:music|media|playing))$', self._stop_media),
            
            # ══════════════════════════════════════════════════════
            # TIER 9: SYSTEM ACTIONS
            # ══════════════════════════════════════════════════════
            
            (r'^(?:screenshot|take\s+(?:a\s+)?screenshot|capture\s+screen|snip)',
             self._screenshot),
            (r'^(?:lock|lock\s+screen|lock\s+computer)$', self._lock),
            (r'^(?:sleep|sleep\s+mode)$', self._sleep),
            (r'^(?:shutdown|shut\s+down|turn\s+off)$', self._shutdown),
            (r'^(?:restart|reboot)$', self._restart),
            (r'^(?:sign\s+out|log\s*out)$', self._sign_out),
            
            # ── BRIGHTNESS ──
            (r'^(?:brightness\s+up|brighter|increase\s+brightness)', self._brightness_up),
            (r'^(?:brightness\s+down|dimmer|darker|decrease\s+brightness)', self._brightness_down),
            
            # ══════════════════════════════════════════════════════
            # TIER 10: INFO & MISC
            # ══════════════════════════════════════════════════════
            
            (r'^(?:what\s+time|time|current\s+time|what\'?s?\s+the\s+time)',
             self._tell_time),
            (r'^(?:what.*date|date|today|what\s+day)', self._tell_date),
            (r'^(?:battery|battery\s+level|power\s+status)', self._battery_status),
            
            # ── FIND/DELETE ──
            (r'^(?:find|search\s+here|ctrl\s*f)$', self._find),
            (r'^(?:delete|backspace)$', self._delete),
            
            # ── CLOSE APP ──
            (r'^(?:close|kill|exit|quit)\s+(.+)', self._close_app),
            
            # ══════════════════════════════════════════════════════
            # TIER 11: FILE SEARCH (slowest - at the end)
            # ══════════════════════════════════════════════════════
            
            (r'^(?:open\s+file|find\s+file|locate)\s+(.+)', self._find_file),
            
            # ══════════════════════════════════════════════════════
            # TIER 12: VOICE CONTROL & HELP
            # ══════════════════════════════════════════════════════
            
            (r'^(?:stop\s+listening|pause\s+listening|shut\s+up)$', self._stop_listening),
            (r'^(?:help|commands|what\s+can\s+you\s+do)$', self._help),
            (r'^(?:clear\s+history|clear\s+commands)$', self._clear_history),
            
            # ══════════════════════════════════════════════════════
            # TIER 13: IDENTITY & GREETING
            # ══════════════════════════════════════════════════════
            
            (r'^(?:who\s+are\s+you|what\'?s?\s+your\s+name|your\s+name)', self._who_am_i),
            (r'^(?:hello|hi|hey)(?:\s+nova)?$', self._greet_response),
        ]

    # ══════════════════════════════════════════════════════════════
    #  MAIN ENTRY POINT - ULTRA OPTIMIZED
    # ══════════════════════════════════════════════════════════════

    def process(self, raw_text):
        """
        Parse raw_text and execute the matching action.
        
        OPTIMIZATIONS:
        - Quick input validation
        - Pre-compiled pattern matching
        - Limited history size
        
        Args:
            raw_text: The voice command text to process
            
        Returns:
            CommandResult object with success status and message
        """
        
        # ═══════════════════════════════════════════════════════════════
        # ✅ NEW: IGNORE INPUT WHILE SPEAKING (prevents echo)
        # ═══════════════════════════════════════════════════════════════
        if self.is_speaking:
            print("  🔇 [IGNORED] Input received while speaking")
            return CommandResult(
                False, "", "IGNORED", 
                "Ignoring input while speaking", 
                "SYSTEM"
            )
    
        # ✅ Quick rejection of invalid input (existing code)
        if not raw_text:
            return CommandResult(False, "", "EMPTY", "No command received", "SYSTEM")
    
        raw_text = str(raw_text).strip()
    
        if len(raw_text) < 2:
            return CommandResult(False, raw_text, "EMPTY", "Command too short", "SYSTEM")
        
        # ✅ Fast text normalization (single pass)
        clean = ' '.join(raw_text.lower().split())
        
        print(f"\n🎤 Processing: '{clean}'")
        start_time = time.perf_counter()  # ✅ More precise timing
        
        # ✅ Pattern matching with pre-compiled patterns
        for pattern, handler in self.compiled_patterns:
            match = pattern.match(clean)
            if match:
                try:
                    result = handler(match, clean)
                except Exception as e:
                    self.audio.speak_async("Error executing command")
                    result = CommandResult(
                        False, clean, "ERROR",
                        f"Error executing command: {str(e)[:50]}", "ERROR"
                    )
                
                # Log execution time
                elapsed = (time.perf_counter() - start_time) * 1000
                
                # ✅ Limit history size
                self.command_history.append(result)
                if len(self.command_history) > self.MAX_HISTORY_SIZE:
                    self.command_history.pop(0)
                
                print(f"   {result} ({elapsed:.1f}ms)")
                return result

        # Fallback — try as direct app name
        fallback = self._try_open_app(clean)
        if fallback and fallback.success:
            self.command_history.append(fallback)
            elapsed = (time.perf_counter() - start_time) * 1000
            print(f"   {fallback} ({elapsed:.1f}ms)")
            return fallback

        # Command not recognized
        self.audio.speak_async(f"Command not recognized")
        result = CommandResult(
            False, clean, "UNKNOWN",
            f"Command not recognized: '{clean}'", "UNKNOWN"
        )
        self.command_history.append(result)
        print(f"   {result}")
        return result

    # ══════════════════════════════════════════════════════════════
    #  HELPER METHODS - OPTIMIZED
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _folder(name):
        """Get path to a user folder."""
        return str(Path.home() / name)

    def _open_path(self, path):
        """Open a file or folder path - non-blocking."""
        try:
            if self.system == "Windows":
                # ✅ Use os.startfile for Windows (faster)
                os.startfile(path)
            elif self.system == "Darwin":
                subprocess.Popen(
                    ["open", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    ["xdg-open", path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            print(f"   ⚠️ Error opening path: {e}")

    def _hotkey(self, *keys):
        """Press a keyboard shortcut - optimized."""
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.hotkey(*keys, interval=0)  # ✅ Zero interval
            except Exception as e:
                print(f"   ⚠️ Hotkey error: {e}")

    def _press(self, key):
        """Press a single key - optimized."""
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press(key, _pause=False)  # ✅ Disable pause
            except Exception as e:
                print(f"   ⚠️ Key press error: {e}")

    def _try_open_app(self, name):
        """
        Try to open an application by name.
    
        Returns:
            CommandResult if successful, None if app not found
        """
        n = name.lower().strip()
        exe = self.app_map.get(n)

        if exe:
            try:
                # ✅ NO speak here - caller already spoke!
            
                if self.system == "Windows":
                    if exe.endswith(":"):
                        # Windows Store app
                        os.startfile(exe)
                    else:
                        subprocess.Popen(
                            f'start "" "{exe}"',
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                elif self.system == "Darwin":
                    subprocess.Popen(
                        ["open", "-a", exe],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(
                        exe.split(),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                return CommandResult(
                    True, f"open {name}", "OPEN_APP",
                    f"🚀 Opened {name}", "APP"
                )
            except Exception as e:
                self.audio.speak_async(f"Failed to open {name}")
                return CommandResult(
                    False, f"open {name}", "OPEN_APP",
                    f"Failed to open {name}: {str(e)[:30]}", "APP"
                )

        # ✅ Skip slow 'where' command for unknown apps
        return None

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - IDENTITY & GREETING
    # ══════════════════════════════════════════════════════════════

    def _who_am_i(self, m, txt):
        """Respond based on current voice gender."""
        # Get current gender from audio manager
        gender = self.audio.get_voice_gender()
        name = "Nova" if gender == "female" else "Nick"
        response = f"I'm {name}, your voice assistant. How may I help you?"
        self.audio.speak_async(response)
        return CommandResult(True, txt, "IDENTITY", f"🤖 {response}", "INFO")
    
    def _greet_response(self, m, txt):
        """Respond with correct name based on voice gender."""
        if time.time() - self._greeting_cooldown < 10:
            print("  🔇 Greeting cooldown active")
            return CommandResult(True, txt, "GREETING", "🤖 (cooldown)", "INFO")
    
        gender = self.audio.get_voice_gender()
        name = "Nova" if gender == "female" else "Nick"
        greeting = self.audio.get_time_greeting(name)
        self.audio.speak_async(greeting)
        self._greeting_cooldown = time.time()
        return CommandResult(True, txt, "GREETING", f"🤖 {greeting}", "INFO")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - APP TAB NAVIGATION  ✅ NEW
    # ══════════════════════════════════════════════════════════════

    def _switch_app_tab(self, match, txt):
        """
        Switch to internal app page by voice.

        Examples:
            'go to settings'
            'switch to gestures'
            'navigate to calibration'
        """
        target = match.group(1).strip().lower()

        # Direct match in tab_map
        page_index = self.tab_map.get(target)

        if page_index is not None:
            return self._do_switch_tab(page_index, target, txt)

        # Partial match fallback
        for tab_name, idx in self.tab_map.items():
            if tab_name in target or target in tab_name:
                return self._do_switch_tab(idx, tab_name, txt)

        # Not a tab — try normal open
        return self._open_generic(match, txt)

    def _do_switch_tab(self, page_index, tab_name, txt):
        """Execute the actual page switch."""
        display_names = {
            0: "Dashboard",
            1: "Gestures",
            2: "Shortcuts",
            3: "Logs",
            4: "Settings",
            5: "Preferences",
            6: "AI Trainer",
            7: "Calibration",
            8: "Gaming Mode",
            9: "Training Mode",
        }
        display = display_names.get(page_index, tab_name.title())

        # Audio feedback
        self.audio.speak_async(f"Opening {display}")

        if self._page_switcher is not None:
            try:
                self._page_switcher(page_index)
                return CommandResult(
                    True, txt, "SWITCH_TAB",
                    f"📄 Switched to {display} (page {page_index})",
                    "NAVIGATION"
                )
            except Exception as e:
                self.audio.speak_async(f"Could not open {display}")
                return CommandResult(
                    False, txt, "SWITCH_TAB",
                    f"Page switch failed: {str(e)[:40]}",
                    "NAVIGATION"
                )
        else:
            self.audio.speak_async("Navigation not ready yet")
            return CommandResult(
                False, txt, "SWITCH_TAB",
                "Page switcher not connected",
                "NAVIGATION"
            )

    def _go_dashboard(self, m, txt):
        """Go to dashboard page."""
        self.audio.speak_async("Going to Dashboard")
        if self._page_switcher:
            self._page_switcher(0)
        return CommandResult(
            True, txt, "SWITCH_TAB", "🏠 Dashboard", "NAVIGATION"
        )

    def _go_gestures(self, m, txt):
        """Go to gestures page."""
        self.audio.speak_async("Opening Gestures")
        if self._page_switcher:
            self._page_switcher(1)
        return CommandResult(
            True, txt, "SWITCH_TAB", "🖐️ Gestures Page", "NAVIGATION"
        )

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - OPEN
    # ══════════════════════════════════════════════════════════════

    def _open_generic(self, match, txt):
        """Handle 'open [target]' command."""
        target = match.group(1).strip()
    
        # 🔊 Audio feedback (ONLY HERE, not in _try_open_app)
        self.audio.speak_async(f"Opening {target}")
    
        # Check if it's a known website
        if target in self.website_map:
            webbrowser.open(self.website_map[target])
            return CommandResult(True, txt, "OPEN_WEB", f"🌐 Opened {target}", "WEB")
    
        # Try to open as app (no speak inside - we already spoke above)
        result = self._try_open_app(target)
        if result and result.success:
            return result
    
        # Try as website (if contains common TLD or is a URL)
        if any(tld in target for tld in ['.com', '.org', '.net', '.io', '.edu', '.gov', 'www.']):
            url = target if target.startswith('http') else f'https://{target}'
            webbrowser.open(url)
            return CommandResult(True, txt, "OPEN_WEB", f"🌐 Opened {target}", "WEB")
    
        # 🔊 Error feedback
        self.audio.speak_async(f"Could not find {target}")
        return CommandResult(False, txt, "OPEN", f"'{target}' not found", "APP")

    def _close_app(self, match, txt):
        """Handle 'close [app]' command."""
        target = match.group(1).strip()
    
        # 🔊 Audio feedback
        self.audio.speak_async(f"Closing {target}")
    
        # ✅ Map common app names to process names
        process_map = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "notepad": "notepad.exe",
            "calculator": "Calculator.exe",
            "calc": "Calculator.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "terminal": "WindowsTerminal.exe",
            "discord": "Discord.exe",
            "spotify": "Spotify.exe",
            "vlc": "vlc.exe",
            "vscode": "Code.exe",
            "visual studio code": "Code.exe",
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "outlook": "OUTLOOK.EXE",
            "teams": "Teams.exe",
            "zoom": "Zoom.exe",
            "slack": "slack.exe",
            "steam": "steam.exe",
            "obs": "obs64.exe",
        }
    
        try:
            if self.system == "Windows":
                # ✅ Try mapped process name first
                process_name = process_map.get(target.lower())
            
                if not process_name:
                    # If not in map, try adding .exe
                    if not target.endswith('.exe'):
                        process_name = f"{target}.exe"
                    else:
                        process_name = target
            
                # Try to kill the process
                result = subprocess.run(
                    ["taskkill", "/IM", process_name, "/F"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=3
                )
            
                if result.returncode == 0:
                    return CommandResult(True, txt, "CLOSE_APP", f"❌ Closed {target}", "APP")
                else:
                    # Try without .exe extension
                    alt_name = target if target.endswith('.exe') else f"{target}"
                    result2 = subprocess.run(
                        ["taskkill", "/FI", f"IMAGENAME eq *{alt_name}*", "/F"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=3
                    )
                
                    if result2.returncode == 0:
                        return CommandResult(True, txt, "CLOSE_APP", f"❌ Closed {target}", "APP")
                    else:
                        self.audio.speak_async(f"Could not find {target}")
                        return CommandResult(False, txt, "CLOSE_APP", f"Process '{target}' not found", "APP")
                    
            elif self.system == "Darwin":
                subprocess.run(
                    ["pkill", "-f", target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                )
                return CommandResult(True, txt, "CLOSE_APP", f"❌ Closed {target}", "APP")
            
            else:  # Linux
                subprocess.run(
                    ["pkill", "-f", target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3
                )
                return CommandResult(True, txt, "CLOSE_APP", f"❌ Closed {target}", "APP")
            
        except subprocess.TimeoutExpired:
            self.audio.speak_async(f"Timeout closing {target}")
            return CommandResult(False, txt, "CLOSE_APP", f"Timeout closing {target}", "APP")
        except Exception as e:
            self.audio.speak_async(f"Failed to close {target}")
            return CommandResult(False, txt, "CLOSE_APP", f"Failed: {str(e)[:30]}", "APP")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - SEARCH
    # ══════════════════════════════════════════════════════════════

    def _google_search(self, match, txt):
        """Google search."""
        query = match.group(1).strip()
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching for {query}")
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, txt, "GOOGLE", f"🔍 Searched: '{query}'", "WEB")

    def _youtube_search(self, match, txt):
        """YouTube search."""
        query = match.group(1).strip()
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching YouTube for {query}")
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, txt, "YOUTUBE", f"▶️ YouTube: '{query}'", "WEB")

    def _wiki_search(self, match, txt):
        """Wikipedia search."""
        query = match.group(1).strip()
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching Wikipedia for {query}")
        url = f"https://en.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, txt, "WIKI", f"📚 Wikipedia: '{query}'", "WEB")

    def _amazon_search(self, match, txt):
        """Amazon search."""
        query = match.group(1).strip()
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching Amazon for {query}")
        url = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, txt, "AMAZON", f"🛒 Amazon: '{query}'", "WEB")

    def _github_search(self, match, txt):
        """GitHub search."""
        query = match.group(1).strip()
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching GitHub for {query}")
        url = f"https://github.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, txt, "GITHUB", f"🐙 GitHub: '{query}'", "WEB")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - WEBSITE
    # ══════════════════════════════════════════════════════════════

    def _open_website(self, match, txt):
        """Open a website."""
        target = match.group(1).strip()
        
        # 🔊 Audio feedback
        self.audio.speak_async(f"Opening {target}")
        
        # Check known websites first
        if target in self.website_map:
            webbrowser.open(self.website_map[target])
            return CommandResult(True, txt, "WEBSITE", f"🌐 Opened {target}", "WEB")
        
        # Construct URL
        if target.startswith(('http://', 'https://')):
            url = target
        elif '.' in target:
            url = f"https://{target}"
        else:
            url = f"https://www.{target}.com"
        
        webbrowser.open(url)
        return CommandResult(True, txt, "WEBSITE", f"🌐 Opened {target}", "WEB")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - FOLDERS
    # ══════════════════════════════════════════════════════════════

    def _folder_cmd(self, folder_name, txt):
        """Generic folder open handler."""
        # 🔊 Audio feedback
        self.audio.speak_async(f"Opening {folder_name} folder")
        
        path = self._folder(folder_name)
        if os.path.isdir(path):
            self._open_path(path)
            return CommandResult(True, txt, "FOLDER", f"📁 Opened {folder_name}", "FILE")
        
        self.audio.speak_async(f"{folder_name} folder not found")
        return CommandResult(False, txt, "FOLDER", f"{folder_name} not found", "FILE")

    def _open_downloads(self, m, txt):
        return self._folder_cmd("Downloads", txt)

    def _open_documents(self, m, txt):
        return self._folder_cmd("Documents", txt)

    def _open_desktop(self, m, txt):
        return self._folder_cmd("Desktop", txt)

    def _open_pictures(self, m, txt):
        return self._folder_cmd("Pictures", txt)

    def _open_music(self, m, txt):
        return self._folder_cmd("Music", txt)

    def _open_videos(self, m, txt):
        return self._folder_cmd("Videos", txt)

    def _open_home(self, m, txt):
        # 🔊 Audio feedback
        self.audio.speak_async("Opening home folder")
        self._open_path(str(Path.home()))
        return CommandResult(True, txt, "FOLDER", "📁 Opened Home folder", "FILE")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - FILE SEARCH (ULTRA OPTIMIZED)
    # ══════════════════════════════════════════════════════════════

    def _find_file(self, match, txt):
        """Find and open a file - ULTRA OPTIMIZED with indexing."""
        name = match.group(1).strip().lower()
        
        # 🔊 Audio feedback
        self.audio.speak_async(f"Searching for file {name}")
        
        # ✅ Check cache first (instant)
        if name in self._file_search_cache:
            cached_path, cache_time = self._file_search_cache[name]
            if time.time() - cache_time < self.FILE_CACHE_TIMEOUT:
                if os.path.exists(cached_path):
                    self.audio.speak_async(f"Opening {os.path.basename(cached_path)}")
                    self._open_path(cached_path)
                    return CommandResult(
                        True, txt, "OPEN_FILE",
                        f"📄 Opened (cached): {os.path.basename(cached_path)}", 
                        "FILE"
                    )
        
        # ✅ Check pre-built index (very fast)
        with self._index_lock:
            if self._index_built:
                for filename, filepath in self._file_index.items():
                    if name in filename:
                        self._file_search_cache[name] = (filepath, time.time())
                        self.audio.speak_async(f"Opening {os.path.basename(filepath)}")
                        self._open_path(filepath)
                        return CommandResult(
                            True, txt, "OPEN_FILE",
                            f"📄 Opened: {os.path.basename(filepath)}", 
                            "FILE"
                        )
        
        # ✅ Fallback: Fast glob search with timeout
        search_dirs = [
            self._folder("Desktop"),
            self._folder("Documents"),
            self._folder("Downloads"),
        ]
        
        start_time = time.perf_counter()
        
        for search_dir in search_dirs:
            if not os.path.isdir(search_dir):
                continue
            
            # Timeout check
            if time.perf_counter() - start_time > self.FILE_SEARCH_TIMEOUT:
                self.audio.speak_async("Search timed out")
                return CommandResult(
                    False, txt, "FIND_FILE",
                    f"⏱️ Search timeout", "FILE"
                )
            
            # ✅ Use glob for faster search
            for depth_pattern in [f"*{name}*", f"*/*{name}*"]:
                pattern = os.path.join(search_dir, depth_pattern)
                try:
                    matches = glob.glob(pattern)
                    for full_path in matches:
                        if os.path.isfile(full_path):
                            # Cache result
                            self._file_search_cache[name] = (full_path, time.time())
                            self.audio.speak_async(f"Opening {os.path.basename(full_path)}")
                            self._open_path(full_path)
                            return CommandResult(
                                True, txt, "OPEN_FILE",
                                f"📄 Opened: {os.path.basename(full_path)}", 
                                "FILE"
                            )
                except Exception:
                    pass
        
        self.audio.speak_async(f"File {name} not found")
        return CommandResult(
            False, txt, "FIND_FILE",
            f"File '{name}' not found", "FILE"
        )

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - TYPE / PRESS (OPTIMIZED)
    # ══════════════════════════════════════════════════════════════

    def _type_text(self, match, txt):
        """Type text using keyboard - OPTIMIZED."""
        text = match.group(1)
        
        # 🔊 Audio feedback
        self.audio.speak_async("Typing")
        
        if not PYAUTOGUI_AVAILABLE:
            self.audio.speak_async("Typing not available")
            return CommandResult(False, txt, "TYPE", "pyautogui not installed", "TYPE")
        
        try:
            # ✅ OPTIMIZED: Direct write for short ASCII text
            if len(text) <= 50 and text.isascii():
                pyautogui.write(text, interval=0)  # ✅ Zero interval
            else:
                # Use clipboard for longer/non-ASCII text
                if PYPERCLIP_AVAILABLE:
                    pyperclip.copy(text)
                    if self.system == "Darwin":
                        pyautogui.hotkey('command', 'v', interval=0)
                    else:
                        pyautogui.hotkey('ctrl', 'v', interval=0)
                else:
                    pyautogui.write(text, interval=0.01)
                    
        except Exception as e:
            self.audio.speak_async("Typing failed")
            return CommandResult(False, txt, "TYPE", f"Error: {str(e)[:30]}", "TYPE")
        
        display_text = text[:30] + "..." if len(text) > 30 else text
        return CommandResult(True, txt, "TYPE", f"⌨️ Typed: '{display_text}'", "TYPE")

    def _press_enter(self, m, txt):
        """Press Enter key."""
        # 🔊 Audio feedback
        self.audio.speak_async("Enter")
        self._press("enter")
        return CommandResult(True, txt, "KEY", "↵ Pressed Enter", "TYPE")

    def _press_key(self, match, txt):
        """Press a specific key."""
        key = match.group(1).strip().lower().replace(" ", "")
        
        # 🔊 Audio feedback
        self.audio.speak_async(f"Pressing {key}")
        
        key_map = {
            "space": "space",
            "spacebar": "space",
            "tab": "tab",
            "escape": "esc",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "up": "up",
            "down": "down",
            "left": "left",
            "right": "right",
            "home": "home",
            "end": "end",
            "pageup": "pageup",
            "pagedown": "pagedown",
            "capslock": "capslock",
            "numlock": "numlock",
            "printscreen": "printscreen",
            "insert": "insert",
        }
        
        # Add function keys
        for i in range(1, 13):
            key_map[f"f{i}"] = f"f{i}"
        
        actual_key = key_map.get(key, key)
        self._press(actual_key)
        return CommandResult(True, txt, "KEY", f"⌨️ Pressed {actual_key}", "TYPE")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - VOLUME (OPTIMIZED)
    # ══════════════════════════════════════════════════════════════

    def _vol_up(self, m, txt):
        """Increase volume - OPTIMIZED with key hold."""
        # 🔊 Audio feedback
        self.audio.speak_async("Volume up")
        if PYAUTOGUI_AVAILABLE:
            # ✅ Multiple quick presses without pause
            for _ in range(3):
                pyautogui.press("volumeup", _pause=False)
        return CommandResult(True, txt, "VOL", "🔊 Volume Up", "VOLUME")

    def _vol_down(self, m, txt):
        """Decrease volume - OPTIMIZED."""
        # 🔊 Audio feedback
        self.audio.speak_async("Volume down")
        if PYAUTOGUI_AVAILABLE:
            for _ in range(3):
                pyautogui.press("volumedown", _pause=False)
        return CommandResult(True, txt, "VOL", "🔉 Volume Down", "VOLUME")

    def _mute(self, m, txt):
        """Toggle mute."""
        # 🔊 Audio feedback
        self.audio.speak_async("Mute toggled")
        self._press("volumemute")
        return CommandResult(True, txt, "VOL", "🔇 Mute toggled", "VOLUME")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - BRIGHTNESS
    # ══════════════════════════════════════════════════════════════

    def _brightness_up(self, m, txt):
        """Increase screen brightness."""
        # 🔊 Audio feedback
        self.audio.speak_async("Brightness up")
        if self.system == "Windows" and SBC_AVAILABLE:
            try:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(min(100, current + 15))
                return CommandResult(True, txt, "BRIGHT", "☀️ Brightness Up", "SYSTEM")
            except Exception as e:
                self.audio.speak_async("Brightness control failed")
                return CommandResult(False, txt, "BRIGHT", f"Error: {str(e)[:30]}", "SYSTEM")
        self.audio.speak_async("Brightness control not supported")
        return CommandResult(False, txt, "BRIGHT", "Not supported", "SYSTEM")

    def _brightness_down(self, m, txt):
        """Decrease screen brightness."""
        # 🔊 Audio feedback
        self.audio.speak_async("Brightness down")
        if self.system == "Windows" and SBC_AVAILABLE:
            try:
                current = sbc.get_brightness()[0]
                sbc.set_brightness(max(0, current - 15))
                return CommandResult(True, txt, "BRIGHT", "🔅 Brightness Down", "SYSTEM")
            except Exception as e:
                self.audio.speak_async("Brightness control failed")
                return CommandResult(False, txt, "BRIGHT", f"Error: {str(e)[:30]}", "SYSTEM")
        self.audio.speak_async("Brightness control not supported")
        return CommandResult(False, txt, "BRIGHT", "Not supported", "SYSTEM")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - WINDOW MANAGEMENT
    # ══════════════════════════════════════════════════════════════

    def _minimize(self, m, txt):
        """Minimize current window."""
        # 🔊 Audio feedback
        self.audio.speak_async("Minimizing window")
        if self.system == "Windows":
            self._hotkey("win", "down")
        elif self.system == "Darwin":
            self._hotkey("command", "m")
        else:
            self._hotkey("super", "h")
        return CommandResult(True, txt, "WIN", "⬇️ Minimized", "WINDOW")

    def _maximize(self, m, txt):
        """Maximize current window."""
        # 🔊 Audio feedback
        self.audio.speak_async("Maximizing window")
        if self.system == "Windows":
            self._hotkey("win", "up")
        elif self.system == "Darwin":
            self._hotkey("command", "ctrl", "f")
        else:
            self._hotkey("super", "up")
        return CommandResult(True, txt, "WIN", "⬆️ Maximized", "WINDOW")

    def _close_window(self, m, txt):
        """Close current window."""
        # 🔊 Audio feedback
        self.audio.speak_async("Closing window")
        if self.system == "Darwin":
            self._hotkey("command", "w")
        else:
            self._hotkey("alt", "F4")
        return CommandResult(True, txt, "WIN", "❌ Closed window", "WINDOW")

    def _alt_tab(self, m, txt):
        """Switch to next window."""
        # 🔊 Audio feedback
        self.audio.speak_async("Switching window")
        if self.system == "Darwin":
            self._hotkey("command", "tab")
        else:
            self._hotkey("alt", "tab")
        return CommandResult(True, txt, "WIN", "🔄 Switched window", "WINDOW")

    def _restore_window(self, m, txt):
        """Restore window to normal size."""
        # 🔊 Audio feedback
        self.audio.speak_async("Restoring window")
        if self.system == "Windows":
            self._hotkey("win", "down")
        return CommandResult(True, txt, "WIN", "↩️ Restored", "WINDOW")

    def _snap_left(self, m, txt):
        """Snap window to left half."""
        # 🔊 Audio feedback
        self.audio.speak_async("Snapping left")
        if self.system == "Windows":
            self._hotkey("win", "left")
        return CommandResult(True, txt, "WIN", "⬅️ Snapped left", "WINDOW")

    def _snap_right(self, m, txt):
        """Snap window to right half."""
        # 🔊 Audio feedback
        self.audio.speak_async("Snapping right")
        if self.system == "Windows":
            self._hotkey("win", "right")
        return CommandResult(True, txt, "WIN", "➡️ Snapped right", "WINDOW")

    def _show_desktop(self, m, txt):
        """Show desktop."""
        # 🔊 Audio feedback
        self.audio.speak_async("Showing desktop")
        if self.system == "Windows":
            self._hotkey("win", "d")
        elif self.system == "Darwin":
            self._hotkey("command", "F3")
        else:
            self._hotkey("super", "d")
        return CommandResult(True, txt, "WIN", "🖥️ Show Desktop", "WINDOW")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - KEYBOARD SHORTCUTS
    # ══════════════════════════════════════════════════════════════

    def _copy(self, m, txt):
        """Copy selection."""
        # 🔊 Audio feedback
        self.audio.speak_async("Copied")
        if self.system == "Darwin":
            self._hotkey("command", "c")
        else:
            self._hotkey("ctrl", "c")
        return CommandResult(True, txt, "KB", "📋 Copied", "KEYBOARD")

    def _paste(self, m, txt):
        """Paste from clipboard."""
        # 🔊 Audio feedback
        self.audio.speak_async("Pasted")
        if self.system == "Darwin":
            self._hotkey("command", "v")
        else:
            self._hotkey("ctrl", "v")
        return CommandResult(True, txt, "KB", "📋 Pasted", "KEYBOARD")

    def _cut(self, m, txt):
        """Cut selection."""
        # 🔊 Audio feedback
        self.audio.speak_async("Cut")
        if self.system == "Darwin":
            self._hotkey("command", "x")
        else:
            self._hotkey("ctrl", "x")
        return CommandResult(True, txt, "KB", "✂️ Cut", "KEYBOARD")

    def _undo(self, m, txt):
        """Undo last action."""
        # 🔊 Audio feedback
        self.audio.speak_async("Undo")
        if self.system == "Darwin":
            self._hotkey("command", "z")
        else:
            self._hotkey("ctrl", "z")
        return CommandResult(True, txt, "KB", "↩️ Undo", "KEYBOARD")

    def _redo(self, m, txt):
        """Redo last action."""
        # 🔊 Audio feedback
        self.audio.speak_async("Redo")
        if self.system == "Darwin":
            self._hotkey("command", "shift", "z")
        else:
            self._hotkey("ctrl", "y")
        return CommandResult(True, txt, "KB", "↪️ Redo", "KEYBOARD")

    def _select_all(self, m, txt):
        """Select all."""
        # 🔊 Audio feedback
        self.audio.speak_async("Selected all")
        if self.system == "Darwin":
            self._hotkey("command", "a")
        else:
            self._hotkey("ctrl", "a")
        return CommandResult(True, txt, "KB", "🔲 Selected all", "KEYBOARD")

    def _save(self, m, txt):
        """Save file."""
        # 🔊 Audio feedback
        self.audio.speak_async("Saving")
        if self.system == "Darwin":
            self._hotkey("command", "s")
        else:
            self._hotkey("ctrl", "s")
        return CommandResult(True, txt, "KB", "💾 Saved", "KEYBOARD")

    def _delete(self, m, txt):
        """Delete/backspace."""
        # 🔊 Audio feedback
        self.audio.speak_async("Deleted")
        self._press("backspace")
        return CommandResult(True, txt, "KB", "🗑️ Deleted", "KEYBOARD")

    def _find(self, m, txt):
        """Open find dialog."""
        # 🔊 Audio feedback
        self.audio.speak_async("Opening find")
        if self.system == "Darwin":
            self._hotkey("command", "f")
        else:
            self._hotkey("ctrl", "f")
        return CommandResult(True, txt, "KB", "🔍 Find opened", "KEYBOARD")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - BROWSER
    # ══════════════════════════════════════════════════════════════

    def _new_tab(self, m, txt):
        """Open new browser tab."""
        # 🔊 Audio feedback
        self.audio.speak_async("New tab")
        if self.system == "Darwin":
            self._hotkey("command", "t")
        else:
            self._hotkey("ctrl", "t")
        return CommandResult(True, txt, "BR", "➕ New tab", "BROWSER")

    def _close_tab(self, m, txt):
        """Close current browser tab."""
        # 🔊 Audio feedback
        self.audio.speak_async("Closing tab")
        if self.system == "Darwin":
            self._hotkey("command", "w")
        else:
            self._hotkey("ctrl", "w")
        return CommandResult(True, txt, "BR", "❌ Closed tab", "BROWSER")

    def _refresh(self, m, txt):
        """Refresh page."""
        # 🔊 Audio feedback
        self.audio.speak_async("Refreshing")
        if self.system == "Darwin":
            self._hotkey("command", "r")
        else:
            self._press("f5")
        return CommandResult(True, txt, "BR", "🔄 Refreshed", "BROWSER")

    def _go_back(self, m, txt):
        """Go back in browser."""
        # 🔊 Audio feedback
        self.audio.speak_async("Going back")
        if self.system == "Darwin":
            self._hotkey("command", "[")
        else:
            self._hotkey("alt", "left")
        return CommandResult(True, txt, "BR", "⬅️ Back", "BROWSER")

    def _go_forward(self, m, txt):
        """Go forward in browser."""
        # 🔊 Audio feedback
        self.audio.speak_async("Going forward")
        if self.system == "Darwin":
            self._hotkey("command", "]")
        else:
            self._hotkey("alt", "right")
        return CommandResult(True, txt, "BR", "➡️ Forward", "BROWSER")

    def _zoom_in(self, m, txt):
        """Zoom in."""
        # 🔊 Audio feedback
        self.audio.speak_async("Zooming in")
        if self.system == "Darwin":
            self._hotkey("command", "=")
        else:
            self._hotkey("ctrl", "=")
        return CommandResult(True, txt, "BR", "🔍 Zoom in", "BROWSER")

    def _zoom_out(self, m, txt):
        """Zoom out."""
        # 🔊 Audio feedback
        self.audio.speak_async("Zooming out")
        if self.system == "Darwin":
            self._hotkey("command", "-")
        else:
            self._hotkey("ctrl", "-")
        return CommandResult(True, txt, "BR", "🔍 Zoom out", "BROWSER")

    def _zoom_reset(self, m, txt):
        """Reset zoom to 100%."""
        # 🔊 Audio feedback
        self.audio.speak_async("Zoom reset")
        if self.system == "Darwin":
            self._hotkey("command", "0")
        else:
            self._hotkey("ctrl", "0")
        return CommandResult(True, txt, "BR", "🔍 Zoom reset", "BROWSER")

    def _address_bar(self, m, txt):
        """Focus address bar."""
        # 🔊 Audio feedback
        self.audio.speak_async("Address bar")
        if self.system == "Darwin":
            self._hotkey("command", "l")
        else:
            self._hotkey("ctrl", "l")
        return CommandResult(True, txt, "BR", "📍 Address bar focused", "BROWSER")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - SCROLL
    # ══════════════════════════════════════════════════════════════

    def _scroll_up(self, m, txt):
        """Scroll up."""
        # 🔊 Audio feedback
        self.audio.speak_async("Scrolling up")
        if PYAUTOGUI_AVAILABLE:
            pyautogui.scroll(5)
        return CommandResult(True, txt, "SCROLL", "⬆️ Scrolled up", "SCROLL")

    def _scroll_down(self, m, txt):
        """Scroll down."""
        # 🔊 Audio feedback
        self.audio.speak_async("Scrolling down")
        if PYAUTOGUI_AVAILABLE:
            pyautogui.scroll(-5)
        return CommandResult(True, txt, "SCROLL", "⬇️ Scrolled down", "SCROLL")

    def _scroll_top(self, m, txt):
        """Scroll to top of page."""
        # 🔊 Audio feedback
        self.audio.speak_async("Scrolling to top")
        if self.system == "Darwin":
            self._hotkey("command", "up")
        else:
            self._hotkey("ctrl", "Home")
        return CommandResult(True, txt, "SCROLL", "⏫ Scrolled to top", "SCROLL")

    def _scroll_bottom(self, m, txt):
        """Scroll to bottom of page."""
        # 🔊 Audio feedback
        self.audio.speak_async("Scrolling to bottom")
        if self.system == "Darwin":
            self._hotkey("command", "down")
        else:
            self._hotkey("ctrl", "End")
        return CommandResult(True, txt, "SCROLL", "⏬ Scrolled to bottom", "SCROLL")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - MEDIA
    # ══════════════════════════════════════════════════════════════

    def _play_pause(self, m, txt):
        """Play/pause media."""
        # 🔊 Audio feedback
        self.audio.speak_async("Play pause")
        self._press("playpause")
        return CommandResult(True, txt, "MEDIA", "⏯️ Play/Pause", "MEDIA")

    def _next_track(self, m, txt):
        """Next track."""
        # 🔊 Audio feedback
        self.audio.speak_async("Next track")
        self._press("nexttrack")
        return CommandResult(True, txt, "MEDIA", "⏭️ Next track", "MEDIA")

    def _prev_track(self, m, txt):
        """Previous track."""
        # 🔊 Audio feedback
        self.audio.speak_async("Previous track")
        self._press("prevtrack")
        return CommandResult(True, txt, "MEDIA", "⏮️ Previous track", "MEDIA")

    def _stop_media(self, m, txt):
        """Stop media playback."""
        # 🔊 Audio feedback
        self.audio.speak_async("Stopping media")
        self._press("stop")
        return CommandResult(True, txt, "MEDIA", "⏹️ Stopped", "MEDIA")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - SCREENSHOT
    # ══════════════════════════════════════════════════════════════

    def _screenshot(self, m, txt):
        """Take a screenshot."""
        # 🔊 Audio feedback
        self.audio.speak_async("Taking screenshot")
        if self.system == "Windows":
            self._hotkey("win", "shift", "s")
        elif self.system == "Darwin":
            self._hotkey("command", "shift", "4")
        else:
            self._press("printscreen")
        return CommandResult(True, txt, "SCREENSHOT", "📸 Screenshot tool opened", "SYSTEM")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - SYSTEM
    # ══════════════════════════════════════════════════════════════

    def _lock(self, m, txt):
        """Lock the computer."""
        # 🔊 Audio feedback
        self.audio.speak_async("Locking computer")
        if self.system == "Windows":
            subprocess.Popen(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif self.system == "Darwin":
            subprocess.Popen(
                ["pmset", "displaysleepnow"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                ["loginctl", "lock-session"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return CommandResult(True, txt, "LOCK", "🔒 Computer locked", "SYSTEM")

    def _sleep(self, m, txt):
        """Put computer to sleep."""
        # 🔊 Audio feedback
        self.audio.speak_async("Going to sleep")
        if self.system == "Windows":
            subprocess.Popen(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif self.system == "Darwin":
            subprocess.Popen(
                ["pmset", "sleepnow"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                ["systemctl", "suspend"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return CommandResult(True, txt, "SLEEP", "😴 Going to sleep", "SYSTEM")

    # ══════════════════════════════════════════════════════════════
    #  SHUTDOWN & RESTART - FIXED (Correct Indentation)
    # ══════════════════════════════════════════════════════════════

    def _shutdown(self, m, txt):
        """Open official Windows Shut Down dialog."""
        self.audio.speak_async("Opening shutdown menu")
    
        if self.system == "Windows":
            if PYAUTOGUI_AVAILABLE:
                try:
                    # Step 1: Show Desktop (minimize all windows)
                    pyautogui.hotkey('win', 'd', interval=0)
                    time.sleep(0.5)  # Wait for desktop to focus
                    
                    # Step 2: Press Alt+F4 to open Shutdown Dialog
                    pyautogui.hotkey('alt', 'f4', interval=0)
                    
                    return CommandResult(
                        True, txt, "SHUTDOWN", 
                        "🖥️ Shutdown dialog opened. Select option and press OK.", "SYSTEM"
                    )
                except Exception as e:
                    print(f"⚠️ Error: {e}")
            
            # Fallback: Command line shutdown
            subprocess.Popen(["shutdown", "/s", "/t", "60"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CommandResult(True, txt, "SHUTDOWN", "⚠️ Shutting down in 60 seconds", "SYSTEM")
        else:
            subprocess.Popen(["shutdown", "-h", "+1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CommandResult(True, txt, "SHUTDOWN", "⚠️ Shutting down in 1 minute", "SYSTEM")

    def _restart(self, m, txt):
        """Open official Windows Shut Down dialog."""
        self.audio.speak_async("Opening shutdown menu")
    
        if self.system == "Windows":
            if PYAUTOGUI_AVAILABLE:
                try:
                    # Step 1: Show Desktop (minimize all windows)
                    pyautogui.hotkey('win', 'd', interval=0)
                    time.sleep(0.5)  # Wait for desktop to focus
                    
                    # Step 2: Press Alt+F4 to open Shutdown Dialog
                    pyautogui.hotkey('alt', 'f4', interval=0)
                    
                    return CommandResult(
                        True, txt, "RESTART", 
                        "🖥️ Shutdown dialog opened. Select 'Restart' and press OK.", "SYSTEM"
                    )
                except Exception as e:
                    print(f"⚠️ Error: {e}")
            
            # Fallback: Command line restart
            subprocess.Popen(["shutdown", "/r", "/t", "60"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CommandResult(True, txt, "RESTART", "⚠️ Restarting in 60 seconds", "SYSTEM")
        else:
            subprocess.Popen(["shutdown", "-r", "+1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CommandResult(True, txt, "RESTART", "⚠️ Restarting in 1 minute", "SYSTEM")

    def _sign_out(self, m, txt):
        """Sign out of the current session."""
        # 🔊 Audio feedback
        self.audio.speak_async("Signing out")
        if self.system == "Windows":
            subprocess.Popen(
                ["shutdown", "/l"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif self.system == "Darwin":
            subprocess.Popen(
                ["osascript", "-e", 'tell application "System Events" to log out'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                ["gnome-session-quit", "--logout"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return CommandResult(True, txt, "SIGNOUT", "👋 Signing out", "SYSTEM")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - INFO (WITH SPOKEN RESPONSES!)
    # ══════════════════════════════════════════════════════════════

    def _tell_time(self, m, txt):
        """Tell the current time."""
        current_time = datetime.now().strftime("%I:%M %p")
        # 🔊 Audio feedback - SPEAK THE TIME!
        self.audio.speak_async(f"The current time is {current_time}")
        return CommandResult(True, txt, "TIME", f"🕐 Current time: {current_time}", "INFO")

    def _tell_date(self, m, txt):
        """Tell the current date."""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        # 🔊 Audio feedback - SPEAK THE DATE!
        self.audio.speak_async(f"Today is {current_date}")
        return CommandResult(True, txt, "DATE", f"📅 Today is: {current_date}", "INFO")

    def _battery_status(self, m, txt):
        """Get battery status."""
        if PSUTIL_AVAILABLE:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    status = "charging" if battery.power_plugged else "not charging"
                    # 🔊 Audio feedback - SPEAK BATTERY STATUS!
                    self.audio.speak_async(f"Battery is at {battery.percent:.0f} percent, {status}")
                    return CommandResult(
                        True, txt, "BATTERY",
                        f"🔋 Battery: {battery.percent:.0f}% ({status})", "INFO"
                    )
                self.audio.speak_async("No battery detected")
                return CommandResult(False, txt, "BATTERY", "No battery detected", "INFO")
            except Exception as e:
                self.audio.speak_async("Could not get battery status")
                return CommandResult(False, txt, "BATTERY", f"Error: {str(e)[:30]}", "INFO")
        self.audio.speak_async("Battery monitoring not available")
        return CommandResult(False, txt, "BATTERY", "Install: pip install psutil", "INFO")

    # ══════════════════════════════════════════════════════════════
    #  COMMAND HANDLERS - VOICE CONTROL & HELP
    # ══════════════════════════════════════════════════════════════

    def _stop_listening(self, m, txt):
        """Signal to stop voice listening."""
        # 🔊 Audio feedback
        self.audio.speak_async("Stopping voice control")
        return CommandResult(True, txt, "STOP_LISTEN", "🛑 Stopped listening", "CONTROL")

    def _clear_history(self, m, txt):
        """Clear command history."""
        # 🔊 Audio feedback
        self.audio.speak_async("History cleared")
        self.command_history.clear()
        self._file_search_cache.clear()
        return CommandResult(True, txt, "CLEAR", "🗑️ History cleared", "CONTROL")

    def _help(self, m, txt):
        """Show help message."""
        # 🔊 Audio feedback
        self.audio.speak_async("Showing help commands")
        help_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🎤 VOICE COMMAND HELP                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ 📱 APPS:      "open chrome", "open notepad", "close discord"                 ║
║ 🔍 SEARCH:    "search python tutorial", "youtube cats", "wikipedia python"  ║
║ 🌐 WEBSITES:  "go to github", "visit reddit"                                 ║
║ 📁 FOLDERS:   "open downloads", "open documents"                             ║
║ 📄 FILES:     "open file report", "find file notes"                          ║
║ ⌨️ TYPE:      "type hello world", "press enter"                              ║
║ 🔊 VOLUME:    "volume up", "volume down", "mute"                             ║
║ 🪟 WINDOWS:   "minimize", "maximize", "close window", "alt tab"              ║
║ 📋 EDIT:      "copy", "paste", "undo", "save", "select all"                  ║
║ 🌐 BROWSER:   "new tab", "close tab", "refresh", "go back"                   ║
║ 📜 SCROLL:    "scroll up", "scroll down", "scroll to top"                    ║
║ 🎵 MEDIA:     "play", "pause", "next track"                                  ║
║ 📸 SYSTEM:    "screenshot", "lock", "sleep"                                  ║
║ ℹ️ INFO:      "what time", "what date", "battery"                            ║
║ 🤖 NOVA:      "hello", "hi", "who are you"                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        print(help_text)
        return CommandResult(True, txt, "HELP", "📖 Help displayed above", "INFO")

    # ══════════════════════════════════════════════════════════════
    #  UTILITY METHODS
    # ══════════════════════════════════════════════════════════════

    def get_history(self, limit=10):
        """Get recent command history."""
        return self.command_history[-limit:]

    def get_supported_apps(self):
        """Get list of supported applications."""
        return list(self.app_map.keys())

    def get_supported_websites(self):
        """Get list of supported websites."""
        return list(self.website_map.keys())

    def add_custom_app(self, name, executable):
        """Add a custom application to the app map."""
        self.app_map[name.lower()] = executable
        self.audio.speak_async(f"Added custom app {name}")
        print(f"✅ Added custom app: {name} -> {executable}")

    def add_custom_website(self, name, url):
        """Add a custom website to the website map."""
        self.website_map[name.lower()] = url
        self.audio.speak_async(f"Added custom website {name}")
        print(f"✅ Added custom website: {name} -> {url}")

    def set_audio_enabled(self, enabled: bool):
        """Enable/disable audio feedback."""
        self.audio.tts_enabled = enabled
        print(f"🔊 Audio feedback {'enabled' if enabled else 'disabled'}")

    def set_audio_rate(self, rate: int):
        """Set TTS speech rate (100-200)."""
        self.audio.set_tts_rate(rate)

    def set_audio_volume(self, volume: float):
        """Set TTS volume (0.0-1.0)."""
        self.audio.set_tts_volume(volume)
    
    def set_assistant_name(self, name: str):
        """Change the assistant's name."""
        self.assistant_name = name
        VoiceCommandProcessor.ASSISTANT_NAME = name
        print(f"🤖 Assistant name changed to: {name}")


# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE BENCHMARKING
# ══════════════════════════════════════════════════════════════════════════════

def benchmark_commands(processor, iterations=10):
    """Benchmark common commands for performance testing."""
    
    # Temporarily disable audio for benchmarking
    original_tts_state = processor.audio.tts_enabled
    processor.audio.tts_enabled = False
    
    test_commands = [
        "volume up",
        "copy",
        "paste",
        "new tab",
        "scroll down",
        "what time",
        "search hello world",
        "open chrome",
    ]
    
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARK (Audio disabled for accuracy)")
    print("="*60)
    
    results = {}
    
    for cmd in test_commands:
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            processor.process(cmd)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        results[cmd] = avg_time
        
        print(f"  '{cmd}': avg={avg_time:.1f}ms, min={min_time:.1f}ms, max={max_time:.1f}ms")
    
    print("="*60)
    overall_avg = sum(results.values()) / len(results)
    print(f"  OVERALL AVERAGE: {overall_avg:.1f}ms")
    print("="*60 + "\n")
    
    # Restore audio state
    processor.audio.tts_enabled = original_tts_state
    
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN - INTERACTIVE TESTING
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Interactive testing mode for the voice command processor."""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    VOICE COMMAND PROCESSOR - ULTRA OPTIMIZED                 ║
║                           Interactive Testing Mode                           ║
║                                                                              ║
║  ⚡ Pre-compiled regex patterns                                              ║
║  ⚡ Zero PyAutoGUI delay                                                     ║
║  ⚡ Background file indexing                                                 ║
║  ⚡ Optimized clipboard operations                                          ║
║  🔊 Audio feedback for ALL commands                                          ║
║  🤖 Nova Assistant with time-based greetings                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # ✅ Initialize with greeting on start!
    processor = VoiceCommandProcessor(greet_on_start=True, assistant_name="Nova")
    
    # Wait for file indexing
    time.sleep(0.5)
    
    print("\n📋 Commands:")
    print("   - Type any voice command to test")
    print("   - 'benchmark' - Run performance benchmark")
    print("   - 'help' - Show all commands")
    print("   - 'audio on/off' - Toggle audio feedback")
    print("   - 'greet' - Trigger greeting manually")
    print("   - 'quit' - Exit")
    print()
    
    while True:
        try:
            command = input("🎤 > ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['quit', 'exit', 'q']:
                processor.audio.speak_async("Goodbye!")
                print("\n👋 Goodbye!")
                break
            
            if command.lower() == 'benchmark':
                benchmark_commands(processor)
                continue
            
            if command.lower() == 'audio on':
                processor.set_audio_enabled(True)
                processor.audio.speak_async("Audio enabled")
                continue
            
            if command.lower() == 'audio off':
                processor.set_audio_enabled(False)
                print("🔇 Audio feedback disabled")
                continue
            
            if command.lower() == 'greet':
                # ✅ Manually trigger greeting (simulates mic activation)
                processor.on_mic_activated()
                continue
            
            result = processor.process(command)
            
            # Check if we should stop listening
            if result.action == "STOP_LISTEN":
                print("\n👋 Stopping...")
                break
                
        except KeyboardInterrupt:
            processor.audio.speak_async("Interrupted")
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
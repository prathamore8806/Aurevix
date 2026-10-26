"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          ACTIVE AI ENGINE                                    ║
║              👁️ Vision  +  👂 Voice  +  🧠 Command Processing               ║
║                  🎤 VOICE COMMAND INTEGRATION                                ║
║              ✅ FIX: NO DUPLICATE, ECHO PROTECTION ADDED                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import cv2
import mediapipe as mp
import speech_recognition as sr
import threading
import numpy as np
import time
from PySide6.QtCore import QThread, Signal

from voice_command_processor import VoiceCommandProcessor, CommandResult


class ActiveAIEngine(QThread):

    frame_ready       = Signal(np.ndarray)
    gesture_detected  = Signal(bool, list)
    voice_command     = Signal(str)
    command_result    = Signal(object)
    listening_started = Signal()
    listening_stopped = Signal()
    error_occurred    = Signal(str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = True

        self.voice_enabled = True
        self.camera_enabled = True
        self.process_commands = True

        self.is_speaking = False
        self.mic_paused = False
        self._greeting_done = False
        self._greeting_time = 0  # ✅ Track when greeting finished

        # Vision
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
        )

        # Audio
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self._voice_lock = threading.Lock()
        self._voice_listening = False

        # Command processor
        self.cmd_processor = VoiceCommandProcessor()

    # ════════════════════════════════════════════════════════════════
    #  PUBLIC CONTROL
    # ════════════════════════════════════════════════════════════════

    def start_voice(self):
        """
        ✅ FIXED: NO duplicate, NO greeting
        """
        print("\n" + "🎤"*20)
        print("🎤 AI Engine: start_voice()")
        print("🎤"*20)

        # Pause mic (main.py will resume after greeting)
        self.mic_paused = True
        self.is_speaking = True
        print("  🔇 Mic PAUSED")

        # Enable voice listening
        with self._voice_lock:
            self._voice_listening = True
        print("  ✅ Voice listening enabled")

        # Emit signal ONCE (main.py handles greeting)
        print("  📡 Emitting listening_started signal...")
        self.listening_started.emit()
        print("  ✅ Signal emitted!")

        print("🎤"*20 + "\n")

    def stop_voice(self):
        """Stop audio capture."""
        with self._voice_lock:
            self._voice_listening = False
        self.mic_paused = True
        self.listening_stopped.emit()
        print("🔇 AI Engine: voice OFF")

    @property
    def is_voice_active(self):
        with self._voice_lock:
            return self._voice_listening

    def set_camera(self, state):
        self.camera_enabled = state

    def set_process_commands(self, state):
        self.process_commands = state

    # ════════════════════════════════════════════════════════════════
    #  ✅ FIXED: AUDIO WORKER WITH ECHO PROTECTION
    # ════════════════════════════════════════════════════════════════

    def _audio_worker(self):
        """
        Background daemon for continuous audio listening.
        ✅ FIXES: Mic pause check + Echo/greeting detection
        """
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Mic ready — ambient noise adjusted")
        except Exception as e:
            self.error_occurred.emit(f"Mic init failed: {e}")
            print(f"⚠️ Mic init error: {e}")
            return

        while self.is_running:
            # ═══════════════════════════════════════════════════════
            # CHECK 1: Is voice listening enabled?
            # ═══════════════════════════════════════════════════════
            with self._voice_lock:
                active = self._voice_listening

            if not active:
                time.sleep(0.3)
                continue

            # ═══════════════════════════════════════════════════════
            # CHECK 2: Is mic paused? (During greeting/speaking)
            # ═══════════════════════════════════════════════════════
            if self.mic_paused or self.is_speaking:
                time.sleep(0.1)
                continue

            try:
                with self.mic as source:
                    audio = self.recognizer.listen(
                        source, timeout=2, phrase_time_limit=5
                    )

                # ═══════════════════════════════════════════════════
                # CHECK 3: Double-check AFTER recognition
                # ═══════════════════════════════════════════════════
                if self.mic_paused or self.is_speaking:
                    print("  🔇 [IGNORED] Captured audio while speaking")
                    continue

                text = self.recognizer.recognize_google(audio).lower().strip()

                if len(text) < 2:
                    continue

                # ═══════════════════════════════════════════════════
                # ✅ CHECK 4: ECHO PROTECTION
                # Ignore if text sounds like greeting echo
                # ═══════════════════════════════════════════════════
                echo_words = [
                    "good morning", "good afternoon", "good evening",
                    "i'm nova", "im nova", "i'm nick", "im nick",
                    "how may i help", "how can i help", "help you"
                ]

                is_echo = any(word in text for word in echo_words)

                if is_echo and (time.time() - self._greeting_time) < 8:
                    print(f"  🔇 [ECHO BLOCKED] '{text}'")
                    continue

                print(f"🗣️ Heard: '{text}'")
                self.voice_command.emit(text)

                # Auto-process
                if self.process_commands:
                    # ═══════════════════════════════════════════════
                    # MUTE MIC WHILE PROCESSING
                    # ═══════════════════════════════════════════════
                    self.is_speaking = True

                    result = self.cmd_processor.process(text)
                    self.command_result.emit(result)

                    # Wait for TTS to finish
                    time.sleep(1.5)  # ✅ INCREASED from 0.3 to 1.5
                    self.is_speaking = False

                    if result.action == "STOP_LISTEN":
                        self.stop_voice()

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                self.error_occurred.emit(f"Speech API error: {e}")
                print(f"⚠️ Speech API: {e}")
                time.sleep(2)
            except Exception as e:
                self.error_occurred.emit(f"Audio error: {e}")
                print(f"⚠️ Audio: {e}")
                time.sleep(1)

    # ════════════════════════════════════════════════════════════════
    #  MAIN RUN LOOP
    # ════════════════════════════════════════════════════════════════

    def run(self):
        """Main loop — camera + audio in parallel."""
        if self.voice_enabled:
            audio_t = threading.Thread(
                target=self._audio_worker, daemon=True, name="AudioWorker"
            )
            audio_t.start()
            print("👂 Audio worker started")

        cap = None
        if self.camera_enabled:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                self.error_occurred.emit(f"Cannot open camera {self.camera_index}")

        while self.is_running:
            if cap and cap.isOpened() and self.camera_enabled:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.01)
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)

                if results.multi_hand_landmarks:
                    for hl in results.multi_hand_landmarks:
                        h, w, _ = frame.shape
                        lm_data = [
                            (i, int(lm.x * w), int(lm.y * h))
                            for i, lm in enumerate(hl.landmark)
                        ]
                        self.gesture_detected.emit(True, lm_data)
                else:
                    self.gesture_detected.emit(False, [])

                self.frame_ready.emit(frame)
            else:
                time.sleep(0.05)

            time.sleep(0.01)

        if cap:
            cap.release()
        self.hands.close()
        print("🛑 AI Engine stopped")

    # ════════════════════════════════════════════════════════════════
    #  STOP
    # ════════════════════════════════════════════════════════════════

    def stop(self):
        self.is_running = False
        self.stop_voice()
        self.wait(3000)
"""
╔══════════════════════════════════════════════════════════════╗
║                  AUREVIX CLAP DETECTOR                       ║
║         Double-clap → Activate Voice Input                   ║
║         Runs in background thread when toggle is ON          ║
╚══════════════════════════════════════════════════════════════╝
"""

import threading
import time
import numpy as np
from PySide6.QtCore import QObject, Signal

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠️ sounddevice not installed.")
    print("   Install: pip install sounddevice numpy")


class ClapDetector(QObject):
    """
    Detects double-clap pattern from microphone.

    Usage:
        detector = ClapDetector()
        detector.clap_detected.connect(your_function)
        detector.start()   # when toggle is turned ON
        detector.stop()    # when toggle is turned OFF

    Signal:
        clap_detected — emitted on valid double-clap
    """

    clap_detected = Signal()

    # ── Tuning ────────────────────────────────────────────────
    SAMPLE_RATE  = 44100
    CHUNK_SIZE   = 1024
    THRESHOLD    = 0.30   # lower = more sensitive
    MIN_GAP      = 0.08   # seconds min between two claps
    MAX_GAP      = 0.60   # seconds max between two claps
    COOLDOWN     = 2.0    # seconds to ignore after detection
    # ─────────────────────────────────────────────────────────

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running   = False
        self._thread    = None
        self._last_clap = 0.0
        self._last_emit = 0.0
        print("👏 ClapDetector: Initialized")

    # ── Public API ────────────────────────────────────────────

    def start(self):
        """Start listening for claps in background thread."""
        if not SOUNDDEVICE_AVAILABLE:
            print("❌ ClapDetector: sounddevice not installed")
            print("   Run: pip install sounddevice numpy")
            return False

        if self._running:
            print("⚠️ ClapDetector: Already running")
            return True

        self._running = True
        self._thread = threading.Thread(
            target  = self._listen_loop,
            daemon  = True,
            name    = "AurevixClapDetector"
        )
        self._thread.start()
        print("✅ ClapDetector: Started — 👏👏 to activate voice")
        return True

    def stop(self):
        """Stop clap detection."""
        self._running = False
        print("⏹ ClapDetector: Stopped")

    @property
    def is_running(self):
        return self._running

    # ── Internal ─────────────────────────────────────────────

    def _listen_loop(self):
        """
        Background thread:
        Reads mic in chunks → detects amplitude spike →
        checks timing → emits if double-clap pattern found.
        """
        print("👂 ClapDetector: Mic stream opening...")

        try:
            with sd.InputStream(
                samplerate = self.SAMPLE_RATE,
                channels   = 1,
                dtype      = 'float32',
                blocksize  = self.CHUNK_SIZE
            ) as stream:

                print("👂 ClapDetector: Mic active — listening")

                while self._running:
                    try:
                        data, _ = stream.read(self.CHUNK_SIZE)
                        amplitude = float(np.max(np.abs(data)))

                        if amplitude > self.THRESHOLD:
                            now = time.time()
                            gap = now - self._last_clap

                            if self.MIN_GAP < gap < self.MAX_GAP:
                                # Valid double-clap timing
                                if now - self._last_emit > self.COOLDOWN:
                                    print(
                                        f"\n👏 DOUBLE CLAP DETECTED!"
                                        f" (gap={gap:.2f}s, amp={amplitude:.2f})"
                                    )
                                    self._last_emit = now
                                    self.clap_detected.emit()

                            self._last_clap = now

                    except Exception as read_err:
                        print(f"⚠️ ClapDetector read error: {read_err}")
                        time.sleep(0.05)

        except Exception as e:
            print(f"❌ ClapDetector stream error: {e}")
            if "PortAudio" in str(e) or "No Default" in str(e):
                print("   → No microphone found or PortAudio missing")
                print("   → Install: pip install sounddevice")
        finally:
            self._running = False
            print("👂 ClapDetector: Mic stream closed")
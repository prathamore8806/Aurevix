# hand_tracking/core/ds_pipeline.py
"""
Data Structures Engine for Aurevix Hand Tracking:
1. CircularBuffer: O(1) Fixed-Size Ring Buffer for Landmark Smoothing & FPS stability.
2. GestureQueue: FIFO Thread-Safe Queue for decoupled gesture execution.
"""

import collections
import threading
import time
import numpy as np


# ══════════════════════════════════════════════════════════════
#  1. CIRCULAR BUFFER (Ring Buffer Data Structure)
# ══════════════════════════════════════════════════════════════
class CircularBuffer:
    """
    Fixed-capacity circular array for Landmark Coordinates & Velocity Smoothing.
    Time Complexity: Insert O(1), Access O(1), Memory: O(N) bounded.
    """
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.size = 0

    def append(self, item):
        """Insert element at head and advance circular pointer."""
        self.buffer[self.head] = item
        self.head = (self.head + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1

    def get_latest(self):
        """Fetch newest item."""
        if self.size == 0:
            return None
        latest_idx = (self.head - 1 + self.capacity) % self.capacity
        return self.buffer[latest_idx]

    def get_all(self):
        """Return all elements in chronological order (oldest to newest)."""
        if self.size == 0:
            return []
        if self.size < self.capacity:
            return self.buffer[:self.size]
        # Wrap around order
        return self.buffer[self.head:] + self.buffer[:self.head]

    def get_smoothed_point(self):
        """
        Calculate Moving Average for (x, y) coordinates.
        Jitter/Shaking hatane ke liye best algorithm.
        """
        valid_items = [p for p in self.get_all() if p is not None]
        if not valid_items:
            return None
        
        # Calculate mean across 2D/3D coordinate tuples
        arr = np.array(valid_items)
        avg_point = np.mean(arr, axis=0)
        return tuple(avg_point)

    def clear(self):
        self.buffer = [None] * self.capacity
        self.head = 0
        self.size = 0


# ══════════════════════════════════════════════════════════════
#  2. GESTURE QUEUE (FIFO Queue with Background Worker)
# ══════════════════════════════════════════════════════════════
class GestureQueue:
    """
    Thread-Safe FIFO Queue for processing gesture events asynchronously.
    Prevents UI thread freezing during high-frequency gesture detections.
    """
    def __init__(self, maxsize=50):
        self.queue = collections.deque(maxlen=maxsize)
        self.lock = threading.Lock()
        self.running = False
        self.worker_thread = None

    def enqueue(self, gesture_event):
        """Push a gesture event to the queue."""
        with self.lock:
            self.queue.append(gesture_event)

    def dequeue(self):
        """Pop the oldest gesture event."""
        with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None

    def is_empty(self):
        with self.lock:
            return len(self.queue) == 0

    def size(self):
        with self.lock:
            return len(self.queue)

    def start_dispatcher(self, handler_callback):
        """
        Starts worker daemon thread to process gestures continuously.
        handler_callback: function(event) jo action execute karegi
        """
        self.running = True
        
        def _worker():
            while self.running:
                event = self.dequeue()
                if event:
                    try:
                        handler_callback(event)
                    except Exception as e:
                        print(f"[GestureQueue Worker Error]: {e}")
                else:
                    time.sleep(0.005)  # 5ms sleep to prevent CPU spiking

        self.worker_thread = threading.Thread(target=_worker, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.running = False
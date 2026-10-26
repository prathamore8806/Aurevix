"""
Threaded Camera - FIXED: Proper shutdown sequence
"""

import cv2
import threading
import time
import numpy as np


class ThreadedCamera:
    """Separate thread for camera - ZERO LAG"""
    
    def __init__(self, camera_index=0):
        self.cap = None
        self.camera_index = camera_index
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        self._shutdown_event = threading.Event()  # ✅ NEW: Clean shutdown signal
        
    def start(self):
        """Start camera thread"""
        if self.running:
            return True
        
        # ✅ Clear shutdown event
        self._shutdown_event.clear()
        
        # Initialize camera
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        except:
            self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            print("❌ Camera failed to open")
            return False
        
        # Optimize camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        try:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        except:
            pass
        
        try:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        except:
            pass
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print("📷 Threaded camera started")
        return True
        
    def _capture_loop(self):
        """Continuous capture in background"""
        while self.running and not self._shutdown_event.is_set():
            # ✅ Check shutdown BEFORE accessing camera
            if self._shutdown_event.is_set():
                break
                
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue
            
            # ✅ Use try-except to handle mid-capture shutdown
            try:
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    with self.lock:
                        self.frame = frame
                        self.frame_count += 1
                    
                    # FPS calculation
                    now = time.time()
                    if now - self.last_fps_time >= 1.0:
                        self.fps = self.frame_count
                        self.frame_count = 0
                        self.last_fps_time = now
            except Exception as e:
                # ✅ Camera was closed mid-read - exit gracefully
                if self._shutdown_event.is_set():
                    break
                print(f"⚠️ Camera read error: {e}")
                time.sleep(0.1)
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.001)
        
        print("📷 Capture loop exited cleanly")
    
    def read(self):
        """Get latest frame"""
        with self.lock:
            if self.frame is not None:
                return True, self.frame.copy()
            return False, None
    
    def get_fps(self):
        return self.fps
    
    def stop(self):
        """Stop with proper cleanup - FIXED SEQUENCE"""
        if not self.running:
            return
            
        print("📷 Stopping camera...")
        
        # ✅ STEP 1: Signal thread to stop
        self.running = False
        self._shutdown_event.set()
        
        # ✅ STEP 2: Wait for thread to finish current read
        if self.thread is not None:
            self.thread.join(timeout=3.0)  # Increased timeout
            if self.thread.is_alive():
                print("⚠️ Camera thread did not stop cleanly")
            self.thread = None
        
        # ✅ STEP 3: Clear frame BEFORE releasing camera
        with self.lock:
            self.frame = None
        
        # ✅ STEP 4: Release camera resource
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                print(f"⚠️ Camera release error: {e}")
            self.cap = None
        
        # ✅ STEP 5: Small delay to ensure OS releases camera
        time.sleep(0.3)
        
        print("✅ Camera stopped cleanly")
    
    def isOpened(self):
        return self.cap is not None and self.cap.isOpened()
import cv2
import numpy as np
import threading
import time
import mode_manager

# Color palette for different object classes
CLASS_COLORS = {}


def get_color_for_class(class_id):
    """Generate a consistent color for each class ID."""
    if class_id not in CLASS_COLORS:
        np.random.seed(class_id * 17 + 42)
        CLASS_COLORS[class_id] = tuple(int(c) for c in np.random.randint(100, 255, 3))
    return CLASS_COLORS[class_id]


class ObjectDetector:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        # Detection settings
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        self.max_detections = 20
        self.target_classes = None  # None = all classes, or list of class indices
        self.model_path = "yolov8n.pt"  # nano model (fastest)

        # Performance
        self.detection_interval = 0.1  # seconds between detections (10 FPS)
        self.last_detection_time = 0
        self.inference_time_ms = 0

    def load_model(self, model_path=None):
        """Load YOLOv8 model. Downloads automatically if not present."""
        if model_path:
            self.model_path = model_path

        try:
            from ultralytics import YOLO
            print(f"🔍 Loading YOLO model: {self.model_path}")
            self.model = YOLO(self.model_path)
            self.model_loaded = True
            mode_manager.set_object_detection_model(self.model)
            print(f"✅ YOLO model loaded: {self.model_path}")
            print(f"   Classes: {len(self.model.names)} categories")
            return True
        except ImportError:
            print("❌ ultralytics not installed. Run: pip install ultralytics")
            return False
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False

    def detect(self, frame):
        """Run detection on a single frame. Returns annotated frame + results list."""
        if not self.model_loaded or frame is None:
            return frame, []

        start = time.time()

        # Run inference
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            max_det=self.max_detections,
            classes=self.target_classes,
            verbose=False
        )

        self.inference_time_ms = (time.time() - start) * 1000

        detected = []
        annotated = frame.copy()

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                # Extract data
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]

                detected.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2),
                    "class_id": cls_id
                })

                # Draw on frame
                color = get_color_for_class(cls_id)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

                # Label background
                text = f"{label} {conf:.0%}"
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 10, y1), color, -1)
                cv2.putText(
                    annotated, text, (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA
                )

        # Draw inference time
        cv2.putText(
            annotated,
            f"YOLO: {self.inference_time_ms:.0f}ms | {len(detected)} objects",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA
        )

        return annotated, detected

    def start_continuous(self):
        """Start continuous detection in background thread."""
        if self.running:
            return

        if not self.model_loaded:
            if not self.load_model():
                return

        self.running = True
        mode_manager.set_object_detection_enabled(True)
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        print("🔍 Object detection loop started")

    def _detection_loop(self):
        """Background loop that processes shared frames."""
        while self.running:
            now = time.time()
            if now - self.last_detection_time < self.detection_interval:
                time.sleep(0.01)
                continue

            frame = mode_manager.shared_frame
            if frame is None:
                time.sleep(0.05)
                continue

            _, detected = self.detect(frame)

            with self.lock:
                mode_manager.set_detected_objects(detected)

            self.last_detection_time = now

    def stop(self):
        """Stop continuous detection."""
        self.running = False
        mode_manager.set_object_detection_enabled(False)
        mode_manager.set_detected_objects([])
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        print("🔍 Object detection stopped")

    def get_class_names(self):
        """Return list of all class names."""
        if self.model_loaded:
            return list(self.model.names.values())
        return []

    def set_target_classes_by_name(self, names):
        """Filter detection to specific class names only."""
        if not self.model_loaded:
            return
        if names is None or len(names) == 0:
            self.target_classes = None
            return
        name_to_id = {v: k for k, v in self.model.names.items()}
        self.target_classes = [name_to_id[n] for n in names if n in name_to_id]
        print(f"🎯 Filtering to classes: {names}")


# Singleton instance
detector = ObjectDetector()

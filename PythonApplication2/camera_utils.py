# camera_utils.py - Helper to detect available cameras

import cv2


def detect_available_cameras(max_cameras=5):
    """
    Detect which camera indices are available.
    Returns a list of available camera indices.
    """
    available = []
    
    for i in range(max_cameras):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        except Exception as e:
            print(f"Error checking camera {i}: {e}")
            continue
    
    return available if available else [0]  # Default to camera 0


def get_camera_names():
    """Returns a dictionary of camera indices and their names."""
    return {
        0: "Integrated Webcam",
        1: "External Camera",
        2: "USB Camera",
        3: "Camera 3",
        4: "Camera 4"
    }


def get_available_cameras_with_names(max_cameras=5):
    """
    Detect available cameras and return with names.
    Returns: List of tuples [(index, "Camera X (Name)"), ...]
    """
    available_indices = detect_available_cameras(max_cameras)
    names = get_camera_names()
    
    result = []
    for idx in available_indices:
        name = names.get(idx, f"Camera {idx}")
        result.append((idx, f"Camera {idx} ({name})"))
    
    return result


def test_camera(index):
    """
    Test if a specific camera index works.
    Returns: True if camera works, False otherwise
    """
    try:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
    except:
        pass
    return False
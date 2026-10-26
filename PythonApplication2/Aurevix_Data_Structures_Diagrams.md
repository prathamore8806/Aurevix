# 📊 Aurevix — Core Data Structures Visual Blueprint

This document contains visual architectural diagrams, state flows, and structural mappings for the five primary data structures powering the **Aurevix** Multimodal Interaction Engine.

---

## 1. Circular Buffer (Ring Buffer) — $O(1)$ Moving Average

Used in [`hand_tracking/ds_pipeline.py`](file:///c:/Users/PRATHA%20MORE/source/repos/Aurevix/PythonApplication2/hand_tracking/ds_pipeline.py) for real-time landmark stabilization and mouse cursor jitter elimination.

```mermaid
flowchart TD
    subgraph Stream ["Live Landmark Stream (60 FPS)"]
        RAW["Raw Landmark Input: (x_t, y_t)"]
    end

    subgraph Ring ["Circular Buffer (Fixed Capacity N = 10)"]
        direction LR
        SLOT0["Index 0: (x_0, y_0)"]
        SLOT1["Index 1: (x_1, y_1)"]
        SLOT2["Index 2: (x_2, y_2)"]
        SLOT3["Index 3: (x_3, y_3)"]
        SLOT4["Index 4: (x_4, y_4)"]
        SLOT5["Index 5: (x_5, y_5)"]
        SLOT6["Index 6: (x_6, y_6)"]
        SLOT7["Index 7: (x_7, y_7)"]
        SLOT8["Index 8: (x_8, y_8)"]
        SLOT9["Index 9: (x_9, y_9)"]

        SLOT0 --> SLOT1 --> SLOT2 --> SLOT3 --> SLOT4
        SLOT4 --> SLOT5 --> SLOT6 --> SLOT7 --> SLOT8 --> SLOT9
        SLOT9 -.->|"Circular Wrap: (head + 1) % 10"| SLOT0
    end

    subgraph Pointer ["Head & State Management"]
        HEAD["Head Pointer (Points to next write position)"]
        SIZE["Size Counter (Bounded: 0 <= size <= 10)"]
    end

    subgraph Compute ["O(1) Moving Average Calculation"]
        SUM["Vector Mean: μ_x = Σ x_i / N,  μ_y = Σ y_i / N"]
        OUT["Smoothed Coordinate: (x_smooth, y_smooth)"]
    end

    RAW -->|"O(1) Overwrite at Head"| Ring
    HEAD -.-> Ring
    Ring --> SUM
    SUM --> OUT
    OUT -->|"Jitter-Free Signal"| CURSOR["OS Virtual Mouse Cursor"]
```

### Mathematical Formulation
Given a capacity $N=10$, each new measurement $p_t = (x_t, y_t)$ overwrites slot $h$:
$$\text{buffer}[h] \leftarrow p_t, \quad h \leftarrow (h + 1) \pmod N$$
The filtered coordinate $\bar{p}_t$ is computed via vector mean:
$$\bar{p}_t = \frac{1}{|S|} \sum_{i \in S} \text{buffer}[i], \quad S = \{i \mid \text{buffer}[i] \neq \text{None}\}$$

---

## 2. Thread-Safe FIFO Gesture Queue (Producer-Consumer)

Used in [`hand_tracking/ds_pipeline.py`](file:///c:/Users/PRATHA%20MORE/source/repos/Aurevix/PythonApplication2/hand_tracking/ds_pipeline.py) $\rightarrow$ `GestureQueue` to decouple video processing from OS action execution.

```mermaid
flowchart LR
    subgraph Producer ["Producer: Vision Thread (60 FPS)"]
        CAM["Webcam Capture"] --> MP["MediaPipe Hands"]
        MP --> GEST["Gesture Classifier (Pinch / Fist / Swipe)"]
    end

    subgraph CriticalSection ["Critical Section (Mutex Guard)"]
        LOCK["threading.Lock()"]
        
        subgraph Queue ["FIFO Double-Ended Queue (collections.deque, maxlen=50)"]
            Q_TAIL["[Tail / Input]"]
            E3["Event 3: CLICK_DOWN"]
            E2["Event 2: SCROLL_UP"]
            E1["Event 1: KEY_PRESS_W"]
            Q_HEAD["[Head / Output]"]
            
            Q_TAIL --> E3 --> E2 --> E1 --> Q_HEAD
        end
    end

    subgraph Consumer ["Consumer: Dispatcher Daemon Thread"]
        WORKER["Worker Thread (_worker loop)"]
    end

    subgraph Execution ["OS Action Execution (Zero UI Lag)"]
        ACT1["pyautogui.click()"]
        ACT2["win32api.keybd_event()"]
        ACT3["AudioManager.play_sfx()"]
    end

    GEST -->|"enqueue(event) [O(1)]"| Q_TAIL
    Q_HEAD -->|"dequeue() [O(1) popleft]"| WORKER
    LOCK -.->|"Acquire / Release"| Queue
    WORKER --> ACT1
    WORKER --> ACT2
    WORKER --> ACT3
```

---

## 3. Kalman Filter 2D — State Estimation & Prediction

Used in [`hand_tracking/core/filters.py`](file:///c:/Users/PRATHA%20MORE/source/repos/Aurevix/PythonApplication2/hand_tracking/core/filters.py) $\rightarrow$ `KalmanFilter2D` for predicting cursor coordinates and preventing drift.

```mermaid
flowchart TD
    subgraph StateVector ["State Representation"]
        STATE["State Vector: x = [ x,  y,  dx/dt,  dy/dt ]^T (Position + Velocity)"]
        COV["Covariance Matrix: P (4x4 Uncertainty Matrix)"]
    end

    subgraph PredictStep ["Step 1: Time Update (Prediction)"]
        F_MAT["State Transition: F (4x4)"]
        PRED_X["Project State: x_hat^- = F * x_prev"]
        PRED_P["Project Error Covariance: P^- = F * P * F^T + Q"]
    end

    subgraph MeasureStep ["Step 2: Measurement & Gain"]
        Z_VAL["Sensor Measurement: z = [ z_x,  z_y ]^T (From Camera)"]
        INNOV["Innovation: y = z - H * x_hat^-"]
        S_MAT["Innovation Covariance: S = H * P^- * H^T + R"]
        K_GAIN["Kalman Gain: K = P^- * H^T * S^(-1)"]
    end

    subgraph CorrectStep ["Step 3: Measurement Update (Correction)"]
        UPD_X["Update State: x_hat = x_hat^- + K * y"]
        UPD_P["Update Covariance: P = (I - K * H) * P^-"]
        DRIFT["Drift Check: if frame % 300 == 0: clip(P)"]
    end

    STATE --> PredictStep
    PredictStep --> MeasureStep
    Z_VAL --> MeasureStep
    MeasureStep --> CorrectStep
    CorrectStep -->|"Feedback Loop (Next Frame)"| STATE
    UPD_X -->|"Predicted Smooth Pos"| CURSOR_POS["Screen Coordinate: (x, y)"]
```

---

## 4. Spatial Landmark Tensors — 3D $(21, 3)$ Hand Graph

Used in [`hand_tracking/core/camera.py`](file:///c:/Users/PRATHA%20MORE/source/repos/Aurevix/PythonApplication2/hand_tracking/core/camera.py) and MediaPipe Hands to capture the geometric anatomy of the human hand.

```mermaid
graph TD
    WRIST["0: Wrist [x0, y0, z0]"]

    subgraph Thumb ["Thumb Joint Chain"]
        T1["1: Thumb CMC"] --> T2["2: Thumb MCP"] --> T3["3: Thumb IP"] --> T4["4: Thumb Tip [x4, y4, z4]"]
    end

    subgraph IndexFinger ["Index Finger Joint Chain"]
        I1["5: Index MCP"] --> I2["6: Index PIP"] --> I3["7: Index DIP"] --> I4["8: Index Tip [x8, y8, z8]"]
    end

    subgraph MiddleFinger ["Middle Finger Joint Chain"]
        M1["9: Middle MCP"] --> M2["10: Middle PIP"] --> M3["11: Middle DIP"] --> M4["12: Middle Tip [x12, y12, z12]"]
    end

    subgraph RingFinger ["Ring Finger Joint Chain"]
        R1["13: Ring MCP"] --> R2["14: Ring PIP"] --> R3["15: Ring DIP"] --> R4["16: Ring Tip [x16, y16, z16]"]
    end

    subgraph PinkyFinger ["Pinky Finger Joint Chain"]
        P1["17: Pinky MCP"] --> P2["18: Pinky PIP"] --> P3["19: Pinky DIP"] --> P4["20: Pinky Tip [x20, y20, z20]"]
    end

    WRIST --> T1
    WRIST --> I1
    WRIST --> M1
    WRIST --> R1
    WRIST --> P1

    subgraph TensorRepresentation ["Landmark Matrix Tensor (21 x 3)"]
        MAT["L = [ [x0, y0, z0],
       [x1, y1, z1],
       ...
       [x20, y20, z20] ]"]
    end

    I4 -.->|"Euclidean Distance: d = ||P8 - P4|| < Threshold"| PINCH["Pinch Action (Left Click Trigger)"]
    T4 -.-> PINCH
```

---

## 5. Hash Tables & Dataclasses — $O(1)$ Dispatch Maps

Used across the application for instantaneous action lookup, key-binding resolution, and structured state holding.

```mermaid
classDiagram
    class GamePreset {
        +str name
        +str description
        +dict bindings
        +get_key(gesture_name) str
    }

    class CalibrationData {
        +float margin_x_min
        +float margin_x_max
        +float margin_y_min
        +float margin_y_max
        +bool hologram_mode
        +to_dict() dict
        +from_dict(data) CalibrationData
    }

    class CalibrationProfile {
        +str name
        +str mode
        +CalibrationData calibration
        +display_name() str
    }

    class Notification {
        +str id
        +str title
        +str message
        +str level
        +float timestamp
        +bool is_read
    }

    class VoiceDispatchMap {
        <<Hash Table O(1)>>
        +key: "open browser" -> callback()
        +key: "mute volume" -> callback()
        +key: "gaming mode" -> callback()
        +key: "calibrate" -> callback()
    }

    class GestureActionMap {
        <<Hash Table O(1)>>
        +key: "PINCH" -> mouse_down()
        +key: "OPEN_PALM" -> mouse_up()
        +key: "SWIPE_RIGHT" -> next_slide()
        +key: "V_SIGN" -> laser_pointer()
    }

    CalibrationProfile *-- CalibrationData
    GamePreset --> GestureActionMap : "resolves keycodes"
```

---

## Summary Matrix

| Data Structure | Primary File | Access Complexity | Insert Complexity | Primary Purpose in Aurevix |
| :--- | :--- | :--- | :--- | :--- |
| **CircularBuffer** | `ds_pipeline.py` | $O(1)$ | $O(1)$ | 60 FPS coordinate window for moving average filter |
| **GestureQueue** | `ds_pipeline.py` | $O(1)$ | $O(1)$ | Thread-safe FIFO queue decoupling camera and OS actions |
| **KalmanFilter2D** | `filters.py` | $O(1)$ | $O(1)$ | 4D state vector & covariance matrix trajectory prediction |
| **Spatial Landmark Tensor** | `camera.py` | $O(1)$ | $O(1)$ | $21 \times 3$ coordinate matrix for hand skeleton geometry |
| **Hash Tables (`dict`)** | `gaming_gesture_controller.py`, `voice_command_processor.py` | $O(1)$ | $O(1)$ | Instant lookup for voice commands, game keys, and gesture types |
| **Dataclasses** | `calibration_profiles.py`, `notification_manager.py` | $O(1)$ | $O(1)$ | Strongly-typed, validated data representations |

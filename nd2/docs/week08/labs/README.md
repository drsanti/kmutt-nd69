# Week 08 Labs: Building Voice-Enabled Web Services with `robotos_kws`

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

In this lab, you learn how to bridge Edge AI models into modern web and backend applications. You will use the **`robotos_kws` Python SDK** to classify audio streams, build a FastAPI REST microservice, create a real-time WebSocket speech broadcaster, and build a reactive web dashboard.

---

## Table of Contents

- [1. Environment Setup](#1-environment-setup)
- [2. Lab 2.1: Python SDK Fundamentals & Audio Classification](#2-lab-21-python-sdk-fundamentals--audio-classification)
- [3. Lab 2.2: Building an Audio Inference Microservice (FastAPI)](#3-lab-22-building-an-audio-inference-microservice-fastapi)
- [4. Lab 2.3: Real-Time Event Streaming over WebSockets](#4-lab-23-real-time-event-streaming-over-websockets)
- [5. Lab 2.4: Full-Stack Voice-Reactive Dashboard](#5-lab-24-full-stack-voice-reactive-dashboard)
- [6. Lab 2.5: Automated MLOps Retraining Pipeline](#6-lab-25-automated-mlops-retraining-pipeline)

---

## 1. Environment Setup

### 1.1 Virtual Environment

```bash
cd nd2/docs/week08/labs/web-app
```

- **Windows (Git Bash):**
  ```bash
  py -3.11 -m venv .venv      # or: python -m venv .venv
  source .venv/Scripts/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  py -3.11 -m venv .venv      # or: python -m venv .venv
  # If script execution is disabled: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt cmd.exe):**
  ```cmd
  py -3.11 -m venv .venv      # or: python -m venv .venv
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

*(When activated, your terminal prompt will show `(.venv)`).*

> [!TIP]
> **Prefer typing `py` instead of `python` on Windows?**  
> Virtual environments create `python.exe` by default. If you prefer typing `py` in Git Bash or PowerShell, copy it once:
> - **Git Bash:** `cp .venv/Scripts/python.exe .venv/Scripts/py.exe`
> - **PowerShell:** `Copy-Item .\.venv\Scripts\python.exe .\.venv\Scripts\py.exe`
> - **CMD:** `copy .venv\Scripts\python.exe .venv\Scripts\py.exe`  
> Now both `python` and `py` will work interchangeably in your terminal!

> [!TIP]
> **Already set up ND1? Reuse your existing `.venv`!**
> If you already configured the virtual environment in `nd1`, you do not need to download or install TensorFlow again (~1.5 GB). You can simply activate the existing ND1 environment:
> - **Git Bash:** `source ../../../nd1/docs/week08/labs/python/.venv/Scripts/activate`
> - **PowerShell:** `..\..\..\nd1\docs\week08\labs\python\.venv\Scripts\Activate.ps1`
> - **CMD:** `..\..\..\nd1\docs\week08\labs\python\.venv\Scripts\activate.bat`
> - **Linux / macOS:** `source ../../../nd1/docs/week08/labs/python/.venv/bin/activate`

### 1.2 Install Requirements & `robotos_kws` Wheel

```bash
pip install -r requirements.txt
pip install ../dist/robotos_kws-0.1.0-py3-none-any.whl
```

> [!TIP]
> **Universal Fallback:** If `pip` says `command not found`, use `python -m pip install -r requirements.txt` and `python -m pip install ../dist/robotos_kws-0.1.0-py3-none-any.whl`.

Verify that the SDK imports cleanly:
```bash
python -c "import robotos_kws as rk; print('robotos_kws version:', rk.__version__)"
```

> [!NOTE]
> **Windows Note (`python` vs `py`):**  
> On Windows, `py` is the global system launcher and will run the global Python rather than your virtual environment. Once your `.venv` is activated (your prompt shows `(.venv)`), always run **`python`**, which points directly to `.venv/Scripts/python.exe`. (Alternatively, run `./.venv/Scripts/python -c ...`).

---

## 2. Lab 2.1: Python SDK Fundamentals & Audio Classification

In this exercise, you interact with the core `robotos_kws.Detector` abstraction.

Inspect and run [examples/03_classify_audio_file.py](examples/03_classify_audio_file.py):

```python
import robotos_kws as rk

# Load int8 quantized model
detector = rk.Detector("artifacts/model_int8.tflite", threshold=0.80)

# 1. Top predicted label and confidence score
top_label, confidence = detector.predict("test.wav")
print(f"Top class: {top_label} ({confidence:.1%})")

# 2. Complete softmax probability distribution
probs = detector.predict_proba("test.wav")
for label, p in probs.items():
    print(f"  {label:<10}: {p:.1%}")
```

Run the example with the included test audio clip (or any `.wav` file):
```bash
python examples/03_classify_audio_file.py sample_audio.wav
# Or with py:
py examples/03_classify_audio_file.py sample_audio.wav
```

---

## 3. Lab 2.2: Building an Audio Inference Microservice (FastAPI)

In this exercise, you wrap the model inside a high-performance REST API.

Run the provided FastAPI server:
```bash
python app.py
# Or with py:
py app.py
```

The server starts at `http://127.0.0.1:8000`.

### Endpoints Available:
- `GET /api/v1/model/info`: Returns active model metadata, labels, and input parameters.
- `GET /api/v1/sample-audio`: Downloads the included `sample_audio.wav` test clip.
- `POST /api/v1/classify`: Accepts a multipart form upload containing a `.wav` file and returns structured JSON predictions:
  ```json
  {
    "top_class": "blue",
    "confidence": 0.942,
    "probabilities": {
      "red": 0.012,
      "green": 0.021,
      "blue": 0.942,
      "off": 0.015,
      "_silence_": 0.005,
      "_unknown_": 0.005
    }
  }
  ```

### How to Test the Classification Endpoint:
You do **not** need to manually record audio for this track. You can test it in multiple ways:
1. **Via Web Dashboard (Easiest)**: Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) and click **"📁 Use Built-in Sample"** or **"🎙️ Record Mic (1s)"**.
2. **Via Swagger Docs**: Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), expand `POST /api/v1/classify`, click *Try it out*, and upload `sample_audio.wav`.
3. **Via cURL (Terminal)**:
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/v1/classify" -F "file=@sample_audio.wav"
   ```

---

## 4. Lab 2.3: Real-Time Event Streaming over WebSockets

HTTP polling is inefficient for continuous speech detection. In this exercise, we use WebSockets to push live detection events to connected web clients with sub-50 ms latency.

In `app.py`, a background thread consumes the generator:
```python
for keyword, confidence, timestamp in detector.stream_pc():
    payload = {
        "event": "keyword_detected",
        "keyword": keyword,
        "confidence": confidence,
        "timestamp": round(timestamp, 2)
    }
    await broadcast_websocket(payload)
```

Clients connect to `ws://localhost:8000/ws/kws` and immediately receive real-time detection notifications.

---

## 5. Lab 2.4: Full-Stack Voice-Reactive Dashboard (VS Code Theme)

Open `http://localhost:8000` (or `http://127.0.0.1:8000`) in your browser.

The dashboard uses a modern **VS Code-style split-panel industrial layout**:

1. **Activity Bar & Primary Sidebar (Left)**:
   - **Model Profile**: Architecture specs (`DS-CNN int8`), active vocab labels, threshold settings.
   - **Inference Actions**: One-click **"📁 Use Built-in Sample"**, **"🎙️ Record Mic (1s)"**, or custom file upload.
2. **Main SCADA Stage (Center)**:
   - **Industrial HUD State Monitor**: Large glowing status indicator reacting with hazard stripes on `"red"` (E-STOP), emerald glow on `"green"` (DRIVE), sky glow on `"blue"` (NAV), and amber glow on `"off"` (STANDBY).
   - **Safety Interlock Matrix**: Status cards defining the 4-state deterministic robot FSM.
   - **Live Audio Activity Indicator**: Shows continuous 16 kHz PCM server stream status.
3. **Softmax Distribution Meters (Right)**:
   - High-precision segmented probability bars and percentage readouts across all classes.
4. **Bottom Terminal / Output Panel**:
   - Tabbed output console (`WEBSOCKET TELEMETRY`, `REST INSPECTOR`, `MODEL META`) streaming real-time timestamped event logs with color-coded tags.
5. **VS Code Status Bar (Bottom)**:
   - Displays git branch, live WebSocket link, DSP frame specs, and runtime telemetry.

---

## 6. Lab 2.5: Automated MLOps Retraining Pipeline

In production applications, new data collected from users is used to retrain models.

Inspect `examples/04_programmatic_train.py`:
```python
import robotos_kws as rk

# Instantiate trainer
trainer = rk.Trainer(data_dir="dataset", out_dir="artifacts")

# Programmatically train and quantize int8 model
meta = trainer.train(epochs=40, augment=4)
print("New model trained with labels:", meta["labels"])

# Hot-reload into the running web server
app.state.detector = rk.Detector("artifacts/model_int8.tflite")
```

> [!NOTE]
> `rk.Trainer` automatically discovers audio datasets in the workspace (including ND1's collected dataset). If running standalone without prior recordings, it automatically generates a synthetic multi-speaker audio dataset so that training, int8 quantization, and evaluation report generation (`artifacts/report.md`) always run cleanly out-of-the-box!

Run the retraining script:
```bash
python examples/04_programmatic_train.py
# Or with py:
py examples/04_programmatic_train.py
```
Observe how the entire training, quantization, and evaluation report generation runs without shell commands.

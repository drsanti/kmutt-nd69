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
py -3.11 -m venv .venv           # Windows
.\.venv\Scripts\Activate.ps1
```
*(On Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate`)*

### 1.2 Install Requirements & `robotos_kws` Wheel

```bash
pip install -r requirements.txt
pip install ../dist/robotos_kws-0.1.0-py3-none-any.whl
```

Verify that the SDK imports cleanly:
```bash
python -c "import robotos_kws as rk; print('robotos_kws version:', rk.__version__)"
```

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

Run the example with a test audio clip:
```bash
python examples/03_classify_audio_file.py ../../../nd1/docs/week08/labs/python/dataset/blue/s01_me_pc_0000.wav
```

---

## 3. Lab 2.2: Building an Audio Inference Microservice (FastAPI)

In this exercise, you wrap the model inside a high-performance REST API.

Run the provided FastAPI server:
```bash
python app.py
```

The server starts at `http://127.0.0.1:8000`.

### Endpoints Available:
- `GET /api/v1/model/info`: Returns active model metadata, labels, and input parameters.
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

Test the API via Swagger documentation:
- Open your browser to `http://127.0.0.1:8000/docs`.
- Try out the `/api/v1/classify` endpoint by uploading an audio clip.

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

## 5. Lab 2.4: Full-Stack Voice-Reactive Dashboard

Open `http://localhost:8000` in your browser.

The single-page web dashboard provides:
1. **Live Audio Status Indicator**: Shows whether the server's microphone stream is actively listening.
2. **Real-Time Probability Bars**: Visually renders the confidence distribution across all recognized keywords.
3. **Reactive UI State Machine**:
   - Speak `"red"` $\to$ UI triggers **Emergency Stop** modal with high-visibility red alert.
   - Speak `"green"` $\to$ UI enters **Active / Running** state.
   - Speak `"blue"` $\to$ UI switches to **Manual Navigation / Steering** mode.
   - Speak `"off"` $\to$ UI enters **Standby / Sleep** mode.

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

Run the retraining script:
```bash
python examples/04_programmatic_train.py
```
Observe how the entire training, quantization, and evaluation report generation runs without shell commands.

# RobotOS Voice Controller — Web Application (ND02)

![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![framework](https://img.shields.io/badge/framework-FastAPI-009688?style=flat-square)
![ui](https://img.shields.io/badge/ui-Figma--Like%20Design%20System-0d99ff?style=flat-square)
![python](https://img.shields.io/badge/python-3.11-3776ab?style=flat-square)

The **RobotOS Voice Controller Web App** bridges the quantized DS-CNN keyword spotting (KWS) model into a full-stack, real-time application. It provides high-performance REST inference endpoints, an asynchronous WebSocket speech streaming service, and an interactive **Figma-inspired visual editor desktop interface**.

---

## 1. Quick Start

### 1.1 Activate Environment & Install Dependencies

From this directory (`nd2/docs/week08/labs/web-app`):

- **Windows (PowerShell):**
  ```powershell
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  pip install ../dist/robotos_kws-0.1.2-py3-none-any.whl
  ```
- **macOS / Linux:**
  ```bash
  python3.11 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install ../dist/robotos_kws-0.1.2-py3-none-any.whl
  ```

### 1.2 Start the Development Server

```bash
python app.py
```

Open your browser at:
- **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 2. UI Architecture (Figma-Like Design System)

The frontend is built according to the **`figma-like-ui-designer`** specification, utilizing a modern desktop visual editor aesthetic:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TopBar (44px): Breadcrumb [RobotOS / Voice Controller] | Thresh | WS  │
├──────────────┬──────────────────────────────────────────┬──────────────┤
│ Left Panel   │ Center Canvas Viewport                   │ Right Panel  │
│ (270px)      │ • Floating Toolbar (PTT, Continuous, VU) │ (310px)      │
│ • Layers     │ • Real-Time Oscilloscope (60 FPS FFT)    │ • Model Info │
│ • Assets     │ • Artboard Frame: # Robot FSM (880×360)  │ • Threshold  │
│ • DSP Specs  │   - Active State Banner (E-Stop/Run/...) │ • Softmax    │
│              │   - Component Variant Simulation Cards   │ • REST JSON  │
├──────────────┴──────────────────────────────────────────┴──────────────┤
│ Bottom Drawer (44px/expanded): Telemetry Stream Log & Console Tabs     │
├────────────────────────────────────────────────────────────────────────┤
│ StatusBar (26px): Git Branch | 16kHz PCM | DS-CNN int8 | KMUTT ND69    │
└────────────────────────────────────────────────────────────────────────┘
```

### Key UI Features:
1. **Push-to-Talk (PTT)**:
   - Click and hold `[ HOLD TO TALK ]` or hold the **Spacebar** anywhere on the page to downsample your browser microphone to 16 kHz PCM16 and stream to the server.
2. **Continuous Speech Mode**:
   - Toggle `[ Continuous: LIVE ]` for hands-free audio streaming and live inference.
3. **Real-Time Oscilloscope**:
   - Web Audio API `AnalyserNode` rendering live 48-bin frequency spectrum bars and a time-domain waveform line.
4. **Interactive FSM Simulator**:
   - Click `⚡ Test "red"`, `⚡ Test "green"`, `⚡ Test "blue"`, or `⚡ Test "off"` to trigger deterministic state transitions without a microphone.
5. **Dynamic Sensitivity Controller**:
   - Adjust the confidence threshold slider or click presets (`10%`, `50%`, `80%`, `95%`) to update the vertical threshold marker across the live softmax distribution meters.

---

## 3. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the single-page Figma-style dashboard (`static/index.html`). |
| `GET` | `/api/v1/model/info` | Returns active model metadata, vocabulary classes, and input parameters. |
| `POST` | `/api/v1/model/threshold` | Updates confidence threshold dynamically (`{"threshold": 0.85}`). |
| `POST` | `/api/v1/classify` | Accepts `.wav` multipart upload; returns top class and softmax distribution. |
| `POST` | `/api/v1/simulate` | Simulates keyword trigger for testing (`{"keyword": "red", "confidence": 0.98}`). |
| `GET` | `/api/v1/sample-audio` | Serves `sample_audio.wav` for quick client benchmarking. |
| `WS` | `/ws/kws` | Full-duplex WebSocket stream receiving PCM16 audio and broadcasting detections. |

---

## 4. File Layout

```
web-app/
├── app.py                     # FastAPI backend application & WebSocket broadcaster
├── sample_audio.wav           # Reference 16 kHz mono test clip
├── requirements.txt           # Python package dependencies
├── artifacts/
│   └── model_int8.tflite      # Quantized DS-CNN model weights (18.8 KiB)
├── examples/
│   ├── 03_classify_audio_file.py    # Python SDK batch inference example
│   └── 04_programmatic_train.py     # Automated MLOps retraining script
└── static/
    ├── index.html             # Figma-style AppShell & Artboard markup
    ├── styles.css             # Figma design system tokens & styles
    └── app.js                 # Web Audio API & telemetry controller
```

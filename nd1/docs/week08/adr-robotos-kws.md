# ADR-0030: robotos_kws Unified CLI and SDK for Edge AI Keyword Spotting

Status: accepted

## Context

In Week 08 of the curriculum (Edge AI on Microcontrollers), students learn the end-to-end pipeline of audio data collection, spectrogram feature extraction, deep neural network training (DS-CNN), int8 post-training quantization, and microcontroller deployment (ESP32-S3).

Previously, this workflow relied on seven loose Python scripts in `nd1/docs/week08/labs/python/`:
- `collect_pc_mic.py` & `collect.py` (data collection)
- `make_synthetic_dataset.py` (test clip generator)
- `train.py` (Keras DS-CNN training + int8 TFLite export)
- `evaluate.py` (model benchmark + confusion matrix generation)
- `live_infer_pc.py` & `live_infer_board.py` (sliding-window real-time inference)
- `verify_c_features.py` & `export_c_array.py` (ESP-IDF C headers generator)

Distributing raw Python source code creates two challenges:
1. **Intellectual Property & Academic Protection:** Course authors wish to close-source the underlying algorithms (DSP filter chain, log-mel FFT pipeline, serial framing, model quantization) while keeping the tool accessible.
2. **Pedagogical Integration:** Students need a command-line interface (CLI) for fast data collection and training, but also require a programmable Python SDK (`import robotos_kws`) so they can build voice-controlled robots, state machines, and event-driven robotics applications.
3. **Cross-Platform Support:** Students use both Windows and macOS (Intel and Apple Silicon).

## Decision

We establish **`robotos_kws`**: a unified Python package and command-line suite that consolidates all keyword spotting capabilities into a closed-source binary wheel (`.whl`) and executable tool.

### 1. Unified Subcommand CLI (`robotos-kws` and `robotos_kws`)

The CLI provides subcommands for every stage of the Edge AI lifecycle:

| Subcommand | Legacy Script | Role |
| :--- | :--- | :--- |
| `devices` | `collect_pc_mic.py --list-devices` | List available audio input devices |
| `check-board` | `collect.py --info` | Verify ESP32-S3 wire connection and live dBFS meter |
| `collect-pc` | `collect_pc_mic.py` | Record keyword clips with PC mic or slice WAV |
| `collect-board` | `collect.py` | Record keyword clips streamed from board MEMS mic |
| `synth-data` | `make_synthetic_dataset.py` | Generate synthetic audio dataset for testing |
| `train` | `train.py` | Train DS-CNN, quantize to int8, export metadata |
| `evaluate` | `evaluate.py` | Benchmark accuracy, generate confusion matrix & report |
| `live-pc` | `live_infer_pc.py` | Real-time keyword spotting from PC mic or test WAV |
| `live-board` | `live_infer_board.py` | Real-time keyword spotting streamed from board |
| `export` | `export_c_array.py` | Generate `model_data.cc` and `kws_labels.h` for ESP-IDF |
| `verify-c` | `verify_c_features.py` | Cross-validate C feature extraction vs Python |

### 2. Python SDK (`import robotos_kws`)

The SDK exposes clean, high-level abstractions:
- **`Detector`**: Loads float32 or int8 TFLite models. Exposes `.predict()`, `.predict_proba()`, `.stream_pc()`, and `.stream_board()` generators for voice-command loops in robot controllers.
- **`Board`**: Wraps the serial wire protocol session over USB/UART with context-manager semantics (`with Board("COM5") as b:`), level measurement, and recording.
- **`AudioRecorder`**: Records calibrated 16 kHz mono 16-bit PCM clips from computer microphones.
- **`Trainer`**: Exposes programmatic training and evaluation for notebook and scripting workflows.

### 3. Closed-Source Packaging Strategy

1. **Compilation to Native C-Extensions (`.pyd` / `.so`):**
   Internal modules (`features`, `wire`, `trainer`, `dsp`) are compiled via Cython or Mypyc into native shared libraries.
2. **Distribution via Precompiled Wheels (`.whl`):**
   Compiled wheels are built for target platforms:
   - `robotos_kws-*-cp311-win_amd64.whl` (Windows x64)
   - `robotos_kws-*-cp311-macosx_*_arm64.whl` (macOS Apple Silicon)
   - `robotos_kws-*-cp311-macosx_*_x86_64.whl` (macOS Intel)
3. **Automated Cross-Platform Builds:**
   GitHub Actions CI builds and signs the platform wheels on native macOS and Windows runners using `cibuildwheel`.

### 4. Continuous Synchronization & Student Deployment Rule

Whenever `robotos/sdk/python-kws` is updated:
1. **Compilation & Build**: Both the library code and student examples are byte-compiled, verified for syntax, and packaged into a precompiled `.whl` wheel.
2. **Synchronization**: The compiled wheel and the student example scripts (`examples/`) are deployed directly to the student repository (`kmutt-nd69/nd1/docs/week08/labs/dist/` and `kmutt-nd69/nd1/docs/week08/labs/python/examples/`).
3. **Leak Audit**: The student folder is audited to ensure zero raw source code files (`robotos_kws/`, `collect.py`, `train.py`, `wire.py`, etc.) exist in the student repository.
4. **Automated Script**: This is executed via `publish_to_students.py`.

## Consequences

### Positive
- **Single Tool UX:** Students learn one command (`robotos-kws`) instead of managing 7 independent Python scripts.
- **Protected Algorithms:** Core feature extraction and model quantization implementations cannot be inspected or modified by students.
- **Robotics Enablement:** Students can script voice-driven actions in their RobotOS Python nodes with `from robotos_kws import Detector`.
- **Consistency:** Input validation, automatic retries for quiet (< −40 dBFS) or clipped audio, and standardized metadata formatting are enforced across all interfaces.

### Negative / Trade-offs
- macOS builds must be compiled on macOS runners (addressed via GitHub Actions).
- Precompiled wheels require binary builds matching supported Python minor versions (target: Python 3.10–3.13).

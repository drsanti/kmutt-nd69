# Week 08 Labs: Embedded Edge AI with `robotos-kws`

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

**Focus for Group 1 (ND1 — Embedded Systems & IoT):**
In this lab, you complete the end-to-end Edge AI development lifecycle using the production **`robotos-kws` CLI**. You will use your computer's microphone (no hardware board required for the core pipeline), collect clean multi-class datasets, train and quantize an int8 neural network, benchmark quantization loss, test real-time sliding-window detection, and export MCU-ready C arrays (`model_data.cc`) and headers for ESP32-S3 firmware.

---

## Table of Contents

- [1. Environment Setup & CLI Installation](#1-environment-setup--cli-installation)
  - [1.5 Optional: Flash Workshop Firmware to ESP32-S3 Board](#15-optional-flash-workshop-firmware-to-esp32-s3-board)
- [2. Lab 1.1: Audio Sensing & Device Calibration](#2-lab-11-audio-sensing--device-calibration)
- [3. Lab 1.2: Rigorous Multi-Class Audio Collection](#3-lab-12-rigorous-multi-class-audio-collection)
- [4. Lab 1.3: Deep Learning Training & Int8 Quantization](#4-lab-13-deep-learning-training--int8-quantization)
- [5. Lab 1.4: Model Evaluation & Confusion Matrix](#5-lab-14-model-evaluation--confusion-matrix)
- [6. Lab 1.5: Real-Time Live Inference via PC Microphone](#6-lab-15-real-time-live-inference-via-pc-microphone)
- [7. Lab 1.6: Embedded C Firmware Export & DSP Verification](#7-lab-16-embedded-c-firmware-export--dsp-verification)
- [Troubleshooting](#troubleshooting)

---

## 1. Environment Setup & CLI Installation

> [!TIP]
> ✈️ **Before you begin:** Test your developer literacy with the **[Pre-Flight Readiness Quiz](../preflight.md)** (10 self-check questions on Python versions, terminal paths, and permissions).

### 1.1 Open Terminal & Navigate to Directory

```bash
cd nd1/docs/week08/labs/python
```

### 1.2 Create & Activate Virtual Environment

> [!IMPORTANT]
> **Python Version Requirement (Python 3.10 – 3.13; Python 3.11 recommended):**  
> TensorFlow does **not** yet have wheels for Python 3.14+ on Windows or macOS.  
> - **Windows:** If Python 3.11 is not installed, install it in PowerShell: `winget install Python.Python.3.11`
> - **macOS:** If `python3 --version` shows 3.14+, install Python 3.11 via Homebrew: `brew install python@3.11`
> - **Already created `.venv` with the wrong Python (e.g. 3.14)? Delete and recreate it:**
>   - macOS/Linux: `deactivate && rm -rf .venv && python3.11 -m venv .venv && source .venv/bin/activate`
>   - Windows (PowerShell): `deactivate; Remove-Item -Recurse -Force .venv; py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1`
>   - Verify with: `python --version` (must output `Python 3.11.x`!)

Choose the section matching your shell:

- **Windows (Git Bash):**
  ```bash
  py -3.11 -m venv .venv      # or: python -m venv .venv
  source .venv/Scripts/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  py -3.11 -m venv .venv      # or: python -m venv .venv
  # If script execution is disabled on your PC, run this once:
  # Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt cmd.exe):**
  ```cmd
  py -3.11 -m venv .venv      # or: python -m venv .venv
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS (bash/zsh):**
  ```bash
  # Check your version with 'python3 --version'. If it shows 3.14+ (common on Homebrew),
  # specify python3.11 or python3.12 (TensorFlow requires Python 3.10-3.13):
  python3.11 -m venv .venv       # or: python3.12 -m venv .venv / python3 -m venv .venv
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

### 1.3 Install Precompiled Wheel and Dependencies

```bash
pip install -r requirements.txt
pip install ../dist/robotos_kws-0.1.3-py3-none-any.whl
```

> [!TIP]
> **Universal Fallback (if `pip` says `command not found` in any shell):**  
> You can always run `pip` through Python directly:
> ```bash
> python -m pip install -r requirements.txt
> python -m pip install ../dist/robotos_kws-0.1.3-py3-none-any.whl
> ```

### 1.4 Verify CLI

```bash
robotos-kws --help
```

Or use:

```bash
python -m robotos_kws --help
```

> [!NOTE]
> **Windows Note (`python` vs `py`):**  
> On Windows, `py` launches the global system Python and ignores your virtual environment. Once your `.venv` is activated (your prompt shows `(.venv)`), always use **`python`**, which points to `.venv/Scripts/python.exe`.

### 1.5 Optional: Flash Workshop Firmware to ESP32-S3 Board

If you are using a physical ESP32-S3 board with microphone (`es3c28p`) or IMU (`ws28p`), flash the workshop firmware first:

```bash
# For microphone board (ES3C28P):
robotos flash-firmware --board es3c28p

# For IMU motion board (WS28P):
robotos flash-firmware --board ws28p
```
*(Or use `robotos-flash --board es3c28p`)*.

The tool auto-detects your serial port (`COM*` or `/dev/cu.usbmodem*`), downloads the binaries, flashes with live progress, and performs an automated handshake verification confirming the board is ready.

---

## 2. Lab 1.1: Audio Sensing & Device Calibration

Inspect available audio input devices connected to your computer:

```bash
robotos-kws devices
```

Look for your default input device index. Note the sampling rate ($16\text{ kHz}$) and 16-bit PCM dynamic range.

---

## 3. Lab 1.2: Rigorous Multi-Class Audio Collection

Collect labelled audio clips using your computer's microphone. All audio is automatically centered, trimmed to 1.0 second (16,000 samples @ 16 kHz), and validated against minimum SNR thresholds.

### 3.1 Collect Keyword Commands
Record 20 takes for each of the target keywords (`red`, `green`, `blue`, `off`):
```bash
robotos-kws collect-pc --speaker me --session s01 --labels red green blue off --takes 20
```
> Press **Enter**, wait for the **GO** prompt, and speak clearly into your microphone.

### 3.2 Collect Ambient Silence (Negative Class)
Record background room noise (fans, keyboard typing, ambient stillness) without speech prompts:
```bash
robotos-kws collect-pc --speaker me --session s01 --labels _silence_ --takes 30 --no-prompt
```

### 3.3 Collect Unknown Speech (Negative Class)
Record non-keyword words (e.g. *"computer"*, *"robot"*, *"yellow"*, numbers) to teach the model to ignore other speech:
```bash
robotos-kws collect-pc --speaker me --session s01 --labels _unknown_ --takes 20
```

> [!TIP]
> **No Mic Available or Need Quick Test?**
> You can generate a 100% synthetic test dataset in 5 seconds without recording:
> ```bash
> robotos-kws synth-data --out dataset
> ```

---

## 4. Lab 1.3: Deep Learning Training & Int8 Quantization

Train a Depthwise Separable Convolutional Neural Network (DS-CNN) with 4× data augmentation (time-shifts, additive noise, volume scaling) and perform Post-Training Quantization (PTQ) to int8:

```bash
robotos-kws train --data dataset --out artifacts --epochs 40 --augment 4
```

### Key Concepts Observed:
- **Log-Mel Spectrogram Extraction**: Turns 16,000 PCM samples into a $49 \times 40$ time-frequency matrix.
- **Post-Training Quantization (PTQ)**: Scales weights and activations from float32 ($32\text{ bits}$) to int8 ($8\text{ bits}$) using representative calibration samples.
- **Model Footprint**: The resulting `model_int8.tflite` is only ~18.8 KiB (fitting comfortably inside an ESP32-S3's internal SRAM).

---

## 5. Lab 1.4: Model Evaluation & Confusion Matrix

Benchmark the quantized int8 model on held-out test splits and generate an evaluation report:

```bash
robotos-kws evaluate --artifacts artifacts --data dataset
```

Open and inspect `artifacts/report.md`:
- Review the confusion matrix (checking for confusion between words).
- Verify precision, recall, and F1-score across all classes.
- Measure quantization loss (comparing float32 vs int8 accuracy).

---

## 6. Lab 1.5: Real-Time Live Inference via PC Microphone

Run continuous, sliding-window keyword spotting in real time directly on your computer microphone:

```bash
robotos-kws live-pc --model artifacts/model_int8.tflite --threshold 0.85
```

- Speak keywords (`"red"`, `"green"`, `"blue"`, `"off"`) into your microphone.
- Observe:
  - **Sliding Window**: Step size ($200\text{ ms}$ hop) and $1.0\text{ s}$ window.
  - **Refractory Window**: $1000\text{ ms}$ cooldown preventing duplicate triggers for a single utterance.
  - **Softmax Confidence**: Triggers only when probability exceeds $0.85$.

---

## 7. Lab 1.6: Embedded C Firmware Export & DSP Verification

As an Embedded Systems engineer, your final task is preparing the model for bare-metal / RTOS firmware deployment.

### 7.1 Verify C DSP Feature Parity
Verify that the C-based log-mel filterbank implementation in ESP-IDF matches the Python DSP bit-for-bit:

```bash
robotos-kws verify-c --data dataset --max-clips 30
```

### 7.2 Export Model Array for ESP-IDF Firmware
Convert the quantized int8 TFLite model into a byte-aligned C array and header:

```bash
robotos-kws export --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main
```

Inspect the generated files:
- `../firmware/kws-inference/main/model_data.cc`: Contains `alignas(16) const unsigned char g_model[]` mapped to flash memory (`.rodata`).
- `../firmware/kws-inference/main/kws_labels.h`: Contains the label enum and string array.

---

## Troubleshooting

- **Microphone too quiet / "Signal too quiet" warning:**
  Speak 15–30 cm from the microphone. If using a laptop mic, check your OS input volume levels in Sound Settings.
- **Python version conflicts:**
  Ensure you are using Python 3.10–3.13. On Windows, use `py -3.11 -m venv .venv`.
- **PortAudio missing on Linux:**
  Run `sudo apt install libportaudio2`.

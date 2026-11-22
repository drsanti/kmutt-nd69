# ND01 — Week 08: Edge AI Data, Training, Testing, and Firmware

> **Before the practical:** [ND01 — Week 07 Edge AI theory](../week07/README.md). Week 07 explains the foundational concepts; this Week 08 section applies them in labs.

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

**Session:** Saturday 21 November 2026 · Online · 09:00–12:00  
**Topic:** *Data collection, model training, model testing, and firmware/algorithms for Edge AI*  
**Track Focus for ND1:** **Embedded Systems & IoT — CLI Pipeline using Computer Microphone (No Board Required)**

In this session, you build a complete Edge AI pipeline from raw audio signals to microcontroller-ready firmware headers. You interact with the pipeline entirely through the **`robotos-kws` CLI**, recording clean audio datasets via your computer's microphone, training a compact convolutional neural network (DS-CNN), quantizing to int8, testing live detection, and exporting MCU C arrays (`model_data.cc`).

> [!NOTE]
> - **ND01 (This Track):** Embedded Systems & IoT — Focus on CLI-only pipeline using PC microphone, model quantization, and C firmware generation.
> - **ND02 (App Track):** Backend & Frontend — Focus on Python SDK (`import robotos_kws`), FastAPI inference APIs, WebSockets, and reactive web dashboards.
> - **ND03 (Robotics Track):** Automation & Robotics — Focus on real board hardware and 50 Hz IMU motion gestures.

---

## Table of Contents

- [Labs Guide](labs/README.md)
- [Pre-Flight Readiness Quiz (10 Questions)](preflight.md)
- [Architecture Decision Record: `robotos-kws`](adr-robotos-kws.md)
- [Checkpoint Quiz](checkpoint.md)
- [Mini Challenge → Mini-Project 2](mini-challenge.md)
- [Troubleshooting](troubleshooting.md)
- [Track Index](../../README.md)

---

## Learning Outcomes

- **Describe the Edge AI Pipeline**: Acoustic sensing → Log-mel spectrograms → DS-CNN → int8 quantization → MCU C array export.
- **Microcontroller Resource Budgeting**: Understand why model memory footprint must fit in SRAM (< 25 KiB) and evaluate static tensor arena memory allocation in FreeRTOS.
- **Acoustic Dataset Hygiene**: Collect balanced multi-class datasets using computer microphones, enforcing minimum SNR thresholds and negative classes (`_silence_`, `_unknown_`).
- **Post-Training Quantization (PTQ)**: Quantize float32 models to int8 with representative calibration datasets and evaluate quantization loss.
- **Real-Time Sliding-Window Inference**: Benchmark continuous detection latency, hop size ($200\text{ ms}$), refractory delay, and softmax confidence thresholds.
- **Embedded C Feature Parity**: Verify bit-level feature extraction equivalence between Python DSP and ESP-IDF C headers (`kws_features.c`).

---

## Schedule (09:00–12:00)

| Time | Block | Topic | Hands-On CLI Command |
| :--- | :--- | :--- | :--- |
| **09:00–09:25** | Block 1 | Audio Sensing & Device Calibration | `robotos-kws devices` |
| **09:25–10:00** | Block 2 | Multi-Class Audio Dataset Collection | `robotos-kws collect-pc` |
| **10:00–10:35** | Block 3 | DS-CNN Model Training & Int8 Quantization | `robotos-kws train` |
| **10:35–11:05** | Block 4 | Model Benchmarking & Confusion Matrix | `robotos-kws evaluate` |
| **11:05–11:35** | Block 5 | Real-Time Live Inference via PC Mic | `robotos-kws live-pc` |
| **11:35–12:00** | Block 6 | Embedded C Firmware Export & Verification | `robotos-kws export`, `robotos-kws verify-c` |

---

## Prerequisites & Installation

Inside `nd1/docs/week08/labs/python`:

```bash
cd nd1/docs/week08/labs/python

# 1. Create and activate virtual environment (Python 3.10 - 3.13; avoid 3.14+)
# (Windows: if 3.11 not installed, run: winget install Python.Python.3.11)
# (macOS:   if 3.11 not installed, run: brew install python@3.11)

# Windows:
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3.11 -m venv .venv       # or: python3.12 -m venv .venv / python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies & precompiled wheel
pip install -r requirements.txt
pip install ../dist/robotos_kws-0.1.3-py3-none-any.whl

# 3. Verify CLI is ready
robotos-kws --help
```

---

## Hardware & Firmware Flashing (Optional for ND1)

While the primary ND1 lab operates entirely on your computer's microphone, you can also connect and test directly with physical ESP32-S3 boards:
- **Audio Board (`es3c28p`):** Onboard ES8311 microphone + WS2812 RGB LED (`caps = 0x33`).
- **IMU Board (`ws28p`):** QMI8658 6-axis IMU + LCD display (`caps = 0x3c`).

> [!IMPORTANT]
> ### ⚡ If using an ESP32-S3 Board, Flash Workshop Firmware First!
> Before running hardware telemetry commands (`check-board`, `collect-board`, `live-board`), ensure your board is programmed with the workshop firmware:
> ```bash
> # Flash audio/mic board firmware:
> robotos flash-firmware --board es3c28p
>
> # Or for IMU/motion board:
> robotos flash-firmware --board ws28p
> ```
> *(Or use `robotos-flash --board es3c28p`)*.
> The automated flasher detects the USB port, downloads prebuilt binaries, flashes with live progress, and performs an automated handshake verification.

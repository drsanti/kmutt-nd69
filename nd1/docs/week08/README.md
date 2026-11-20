# ND01 — Week 08: Edge AI Data, Training, Testing, and Firmware

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

**Session:** Saturday 21 November 2026 · Online · 09:00–12:00 · Topic: *Data collection, model training, model testing, and firmware/algorithms for Edge AI*

In this session you build a complete Edge AI pipeline: record labelled data, train a small neural network, test and quantize it, then run it on the ES3C28P (ESP32-S3R8) with FreeRTOS. The main example is a **keyword spotter** that listens for four words (`red`, `green`, `blue`, `off`) and sets the WS2812 LED. A lighter **touch-screen gesture** track uses the same workflow.

## Table of contents

- [Lessons](lessons/README.md)
- [Labs (firmware + Python)](labs/README.md)
- [Checkpoint quiz](checkpoint.md)
- [Mini challenge → Mini-Project 2](mini-challenge.md)
- [Troubleshooting](troubleshooting.md)
- [Week 06](../week06/README.md)
- [Week 03](../week03/README.md)
- [Week 02](../week02/README.md)
- [Documents](../README.md)
- [Track index](../../README.md)

## Learning outcomes

- Describe the Edge AI pipeline (data → features → model → quantization → firmware) and the ESP32-S3 limits that shape each step.
- Collect a clean, labelled audio dataset with the board microphone or a computer microphone, and split it without leakage.
- Train a small DS-CNN on log-mel features and read a confusion matrix.
- Quantize to int8 with a representative dataset and measure the accuracy and size change.
- Run the model on the ESP32-S3 with TensorFlow Lite Micro, using a FreeRTOS producer/consumer design, and measure latency.
- Explain why on-device features must match training features exactly, and how to check it.
- Name the security controls that protect a deployed model (secure boot, flash encryption).

## Schedule (09:00–12:00)

| Time | Block | Lesson / lab |
|---|---|---|
| 09:00–09:20 | The Edge AI pipeline and ESP32-S3 limits | [01](lessons/01-edge-ai-pipeline.md) |
| 09:20–09:50 | Data collection: board mic, PC mic, dataset hygiene | [02](lessons/02-data-collection.md) · `collect.py`, `collect_pc_mic.py` |
| 09:50–10:25 | Features (log-mel) and a small DS-CNN in Keras / Colab | [03](lessons/03-features-and-model.md) · `train.py` |
| 10:25–10:55 | Testing, confusion matrix, int8 quantization, PC live test | [04](lessons/04-testing-and-quantization.md) · `evaluate.py`, `live_infer_pc.py` |
| 10:55–11:40 | Firmware: TFLite Micro, static arena, FreeRTOS tasks, latency | [05](lessons/05-firmware-inference.md) · `kws-inference` |
| 11:40–12:00 | Secure Edge AI note, checkpoint, mini challenge | [06](lessons/06-secure-edge-ai.md) · [checkpoint](checkpoint.md) · [challenge](mini-challenge.md) |

The [touch-screen gesture track](lessons/07-touch-gesture-alternative.md) is an alternative for students who prefer it, or extra work after class.

## Three data paths

Pick the path that matches your hardware. All three produce the same dataset layout, so the training and testing steps do not change.

| Path | Hardware | Collect with | Best for | Watch out for |
|---|---|---|---|---|
| **A — Board microphone (main)** | ES3C28P + USB-C cable | `audio-logger` firmware + `collect.py` | Data that matches deployment exactly | Needs ESP-IDF set up (Week 03) |
| **B — Computer microphone** | Laptop / USB mic | `collect_pc_mic.py`; test live with `live_infer_pc.py` | Fast collection and testing **without a board** | Domain shift: a PC mic hears differently from the board mic |
| **C — Touch screen (lighter)** | ES3C28P | `touch-logger` firmware + `collect_touch.py` | A simpler first model (gestures) | Different model and features; see Lesson 07 |

> [!IMPORTANT]
> **No board?** You can complete data collection, training, testing, and live testing entirely on your computer with path B. **Have a board?** Mix PC and board clips for training, and always test on **board-recorded** clips before you trust the model on the board.

## Prerequisites

- ESP-IDF **v6.1** working from a terminal (`idf.py --version`) — see [Week 03](../week03/lessons/install-esp-idf.md). Only needed for the firmware parts.
- Python 3.10–3.13 with a virtual environment, or a Google account for Colab.
- Week 02 hardware lessons, especially [Lesson 10 — Audio chain](../week02/lessons/EN/10-audio-chain.md), [Lesson 09 — Touch](../week02/lessons/EN/09-ft6336-touch.md), [Lesson 11 — WS2812](../week02/lessons/EN/11-ws2812-rmt-led.md), and [Lesson 15 — FreeRTOS](../week02/lessons/EN/15-embedded-c-freertos-review.md).

```bash
cd nd1/docs/week08/labs/python
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python make_synthetic_dataset.py   # 30-second check that everything is installed
```

## What was verified

| Item | Status |
|---|---|
| Python scripts (synthetic dataset → train → evaluate → export → live test) | Run end-to-end on Linux, Python 3.13, TensorFlow 2.21 on 20 November 2026 |
| `collect_pc_mic.py`, `live_infer_pc.py` microphone code | Run with a **mocked** `sounddevice` (no microphone on the test machine); `--from-wav` / `--wav` paths run for real |
| `collect.py` serial protocol | Run against a simulated audio-logger on a pseudo-terminal (no board) |
| C feature code (`kws_features.c`) vs Python features | Compiled with gcc and compared: max difference 0.00008 |
| int8 model on the TFLite Micro reference interpreter | Same top-1 result as TFLite on 48 of 48 test clips |
| Firmware projects | API names checked against ESP-IDF v6.1, esp_codec_dev 1.6.2, esp-tflite-micro 1.4.3, and led_strip 3.1.1. `kws_main.cc` passed a host syntax check with stub IDF headers. **Not built with `idf.py` and not flashed** |

Record your own build and hardware results separately, as in Week 03.

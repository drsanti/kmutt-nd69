# ND01 — Week 08: Edge AI Data, Training, Testing, and Firmware

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-index-2e8b57?style=flat-square)

**Session:** Saturday 21 November 2026 · Online · 09:00–12:00 · Topic: *Data collection, model training, model testing, and firmware/algorithms for Edge AI*

In this session you build a complete Edge AI pipeline: record labelled data, train a small neural network, test and quantize it, then run it live. You start from where the [hardware-interface-workshop](https://github.com/drsanti/hardware-interface-workshop) ended: your board already runs the workshop's **prebuilt firmware** (flashed with `rb flash-bin`, no ESP-IDF), and it already streams sensor data over USB with the workshop wire protocol. This week a Python program on your computer speaks that same protocol, so **you do not need to flash anything to collect data or test a model**.

- **Main track — keyword spotting (ES3C28P, board microphone).** Listen for `red`, `green`, `blue`, `off`. The board streams 16 kHz audio; the model runs on your computer (`live_infer_board.py`).
- **Alternative track — IMU gestures (ws28p).** Recognise `idle`, `shake`, `circle`, `lift` from the 50 Hz accelerometer + gyroscope stream (`live_infer_imu.py`).
- **No board?** Use your computer microphone for the whole keyword track.
- **On-device step.** The last block runs the keyword model *on the ESP32-S3* with TensorFlow Lite Micro (`kws-inference`, ESP-IDF). It is an instructor demo / advanced lab and the starting point for Mini-Project 2 (5 December).

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
- Read sensor streams from the workshop firmware in Python (COBS frames, CRC, protobuf, capability check) and detect lost data.
- Collect a clean, labelled dataset (board microphone, computer microphone, or IMU) and split it without leakage (by speaker / person).
- Train a small DS-CNN on log-mel features and read a confusion matrix.
- Quantize to int8 with a representative dataset and measure the accuracy and size change.
- Test the model live with the board streaming to the computer, then explain what changes when it runs on the ESP32-S3 with TensorFlow Lite Micro (FreeRTOS producer/consumer, static arena, latency).
- Explain why on-device features must match training features exactly, and how to check it.
- Name the security controls that protect a deployed model (secure boot, flash encryption).

## Schedule (09:00–12:00)

| Time | Block | Keyword track (ES3C28P / PC mic) | IMU track (ws28p) |
|---|---|---|---|
| 09:00–09:15 | The Edge AI pipeline, from workshop rules to trained models | [01](lessons/01-edge-ai-pipeline.md) | same |
| 09:15–09:50 | Data collection over the workshop wire protocol; dataset hygiene | [02](lessons/02-data-collection.md) · `collect.py`, `collect_pc_mic.py` | [07 §1–3](lessons/07-imu-gesture-alternative.md) · `collect_imu.py` |
| 09:50–10:20 | Features and a small CNN in Keras / Colab | [03](lessons/03-features-and-model.md) · `train.py` | [07 §4–6](lessons/07-imu-gesture-alternative.md) · `train_imu.py` |
| 10:20–10:55 | Testing, confusion matrix, int8, **live test with the board** | [04](lessons/04-testing-and-quantization.md) · `evaluate.py`, `live_infer_board.py`, `live_infer_pc.py` | [07 §7](lessons/07-imu-gesture-alternative.md) · `live_infer_imu.py` |
| 10:55–11:35 | On-device inference: TFLite Micro, static arena, FreeRTOS, latency (demo / advanced) | [05](lessons/05-firmware-inference.md) · `kws-inference` | watch the demo |
| 11:35–12:00 | Secure Edge AI note, checkpoint, mini challenge | [06](lessons/06-secure-edge-ai.md) · [checkpoint](checkpoint.md) · [challenge](mini-challenge.md) | same |

## Three data paths

Pick the path that matches your hardware. Paths A and B produce the same keyword dataset layout, so training and testing do not change between them.

| Path | Hardware + firmware | Collect with | Live test with | Watch out for |
|---|---|---|---|---|
| **A — Board microphone (main)** | ES3C28P + workshop prebuilt `es3c28p` firmware | `collect.py` | `live_infer_board.py` | Close the workshop browser tab first: only one program can own the serial port |
| **B — Computer microphone** | Laptop / USB mic, no board | `collect_pc_mic.py` | `live_infer_pc.py` | Domain shift: a PC mic hears differently from the board mic |
| **C — IMU gestures (alternative)** | ws28p + workshop prebuilt `ws28p` firmware | `collect_imu.py` | `live_infer_imu.py` | Different data and model; see [Lesson 07](lessons/07-imu-gesture-alternative.md) |

> [!IMPORTANT]
> **No board?** You can do data collection, training, testing, and live testing entirely on your computer with path B. **Have an ES3C28P?** Mix PC and board clips for training, and always test on **board-recorded** clips before you trust the model with the board. **Wrong board attached?** Every board tool reads `BoardInfo` first and stops with a clear message (ES3C28P caps `0x33` has the mic; ws28p caps `0x3c` has the IMU).

## Prerequisites

- The [hardware-interface-workshop](https://github.com/drsanti/hardware-interface-workshop) prebuilt firmware on your board ([`firmware-prebuilt/`](https://github.com/drsanti/hardware-interface-workshop/tree/main/firmware-prebuilt): `rb config --port <PORT> --board es3c28p` or `ws28p`, then `rb flash-bin`). Nothing else to flash for the main labs.
- Python 3.10–3.13 with a virtual environment, or a Google account for Colab (training only).
- Only for the on-device block (Lesson 05): ESP-IDF **v6.1** working from a terminal — see [Week 03](../week03/lessons/install-esp-idf.md).
- Background: workshop labs ex03 (BoardInfo), ex20–21 (IMU), ex28 (mic recorder), ex30 (mic features), ex32 (mic classify); Week 02 [Lesson 10 — Audio chain](../week02/lessons/EN/10-audio-chain.md) and [Lesson 15 — FreeRTOS](../week02/lessons/EN/15-embedded-c-freertos-review.md).

```bash
cd nd1/docs/week08/labs/python
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python test_wire.py                # board protocol self-test (no board needed)
python make_synthetic_dataset.py   # 30-second check that everything is installed
```

## What was verified

| Item | Status |
|---|---|
| `wire.py` codec (COBS, CRC-16/XMODEM, frames, protobuf messages) | Matches the firmware's published golden frames; byte-identical to the workshop's TypeScript codec (`demos/src/lib/wire/*.ts` run with Node.js + protobufjs) in both directions |
| `collect.py`, `collect_imu.py`, `live_infer_board.py`, `live_infer_imu.py` | Run against a **simulated board** on a pseudo-terminal sending real frames (BoardInfo, CmdAck, MicPcm, AudioLevel, Imu) with log noise, a corrupted frame and deliberately dropped chunks/samples. Saved clips were sample-exact; drops were detected; the wrong board was rejected. **No real board was attached** |
| Keyword pipeline (synthetic dataset → train → evaluate → export → live test) | Run end-to-end on Linux, Python 3.13, TensorFlow 2.21 (20 November 2026) |
| `train_imu.py --synthetic` | 8 synthetic people, 2 held out: float32 100%, int8 98.5% (plumbing test, not a real-data result) |
| `collect_pc_mic.py`, `live_infer_pc.py` microphone code | Run with a **mocked** `sounddevice`; `--from-wav` / `--wav` paths run for real |
| C feature code (`kws_features.c`) vs Python features | Compiled with gcc and compared: MATCH |
| int8 keyword model on the TFLite Micro reference interpreter | Same top-1 result as TFLite on 48 of 48 test clips |
| `kws-inference` firmware | API names checked against ESP-IDF v6.1, esp_codec_dev 1.6.2, esp-tflite-micro 1.4.3, led_strip 3.1.1; host syntax check with stub headers. **Not built with `idf.py` and not flashed** |

Record your own board results separately, as in Week 03.

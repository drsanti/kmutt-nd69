# Week 08 lessons

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lessons-2e8b57?style=flat-square)

## Table of contents

- [Week 08 index](../README.md)
- [Lesson 01 — The Edge AI Pipeline and ESP32-S3 Limits](01-edge-ai-pipeline.md)
- [Lesson 02 — Data Collection: Board Mic, PC Mic, and Dataset Hygiene](02-data-collection.md)
- [Lesson 03 — Log-Mel Features and a Small DS-CNN](03-features-and-model.md)
- [Lesson 04 — Testing, Confusion Matrix, and int8 Quantization](04-testing-and-quantization.md)
- [Lesson 05 — Firmware: TFLite Micro on FreeRTOS](05-firmware-inference.md)
- [Lesson 06 — Secure Edge AI: Protecting the Model and Firmware](06-secure-edge-ai.md)
- [Lesson 07 — Alternative Track: IMU Gesture Classifier (ws28p)](07-imu-gesture-alternative.md)
- [Labs](../labs/README.md)

## Read in this order

1. Lesson 01 — the whole picture, before you touch any code
2. Lesson 02 — record data (board mic over the workshop protocol **or** PC mic, or both)
3. Lesson 03 → 04 — train, test, quantize, then the live test with the board (laptop or Colab)
4. Lesson 05 — move the model onto the board (demo / advanced; reflash the workshop firmware afterwards)
5. Lesson 06 — read before you ship anything
6. Lesson 07 — the IMU gesture track for ws28p boards (same workflow, different sensor)

## One rule for the whole week

> [!IMPORTANT]
> **Inference must compute exactly the same numbers the model was trained on.** Sample rate, gain, filters, trimming, framing, window, FFT size, mel filters, log, and quantization are all part of the model (for the IMU track: rate, window length, axis order, and scaling). `kws_common.py` (Python) and `kws_features.c` (firmware) implement one specification, and `verify_c_features.py` checks that they agree.

## Paths used in these lessons

| Name | What it is |
|---|---|
| Python labs | `nd1/docs/week08/labs/python` — run every `python ...` command from here |
| Board protocol (Python) | `nd1/docs/week08/labs/python/wire.py` — same frames as the workshop's `demos/src/lib/wire/*.ts` |
| Board firmware for collection and live tests | hardware-interface-workshop [`firmware-prebuilt/`](https://github.com/drsanti/hardware-interface-workshop/tree/main/firmware-prebuilt) (`rb flash-bin`) |
| On-device inference firmware | `nd1/docs/week08/labs/firmware/kws-inference` (ESP-IDF; replaces the prebuilt firmware while flashed) |
| Audio driver used by `kws-inference` | `nd1/docs/week08/labs/firmware/components/es3c28p_audio` |

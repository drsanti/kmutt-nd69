# kws-inference — Keyword Spotting on the ESP32-S3

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-firmware-2e8b57?style=flat-square)

[Labs index](../../README.md) · [Lesson 05](../../../lessons/05-firmware-inference.md)

Listens continuously to the onboard microphone, runs a TensorFlow Lite Micro int8 model every 500 ms, and sets the WS2812 LED (GPIO42) for `red`, `green`, or `blue`, or turns it off for `off`.

> [!IMPORTANT]
> **This firmware replaces the hardware-interface-workshop prebuilt firmware while it is on the board.** It does not speak the workshop wire protocol, so `collect.py`, `live_infer_board.py`, and the workshop browser demos will not work until you put the prebuilt firmware back:
>
> ```bash
> cd hardware-interface-workshop/firmware-prebuilt/es3c28p
> python -m esptool --chip esp32s3 -p <PORT> write-flash "@flash_args"
> # Windows: py -m esptool --chip esp32s3 -p COMx write-flash "@flash_args"
> ```
>
> In class this is an **instructor demo / advanced lab** (it needs ESP-IDF v6.1) and the starting point for Mini-Project 2 (5 December).

## Build and flash

```bash
# 1. put YOUR model in (the checked-in model is a synthetic placeholder)
cd nd1/docs/week08/labs/python
python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main

# 2. build, flash, watch
cd ../firmware/kws-inference
idf.py set-target esp32s3
idf.py build flash monitor
```

Use `idf.py -p <PORT> flash` if the port is not found. Close the workshop browser tab first.

The first build downloads `espressif/esp-tflite-micro` (~1.4.3, with `esp-nn`), `espressif/led_strip` (~3.1.1), and `espressif/esp_codec_dev` (~1.6.2).

## Design

```text
capture_task (core 0, prio 6): 20 ms blocks from the ES8311 → xQueueSend(q, 0) (count drops, never block)
inference_task (core 1, prio 4): 1 s ring buffer → every 500 ms: kws_features_compute → int8 → Invoke
                                 → average of 3 → threshold 0.70 + refractory → LED + printf
```

| File | Role |
|---|---|
| `main/kws_main.cc` | Tasks, queue, interpreter, decision logic, LED, latency measurement |
| `main/kws_config.h` | Gain/slot (match the level of your training clips), hop, smoothing, threshold, arena, priorities |
| `main/kws_features.c/.h` | Log-mel features. Must match `labs/python/kws_common.py`; check with `verify_c_features.py` |
| `main/model_data.cc` | Model C array (generated, 16-byte aligned, in flash) |
| `main/kws_labels.h` | Label order (generated) |

`sdkconfig.defaults`: target esp32s3, USB Serial/JTAG console, 240 MHz, `-O2` (performance), the single-app *large* partition table (TFLM needs more than the default 1 MB app partition), and FreeRTOS run-time stats.

## Serial output

```text
I (xxx) kws: model 19240 bytes, arena used NNNNN of 65536 bytes, input scale 0.092664 zp 21
_silence_  0.97          | features  xx.x ms  quant  x.x ms  invoke  xx.x ms | queue 0/16 dropped 0 |  -xx.x dBFS
red        0.88 DETECTED | features  xx.x ms  quant  x.x ms  invoke  xx.x ms | queue 0/16 dropped 0 |  -xx.x dBFS
```

## Status

Written against ESP-IDF v6.1, esp-tflite-micro 1.4.3, led_strip 3.1.1, and esp_codec_dev 1.6.2. API names and header paths were checked against those component sources, and `kws_main.cc` passed a host C++ syntax check against the real TFLM and led_strip headers (with ESP-IDF headers stubbed). `kws_features.c` was compiled on a PC and matches the Python features. The int8 placeholder model runs on the TFLite Micro reference interpreter. The project has **not** been built with `idf.py`, and latency has not been measured on a board. The auto mic-slot option in `components/es3c28p_audio` was added without a compile check on a target.

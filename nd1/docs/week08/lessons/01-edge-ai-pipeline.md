# Lesson 01 — The Edge AI Pipeline and ESP32-S3 Limits

> Week 08 · ES3C28P / ESP32-S3 · 09:00–09:20

[Lesson index](README.md) · [Next: Lesson 02](02-data-collection.md)

## Learning objectives

Name every stage of an Edge AI project, say which stage runs where (PC, cloud, or microcontroller), and use the ESP32-S3's memory and compute limits to size a model before you train it.

## The pipeline

```text
   ┌────────────┐   ┌───────────┐   ┌──────────┐   ┌──────────────┐   ┌────────────┐
   │ 1. Collect │──►│ 2. Train  │──►│ 3. Test  │──►│ 4. Quantize  │──►│ 5. Deploy  │
   │ labelled   │   │ features  │   │ held-out │   │ float → int8 │   │ C array +  │
   │ clips      │   │ + model   │   │ data     │   │ + re-test    │   │ TFLite µ   │
   └────────────┘   └───────────┘   └──────────┘   └──────────────┘   └─────┬──────┘
         ▲                                                                   │
         └─────────── 6. Monitor on the device, collect the failures ◄───────┘
```

| Stage | Runs on | Tool in this week | Output |
|---|---|---|---|
| Collect | Board or PC | `collect.py`, `collect_pc_mic.py` | `dataset/<label>/*.wav` |
| Train | PC / Colab | `train.py` (Keras) | `model.keras`, `model_float.tflite` |
| Test | PC / Colab | `evaluate.py`, `live_infer_pc.py` | `report.md`, confusion matrix |
| Quantize | PC / Colab | `train.py` (TFLite converter) | `model_int8.tflite` |
| Deploy | ESP32-S3 | `export_c_array.py` + `kws-inference` | firmware with the model in flash |
| Monitor | ESP32-S3 | serial log: scores, latency, drops | the next round of data |

Stage 6 is where real projects spend most of their time. The first deployed model is never the last one: you record the cases where it fails on the board and add them to the dataset.

## Why run AI at the edge?

| Benefit | Example in this lab |
|---|---|
| Latency | The LED reacts in well under a second, with no network round trip |
| Privacy | Audio never leaves the board; only the result is used |
| Works offline | No Wi-Fi needed |
| Energy and cost | No server; the MCU can sleep between events |

The price is a very small budget for memory and compute, which drives every design choice below.

## The ESP32-S3R8 budget

Numbers for the ES3C28P (see [Week 02, Lesson 03](../../week02/lessons/EN/03-memory-types.md)):

| Resource | Available | What it means for the model |
|---|---|---|
| CPU | 2 × Xtensa LX7 up to 240 MHz, with vector (SIMD) instructions | int8 kernels from ESP-NN run much faster than float kernels |
| Internal SRAM | ~512 KB, shared with Wi-Fi, stacks, drivers | Tensor arena + audio buffers should fit in tens of KB |
| PSRAM | 8 MB (octal) | Large but slower; use for big buffers, not hot tensors |
| Flash | Holds firmware + model (read in place) | Model weights cost flash, not RAM |
| No FPU-heavy accelerator | Single-precision FPU only | Keep float work (features) small and int8 for the network |

### Sizing the keyword model

```text
Input:   49 frames × 40 mel bands = 1,960 values (int8 → 1,960 bytes)
Model:   DS-CNN, ~5.5 k parameters → about 19 KB int8 .tflite in flash
Arena:   activations + scratch ≈ 37 KB (measured with the TFLite Micro reference
         interpreter on a PC; the firmware prints the real value at boot)
Work:    one inference every 500 ms
```

A model that needs 2 MB of weights or 500 KB of activations does not fit, however accurate it is. Decide the budget **first**, then design the model to fit it.

## Two kinds of "algorithm" on the device

1. **Signal processing (deterministic):** windowing, FFT, mel filters, log. Written in C. It must match training exactly.
2. **Neural network (learned):** the TFLite model. Its weights come from training; TFLite Micro runs it.

Around both sits **decision logic**: averaging scores over time, a threshold, and a refractory period so one word does not trigger three times. This logic is tuned on the PC with `live_infer_pc.py` and copied into `kws_config.h`.

## Check your understanding

1. Which stage needs the board, and which stages can a student without a board complete?
2. Why do model weights cost flash but activations cost RAM?
3. Give one reason a 99%-accurate model on the PC can be useless on the board.

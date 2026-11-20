# ND01.4 — Firmware Architecture and Real-Time Edge AI

[ND01 Week 07](../README.md) | [Previous: TinyML](03-tinyml-and-memory.md) | [Week 08 practice](../../week08/labs/README.md)

## Inference software is not a single function

Microphone samples arrive on a schedule whether or not the CPU is running an FFT. A robust embedded design separates acquisition, feature processing, inference and user-visible actions.

```mermaid
flowchart LR
    H["I²S + DMA"] --> C["High-priority capture task"]
    C --> Q["Bounded queue / ring buffer"]
    Q --> P["Feature extraction task"]
    P --> M["INT8 model invocation"]
    M --> G["Threshold + smoothing"]
    G --> U["Low-priority display / LED"]
```

## Producer–consumer reasoning

The capture task is a **producer**: it places newly received audio blocks into a queue. The inference task is a **consumer**. A bounded queue absorbs temporary delays but cannot hide sustained overload.

If the producer must wait for a full queue, the next DMA block may overrun or be missed. A design may therefore send with zero timeout and increment a dropped-block counter. That keeps acquisition responsive but does **not** make drops harmless. A lost block can corrupt a model window.

A proper log should include queue occupancy, dropped blocks, timestamps and effective sampling rate.

## Scheduling and end-to-end latency

Consider:
- Audio acquisition duration (a 1-second window must be populated).
- Hop interval for repeated classifications.
- Feature computation.
- Model inference.
- Smoothing across model outputs.
- Refractory period.
- Action scheduling and peripheral response.

**End-to-end detection latency is not the same as neural-network invocation time.** A detector with a 10 ms inference can still respond hundreds of milliseconds after the event because it needs a window and decision rules.

### Useful instrumentation

Measure the beginning and end of feature computation, tensor filling, `Invoke()`, and action handling using a monotonic timer. Measure peak task stack use, queue occupancy and buffer drops. Compare these metrics while varying hop length.

## Host inference versus on-device inference

| Aspect | Host-side model | MCU-side model |
|---|---|---|
| Sensor data path | Board/PC → host | Mic/codec → MCU |
| Processing | Python SDK / desktop | C/C++ + embedded runtime |
| Iteration | Usually fast | May require firmware build and flash |
| Resource constraints | Host RAM and OS timing | SRAM, Flash and fixed-time capture |
| Dependence on connection | Usually host/USB dependent | Can be autonomous |
| Trust boundary | Sensor data leave local board | Audio can stay on board |

When firmware is replaced with a custom inference program, the previous workshop serial protocol may no longer be available. Keep a known recovery procedure to restore the workshop firmware.

## Preprocessing parity and reproducibility

Treat capture chain + DSP + model + postprocessing as one versioned artifact. Maintain a small set of reference audio clips and expected feature tensors. Re-test when codec gain, slot, filter coefficients, microphone placement or model changes.

Avoid claiming bitwise parity unless fixed-point representation and rounding match. Otherwise compare numerical tolerances and observed predictions.

## Security and updates

- **Secure boot** authenticates firmware at boot; it does not by itself encrypt model bytes in Flash.
- **Flash encryption** can protect data at rest on supported/appropriately configured devices; it serves a different purpose.
- Firmware/model updates require compatibility checking, integrity validation and rollback procedures.
- Hot-swapping a model without recompilation is possible *only if* firmware was designed with external model storage, dynamic loading and compatible kernels/memory plans.

A demo can use a compiled-in model array. A production device may need a model partition and robust update infrastructure, but this adds engineering complexity.

## Practical architecture exercise

Sketch FreeRTOS tasks for an ESP32-S3 keyword spotter. Mark task priorities, queue size, capture block size and inference hop. If inference suddenly needs 600 ms every 500 ms, determine whether the queue can remain stable indefinitely (it cannot) and propose measurable remedies.

## Review questions

1. Why is it dangerous to block a capture producer waiting for inference?
2. What is the difference between a short compute time and short end-to-end response time?
3. Why must model input preprocessing match training?
4. What must change to support model hot-loading from a data partition?
5. How do secure boot and flash encryption address different risks?

Continue to [ND01 Week 08 practical labs](../../week08/labs/README.md) and [embedded firmware lessons](../../week08/lessons/README.md).

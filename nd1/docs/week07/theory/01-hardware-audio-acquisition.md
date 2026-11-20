# ND01.1 — Hardware Audio Acquisition: Microphone to Digital Samples

[ND01 Week 07](../README.md) | [Shared sensors](../../../../shared/week07/foundations/01-sensors-and-signals.md) | [Next: DSP](02-audio-dsp-features.md)

## The real signal chain

Sound is a pressure variation in air. A microphone diaphragm responds to pressure and produces an electrical signal. For an analog microphone, amplification, bias and analog filtering occur before the audio ADC. An audio codec converts the waveform into digital samples; the ESP32 receives those samples over a digital serial interface.

```mermaid
flowchart LR
    A["Sound pressure"] --> M["Microphone element"]
    M --> B["Analog gain + conditioning"]
    B --> C["ES8311 audio ADC / codec"]
    C --> D["I²S receive peripheral"]
    D --> E["DMA buffers"]
    E --> F["Firmware audio pipeline"]
```

The course's **ES3C28P** configuration uses an **ES8311 audio codec**. The ESP32-S3 does not necessarily perform microphone conversion through its generic SAR ADC. Know the responsibilities of each chip: analog input and conversion in the audio chain, and digital transport and computation in the microcontroller.

## Analog frontend

Tiny microphone output levels need a suitable signal path. Conceptually inspect:
- Microphone supply, bias and reference.
- Input amplifier and gain settings.
- Signal clipping at analog and digital stages.
- High-pass filtering for DC/low-frequency noise.
- Anti-alias filtering before the effective sampling/decimation stage.

Gain affects signal-to-noise ratio only if the selected stage and the sources of noise are understood. If the acoustic input is poor, turning up digital volume cannot restore information that was never captured.

## ADC, PCM and format

A 16 kHz signed-16-bit mono PCM stream contains 16,000 sample values per second. In raw form, that is 32,000 bytes per second. In a real system, I²S peripheral transport can include extra slot and word widths, potentially yielding more bytes on the wire than the mono samples eventually stored.

The following parameters must be unambiguous:
- Sample rate, bit depth and signedness.
- Mono/stereo channel selection.
- Channel/slot mapping and byte order.
- Microphone input gain and filters.
- Where timestamps or sequence counters are assigned.

A sample stream is not the same as a WAV file. WAV includes a header carrying a description of the audio representation.

## Interfaces: I²C and I²S have different roles

The MCU usually configures an audio codec using a **control interface**, often I²C. The audio samples are carried over an **audio-data interface**, commonly I²S. Configuration registers and continuous audio frames are conceptually separate.

- **I²C:** codec setup such as gain, power and format.
- **I²S:** streaming audio words synchronized with clock and frame signals.
- **DMA:** transfers buffered data with reduced per-sample CPU intervention.
- **Interrupt / task notification:** tells firmware that new buffered data are ready.

## Why buffers exist

For 16 kHz mono audio, receiving just one sample per interrupt is often wasteful. DMA fills blocks so firmware can process groups of samples efficiently.

Example: a block of **320 samples** represents `320/16000 = 0.02 s` or 20 ms of audio. A 16-block queue spans 320 ms of buffered audio *capacity* (not guaranteed user-visible response delay). If the consumer falls behind, the queue fills; the system must detect drops and avoid pretending the resulting input is intact.

## Raw audio level and dBFS

Digital full-scale (dBFS) expresses a signal's level relative to the largest representable amplitude. RMS dBFS is often computed as `20*log10(rms / full_scale)`. Silence can be represented as negative infinity dBFS in an ideal noiseless calculation, although real microphones have noise floors.

Check both:
- **Too quiet:** model input may consist mostly of noise.
- **Clipping:** waveform peaks are flattened and cannot be reconstructed exactly.

Different microphone or codec gains can change the feature distribution and cause domain shift.

## Engineering exercise

Given a 16 kHz mono, 16-bit PCM capture path:
1. Calculate bytes generated each second.
2. Calculate the period and byte size of 320-sample blocks.
3. Decide what happens if inference is slower than the arrival rate.
4. Explain why changing I²S slot selection can produce missing or distorted audio.
5. Draw the I²C control path *separately* from the I²S data path.

## Review

What must stay consistent between an audio recording used for training and the audio capture chain used during inference? Include format, channel choice, level, filters and sampling rate.

[Next: Audio DSP](02-audio-dsp-features.md)

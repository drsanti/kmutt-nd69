# 02 — Analog-to-Digital Conversion and Sampling

[Foundations](README.md) | [Previous: Sensors](01-sensors-and-signals.md) | [Next: DSP and features](03-dsp-and-feature-extraction.md)

## The three steps of digitization

An analog-to-digital converter (ADC) measures a continuously varying electrical signal and represents its amplitude with finite-width digital codes.

```mermaid
flowchart LR
    A["Analog input x(t)"] --> F["Analog anti-alias filter"]
    F --> S["Sample at selected instants"]
    S --> Q["Quantize amplitude"]
    Q --> E["Encode as N-bit code"]
    E --> D["Sample values + timestamps"]
```

- **Sampling** determines *when* a measurement is taken.
- **Amplitude quantization** selects one of a finite number of representable levels.
- **Encoding** stores the selected level as bits.
- **Machine-learning model quantization** is a *different* optimization that reduces parameter or activation precision after or during training.

An ADC often has more circuitry than this simplified diagram shows. An audio codec may perform advanced oversampling and digital filtering internally.

## Sampling rate and sample interval

For uniform sampling at `fs` samples/s:

```text
sample interval Ts = 1 / fs
sample index n  ->  time t = n / fs
number of samples = fs * duration
```

Examples:
- Microphone at 16,000 Hz: one sample every 62.5 microseconds; a one-second mono window has 16,000 samples.
- IMU at 50 Hz: one sample every 20 milliseconds; a two-second window has 100 rows, each containing six channels in the ND03 example.

**Careful:** arrival time of a USB or serial packet is not necessarily the moment the sensor was sampled. Hardware buffering, scheduling and transmission add delays and jitter.

## ADC bits and amplitude resolution

An ideal `N`-bit unipolar ADC has `2^N` codes. If the ideal full-scale interval is `Vrange`, then:

```text
ideal step (LSB) = Vrange / 2^N
```

For a hypothetical 0–3.3 V ADC:

| Nominal bits | Number of codes | Ideal step |
|---:|---:|---:|
| 8 | 256 | 12.89 mV |
| 10 | 1,024 | 3.22 mV |
| 12 | 4,096 | 0.806 mV |
| 16 | 65,536 | 0.0504 mV |

**Worked example.** A hypothetical 12-bit linear ADC measures 1.65 V over a 0–3.3 V ideal range. Half-scale is near code 2048. In practice, ADC noise, gain error, offset, calibration, input impedance and nonlinearity influence the result.

ADC **resolution** is not equal to noise-free **accuracy**. A perfectly repeatable offset can bias every sample even if the ADC has many bits.

## Signed PCM is not the same as a unipolar ADC code

Audio often uses signed 16-bit pulse-code modulation (PCM): integer range -32768 to +32767. It represents positive and negative waveform excursions around the digital zero reference.

One second at 16 kHz, mono, 16-bit PCM uses:

```text
16,000 samples × 2 bytes/sample = 32,000 bytes
≈ 31.25 KiB of raw PCM
```

A WAV file is a container with header metadata; PCM is one possible sample encoding inside it. Sampling a microphone at 16 kHz does **not** mean using a generic ESP32 ADC at 16 kHz; the codec can do conversion.

## Nyquist limit, aliasing and anti-alias filters

For ideal reconstruction of a band-limited continuous signal, the sampling frequency must exceed twice the highest signal frequency. A practical system also requires an analog filter before sampling that suppresses out-of-band energy.

At 16 kHz sampling, the Nyquist frequency is 8 kHz. A real 9 kHz tone may alias into a 7 kHz pattern if not adequately filtered. A high number of ADC bits does not fix this aliasing problem.

If the sensor uses an internal sampling and decimation chain, find out where its anti-alias filtering occurs.

### Activity: sample a sine wave on paper

Sketch a sine wave and place sample dots at several different rates. Try a rate comfortably above twice the tone frequency, then one below it. Ask which sampled pattern could be explained by another, lower-frequency tone.

## Dynamic range, gain and clipping

Increasing microphone gain can increase the amplitude of desired sound, but it also amplifies upstream noise and may cause clipping when the waveform hits the representable limit. Clipped peaks are lost information.

In the course CLI, a sample may be rejected for being too quiet or for clipping. These are **data quality rules**, not model predictions.

## Questions

1. What is the difference between sampling and amplitude quantization?
2. What are the Nyquist frequencies for 16 kHz audio and 50 Hz IMU sampling?
3. Calculate the memory for two seconds of six-channel 16-bit IMU readings sampled at 50 Hz, excluding timestamps: `2*50*6*2 = 1200 bytes`.
4. Why can a digital IMU provide data without the MCU's ADC?
5. Does 16-bit audio imply a 16-bit neural network?
6. How can timing jitter or lost frames distort a motion-recognition model?

[Next: DSP and features](03-dsp-and-feature-extraction.md)

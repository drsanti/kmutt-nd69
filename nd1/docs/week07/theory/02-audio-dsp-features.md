# ND01.2 — Audio DSP and Reproducible Feature Extraction

[ND01 Week 07](../README.md) | [Previous: Acquisition](01-hardware-audio-acquisition.md) | [Next: TinyML](03-tinyml-and-memory.md)

## Why raw audio is not yet a keyword

Consider the spoken words “red” and “green.” Their recordings are arrays of amplitude values, not strings. The same word varies in duration, loudness, pitch, speaker, room acoustics and microphone response.

The signal-processing pipeline must create a stable numerical representation while preserving the differences that matter for recognizing words.

## Time and frequency views

A waveform plots amplitude versus time. A Fourier transform describes the contribution of frequencies to an analyzed interval. Spoken language changes over time, so keyword spotting typically uses **short-time** spectra rather than one FFT for the entire clip.

```mermaid
flowchart LR
    A["16,000 PCM samples"] --> B["Short overlapping frames"]
    B --> C["Window function"]
    C --> D["FFT and power spectrum"]
    D --> E["Mel filter bank"]
    E --> F["Log energy"]
    F --> G["49 × 40 feature matrix"]
```

## Frame geometry worked example

In the Week 08 keyword-spotting material:
- Sampling rate: 16,000 samples/s.
- Clip length: 1 second, or 16,000 samples.
- Frame length: 480 samples (30 ms).
- Frame hop: 320 samples (20 ms).
- FFT length: 512 samples; frames are typically zero-padded to this size.
- Feature bands: 40.

The count of complete frames is:

```text
1 + floor((16000 - 480) / 320)
= 1 + floor(48.5)
= 49
```

Thus the model's example time-frequency input has 49×40 = **1,960** feature values before any additional channel dimension is added. This is not equivalent to the 16,000 original PCM values; the transform aggregates and compresses information.

## The FFT in context

An FFT efficiently computes a discrete Fourier transform. Every bin is associated with a frequency relative to the sample rate and FFT size. For a 512-point FFT at 16 kHz, nominal bin spacing is `16000/512 = 31.25 Hz`. This is *grid spacing*, not a claim that nearby frequencies can always be resolved precisely in a 30 ms window.

Shorter windows are better at tracking rapid time changes, while longer windows generally provide better spectral discrimination. The choice is an engineering trade-off.

## Mel filters and log compression

Instead of supplying every FFT bin directly, a mel filter bank combines energy into overlapping frequency bands. A log operation compresses a wide energy range. A common conceptual form is:

```text
feature[frame, band] = log(mel_energy[frame, band] + epsilon)
```

The exact choice of power/magnitude convention, filter geometry, log base, epsilon, window function and normalization must be versioned. Two “log-mel” implementations may differ substantially.

## Why parity with firmware matters

A model trained using Python features should not receive inconsistent C-computed features after deployment. Potential mismatches:
- Different PCM gain and microphone channel.
- Different sample-rate conversion.
- Different frame padding or hop.
- Different Hann-window coefficient convention.
- Mel frequency edges or normalization.
- Float-vs-fixed-point rounding and quantization.

The Week 08 CLI includes a `verify-c` stage intended to compare embedded C feature extraction with the Python reference. **A passing feature-parity test does not guarantee accuracy** if the live capture path differs in gain, filtering or acoustics.

## Input pipeline acceptance tests

A strong test sequence:
1. Save a known short PCM clip as a reference fixture.
2. Run Python feature extraction and preserve the feature tensor.
3. Run the equivalent C implementation on the *same* samples.
4. Compare absolute and relative errors against a defined tolerance.
5. Inspect selected frames / bands, including silence and high-energy cases.
6. Repeat on real board-collected recordings, not only synthetic tones.

“Bit-for-bit equivalence” is possible only when implementations intentionally use matching representations and rounding. Otherwise define numerical tolerance rather than claiming an exact bit match.

## Why a simple waveform demo is valuable

Show the same spoken word as (1) a waveform, (2) a spectrogram, and (3) a log-mel tensor. Ask what changes when the speaker moves farther from the microphone. Then show how a high-confidence prediction can still be wrong if the input changes drastically.

## Questions

1. Why are overlapped short frames used for speech?
2. What is the shape of the model input in this example?
3. What is lost when an FFT spectrum is collapsed into mel bands?
4. Why should the audio processing pipeline be treated as part of the model?
5. How can identical source samples produce different model predictions through different preprocessing?

[Next: TinyML](03-tinyml-and-memory.md)

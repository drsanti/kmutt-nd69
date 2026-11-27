# Lesson 03 — Log-Mel Features and a Small DS-CNN

> Week 08 · ES3C28P / ESP32-S3 · 09:50–10:20

[Lesson index](README.md) · [Previous: Lesson 02](02-data-collection.md) · [Next: Lesson 04](04-testing-and-quantization.md)

## Learning objectives

Turn one second of audio into a log-mel "image", explain each processing step, and train a depthwise-separable CNN small enough for the ESP32-S3 — on a laptop or on Google Colab.

## Why not feed raw audio to the network?

One second at 16 kHz is 16,000 numbers. A network that learns directly from that needs many more parameters and much more data. Speech information sits in **which frequencies are loud over time**, so we compute that first with fixed signal processing, then give the network a small 49 × 40 matrix.

## The feature pipeline (the contract)

```text
int16 PCM, 16 kHz, 16000 samples
  │  ÷ 32768            → float in [-1, 1)
  │  − mean             → remove DC offset (the board mic path can have one)
  ▼
49 frames × 480 samples   (30 ms window, 20 ms hop, no padding: 1 + (16000 − 480) / 320 = 49)
  │  × periodic Hann window
  │  512-point FFT       → 257 frequency bins (0 … 8 kHz, 31.25 Hz apart)
  │  |X|²                → power spectrum
  ▼
40 triangular mel filters, 20–7600 Hz (HTK mel scale: mel = 2595·log10(1 + f/700))
  │  ln(energy + 1e-6)
  ▼
49 × 40 log-mel matrix  → model input (49, 40, 1)
```

| Step | Why |
|---|---|
| Framing (30 ms / 20 ms) | Speech is roughly stable over 20–30 ms; overlap avoids missing transitions |
| Hann window | Reduces spectral leakage at frame edges |
| FFT 512 | Next power of two above 480; fast on any CPU |
| Mel filters | Match human pitch perception: fine resolution at low frequencies, coarse at high |
| Log | Loudness is perceived logarithmically; it also compresses the range for int8 |
| Upper edge 7600 Hz | Stays below the 8 kHz Nyquist limit, where filters are poorly defined |

This exact definition lives in the wheel's `robotos_edge.audio.features` (`log_mel()`) and in `labs/firmware/kws-inference/main/kws_features.c`. **MFCC** would add one more step (a DCT that decorrelates the 40 bands into ~10–13 coefficients). MFCCs suit classic models; CNNs work well on log-mel directly, so we skip the DCT and keep the firmware simpler.

### Verify the C twin

```bash
robotos-kws verify-c --data dataset --max-clips 50
```

This compiles the firmware's C code on your PC (gcc or clang), runs it on your clips, and compares every value. On the course test data the largest difference was 0.00008 (float rounding). A large difference means the board would see different inputs from the ones the model learned — fix it **before** deploying.

## The model: DS-CNN

A normal 3 × 3 convolution with 32 input and 32 output channels needs 3·3·32·32 = 9,216 weights. A **depthwise-separable** convolution splits it into:

1. a **depthwise** 3 × 3 filter per channel: 3·3·32 = 288 weights
2. a **pointwise** 1 × 1 convolution that mixes channels: 32·32 = 1,024 weights

That is 1,312 weights instead of 9,216 — about 7× fewer — with similar accuracy on keyword spotting. It is the standard building block for microcontroller vision and audio models.

```text
Input 49×40×1
Conv2D 32, 5×3, stride 2  → BN → ReLU         25×20×32
[ DepthwiseConv 3×3 → BN → ReLU → Conv 1×1 (32) → BN → ReLU ] × 3
GlobalAveragePooling                            32
Dropout 0.2
Dense 6, softmax                                6 class probabilities
≈ 5.5 k parameters
```

Batch normalisation is folded into the convolutions during TFLite conversion, so it costs nothing on the device. Global average pooling becomes the `MEAN` op.

## Training

```bash
robotos-kws train --data dataset --out artifacts --epochs 40
```

What `robotos-kws train` does:

1. Scans `dataset/`, prints clips per label and per device, refuses to train if a label is empty.
2. Splits by speaker (or speaker + session) and saves `splits.json`.
3. Augments each training clip twice: time shift ±100 ms, gain ±6 dB, and `_silence_` noise mixed in at 5–25 dB SNR.
4. Computes log-mel features with `robotos_edge.audio.features.log_mel()`.
5. Trains with class weights, early stopping on validation accuracy, and learning-rate reduction.
6. Saves `model.keras`, `model_float.tflite`, `model_int8.tflite`, and `meta.json`, and prints the list of ops the firmware must register.

A synthetic dry run (no microphone) shows the expected output:

```bash
robotos-kws synth-data --out synth_dataset --per-class 64
robotos-kws train --data synth_dataset --out synth_artifacts --epochs 40
```

```text
Parameters: 5,510
float32 TFLite: 26.1 KiB   int8 TFLite: 18.8 KiB
int8 ops (register these in the firmware op resolver): ['CONV_2D', 'DEPTHWISE_CONV_2D', 'FULLY_CONNECTED', 'MEAN', 'SOFTMAX']
```

> [!WARNING]
> The synthetic dataset is made of tones, not speech. It proves that the scripts work; a model trained on it recognises nothing real.

### On Google Colab

Open [`labs/python/train_colab.ipynb`](../labs/python/train_colab.ipynb) in Colab (File → Open notebook → GitHub, or upload the file). Zip your `dataset` folder, upload it when the notebook asks, and run all cells. The notebook trains, evaluates, checks the C features, and downloads `week08_export.zip` with `model_data.cc` and `kws_labels.h`.

> [!NOTE]
> Colab runs Linux, and `robotos_edge` 0.2.0 is published only for Windows and macOS, so the notebook cannot install it yet. Train on your laptop until a Linux wheel is added to `labs/dist/`.

### Knobs worth trying

| Knob | Where | Effect |
|---|---|---|
| `--width 16` / `--width 48` | `robotos-kws train` | Fewer / more channels → smaller / larger and usually less / more accurate |
| `--augment 0` vs `4` | `robotos-kws train` | Shows how much augmentation helps on the test speakers |

## Check your understanding

1. Why is the frame count 49 and not 50?
2. How many weights does a 3 × 3 depthwise-separable layer with 32 → 32 channels need, compared with a normal convolution?
3. You change the hop from 20 ms to 10 ms in Python only. What happens on the board?

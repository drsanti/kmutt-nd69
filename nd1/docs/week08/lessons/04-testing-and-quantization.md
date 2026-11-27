# Lesson 04 — Testing, Confusion Matrix, and int8 Quantization

> Week 08 · ES3C28P / ESP32-S3 · 10:20–10:55

[Lesson index](README.md) · [Previous: Lesson 03](03-features-and-model.md) · [Next: Lesson 05](05-firmware-inference.md)

## Learning objectives

Measure a model honestly on held-out data, read a confusion matrix, quantize the model to int8 with a representative dataset, measure what quantization costs, and try the model live — with the board streaming its microphone to your computer, or with the computer microphone — before anything is flashed.

## Evaluate on the test split

```bash
robotos-kws evaluate --artifacts artifacts --data dataset
robotos-kws evaluate --artifacts artifacts --data dataset --device board     # board clips only
robotos-kws evaluate --artifacts artifacts --data board_session3 --all       # a fresh folder, every clip
```

`robotos-kws evaluate` runs **both** TFLite models (float32 and int8) through `robotos_edge.audio.features.run_tflite()`, the same input quantization the firmware uses, and writes `artifacts/report.md`.

Example from the synthetic dry run (48 test clips from held-out speakers):

```text
## model_int8.tflite
- accuracy: 91.7%
- file size: 18.8 KiB
- accuracy on `board` clips: 87.5% (n=24)
- accuracy on `pc` clips: 95.8% (n=24)

true \ pred       red     green      blue       off _silence_ _unknown_   recall
red                8         0         0         0         0         0   100.0%
green              0         8         0         0         0         0   100.0%
blue               0         0         8         0         0         0   100.0%
off                0         0         0         8         0         0   100.0%
_silence_          0         0         0         0         8         0   100.0%
_unknown_          2         2         0         0         0         4    50.0%

## Quantization
- accuracy drop float32 -> int8: +0.00 percentage points
- size ratio int8/float32: 0.72
```

### Reading the confusion matrix

- **Rows** are the true labels, **columns** are predictions. The diagonal is correct.
- **Recall** per row: of all real `_unknown_` clips, how many were recognised as `_unknown_`.
- Here, `_unknown_` clips were taken for `red` or `green` 4 times out of 8. On a device, that is a **false trigger**: the LED changes when nobody said a keyword.

For a keyword spotter, the two errors have different costs:

| Error | Example | User experience | Lever |
|---|---|---|---|
| Miss (false reject) | "red" → `_silence_` | Annoying: say it again | Lower threshold, more keyword data |
| False trigger (false accept) | TV says "bread" → `red` | Worse: the device acts by itself | Higher threshold, more `_unknown_` data, smoothing |

Accuracy alone hides this. Always look at the `_unknown_` and `_silence_` rows.

### The domain-shift number

The per-device lines are the most important result for anyone who trained with PC clips. A gap such as 95.8% on `pc` vs 87.5% on `board` (even on synthetic data) is the warning from Lesson 02 in numbers. The number that predicts the board's behaviour is the **board-only test accuracy**.

## Quantization: float32 → int8

The board runs an **int8** model: every weight and activation is stored as an 8-bit integer plus a scale and zero point:

```text
real_value ≈ scale × (q − zero_point)          q ∈ [−128, 127]
```

| | float32 | int8 |
|---|---|---|
| Weight storage | 4 bytes | 1 byte |
| Arithmetic | float multiply–add | integer multiply–add (ESP-NN SIMD on the S3) |
| Typical accuracy cost | — | 0–2 percentage points for a well-calibrated small CNN |

### The representative dataset

To choose a scale for every activation tensor, the converter must see realistic inputs. `robotos-kws train` passes 300 random training feature matrices:

```python
conv.optimizations = [tf.lite.Optimize.DEFAULT]
conv.representative_dataset = representative          # yields real log-mel inputs
conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
conv.inference_input_type = tf.int8                    # the firmware feeds int8
conv.inference_output_type = tf.int8
```

If the representative data does not cover real conditions (for example only quiet PC clips), the scales are wrong for loud board clips, values saturate at −128/127, and accuracy drops. Include every source and noise level.

### Input quantization on the device

The converter stores the input scale and zero point in the model (`meta.json` shows them, for example `scale=0.0927, zero_point=21`). The firmware reads them from the model at run time and applies:

```text
q = clamp(round(x / scale) + zero_point, −128, 127)
```

`robotos_edge.audio.features.run_tflite()` does exactly the same, so the PC accuracy of the int8 model is what the board should achieve on the same audio.

### Why is int8 not 4× smaller here?

The size ratio was 0.72, not 0.25. With only ~5.5 k weights, the FlatBuffer structure, tensor names, and per-channel quantization parameters are a large share of the file. For bigger models the ratio approaches 0.25–0.3.

## Live test with the board (in class)

The board keeps the workshop firmware and streams its microphone; the model runs on your computer:

```bash
robotos-kws live-board --port COM5 --model artifacts/model_float.tflite artifacts/model_int8.tflite
```

```text
ES3C28P mic ─► workshop firmware ─USB MicPcm 16 kHz─► robotos-kws live-board ─► log-mel ─► model ─► "red  0.91  <== DETECTED"
```

This is the most honest test you can do without new firmware: it uses the **board microphone, the board's filter chain, and the board gain** — exactly what the data path A clips contain. If a USB chunk is lost (`MicPcm.seq` gap), the script inserts the same number of silent samples so the timing stays right, and prints the number of lost chunks at the end. A few in a minute is harmless; many means the computer is overloaded or another program is reading the port.

No board? Use the computer microphone with the same detector code:

```bash
robotos-kws live-pc --model artifacts/model_float.tflite artifacts/model_int8.tflite
robotos-kws live-pc --model artifacts/model_int8.tflite --wav my_sentence.wav      # no microphone needed
```

Both scripts use the same streaming logic as the on-device firmware in Lesson 05:

```text
every 250 ms: newest 1.0 s of audio → log-mel → model
average the last 3 probability vectors
accept a keyword if score ≥ 0.70 and it is not _silence_/_unknown_
ignore new detections for 1 s afterwards (refractory period)
```

Try:

1. Say each keyword at normal distance, then from 2 m away.
2. Talk normally for 30 s without keywords and count false triggers.
3. Change `--threshold` (0.5, 0.7, 0.9) and `--smooth` (1, 3, 5). Note the trade-off between misses and false triggers.
4. Write down the best values. If you continue to Lesson 05, copy them into `kws_config.h` (`KWS_THRESHOLD`, `KWS_SMOOTH_WINDOW`). The firmware hop is 500 ms, so its smoothing window covers more time; adjust accordingly.

Remember: a good live result on the **PC** microphone does not guarantee a good result with the **board** microphone. `robotos-kws live-board` is the test that counts.

## Lab checklist

- [ ] `report.md` saved, with float32 and int8 accuracy and the drop in percentage points
- [ ] Board-only accuracy reported (or "no board data")
- [ ] One sentence on the worst row of the confusion matrix and what data would fix it
- [ ] Live test done with `robotos-kws live-board` (or `robotos-kws live-pc` without a board): detections and false triggers noted
- [ ] Threshold and smoothing chosen from the live test

## Check your understanding

1. In the matrix above, what is the recall of `_unknown_`, and what does a low value mean on the device?
2. Why must the representative dataset include board clips if the model will run on the board?
3. Float32 and int8 agree on 100% of test clips, but the board performs badly. Is quantization the cause? What would you check first?
4. `robotos-kws live-board` reports 40 lost chunks in one minute. What does each lost chunk do to the audio the model sees, and what would you check?

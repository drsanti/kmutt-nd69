# Lesson 07 — Alternative Track: Touch-Screen Gesture Classifier

> Week 08 · ES3C28P / ESP32-S3 · optional / lighter track

[Lesson index](README.md) · [Previous: Lesson 06](06-secure-edge-ai.md)

## Learning objectives

Apply the same Edge AI workflow (collect → train → test → quantize → deploy) to a simpler signal: one-finger strokes on the FT6336G touch screen, classified as `circle`, `triangle`, `check`, or `line`.

## Why this track is lighter

| | Keyword spotting (main) | Touch gestures (this lesson) |
|---|---|---|
| Raw data | 16,000 samples/s | ~100 points/s, only while touching |
| Features | log-mel (FFT, mel filters) | resample to 32 points, centre, scale |
| Model | DS-CNN, ~5.5 k parameters | 64 → 32 → 16 → 4 dense network, ~2.7 k parameters |
| Int8 size (synthetic dry run) | 18.8 KiB | 6.4 KiB |
| Real-time pressure | Continuous audio stream | One classification per stroke |

## Hardware recap

From [Week 02, Lesson 09](../../week02/lessons/EN/09-ft6336-touch.md): FT6336G at I2C address `0x38` on SDA GPIO16 / SCL GPIO15 (shared with the ES8311 at `0x18`), interrupt GPIO17, reset GPIO18 (active low). Raw coordinates span about 240 × 320.

## Step 1 — the touch logger

```bash
cd nd1/docs/week08/labs/firmware/touch-logger
idf.py set-target esp32s3
idf.py build flash
```

The firmware resets the controller, polls register `0x02` every 10 ms (status + first touch point), masks the event and ID bits in the high bytes, and prints text lines:

```text
D 112 87 15320      finger down at (112, 87), t = 15320 ms
M 115 90 15330      moved
U 15610             finger up
E ESP_ERR_TIMEOUT   I2C read failed - NOT treated as "finger up"
```

Keeping "read failed" separate from "no contact" avoids false UP events, as Week 02 recommends.

## Step 2 — collect strokes

```bash
cd ../../python
python collect_touch.py --port COM5 --speaker alice --session s01 --takes 15
```

Draw each requested shape with one finger and lift. Files go to `touch_dataset/<gesture>/<session>_<speaker>_board_<index>.csv` with columns `t_ms,x,y`. Ask classmates to draw too: people draw circles clockwise and anticlockwise, and triangles from different corners.

## Step 3 — features

`touch_common.normalise()`:

1. **Resample** the stroke to 32 points spaced equally **along the path**, so drawing speed does not matter.
2. **Centre** the bounding box at (0, 0), so the position on the screen does not matter.
3. **Scale** by the larger side, so the size does not matter (the aspect ratio is kept, so a line stays a line).

The result is 32 × 2 = 64 numbers. On the device you would implement the same three steps in C, just like `kws_features.c` for audio.

## Step 4 — train, test, quantize

```bash
python train_touch.py --data touch_dataset --out touch_artifacts
python train_touch.py --synthetic --out touch_artifacts_synth     # no board: generated shapes
```

The script holds out whole speakers/sessions for testing, trains the small dense network, converts to float32 and int8 TFLite, and prints a confusion matrix for both. The synthetic dry run gives 100% test accuracy for both models, with a 6.4 KiB int8 file — real strokes will be harder.

## Step 5 — deploy (exercise)

The audio firmware is the template:

1. `python export_c_array.py --model touch_artifacts/model_int8.tflite --name g_touch_model --out-dir <your main folder>`
2. Copy the `kws-inference` structure, replace the audio capture task with the touch polling loop from `touch-logger`, and collect points between `D` and `U`.
3. On `U`: resample / centre / scale (in C), quantize the 64 inputs with the model's input scale and zero point, `Invoke()`, and show the result on the LED or the display.
4. Register the ops that the converter used (for this model: `FULLY_CONNECTED` and `SOFTMAX`; check with the TFLite analyzer or the `_get_ops_details()` helper used in `train.py`).

## Extensions

- Add a `none` class for random scribbles, the gesture version of `_unknown_`.
- Use the stroke direction and duration as extra features and compare the accuracy.
- Combine both tracks: a gesture selects a mode, and a keyword confirms it.

## Check your understanding

1. Why resample by arc length instead of keeping every 3rd point?
2. What would go wrong if the C code on the board scaled by the width only, while Python scaled by the larger side?
3. Which ops would you expect in the int8 model for a pure dense network?

# Lesson 07 — Alternative Track: IMU Gesture Classifier (ws28p)

> Week 08 · ws28p (Waveshare ESP32-S3-Touch-LCD-2.8) · runs alongside Lessons 02–04 for students with a ws28p

[Lesson index](README.md) · [Previous: Lesson 06](06-secure-edge-ai.md)

## Learning objectives

Collect labelled motion windows from the ws28p IMU over the workshop wire protocol, turn a 50 Hz stream into fixed windows, handle orientation and scaling, train a tiny 1D CNN with a person-disjoint test set, quantize it to int8, and test it live with the board.

The workflow is the same as the keyword track — collect → train → test → quantize → live test — only the sensor and the features change.

## 1. What the board sends

Flash the workshop's **ws28p** prebuilt firmware (`cd hardware-interface-workshop/firmware-prebuilt/ws28p` → `python -m esptool -p <PORT> write-flash "@flash_args"`). The board then streams IMU data by itself; nothing has to be enabled. This is the stream you used in workshop labs ex20 (IMU hello) and ex21 (shake → beep).

| Item | Value |
|---|---|
| Message | `Imu` (`0x20`), protobuf `robotos.sensor.v1.Imu` |
| Rate | about **50 Hz** (one frame every 20 ms) |
| `acceleration` x, y, z | m/s², ±4 g range — about 9.8 on the axis that points up when the board is still |
| `angular_velocity` x, y, z | rad/s, ±512 °/s range (±8.9 rad/s) |
| `timestamp_ns` | the board's own clock, on a 20 ms grid |
| `BoardInfo.caps` | `0x3c` = IMU + RTC + BATT + BTN (no mic, no RGB LED) |

The ES3C28P has **no IMU** (caps `0x33`). Every IMU tool checks this first and stops with a clear message if the wrong board is attached.

## 2. Collect windows

Close the workshop browser tab first (only one program can own the port), then:

```bash
cd nd1/docs/week08/labs/python
robotos-kws check-imu --port COM7                                  # 3 s of live values
robotos-kws collect-imu --port COM7 --person alice --session s01 --takes 20
```

`--check` prints the measured rate, lost samples, the mean acceleration (|a| should be about 9.8 when still), and the gyro noise.

For each take: press Enter, wait for **GO**, perform the gesture within the 2 s window. The script:

1. listens for `Imu` frames (and `BoardInfo` to check the capabilities),
2. collects 2 s of samples,
3. counts **lost samples** from gaps in `timestamp_ns` (a step bigger than 1.5 × 20 ms); a take with more than `--max-lost` (default 3) is recorded again,
4. resamples onto an exact 50 Hz grid and saves 100 rows × 6 columns.

```text
imu_dataset/
├── idle/     s01_alice_ws28p_0000.csv ...
├── shake/
├── circle/
└── lift/

CSV columns: t_s, ax, ay, az (m/s²), gx, gy, gz (rad/s) — 100 rows = 2.0 s at 50 Hz
```

Pack all windows into one array file for Colab or your own notebook: `python -c "from robotos_edge.imu import features as f; f.main(['pack', '--data', 'imu_dataset'])"` → `imu_dataset.npz` (`x` = N × 100 × 6, `y`, `person`, `session`, `labels`).

## 3. Design the dataset

| Gesture | How | Why it is in the set |
|---|---|---|
| `idle` | hold still, rest it in the hand, put it down, pick it up slowly | the "nothing happened" class, like `_silence_` — make it **varied** |
| `shake` | quick left–right shakes | strong, fast accelerations; gyro around the vertical axis |
| `circle` | draw one or two circles in the air | slow, smooth, two axes out of phase |
| `lift` | lift up and put down | mostly one axis (along gravity) |

Rules carried over from Lesson 02:

- **Balanced classes**, at least 30 windows per gesture per person to start.
- **Many people.** Everybody moves differently: speed, size, and grip. Swap windows with classmates (with consent).
- **Split by person.** `robotos-kws train-imu` holds out whole people for the test set, so the score says how the model does on someone it has never seen. Two windows of the same person are near-copies; mixing them across train and test inflates the score.
- `idle` must include the boring things people really do (looking at the screen, walking with the board), or the model will call them gestures.

The four gesture slots (`idle`, `shake`, `circle`, `lift`) are fixed in `robotos_edge` 0.2.0. To use your own gesture, perform it while collecting one of the three motion slots (for example `--labels circle`) and rename that slot in your application.

## 4. Windowing and resampling

The model sees a fixed **window**: 2.0 s = 100 time steps × 6 channels. Why fixed and why resample?

- A neural network needs a fixed input shape.
- USB delivery is bursty and a frame can be lost; interpolating onto an exact 20 ms grid (`robotos_edge.imu.features.to_grid()`) gives the model evenly spaced samples, using the board's timestamps rather than the arrival time.
- 2 s holds a whole gesture plus a little context. Shorter windows react faster but can cut a circle in half; longer windows delay detection.

Live, the same window **slides**: `robotos-kws live-imu` keeps the newest 2 s and runs the model every 200 ms (`--hop-ms`).

```text
time ─────────────────────────────────────────────►
      [──────── window 1 (2 s) ────────]
          [──────── window 2 ────────]            hop = 0.2 s
              [──────── window 3 ────────]
```

## 5. Normalisation, orientation, and axes

`robotos_edge.imu.features.normalise()` divides acceleration by 9.80665 (→ units of g) and angular velocity by 4 rad/s, then clips to ±4. It uses **fixed** scales, not a per-window z-score, on purpose: a gentle tilt and a hard shake must not look the same.

**Orientation is the hard part.** The IMU measures in the **board's** axes. Gravity (1 g) appears on whichever axis points down:

```text
board flat, screen up:      a ≈ ( 0,    0,   +9.8)
board upright, in portrait: a ≈ ( 0,  +9.8,   0  )      (axis names depend on the chip's mounting)
```

The same "lift" made with the board held flat or held upright therefore produces different numbers. Options, from simplest to strongest:

| Approach | Effect | Cost |
|---|---|---|
| Agree on a grip ("screen up, USB to the right") | Consistent data | Users must follow the rule |
| **Rotation augmentation** (`robotos_edge.imu.features.augment`, ±20° random rotation of accel and gyro together) | Model tolerates a sloppy grip | More training time |
| Remove gravity (subtract the window mean of acceleration) | Ignores how the board is held | Loses tilt information (cannot tell "turn over" from "idle") |
| Use magnitudes (|a|, |ω|) | Fully orientation-independent | Loses direction: `lift` and `shake` may blur |

`robotos-kws train-imu` uses fixed scaling plus augmentation: random rotation, time shift (±10 samples = ±0.2 s), motion strength ×0.8–1.2, and sensor noise. Check the axis directions on your board first with workshop lab ex20 or `robotos-kws collect-imu --check`.

## 6. Train, test, quantize

```bash
robotos-kws train-imu --data imu_dataset --out imu_artifacts
robotos-kws train-imu --synthetic --out imu_artifacts       # no board: generated gestures, plumbing test only
```

```text
Input (100, 6)
Conv1D  8 filters, kernel 5, ReLU   → MaxPool 2
Conv1D 16 filters, kernel 5, ReLU   → MaxPool 2
Conv1D 16 filters, kernel 3, ReLU
GlobalAveragePooling → Dropout 0.2 → Dense 4, softmax          ≈ 1.8 k parameters
```

The script writes `model.keras`, `model_float.tflite`, `model_int8.tflite`, `meta.json`, and prints a confusion matrix for both models on the held-out people. Synthetic dry run on the course test machine (8 generated "people", 2 held out — **not** a real-data result):

```text
model_float.tflite: test accuracy 100.0% on unseen people, 13716 bytes
model_int8.tflite:  test accuracy  98.5% on unseen people, 10496 bytes
true \ pred    idle   shake  circle    lift   recall
lift              3       0       0      47    94.0%
Parameters: 1756   int8 ops: CONV_2D, EXPAND_DIMS, FULLY_CONNECTED, MAX_POOL_2D, MEAN, RESHAPE, SOFTMAX
```

Notes:

- TFLite runs a `Conv1D` as a 2-D convolution with a height of 1, hence `EXPAND_DIMS` / `RESHAPE` / `CONV_2D`. All of these exist in TFLite Micro.
- int8 quantization works exactly as in Lesson 04 (representative windows from the training set).
- Look at the `idle` row and column: a gesture predicted when the user did nothing is the false trigger of this track.

## 7. Live test with the board

```bash
robotos-kws live-imu --port COM7 --model imu_artifacts/model_int8.tflite
robotos-kws live-imu --replay imu_dataset/circle/s01_alice_ws28p_0003.csv --model imu_artifacts/model_int8.tflite   # no board
```

```text
[lost   0] circle  0.93  idle:0.03 shake:0.01 circle:0.93 lift:0.03  <== CIRCLE
```

Same decision logic as the keyword track: average the last 3 results, accept a gesture (never `idle`) when the score ≥ 0.7, then ignore new detections for 1 s. A long gesture can be reported twice; raise `--refractory-ms` if that bothers you.

Try:

1. Each gesture five times — count hits and misses.
2. Hold the board in a different grip. Which gesture suffers most? Retrain with more rotation augmentation or with data in that grip.
3. Walk around for 30 s holding the board. Count false triggers; add that motion to `idle` if needed.
4. Ask a classmate who is not in your dataset to try it. That is your real test accuracy.

> [!NOTE]
> On-device IMU inference is a **mini challenge** (see [mini-challenge.md](../mini-challenge.md)): the model is small enough for TFLite Micro on the ws28p, but it needs your own ESP-IDF firmware that reads the QMI8658, which replaces the workshop firmware while it is flashed.

## Check your understanding

1. Why does `robotos-kws collect-imu` resample on the board's timestamps instead of using the samples as they arrive?
2. A model trained with the board flat fails when the board is held upright. Give two fixes and their costs.
3. Why does `robotos-kws train-imu` split by person, and what would a random split report instead?
4. Why are fixed scales better than per-window standardisation for telling `idle` from `shake`?

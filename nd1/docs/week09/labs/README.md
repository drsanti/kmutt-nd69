# Week 09 Labs: Seeing the Signal

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

[Week 09 index](../README.md) · Lessons: [01 — Time and frequency](../lessons/01-time-and-frequency.md) · [02 — Drawing on a device](../lessons/02-drawing-on-a-device.md)

Five labs, about 30 minutes each. Each script in `labs/python/` runs as-is and has **three `# TODO` tasks**; complete them in order.

| You have | Run labs with |
|---|---|
| **ws28p** (IMU + screen) | no flag — live motion, drawn on the ws28p screen |
| **es3c28p** (mic + screen) | `--replay` — recorded motion, drawn on the es3c28p screen |
| no board | `--replay` — labs 9.1 and 9.2 fully; 9.3–9.5 need a board for the screen |

---

## 1. Setup (15 min)

Reuse your **Week 08** environment and upgrade the `robotos_edge` wheel (Week 09 needs **0.2.2** or newer for the screen API).

```bash
cd nd1/docs/week09/labs/python
```

- **macOS / Linux:**
  ```bash
  source ../../../week08/labs/python/.venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  ..\..\..\week08\labs\python\.venv\Scripts\Activate.ps1
  ```

Then, in any shell:

```bash
pip install -r requirements.txt                                  # adds matplotlib for the PC plots
pip install -U --no-index -f ../../../week08/labs/dist robotos_edge
python -c "import robotos_edge as rk; print(rk.__version__)"      # 0.2.2 or newer
```

**Board check** (skip without a board):

```bash
robotos detect                     # ws28p: caps 0x3c (IMU) · es3c28p: caps 0x33 (MIC)
robotos check-imu                  # ws28p only: ~150 samples at 50 Hz, |a| about 9.8
```

If `robotos detect` says the board needs flashing: `robotos flash-firmware --board ws28p` (or `--board es3c28p`). Always pass `--board`.

**Gesture model for Lab 9.5** — copy yours from Week 08 into `imu_artifacts/model_int8.tflite`, or train one now (about 1 minute):

```bash
robotos-kws train-imu --synthetic --out imu_artifacts
```

> **Synthetic vs. your own model.** `--synthetic` trains only on simulated motion. On a real ws28p it can misread gestures: in our test a shake was reported as `circle` again and again. Use your own Week 08 model (trained on your recordings) when you have one. If the synthetic model mislabels a gesture, that is a lesson in itself: the model only knows the data it was trained on.

> The board's screen holds **3 pages** of your own (plus its built-in HOST tab). Each lab reuses its page name (METER, CHARTS, MODEL), so re-running a lab never adds pages.

---

## Lab 9.1 — Time domain (30 min)

**Script:** `lab9_1_time_domain.py` · **Lesson:** [01 — Time and frequency](../lessons/01-time-and-frequency.md)

```bash
python lab9_1_time_domain.py --replay              # recorded: idle, shake, circle, lift
python lab9_1_time_domain.py --seconds 10          # ws28p: move it around, then hold it still
```

| TODO | Task |
|---|---|
| 1 | Compute \|a\| = √(ax² + ay² + az²) for every sample |
| 2 | Estimate the sample rate from the timestamps |
| 3 | Find which axis points along gravity |

**Observe:** with the board still, \|a\| sits near **9.81 m/s²** whatever its orientation. During `lift` it dips below 9.81, then rises above it — why? Compare the noise (std) of the three accel axes while still.

**Answer in your notes:** (1) What is the time between two samples? (2) Why is \|a\| a better "is it moving?" signal than ax alone? (3) What would `lost > 0` mean, and where can it come from?

---

## Lab 9.2 — Frequency domain (30 min)

**Script:** `lab9_2_frequency.py`

```bash
python lab9_2_frequency.py                         # the 4 sample gestures
python lab9_2_frequency.py --replay my_take.csv    # your own recording(s) from collect-imu
```

| TODO | Task |
|---|---|
| 1 | Remove the mean (gravity, 0 Hz) and take the magnitude of the FFT |
| 2 | Build the frequency axis; the last bin must be 25 Hz |
| 3 | Find the dominant frequency (ignore bin 0) |

**Observe:** `shake` peaks near **11.5 Hz** in \|a\|, but count the swings in the `ax` row of the heat map: the hand moves at about half that. Why does \|a\| double the frequency? The bottom row is exactly what the gesture model receives (100 samples × 6 channels, normalised).

**Answer in your notes:** (1) What is the frequency resolution of a 2 s window, and how would you make it finer? (2) A motor vibrates at 40 Hz — what does a 50 Hz IMU show? (3) Which channels carry most of the `circle` information?

---

## Lab 9.3 — Drawing on the device (30 min)

**Script:** `lab9_3_display_basics.py` · **Lesson:** [02 — Drawing on a device](../lessons/02-drawing-on-a-device.md)

```bash
python lab9_3_display_basics.py --replay           # es3c28p or ws28p screen, recorded motion
python lab9_3_display_basics.py                    # ws28p: live
```

A new **METER** tab appears on the board's screen.

| TODO | Task |
|---|---|
| 1 | Draw the static parts once: title, frame, scale |
| 2 | Convert \|a\| (0–30 m/s²) to a bar width (0–300 px) |
| 3 | The starter **flickers**. Fix it: draw only the part of the bar that changed |

**Observe:** before TODO 3, watch the bar blink; after it, the bar moves smoothly. The script prints `link: {'commands': …}` at the end — compare the number of commands before and after your fix.

**Answer in your notes:** (1) Why does clearing and redrawing flicker on this screen? (2) How many bytes does one full-screen RGB565 image need, and why don't we send that every frame?

---

## Lab 9.4 — Live charts on the device (30 min)

**Script:** `lab9_4_live_charts.py`

```bash
python lab9_4_live_charts.py --replay
python lab9_4_live_charts.py                       # ws28p: tilt and shake it
```

A **CHARTS** tab: a scrolling 3-axis chart on top, a bubble level bottom right.

| TODO | Task |
|---|---|
| 1 | Create a `StripChart` with three traces (ax red, ay green, az blue), range −20…20 m/s² |
| 2 | Convert tilt (ax/g, ay/g) into the bubble's position inside the dial |
| 3 | The starter leaves a **trail** of bubbles. Erase only the old bubble before drawing the new one |

**Observe:** the chart sweeps left to right with a white cursor, like a chart recorder — only the newest columns are sent. Tilt the board: the bubble should move like a spirit level's.

**Answer in your notes:** (1) The chart shows 1 pixel per sample — how many seconds fit across 312 px? (2) Why does the strip chart send only new columns instead of scrolling the whole image?

---

## Lab 9.5 — Seeing the model (30 min)

**Script:** `lab9_5_model_view.py` · needs `imu_artifacts/model_int8.tflite` (see Setup)

```bash
python lab9_5_model_view.py --replay
python lab9_5_model_view.py                        # ws28p: shake, circle, lift
```

A **MODEL** tab: four probability bars (idle, shake, circle, lift), a yellow threshold line, and detection counters.

| TODO | Task |
|---|---|
| 1 | Give every IMU sample to the gesture detector |
| 2 | Draw the bars with the threshold line; highlight a detected gesture (not idle, above the threshold) |
| 3 | A tap inside the bars sets the threshold (top = 1.0, bottom = 0.0) |

**Observe:** tap high (strict) and low (loose) and watch the detection counters. With a low threshold, does `idle` motion start triggering gestures?

**Answer in your notes:** (1) What trade-off does the threshold control? (2) Where would you put it for a robot's emergency-stop gesture, and why?

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: robotos_edge` | Activate the Week 08 `.venv` first (Setup) |
| `AttributeError: … has no attribute 'Display'` / `'ImuStream'` | Old wheel: `pip install -U --no-index -f ../../../week08/labs/dist robotos_edge` |
| `could not create page … (rc=-12)` | The screen's 3 page slots are full: re-run a lab (it reuses its page) or press RESET on the board |
| `no IMU samples …` | Not a ws28p (or wrong firmware): use `--replay`, or `robotos flash-firmware --board ws28p` |
| Nothing appears on the screen | Tap the lab's tab (METER / CHARTS / MODEL) at the top of the screen |
| `imu_artifacts/model_int8.tflite not found` | `robotos-kws train-imu --synthetic --out imu_artifacts` |
| Plots don't open (Lab 9.1/9.2) | `pip install -r requirements.txt` (matplotlib) |

# Week 09 Labs: Seeing the Signal, from Node.js

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

[Week 09 index](../README.md) · Lessons: [01 — Time and frequency](../lessons/01-time-and-frequency.md) · [02 — Drawing on a device](../lessons/02-drawing-on-a-device.md)

Five labs, about 30 minutes each. Each file in `labs/node/` runs as-is and has **three `// TODO` tasks**; complete them in order.

| You have | Run labs with |
|---|---|
| **ws28p** (IMU + screen) | no flag — live motion, drawn on the ws28p screen |
| **es3c28p** (mic + screen) | `--replay` — recorded motion, drawn on the es3c28p screen |
| no board | `--replay` — Labs 9.1 and 9.2 fully; 9.3–9.5 need a board for the screen |

| Folder | What is in it |
|---|---|
| `labs/node/` | the five labs (TypeScript), `lab_common.ts`, recorded motion in `samples/` |
| `labs/service/` | `gesture_service.py`: your IMU model behind a WebSocket (Lab 9.5) |
| `labs/dist/` | `robotos-board-0.1.0.tgz`: the board library (installed by `npm install`) |

---

## 1. Setup (20 min)

### 1a. Node.js and the labs

You need **Node.js 22 or newer** (for the built-in `WebSocket`):

```bash
node --version             # v22.x or newer
```

Older? Install the current LTS from [nodejs.org](https://nodejs.org) (Windows: `winget install OpenJS.NodeJS.LTS`).

```bash
cd nd2/docs/week09/labs/node
npm install                # robotos-board (from ../dist), tsx, TypeScript
npx tsx lab9_2_frequency.ts      # quick check: prints 4 lines and opens a page of plots
```

Open the `labs/node` folder in VS Code: the `robotos-board` API has full type hints (hover a function to see what it does).

### 1b. Board check (skip without a board)

The `robotos` tools come with your Week 08 Python environment. In a **second terminal**:

- **macOS / Linux:**
  ```bash
  source nd2/docs/week08/labs/web-app/.venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  nd2\docs\week08\labs\web-app\.venv\Scripts\Activate.ps1
  ```

```bash
robotos detect             # ws28p: caps 0x3c (IMU) · es3c28p: caps 0x33 (MIC)
```

If it says the board needs flashing: `robotos flash-firmware --board ws28p` (or `--board es3c28p`). Always pass `--board`.

> **One program per board.** Only one program can open the board's USB port at a time. Close `robotos check-imu`, the Week 08 web app, browser tabs using Web Serial and any other lab before you run the next one.

> The board's screen holds **3 pages** of your own (plus its built-in HOST tab). Each lab reuses its page name (METER, CHARTS, MODEL), and Ctrl+C removes the page, so re-running a lab never adds pages.

---

## Lab 9.1 — Time domain (30 min)

**File:** `lab9_1_time_domain.ts` · **Lesson:** [01 — Time and frequency](../lessons/01-time-and-frequency.md)

```bash
npx tsx lab9_1_time_domain.ts --replay             # recorded: idle, shake, circle, lift
npx tsx lab9_1_time_domain.ts --seconds 10         # ws28p: move it around, then hold it still
```

The plots open in your browser (`lab9_1_time_domain.html`, refresh it after each run).

| TODO | Task |
|---|---|
| 1 | Compute \|a\| = √(ax² + ay² + az²) for every sample |
| 2 | Estimate the sample rate from the timestamps |
| 3 | Find which axis points along gravity |

**Observe:** with the board still, \|a\| sits near **9.81 m/s²** whatever its orientation. During `lift` it dips below 9.81, then rises above it. Why? Compare the noise (std) of the three accel axes while still.

**Answer in your notes:** (1) What is the time between two samples? (2) Why is \|a\| a better "is it moving?" signal than ax alone? (3) What would `lost > 0` mean, and where can it come from?

---

## Lab 9.2 — Frequency domain (30 min)

**File:** `lab9_2_frequency.ts`

```bash
npx tsx lab9_2_frequency.ts                        # the 4 sample gestures
npx tsx lab9_2_frequency.ts --replay my_take.csv   # your own recording(s): t_s,ax,ay,az,gx,gy,gz
```

| TODO | Task |
|---|---|
| 1 | Remove the mean (gravity, 0 Hz) and take the magnitude of the FFT (`rk.dsp.rfft`, `rk.dsp.abs`) |
| 2 | Build the frequency axis; the last bin must be 25 Hz |
| 3 | Find the dominant frequency (ignore bin 0) |

**Observe:** `shake` peaks near **11.5 Hz** in \|a\|, but count the swings in the `ax` row of the heat map: the hand moves at about half that. Why does \|a\| double the frequency? The heat maps at the bottom are exactly what the gesture model receives (100 samples × 6 channels, normalised).

**Answer in your notes:** (1) What is the frequency resolution of a 2 s window, and how would you make it finer? (2) A motor vibrates at 40 Hz — what does a 50 Hz IMU show? (3) Which channels carry most of the `circle` information?

---

## Lab 9.3 — Drawing on the device (30 min)

**File:** `lab9_3_display_basics.ts` · **Lesson:** [02 — Drawing on a device](../lessons/02-drawing-on-a-device.md)

```bash
npx tsx lab9_3_display_basics.ts --replay          # es3c28p or ws28p screen, recorded motion
npx tsx lab9_3_display_basics.ts                   # ws28p: live
```

A new **METER** tab appears on the board's screen.

| TODO | Task |
|---|---|
| 1 | Draw the static parts once: title, frame, scale |
| 2 | Convert \|a\| (0–30 m/s²) to a bar width (0–300 px) |
| 3 | The starter **flickers**. Fix it: draw only the part of the bar that changed |

**Observe:** before TODO 3, watch the bar blink; after it, the bar moves smoothly. The script prints `link: { commands: … }` at the end — compare the number of commands before and after your fix.

**Answer in your notes:** (1) Why does clearing and redrawing flicker on this screen? (2) How many bytes does one full-screen RGB565 image need, and why don't we send that every frame?

---

## Lab 9.4 — Live charts on the device (30 min)

**File:** `lab9_4_live_charts.ts`

```bash
npx tsx lab9_4_live_charts.ts --replay
npx tsx lab9_4_live_charts.ts                      # ws28p: tilt and shake it
```

A **CHARTS** tab: a scrolling 3-axis chart on top, a bubble level bottom right.

| TODO | Task |
|---|---|
| 1 | Create a `StripChart` with three traces (ax red, ay green, az blue), range −20…20 m/s² |
| 2 | Convert tilt (ax/g, ay/g) into the bubble's position inside the dial |
| 3 | The starter leaves a **trail** of bubbles. Erase only the old bubble before drawing the new one |

**Observe:** the chart sweeps left to right with a white cursor, like a chart recorder — only the newest columns are sent. Tap another tab and back: `d.onShown` repaints the page.

**Answer in your notes:** (1) The chart shows 1 pixel per sample — how many seconds fit across 312 px? (2) Why does the strip chart send only new columns instead of scrolling the whole image?

---

## Lab 9.5 — Seeing the model (30 min)

**Files:** `lab9_5_model_view.ts` and `../service/gesture_service.py`

The model runs in Python (TensorFlow Lite, as in Week 08). `gesture_service.py` puts it behind a WebSocket; your Node script streams samples to it and draws what it decides.

**Terminal 1 — the service** (Week 08 Python environment, activated as in Setup 1b):

```bash
cd nd2/docs/week09/labs/service
pip install -U --no-index -f ../../../week08/labs/dist robotos_edge     # 0.2.2 or newer
robotos-kws train-imu --synthetic --out imu_artifacts                   # a model, about 1 minute
python gesture_service.py                                               # ws://127.0.0.1:8765/ws
```

Have your own IMU model from Week 08? Use it: `python gesture_service.py --model path/to/model_int8.tflite`.

> **Synthetic vs. your own model.** `--synthetic` trains only on simulated motion. On a real ws28p it can misread gestures: in our test a shake was reported as `circle` again and again. Use your own Week 08 model (trained on your recordings) when you have one. If the synthetic model mislabels a gesture, that is a lesson in itself: the model only knows the data it was trained on.

**Terminal 2 — the lab:**

```bash
npx tsx lab9_5_model_view.ts --replay
npx tsx lab9_5_model_view.ts                       # ws28p: shake, circle, lift
```

A **MODEL** tab: four probability bars (idle, shake, circle, lift), a yellow threshold line, and detection counters. The service prints each detection too.

| TODO | Task |
|---|---|
| 1 | Send every IMU sample to the service (`model.push`) |
| 2 | Draw the bars with the threshold line; highlight a detected gesture (not idle, above the threshold) |
| 3 | A tap inside the bars sets the threshold (top = 1.0, bottom = 0.0) |

**Observe:** tap high (strict) and low (loose) and watch the detection counters. With a low threshold, does `idle` motion start triggering gestures? Open <http://127.0.0.1:8765/docs> to see the service's API page.

**Answer in your notes:** (1) What trade-off does the threshold control? (2) The service is a separate process. What else could use it, and what would you add before putting it on a network?

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Cannot find module 'robotos-board'` | Run `npm install` in `labs/node` |
| `This needs Node.js 22 or newer` | Update Node.js (Setup 1a) |
| `No board found` | Plug in the board (USB-C **data** cable); check with `robotos detect` |
| `cannot open … Resource busy` / `Access denied` | Another program has the port: close it (one program per board) |
| `This needs an IMU (ws28p)` / `no IMU samples …` | Not a ws28p: use `--replay` |
| `could not create page … (rc=-12)` | The screen's page slots are full: re-run a lab (it reuses its page) or press RESET on the board |
| Nothing appears on the screen | Tap the lab's tab (METER / CHARTS / MODEL) at the top of the screen |
| `gesture service not reachable` | Start `python gesture_service.py` first (Lab 9.5, terminal 1) |
| `imu_artifacts/model_int8.tflite not found` | `robotos-kws train-imu --synthetic --out imu_artifacts` in `labs/service` |
| The plot page does not open | Open the `.html` file it printed in your browser yourself |

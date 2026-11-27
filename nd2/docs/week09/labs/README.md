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
| `labs/service/` | `gesture_service.py` (your IMU model behind a WebSocket, Lab 9.5) and the Python environment for the board tools |
| `labs/dist/` | `robotos-board-0.1.0.tgz` (the Node board library, installed by `npm install`) and the `robotos_edge` Python wheel |

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

**What these do:** `npm install` reads `package.json` and downloads what the labs need into `node_modules/`: the board library `robotos-board` (from `../dist`), TypeScript, and `tsx`. `npx tsx <file>.ts` runs a TypeScript file directly, without a separate build step (`npx` runs a tool installed in this folder).

Open the `labs/node` folder in VS Code: the `robotos-board` API has full type hints (hover a function to see what it does).

### 1b. Python environment (board tools + the Lab 9.5 model service)

The board tools (`robotos detect`, firmware flashing) and the model service in Lab 9.5 are Python. Week 09 is **self-contained**: you need nothing from earlier weeks. Do this **before class** if you can: the first install downloads about 600 MB (TensorFlow).

**Python 3.11 is required** (the `robotos_edge` wheel is built for 3.11):

| | Check | Install |
|---|---|---|
| macOS | `python3.11 --version` | `brew install python@3.11` |
| Windows | `py -3.11 --version` | `winget install Python.Python.3.11` |

> **What is `.venv`?** A *virtual environment*: a private folder of Python packages for this week's labs only. While it is activated, `python`, `pip` and the `robotos` commands use that folder, so nothing clashes with other projects or other weeks. To start over, delete the `.venv` folder and create it again.

In a **second terminal**, create the environment (once):

```bash
cd nd2/docs/week09/labs/service
```

- **macOS / Linux:**
  ```bash
  python3.11 -m venv .venv
  source .venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Git Bash):**
  ```bash
  py -3.11 -m venv .venv
  source .venv/Scripts/activate
  ```

Then install everything with **one line** (copy the whole line). It first downloads the libraries (TensorFlow, FastAPI, pyserial; a few minutes the first time), then installs the course SDK `robotos_edge` from `labs/dist`. The second part only works after the first:

```bash
pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge
```

**What the install line does:**

| Part | Meaning |
|---|---|
| `pip install -r requirements.txt` | install every library listed in `requirements.txt`, from the internet |
| `pip install -U --no-index -f ../dist robotos_edge` | install the course SDK `robotos_edge`: `-U` upgrades an older copy, `--no-index` means *do not look on the internet*, `-f ../dist` means *look in the `labs/dist` folder* |

The SDK is not on the internet (only in `labs/dist`), which is why its libraries must be installed first.

Next time, only activate it again (`source .venv/bin/activate`, or `.\.venv\Scripts\Activate.ps1` on Windows).

> **Windows:** if the second `pip install` says *No matching distribution found for robotos_edge*, the Windows wheel is not in `labs/dist` yet: run `git pull` in the course folder and try again.

**Board check** (skip without a board), in the same terminal:

```bash
robotos detect
robotos check-imu                  # ws28p only
```

| Command | What it does | Good result |
|---|---|---|
| `robotos detect` | finds the board on USB, talks to it, and shows its model, capabilities and firmware | `ws28p` with caps `0x3c (IMU…)`, or `es3c28p` with caps `0x33 (…MIC…)`, and `Firmware: robotos-fw/0.3.2` (0.3.0 or newer works for these labs) |
| `robotos check-imu` | reads about 3 s of motion data from a ws28p | about 150 samples, `50.0 Hz, lost 0`, and \|a\| about 9.8 m/s² with the board lying still |

- **No board found:** use a USB-C *data* cable, and close every other program that uses the board (another lab, a serial monitor, a browser tab with Web Serial).
- **Board needs flashing, or old firmware:** `robotos flash-firmware --board ws28p` (or `--board es3c28p`). It downloads the newest firmware, writes it (about 1 minute) and checks the board. Always pass `--board`.
- **`check-imu` says there is no IMU:** you have an es3c28p. That is fine: run the labs with `--replay`.

**Gesture model for Lab 9.5.** Lab 9.5 needs a trained gesture model at `labs/service/imu_artifacts/model_int8.tflite`. There are two ways to get one (run them in `labs/service`, with the `.venv` active).

**A. Quick: a synthetic model** (about 1 minute, no board needed):

```bash
robotos-kws train-imu --synthetic --out imu_artifacts
```

- **What it does:** it makes up 800 practice gestures from formulas for 8 imaginary people (shake = a fast 6 Hz side-to-side wave, circle = a 1.5 Hz circle, lift = one slow up-and-down, idle = a tiny drift). It then trains a small neural network on them: a 1-D CNN with about 1,800 parameters.
- **What it prints:** a test accuracy and a confusion matrix. Expect about 100 %. That score is measured on more made-up gestures, so it says nothing about real motion.
- **What it saves in `imu_artifacts/`:** `model_int8.tflite` (the model the service uses: 8-bit numbers, about 10 KB, small enough for a microcontroller), plus the same model as `model_float.tflite` and `model.keras`, and its settings in `meta.json`.

**B. Better: train on your own recordings** (needs a ws28p, about 10 minutes):

```bash
robotos-kws collect-imu --person yourname --takes 10
robotos-kws train-imu --data imu_dataset --out imu_artifacts
```

- **`collect-imu`** asks for each gesture in turn (idle, shake, circle, lift) and records it `--takes` times: press **Enter**, then perform the gesture for 2 seconds. Each take is saved as `imu_dataset/<gesture>/s01_yourname_ws28p_<n>.csv` (100 samples × 6 channels). A take that lost too many samples is recorded again.
- **`train-imu --data imu_dataset`** trains the same network on your recordings instead of the formulas. With only one person it warns and splits the data per gesture. That is fine; recordings from more people give a model that works for more people.

> **Synthetic vs. your own model.** The synthetic model has only seen idealised formulas. On a real ws28p it can misread gestures: in our test a shake was reported as `circle` again and again. If that happens, it is a lesson in itself: a model only knows the data it was trained on. Try way B and compare.

> **One program per board.** Only one program can open the board's USB port at a time. Close `robotos check-imu`, other web apps or browser tabs using Web Serial and any other lab before you run the next one.

> The board's screen holds **3 pages** of your own (plus its built-in HOST tab). Each lab reuses its page name (METER, CHARTS, MODEL), and Ctrl+C removes the page, so re-running a lab never adds pages.

---

## 2. Options every lab takes

| Option | Meaning | Example |
|---|---|---|
| *(none)* | live: use the board that is plugged in | `npx tsx lab9_1_time_domain.ts` |
| `--replay` | no ws28p: play the recorded motion in `samples/` (idle, shake, circle, lift) instead | `… --replay` |
| `--replay FILE …` | play your own recording(s) instead, e.g. a take from `collect-imu` | `… --replay ../service/imu_dataset/shake/s01_yourname_ws28p_0000.csv` |
| `--seconds N` | stop after N seconds (each lab has its own default) | `… --seconds 10` |
| `--port PORT` | use this serial port instead of finding the board automatically (two boards plugged in, or detection fails; see `robotos detect`) | `… --port COM5` · `… --port /dev/cu.usbmodem101` |
| `--help` | print the lab's options and exit | `… --help` |

Stop any lab with **Ctrl+C** (it also removes the lab's page from the screen).

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
npx tsx lab9_2_frequency.ts --replay ../service/imu_dataset/shake/s01_yourname_ws28p_0000.csv   # your own take (Setup 1b, model B)
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

The model runs in Python (TensorFlow Lite). `gesture_service.py` puts it behind a WebSocket; your Node script streams samples to it and draws what it decides.

**Terminal 1 — the service** (the Python environment from Setup 1b, activated):

```bash
cd nd2/docs/week09/labs/service
python gesture_service.py                          # ws://127.0.0.1:8765/ws  (uses the model from Setup 1b)
```

**Service options:** `--model FILE` uses another model (default `imu_artifacts/model_int8.tflite`); `--threshold 0.8` sets the starting detection threshold (default 0.7). It prints every detection it makes; stop it with Ctrl+C.

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
| `No matching distribution found for numpy>=1.26` (or tensorflow) when installing `robotos_edge` | The libraries were not installed first. Run the whole line from Setup: `pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge` |
| `Cannot find module 'robotos-board'` | Run `npm install` in `labs/node` |
| `This needs Node.js 22 or newer` | Update Node.js (Setup 1a) |
| `No board found` | Plug in the board (USB-C **data** cable); check with `robotos detect` |
| `cannot open … Resource busy` / `Access denied` | Another program has the port: close it (one program per board) |
| `This needs an IMU (ws28p)` / `no IMU samples …` | Not a ws28p: use `--replay` |
| `could not create page … (rc=-12)` | The screen's page slots are full: re-run a lab (it reuses its page) or press RESET on the board |
| Nothing appears on the screen | Tap the lab's tab (METER / CHARTS / MODEL) at the top of the screen |
| `gesture service not reachable` | Start `python gesture_service.py` first (Lab 9.5, terminal 1) |
| `imu_artifacts/model_int8.tflite not found` | `robotos-kws train-imu --synthetic --out imu_artifacts` in `labs/service` (Setup 1b) |
| `robotos: command not found` / `No module named robotos_edge` | Activate the `.venv` in `labs/service` (Setup 1b) |
| The plot page does not open | Open the `.html` file it printed in your browser yourself |

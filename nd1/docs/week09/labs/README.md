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

## 1. Setup (20 min)

Week 09 is **self-contained**: you need nothing from earlier weeks. Do this setup **before class** if you can: the first install downloads about 600 MB (TensorFlow).

**Python 3.11 is required** (the `robotos_edge` wheel is built for 3.11). Check, and install it if missing:

| | Check | Install |
|---|---|---|
| macOS | `python3.11 --version` | `brew install python@3.11` |
| Windows | `py -3.11 --version` | `winget install Python.Python.3.11` |

> **What is `.venv`?** A *virtual environment*: a private folder of Python packages for this week's labs only. While it is activated, `python`, `pip` and the `robotos` commands use that folder, so nothing clashes with other projects or other weeks. To start over, delete the `.venv` folder and create it again.

**Create the environment** (once):

```bash
cd nd1/docs/week09/labs/python
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

Your prompt now starts with `(.venv)`. Then install everything with **one line** (copy the whole line). It first downloads the libraries (numpy, TensorFlow, pyserial, matplotlib; a few minutes the first time), then installs the course SDK `robotos_edge` from `labs/dist`. The second part only works after the first:

```bash
pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge
python -c "import robotos_edge as rk; print(rk.__version__)"   # 0.2.2 or newer
```

**What the install line does:**

| Part | Meaning |
|---|---|
| `pip install -r requirements.txt` | install every library listed in `requirements.txt`, from the internet |
| `pip install -U --no-index -f ../dist robotos_edge` | install the course SDK `robotos_edge`: `-U` upgrades an older copy, `--no-index` means *do not look on the internet*, `-f ../dist` means *look in the `labs/dist` folder* |
| `python -c "import robotos_edge …"` | a check: prints the SDK version if everything is installed |

The SDK is not on the internet (only in `labs/dist`), which is why its libraries must be installed first.

Next time, only activate it again (`source .venv/bin/activate`, or `.\.venv\Scripts\Activate.ps1` on Windows).

> **Windows:** if the second `pip install` says *No matching distribution found for robotos_edge*, the Windows wheel is not in `labs/dist` yet: run `git pull` in the course folder and try again.

**Board check** (skip without a board):

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

**Gesture model for Lab 9.5.** Lab 9.5 needs a trained gesture model at `labs/python/imu_artifacts/model_int8.tflite`. There are two ways to get one.

**A. Quick: a synthetic model** (about 1 minute, no board needed):

```bash
robotos-kws train-imu --synthetic --out imu_artifacts
```

- **What it does:** it makes up 800 practice gestures from formulas for 8 imaginary people (shake = a fast 6 Hz side-to-side wave, circle = a 1.5 Hz circle, lift = one slow up-and-down, idle = a tiny drift). It then trains a small neural network on them: a 1-D CNN with about 1,800 parameters.
- **What it prints:** a test accuracy and a confusion matrix. Expect about 100 %. That score is measured on more made-up gestures, so it says nothing about real motion.
- **What it saves in `imu_artifacts/`:** `model_int8.tflite` (the model the lab uses: 8-bit numbers, about 10 KB, small enough for a microcontroller), plus the same model as `model_float.tflite` and `model.keras`, and its settings in `meta.json`.

**B. Better: train on your own recordings** (needs a ws28p, about 10 minutes):

```bash
robotos-kws collect-imu --person yourname --takes 10
robotos-kws train-imu --data imu_dataset --out imu_artifacts
```

- **`collect-imu`** asks for each gesture in turn (idle, shake, circle, lift) and records it `--takes` times: press **Enter**, then perform the gesture for 2 seconds. Each take is saved as `imu_dataset/<gesture>/s01_yourname_ws28p_<n>.csv` (100 samples × 6 channels). A take that lost too many samples is recorded again.
- **`train-imu --data imu_dataset`** trains the same network on your recordings instead of the formulas. With only one person it warns and splits the data per gesture. That is fine; recordings from more people give a model that works for more people.

> **Synthetic vs. your own model.** The synthetic model has only seen idealised formulas. On a real ws28p it can misread gestures: in our test a shake was reported as `circle` again and again. If that happens, it is a lesson in itself: a model only knows the data it was trained on. Try way B and compare.

> The board's screen holds **3 pages** of your own (plus its built-in HOST tab). Each lab reuses its page name (METER, CHARTS, MODEL), so re-running a lab never adds pages.

---

## 2. Options every lab takes

| Option | Meaning | Example |
|---|---|---|
| *(none)* | live: use the board that is plugged in | `python lab9_1_….py` |
| `--replay` | no ws28p: play the recorded motion in `samples/` (idle, shake, circle, lift) instead | `… --replay` |
| `--replay FILE …` | play your own recording(s) instead, e.g. a take from `collect-imu` | `… --replay imu_dataset/shake/s01_yourname_ws28p_0000.csv` |
| `--seconds N` | stop after N seconds (each lab has its own default) | `… --seconds 10` |
| `--port PORT` | use this serial port instead of finding the board automatically (two boards plugged in, or detection fails; see `robotos detect`) | `… --port COM5` · `… --port /dev/cu.usbmodem101` |
| `--help` | print the lab's options and exit | `… --help` |

Stop any lab with **Ctrl+C**.

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
python lab9_2_frequency.py --replay imu_dataset/shake/s01_yourname_ws28p_0000.csv   # your own take (Setup, model B)
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
| `No matching distribution found for numpy>=1.26` (or tensorflow) when installing `robotos_edge` | The libraries were not installed first. Run the whole line from Setup: `pip install -r requirements.txt; pip install -U --no-index -f ../dist robotos_edge` |
| `ModuleNotFoundError: robotos_edge` | Activate the `.venv` in `labs/python` first (Setup) |
| `AttributeError: … has no attribute 'Display'` / `'ImuStream'` | Old wheel: `pip install -U --no-index -f ../dist robotos_edge` |
| `could not create page … (rc=-12)` | The screen's 3 page slots are full: re-run a lab (it reuses its page) or press RESET on the board |
| `no IMU samples …` | Not a ws28p (or wrong firmware): use `--replay`, or `robotos flash-firmware --board ws28p` |
| Nothing appears on the screen | Tap the lab's tab (METER / CHARTS / MODEL) at the top of the screen |
| `imu_artifacts/model_int8.tflite not found` | `robotos-kws train-imu --synthetic --out imu_artifacts` |
| Plots don't open (Lab 9.1/9.2) | `pip install -r requirements.txt` (matplotlib) |

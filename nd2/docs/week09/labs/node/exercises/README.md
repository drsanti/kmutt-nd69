# Week 09 Exercises (optional)

![track](https://img.shields.io/badge/track-ND02-1d4ed8?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-exercises-2e8b57?style=flat-square)

[Labs guide](../../README.md) · [Week 09 index](../../../README.md)

This folder is **separate from the demos**. The demos in the folder above are complete, working programs. Here are the same five labs as **exercises**: in each file, three parts of the code are left out and marked `TODO 1`, `TODO 2`, `TODO 3`. Each file still runs before you change anything; it just shows less (for example only one chart line, or a bubble that does not move) until you write the missing code.

Use the same setup as the demos: run `npm install` once in `labs/node` (see the labs guide, Setup). The exercises use its `node_modules`.

```bash
cd nd2/docs/week09/labs/node/exercises
npx tsx lab9_4_live_charts.ts --replay
```

When a script starts, it prints its tasks and what the unfinished version shows. All options work as in the demos (`--replay`, `--seconds`, `--port`, `--help`).

**Stuck?** The demo with the same file name in the folder above (`../lab9_….ts`) is the complete answer. Compare it with your file.

## The tasks

### Lab 9.1 — Time domain

`lab9_1_time_domain.ts`

| TODO | Task |
|---|---|
| 1 | Compute \|a\| = √(ax² + ay² + az²) for every sample |
| 2 | Estimate the sample rate from the timestamps |
| 3 | Find which axis points along gravity |

### Lab 9.2 — Frequency domain

`lab9_2_frequency.ts`

| TODO | Task |
|---|---|
| 1 | Remove the mean (gravity, 0 Hz) and take the magnitude of the FFT (`rk.dsp.rfft`, `rk.dsp.abs`) |
| 2 | Build the frequency axis; the last bin must be 25 Hz |
| 3 | Find the dominant frequency (ignore bin 0) |

### Lab 9.3 — Drawing on the device

`lab9_3_display_basics.ts`

| TODO | Task |
|---|---|
| 1 | Draw the static parts once: title, frame, scale |
| 2 | Convert \|a\| (0–30 m/s²) to a bar width (0–300 px) |
| 3 | The starter **flickers**. Fix it: draw only the part of the bar that changed |

### Lab 9.4 — Live charts on the device

`lab9_4_live_charts.ts`

| TODO | Task |
|---|---|
| 1 | Create a `StripChart` with three traces (ax red, ay green, az blue), range −20…20 m/s² |
| 2 | Convert tilt (ax/g, ay/g) into the bubble's position inside the dial |
| 3 | The starter leaves a **trail** of bubbles. Erase only the old bubble before drawing the new one |

### Lab 9.5 — Seeing the model

`lab9_5_model_view.ts`

| TODO | Task |
|---|---|
| 1 | Send every IMU sample to the service (`model.push`) |
| 2 | Draw the bars with the threshold line; highlight a detected gesture (not idle, above the threshold) |
| 3 | A tap inside the bars sets the threshold (top = 1.0, bottom = 0.0) |

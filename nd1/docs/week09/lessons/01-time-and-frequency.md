# Lesson 01 — Time and frequency: reading an IMU signal

![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-lesson-2e8b57?style=flat-square)

[Week 09 index](../README.md) · [Labs](../labs/README.md) · Next: [02 — Drawing on a device](02-drawing-on-a-device.md)

## 1. What the ws28p sends

The QMI8658 IMU is sampled **50 times per second**. Each sample has 6 numbers:

| Channel | Unit | Still on a desk |
|---|---|---|
| `ax, ay, az` | m/s² | about (0, 0, ±9.81): gravity on the axis that points up or down |
| `gx, gy, gz` | rad/s | about (0, 0, 0) plus a little noise |

An accelerometer cannot tell gravity from motion: a board at rest measures **1 g** (9.81 m/s²). That is why the magnitude

$$|a| = \sqrt{a_x^2 + a_y^2 + a_z^2}$$

is useful: it stays near 9.81 **whatever the orientation**, and moves away from it only when the board accelerates. During `lift` it rises above 9.81 while you push up and falls below it while the board slows down.

**Sample period:** 1 / 50 Hz = **20 ms**. The board stamps each sample with its own clock, so a missing timestamp step means a **lost** sample (USB busy, a slow script) — `ImuStream.lost` counts them.

## 2. From time to frequency

A 2 s window holds **N = 100** samples. The FFT turns it into 51 frequency bins:

- **Resolution** = 1 / window length = 1 / 2 s = **0.5 Hz** per bin. A longer window gives finer resolution but reacts more slowly.
- **Nyquist limit** = sample rate / 2 = **25 Hz**. Anything faster cannot be represented; a 40 Hz vibration folds back (aliases) and appears at 50 − 40 = **10 Hz**. Filter before you sample, or sample faster.
- **Bin 0** is the average (DC) — for |a| that is gravity. Remove the mean first, or bin 0 dominates the plot.

```python
mag   = np.abs(np.fft.rfft(a_mag - a_mag.mean()))
freqs = np.fft.rfftfreq(len(a_mag), d=1 / 50)       # 0, 0.5, 1.0, ... 25.0 Hz
```

**Why |a| doubles the frequency.** A side-to-side shake makes `ax` swing + and − at, say, 5.75 Hz. |a| is a magnitude, so both the + and the − swing push it up: it peaks **twice per cycle**, at 11.5 Hz. Use a single axis when you need the true motion frequency.

## 3. What the gesture model sees

The model from Week 08 receives one 2 s window: **100 samples × 6 channels**, normalised (accel ÷ 1 g, gyro ÷ 4 rad/s). Drawing it as an image (time → x, channel → y, value → colour) shows the "fingerprint" of each gesture: `shake` is a regular stripe pattern on `ax` and `gz`, `lift` a slow dip on `az`, `idle` almost flat. If two gestures look alike in this picture, the model will confuse them too.

## Check yourself

1. The board lies flat, screen up. Which accel axis reads about ±9.81, and what does |a| read?
2. A 3 s window at 50 Hz: how many samples, how many FFT bins, and what resolution?
3. Why can a 50 Hz IMU never measure a 30 Hz vibration correctly?

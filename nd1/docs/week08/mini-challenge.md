# Week 08 mini challenge → Mini-Project 2

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Schedule](../../../Schedule/ND1.md)

This challenge is the starting point for **Mini-Project 2** (self-study, 5 December 2026), which you bring to the onsite workshop on 12 December.

## The challenge: your own Edge AI command set

Build a keyword spotter on the ES3C28P (or an IMU gesture classifier on the ws28p) with **your own vocabulary**.

### Minimum (everyone, PC-only is fine)

1. Choose 3–4 command words that suit a device you care about (for example `play`, `stop`, `next` for a music box, or `fan`, `light`, `off`). In `robotos_edge` 0.2.0 the four keyword slots are named `red`, `green`, `blue`, `off`: record **your** word into a slot (say "play" while collecting `--labels red`), then rename the slots in your app and in `show_label()` of the `kws-inference` firmware. Write your slot mapping in your report.
2. Record at least **50 clips per word** from **at least 3 sessions**, plus `_silence_` and `_unknown_` (include words that sound like your commands).
3. Train, then report from `robotos-kws evaluate`:
   - float32 and int8 test accuracy and the drop in percentage points
   - the confusion matrix, with one sentence on the worst row
   - model size in KB
4. Show a live demo with `robotos-kws live-board` (or `robotos-kws live-pc` without a board) and count false triggers during 60 s of normal talking.

### Board level (if you have a board)

5. Record at least one full session with the **board** microphone (`robotos-kws collect-board`, workshop firmware) and report board-only test accuracy (`--device board`).
6. Host-side action: extend `robotos-kws live-board` so a detected word sends a command back to the board over the same wire protocol (for example an LED colour with `MSG_LED_FX` `0x8e`, as in the workshop LED labs). The board keeps the workshop firmware.
7. Advanced (ESP-IDF): run `robotos-kws verify-c` (must print `MATCH`), export, flash `kws-inference`, match the input level (Lesson 05), and fill in the latency table. **Reflash the workshop firmware afterwards** (`python -m esptool write-flash "@flash_args"`).
8. Make each command do something visible: LED colours, a message on the display, or a sound through the speaker (amplifier enable GPIO1 is active-low).

### IMU track (ws28p)

- Minimum: 4 gestures (your own or the defaults), at least 3 people, `robotos-kws train-imu` report with the person-disjoint confusion matrix, and a live demo with `robotos-kws live-imu`.
- Host-side action: a detected gesture sends `SfxCmd` (`0x84`) to play a sound on the ws28p, like workshop lab ex21 — but triggered by your model instead of a threshold.
- **On-device IMU challenge (advanced):** write an ESP-IDF app for the ws28p that reads the QMI8658 at 50 Hz (±4 g, ±512 °/s, same units as the workshop firmware), keeps a 2 s ring buffer, applies `robotos_edge.imu.features.normalise()` in C, and runs `model_int8.tflite` with TFLite Micro (ops: CONV_2D, EXPAND_DIMS, RESHAPE, MAX_POOL_2D, MEAN, FULLY_CONNECTED, SOFTMAX). Reuse the task/queue/arena design of `kws-inference`. Prove it matches: feed one recorded CSV window through both Python and C and compare the scores. Reflash the workshop firmware afterwards.

### Stretch goals (pick any)

- Shrink the model (`--width 16`) and the arena until accuracy drops by more than 2 points; report the trade-off.
- Two-stage wake-up: a wake word must come before a command.
- Combine tracks: an IMU gesture on the ws28p selects a mode and a keyword on the ES3C28P confirms it (two boards, one host script).
- Log every detection with its score to the microSD card for later retraining (Week 02, Lesson 12).

## Deliverable for Mini-Project 2

A public GitHub repository (as in Mini-Project 1) with:

- `README.md`: the problem, your vocabulary, data counts per label/device/session, and results (the `report.md` tables and the latency table)
- your scripts or notebook changes, and the exported firmware files (`model_data.cc`, `kws_labels.h`, `kws_config.h`)
- a short video or GIF of the demo
- **no** raw voice recordings of other people unless they agreed; you may share only your own clips, or only the trained model

## Assessment hints

| Criterion | What good looks like |
|---|---|
| Data | Balanced, several sessions/speakers, honest group split, hard `_unknown_` examples |
| Testing | Confusion matrix read and explained; board-only number reported if you have a board |
| Deployment | Live test with the board; if on-device: same features (verified), input level matched, latency measured, no dropped blocks |
| Engineering | Clear README, reproducible commands, limits stated honestly |

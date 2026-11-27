# Week 08 mini challenge — your own Edge AI command set

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Schedule](../../../Schedule/ND1.md)

> **Optional.** Try it during the session or afterwards, at your own pace. Nothing is handed in or scored; it is a way to practise what the labs showed.

Build a keyword spotter on the ES3C28P (or an IMU gesture classifier on the ws28p) with **your own vocabulary**.

## Start here (PC-only is fine)

1. Choose 3–4 command words that suit a device you care about (for example `play`, `stop`, `next` for a music box, or `fan`, `light`, `off`). In `robotos_edge` the four keyword slots are named `red`, `green`, `blue`, `off`: record **your** word into a slot (say "play" while collecting `--labels red`), then rename the slots in your app and in `show_label()` of the `kws-inference` firmware. Write your slot mapping down so you remember which word is which.
2. Record at least **50 clips per word** from **at least 3 sessions**, plus `_silence_` and `_unknown_` (include words that sound like your commands).
3. Train, then read `robotos-kws evaluate`:
   - float32 and int8 test accuracy, and how many percentage points int8 loses
   - the confusion matrix: which row is worst, and why?
   - model size in KB
4. Try it live with `robotos-kws live-board` (or `robotos-kws live-pc` without a board) and count false triggers during 60 s of normal talking.

## Board level (if you have a board)

5. Record at least one full session with the **board** microphone (`robotos-kws collect-board`, workshop firmware) and check the board-only test accuracy (`--device board`).
6. Host-side action: extend `robotos-kws live-board` so a detected word sends a command back to the board over the same wire protocol (for example an LED colour with `MSG_LED_FX` `0x8e`, as in the workshop LED labs). The board keeps the workshop firmware.
7. Advanced (ESP-IDF): run `robotos-kws verify-c` (must print `MATCH`), export, flash `kws-inference`, match the input level (Lesson 05), and fill in the latency table. **Reflash the workshop firmware afterwards** (`python -m esptool write-flash "@flash_args"`).
8. Make each command do something visible: LED colours, a message on the display, or a sound through the speaker (amplifier enable GPIO1 is active-low).

## IMU track (ws28p)

- Start here: 4 gestures (your own or the defaults), at least 3 people, the `robotos-kws train-imu` results with the person-disjoint confusion matrix, and a live test with `robotos-kws live-imu`.
- Host-side action: a detected gesture sends `SfxCmd` (`0x84`) to play a sound on the ws28p, like workshop lab ex21 — but triggered by your model instead of a threshold.
- **On-device IMU challenge (advanced):** write an ESP-IDF app for the ws28p that reads the QMI8658 at 50 Hz (±4 g, ±512 °/s, same units as the workshop firmware), keeps a 2 s ring buffer, applies `robotos_edge.imu.features.normalise()` in C, and runs `model_int8.tflite` with TFLite Micro (ops: CONV_2D, EXPAND_DIMS, RESHAPE, MAX_POOL_2D, MEAN, FULLY_CONNECTED, SOFTMAX). Reuse the task/queue/arena design of `kws-inference`. Prove it matches: feed one recorded CSV window through both Python and C and compare the scores. Reflash the workshop firmware afterwards.

## Stretch goals (pick any)

- Shrink the model (`--width 16`) and the arena until accuracy drops by more than 2 points; note the trade-off.
- Two-stage wake-up: a wake word must come before a command.
- Combine tracks: an IMU gesture on the ws28p selects a mode and a keyword on the ES3C28P confirms it (two boards, one host script).
- Log every detection with its score to the microSD card for later retraining (Week 02, Lesson 12).

## Check your result

| Ask yourself | What good looks like |
|---|---|
| Data | Balanced, several sessions/speakers, honest group split, hard `_unknown_` examples |
| Testing | You can explain the confusion matrix; you know the board-only number if you have a board |
| Deployment | It works live on the board; if on-device: same features (verified), input level matched, latency measured, no dropped blocks |
| Engineering | You could repeat it from your own notes: clear commands, limits written down honestly |

Want to share it? A short video or GIF of the demo is a nice way to show the group. Share only your own voice clips (or only the trained model), never other people's recordings without their agreement.

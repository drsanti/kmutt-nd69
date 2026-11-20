# Week 08 mini challenge → Mini-Project 2

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-challenge-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Schedule](../../../Schedule/ND1.md)

This challenge is the starting point for **Mini-Project 2** (self-study, 5 December 2026), which you bring to the onsite workshop on 12 December.

## The challenge: your own Edge AI command set

Build a keyword spotter (or a gesture classifier) that controls something on the ES3C28P with **your own vocabulary**.

### Minimum (everyone, PC-only is fine)

1. Choose 3–4 command words that suit a device you care about (for example `play`, `stop`, `next` for a music box, or `fan`, `light`, `off`). Edit `KEYWORDS` in `kws_common.py`.
2. Record at least **50 clips per word** from **at least 3 sessions**, plus `_silence_` and `_unknown_` (include words that sound like your commands).
3. Train, then report from `evaluate.py`:
   - float32 and int8 test accuracy and the drop in percentage points
   - the confusion matrix, with one sentence on the worst row
   - model size in KB
4. Show a live demo with `live_infer_pc.py` and count false triggers during 60 s of normal talking.

### Board level (if you have a board)

5. Record at least one full session with the **board** microphone and report board-only test accuracy (`--device board`).
6. Run `verify_c_features.py` on your clips (it must print `MATCH`).
7. Export, flash `kws-inference`, and fill in the latency table from Lesson 05.
8. Make each command do something visible: LED colours, a message on the display, or a sound through the speaker (amplifier enable GPIO1 is active-low).

### Stretch goals (pick any)

- Shrink the model (`--width 16`) and the arena until accuracy drops by more than 2 points; report the trade-off.
- Two-stage wake-up: a wake word must come before a command.
- Combine tracks: a touch gesture selects a mode and a keyword confirms it.
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
| Deployment | Same features on PC and board (verified), latency measured, no dropped blocks |
| Engineering | Clear README, reproducible commands, limits stated honestly |

# Instructor route — 09:00–12:00

Use the course's existing timetable. The 85 slides include reference material; do not lecture through all of it before the labs. Let learners predict, manipulate a demonstration, run the complete Python script, then explain one result. The optional challenge is not graded and has no required submission.

| Time | Suggested core route | Ask and observe |
|---|---|---|
| 09:00–09:20 | 1–7, 9–10, 12, 14–15 | Identify board type and interpreter; detect the board; choose a valid replay/live path. Explain the host/MCU boundary before running anything. |
| 09:20–09:50 | 16–18, 20, 23, 25–27 | Tilt while still, then accelerate. Predict which axes change and what magnitude alone cannot establish. Run Lab 9.1 and inspect rate/lost/noise. |
| 09:50–10:20 | 28–31, 34, 36, 38–41 | Predict DC and peaks, vary duration, show 40→10 Hz aliasing. Compare the bundled shake's ax rhythm with its magnitude spectrum. Run Lab 9.2. |
| 10:20–10:30 | Break | Leave the all-slides view available for self-study. |
| 10:30–11:00 | 42, 44, 46–50, 52, 54 | Predict a rectangle before drawing. Compute the full-frame byte count. Show shrinking and colour-changing bars. Run the meter; inspect stats. |
| 11:00–11:30 | 55–56, 59, 62, 64, 66 | Predict sweep duration. Tilt then shake; explain why a level is unreliable during dynamic acceleration. Run Lab 9.4; separate acquisition loss from chart drops. |
| 11:30–12:00 | 67, 70, 74–75, 78–81, 82–85 | Show idle winning despite a low threshold. Vary threshold on a fixed labelled set, then run Lab 9.5. Discuss synthetic-to-real mismatch. Introduce the optional challenge. |

Prepare the Python environment and model before class when possible. First-time TensorFlow downloads can take much of the setup block. Open the offline HTML in a browser, check fullscreen, and keep the lab terminal ready in `nd1/docs/week09/labs/python`. If hardware is unavailable, use Labs 9.1/9.2 replay and the deck's display simulations. Do not describe the simulations as a successful hardware test.

## Discussion prompts

- **Sampling:** does a good median rate prove there were no missing samples? No; examine timestamp gaps and `lost` too.
- **FFT:** does the largest bin of idle noise prove a meaningful vibration? No; interpret amplitude, repeatability and context.
- **Graphics:** why can a 50-pixel erase be cheaper than a new frame? It encodes one small operation and touches less screen area. Pixel count alone is not wire payload.
- **Charts:** why can a 50 Hz sensor use 10 chart batches/s? Batch five new samples, preserving acquisition rate.
- **Level:** why show both axis clipping and radial limiting? Axis clipping matches this lab; radial limiting is a clearly labelled extension for arbitrary dynamic input.
- **Model:** why can an orange bar fail to increment a counter? Highlight uses the current score rule; accepted events also use warm-up, smoothing and a refractory interval.
- **Evaluation:** why is this matrix not model accuracy? It uses invented labelled scores. Real performance needs independently labelled trials and an agreed trial/event definition.

## Checkpoint answer guide

1. `sqrt(4.1²+8.9²)≈9.80 m/s²`: consistent with a tilted stationary board, but magnitude alone cannot prove stillness.
2. Two samples missing: 1.060 and 1.080 s.
3. A 2 s, 50 Hz window has 0.5 Hz bins and a 25 Hz Nyquist limit.
4. A mostly sideways 6 Hz shake can put a magnitude peak near 12 Hz because both signs increase magnitude. This is not a universal rule for all motion axes.
5. Removing the mean suppresses DC, making variation visible; it does not remove all gravity-related effects or noise.
6. `320×240×2=153,600` pixel bytes per full RGB565 frame, before transport overhead.
7. Erase/redraw can span a screen refresh. Keep previous state and update the changed region; repaint on a colour change.
8. A higher threshold generally reduces accepted events and increases misses. Precision may improve, but is not guaranteed to increase monotonically on every dataset; recall cannot increase for the fixed binary score demo.

For an emergency-stop discussion, ask about missed-action cost, accidental activation and independent validation. An illustrative threshold slider does not establish a safe operating threshold.

## Mini challenge review

Have learners sketch one body-only layout with at least three views, one tap action and partial updates. Ask for a live 60 s measurement with hardware/firmware/source mode, display update rate (target ≥8/s), commands per update and IMU loss. A browser frame rate or `d.stats['commands'] / seconds` alone does not measure full dashboard updates. The gesture model is not a machine-condition model without appropriate new data and validation.

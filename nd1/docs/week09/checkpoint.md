# Week 09 Self-Check

![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-09-334155?style=flat-square)
![kind](https://img.shields.io/badge/kind-self--check-2e8b57?style=flat-square)

[Week 09 index](README.md)

For you, not for a grade: try each question in your head or on paper, then open **Answer** to check.

**1.** The ws28p lies still at an angle. ax = 4.1, ay = 0.0, az = −8.9 m/s². What is |a|, and is the board moving?
<details><summary>Answer</summary>|a| = √(4.1² + 8.9²) ≈ 9.80 m/s² ≈ 1 g, so it is still — the tilt only moves gravity between axes.</details>

**2.** Timestamps go 1.000, 1.020, 1.040, 1.100 s at 50 Hz. How many samples were lost?
<details><summary>Answer</summary>Two: after 1.040 the next samples should be 1.060 and 1.080.</details>

**3.** A 2 s window at 50 Hz: frequency resolution and highest frequency?
<details><summary>Answer</summary>0.5 Hz per bin; 25 Hz (Nyquist = 50 / 2).</details>

**4.** A shake moves the hand at 6 Hz. Where does the |a| spectrum peak, and why?
<details><summary>Answer</summary>Near 12 Hz: |a| is a magnitude, so both directions of each swing raise it — two peaks per cycle.</details>

**5.** Why remove the mean before the FFT of |a|?
<details><summary>Answer</summary>The mean (gravity, ~9.81) lands in bin 0 and dwarfs the motion; removing it shows the motion's frequencies.</details>

**6.** How many bytes is a full 320 × 240 RGB565 frame?
<details><summary>Answer</summary>320 × 240 × 2 = 153,600 bytes.</details>

**7.** Your bar chart blinks every update. What is the cause, and the fix?
<details><summary>Answer</summary>It clears the area and then redraws, and the screen can refresh in between. Draw only what changed (grow → paint the new part, shrink → erase the extra part) and never clear what you are about to redraw.</details>

**8.** Raising the detection threshold from 0.5 to 0.9 — what improves and what gets worse?
<details><summary>Answer</summary>Fewer false detections (more precise), but more missed gestures (lower recall); the user must perform the gesture more clearly.</details>

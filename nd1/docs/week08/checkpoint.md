# Week 08 checkpoint quiz

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-quiz-2e8b57?style=flat-square)

[Week 08 index](README.md) · [Lessons](lessons/README.md)

Twelve questions, about 12 minutes. Answers are at the bottom; try first.

1. Put these stages in order: quantize, collect, deploy, train, test.
2. A dataset has 400 `red` clips and 40 clips for each other label. What will a naive model learn, and name two fixes.
3. One student recorded all clips alone in one session. Why does a random clip split give a misleading test score?
4. Why does the dataset need a `_silence_` class and an `_unknown_` class?
5. How many frames does a 1 s clip at 16 kHz give with a 480-sample window and a 320-sample hop?
6. A 3 × 3 depthwise-separable layer maps 32 channels to 32 channels. How many weights does it have (no bias)? How many would a normal 3 × 3 convolution need?
7. What does the representative dataset do during int8 conversion, and what happens if it contains only quiet PC clips?
8. A model trained only on laptop-microphone clips scores 95% on PC test clips and 60% on board clips. What is this effect called, and give two ways to reduce it.
9. In `kws-inference`, why is the capture task's priority higher than the inference task's, and why does it call `xQueueSend` with a timeout of 0?
10. Secure boot is enabled but flash encryption is not. Can someone copy your model from the board? Can they run their own modified firmware?
11. `collect.py` receives `MicPcm` frames with `seq` 200, 201, 203. What happened, and what does the script do with that take? Why is `seq` compared modulo 256?
12. You plug a ws28p into `collect.py`. How does the script know it is the wrong board, and what does `0x3c` mean?

---

<details>
<summary>Answers</summary>

1. Collect → train → test → quantize → (re-test) → deploy.
2. It learns to favour `red` (high accuracy, poor recall for the other labels). Fixes: record more of the small classes, use class weights (as `train.py` does), downsample `red`, augment the small classes.
3. Clips from the same speaker and session are near-duplicates. Some end up in training and some in test, so the test measures memorisation. Split by speaker or session.
4. Without them, every sound is forced into a keyword: noise and other words cause false triggers. `_silence_` = nothing happened, `_unknown_` = speech that is not a command.
5. 1 + (16000 − 480) / 320 = 1 + 48.5 → **49** (the last partial frame is dropped).
6. Depthwise 3·3·32 = 288 plus pointwise 32·32 = 1,024 → **1,312**. A normal convolution needs 3·3·32·32 = **9,216**.
7. It provides realistic inputs so the converter can choose a scale and zero point for every activation tensor. With only quiet clips, the ranges are too small: loud board audio saturates at −128/127 and accuracy drops.
8. Domain shift. Mix PC and board clips, augment gain/noise, turn off OS audio processing, and always test on board-recorded clips.
9. Audio arrives in real time and DMA buffers are small; capture must never be delayed by the heavy FFT/inference work. A zero timeout means that if the consumer falls behind, the block is counted as dropped instead of blocking the capture loop (and losing even more audio).
10. **Yes**, they can read the flash and copy the model, because nothing hides it. **No**, they cannot run modified firmware, because its signature would fail verification.
11. One chunk (seq 202, up to 240 samples = 15 ms) was lost on USB. The take would contain a hole, so `collect.py` discards it and records it again (`live_infer_board.py` fills the gap with silence instead, to keep timing). The prebuilt firmware counts `MicPcm.seq` with an 8-bit counter, so after 255 comes 0.
12. It reads `BoardInfo.caps`: `0x3c` = IMU (0x04) + RTC (0x08) + BATT (0x10) + BTN (0x20) — no MIC bit (0x02). (If `BoardInfo` has not arrived yet, a stream of `Imu` frames also gives it away.) The ES3C28P reports `0x33` = LED + MIC + BATT + BTN.

</details>

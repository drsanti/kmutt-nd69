# Lesson 02 — Data Collection: Board Mic, PC Mic, and Dataset Hygiene

> Week 08 · ES3C28P / ESP32-S3 · 09:15–09:50

[Lesson index](README.md) · [Previous: Lesson 01](01-edge-ai-pipeline.md) · [Next: Lesson 03](03-features-and-model.md)

## Learning objectives

Read the board's microphone stream from Python using the hardware-interface-workshop wire protocol, record labelled one-second clips from the board and from a computer microphone, organise them in one dataset layout, and avoid the dataset mistakes that make a model look better than it is.

## The task: four keywords plus two "everything else" classes

| Label | What to record | Why it exists |
|---|---|---|
| `red`, `green`, `blue`, `off` | The keyword, once per clip | The commands we want |
| `_silence_` | Room noise, fan, keyboard, no speech | So the model can say "nothing happened" |
| `_unknown_` | Other words: "bread", "seen", "glue", "of", names, numbers | So the model does not force every sound into a keyword |

Without `_silence_` and `_unknown_`, a classifier always picks one of the four keywords — even for a cough. Choose `_unknown_` words that **sound similar** to the keywords; those are the hard negatives that teach the model where the boundary is.

The four keyword slots are fixed in `robotos_edge` (`red`, `green`, `blue`, `off`). To use your own words, record each word into one slot (say "play" while collecting `--labels red`) and rename the slots in your application (and in `show_label()` of the `kws-inference` firmware if you run the model on the board).

## One dataset layout for every source

```text
dataset/
├── red/        s01_alice_board_0000.wav  s01_alice_pc_0000.wav  s02_bob_board_0003.wav ...
├── green/
├── blue/
├── off/
├── _silence_/
└── _unknown_/

file name = <session>_<speaker>_<device>_<index>.wav     (16 kHz, mono, 16-bit, exactly 1.0 s)
```

> [!NOTE]
> **Clip Length & Quality Checks:**
> - Every saved clip is trimmed to exactly **1.0 s** (`CLIP_SAMPLES = 16000` in `robotos_edge.audio.features`), centered on speech energy from a 1.5 s raw record window (`--seconds 1.5`).
> - Takes that are too quiet (speech RMS < −40 dBFS) or clip (peak ≥ 32,000) are automatically discarded and retried.
> - The 1.0 s clip length is built into the `robotos_edge` wheel and the firmware (`kws_features.h`); keep it as is.

The file name carries the metadata that `robotos-kws train` and `robotos-kws evaluate` need:

- **session** (`s01`, `s02`, …): a new room, day, or setup starts a new session
- **speaker**: who spoke (letters, digits, `-`)
- **device**: `board` or `pc` — used to measure domain shift

## Path A — the board microphone (main lab)

Your ES3C28P still runs the **workshop prebuilt firmware** (`firmware-prebuilt/es3c28p`, flashed with `esptool`). It already knows how to stream microphone audio over USB — that is what the workshop's ex28 recorder and ex30/ex32 feature and classifier labs use. `robotos-kws collect-board` is a Python version of that same host code.

```text
MEMS mic ─► ES8311 ADC ─I2S─► ESP32-S3 (prebuilt firmware)                  ─USB─► robotos-kws collect-board ─► dataset/
                               40 Hz high-pass ─► 6.5 kHz low-pass ─► soft limiter
                               ─► AudioLevel (~10/s) and MicPcm chunks (16 kHz int16, ≤240 samples)
```

1. **Close the browser tab** that runs the workshop demos (Web Serial) and any serial monitor. Only one program can own the port.

2. Check the board and the level:

   ```bash
   cd nd1/docs/week08/labs/python
   robotos detect                          # auto-detect board port, model & handshake
   robotos-kws check-board --gain 80      # speak while it runs (port is auto-detected!)
   ```

   `--info` prints the `BoardInfo` line (model, firmware, capabilities), a live level meter from the board's `AudioLevel` messages, and a 1-second test stream. Speech should peak around −20 to −6 dBFS (peak amplitude 4,000 to 15,000, speech RMS −26 to −18 dBFS). If it clips, use `--gain 50`; if it is very quiet (< −38 dBFS), use `--gain 80` or `--gain 85`.

3. Record (keep the same `--gain` you found):

   ```bash
   robotos-kws collect-board --port COM5 --speaker alice --session s01 --gain 80 --takes 20
   robotos-kws collect-board --port COM5 --speaker alice --session s01 --gain 80 --labels _silence_ --takes 30 --no-prompt
   robotos-kws collect-board --port COM5 --speaker alice --session s01 --gain 80 --labels _unknown_ --takes 30
   ```

   macOS: `--port /dev/cu.usbmodem…`; Linux: `--port /dev/ttyACM0`.

### What `robotos-kws collect-board` does on the wire

Every message is one frame (the same format as the workshop's `lib/wire/frame.ts`; Python version in `robotos_edge.hardware.wire`):

```text
0x00 | COBS( msg_type u8 | seq u16 LE | len u16 LE | protobuf payload | CRC-16/XMODEM LE ) | 0x00
```

| Step | Direction | Message |
|---|---|---|
| Open the port, wait 2.5 s | — | Opening USB can reset the board; boot log text is skipped (it is outside the 0x00 delimiters or fails the CRC) |
| Who are you? | board → host | `BoardInfo` (0x28): `hw_model`, `fw_version`, `caps`. Sent at boot and about every 10 s. `caps` must include MIC (0x02) — ES3C28P reports `0x33`. A ws28p (`0x3c`, no mic) is rejected with a clear message |
| Mic on | host → board | `MicCmd` (0x86) `{enable: true, gain_pct: 60}` → board answers `CmdAck` (0x27) with `rc = 0` |
| Per take: stream on | host → board | `MicCmd {stream: true, enable: true}` → `CmdAck` |
| Audio | board → host | `MicPcm` (0x24) `{seq, samples[]}`: 16 kHz signed 16-bit, up to 240 samples (15 ms) per frame |
| Per take: stream off | host → board | `MicCmd {stream: false}` → `CmdAck` |

`robotos-kws collect-board` throws away the first 0.1 s after the stream starts (filters settling), gathers **1.5 s**, and keeps the **loudest 1.0 s** (`center_on_energy()`), so you do not need perfect timing.

**Lost data.** USB can drop a frame when the computer is busy. `MicPcm.seq` counts 0, 1, …, 255, 0, … (one step per chunk), so a jump means chunks are missing. A take with a gap would contain a click or a hole, so `robotos-kws collect-board` discards it and records it again. Frames that fail the CRC are dropped the same way.

**Sample rate.** The prebuilt firmware streams at 16 kHz, the rate the model uses. If a future firmware streams at another rate, pass `--board-rate` and the clip is resampled to 16 kHz before it is saved.

> [!TIP]
> The workshop's **ex28 mic recorder** page downloads a 16 kHz mono 16-bit WAV (up to 30 s). That format is exactly what `robotos-kws collect-pc --from-wav` slices, so a long recording made in the browser can become `_silence_` or `_unknown_` clips: `robotos-kws collect-pc --labels _silence_ --from-wav mic-….wav --takes 60`. Rename the device tag honestly if you do this (the audio came from the board, so treat it as board data when you evaluate).

The microphone gain and the firmware's filter chain are part of your data. Keep `--gain` the same for all your sessions, or record new data when you change it.

## Path B — the computer microphone

No board is required to start collecting training data! You can record directly using your PC or laptop microphone:

```bash
# 1. List input devices to identify your microphone index
robotos-kws collect-pc --list-devices
# Windows Git Bash: robotos-kws collect-pc --list-devices

# 2. Record 20 takes for all 4 keywords (red, green, blue, off):
robotos-kws collect-pc --speaker alice --session s01 --takes 20

# 3. Record only a single keyword (e.g. only "blue" or "red"):
robotos-kws collect-pc --speaker alice --session s01 --labels blue --takes 20

# 4. Use a specific microphone device from --list-devices (e.g. device 1):
robotos-kws collect-pc --speaker alice --session s01 --device 1 --labels blue --takes 20

# 5. Record background room noise (stay quiet, Enter key prompt disabled):
robotos-kws collect-pc --speaker alice --session s01 --labels _silence_ --takes 30 --no-prompt

# 6. Record out-of-vocabulary words for unknown negative class:
robotos-kws collect-pc --speaker alice --session s01 --labels _unknown_ --takes 30
```

`robotos-kws collect-pc` records audio at 16 kHz mono with `sounddevice` (default raw buffer `--seconds 1.5`), centers on the loudest speech energy to extract the exact 1.0 s clip, and saves `<session>_<speaker>_pc_<index>.wav` in the corresponding label folder.

> [!TIP]
> **Audio Quality Filters:**
> - If audio is clipped (peak amplitude ≥ 32,000) or too quiet (speech RMS < −40 dBFS for keywords; relaxed to < −52 dBFS for `_unknown_` to accept quiet/whispered speech), the take is automatically discarded and retried with an on-screen hint so flawed audio never enters your training set.
> - **Recording Duration:** The raw recording window defaults to `--seconds 1.5` before trimming down to the 1.0 s clip. To capture longer words or if extending clip length to 1.5 s (`CLIP_SAMPLES = 24000`), pass `--seconds 2.0`.

You can also slice an existing long WAV recording (for example 2 minutes of room noise for `_silence_`) without a live microphone:

```bash
robotos-kws collect-pc --speaker alice --session s01 --labels _silence_ --takes 60 --from-wav room_noise.wav
```

### PC mic: strengths and the domain-shift trap

| | PC microphone | Board microphone |
|---|---|---|
| Speed | Very fast, no cable | Fast too: no flashing, the workshop firmware streams audio |
| Who can do it | Everyone | Only students with a board |
| Signal path | Laptop mic + OS processing (AGC, noise suppression, echo cancel) | LMA2718B381 MEMS mic + ES8311 PGA + firmware 40 Hz high-pass, 6.5 kHz low-pass, soft limiter |
| Frequency response | Tuned for calls | Different curve, different noise floor |
| Gain | Automatic, often changing | Fixed (`robotos-kws collect-board --gain`, default 60 %) |

A model trained **only** on PC clips learns the PC's sound. On the board, the same word arrives with a different spectrum and level, so accuracy can drop sharply. This is **domain shift**.

What to do:

1. **Mix sources.** Train on PC and board clips together (the device tag lets you count them).
2. **Turn off OS effects** (noise suppression, voice isolation, automatic gain) while recording on the PC, if your OS allows it.
3. **Test on board data.** Run `robotos-kws evaluate --device board`. A board-only test score is the number that predicts real behaviour.
4. **Augment.** `robotos-kws train` adds random gain (±6 dB), time shift (±100 ms), and background noise, which makes the model less sensitive to the recording device.

> [!NOTE]
> Without a board you can still do everything up to and including the live PC test (`robotos-kws live-pc`). With a board, the live test is `robotos-kws live-board` (Lesson 04). Keep the device tag `pc` honest, so you know later which clips came from where.

## Dataset hygiene

| Rule | Why |
|---|---|
| **Balanced classes** (similar counts per label) | Otherwise the model learns "always say the big class" |
| **Many speakers** (voices, accents, distances) | A model trained on one voice learns that voice |
| **Several sessions** (rooms, times, noise levels) | Each room has its own echo and noise |
| **Listen to a sample** of every label | Wrong labels teach wrong answers; delete bad clips |
| **Never edit test clips after looking at results** | That leaks the test set into your decisions |
| **Split by group, not by clip** | See below |

### Splits without leakage

Clips from the same speaker in the same session are almost copies of each other. If one copy is in training and another is in the test set, the test score measures memory, not generalisation.

`robotos-kws train` therefore splits by **speaker** (when there are at least 3 speakers) or by **speaker + session** (when you recorded alone). It writes the split to `artifacts/splits.json`, and `robotos-kws evaluate` reuses it.

```text
train 70%  ─ speakers/sessions the model learns from
val   15%  ─ chooses when to stop training
test  15%  ─ touched once, at the end, for the score you report
```

If you recorded alone in one session, the script warns and falls back to a random split: the score will be optimistic. Record at least 2–3 sessions, or swap clips with classmates (with their consent; voice recordings are personal data).

### How much data?

For a classroom model: at least **50 clips per keyword** from at least 3 sessions, plus 100+ `_silence_` and 100+ `_unknown_`. More speakers matter more than more clips from the same speaker.

## Lab

1. Record 20 takes per keyword plus `_silence_` and `_unknown_` with **one** source (board or PC).
2. Record a second session in a different place or at a different distance.
3. If you have a board: record at least one session with each source.
4. Count your clips: `python -c "from robotos_edge.audio import features as kc; import collections; print(collections.Counter((c.label, c.device) for c in kc.scan_dataset('dataset')))"`

## Check your understanding

1. Why does the dataset need `_unknown_`, and which words make the best `_unknown_` clips?
2. You trained on PC clips and the board misses most keywords. Name two likely causes and two fixes.
3. Why is a random clip split misleading when one person recorded everything in one session?
4. What does `robotos-kws collect-board` do when `MicPcm.seq` jumps from 41 to 43, and why is that better than keeping the take?

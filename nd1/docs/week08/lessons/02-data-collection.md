# Lesson 02 — Data Collection: Board Mic, PC Mic, and Dataset Hygiene

> Week 08 · ES3C28P / ESP32-S3 · 09:20–09:50

[Lesson index](README.md) · [Previous: Lesson 01](01-edge-ai-pipeline.md) · [Next: Lesson 03](03-features-and-model.md)

## Learning objectives

Record labelled one-second clips from the board microphone and from a computer microphone, organise them in one dataset layout, and avoid the dataset mistakes that make a model look better than it is.

## The task: four keywords plus two "everything else" classes

| Label | What to record | Why it exists |
|---|---|---|
| `red`, `green`, `blue`, `off` | The keyword, once per clip | The commands we want |
| `_silence_` | Room noise, fan, keyboard, no speech | So the model can say "nothing happened" |
| `_unknown_` | Other words: "bread", "seen", "glue", "of", names, numbers | So the model does not force every sound into a keyword |

Without `_silence_` and `_unknown_`, a classifier always picks one of the four keywords — even for a cough. Choose `_unknown_` words that **sound similar** to the keywords; those are the hard negatives that teach the model where the boundary is.

To change the vocabulary, edit `KEYWORDS` in `labs/python/kws_common.py` (and `show_label()` in the firmware).

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

The file name carries the metadata that `train.py` and `evaluate.py` need:

- **session** (`s01`, `s02`, …): a new room, day, or setup starts a new session
- **speaker**: who spoke (letters, digits, `-`)
- **device**: `board` or `pc` — used to measure domain shift

## Path A — the board microphone (main lab)

The audio chain from [Week 02, Lesson 10](../../week02/lessons/EN/10-audio-chain.md):

```text
MEMS mic ──► ES8311 ADC + PGA ──I2S──► ESP32-S3 ──USB Serial/JTAG──► collect.py ──► dataset/
             I2C 0x18 SDA16/SCL15      DIN GPIO6, BCLK 5, WS 7, MCLK 4
```

1. Build and flash the logger (ESP-IDF v6.1 terminal, from the project folder):

   ```bash
   cd nd1/docs/week08/labs/firmware/audio-logger
   idf.py set-target esp32s3
   idf.py build flash        # add -p COM5 / -p /dev/ttyACM0 if needed
   ```

   Do **not** keep `idf.py monitor` open: only one program can own the serial port.

2. Check the link and find the microphone slot:

   ```bash
   cd ../../python
   python collect.py --port COM5 --ping
   python collect.py --port COM5 --info      # speak while it runs
   ```

   The ES8311 sends stereo I2S frames. `--info` prints the level of slot 0 and slot 1; the slot that rises when you speak is the microphone. If it is slot 1, set `MIC_SLOT 1` in `audio_logger_main.c` **and** `KWS_MIC_SLOT 1` in `kws_config.h`.

3. Record:

   ```bash
   python collect.py --port COM5 --speaker alice --session s01 --takes 20
   python collect.py --port COM5 --speaker alice --session s01 --labels _silence_ --takes 30 --no-prompt
   python collect.py --port COM5 --speaker alice --session s01 --labels _unknown_ --takes 30
   ```

### How the logger works

The host sends one byte, `r`. The firmware records **1.5 s** and sends one binary frame:

```text
"KWS1" | uint32 n_samples | uint32 sample_rate | int16 pcm[n_samples] | uint32 checksum
```

`collect.py` keeps the **loudest 1.0 s** (`center_on_energy()`), so you do not need perfect timing. The checksum catches lost bytes or log text that leaked into the stream; the script simply retries that take.

The microphone gain (`MIC_GAIN_DB`, 30 dB by default) is part of your data. If you change it, change it in **both** firmware projects and record new data.

## Path B — the computer microphone

```bash
python collect_pc_mic.py --list-devices
python collect_pc_mic.py --speaker alice --session s01 --takes 20
python collect_pc_mic.py --speaker alice --session s01 --labels _silence_ --takes 30 --no-prompt
python collect_pc_mic.py --speaker alice --session s01 --labels _unknown_ --takes 30
```

`collect_pc_mic.py` records 1.5 s at 16 kHz mono with `sounddevice`, keeps the loudest 1.0 s with the **same** function as `collect.py`, and saves `<session>_<speaker>_pc_<index>.wav` in the same folders. It warns when a clip is clipped or very quiet.

You can also slice a long recording (for example 2 minutes of room noise for `_silence_`) without a live microphone:

```bash
python collect_pc_mic.py --speaker alice --session s01 --labels _silence_ --takes 60 --from-wav room_noise.wav
```

### PC mic: strengths and the domain-shift trap

| | PC microphone | Board microphone |
|---|---|---|
| Speed | Very fast, no flashing, no cable | Slower to set up |
| Who can do it | Everyone | Only students with a board |
| Signal path | Laptop mic + OS processing (AGC, noise suppression, echo cancel) | LMA2718B381 MEMS mic + ES8311 PGA, no processing |
| Frequency response | Tuned for calls | Different curve, different noise floor |
| Gain | Automatic, often changing | Fixed (`MIC_GAIN_DB`) |

A model trained **only** on PC clips learns the PC's sound. On the board, the same word arrives with a different spectrum and level, so accuracy can drop sharply. This is **domain shift**.

What to do:

1. **Mix sources.** Train on PC and board clips together (the device tag lets you count them).
2. **Turn off OS effects** (noise suppression, voice isolation, automatic gain) while recording on the PC, if your OS allows it.
3. **Test on board data.** Run `evaluate.py --device board`. A board-only test score is the number that predicts real behaviour.
4. **Augment.** `train.py` adds random gain (±6 dB), time shift (±100 ms), and background noise, which makes the model less sensitive to the recording device.

> [!NOTE]
> Without a board you can still do everything up to and including the live PC test (`live_infer_pc.py`). Keep the device tag `pc` honest, so you know later which clips came from where.

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

`train.py` therefore splits by **speaker** (when there are at least 3 speakers) or by **speaker + session** (when you recorded alone). It writes the split to `artifacts/splits.json`, and `evaluate.py` reuses it.

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
4. Count your clips: `python -c "import kws_common as kc, collections; print(collections.Counter((c.label, c.device) for c in kc.scan_dataset('dataset')))"`

## Check your understanding

1. Why does the dataset need `_unknown_`, and which words make the best `_unknown_` clips?
2. You trained on PC clips and the board misses most keywords. Name two likely causes and two fixes.
3. Why is a random clip split misleading when one person recorded everything in one session?

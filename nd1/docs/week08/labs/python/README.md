# Week 08 Python tools

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lab-2e8b57?style=flat-square)

[Labs index](../README.md) · [Lessons](../../lessons/README.md)

## Install

> [!IMPORTANT]
> **Use Python 3.10 to 3.13 (Python 3.11 strongly recommended).**
> Avoid Python 3.14+ (TensorFlow has no pre-compiled wheels for Python 3.14+ on Windows or macOS).
> - **Windows:** If Python 3.11 is not installed (or `py -3.11` fails), install it in PowerShell via: `winget install Python.Python.3.11`
> - **macOS:** If `python3 --version` shows 3.14+, install Python 3.11 via Homebrew: `brew install python@3.11`
> - **Already created `.venv` with an incompatible version (like 3.14)? Delete and recreate it:**
>   - macOS/Linux: `deactivate && rm -rf .venv && python3.11 -m venv .venv && source .venv/bin/activate`
>   - Windows (PowerShell): `deactivate; Remove-Item -Recurse -Force .venv; py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1`
>   - Verify with: `python --version` (must say `Python 3.11.x`!)

```bash
# Linux / macOS:
# Check 'python3 --version'. If 3.14+ (common on Homebrew), use python3.11 or python3.12:
python3.11 -m venv .venv && source .venv/bin/activate   # or: python3.12 / python3
# (On macOS if needed: brew install python@3.11)

# Windows Git Bash:
py -3.11 -m venv .venv && source .venv/Scripts/activate

# Windows PowerShell:
# (If script execution is disabled: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows CMD (Command Prompt):
py -3.11 -m venv .venv && .venv\Scripts\activate.bat

# Install lab packages and CLI wheel:
pip install -r requirements.txt
pip install ../dist/robotos_edge-0.2.0-cp311-cp311-win_amd64.whl

# (Universal fallback if 'pip' is not recognized: use 'python -m pip')
```

Once installed, you can use the unified **`robotos-kws` CLI** or write code with **`import robotos_kws`**!

---

## Unified CLI (`robotos-kws`)

The `robotos-kws` CLI consolidates all lab operations into simple subcommands:

```bash
# 0. Auto-detect boards & test wire handshake
robotos-kws detect

# 1. Inspect PC audio devices & test board connection
robotos-kws devices

# Test board: 1. Auto-Detection (Recommended)
robotos-kws check-board

# Test board: 2. Specify port manually
robotos-kws check-board --port COM5 --gain 80

# 2. Collect keyword dataset
robotos-kws collect-pc --speaker me --session s01 --labels red green blue off --takes 20
robotos-kws collect-pc --speaker me --session s01 --labels _silence_ --takes 30 --no-prompt
robotos-kws collect-pc --speaker me --session s01 --labels _unknown_ --takes 20
# Or collect using board mic (auto-detects port):
# robotos-kws collect-board --gain 80 --takes 20

# 3. Train DS-CNN neural network & quantize to int8
robotos-kws train --data dataset --out artifacts --epochs 40 --augment 4

# 4. Evaluate on test split & generate confusion matrix
robotos-kws evaluate --artifacts artifacts --data dataset

# 5. Live real-time keyword spotting
robotos-kws live-pc --model artifacts/model_int8.tflite --threshold 0.85
robotos-kws live-board --model artifacts/model_int8.tflite  # Auto-detects port

# 6. Export C array header for ESP-IDF microcontroller firmware
robotos-kws export --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main
```

---

## Python SDK Examples (`examples/`)

Students can use the `robotos_kws` SDK to integrate keyword spotting directly into robot controllers and automation scripts:

- **`examples/01_live_voice_control.py`**: Real-time microphone event loop (`detector.stream_pc()`) triggering robot motor behaviors.
- **`examples/02_board_voice_control.py`**: Live voice recognition streamed directly over USB from the ES3C28P microcontroller (`detector.stream_board()`).
- **`examples/03_classify_audio_file.py`**: Single-clip classification and softmax probability breakdown (`detector.predict()` and `detector.predict_proba()`).
- **`examples/04_programmatic_train.py`**: Programmatic model training and evaluation (`trainer.train()`, `trainer.evaluate()`).

Run any example with:
```bash
python examples/01_live_voice_control.py
python examples/03_classify_audio_file.py dataset/blue/s01_me_pc_0000.wav
```

---

## Script Reference (Under the Hood)

> [!NOTE]
> **Which command to use? (`python`, `python3`, `py`, or `py3`)**
> - **Inside activated `.venv` (all OSes):** `python <script>.py`
> - **Linux / macOS:** `python3 <script>.py` (or `py3` if aliased)
> - **Windows (Git Bash, PowerShell, CMD):** `py <script>.py` or `py -3.11 <script>.py` (especially if `python` points to an incompatible Python 3.14+ version)
> - **Direct fallback:** `./.venv/Scripts/python <script>.py` (Windows) or `./.venv/bin/python <script>.py` (Linux/macOS)

Board scripts need the board running the [hardware-interface-workshop](https://github.com/drsanti/hardware-interface-workshop) **prebuilt firmware** (flashed with `esptool write-flash "@flash_args"`) and the workshop browser tab disconnected.

| Step | Command | Output |
|---|---|---|
| Auto-detect boards | `robotos detect` (or `python detect_board.py`) | Port, model, UUID, caps, live sensor check |
| Flash firmware | `robotos flash-firmware --board es3c28p` | Auto-flashes and verifies board |
| Protocol self-test | `python test_wire.py` | `ALL OK` (no board needed) |
| Record (ES3C28P mic) | `python collect.py --speaker me --session s01 --gain 80 --takes 20` | `dataset/<label>/sNN_me_board_NNNN.wav` (auto-detects port) |
| Mic level / board check | `python collect.py --info --gain 80` | BoardInfo, live level meter, 1 s test stream |
| Record (PC mic) | `python collect_pc_mic.py --speaker me --session s01 --takes 20` | `dataset/<label>/sNN_me_pc_NNNN.wav` |
| Slice a long wav (also an ex28 recorder WAV) | `python collect_pc_mic.py --labels _silence_ --from-wav noise.wav --takes 60` | `_silence_` clips |
| Test data | `python make_synthetic_dataset.py --out synth_dataset` | synthetic clips (plumbing test only) |
| Train | `python train.py --data dataset --out artifacts` | `model.keras`, `model_float.tflite`, `model_int8.tflite`, `meta.json`, `splits.json` |
| Test | `python evaluate.py --artifacts artifacts --data dataset [--device board]` | `artifacts/report.md` |
| Live (board mic) | `python live_infer_board.py --gain 80 --model artifacts/model_int8.tflite` | detections on screen, lost-chunk count (auto-detects port) |
| Live (PC mic) | `python live_infer_pc.py --model artifacts/model_int8.tflite [--wav file.wav]` | detections on screen |
| Check C features | `python verify_c_features.py --data dataset` | `MATCH` / `MISMATCH` |
| Export | `python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main` | `model_data.cc`, `kws_labels.h` |
| IMU: check board | `python collect_imu.py --check` | rate, lost samples, mean accel (auto-detects port) |
| IMU: record | `python collect_imu.py --person me --session s01 --takes 20` | `imu_dataset/<gesture>/sNN_me_ws28p_NNNN.csv` (auto-detects port) |
| IMU: pack | `python imu_common.py pack --data imu_dataset` | `imu_dataset.npz` |
| IMU: train | `python train_imu.py --data imu_dataset --out imu_artifacts` (or `--synthetic`) | `model_float.tflite`, `model_int8.tflite`, `meta.json` |
| IMU: live | `python live_infer_imu.py --model imu_artifacts/model_int8.tflite` | gestures on screen (auto-detects port) |

Every script has `--help`. Both `collect.py` and `collect_pc_mic.py` support `--labels <word...>` to record or re-record specific words (e.g. `--labels blue` or `--labels _silence_ --no-prompt --takes 30`), and `--seconds <sec>` to adjust the raw recording window (default 1.5 s). `collect_pc_mic.py` supports `--device <index>` to select your desired microphone from `--list-devices`. Exit codes of the board scripts: `0` ok, `2` connection/protocol problem, `3` wrong board.

## Formats

- **Keyword clips:** 16 kHz, mono, 16-bit PCM WAV, exactly 16,000 samples (1.0 s, defined by `CLIP_SAMPLES` in `kws_common.py`; to use 1.5 s, change to 24,000 samples and record with `--seconds 2.0`). File name `<session>_<speaker>_<device>_<index>.wav`, with `device` = `board`, `pc`, or `synth`. Automatic quality filters discard and retry any take that clips (peak ≥ 32,000) or is too quiet (speech RMS < −40 dBFS).
- **IMU windows:** CSV with `t_s, ax, ay, az, gx, gy, gz` (m/s², rad/s), 100 rows at 50 Hz. File name `<session>_<person>_ws28p_<index>.csv`.

## Board protocol in one paragraph (`wire.py`)

Frame = `0x00 | COBS(msg_type u8, seq u16 LE, len u16 LE, protobuf payload, CRC-16/XMODEM LE) | 0x00`, identical to the workshop's `demos/src/lib/wire/frame.ts`. Messages used here: `BoardInfo` 0x28 (caps: MIC 0x02, IMU 0x04; ES3C28P `0x33`, ws28p `0x3c`), `MicCmd` 0x86 → `CmdAck` 0x27 (matched on `msg_type` + frame `seq`, 2.5 s timeout), `AudioLevel` 0x23, `MicPcm` 0x24 (16 kHz int16, ≤240 samples, 8-bit `seq` for loss detection), `Imu` 0x20 (~50 Hz, m/s² and rad/s, board timestamp). The port is opened at 921600 baud (ignored by USB Serial/JTAG) and the scripts wait 2.5 s after opening because the board may reset.

## Verified on the course test machine (20 November 2026)

| Script | How it was run | Result |
|---|---|---|
| `test_wire.py` / `wire.py` | Golden frames from the firmware's test vectors; Node.js running the workshop's `frame.ts`, `cobs.ts`, `crc16.ts`, `mic.ts`, `boardInfo.ts`, `imu.ts`, `led.ts` with protobufjs | All golden frames match; 6 `MicCmd` + 4 raw frames byte-identical TS ↔ Python; 9 Python-made frames (BoardInfo, MicPcm, Imu, CmdAck, with log noise) decoded identically by the TS code |
| `collect.py` | Simulated ES3C28P on a pseudo-terminal: real frames, boot text, noise bytes, a bad-CRC frame, one MicPcm chunk dropped every 150 | 6 clips saved, each **sample-exact** against the source audio; takes with a seq gap were discarded and re-recorded; `--info` OK |
| `live_infer_board.py` | Same simulator streaming a 7.5 s test sentence in real time for 15.5 s | red, green, blue, off detected in order twice by float32 and int8; 6 lost chunks reported = 6 dropped by the simulator |
| `collect_imu.py` | Simulated ws28p (Imu 50 Hz, BoardInfo only every 10 s, one sample dropped every 97) | `--check` 49.3 Hz; 4 windows saved (100 × 6); `--max-lost 0` rejected every gapped take |
| `live_infer_imu.py` | Simulated ws28p cycling idle/shake/circle/lift for 21 s; also `--replay` | shake, circle, lift detected in order (twice); 11 lost samples reported = 11 dropped |
| Wrong board / bad port | `collect.py` and `live_infer_board.py` on the ws28p simulator; `collect_imu.py` and `live_infer_imu.py` on the ES3C28P simulator; a missing port | Clear "Wrong board" message, exit code 3; missing port → exit code 2 with a hint |
| `train_imu.py --synthetic` | 8 generated people × 4 gestures × 25, 2 people held out | 1,756 parameters; float32 100%, int8 98.5%; int8 10.3 KiB; ops CONV_2D, EXPAND_DIMS, FULLY_CONNECTED, MAX_POOL_2D, MEAN, RESHAPE, SOFTMAX |
| `make_synthetic_dataset.py` + `train.py` | 64 clips × 6 labels, 8 speakers, pc + board | 5,510 parameters; float32 26.1 KiB; int8 18.8 KiB |
| `evaluate.py` | 48 test clips from held-out speakers | float32 91.7%, int8 91.7%; board 87.5%, pc 95.8% |
| `live_infer_pc.py` (`--wav` and mocked mic) | sentence "red, (silence), green, blue, off" | 4 detections in order |
| `collect_pc_mic.py` | mocked `sounddevice.rec`; `--from-wav` for real | 1.0 s clips with correct names |
| `verify_c_features.py` | 384 synthetic clips | MATCH |
| TFLite Micro reference interpreter | int8 KWS model, 48 test clips | same top-1 as TFLite on 48/48; arena ≈ 37 KiB (64-bit host) |

No real microphone or board was used for these runs.

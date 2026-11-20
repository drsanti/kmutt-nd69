# Week 08 Python tools

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lab-2e8b57?style=flat-square)

[Labs index](../README.md) · [Lessons](../../lessons/README.md)

## Install

> [!IMPORTANT]
> **Use Python 3.10 to 3.13.**
> Check your command with `python --version`, `python3 --version`, or `py --version` (Windows).
> On Windows with multiple Python versions installed, specify Python 3.11 with `py -3.11 -m venv .venv`. Avoid Python 3.14+ (incompatible with pre-compiled TensorFlow/NumPy C-extensions).

```bash
# Linux / macOS:
python3 -m venv .venv && source .venv/bin/activate

# Windows Git Bash:
py -3.11 -m venv .venv && source .venv/Scripts/activate

# Windows PowerShell:
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows CMD:
py -3.11 -m venv .venv && .venv\Scripts\activate.bat

# Install lab packages:
pip install -r requirements.txt
```

`sounddevice` needs PortAudio: it is bundled in the wheel on Windows and macOS; on Debian/Ubuntu run `sudo apt install libportaudio2`.

## Commands

> [!NOTE]
> **Which command to use? (`python`, `python3`, `py`, or `py3`)**
> - **Inside activated `.venv` (all OSes):** `python <script>.py`
> - **Linux / macOS:** `python3 <script>.py` (or `py3` if aliased)
> - **Windows (Git Bash, PowerShell, CMD):** `py <script>.py` or `py -3.11 <script>.py` (especially if `python` points to an incompatible Python 3.14+ version)
> - **Direct fallback:** `./.venv/Scripts/python <script>.py` (Windows) or `./.venv/bin/python <script>.py` (Linux/macOS)

Board scripts need the board running the [hardware-interface-workshop](https://github.com/drsanti/hardware-interface-workshop) **prebuilt firmware** (flashed with `esptool write-flash "@flash_args"`) and the workshop browser tab disconnected.

| Step | Command | Output |
|---|---|---|
| Protocol self-test | `python test_wire.py` | `ALL OK` (no board needed) |
| Record (ES3C28P mic) | `python collect.py --port COM5 --speaker me --session s01 --takes 20` | `dataset/<label>/sNN_me_board_NNNN.wav` |
| Mic level / board check | `python collect.py --port COM5 --info` | BoardInfo, live level, 1 s test stream |
| Record (PC mic) | `python collect_pc_mic.py --speaker me --session s01 --takes 20` | `dataset/<label>/sNN_me_pc_NNNN.wav` |
| Slice a long wav (also an ex28 recorder WAV) | `python collect_pc_mic.py --labels _silence_ --from-wav noise.wav --takes 60` | `_silence_` clips |
| Test data | `python make_synthetic_dataset.py --out synth_dataset` | synthetic clips (plumbing test only) |
| Train | `python train.py --data dataset --out artifacts` | `model.keras`, `model_float.tflite`, `model_int8.tflite`, `meta.json`, `splits.json` |
| Test | `python evaluate.py --artifacts artifacts --data dataset [--device board]` | `artifacts/report.md` |
| Live (board mic) | `python live_infer_board.py --port COM5 --model artifacts/model_int8.tflite` | detections on screen, lost-chunk count |
| Live (PC mic) | `python live_infer_pc.py --model artifacts/model_int8.tflite [--wav file.wav]` | detections on screen |
| Check C features | `python verify_c_features.py --data dataset` | `MATCH` / `MISMATCH` |
| Export | `python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main` | `model_data.cc`, `kws_labels.h` |
| IMU: check board | `python collect_imu.py --port COM7 --check` | rate, lost samples, mean accel |
| IMU: record | `python collect_imu.py --port COM7 --person me --session s01 --takes 20` | `imu_dataset/<gesture>/sNN_me_ws28p_NNNN.csv` |
| IMU: pack | `python imu_common.py pack --data imu_dataset` | `imu_dataset.npz` |
| IMU: train | `python train_imu.py --data imu_dataset --out imu_artifacts` (or `--synthetic`) | `model_float.tflite`, `model_int8.tflite`, `meta.json` |
| IMU: live | `python live_infer_imu.py --port COM7 --model imu_artifacts/model_int8.tflite` | gestures on screen |

Every script has `--help`. Exit codes of the board scripts: `0` ok, `2` connection/protocol problem, `3` wrong board.

## Formats

- **Keyword clips:** 16 kHz, mono, 16-bit PCM WAV, exactly 16,000 samples. File name `<session>_<speaker>_<device>_<index>.wav`, with `device` = `board`, `pc`, or `synth`.
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

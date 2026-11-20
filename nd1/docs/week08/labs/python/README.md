# Week 08 Python tools

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-lab-2e8b57?style=flat-square)

[Labs index](../README.md) · [Lessons](../../lessons/README.md)

## Install

```bash
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Python 3.10–3.13. `sounddevice` needs PortAudio: it is bundled on Windows and macOS; on Debian/Ubuntu run `sudo apt install libportaudio2`.

## Commands

| Step | Command | Output |
|---|---|---|
| Record (board) | `python collect.py --port COM5 --speaker me --session s01 --takes 20` | `dataset/<label>/sNN_me_board_NNNN.wav` |
| Record (PC mic) | `python collect_pc_mic.py --speaker me --session s01 --takes 20` | `dataset/<label>/sNN_me_pc_NNNN.wav` |
| Slice a long wav | `python collect_pc_mic.py --labels _silence_ --from-wav noise.wav --takes 60` | `_silence_` clips |
| Test data | `python make_synthetic_dataset.py --out synth_dataset` | synthetic clips (plumbing test only) |
| Train | `python train.py --data dataset --out artifacts` | `model.keras`, `model_float.tflite`, `model_int8.tflite`, `meta.json`, `splits.json` |
| Test | `python evaluate.py --artifacts artifacts --data dataset [--device board]` | `artifacts/report.md` |
| Live (PC) | `python live_infer_pc.py --model artifacts/model_int8.tflite [--wav file.wav]` | detections on screen |
| Check C features | `python verify_c_features.py --data dataset` | `MATCH` / `MISMATCH` |
| Export | `python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main` | `model_data.cc`, `kws_labels.h` |
| Gestures | `python collect_touch.py --port COM5` · `python train_touch.py --data touch_dataset` | strokes, gesture models |

Every script has `--help`.

## Clip format

16 kHz, mono, 16-bit PCM WAV, exactly 16,000 samples. File name `<session>_<speaker>_<device>_<index>.wav`, with `device` = `board`, `pc`, or `synth`.

## Verified on the course test machine (20 November 2026)

| Script | How it was run | Result |
|---|---|---|
| `make_synthetic_dataset.py` | 64 clips × 6 labels, 8 speakers, pc + board | 384 clips |
| `train.py` | 40 epochs max, CPU | 5,510 parameters; float32 26.1 KiB; int8 18.8 KiB; ops CONV_2D, DEPTHWISE_CONV_2D, FULLY_CONNECTED, MEAN, SOFTMAX |
| `evaluate.py` | 48 test clips from held-out speakers | float32 91.7%, int8 91.7% (drop 0.00 pp); board 87.5%, pc 95.8% |
| `live_infer_pc.py --wav` | sentence "red, (silence), green, blue, off" | red, green, blue, off detected in order by both models |
| `live_infer_pc.py` (mic path) | mocked `sounddevice.InputStream` fed from a wav | same 4 detections |
| `collect_pc_mic.py` | mocked `sounddevice.rec`; also `--from-wav` for real | 1.0 s clips with correct names |
| `collect.py` | simulated audio-logger on a pseudo-terminal (with stray log text) | `--ping`, `--info`, 2 clips saved, checksums OK |
| `verify_c_features.py` | 384 synthetic clips | max difference 0.00008 → MATCH |
| `export_c_array.py` | KWS and touch models | C files compile with g++ |
| `train_touch.py --synthetic` | 240 strokes, 1 speaker held out | float32 and int8 100%; int8 6.4 KiB |
| TFLite Micro reference interpreter (`tflite-micro` pip package) | int8 KWS model, 48 test clips | same top-1 as TFLite on 48/48; arena needed ≈ 37 KiB (64-bit host) |

No real microphone or board was used for these runs.

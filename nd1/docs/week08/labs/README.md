# Week 08 labs

![course](https://img.shields.io/badge/course-KMUTT%20ND69-1a2f5a?style=flat-square)
![track](https://img.shields.io/badge/track-ND01-0e7490?style=flat-square)
![week](https://img.shields.io/badge/week-08-334155?style=flat-square)
![lang](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)
![kind](https://img.shields.io/badge/kind-labs-2e8b57?style=flat-square)

## Table of contents

- [Week 08 index](../README.md)
- [Lessons](../lessons/README.md)
- [Python tools](python/README.md)
- [Firmware: kws-inference (on-device step)](firmware/kws-inference/README.md)
- [hardware-interface-workshop prebuilt firmware](https://github.com/drsanti/hardware-interface-workshop/tree/main/firmware-prebuilt) (on the board for collection and live tests)

## Layout

```text
labs/
├── python/                      run every command from here
│   ├── wire.py                  workshop wire protocol: COBS + CRC-16 frames, protobuf messages, BoardSession
│   ├── test_wire.py             protocol self-test (golden frames), no board needed
│   ├── kws_common.py            keyword settings + feature pipeline + dataset helpers (the contract)
│   ├── collect.py               ES3C28P board mic → dataset   (workshop prebuilt firmware)
│   ├── collect_pc_mic.py        computer mic → dataset
│   ├── make_synthetic_dataset.py  pipeline test without any microphone
│   ├── train.py                 DS-CNN training + float32/int8 TFLite export
│   ├── train_colab.ipynb        the same on Google Colab
│   ├── evaluate.py              accuracy, confusion matrix, per-device, quantization drop
│   ├── live_infer_board.py      live keyword spotting: board mic stream → model on the computer
│   ├── live_infer_pc.py         live keyword spotting on the computer mic (or a wav file)
│   ├── verify_c_features.py     compiles kws_features.c and compares it with Python
│   ├── export_c_array.py        .tflite → model_data.cc + kws_labels.h
│   ├── imu_common.py            IMU windows, normalisation, augmentation, dataset helpers
│   ├── collect_imu.py           ws28p IMU → labelled 2 s windows (CSV)
│   ├── train_imu.py             tiny 1D CNN + float32/int8 export + confusion matrix
│   ├── live_infer_imu.py        live gestures: ws28p IMU stream → model on the computer
│   └── requirements.txt
└── firmware/                    ESP-IDF v6.1, only for the on-device step (Lesson 05)
    ├── components/es3c28p_audio/   I2C + I2S + ES8311 microphone capture
    └── kws-inference/           TFLite Micro keyword spotter (replaces the workshop firmware while flashed)
```

## Which firmware is on the board?

| Activity | Board firmware |
|---|---|
| `collect.py`, `live_infer_board.py` (ES3C28P) | workshop prebuilt `es3c28p` — `rb config --board es3c28p`, `rb flash-bin` |
| `collect_imu.py`, `live_infer_imu.py` (ws28p) | workshop prebuilt `ws28p` — `rb config --board ws28p`, `rb flash-bin` |
| On-device keyword spotting (Lesson 05) | `kws-inference` (`idf.py flash`); afterwards reflash the prebuilt image |

Only one program can own the serial port: disconnect the workshop browser tab before running a board script.

## Quick start without hardware (10 minutes)

```bash
cd nd1/docs/week08/labs/python
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python make_synthetic_dataset.py --out synth_dataset
python train.py --data synth_dataset --out synth_artifacts --epochs 30
python evaluate.py --artifacts synth_artifacts --data synth_dataset
python verify_c_features.py --data synth_dataset --max-clips 30
```

Then replace the synthetic data with your own recordings (`collect_pc_mic.py` or `collect.py`).

IMU track without hardware:

```bash
python test_wire.py
python train_imu.py --synthetic --out imu_artifacts
```

## Status

The Python tools were run end-to-end on synthetic data (Linux, Python 3.13, TensorFlow 2.21). The board tools were run against a simulated board on a pseudo-terminal that sends real workshop frames, including noise and dropped frames; `wire.py` was cross-checked byte-for-byte against the workshop's TypeScript codec. No real board was attached. `kws-inference` has not been built with `idf.py` or flashed; see its README.

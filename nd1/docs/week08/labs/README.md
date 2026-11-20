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
- [Firmware: audio-logger](firmware/audio-logger/README.md)
- [Firmware: kws-inference](firmware/kws-inference/README.md)
- [Firmware: touch-logger](firmware/touch-logger/README.md)

## Layout

```text
labs/
├── python/                      run every command from here
│   ├── kws_common.py            settings + feature pipeline + dataset helpers (the contract)
│   ├── collect.py               board mic → dataset   (needs audio-logger)
│   ├── collect_pc_mic.py        computer mic → dataset
│   ├── make_synthetic_dataset.py  pipeline test without any microphone
│   ├── train.py                 DS-CNN training + float32/int8 TFLite export
│   ├── train_colab.ipynb        the same on Google Colab
│   ├── evaluate.py              accuracy, confusion matrix, per-device, quantization drop
│   ├── live_infer_pc.py         live keyword spotting on the computer mic (or a wav file)
│   ├── verify_c_features.py     compiles kws_features.c and compares it with Python
│   ├── export_c_array.py        .tflite → model_data.cc + kws_labels.h
│   ├── touch_common.py, collect_touch.py, train_touch.py    gesture track
│   └── requirements.txt
└── firmware/                    ESP-IDF v6.1 projects for the ES3C28P
    ├── components/es3c28p_audio/   I2C + I2S + ES8311 microphone capture (shared)
    ├── audio-logger/            streams 1.5 s clips to collect.py over USB Serial/JTAG
    ├── kws-inference/           TFLite Micro keyword spotter, FreeRTOS capture → queue → inference
    └── touch-logger/            prints FT6336G strokes for collect_touch.py
```

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

## Status

The Python tools were run end-to-end on synthetic data (Linux, Python 3.13, TensorFlow 2.21). The microphone and serial paths were exercised with a mocked microphone and a simulated board. The firmware projects have not been built with `idf.py` or flashed yet; see each project README.

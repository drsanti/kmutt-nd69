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

| Activity | Board firmware | How to flash with `esptool` |
|---|---|---|
| `collect.py`, `live_infer_board.py` (ES3C28P) | workshop prebuilt `es3c28p` | `python -m esptool --chip esp32s3 -p <PORT> write-flash "@flash_args"` |
| `collect_imu.py`, `live_infer_imu.py` (ws28p) | workshop prebuilt `ws28p` | `python -m esptool --chip esp32s3 -p <PORT> write-flash "@flash_args"` |
| On-device keyword spotting (Lesson 05) | `kws-inference` | `idf.py flash` (in `firmware/kws-inference`); afterwards reflash prebuilt |

> [!TIP]
> **How to flash prebuilt firmware using `esptool` (no ESP-IDF required):**
> ```bash
> # 1. Install esptool:
> pip install esptool
> 
> # 2. Change to the prebuilt board folder:
> cd hardware-interface-workshop/firmware-prebuilt/es3c28p   # (or ws28p for IMU)
> 
> # 3. Flash the board (replace <PORT> with COMx on Windows or /dev/ttyACM0 on Linux):
> python -m esptool --chip esp32s3 -p <PORT> write-flash "@flash_args"
> # On Windows with py: py -m esptool --chip esp32s3 -p COMx write-flash "@flash_args"
> ```

Only one program can own the serial port: disconnect the workshop browser tab before running a board script.

## Prerequisites: Python Setup (Python 3.10 – 3.13)

> [!IMPORTANT]
> **Use Python 3.10 to 3.13.**
> Do **NOT** use Python 3.14+ (pre-release free-threaded builds break precompiled NumPy C-extensions and TensorFlow).

### Which command runs Python on your system? (`py`, `python`, `python3`, `py3`)

Depending on your Operating System, installed shells, and configurations, Python is invoked with different command words. Use this guide to identify and test yours:

| Command word | Where it works | When to use |
|---|---|---|
| **`python`** | All OSes (Windows, Linux, macOS) | **Standard command.** Always use this when your `.venv` is activated. |
| **`python3`** | Linux, macOS, WSL | Standard on Unix systems where `python` may refer to an older or system Python. |
| **`py`** | Windows (CMD, PowerShell, Git Bash) | **Recommended on Windows.** Invokes the official Windows Python Launcher (`C:\Windows\py.exe`), automatically picking your latest stable Python. |
| **`py -3.11`** (or `-3.12`) | Windows | Forces the launcher to use a specific version when multiple Python versions are installed. |
| **`py3`** | Linux / custom aliases | Some Linux distributions or student configurations alias `python3` to `py3`. |
| **`./.venv/Scripts/python`** | Windows Git Bash / CMD | Direct path to the virtual environment interpreter — always works even if PATH/activation is broken. |
| **`./.venv/bin/python`** | Linux / macOS | Direct path to the virtual environment interpreter. |

#### How to check and verify your command:

Run these in your terminal to see which one works and which version it runs:

```bash
# 1. Test which command word is recognized and prints Python 3.10 - 3.13:
python --version
python3 --version
py --version          # Windows only
py -3.11 --version    # Windows only

# 2. Check the exact path of the Python executable your shell is running:
which python          # Linux, macOS, Git Bash
where python          # Windows CMD
Get-Command python    # Windows PowerShell
```

If `python --version` outputs `Python 3.14` or fails with NumPy C-extension errors, use **`py`** or **`py -3.11`** on Windows!

---

### 1. Create and Activate Virtual Environment

Inside `nd1/docs/week08/labs/python`:

```bash
cd nd1/docs/week08/labs/python
```

Choose your shell:

- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- **Windows Git Bash (MINGW64):**
  ```bash
  # Use py -3.11 if python points to Python 3.14
  py -3.11 -m venv .venv
  source .venv/Scripts/activate
  ```

- **Windows PowerShell:**
  ```powershell
  # If you have multiple Python versions installed, specify Python 3.11 or 3.12:
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  *(If PowerShell blocks scripts: run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

- **Windows Command Prompt (cmd.exe):**
  ```cmd
  py -3.11 -m venv .venv
  .venv\Scripts\activate.bat
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```
*(On Linux/Debian/Ubuntu, if `sounddevice` fails with PortAudio missing: `sudo apt install libportaudio2`).*

---

## Lab Path A: Quick Start without Hardware (Synthetic Pipeline, 10 min)

Test the complete training and export pipeline immediately without any microphone or board:

> [!NOTE]
> **Git Bash / Windows Users (`py` command):**
> If you are running in **Git Bash** on Windows and `python` fails with a NumPy C-extension import error (or points to Python 3.14+), use `py` instead of `python`:
> ```bash
> py make_synthetic_dataset.py --out synth_dataset
> ```
> The Windows `py` launcher automatically routes to your installed stable Python 3.11/3.12 environment where packages are installed. You can use `py` for all script commands in this lab.

```bash
# 1. Generate synthetic test dataset
python make_synthetic_dataset.py --out synth_dataset

# 2. Train DS-CNN model and export float32 + int8 TFLite
python train.py --data synth_dataset --out synth_artifacts --epochs 30

# 3. Evaluate accuracy and quantization drop
python evaluate.py --artifacts synth_artifacts --data synth_dataset

# 4. Verify C feature extraction matches Python bit-for-bit
python verify_c_features.py --data synth_dataset --max-clips 30
```

IMU gesture track without hardware:
```bash
python test_wire.py
python train_imu.py --synthetic --out imu_artifacts
```

---

## Lab Path B: Collect Data & Live Test with PC Microphone

No hardware board required! You can record real voice keywords directly with your computer microphone:

```bash
# 1. List audio input devices to check your microphone index
python collect_pc_mic.py --list-devices

# 2. Record 20 takes for each keyword (say each word when prompted):
# (Optional: pass --device <index> if your desired mic is not default)
python collect_pc_mic.py --speaker me --session s01 --labels red green blue off --takes 20

# 3. Record background noise (stay quiet):
python collect_pc_mic.py --speaker me --session s01 --labels _silence_ --takes 30 --no-prompt

# 4. Train the model on your real recorded dataset:
python train.py --data dataset --out artifacts --epochs 40

# 5. Run live keyword detection through your PC microphone:
python live_infer_pc.py --model artifacts/model_int8.tflite
```

---

## Lab Path C: Collect Data & Live Test with ES3C28P Board

> [!WARNING]
> **Serial Port Exclusivity**: Close any open serial monitors, IDE consoles, or workshop browser tabs (`WebSerial`) before running board scripts. Only one program can access the COM port at a time.

```bash
# 1. Check board connection and microphone audio level (e.g. COM5 or /dev/ttyUSB0):
python collect.py --port COM5 --info

# 2. Record keyword dataset from board MEMS microphone:
python collect.py --port COM5 --speaker me --session s01 --takes 20

# 3. Train combined model (PC + board clips):
python train.py --data dataset --out artifacts --epochs 40

# 4. Run live keyword spotting streamed from the board:
python live_infer_board.py --port COM5 --model artifacts/model_int8.tflite

# 5. Export C array for flashing to firmware (Lesson 05):
python export_c_array.py --model artifacts/model_int8.tflite --out-dir ../firmware/kws-inference/main
```

---

## Troubleshooting & Help

Encountering an issue? See the detailed guide in [troubleshooting.md](../troubleshooting.md):
- Python 3.14 / NumPy `_multiarray_umath` C-extension error
- Microphone muted, PortAudio missing, or quiet dBFS warnings
- Serial port busy / access denied
- TFLite arena size adjustments for firmware deploy

## Status

The Python tools were run end-to-end on synthetic data (Linux, Python 3.13, TensorFlow 2.21). The board tools were run against a simulated board on a pseudo-terminal that sends real workshop frames, including noise and dropped frames; `wire.py` was cross-checked byte-for-byte against the workshop's TypeScript codec. No real board was attached. `kws-inference` has not been built with `idf.py` or flashed; see its README.

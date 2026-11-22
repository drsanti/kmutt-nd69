---
name: sync-robotos-kws
description: >-
  Build robotos_kws wheel and synchronize compiled wheel, examples, and documentation
  across all 3 student tracks (ND1, ND2, ND3) in kmutt-nd69 on Windows or macOS. Use whenever
  modifying robotos/sdk/python-kws, fixing ESP32-S3 serial/IMU communication, bumping package version,
  or ensuring student lab environments stay identical.
---

# robotos_kws Multi-Track Sync & Build Skill (Windows & macOS)

Use this skill whenever modifying the Python SDK in `robotos/sdk/python-kws`, changing serial/IMU wire protocol, updating models, or keeping the KMUTT ND69 student tracks synchronized across Windows and macOS.

## Repository Layout & Student Tracks

- **Canonical SDK Source**: `robotos/sdk/python-kws/`
- **Track 1 (ND1 Embedded & IoT)**: `robotos/kmutt-nd69/nd1/docs/week08/labs/`
- **Track 2 (ND2 Backend & Frontend)**: `robotos/kmutt-nd69/nd2/docs/week08/labs/`
- **Track 3 (ND3 Automation & Robotics)**: `robotos/kmutt-nd69/nd3/docs/week08/labs/`

## Core Rules

1. **Zero Source Leak Policy**: NEVER copy raw `.py` SDK files or internal package folders directly into student track directories. Students receive only the compiled wheel (`.whl`) and track-specific examples.
2. **Version Parity**: All 3 tracks must always have the exact same version of `robotos_kws-<version>-py3-none-any.whl` in their `dist/` directories.
3. **ESP32-S3 Serial Safety**: The ESP32-S3 native USB Serial/JTAG resets when `RTS=1, DTR=0`. Always ensure PySerial is initialized with `rts=False, dtr=False`, and that `ser.rts=False; ser.dtr=False` is set before `ser.close()`.
4. **macOS Serial Device Rule**: On macOS, ALWAYS use the callout device `/dev/cu.usbmodem*` (never `/dev/tty.*`, which blocks on carrier detect).

## Automated Firmware Flashing (ND1, ND2, ND3)

Students across all tracks can flash and verify their boards using:
```bash
# Auto-detects ESP32-S3 port, downloads prebuilt binaries, flashes, and verifies:
robotos flash-firmware

# Specify board variant:
robotos flash-firmware --board ws28p    # IMU & Robotics (ND3)
robotos flash-firmware --board es3c28p  # Mic & LED (ND1/ND2)

# Use local directory (downloaded firmware files):
robotos flash-firmware --from-dir ~/Downloads/ws28p

# Use specific remote repository preset or custom GitHub URL:
robotos flash-firmware --source robotos-workshop
robotos flash-firmware --source hardware-interface-workshop
robotos flash-firmware --source https://github.com/drsanti/robotos-workshop/tree/main/fw
```

## Step-by-Step Workflow

### 1. Update SDK Code & Bump Version
If public behavior or APIs changed:
1. Update `version` in `robotos/sdk/python-kws/pyproject.toml`
2. Update `__version__` in `robotos/sdk/python-kws/robotos_kws/__init__.py`

### 2. Run the Multi-Track Sync Pipeline
Execute the automated sync script (works identically on Windows and macOS):
```bash
# Windows:
python robotos/sdk/python-kws/publish_to_students.py

# macOS / Linux:
python3 robotos/sdk/python-kws/publish_to_students.py
```
This script handles:
- Python syntax compilation verification (`py_compile`) for all package modules and examples.
- Cleaning build artifacts (`build/`, `*.egg-info`).
- Building the wheel into `dist/` (`robotos_kws-0.1.7-py3-none-any.whl`).
- Copying the wheel to `robotos/dist/` and `nd{1,2,3}/docs/week08/labs/dist/`.
- Deleting old wheel versions from all student tracks.
- Synchronizing examples to ND1 and ND2.
- Running a security audit to guarantee no raw source files leaked into student folders.
- Force-reinstalling into active `.venv` environments in all 3 tracks (`.venv/bin/python` on macOS, `.venv/Scripts/python.exe` on Windows) and running smoke tests.
- Updating wheel filename references across all student Markdown documentation.

### 3. Verify Live Hardware (If physical board connected)
Identify the serial port:
- Windows: `COM17` (or from Device Manager)
- macOS: `ls /dev/cu.usbmodem*` (e.g., `/dev/cu.usbmodem1101`)

Run telemetry check:
```bash
# Windows:
robotos-kws check-imu --port COM17

# macOS:
robotos-kws check-imu --port /dev/cu.usbmodem1101
```
Confirm:
- Connects without resetting the ESP32-S3 board.
- Receives 150+ samples at 50 Hz with 0 lost packets.
- Exits cleanly without rebooting the board.

### 4. macOS Audio/Mic Setup (ND1 & ND2)
- Ensure Terminal / IDE has microphone access in:
  `System Settings -> Privacy & Security -> Microphone`
- If PortAudio missing: `brew install portaudio`

### 5. Commit and Push
Commit changes in `robotos/kmutt-nd69`:
```bash
cd robotos/kmutt-nd69
git status
git add .
git commit -m "[week08] sync robotos_kws <VERSION> across all student tracks"
git push origin main
```

---
name: sync-robotos-kws
description: >-
  Build robotos_kws wheel and synchronize compiled wheel, examples, and documentation
  across all 3 student tracks (ND1, ND2, ND3) in kmutt-nd69. Use whenever modifying
  robotos/sdk/python-kws, fixing ESP32-S3 serial/IMU communication, bumping package version,
  or ensuring student lab environments stay identical.
---

# robotos_kws Multi-Track Sync & Build Skill

Use this skill whenever modifying the Python SDK in `robotos/sdk/python-kws`, changing serial/IMU wire protocol, updating models, or keeping the KMUTT ND69 student tracks synchronized.

## Repository Layout & Student Tracks

- **Canonical SDK Source**: `robotos/sdk/python-kws/`
- **Track 1 (ND1 Embedded & IoT)**: `robotos/kmutt-nd69/nd1/docs/week08/labs/`
- **Track 2 (ND2 Backend & Frontend)**: `robotos/kmutt-nd69/nd2/docs/week08/labs/`
- **Track 3 (ND3 Automation & Robotics)**: `robotos/kmutt-nd69/nd3/docs/week08/labs/`

## Core Rules

1. **Zero Source Leak Policy**: NEVER copy raw `.py` SDK files or internal package folders directly into student track directories. Students receive only the compiled wheel (`.whl`) and track-specific examples.
2. **Version Parity**: All 3 tracks must always have the exact same version of `robotos_kws-<version>-py3-none-any.whl` in their `dist/` directories.
3. **ESP32-S3 Serial Safety**: The ESP32-S3 native USB Serial/JTAG resets when `RTS=1, DTR=0`. Always ensure PySerial is initialized with `rts=False, dtr=False`, and that `ser.rts=False; ser.dtr=False` is set before `ser.close()`.

## Step-by-Step Workflow

### 1. Update SDK Code & Bump Version
If public behavior or APIs changed:
1. Update `version` in `robotos/sdk/python-kws/pyproject.toml`
2. Update `__version__` in `robotos/sdk/python-kws/robotos_kws/__init__.py`

### 2. Run the Multi-Track Sync Pipeline
Execute the automated sync script:
```bash
python robotos/sdk/python-kws/publish_to_students.py
```
This script handles:
- Python syntax compilation verification (`py_compile`) for all package modules and examples.
- Cleaning build artifacts (`build/`, `*.egg-info`).
- Building the wheel into `dist/`.
- Copying the wheel to `robotos/dist/` and `nd{1,2,3}/docs/week08/labs/dist/`.
- Deleting old wheel versions from all student tracks.
- Synchronizing examples to ND1 and ND2.
- Running a security audit to guarantee no raw source files leaked into student folders.
- Force-reinstalling into active `.venv` environments in all 3 tracks and running smoke tests.
- Updating wheel filename references across all student Markdown documentation.

### 3. Verify Live Hardware (If physical board connected)
```bash
robotos-kws check-imu --port <COM_PORT>
```
Confirm:
- Connects without resetting the ESP32-S3 board.
- Receives 150+ samples at 50 Hz with 0 lost packets.
- Exits cleanly without rebooting the board.

### 4. Commit and Push
Commit changes in `robotos/kmutt-nd69`:
```bash
cd robotos/kmutt-nd69
git status
git add .
git commit -m "[week08] sync robotos_kws <VERSION> across all student tracks"
git push origin main
```

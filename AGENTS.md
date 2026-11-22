# Agent Instructions — KMUTT ND69 Curriculum Repository

This repository (`robotos/kmutt-nd69`) houses the curriculum, documentation, and student lab packages for the KMUTT ND69 course. It is a separate Git repository nested within the root `robotos` workspace.

---

## 1. Multi-Track Curriculum Architecture

The course is divided into three distinct specialized student tracks:

| Track | Focus Area | Lab Location | Hardware Requirement | Lab Workflow |
| :--- | :--- | :--- | :--- | :--- |
| **ND1** | Embedded Systems & IoT | `nd1/docs/week08/labs/` | PC Microphone only (no board) | CLI-based data collection, feature extraction, training, model evaluation. |
| **ND2** | Backend & Frontend (AI) | `nd2/docs/week08/labs/` | PC Microphone only (no board) | SDK integration, Python audio recorder, FastAPI backend (`:8000`), Vite React web app UI (`:5173`). |
| **ND3** | Automation & Robotics | `nd3/docs/week08/labs/` | Real ESP32-S3 board (ws28p) + IMU | IMU 6-axis streaming (50 Hz), motion gesture classification, serial CLI (`robotos-kws check-imu`). |

---

## 2. Python KWS SDK (`robotos_kws`) & Multi-Track Distribution Rules

The `robotos_kws` package provides keyword spotting, audio feature extraction, IMU motion streaming, and model training utilities.

### Rule 1: Canonical Source of Truth
- The single source of truth for the `robotos_kws` Python package is `robotos/sdk/python-kws/`.
- **NEVER** edit files directly inside the student tracks' `dist/` or `.venv/` folders.
- **NEVER** copy raw `.py` source code or internal package modules (`wire.py`, `kws_common.py`, `robotos_kws/`) into any student directory. Only compiled wheels and student-facing examples belong in `kmutt-nd69`.

### Rule 2: Strict Multi-Track Synchronization
- All three tracks (`nd1`, `nd2`, `nd3`) **MUST** share the identical wheel package version:
  - `nd1/docs/week08/labs/dist/robotos_kws-<VERSION>-py3-none-any.whl`
  - `nd2/docs/week08/labs/dist/robotos_kws-<VERSION>-py3-none-any.whl`
  - `nd3/docs/week08/labs/dist/robotos_kws-<VERSION>-py3-none-any.whl`
- Whenever any code in `robotos/sdk/python-kws` is updated:
  1. Bump the version in `pyproject.toml` and `robotos_kws/__init__.py`.
  2. Run the automated multi-track build & deployment pipeline script.
  3. Never leave one track on an older wheel version while updating another.

### Rule 3: Automated Pipeline Execution
Run the deployment script from `robotos/sdk/python-kws/` (or via Python):
```bash
python robotos/sdk/python-kws/publish_to_students.py
```
*(On macOS/Linux, run `python3 robotos/sdk/python-kws/publish_to_students.py` or `python3 ../sdk/python-kws/publish_to_students.py`)*

This script automatically:
1. Verifies Python syntax across all package modules and examples (`py_compile`).
2. Cleans build caches and builds the new `.whl`.
3. Validates wheel archive integrity.
4. Deploys the wheel to all 3 student tracks and deletes previous versions.
5. Synchronizes track-specific examples to `nd1` and `nd2`.
6. Enforces a security audit to ensure zero raw SDK source files have leaked.
7. Reinstalls the wheel with `--force-reinstall` into active `.venv` environments across all tracks and executes smoke tests.
8. Automatically updates markdown documentation references across `kmutt-nd69` to the new wheel filename.

---

## 3. Hardware & Serial Communication Rules (ESP32-S3)

### ESP32-S3 USB Serial/JTAG Reset Prevention
- The ws28p board uses the ESP32-S3 native USB Serial/JTAG controller (`USB VID:PID = 303A:1001`).
- **Hardware behavior**: Pulsing `RTS=1, DTR=0` triggers a hardware reset into the bootloader or reboots the board.
- When configuring or connecting via PySerial in `wire.py` or any script:
  ```python
  # ALWAYS disable DTR and RTS before opening:
  ser = serial.Serial()
  ser.port = port
  ser.baudrate = baudrate
  ser.dtr = False
  ser.rts = False
  ser.open()
  ```
- When closing the serial port:
  ```python
  # ALWAYS explicitly clear DTR and RTS before closing:
  ser.dtr = False
  ser.rts = False
  ser.close()
  ```
- **Never** allow PySerial's default constructor (`serial.Serial(port, baudrate)`) to run without explicitly clearing RTS and DTR, as it will reset the microcontroller every time a command connects or exits.

### Firmware Flashing Command (ND1, ND2, ND3)
```bash
# Auto-detects port, downloads prebuilt binaries, flashes, and verifies:
robotos flash-firmware

# Or specify board/port explicitly:
robotos flash-firmware --board ws28p --port COM17
# macOS:
robotos flash-firmware --board ws28p --port /dev/cu.usbmodem1101
```

### Live Verification Command
```bash
# Auto-detection (Recommended):
robotos check-imu

# Or specify port manually:
# Windows:
robotos check-imu --port COM17

# macOS (always use /dev/cu.usbmodem*):
robotos check-imu --port /dev/cu.usbmodem1101
```
Expected behavior:
- Connects cleanly without restarting the board.
- Streams 150+ samples at 50 Hz with 0 lost packets.
- Exits cleanly without rebooting the board.

---

## 4. macOS Environment, Wheel Building & Hardware Telemetry Guide

When working on **macOS (Apple Silicon / Intel)**:

### 4.1 Python Environment on macOS
- Python version requirement: **Python 3.10 – 3.13** (Python 3.11 recommended, e.g. via Homebrew: `brew install python@3.11`).
- Virtual environments use POSIX structure:
  ```bash
  python3.11 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip build wheel setuptools
  ```
- Note: POSIX virtual environment binaries are under `.venv/bin/python`, not `.venv/Scripts/python.exe`.

### 4.2 Building and Deploying the Wheel on macOS
- Run the multi-track pipeline script directly:
  ```bash
  python3 robotos/sdk/python-kws/publish_to_students.py
  # Or from kmutt-nd69:
  python3 ../sdk/python-kws/publish_to_students.py
  ```
- **Wheel Compatibility**: `robotos_edge-0.2.0-cp311-cp311-win_amd64.whl` is a pure-Python wheel (`py3-none-any`). It installs and executes natively on macOS (Apple Silicon arm64 & Intel x86_64), Linux, and Windows without recompilation.
- The pipeline script automatically detects POSIX paths (`.venv/bin/python`), updates wheels in all 3 tracks, audits against code leaks, and runs smoke tests.

### 4.3 Serial Port Naming on macOS (`/dev/cu.*` vs `/dev/tty.*`)
- On macOS, the ESP32-S3 USB Serial device appears under `/dev/cu.usbmodem*`:
  ```bash
  ls -l /dev/cu.usbmodem*
  ```
- **CRITICAL**: Always use `/dev/cu.usbmodem*` (callout device).
- **NEVER** use `/dev/tty.usbmodem*`: on macOS, opening `/dev/tty.*` blocks waiting for Data Carrier Detect (DCD) and will hang the Python process indefinitely.
- Example telemetry check on macOS:
  ```bash
  # Auto-detection:
  robotos check-imu

  # Or manual port:
  robotos check-imu --port /dev/cu.usbmodem1101
  ```

### 4.4 macOS Microphone Privacy Permissions (`sounddevice`)
- For audio keyword spotting data collection (ND1 / ND2 PC microphone) and sound synthesis (ND3 Air Drum):
- macOS requires explicit microphone / audio access granted to the terminal or IDE:
  `System Settings -> Privacy & Security -> Microphone -> Enable for Terminal / iTerm / VS Code / Cursor / Antigravity`.
- If permission is denied, `sounddevice` will raise `PortAudioError` or return silent zero-buffers.
- If PortAudio dynamic library is needed: `brew install portaudio`.

### 4.5 Architectural Separation: `robotos` vs `robotos-kws` on macOS
Agents must maintain the strict separation of concerns across all platforms:
- **`robotos`** (Platform & Hardware CLI — NO ML dependencies):
  - `robotos detect`
  - `robotos flash-firmware`
  - `robotos check-imu`
  - `robotos check-board`
  - `robotos devices`
- **`robotos-kws`** (Machine Learning & Edge AI Toolkit):
  - `robotos-kws collect-imu` / `collect-pc` / `collect-board`
  - `robotos-kws train-imu` / `train`
  - `robotos-kws live-imu` / `live-pc` / `live-board`
  - `robotos-kws evaluate` / `export` / `verify-c`

### 4.6 Running Student Lab Applications on macOS
Interactive lab applications are standalone Python scripts that import `DrumPolySynth` or `wire` from the installed wheel:
- **Interactive Air Drum:**
  ```bash
  cd nd3/docs/week08/labs
  python3 air_drum.py
  # With manual port:
  python3 air_drum.py --port /dev/cu.usbmodem1101
  # Built-in demo:
  python3 air_drum.py --demo
  # Offline replay:
  python3 air_drum.py --replay samples/circle.csv
  ```
- **Robotic Finite State Machine:**
  ```bash
  cd nd3/docs/week08/labs
  python3 robot_fsm.py --model imu_artifacts/model_int8.tflite
  ```
*(On macOS, if multiple Pythons are present, invoke `.venv/bin/python3 air_drum.py` to ensure the virtual environment is used)*.

---

## 5. Web Application & Backend Services (ND2 Track)

- ND2 lab features a FastAPI backend located at `nd2/docs/week08/labs/web-app/server.py`.
- **Default Port**: `8000` (`http://127.0.0.1:8000`).
- **Health check**: `curl http://127.0.0.1:8000/api/v1/model/info`.
- **Frontend Vite UI**: Located at `nd2/docs/week08/labs/web-app/ui/` running on port `5173`.
- Before starting a new server instance, check if port 8000 is already active to avoid `Errno 10048` / `EADDRINUSE`.

---

## 6. Git Commit & Push Guidelines

- Changes to student curriculum, documentation, wheels, and track examples belong to `kmutt-nd69` (branch `main`).
- Always run `git status` and verify that no unwanted temporary files (`.pyc`, caches, raw sources) are staged.
- Commit messages should clearly describe the track affected (e.g., `[week08] bump robotos_kws to 0.1.1 and sync across all student tracks`).

---

## 7. Historical Handoff Notes (2026-11-16)

For reference regarding the 2026-11-16 configurable-frame migration:
- Refer to `docs/MACOS-COORDINATE-HANDOFF.md` in the parent `robotos` repository.
- Legacy lessons keep XY/Z-yaw messages while the simulator renders Y-up.
- World convention changes do not redefine touchscreen or firmware sensor/body axes.

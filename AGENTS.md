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
- Both boards (ws28p, es3c28p) use the ESP32-S3 native USB Serial/JTAG controller (`USB VID:PID = 303A:1001`), which can reset the chip from the DTR/RTS line states.
- **Measured on an es3c28p (fw `robotos-fw/0.3.0`, macOS, 2026-11-27)** — port open, no commands sent, 9 s:
  | Lines while open | Result |
  | :--- | :--- |
  | DTR **low**, RTS low | Board reboots ~4 s after open (ROM prints `rst:0x15 (USB_UART_CHIP_RESET)`), then every command gets "No reply from board" |
  | DTR high, RTS high (pyserial default) | Board resets at open (~5 s of silence), then streams |
  | **DTR high, RTS low** | **Streams the whole time, no reset** |
- **Rule:** open with `rts=False, dtr=True` set *before* `open()`; never assert RTS; on close only drop RTS and close:
  ```python
  ser = serial.Serial()
  ser.port = port
  ser.baudrate = 921600   # ignored by USB Serial/JTAG
  ser.rts = False         # RTS = EN: never pull it
  ser.dtr = True          # DTR low made the board reboot ~4 s after open
  ser.open()
  ...
  ser.rts = False
  ser.close()
  ```
- **Do not change these line states without re-testing on a real board.** An earlier rule here ("always set DTR=False") caused exactly the reboot loop above. The 4 s delay is not explained by the documented `RTS=1, DTR=0` reset trigger, so treat the table as measured behavior, not theory, and re-check on Windows.
- How to see a reset: data stops for ~4.5 s and the ROM banner `rst:0x15 (USB_UART_CHIP_RESET)` appears on the port.
- Side effect: without the reboot, an idle board sends `BoardInfo` only every 10–30 s, so tools must not wait for BoardInfo alone (the SDK switches the mic on briefly to identify an es3c28p).
- **Never** use PySerial's default constructor (`serial.Serial(port, baudrate)`): it raises both lines on open, which resets the board.

### Firmware Flashing Command (ND1, ND2, ND3)
```bash
# Auto-detects port, downloads prebuilt binaries, flashes, and verifies.
# ALWAYS pass --board: it defaults to ws28p and flashes whatever ESP32-S3 is found,
# so a bare command would put IMU firmware on an es3c28p (mic) board.
robotos flash-firmware --board ws28p      # or --board es3c28p

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
- **Wheel Compatibility**: `robotos_edge` 0.2.0 is a compiled (Cython) wheel for CPython 3.11, one file per platform: `…-win_amd64.whl` (build on Windows) and `…-macosx_11_0_arm64.whl` (build on macOS). There is no Linux wheel yet, so Google Colab cannot install it. Student docs install by name (`pip install --no-index -f ../dist robotos_edge`), so pip picks the right file per OS; keep one wheel per platform in each `dist/`.
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

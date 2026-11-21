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

### Live Verification Command
```bash
robotos-kws check-imu --port <COM_PORT>
```
Expected behavior:
- Connects cleanly without restarting the board.
- Streams 150+ samples at 50 Hz with 0 lost packets.
- Exits cleanly without rebooting the board.

---

## 4. Web Application & Backend Services (ND2 Track)

- ND2 lab features a FastAPI backend located at `nd2/docs/week08/labs/web-app/server.py`.
- **Default Port**: `8000` (`http://127.0.0.1:8000`).
- **Health check**: `curl http://127.0.0.1:8000/api/v1/model/info`.
- **Frontend Vite UI**: Located at `nd2/docs/week08/labs/web-app/ui/` running on port `5173`.
- Before starting a new server instance, check if port 8000 is already active to avoid `Errno 10048` (Address already in use).

---

## 5. Git Commit & Push Guidelines

- Changes to student curriculum, documentation, wheels, and track examples belong to `kmutt-nd69` (branch `main`).
- Always run `git status` and verify that no unwanted temporary files (`.pyc`, caches, raw sources) are staged.
- Commit messages should clearly describe the track affected (e.g., `[week08] bump robotos_kws to 0.1.1 and sync across all student tracks`).

---

## 6. Historical Handoff Notes (2026-11-16)

For reference regarding the 2026-11-16 configurable-frame migration:
- Refer to `docs/MACOS-COORDINATE-HANDOFF.md` in the parent `robotos` repository.
- Legacy lessons keep XY/Z-yaw messages while the simulator renders Y-up.
- World convention changes do not redefine touchscreen or firmware sensor/body axes.

# Rule: Multi-Track robotos_kws SDK Synchronization & Cross-Platform Safety

## 1. Single Source of Truth
- The source of truth for `robotos_kws` is `robotos/sdk/python-kws/`.
- Never edit wheel contents directly.
- Never copy raw `.py` SDK code into student track directories (`nd1`, `nd2`, `nd3`). Only wheels (`.whl`) and examples belong in student tracks.

## 2. Multi-Track Wheel Parity
- All 3 student tracks MUST use the exact same wheel version in `docs/week08/labs/dist/`.
- Whenever `robotos/sdk/python-kws` is updated, run:
  - Windows: `python robotos/sdk/python-kws/publish_to_students.py`
  - macOS: `python3 robotos/sdk/python-kws/publish_to_students.py`
- Verify that all 3 tracks pass smoke tests.

## 3. ESP32-S3 Hardware Serial Safety (Windows & macOS)
- Native USB Serial/JTAG (`303A:1001`) resets when `RTS=1, DTR=0` is set.
- Always initialize PySerial with `rts=False, dtr=False` before opening.
- Always set `ser.rts=False; ser.dtr=False; ser.close()` when exiting.
- Never use default `serial.Serial()` constructor without clearing RTS/DTR.

## 4. macOS-Specific Rules
- **Serial Port Device**: Always use `/dev/cu.usbmodem*` (callout device). NEVER use `/dev/tty.usbmodem*` (which blocks on carrier detect).
- **Audio / Mic Permission**: Ensure Terminal / IDE has microphone access granted in `System Settings -> Privacy & Security -> Microphone` for PC microphone keyword spotting.
- **Virtual Environment**: Use POSIX `.venv/bin/python` (not `Scripts/python.exe`).

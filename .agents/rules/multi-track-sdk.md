# Rule: Multi-Track robotos_kws SDK Synchronization & Hardware Safety

## 1. Single Source of Truth
- The source of truth for `robotos_kws` is `robotos/sdk/python-kws/`.
- Never edit wheel contents directly.
- Never copy raw `.py` SDK code into student track directories (`nd1`, `nd2`, `nd3`). Only wheels (`.whl`) and examples belong in student tracks.

## 2. Multi-Track Wheel Parity
- All 3 student tracks MUST use the exact same wheel version in `docs/week08/labs/dist/`.
- Whenever `robotos/sdk/python-kws` is updated, run:
  `python robotos/sdk/python-kws/publish_to_students.py`
- Verify that all 3 tracks pass smoke tests.

## 3. ESP32-S3 Hardware Serial Safety
- Native USB Serial/JTAG (`303A:1001`) resets when `RTS=1, DTR=0` is set.
- Always initialize PySerial with `rts=False, dtr=False` before opening.
- Always set `ser.rts=False; ser.dtr=False; ser.close()` when exiting.
- Never use default `serial.Serial()` constructor without clearing RTS/DTR.

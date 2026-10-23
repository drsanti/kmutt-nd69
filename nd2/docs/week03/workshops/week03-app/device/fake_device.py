#!/usr/bin/env python3
"""Fake device — stands in for the ESP32 board this week.

Talks the same JSON-lines protocol the web app (and next week's
real board) uses:

    device → app:  {"type":"telemetry","seq":N,"level":0..1,"ts_ms":T}
    app → device:  {"type":"led","r":..,"g":..,"b":..}
                   {"type":"rate","hz":N}

Usage:
    python3 fake_device.py /dev/ttys002          # one end of the pair
    python3 fake_device.py COM5                  # Windows
    python3 fake_device.py /dev/ttys002 --hz 10  # telemetry rate
"""
import argparse
import json
import math
import random
import sys
import time

try:
    import serial                       # pyserial
except ImportError:
    sys.exit("pyserial required — pip install pyserial")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("port", help="serial port (one end of the virtual pair)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--hz", type=float, default=5.0,
                    help="telemetry rate (device default)")
    args = ap.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=0.1)
    hz = args.hz
    led_state = {"r": 0, "g": 0, "b": 0}
    seq = 0
    next_tx = time.monotonic()

    print(f"fake_device on {args.port} @ {args.baud} — "
          f"telemetry {hz} Hz, Ctrl-C to stop")
    buf = b""
    try:
        while True:
            # --- emit telemetry at the configured rate ---
            now = time.monotonic()
            if now >= next_tx:
                t = time.time()
                level = (0.5 + 0.4 * math.sin(t * 2.0)
                         + random.uniform(-0.05, 0.05))
                msg = {
                    "type": "telemetry",
                    "seq": seq,
                    "level": round(max(0.0, min(1.0, level)), 3),
                    "ts_ms": int(t * 1000),
                }
                ser.write((json.dumps(msg) + "\n").encode())
                seq += 1
                next_tx = now + 1.0 / hz

            # --- drain incoming commands ---
            data = ser.read(ser.in_waiting or 1)
            if data:
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cmd = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"  rx (non-JSON): {line!r}")
                        continue
                    if cmd.get("type") == "led":
                        led_state.update(
                            {k: int(cmd.get(k, 0)) for k in "rgb"})
                        print(f"  led → rgb({led_state['r']},"
                              f"{led_state['g']},{led_state['b']})")
                    elif cmd.get("type") == "rate":
                        hz = max(0.1, min(100.0, float(cmd["hz"])))
                        print(f"  rate → {hz} Hz")
                    else:
                        print(f"  rx (unknown): {cmd}")
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print(f"\n{seq} telemetry messages sent")


if __name__ == "__main__":
    main()

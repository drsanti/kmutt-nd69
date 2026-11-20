#!/usr/bin/env python3
"""Collect labelled touch-screen strokes from the board (gesture track).

Flash labs/firmware/touch-logger, then:

    python collect_touch.py --port COM5 --speaker alice --session s01 --takes 15

For each take, draw the requested shape with ONE finger on the screen and lift.
Strokes are saved as  touch_dataset/<gesture>/<session>_<speaker>_board_<index>.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import touch_common as tc


def read_stroke(ser, timeout_s: float = 15.0):
    """Wait for a D ... U sequence and return [(t, x, y), ...]."""
    import time
    stroke, end = None, time.monotonic() + timeout_s
    while time.monotonic() < end:
        line = ser.readline().decode("utf-8", "replace").split()
        if not line:
            continue
        kind = line[0]
        if kind == "D" and len(line) == 4:
            stroke = [(int(line[3]), int(line[1]), int(line[2]))]
        elif kind == "M" and len(line) == 4 and stroke is not None:
            stroke.append((int(line[3]), int(line[1]), int(line[2])))
        elif kind == "U" and stroke is not None:
            return stroke
        elif kind == "E":
            print(f"    [board] I2C error {' '.join(line[1:])}")
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--out", type=Path, default=Path("touch_dataset"))
    ap.add_argument("--speaker", default="me")
    ap.add_argument("--session", default="s01")
    ap.add_argument("--labels", nargs="+", default=tc.GESTURES)
    ap.add_argument("--takes", type=int, default=15)
    ap.add_argument("--min-points", type=int, default=5, help="reject taps shorter than this")
    args = ap.parse_args(argv)

    import serial
    ser = serial.Serial()
    ser.port, ser.baudrate, ser.timeout, ser.dtr, ser.rts = args.port, 115200, 0.2, False, False
    ser.open()
    try:
        for label in args.labels:
            print(f"\n=== draw a {label.upper()} ({args.takes} takes)")
            t = 0
            while t < args.takes:
                print(f"  [{t + 1}/{args.takes}] draw now...", flush=True)
                stroke = read_stroke(ser)
                if not stroke or len(stroke) < args.min_points:
                    print("    too short / timeout - try again")
                    continue
                path = tc.next_path(args.out, label, args.session, args.speaker)
                tc.save_stroke(path, stroke)
                print(f"    saved {path} ({len(stroke)} points, {stroke[-1][0] - stroke[0][0]} ms)")
                t += 1
    finally:
        ser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

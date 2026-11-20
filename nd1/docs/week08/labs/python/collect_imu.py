#!/usr/bin/env python3
"""Record labelled IMU gesture windows from the ws28p board over USB.

The board runs the hardware-interface-workshop PREBUILT firmware for ws28p
(``rb config --board ws28p`` + ``rb flash-bin``). It streams one Imu frame about
every 20 ms without being asked - this script only listens (see wire.py):

    1. open the port, wait ~2.5 s (opening USB can reset the board)
    2. check the board has an IMU (BoardInfo caps 0x3c, or IMU frames arriving);
       the es3c28p (caps 0x33, no IMU) is rejected with a clear message
    3. per take: countdown, then record WINDOW_S seconds of samples
    4. gaps in the board timestamps = lost frames; too many -> take re-recorded
    5. resample onto an exact 50 Hz grid (100 x 6) and save a CSV

Files: <out>/<gesture>/<session>_<person>_ws28p_<index>.csv
Pack everything into one array file with:  python imu_common.py pack --data imu_dataset

Examples
    python collect_imu.py --port COM7 --check
    python collect_imu.py --port /dev/ttyACM0 --person alice --session s01 --takes 20
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

import imu_common as ic
import wire

HOW = {"idle": "hold the board still (or rest it in your hand, any natural pose)",
       "shake": "shake it left-right quickly",
       "circle": "draw one or two circles in the air with it",
       "lift": "lift it up and put it down"}


def imu_samples(sess: wire.BoardSession, timeout: float = 0.05):
    for f in sess.poll(timeout):
        if f.msg_type == wire.MSG_IMU:
            s = wire.decode_imu(f.payload)
            t = s.timestamp_ns / 1e9 if s.timestamp_ns else time.monotonic()
            yield t, s.accel, s.gyro


def record_window(sess: wire.BoardSession, seconds: float):
    """Collect samples covering `seconds` (+ a little margin); returns (t, data)."""
    t, x = [], []
    end = time.monotonic() + seconds + 3.0
    while time.monotonic() < end:
        for ts, a, g in imu_samples(sess):
            t.append(ts)
            x.append([*a, *g])
        if len(t) >= 2 and t[-1] - t[0] >= seconds:
            return np.array(t), np.array(x, dtype=np.float32)
    raise wire.WireError(f"IMU stream stalled ({len(t)} samples in {seconds + 3:.0f} s)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--out", type=Path, default=Path("imu_dataset"))
    ap.add_argument("--person", default="me")
    ap.add_argument("--session", default="s01")
    ap.add_argument("--labels", nargs="+", default=ic.GESTURES)
    ap.add_argument("--takes", type=int, default=10)
    ap.add_argument("--countdown", type=float, default=1.0, help="seconds between Enter and recording")
    ap.add_argument("--max-lost", type=int, default=3, help="re-record a take that lost more samples than this")
    ap.add_argument("--no-prompt", action="store_true")
    ap.add_argument("--check", action="store_true", help="print BoardInfo and live values for 3 s, then exit")
    ap.add_argument("--settle", type=float, default=wire.SETTLE_S, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    bad = [lb for lb in args.labels if lb not in ic.GESTURES]
    if bad:
        ap.error(f"unknown gesture(s) {bad}; edit GESTURES in imu_common.py to add your own")
    if not ic.FILENAME_RE.match(f"{args.session}_{args.person}_ws28p_0000.csv"):
        ap.error("session must look like s01 and person may contain only letters, digits and '-'")

    try:
        sess = wire.BoardSession.open(args.port, settle_s=args.settle)
    except wire.WireError as e:
        print(f"ERROR: {e}")
        return 2
    try:
        info = sess.wait_board_info(need_cap=wire.CAP_IMU, need_name="collect_imu.py")
        print(f"Board: {info.describe() if info.uuid else 'IMU stream detected'}")
        if args.check:
            t, x = record_window(sess, 3.0)
            rate = (len(t) - 1) / (t[-1] - t[0])
            print(f"{len(t)} samples, {rate:.1f} Hz, lost {ic.count_gaps(t)}")
            print(f"mean accel (m/s^2) {np.round(x[:, :3].mean(0), 2)}  |a| {np.linalg.norm(x[:, :3].mean(0)):.2f}"
                  "  (about 9.8 when still)")
            print(f"gyro std (rad/s)   {np.round(x[:, 3:].std(0), 3)}")
            return 0
        print(f"Saving to {args.out.resolve()}  (person={args.person}, session={args.session}); "
              f"window {ic.WINDOW_S:.1f} s @ {ic.RATE_HZ} Hz")
        for label in args.labels:
            print(f"\n=== {label}: {args.takes} takes - {HOW.get(label, label)}")
            k = 0
            while k < args.takes:
                if not args.no_prompt:
                    if input(f"  [{k + 1}/{args.takes}] Enter = record, q = quit > ").strip().lower() == "q":
                        return 0
                sess.drain()
                if args.countdown > 0:
                    print("    get ready...", end="", flush=True)
                    end = time.monotonic() + args.countdown
                    while time.monotonic() < end:
                        sess.poll(0.05)
                print(" GO", flush=True)
                try:
                    t, x = record_window(sess, ic.WINDOW_S)
                except wire.WireError as e:
                    print(f"    [retry] {e}")
                    continue
                lost = ic.count_gaps(t)
                if lost > args.max_lost:
                    print(f"    [retry] {lost} samples lost (timestamp gaps) - take discarded")
                    continue
                win = ic.to_grid(t, x)
                path = ic.next_path(args.out, label, args.session, args.person)
                ic.save_window(path, win)
                motion = float(np.linalg.norm(win[:, :3] - win[:, :3].mean(0), axis=1).mean())
                print(f"    saved {path}  motion {motion:5.2f} m/s^2  lost {lost}")
                k += 1
    except wire.WrongBoard as e:
        print(f"ERROR: {e}")
        return 3
    except wire.WireError as e:
        print(f"ERROR: {e}")
        return 2
    finally:
        sess.close()
    print(f"\nDone. Next: python train_imu.py --data {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

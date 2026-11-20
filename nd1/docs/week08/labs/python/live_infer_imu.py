#!/usr/bin/env python3
"""Run the IMU gesture model on your computer, LIVE, fed by the ws28p board.

The board keeps the workshop prebuilt firmware and streams Imu frames (~50 Hz);
this script keeps the newest 2 s, runs the model every --hop-ms and prints a
gesture when the smoothed score passes --threshold ("idle" never triggers).

    python live_infer_imu.py --port COM7 --model imu_artifacts/model_int8.tflite
    python live_infer_imu.py --replay imu_dataset/shake/s01_me_ws28p_0000.csv --model ...   # no board
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np

import imu_common as ic
import kws_common as kc
import wire


class GestureDetector:
    def __init__(self, model_path, hop_ms=200, smooth=3, threshold=0.7, refractory_ms=1000):
        self.name = Path(model_path).name
        self.interp = kc.make_interpreter(model_path)
        self.win = ic.ImuWindow()
        self.hop = max(1, int(ic.RATE_HZ * hop_ms / 1000))
        self.hist = deque(maxlen=smooth)
        self.threshold = threshold
        self.refractory = refractory_ms / 1000
        self.last_hit = -1e9
        self.since = 0
        self.detections = []        # (t_s, label, score)
        self.infer_ms = deque(maxlen=50)

    def push(self, t_s, accel, gyro):
        self.win.push(t_s, accel, gyro)
        self.since += 1
        if self.since >= self.hop and self.win.ready():
            self.since = 0
            self._step(t_s)

    def _step(self, t_s):
        x = ic.normalise(self.win.window())
        t0 = time.perf_counter()
        probs = kc.run_tflite(self.interp, x)
        self.infer_ms.append(1000 * (time.perf_counter() - t0))
        self.hist.append(probs)
        avg = np.mean(self.hist, axis=0)
        top = int(np.argmax(avg))
        label, score = ic.GESTURES[top], float(avg[top])
        hit = label != "idle" and score >= self.threshold and t_s - self.last_hit >= self.refractory
        line = f"\r[lost {self.win.lost:3d}] {label:<7} {score:4.2f}  " + " ".join(
            f"{g}:{p:.2f}" for g, p in zip(ic.GESTURES, avg))
        if hit:
            self.last_hit = t_s
            self.detections.append((t_s, label, score))
            line += "  <== " + label.upper()
        print(line, end="\n" if hit else "", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port")
    src.add_argument("--replay", type=Path, nargs="+", help="CSV windows to play back instead of a board")
    ap.add_argument("--model", type=Path, default=Path("imu_artifacts/model_int8.tflite"))
    ap.add_argument("--hop-ms", type=int, default=200)
    ap.add_argument("--smooth", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--refractory-ms", type=int, default=1000)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--settle", type=float, default=wire.SETTLE_S, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    det = GestureDetector(args.model, args.hop_ms, args.smooth, args.threshold, args.refractory_ms)
    if args.replay:
        t = 0.0
        for path in args.replay:
            for row in ic.load_window(path):
                det.push(t, row[:3], row[3:])
                t += 1 / ic.RATE_HZ
            for _ in range(ic.WINDOW):          # 2 s of stillness between files
                det.push(t, (0, 0, ic.G), (0, 0, 0))
                t += 1 / ic.RATE_HZ
    else:
        try:
            sess = wire.BoardSession.open(args.port, settle_s=args.settle)
        except wire.WireError as e:
            print(f"ERROR: {e}")
            return 2
        try:
            info = sess.wait_board_info(need_cap=wire.CAP_IMU, need_name="live_infer_imu.py")
            print(f"Board: {info.describe() if info.uuid else 'IMU stream detected'}\n"
                  f"Gestures: {ic.GESTURES}  (Ctrl+C to stop)")
            t0 = last = time.monotonic()
            while args.seconds is None or time.monotonic() - t0 < args.seconds:
                for f in sess.poll(0.05):
                    if f.msg_type == wire.MSG_IMU:
                        s = wire.decode_imu(f.payload)
                        det.push(s.timestamp_ns / 1e9 if s.timestamp_ns else time.monotonic(), s.accel, s.gyro)
                        last = time.monotonic()
                if time.monotonic() - last > 1.0:
                    print("\n[board] no IMU frames for 1 s - unplugged, or a browser tab holds the port?",
                          file=sys.stderr)
                    last = time.monotonic()
        except KeyboardInterrupt:
            pass
        except wire.WrongBoard as e:
            print(f"ERROR: {e}")
            return 3
        except wire.WireError as e:
            print(f"ERROR: {e}")
            return 2
        finally:
            sess.close()
    print(f"\n\nSamples {det.win.count}, lost {det.win.lost}")
    print("Detections:")
    for t, label, score in det.detections:
        print(f"  t={t:7.2f} s  {label:<7} score {score:.2f}")
    if det.infer_ms:
        print(f"PC timing: model {np.mean(det.infer_ms):.2f} ms per step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

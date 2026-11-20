#!/usr/bin/env python3
"""Run the keyword model on your computer, LIVE, fed by the ES3C28P board microphone.

The board keeps the workshop prebuilt firmware: it only streams 16 kHz audio
(MicPcm frames) over USB; features and the model run here with exactly the same
code as live_infer_pc.py. This is the in-class live test of the board-mic model.

    python live_infer_board.py --port COM5 --model artifacts/model_int8.tflite
    python live_infer_board.py --port /dev/ttyACM0 --model artifacts/model_float.tflite artifacts/model_int8.tflite

Lost USB chunks (MicPcm.seq gaps) are replaced by silence and counted, so timing
stays correct. Close the workshop browser tab first (only one program may own the port).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

import kws_common as kc
import wire
from live_infer_pc import Detector


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True)
    ap.add_argument("--model", nargs="+", type=Path, default=[Path("artifacts/model_int8.tflite")])
    ap.add_argument("--gain", type=int, default=60)
    ap.add_argument("--board-rate", type=int, default=wire.MIC_RATE_HZ)
    ap.add_argument("--hop-ms", type=int, default=250)
    ap.add_argument("--smooth", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--refractory-ms", type=int, default=1000)
    ap.add_argument("--seconds", type=float, help="stop after this many seconds")
    ap.add_argument("--settle", type=float, default=wire.SETTLE_S, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    det = Detector(args.model, args.hop_ms, args.smooth, args.threshold, args.refractory_ms)
    try:
        sess = wire.BoardSession.open(args.port, settle_s=args.settle)
    except wire.WireError as e:
        print(f"ERROR: {e}")
        return 2
    rc = 0
    mic = None
    t0 = time.monotonic()
    try:
        info = sess.wait_board_info(need_cap=wire.CAP_MIC, need_name="live_infer_board.py")
        print(f"Board: {info.describe()}\nKeywords: {kc.KEYWORDS}  (Ctrl+C to stop)")
        mic = wire.MicStream(sess, args.board_rate)
        mic.enable(args.gain)
        mic.start()
        t0 = time.monotonic()
        last = time.monotonic()
        while args.seconds is None or time.monotonic() - t0 < args.seconds:
            mic.pump(0.05)
            if len(mic.buf) >= det.hop:
                pcm = np.asarray(mic.buf, dtype=np.int16)
                mic.buf = []
                if args.board_rate != kc.SAMPLE_RATE:
                    pcm = kc.resample(pcm, args.board_rate)
                det.push(pcm)
                last = time.monotonic()
            elif time.monotonic() - last > 1.5:
                print("\n[board] no audio for 1.5 s - restarting the stream", file=sys.stderr)
                mic.start(warmup_s=0)
                last = time.monotonic()
    except KeyboardInterrupt:
        pass
    except wire.WrongBoard as e:
        print(f"ERROR: {e}")
        rc = 3
    except wire.WireError as e:
        print(f"ERROR: {e}")
        rc = 2
    finally:
        if mic is not None:
            mic.stop()
        sess.close()
    if rc:
        return rc
    secs = det.samples_seen / kc.SAMPLE_RATE
    print(f"\n\nStreamed {secs:.1f} s of board audio in {time.monotonic() - t0:.1f} s wall time; "
          f"lost chunks: {mic.asm.lost_chunks if mic else 0} of {mic.asm.chunks if mic else 0}")
    print("Detections:")
    for t, name, label, score in det.detections:
        print(f"  t={t:6.2f} s  {name:<20} {label:<8} score {score:.2f}")
    if det.feature_ms:
        print(f"PC timing: features {np.mean(det.feature_ms):.2f} ms, model {np.mean(det.infer_ms):.2f} ms per step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

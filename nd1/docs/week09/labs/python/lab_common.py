"""Shared helpers for the Week 09 labs: pick a live board or a recorded IMU file."""
import argparse
from pathlib import Path

import robotos_edge as rk

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "samples"


def parse_args(description: str, seconds: float = 60.0):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--port", default=None, help="serial port (auto-detected if omitted)")
    ap.add_argument("--replay", nargs="*", metavar="CSV",
                    help="no board: play recorded IMU files (default: all files in samples/)")
    ap.add_argument("--seconds", type=float, default=seconds, help="stop after this many seconds")
    return ap.parse_args()


def replay_files(args):
    order = ["idle", "shake", "circle", "lift"]            # still first, so "noise while still" makes sense
    found = sorted(SAMPLES.glob("*.csv"), key=lambda p: (order.index(p.stem) if p.stem in order else 9, p.name))
    files = args.replay if args.replay else [str(p) for p in found]
    if not files:
        raise SystemExit(f"no CSV files found in {SAMPLES}")
    return files


def imu_source(args, session=None):
    """Live samples from the board (needs a ws28p) or, with --replay, from recorded files."""
    if args.replay is not None:
        print("IMU source: replay of", ", ".join(Path(f).name for f in replay_files(args)))
        return rk.ImuReplay(*replay_files(args), loop=True)
    if session is None:
        raise SystemExit("live IMU needs a board session")
    print("IMU source: live board")
    return rk.ImuStream(session)

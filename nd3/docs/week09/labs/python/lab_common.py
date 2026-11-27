"""Shared helpers for the Week 09 labs: board screen, live IMU (ws28p) or recorded motion."""
import argparse
import time
from pathlib import Path

import robotos_edge as rk

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "samples"
ORDER = ["idle", "shake", "circle", "lift"]


def parse_args(description: str, seconds: float = 60.0, extra=None):
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--port", default=None, help="serial port (auto-detected if omitted)")
    ap.add_argument("--replay", nargs="*", metavar="CSV",
                    help="no ws28p: use recorded IMU files (default: all files in samples/)")
    ap.add_argument("--seconds", type=float, default=seconds, help="stop after this many seconds")
    if extra:
        extra(ap)
    return ap.parse_args()


def imu_source(args, session, default=None):
    """Live samples from a ws28p or, with --replay, recorded files (looped).

    ``default`` = list of sample names (e.g. ["idle", "idle", "shake"]) used when --replay has no files."""
    if args.replay is not None:
        found = sorted(SAMPLES.glob("*.csv"), key=lambda p: (ORDER.index(p.stem) if p.stem in ORDER else 9, p.name))
        if default:
            found = [SAMPLES / f"{name}.csv" for name in default]
        files = args.replay or [str(p) for p in found]
        print("IMU source: replay of", ", ".join(Path(f).name for f in files))
        return rk.ImuReplay(*files, loop=True)
    print("IMU source: live board")
    return rk.ImuStream(session)


class Clock:
    """Frame timing for animations: dt (seconds since the last frame) and a smoothed fps."""

    def __init__(self, fps: float = 15.0):
        self.period = 1.0 / fps
        self.last = time.monotonic()
        self.fps = 0.0

    def tick(self) -> float:
        """Wait until the next frame is due, then return dt (s)."""
        now = time.monotonic()
        wait = self.last + self.period - now
        if wait > 0:
            time.sleep(wait)
            now = time.monotonic()
        dt, self.last = now - self.last, now
        self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt) if self.fps else 1.0 / dt
        return dt

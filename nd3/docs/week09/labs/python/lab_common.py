"""Shared helpers for the Week 09 labs: board screen, live IMU (ws28p) or recorded motion."""
import argparse
import re
import sys
import textwrap
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


# ------------------------------------------------------------------ start-up guide
WIDTH = 78
_TODO = re.compile(r"^\s*#\s*(?:>>> )?TODO (\d+): (.*?)(?: \| starter: .*)?$")


def _wrap(label: str, text: str) -> list:
    pad = " " * (len(label) + 2)
    return textwrap.wrap(text, WIDTH - 1, initial_indent=f" {label} ", subsequent_indent=pad) or [f" {label}"]


def _todos(script: Path) -> list:
    """The TODO tasks written in the lab file itself (first clause of each)."""
    out = []
    try:
        for line in script.read_text(encoding="utf-8").splitlines():
            m = _TODO.match(line)
            if m:
                desc = re.split(r"(?<=[a-z0-9)]): |; |\. ", m[2], maxsplit=1)[0].rstrip(".")
                out.append((m[1], desc))
    except OSError:
        pass
    return out


def intro(doc: str, args=None, live: str = "", replay: str = "", do: str = "", look: str = "",
          before: str = "") -> None:
    """Print what this lab is, what it does, what to do now and what to look for.

    ``live``/``replay``: what to do with a live board / with recorded motion (labs that use the IMU);
    ``do``: what to do (labs that do not use the IMU); ``look``: what to watch for when the lab is done;
    ``before``: what the unchanged starter shows instead (so an unfinished lab does not look broken)."""
    paras = [p.strip() for p in (doc or "").strip().split("\n\n")]
    title = paras[0].splitlines()[0] if paras else Path(sys.argv[0]).stem
    what = " ".join(paras[1].split()) if len(paras) > 1 else ""
    using_replay = args is not None and getattr(args, "replay", None) is not None
    print("=" * WIDTH)
    print(f" {title}")
    print("=" * WIDTH)
    lines = []
    if what:
        lines += _wrap("What it does:", what)
    if live or replay:
        mode = "recorded motion (--replay)" if using_replay else "live board"
        lines += _wrap("Mode:        ", mode + ("" if using_replay else "  - no ws28p? run it again with --replay"))
        lines += _wrap("Do now:      ", replay if using_replay else live)
    elif do:
        lines += _wrap("Do now:      ", do)
    if look:
        lines += _wrap("Look for:    ", look)
    if before:
        lines += _wrap("Before TODOs:", before)
    todos = _todos(Path(sys.argv[0]).resolve())
    if todos:
        lines.append(" Your tasks (TODOs in this file):")
        for n, d in todos:
            lines += textwrap.wrap(d, WIDTH - 1, initial_indent=f"   TODO {n}: ", subsequent_indent=" " * 11)
    lines.append(f" Stop: Ctrl+C    Options: python {Path(sys.argv[0]).name} --help")
    print("\n".join(lines))
    print("-" * WIDTH, flush=True)

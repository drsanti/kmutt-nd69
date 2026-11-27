"""Shared helpers for the Week 09 labs: pick a live board or a recorded IMU file."""
import argparse
import re
import sys
import textwrap
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


# ------------------------------------------------------------------ start-up guide
WIDTH = 78
_TODO = re.compile(r"^\s*#\s*(?:>>> )?(?:TODO|Step) (\d+): (.*?)(?: \| starter: .*)?$")


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
        demo = "TODO" not in Path(sys.argv[0]).read_text(encoding="utf-8")
        lines.append(" Key steps in the code:" if demo else " Your tasks (TODOs in this file):")
        for n, d in todos:
            lines += textwrap.wrap(d, WIDTH - 1, initial_indent=f"   {'Step' if demo else 'TODO'} {n}: ", subsequent_indent=" " * 11)
    lines.append(f" Stop: Ctrl+C    Options: python {Path(sys.argv[0]).name} --help")
    print("\n".join(lines))
    print("-" * WIDTH, flush=True)

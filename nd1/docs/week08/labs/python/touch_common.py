"""Shared stroke handling for the touch-screen gesture track (lighter alternative).

A stroke is the list of (t_ms, x, y) points between finger DOWN and UP. Before the
model sees it, every stroke is resampled to NUM_POINTS points equally spaced along
its path, moved so its centre is at (0, 0) and scaled so its larger side is 1.
That makes the gesture independent of where and how big it was drawn and of drawing
speed - the same steps must run on the board if you deploy the model.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np

GESTURES = ["circle", "triangle", "check", "line"]
NUM_POINTS = 32
SCREEN_W, SCREEN_H = 240, 320          # raw FT6336G range on the ES3C28P panel
FILENAME_RE = re.compile(r"^(?P<session>s\d+)_(?P<speaker>[A-Za-z0-9-]+)_(?P<device>board|synth)_(?P<index>\d+)\.csv$")


def resample(points: np.ndarray, n: int = NUM_POINTS) -> np.ndarray:
    """Resample an (N, 2) path to n points equally spaced by arc length."""
    pts = np.asarray(points, dtype=np.float64)
    if len(pts) == 1:
        return np.repeat(pts, n, axis=0)
    seg = np.sqrt((np.diff(pts, axis=0) ** 2).sum(axis=1))
    dist = np.concatenate([[0.0], np.cumsum(seg)])
    if dist[-1] == 0:
        return np.repeat(pts[:1], n, axis=0)
    target = np.linspace(0, dist[-1], n)
    return np.stack([np.interp(target, dist, pts[:, 0]), np.interp(target, dist, pts[:, 1])], axis=1)


def normalise(points: np.ndarray) -> np.ndarray:
    pts = resample(points)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    centre = (lo + hi) / 2
    scale = max(hi - lo) or 1.0
    return ((pts - centre) / scale).astype(np.float32)


def save_stroke(path: Path, stroke) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ms", "x", "y"])
        w.writerows(stroke)


def load_stroke(path: Path) -> np.ndarray:
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return np.array([[float(r["x"]), float(r["y"])] for r in rows])


def scan(root: Path):
    items = []
    for label in GESTURES:
        for p in sorted((Path(root) / label).glob("*.csv")):
            m = FILENAME_RE.match(p.name)
            if m:
                items.append((p, label, m["speaker"], m["session"]))
    return items


def next_path(root: Path, label: str, session: str, speaker: str, device: str = "board") -> Path:
    folder = Path(root) / label
    folder.mkdir(parents=True, exist_ok=True)
    prefix = f"{session}_{speaker}_{device}_"
    used = [int(p.stem[len(prefix):]) for p in folder.glob(prefix + "*.csv") if p.stem[len(prefix):].isdigit()]
    return folder / f"{prefix}{max(used, default=-1) + 1:04d}.csv"

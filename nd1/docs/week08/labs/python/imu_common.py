"""Shared IMU-gesture code (ws28p board, Week 08 alternative track).

The ws28p prebuilt firmware publishes one ``Imu`` message about every 20 ms (50 Hz):
acceleration in m/s^2 (QMI8658, +/-4 g range) and angular velocity in rad/s
(+/-512 deg/s range) plus the board's monotonic timestamp in ns.

A *window* is WINDOW_S seconds of samples resampled onto an exact 50 Hz grid:
an array of shape (WINDOW, 6) with columns ax, ay, az, gx, gy, gz.

Everything here must run the same way at collection, training and live inference
time - if you later move the model onto the board, port ``normalise`` exactly.

    python imu_common.py pack --data imu_dataset --out imu_dataset.npz
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import numpy as np

GESTURES = ["idle", "shake", "circle", "lift"]
RATE_HZ = 50
WINDOW_S = 2.0
WINDOW = int(RATE_HZ * WINDOW_S)          # 100 samples
CHANNELS = ["ax", "ay", "az", "gx", "gy", "gz"]
G = 9.80665
GYRO_UNIT = 4.0                           # rad/s that maps to 1.0 after normalise()
FILENAME_RE = re.compile(r"^(?P<session>s\d+)_(?P<person>[A-Za-z0-9-]+)_(?P<device>ws28p|synth)_(?P<index>\d+)\.csv$")


def normalise(window: np.ndarray) -> np.ndarray:
    """(WINDOW, 6) raw SI units -> model input: accel in g, gyro / 4 rad/s, clipped to +/-4.

    Fixed scales (not per-window z-score) keep "how hard" information: a gentle
    tilt and a hard shake must not look the same.
    """
    w = np.asarray(window, dtype=np.float32).copy()
    w[:, :3] /= G
    w[:, 3:] /= GYRO_UNIT
    return np.clip(w, -4, 4).astype(np.float32)


def to_grid(t_s: np.ndarray, data: np.ndarray, n: int = WINDOW, rate: float = RATE_HZ) -> np.ndarray:
    """Linear-interpolate irregular samples (t in seconds) onto n points spaced 1/rate,
    ending at the newest sample."""
    t_s = np.asarray(t_s, dtype=np.float64)
    data = np.asarray(data, dtype=np.float64)
    grid = t_s[-1] - (n - 1 - np.arange(n)) / rate
    return np.stack([np.interp(grid, t_s, data[:, c]) for c in range(data.shape[1])], axis=1).astype(np.float32)


def count_gaps(t_s: np.ndarray, rate: float = RATE_HZ) -> int:
    """Number of samples missing in a timestamp sequence (gap > 1.5 periods)."""
    dt = np.diff(np.asarray(t_s, dtype=np.float64)) * rate
    return int(np.sum(np.maximum(0, np.round(dt[dt > 1.5]) - 1)))


class ImuWindow:
    """Keep the newest samples for live inference and count dropped ones."""

    def __init__(self, seconds: float = WINDOW_S + 0.5):
        self.keep = int(seconds * RATE_HZ * 1.5)
        self.t: list[float] = []
        self.x: list[list[float]] = []
        self.lost = 0
        self.count = 0

    def push(self, t_s: float, accel, gyro):
        if self.t:
            dt = (t_s - self.t[-1]) * RATE_HZ
            if dt > 1.5:
                self.lost += int(round(dt)) - 1
            if t_s <= self.t[-1]:          # board rebooted / timestamps went back
                self.t, self.x = [], []
        self.t.append(t_s)
        self.x.append([*accel, *gyro])
        self.count += 1
        if len(self.t) > self.keep:
            del self.t[: len(self.t) - self.keep], self.x[: len(self.x) - self.keep]

    def ready(self) -> bool:
        return len(self.t) >= 2 and self.t[-1] - self.t[0] >= WINDOW_S - 1.0 / RATE_HZ

    def window(self) -> np.ndarray:
        return to_grid(np.array(self.t), np.array(self.x))


# ---------------------------------------------------------------- files
def save_window(path: Path, window: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_s", *CHANNELS])
        for i, row in enumerate(window):
            w.writerow([f"{i / RATE_HZ:.3f}", *(f"{v:.5f}" for v in row)])


def load_window(path: Path) -> np.ndarray:
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    w = np.array([[float(r[c]) for c in CHANNELS] for r in rows], dtype=np.float32)
    if w.shape != (WINDOW, 6):
        raise ValueError(f"{path}: expected {WINDOW} rows x 6 channels, got {w.shape}")
    return w


def scan(root: Path, labels=GESTURES):
    items = []
    for label in labels:
        for p in sorted((Path(root) / label).glob("*.csv")):
            m = FILENAME_RE.match(p.name)
            if m:
                items.append((p, label, m["person"], m["session"]))
    return items


def next_path(root: Path, label: str, session: str, person: str, device: str = "ws28p") -> Path:
    folder = Path(root) / label
    folder.mkdir(parents=True, exist_ok=True)
    prefix = f"{session}_{person}_{device}_"
    used = [int(p.stem[len(prefix):]) for p in folder.glob(prefix + "*.csv") if p.stem[len(prefix):].isdigit()]
    return folder / f"{prefix}{max(used, default=-1) + 1:04d}.csv"


# --------------------------------------------------------- augmentation
def random_rotation(rng, max_deg: float) -> np.ndarray:
    axis = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    a = np.deg2rad(rng.uniform(-max_deg, max_deg))
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * k + (1 - np.cos(a)) * (k @ k)


def augment(window: np.ndarray, rng, rot_deg: float = 20, shift: int = 10) -> np.ndarray:
    """Raw-unit window -> a plausible variation: small rotation of the board in the hand
    (applied to accel and gyro together), time shift, speed/strength scale, sensor noise."""
    w = np.asarray(window, dtype=np.float64)
    r = random_rotation(rng, rot_deg)
    w = np.concatenate([w[:, :3] @ r.T, w[:, 3:] @ r.T], axis=1)
    s = int(rng.integers(-shift, shift + 1))
    if s:
        w = np.roll(w, s, axis=0)
        if s > 0:
            w[:s] = w[s]
        else:
            w[s:] = w[s - 1]
    gravity = w[:, :3].mean(axis=0)
    w[:, :3] = gravity + (w[:, :3] - gravity) * rng.uniform(0.8, 1.2)
    w[:, 3:] *= rng.uniform(0.8, 1.2)
    w += rng.normal(0, [0.05] * 3 + [0.01] * 3, w.shape)
    return w.astype(np.float32)


# ---------------------------------------------- synthetic data (plumbing test)
def synth_window(label: str, rng, person: dict | None = None) -> np.ndarray:
    """Hand-made physics-ish gestures - only for testing the pipeline without a board."""
    person = person or {"speed": 1.0, "strength": 1.0, "tilt": 0.0}
    t = np.arange(WINDOW) / RATE_HZ
    acc = np.zeros((WINDOW, 3))
    gyr = np.zeros((WINDOW, 3))
    sp, st = person["speed"] * rng.uniform(0.85, 1.15), person["strength"] * rng.uniform(0.8, 1.2)
    on = (t > rng.uniform(0.2, 0.5)) & (t < rng.uniform(1.5, 1.8))
    env = np.convolve(on.astype(float), np.hanning(9) / np.hanning(9).sum(), "same")
    if label == "shake":                 # fast left-right along x
        f = 6.0 * sp
        acc[:, 0] = 12 * st * np.sin(2 * np.pi * f * t) * env
        gyr[:, 2] = 3.0 * st * np.cos(2 * np.pi * f * t) * env
    elif label == "circle":              # draw a circle in the x-y plane
        f = 1.5 * sp
        acc[:, 0] = 4 * st * np.cos(2 * np.pi * f * t) * env
        acc[:, 1] = 4 * st * np.sin(2 * np.pi * f * t) * env
        gyr[:, 0] = 0.8 * st * np.sin(2 * np.pi * f * t) * env
        gyr[:, 1] = -0.8 * st * np.cos(2 * np.pi * f * t) * env
    elif label == "lift":                # up then down along z, once or twice
        f = 1.0 * sp
        acc[:, 2] = 6 * st * np.sin(2 * np.pi * f * t) * env
        gyr[:, 1] = 0.4 * st * np.sin(2 * np.pi * f * t + 0.5) * env
    else:                                # idle: hand tremor + slow drift
        acc += np.cumsum(rng.normal(0, 0.02, (WINDOW, 3)), axis=0)
    acc[:, 2] += G                       # board flat, screen up
    r = random_rotation(rng, 10 + 30 * person["tilt"])
    acc, gyr = acc @ r.T, gyr @ r.T
    acc += rng.normal(0, 0.08, acc.shape)
    gyr += rng.normal(0, 0.02, gyr.shape) + rng.normal(0, 0.01, 3)   # noise + bias
    return np.concatenate([acc, gyr], axis=1).astype(np.float32)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="IMU dataset helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack", help="pack all CSV windows into one .npz (x, y, person, session, labels)")
    p.add_argument("--data", type=Path, default=Path("imu_dataset"))
    p.add_argument("--out", type=Path, default=Path("imu_dataset.npz"))
    args = ap.parse_args(argv)
    items = scan(args.data)
    if not items:
        print(f"no windows in {args.data}")
        return 1
    np.savez_compressed(args.out, x=np.stack([load_window(it[0]) for it in items]),
                        y=np.array([GESTURES.index(it[1]) for it in items]),
                        person=np.array([it[2] for it in items]), session=np.array([it[3] for it in items]),
                        labels=np.array(GESTURES), rate_hz=RATE_HZ)
    print(f"packed {len(items)} windows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

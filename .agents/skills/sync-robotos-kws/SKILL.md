---
name: sync-robotos-kws
description: >-
  Build the robotos_edge wheel (formerly robotos_kws) for this OS and sync wheels and examples
  across the 3 student tracks (ND1, ND2, ND3) in kmutt-nd69, on Windows or macOS. Use whenever
  robotos/sdk/python-edge changes, a new version must reach students, a Windows or macOS wheel
  is missing from a track's dist/, or ESP32-S3 serial/IMU behavior is being fixed.
---

# robotos_edge multi-track sync (Windows & macOS)

**Windows continuation pending (2026-11-27):** the Windows `robotos_edge` 0.2.2 wheel is missing. Follow
`docs/WINDOWS-HANDOFF.md` in `drsanti/robotos` (branch `feat/pyo3-binary-wheel`) first.

## Layout

- SDK source: `robotos/sdk/python-edge/` on branch `feat/pyo3-binary-wheel` (`sdk/python-kws` is obsolete).
- Tracks: `robotos/kmutt-nd69/nd{1,2,3}/docs/week08/labs/` and `…/week09/labs/` (every week is self-contained;
  `publish_to_students.py` deploys to all six) — each `dist/` holds **one wheel per
  platform**, same version: `robotos_edge-<V>-cp311-cp311-win_amd64.whl` and
  `robotos_edge-<V>-cp311-cp311-macosx_11_0_arm64.whl`.
- Students install by name: `pip install -U --no-index -f ../dist robotos_edge`.

## Rules

1. No SDK source in student folders — only wheels and `examples/`.
2. The wheel is compiled per OS: build it on each OS, or deploy the other OS's wheel with `--from-wheel`.
3. Bump the version (`pyproject.toml` + `robotos_edge/__init__.py`) for every change students get;
   pip will not replace an installed wheel of the same version.
4. **Serial lines:** `wire.py` opens the port with `rts=False, dtr=True` (set before `open()`), never
   asserts RTS, and on close only drops RTS. Holding DTR low made the ES3C28P reboot ~4 s after every
   open (measured on macOS). Do not change this without measuring on a real board (see the handoff doc).
5. macOS: use `/dev/cu.usbmodem*`, never `/dev/tty.*`.
6. Flashing: always pass `--board ws28p` or `--board es3c28p` — the default is ws28p for any ESP32-S3.

## Workflow

```bash
# 1. In robotos (branch feat/pyo3-binary-wheel), Python 3.11 venv with cython, wheel, setuptools
#    (Windows also needs MSVC Build Tools). Bump the version if the SDK changed.

# 2. Build for this OS and deploy to all tracks:
python sdk/python-edge/publish_to_students.py --binary
#    or deploy a wheel built on the other OS:
python sdk/python-edge/publish_to_students.py --from-wheel <robotos_edge-…whl>
#    add --course-root <path> if kmutt-nd69 is not at robotos/kmutt-nd69
```

The pipeline must end with exit code 0: both platform wheels at the same version in every track
(it warns otherwise), requirements checks ✓, "no doc pins a wheel filename".

```bash
# 3. Check as a student (fresh venv in a track), then on hardware:
robotos detect                 # x3, board must not restart
robotos-edge check-board       # ES3C28P mic
robotos check-imu              # ws28p IMU

# 4. Commit — stage by name, never `git add .` / `-A`:
cd robotos/kmutt-nd69
git status
git add nd1/docs/week08/labs/dist nd2/docs/week08/labs/dist nd3/docs/week08/labs/dist   # + any examples changed
git commit -m "[week08] ship robotos_edge <V> <platform> wheel to all student tracks"
```

**Ask the owner before `git push`** — `main` is what students clone. robotos commits carry no
`Co-Authored-By` trailers.

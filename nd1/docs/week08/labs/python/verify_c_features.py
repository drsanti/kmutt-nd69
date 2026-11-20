#!/usr/bin/env python3
"""Check that the firmware's C feature code matches the Python training features.

Compiles ../firmware/kws-inference/main/kws_features.c with your PC's C compiler
(gcc/clang; on Windows use WSL, MSYS2 or set --cc), runs it on wav clips and
compares the 49 x 40 log-mel matrices with kws_common.log_mel().

    python verify_c_features.py --data dataset --max-clips 50
    python verify_c_features.py --wav dataset/red/s01_me_pc_0000.wav

A mismatch here means the board sees different numbers than the model was trained
on - accuracy on the board will collapse even if the PC accuracy looks perfect.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import kws_common as kc

HERE = Path(__file__).resolve().parent
C_DIR = HERE.parent / "firmware" / "kws-inference" / "main"

HARNESS = r"""
#include <stdio.h>
#include <stdint.h>
#include "kws_features.h"
int main(void) {
    static int16_t pcm[KWS_CLIP_SAMPLES];
    static float out[KWS_NUM_FEATURES];
    kws_features_init();
    while (fread(pcm, sizeof(int16_t), KWS_CLIP_SAMPLES, stdin) == KWS_CLIP_SAMPLES) {
        kws_features_compute(pcm, out);
        fwrite(out, sizeof(float), KWS_NUM_FEATURES, stdout);
    }
    return 0;
}
"""


def build(cc: str, workdir: Path) -> Path:
    (workdir / "harness.c").write_text(HARNESS)
    exe = workdir / ("kws_features_test.exe" if sys.platform == "win32" else "kws_features_test")
    cmd = [cc, "-O2", "-std=c99", f"-I{C_DIR}", str(workdir / "harness.c"), str(C_DIR / "kws_features.c"),
           "-o", str(exe), "-lm"]
    subprocess.run(cmd, check=True)
    return exe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, help="dataset root to sample clips from")
    ap.add_argument("--wav", type=Path, nargs="*", default=[], help="specific wav files")
    ap.add_argument("--max-clips", type=int, default=50)
    ap.add_argument("--cc", default=shutil.which("cc") or shutil.which("gcc") or shutil.which("clang") or "cc")
    ap.add_argument("--tol", type=float, default=0.02, help="max allowed abs difference (log-mel units)")
    args = ap.parse_args(argv)

    paths = list(args.wav)
    if args.data:
        paths += [c.path for c in kc.scan_dataset(args.data)][: args.max_clips]
    if not paths:
        # no data given: random noise + tones
        rng = np.random.default_rng(0)
        t = np.arange(kc.CLIP_SAMPLES) / kc.SAMPLE_RATE
        clips = [kc.float_to_int16(0.3 * np.sin(2 * np.pi * f * t) + rng.normal(0, 0.02, len(t)))
                 for f in (300, 1000, 3000)]
    else:
        clips = [kc.fit_length(kc.read_wav(p)) for p in paths]

    with tempfile.TemporaryDirectory() as tmp:
        exe = build(args.cc, Path(tmp))
        stdin = b"".join(np.asarray(c, dtype="<i2").tobytes() for c in clips)
        out = subprocess.run([str(exe)], input=stdin, capture_output=True, check=True).stdout
    c_feats = np.frombuffer(out, dtype="<f4").reshape(len(clips), kc.NUM_FRAMES, kc.NUM_MEL)
    py_feats = np.stack([kc.log_mel(c) for c in clips])
    diff = np.abs(c_feats - py_feats)
    print(f"clips: {len(clips)}   feature shape: {py_feats.shape[1:]}")
    print(f"max |C - Python| = {diff.max():.5f}   mean = {diff.mean():.6f}   "
          f"(feature range {py_feats.min():.2f} .. {py_feats.max():.2f})")
    ok = diff.max() <= args.tol
    print("MATCH" if ok else f"MISMATCH (> {args.tol}) - fix kws_features.c or kws_common.py before training")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Train and quantize a tiny gesture classifier for the touch-screen track.

    python train_touch.py --data touch_dataset --out touch_artifacts
    python train_touch.py --synthetic --out touch_artifacts     # no board: generated strokes

Input: 32 resampled, normalised (x, y) points = 64 numbers. Model: 64 -> 32 -> 16 -> 4
dense network (about 2.7 k parameters). Outputs model_float.tflite, model_int8.tflite
and a confusion matrix on a speaker/session-disjoint test split.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np

import touch_common as tc


def synth_stroke(label: str, rng) -> np.ndarray:
    """Hand-made shape generator with jitter, rotation and scale (pipeline test only)."""
    if label == "circle":
        a = np.linspace(0, 2 * np.pi * rng.uniform(0.9, 1.05), 40) + rng.uniform(0, 2 * np.pi)
        pts = np.stack([np.cos(a), np.sin(a)], 1)
    elif label == "triangle":
        v = np.array([[0, -1], [0.9, 0.6], [-0.9, 0.6], [0, -1]])
        pts = np.concatenate([np.linspace(v[i], v[i + 1], 12) for i in range(3)])
    elif label == "check":
        v = np.array([[-0.6, 0], [-0.1, 0.6], [0.8, -0.8]])
        pts = np.concatenate([np.linspace(v[0], v[1], 10), np.linspace(v[1], v[2], 20)])
    else:  # line
        pts = np.linspace([-1, rng.uniform(-0.2, 0.2)], [1, rng.uniform(-0.2, 0.2)], 25)
    th = rng.normal(0, 0.15)
    rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    pts = pts @ rot.T * rng.uniform(30, 90) + rng.uniform([60, 80], [180, 240])
    return pts + rng.normal(0, 1.5, pts.shape)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("touch_dataset"))
    ap.add_argument("--out", type=Path, default=Path("touch_artifacts"))
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    import tensorflow as tf
    tf.keras.utils.set_random_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    if args.synthetic:
        items = [(synth_stroke(lb, rng), lb, f"spk{i % 6}") for lb in tc.GESTURES for i in range(60)]
    else:
        items = [(tc.load_stroke(p), lb, f"{spk}/{ses}") for p, lb, spk, ses in tc.scan(args.data)]
    if not items:
        print(f"No strokes in {args.data}")
        return 1
    groups = sorted({g for _, _, g in items})
    random.Random(args.seed).shuffle(groups)
    test_g = set(groups[: max(1, len(groups) // 6)])
    x = np.stack([tc.normalise(s).reshape(-1) for s, _, _ in items])
    y = np.array([tc.GESTURES.index(lb) for _, lb, _ in items])
    is_test = np.array([g in test_g for _, _, g in items])
    print(f"strokes: {len(items)}  train {np.sum(~is_test)}  test {np.sum(is_test)} (groups held out: {sorted(test_g)})")

    L = tf.keras.layers
    model = tf.keras.Sequential([L.Input((2 * tc.NUM_POINTS,)), L.Dense(32, activation="relu"),
                                 L.Dense(16, activation="relu"), L.Dense(len(tc.GESTURES), activation="softmax")])
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(x[~is_test], y[~is_test], epochs=args.epochs, batch_size=16, verbose=0, validation_split=0.15)

    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    (args.out / "model_float.tflite").write_bytes(conv.convert())
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = lambda: ([s[None].astype(np.float32)] for s in x[~is_test][:200])
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = conv.inference_output_type = tf.int8
    int8 = conv.convert()
    (args.out / "model_int8.tflite").write_bytes(int8)

    import kws_common as kc   # reuse the TFLite helpers
    from evaluate import confusion, format_confusion
    report = {}
    for name in ["model_float.tflite", "model_int8.tflite"]:
        interp = kc.make_interpreter(args.out / name)
        pred = np.array([int(np.argmax(kc.run_tflite(interp, s))) for s in x[is_test]])
        acc = float(np.mean(pred == y[is_test]))
        report[name] = {"accuracy": acc, "bytes": (args.out / name).stat().st_size}
        print(f"\n{name}: test accuracy {acc:.1%}, {report[name]['bytes']} bytes")
        print(format_confusion(confusion(y[is_test], pred, len(tc.GESTURES)), tc.GESTURES))
    (args.out / "meta.json").write_text(json.dumps({"labels": tc.GESTURES, "num_points": tc.NUM_POINTS,
                                                    "params": int(model.count_params()), **report}, indent=1))
    print(f"\nParameters: {model.count_params()}. Export with:\n"
          f"  python export_c_array.py --model {args.out}/model_int8.tflite --name g_touch_model --out-dir <dir>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Train and quantize a tiny 1D-CNN gesture classifier for the ws28p IMU track.

    python train_imu.py --data imu_dataset --out imu_artifacts
    python train_imu.py --synthetic --out imu_artifacts      # no board: generated gestures

Input: one 2 s window, 100 time steps x 6 channels (ax ay az gx gy gz), scaled by
imu_common.normalise. Model: three small Conv1D layers + global average pooling
(about 2 k parameters). The test set is PERSON-disjoint: whole people are held out,
so the score tells you how the model does on someone it has never seen.
Training windows are augmented (rotation in the hand, time shift, strength, noise).

Outputs model.keras, model_float.tflite, model_int8.tflite, meta.json and a confusion
matrix for both models.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np

import imu_common as ic


def load_items(args, rng):
    if args.synthetic:
        people = {f"p{i}": {"speed": rng.uniform(0.8, 1.25), "strength": rng.uniform(0.7, 1.3),
                            "tilt": rng.uniform(0, 1)} for i in range(args.synthetic_people)}
        return [(ic.synth_window(lb, rng, prm), lb, name) for name, prm in people.items()
                for lb in ic.GESTURES for _ in range(args.synthetic_per)]
    return [(ic.load_window(p), lb, person) for p, lb, person, _ in ic.scan(args.data)]


def person_split(people, seed, test_frac=0.2, val_frac=0.15):
    people = sorted(people)
    random.Random(seed).shuffle(people)
    n_test = max(1, round(len(people) * test_frac))
    n_val = max(1, round(len(people) * val_frac)) if len(people) - n_test > 1 else 0
    return set(people[:n_test]), set(people[n_test:n_test + n_val])


def build_model(n_classes: int):
    import tensorflow as tf
    L = tf.keras.layers
    return tf.keras.Sequential([
        L.Input((ic.WINDOW, 6)),
        L.Conv1D(8, 5, padding="same", activation="relu"),
        L.MaxPooling1D(2),
        L.Conv1D(16, 5, padding="same", activation="relu"),
        L.MaxPooling1D(2),
        L.Conv1D(16, 3, padding="same", activation="relu"),
        L.GlobalAveragePooling1D(),
        L.Dropout(0.2),
        L.Dense(n_classes, activation="softmax"),
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("imu_dataset"))
    ap.add_argument("--out", type=Path, default=Path("imu_artifacts"))
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--synthetic-people", type=int, default=8)
    ap.add_argument("--synthetic-per", type=int, default=25)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--aug", type=int, default=3, help="augmented copies per training window")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    import tensorflow as tf
    tf.keras.utils.set_random_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    items = load_items(args, rng)
    if not items:
        print(f"No windows in {args.data} - record some with collect_imu.py")
        return 1
    people = {p for _, _, p in items}
    if len(people) < 2:
        print("Need windows from at least 2 people for a person-disjoint test set.")
        return 1
    test_p, val_p = person_split(people, args.seed)
    part = {"train": [], "val": [], "test": []}
    for w, lb, p in items:
        part["test" if p in test_p else "val" if p in val_p else "train"].append((w, ic.GESTURES.index(lb)))

    def arrays(rows, n_aug=0):
        xs, ys = [], []
        for w, y in rows:
            xs.append(ic.normalise(w)); ys.append(y)
            for _ in range(n_aug):
                xs.append(ic.normalise(ic.augment(w, rng))); ys.append(y)
        return np.stack(xs), np.array(ys)

    x_tr, y_tr = arrays(part["train"], args.aug)
    x_te, y_te = arrays(part["test"])
    x_va, y_va = arrays(part["val"]) if part["val"] else (x_te, y_te)
    print(f"windows: train {len(part['train'])} (x{args.aug + 1} with augmentation), val {len(part['val'])}, "
          f"test {len(part['test'])}; test people {sorted(test_p)}, val people {sorted(val_p)}")

    model = build_model(len(ic.GESTURES))
    model.compile(tf.keras.optimizers.Adam(3e-3), "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(x_tr, y_tr, validation_data=(x_va, y_va), epochs=args.epochs, batch_size=32, verbose=0,
              callbacks=[tf.keras.callbacks.EarlyStopping(patience=12, restore_best_weights=True,
                                                          start_from_epoch=10)])
    model.save(args.out / "model.keras")

    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    (args.out / "model_float.tflite").write_bytes(conv.convert())
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    rep = x_tr[rng.permutation(len(x_tr))[:300]]
    conv.representative_dataset = lambda: ([s[None]] for s in rep)
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = conv.inference_output_type = tf.int8
    (args.out / "model_int8.tflite").write_bytes(conv.convert())

    import kws_common as kc                       # TFLite helpers shared with the KWS track
    from evaluate import confusion, format_confusion
    from train import op_names
    report = {}
    for name in ["model_float.tflite", "model_int8.tflite"]:
        interp = kc.make_interpreter(args.out / name)
        pred = np.array([int(np.argmax(kc.run_tflite(interp, s))) for s in x_te])
        acc = float(np.mean(pred == y_te))
        report[name] = {"accuracy": acc, "bytes": (args.out / name).stat().st_size}
        print(f"\n{name}: test accuracy {acc:.1%} on unseen people, {report[name]['bytes']} bytes")
        print(format_confusion(confusion(y_te, pred, len(ic.GESTURES)), ic.GESTURES))
    ops = op_names(args.out / "model_int8.tflite")
    print(f"\nParameters: {model.count_params()}   int8 ops: {', '.join(ops)}")
    (args.out / "meta.json").write_text(json.dumps({
        "labels": ic.GESTURES, "rate_hz": ic.RATE_HZ, "window": ic.WINDOW, "channels": ic.CHANNELS,
        "normalise": {"accel_divisor": ic.G, "gyro_divisor": ic.GYRO_UNIT, "clip": 4},
        "params": int(model.count_params()), "int8_ops": ops, "test_people": sorted(test_p),
        "synthetic": bool(args.synthetic), **report}, indent=1))
    print(f"Live test:  python live_infer_imu.py --port <PORT> --model {args.out}/model_int8.tflite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

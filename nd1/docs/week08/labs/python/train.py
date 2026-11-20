#!/usr/bin/env python3
"""Train the small DS-CNN keyword-spotting model and export float + int8 TFLite.

    python train.py --data dataset --out artifacts --epochs 40

Runs on a laptop CPU in a few minutes for a few thousand clips, or on Google Colab
(see train_colab.ipynb). Outputs in --out:

    model.keras           Keras model (float32)
    model_float.tflite    float32 TFLite model (reference for accuracy)
    model_int8.tflite     full-integer int8 model (this one goes on the ESP32-S3)
    splits.json           which clip belongs to train / val / test (evaluate.py reuses it)
    meta.json             labels, feature settings, quantization parameters, sizes
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np

import kws_common as kc


# ---------------------------------------------------------------- splits
def make_splits(clips, group_by: str, seed: int, val_frac: float = 0.15, test_frac: float = 0.15):
    """Group-disjoint split so the same speaker (or session) never leaks across splits."""
    if group_by == "auto":
        n_speakers = len({c.speaker for c in clips})
        group_by = "speaker" if n_speakers >= 3 else "session"
    key = (lambda c: c.speaker) if group_by == "speaker" else (lambda c: f"{c.speaker}/{c.session}")
    groups = sorted({key(c) for c in clips})
    if len(groups) < 3:
        print(f"[warn] only {len(groups)} {group_by} group(s): falling back to a random clip split. "
              "Record more speakers or sessions for an honest test score.")
        rng = random.Random(seed)
        idx = list(range(len(clips)))
        rng.shuffle(idx)
        n_test = max(1, int(test_frac * len(idx)))
        n_val = max(1, int(val_frac * len(idx)))
        split = {}
        for j, i in enumerate(idx):
            split[str(clips[i].path)] = "test" if j < n_test else "val" if j < n_test + n_val else "train"
        return split, "random"
    rng = random.Random(seed)
    rng.shuffle(groups)
    n_test = max(1, round(test_frac * len(groups)))
    n_val = max(1, round(val_frac * len(groups)))
    test_g, val_g = set(groups[:n_test]), set(groups[n_test:n_test + n_val])
    split = {str(c.path): ("test" if key(c) in test_g else "val" if key(c) in val_g else "train") for c in clips}
    return split, group_by


# ---------------------------------------------------------------- augmentation
def augment(pcm: np.ndarray, noises: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    """Time shift (+-100 ms), gain (+-6 dB) and background noise at 5-25 dB SNR."""
    x = pcm.astype(np.float32) / 32768.0
    shift = int(rng.integers(-1600, 1601))
    x = np.roll(x, shift)
    if shift > 0:
        x[:shift] = 0
    elif shift < 0:
        x[shift:] = 0
    x *= 10 ** (rng.uniform(-6, 6) / 20)
    if noises and rng.random() < 0.8:
        n = noises[int(rng.integers(len(noises)))].astype(np.float32) / 32768.0
        n = n - n.mean()
        p_sig = np.mean(x ** 2) + 1e-10
        p_noise = np.mean(n ** 2) + 1e-10
        snr_db = rng.uniform(5, 25)
        x = x + n * np.sqrt(p_sig / (p_noise * 10 ** (snr_db / 10)))
    return kc.float_to_int16(x)


# ---------------------------------------------------------------- model
def build_ds_cnn(n_classes: int, width: int = 32, blocks: int = 3):
    """Small depthwise-separable CNN (DS-CNN) for a 49 x 40 log-mel input."""
    import tensorflow as tf
    L = tf.keras.layers
    inp = L.Input(shape=(kc.NUM_FRAMES, kc.NUM_MEL, 1), name="log_mel")
    x = L.Conv2D(width, (5, 3), strides=(2, 2), padding="same", use_bias=False)(inp)
    x = L.BatchNormalization(momentum=0.9)(x)
    x = L.ReLU()(x)
    for _ in range(blocks):
        x = L.DepthwiseConv2D((3, 3), padding="same", use_bias=False)(x)
        x = L.BatchNormalization(momentum=0.9)(x)
        x = L.ReLU()(x)
        x = L.Conv2D(width, (1, 1), use_bias=False)(x)
        x = L.BatchNormalization(momentum=0.9)(x)
        x = L.ReLU()(x)
    x = L.GlobalAveragePooling2D()(x)
    x = L.Dropout(0.2)(x)
    out = L.Dense(n_classes, activation="softmax", name="probs")(x)
    return tf.keras.Model(inp, out, name="ds_cnn_kws")


def convert(model, rep_features: np.ndarray, out_dir: Path):
    import tensorflow as tf
    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    float_bytes = conv.convert()
    (out_dir / "model_float.tflite").write_bytes(float_bytes)

    def representative():
        for f in rep_features:
            yield [f[None, ...].astype(np.float32)]

    conv = tf.lite.TFLiteConverter.from_keras_model(model)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = representative
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = tf.int8
    conv.inference_output_type = tf.int8
    int8_bytes = conv.convert()
    (out_dir / "model_int8.tflite").write_bytes(int8_bytes)
    return len(float_bytes), len(int8_bytes)


def op_names(model_path: Path) -> list[str]:
    """Builtin ops in the model (default delegates disabled so XNNPACK does not hide them)."""
    try:
        from ai_edge_litert.interpreter import Interpreter, OpResolverType
    except ImportError:
        import tensorflow as tf
        Interpreter, OpResolverType = tf.lite.Interpreter, tf.lite.experimental.OpResolverType
    interp = Interpreter(model_path=str(model_path),
                         experimental_op_resolver_type=OpResolverType.BUILTIN_WITHOUT_DEFAULT_DELEGATES)
    interp.allocate_tensors()
    try:
        return sorted({d["op_name"] for d in interp._get_ops_details()})
    except Exception:  # private API may change
        return []


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=Path("dataset"))
    ap.add_argument("--out", type=Path, default=Path("artifacts"))
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--augment", type=int, default=2, help="extra augmented copies per training clip")
    ap.add_argument("--group-by", choices=["auto", "speaker", "session"], default="auto")
    ap.add_argument("--width", type=int, default=32, help="channels per DS-CNN layer")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)

    import tensorflow as tf
    tf.keras.utils.set_random_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    clips = kc.scan_dataset(args.data)
    if not clips:
        print(f"No clips found in {args.data}/<label>/*.wav")
        return 1
    counts = Counter(c.label for c in clips)
    print("Clips per label:", {lb: counts.get(lb, 0) for lb in kc.LABELS})
    print("Clips per device:", dict(Counter(c.device for c in clips)))
    missing = [lb for lb in kc.LABELS if counts.get(lb, 0) == 0]
    if missing:
        print(f"[error] no clips for {missing}. Every label needs data (record _silence_ and _unknown_ too).")
        return 1

    split, group_by = make_splits(clips, args.group_by, args.seed)
    (args.out / "splits.json").write_text(json.dumps({"group_by": group_by, "split": split}, indent=1))
    by_split = Counter(split.values())
    print(f"Split by {group_by}: {dict(by_split)}")

    audio = {str(c.path): kc.read_wav(c.path) for c in clips}
    noises = [audio[str(c.path)] for c in clips if c.label == kc.SILENCE and split[str(c.path)] == "train"]
    label_id = {lb: i for i, lb in enumerate(kc.LABELS)}

    def arrays(name, n_aug=0):
        pcm, y = [], []
        for c in clips:
            if split[str(c.path)] != name:
                continue
            pcm.append(audio[str(c.path)])
            y.append(label_id[c.label])
            for _ in range(n_aug):
                pcm.append(augment(audio[str(c.path)], noises, rng))
                y.append(label_id[c.label])
        return kc.batch_log_mel(pcm), np.array(y, dtype=np.int64)

    x_tr, y_tr = arrays("train", args.augment)
    x_va, y_va = arrays("val")
    print(f"Feature tensors: train {x_tr.shape}, val {x_va.shape}")

    weights = len(y_tr) / (len(kc.LABELS) * np.bincount(y_tr, minlength=len(kc.LABELS)).clip(min=1))
    model = build_ds_cnn(len(kc.LABELS), width=args.width)
    model.summary(print_fn=lambda s: print("  " + s))
    model.compile(optimizer=tf.keras.optimizers.Adam(2e-3),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=10, start_from_epoch=5,
                                         restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4),
    ]
    hist = model.fit(x_tr, y_tr, validation_data=(x_va, y_va) if len(y_va) else None,
                     epochs=args.epochs, batch_size=args.batch, verbose=2,
                     class_weight={i: float(w) for i, w in enumerate(weights)}, callbacks=callbacks)
    model.save(args.out / "model.keras")

    rep = x_tr[rng.permutation(len(x_tr))[:300]]
    float_size, int8_size = convert(model, rep, args.out)
    ops = op_names(args.out / "model_int8.tflite")

    interp = kc.make_interpreter(args.out / "model_int8.tflite")
    qi, qo = interp.get_input_details()[0]["quantization"], interp.get_output_details()[0]["quantization"]
    meta = {
        "labels": kc.LABELS,
        "features": {k: getattr(kc, k) for k in ["SAMPLE_RATE", "CLIP_SAMPLES", "FRAME_LEN", "FRAME_STEP",
                                                  "FFT_LEN", "NUM_MEL", "MEL_FMIN", "MEL_FMAX", "LOG_EPS",
                                                  "NUM_FRAMES"]},
        "input_quant": {"scale": float(qi[0]), "zero_point": int(qi[1])},
        "output_quant": {"scale": float(qo[0]), "zero_point": int(qo[1])},
        "params": int(model.count_params()),
        "float_tflite_bytes": float_size,
        "int8_tflite_bytes": int8_size,
        "int8_ops": ops,
        "best_val_accuracy": float(max(hist.history.get("val_accuracy", [0]))),
        "split_group_by": group_by,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"\nParameters: {meta['params']:,}")
    print(f"float32 TFLite: {float_size / 1024:.1f} KiB   int8 TFLite: {int8_size / 1024:.1f} KiB")
    print(f"int8 ops (register these in the firmware op resolver): {ops}")
    print(f"input quant: scale={qi[0]:.6f} zero_point={qi[1]}")
    print(f"Saved to {args.out}/. Next: python evaluate.py --artifacts {args.out} --data {args.data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

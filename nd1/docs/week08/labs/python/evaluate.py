#!/usr/bin/env python3
"""Test the float32 and int8 models on held-out clips and write a report.

    python evaluate.py --artifacts artifacts --data dataset              # test split from train.py
    python evaluate.py --artifacts artifacts --data board_test --all     # every clip in another folder
    python evaluate.py --artifacts artifacts --data dataset --device board

Prints and saves (artifacts/report.md):
  * accuracy of the float32 and int8 models and the drop caused by quantization
  * accuracy per recording device (pc vs board) -> domain shift check
  * confusion matrix (rows = true label, columns = predicted)
  * model file sizes and average PC inference time
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

import kws_common as kc


def confusion(y_true, y_pred, n):
    m = np.zeros((n, n), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        m[t, p] += 1
    return m


def format_confusion(m, labels) -> str:
    w = max(8, max(len(lb) for lb in labels) + 1)
    head = "true \\ pred".ljust(w) + "".join(lb[:w - 1].rjust(w) for lb in labels) + "   recall"
    rows = [head]
    for i, lb in enumerate(labels):
        rec = m[i, i] / m[i].sum() if m[i].sum() else float("nan")
        rows.append(lb.ljust(w) + "".join(str(v).rjust(w) for v in m[i]) + f"   {rec:6.1%}")
    return "\n".join(rows)


def evaluate_model(path: Path, feats, labels_idx):
    interp = kc.make_interpreter(path)
    preds, t0 = [], time.perf_counter()
    for f in feats:
        preds.append(int(np.argmax(kc.run_tflite(interp, f))))
    ms = 1000 * (time.perf_counter() - t0) / max(1, len(feats))
    preds = np.array(preds)
    return preds, float(np.mean(preds == labels_idx)) if len(preds) else float("nan"), ms


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    ap.add_argument("--data", type=Path, default=Path("dataset"))
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--all", action="store_true", help="use every clip in --data (ignore splits.json)")
    ap.add_argument("--device", choices=["pc", "board", "synth"], help="only clips from this device")
    args = ap.parse_args(argv)

    meta = json.loads((args.artifacts / "meta.json").read_text())
    if meta["labels"] != kc.LABELS:
        print(f"[error] labels in meta.json {meta['labels']} != kws_common.LABELS {kc.LABELS}")
        return 1
    clips = kc.scan_dataset(args.data)
    if not args.all:
        split = json.loads((args.artifacts / "splits.json").read_text())["split"]
        clips = [c for c in clips if split.get(str(c.path)) == args.split]
    if args.device:
        clips = [c for c in clips if c.device == args.device]
    if not clips:
        print("No clips to evaluate (check --data/--split/--device).")
        return 1

    label_id = {lb: i for i, lb in enumerate(kc.LABELS)}
    y = np.array([label_id[c.label] for c in clips])
    feats = [kc.log_mel(kc.read_wav(c.path)) for c in clips]
    devices = np.array([c.device for c in clips])

    lines = [f"# KWS evaluation report", "",
             f"Clips: {len(clips)} from `{args.data}` ({'all' if args.all else args.split + ' split'}"
             f"{', device=' + args.device if args.device else ''})", ""]
    results = {}
    for name in ["model_float.tflite", "model_int8.tflite"]:
        path = args.artifacts / name
        pred, acc, ms = evaluate_model(path, feats, y)
        results[name] = (pred, acc)
        lines += [f"## {name}", "",
                  f"- accuracy: **{acc:.1%}**",
                  f"- file size: {path.stat().st_size / 1024:.1f} KiB",
                  f"- PC inference: {ms:.2f} ms/clip (features not included)"]
        for dev in sorted(set(devices)):
            mask = devices == dev
            lines.append(f"- accuracy on `{dev}` clips: {np.mean(pred[mask] == y[mask]):.1%} (n={mask.sum()})")
        lines += ["", "```text", format_confusion(confusion(y, pred, len(kc.LABELS)), kc.LABELS), "```", ""]

    drop = results["model_float.tflite"][1] - results["model_int8.tflite"][1]
    agree = np.mean(results["model_float.tflite"][0] == results["model_int8.tflite"][0])
    lines += ["## Quantization", "",
              f"- accuracy drop float32 -> int8: **{100 * drop:+.2f} percentage points** "
              "(positive = int8 is worse)",
              f"- float32 and int8 agree on {agree:.1%} of clips",
              f"- size ratio int8/float32: {meta['int8_tflite_bytes'] / meta['float_tflite_bytes']:.2f}", ""]
    report = "\n".join(lines)
    print(report)
    (args.artifacts / "report.md").write_text(report + "\n")
    print(f"Saved {args.artifacts / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

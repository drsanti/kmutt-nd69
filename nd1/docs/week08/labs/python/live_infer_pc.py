#!/usr/bin/env python3
"""Run the trained model LIVE on your computer microphone (no board needed).

Uses the same 1 s window, the same log-mel features and the same int8 quantization
steps as the firmware, so it is a quick way to feel how the model behaves before
flashing. Runs float32 and int8 side by side when you pass both models.

    python live_infer_pc.py --model artifacts/model_int8.tflite
    python live_infer_pc.py --model artifacts/model_float.tflite artifacts/model_int8.tflite
    python live_infer_pc.py --model artifacts/model_int8.tflite --wav test_sentence.wav   # no mic needed

Streaming logic (also used in the firmware):
    every --hop-ms: take the newest 1.0 s of audio -> features -> model
    average the last --smooth probability vectors
    report a keyword only if its averaged score >= --threshold and it is not
    _silence_/_unknown_, then ignore new detections for --refractory-ms
"""
from __future__ import annotations

import argparse
import queue
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np

import kws_common as kc


class Detector:
    """Sliding-window detector shared by the microphone and the --wav paths."""

    def __init__(self, model_paths, hop_ms=250, smooth=3, threshold=0.7, refractory_ms=1000):
        self.models = [(Path(p).name, kc.make_interpreter(p)) for p in model_paths]
        self.hop = int(kc.SAMPLE_RATE * hop_ms / 1000)
        self.ring = np.zeros(kc.CLIP_SAMPLES, dtype=np.int16)
        self.pending = 0
        self.history = [deque(maxlen=smooth) for _ in self.models]
        self.threshold = threshold
        self.refractory = int(kc.SAMPLE_RATE * refractory_ms / 1000)
        self.since_detection = [self.refractory] * len(self.models)
        self.samples_seen = 0
        self.detections = []   # (time_s, model_name, label, score)
        self.feature_ms = deque(maxlen=50)
        self.infer_ms = deque(maxlen=50)

    def push(self, block: np.ndarray):
        block = np.asarray(block, dtype=np.int16).reshape(-1)
        for start in range(0, len(block), self.hop):
            chunk = block[start:start + self.hop]
            self.ring = np.concatenate([self.ring[len(chunk):], chunk])
            self.samples_seen += len(chunk)
            self.pending += len(chunk)
            self.since_detection = [s + len(chunk) for s in self.since_detection]
            if self.pending >= self.hop:
                self.pending = 0
                self._step()

    def _step(self):
        t0 = time.perf_counter()
        feats = kc.log_mel(self.ring)
        t1 = time.perf_counter()
        self.feature_ms.append(1000 * (t1 - t0))
        status = []
        for i, (name, interp) in enumerate(self.models):
            t2 = time.perf_counter()
            probs = kc.run_tflite(interp, feats)
            self.infer_ms.append(1000 * (time.perf_counter() - t2))
            self.history[i].append(probs)
            avg = np.mean(self.history[i], axis=0)
            top = int(np.argmax(avg))
            label, score = kc.LABELS[top], float(avg[top])
            status.append(f"{name.replace('.tflite', ''):>12}: {label:<10} {score:4.2f}")
            if (label in kc.KEYWORDS and score >= self.threshold
                    and self.since_detection[i] >= self.refractory):
                self.since_detection[i] = 0
                t = self.samples_seen / kc.SAMPLE_RATE
                self.detections.append((t, name, label, score))
                status[-1] += "  <== DETECTED"
        level = kc.rms_dbfs(self.ring[-self.hop:])
        print(f"\r[{level:6.1f} dBFS] " + " | ".join(status), end="\n" if "DETECTED" in "".join(status) else "",
              flush=True)


def run_wav(det: Detector, path: Path, realtime: bool):
    pcm = kc.read_wav(path)
    pcm = np.concatenate([pcm, np.zeros(kc.CLIP_SAMPLES // 2, dtype=np.int16)])  # flush the tail
    for start in range(0, len(pcm), det.hop):
        det.push(pcm[start:start + det.hop])
        if realtime:
            time.sleep(det.hop / kc.SAMPLE_RATE)


def run_mic(det: Detector, device, seconds: float | None):
    try:
        import sounddevice as sd
    except OSError as e:
        print(f"Cannot load sounddevice/PortAudio: {e}\nSee troubleshooting.md -> 'PC microphone'.")
        return 1
    q: queue.Queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(f"\n[audio] {status}", file=sys.stderr)
        q.put(indata[:, 0].copy())

    print(f"Listening on: {sd.query_devices(device, 'input')['name']}  (Ctrl+C to stop)")
    print(f"Keywords: {kc.KEYWORDS}")
    end = time.monotonic() + seconds if seconds else None
    with sd.InputStream(samplerate=kc.SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=det.hop, device=device, callback=callback):
        while end is None or time.monotonic() < end:
            try:
                det.push(q.get(timeout=0.5))
            except queue.Empty:
                print("\n[audio] no samples for 0.5 s - is the microphone muted or busy?", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", nargs="+", type=Path, default=[Path("artifacts/model_int8.tflite")])
    ap.add_argument("--wav", type=Path, help="stream this 16 kHz mono wav instead of the microphone")
    ap.add_argument("--realtime", action="store_true", help="with --wav: play at real-time speed")
    ap.add_argument("--device", default=None, help="input device index or name")
    ap.add_argument("--hop-ms", type=int, default=250)
    ap.add_argument("--smooth", type=int, default=3)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--refractory-ms", type=int, default=1000)
    ap.add_argument("--seconds", type=float, help="stop after this many seconds (mic mode)")
    args = ap.parse_args(argv)

    det = Detector(args.model, args.hop_ms, args.smooth, args.threshold, args.refractory_ms)
    try:
        if args.wav:
            run_wav(det, args.wav, args.realtime)
            rc = 0
        else:
            device = int(args.device) if args.device and args.device.isdigit() else args.device
            rc = run_mic(det, device, args.seconds)
    except KeyboardInterrupt:
        rc = 0
    print("\n\nDetections:")
    for t, name, label, score in det.detections:
        print(f"  t={t:6.2f} s  {name:<20} {label:<8} score {score:.2f}")
    if det.feature_ms:
        print(f"PC timing: features {np.mean(det.feature_ms):.2f} ms, model {np.mean(det.infer_ms):.2f} ms per step")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

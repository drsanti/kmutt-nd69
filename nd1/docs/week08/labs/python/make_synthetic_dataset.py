#!/usr/bin/env python3
"""Generate a SYNTHETIC dataset to test the whole pipeline without any microphone.

This is a plumbing test, not speech: every "keyword" is a distinctive pattern of
tones/chirps, "speakers" shift the pitch, and the "board" device gets a different
frequency response, gain and noise than "pc" (a toy model of domain shift).
A model trained on it proves that collect -> train -> evaluate -> export works on
your computer; it will NOT recognise real words.

    python make_synthetic_dataset.py --out synth_dataset --per-class 60
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import kws_common as kc

SR = kc.SAMPLE_RATE

# (start_hz, end_hz) pairs per syllable for each synthetic keyword
PATTERNS = {
    "red":   [(500, 900)],
    "green": [(1200, 700), (900, 1400)],
    "blue":  [(300, 300), (1800, 1800)],
    "off":   [(2400, 1200)],
}


def _chirp(f0, f1, dur, rng, pitch):
    n = int(dur * SR)
    f = np.linspace(f0, f1, n) * pitch
    phase = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(phase) + 0.4 * np.sin(2 * phase) + 0.2 * np.sin(3 * phase)
    env = np.hanning(n)
    return tone * env


def synth_word(label, rng, pitch):
    if label == kc.SILENCE:
        return np.zeros(SR)
    if label == kc.UNKNOWN:
        k = rng.integers(1, 3)
        pattern = [(rng.uniform(200, 3000), rng.uniform(200, 3000)) for _ in range(k)]
    else:
        pattern = PATTERNS[label]
    out = np.zeros(SR)
    start = int(rng.uniform(0.1, 0.35) * SR)
    for f0, f1 in pattern:
        seg = _chirp(f0, f1, rng.uniform(0.18, 0.28), rng, pitch)
        end = min(SR, start + len(seg))
        out[start:end] += seg[: end - start]
        start = end + int(0.03 * SR)
    return out


def device_colour(x, device, rng):
    """Toy domain shift: the 'board' path is band-limited, quieter and noisier."""
    if device == "board":
        spec = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / SR)
        resp = 1 / np.sqrt(1 + (150 / np.maximum(f, 1)) ** 4) / np.sqrt(1 + (f / 5000) ** 6)
        x = np.fft.irfft(spec * resp, n=len(x)) * 0.5
        noise = 0.02
    else:
        noise = 0.01
    return x + rng.normal(0, noise * rng.uniform(0.5, 1.5), len(x))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("synth_dataset"))
    ap.add_argument("--per-class", type=int, default=60, help="clips per label (spread over speakers/devices)")
    ap.add_argument("--speakers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    rng = np.random.default_rng(args.seed)
    pitches = {f"spk{i:02d}": rng.uniform(0.85, 1.2) for i in range(args.speakers)}
    n = 0
    for label in kc.LABELS:
        for i in range(args.per_class):
            speaker = list(pitches)[i % args.speakers]
            device = "board" if (i // args.speakers) % 2 else "pc"
            session = f"s{1 + (i // (2 * args.speakers)) % 3:02d}"
            x = synth_word(label, rng, pitches[speaker]) * rng.uniform(0.2, 0.6)
            x = device_colour(x, device, rng)
            path = kc.clip_path(args.out, label, session, speaker, device)
            kc.write_wav(path, kc.float_to_int16(x))
            n += 1
    print(f"Wrote {n} synthetic clips to {args.out}/ ({len(kc.LABELS)} labels, {args.speakers} speakers, pc+board)")


if __name__ == "__main__":
    main()

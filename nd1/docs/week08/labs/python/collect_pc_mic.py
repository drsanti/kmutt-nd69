#!/usr/bin/env python3
"""Record labelled 1 s keyword clips with your COMPUTER microphone.

Clips are saved in exactly the same layout as the board logger (collect.py):

    <out>/<label>/<session>_<speaker>_pc_<index>.wav     16 kHz, mono, 16-bit, 1.0 s

Each take records 1.5 s, then keeps the loudest 1.0 s window (same trimming as
collect.py), so you do not have to time your word perfectly.

Examples
    python collect_pc_mic.py --list-devices
    python collect_pc_mic.py --speaker alice --session s01 --labels red green blue off --takes 20
    python collect_pc_mic.py --speaker alice --session s01 --labels _silence_ --takes 30 --no-prompt
    python collect_pc_mic.py --speaker alice --session s01 --from-wav long_noise.wav --labels _silence_

Notes
* A PC microphone is great for fast collection and testing without hardware, but it
  hears differently from the board's MEMS mic + ES8311 (frequency response, gain,
  noise, automatic gain control). Mix PC and board clips for training and always
  test on board-recorded clips before trusting the model on the board.
* Turn OFF "noise suppression", "voice isolation", "AGC" or similar effects in your
  OS / meeting apps if you can: the board does not have them.
* --from-wav lets you slice a long recording (e.g. background noise for _silence_)
  without a microphone. It uses the same trimming and file naming.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

import kws_common as kc

RECORD_SECONDS = 1.5


def record_take(sd, device, seconds: float = RECORD_SECONDS) -> np.ndarray:
    """Record one take from the PC microphone as int16 at 16 kHz mono."""
    frames = int(seconds * kc.SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=kc.SAMPLE_RATE, channels=1, dtype="int16", device=device)
    sd.wait()
    return np.asarray(audio, dtype=np.int16).reshape(-1)


def save_clip(out: Path, label: str, session: str, speaker: str, take: np.ndarray, quiet_dbfs: float) -> Path:
    clip = kc.center_on_energy(take, kc.CLIP_SAMPLES)
    path = kc.clip_path(out, label, session, speaker, "pc")
    kc.write_wav(path, clip)
    level = kc.rms_dbfs(clip)
    peak = int(np.max(np.abs(clip.astype(np.int32)))) if len(clip) else 0
    warn = ""
    if peak >= 32000:
        warn = "  [!] clipped - move back or lower the input gain"
    elif label not in (kc.SILENCE,) and level < quiet_dbfs:
        warn = "  [!] very quiet - speak louder or move closer"
    print(f"    saved {path}  rms {level:6.1f} dBFS  peak {peak}{warn}")
    return path


def slice_wav(args) -> int:
    """Cut a long wav (any length, 16 kHz mono 16-bit) into 1.5 s takes, trim, save."""
    pcm = kc.read_wav(args.from_wav)
    step = int(RECORD_SECONDS * kc.SAMPLE_RATE)
    n_saved = 0
    for label in args.labels:
        count = 0
        for start in range(0, len(pcm) - kc.CLIP_SAMPLES + 1, step):
            if count >= args.takes:
                break
            save_clip(args.out, label, args.session, args.speaker, pcm[start:start + step], args.quiet_dbfs)
            count += 1
        n_saved += count
    print(f"Done: {n_saved} clips from {args.from_wav}")
    return n_saved


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("dataset"), help="dataset root (default: dataset)")
    ap.add_argument("--speaker", default="me", help="speaker id, letters/digits/dash only")
    ap.add_argument("--session", default="s01", help="session id like s01 (new room/day = new session)")
    ap.add_argument("--labels", nargs="+", default=kc.KEYWORDS, help=f"labels to record (known: {kc.LABELS})")
    ap.add_argument("--takes", type=int, default=10, help="takes per label")
    ap.add_argument("--device", default=None, help="input device index or name (see --list-devices)")
    ap.add_argument("--no-prompt", action="store_true", help="do not wait for Enter between takes")
    ap.add_argument("--quiet-dbfs", type=float, default=-45.0, help="warn when a keyword clip is quieter")
    ap.add_argument("--from-wav", type=Path, help="slice this wav instead of using the microphone")
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args(argv)

    bad = [lb for lb in args.labels if lb not in kc.LABELS]
    if bad:
        ap.error(f"unknown label(s) {bad}; edit KEYWORDS in kws_common.py to change the vocabulary")
    if not kc.FILENAME_RE.match(f"{args.session}_{args.speaker}_pc_0000.wav"):
        ap.error("session must look like s01 and speaker may contain only letters, digits and '-'")

    if args.from_wav:
        return 0 if slice_wav(args) > 0 else 1

    try:
        import sounddevice as sd
    except OSError as e:  # PortAudio library missing
        print(f"Cannot load sounddevice/PortAudio: {e}\nSee troubleshooting.md -> 'PC microphone'.")
        return 1

    if args.list_devices:
        print(sd.query_devices())
        return 0

    device = int(args.device) if args.device and args.device.isdigit() else args.device
    print(f"Input device: {sd.query_devices(device, 'input')['name']}")
    print(f"Saving to {args.out.resolve()}  (speaker={args.speaker}, session={args.session})")
    for label in args.labels:
        what = {kc.SILENCE: "stay quiet (background noise only)",
                kc.UNKNOWN: "say any OTHER word (not a keyword)"}.get(label, f'say  "{label}"')
        print(f"\n=== {label}: {args.takes} takes - {what}")
        for t in range(args.takes):
            if not args.no_prompt:
                if input(f"  [{t + 1}/{args.takes}] Enter = record, q = quit > ").strip().lower() == "q":
                    return 0
            else:
                time.sleep(0.3)
            print("    recording...", end="", flush=True)
            take = record_take(sd, device)
            print("\r", end="")
            save_clip(args.out, label, args.session, args.speaker, take, args.quiet_dbfs)
    print("\nDone. Next: python train.py --data", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

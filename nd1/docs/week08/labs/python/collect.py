#!/usr/bin/env python3
"""Record labelled 1 s keyword clips from the ES3C28P board microphone over USB.

The board runs the hardware-interface-workshop PREBUILT firmware (the one you
flashed with ``rb flash-bin`` in the workshop) - nothing new to flash. This
script speaks the same wire protocol as the workshop's browser demos (see wire.py):

    1. open the port, wait ~2.5 s (opening USB can reset the board)
    2. read BoardInfo and check caps has MIC (es3c28p = 0x33); ws28p is rejected
    3. MicCmd{enable, gain_pct}            -> CmdAck rc=0
    4. per take: MicCmd{stream:on} -> collect MicPcm chunks (16 kHz int16,
       up to 240 samples each, MicPcm.seq counts 0..255) -> MicCmd{stream:off}
    5. a take with lost chunks (seq gap) is thrown away and re-recorded
    6. keep the loudest 1.0 s and save it

Clips are saved as  <out>/<label>/<session>_<speaker>_board_<index>.wav  - the same
layout as collect_pc_mic.py, so both sources can be mixed in one dataset.
Close the workshop browser tab (Web Serial) first: only one program can own the port.

Examples
    python collect.py --port COM5 --info
    python collect.py --port /dev/ttyACM0 --speaker alice --session s01 --takes 20
    python collect.py --port /dev/cu.usbmodem1101 --labels _silence_ --takes 30 --no-prompt
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

import kws_common as kc
import wire


def record_take(mic: wire.MicStream, seconds: float, rate: int) -> tuple[np.ndarray, int]:
    mic.sess.drain()
    mic.start()
    try:
        pcm, lost = mic.read(int(seconds * rate), timeout=seconds + 3)
    finally:
        mic.stop()
    if rate != kc.SAMPLE_RATE:
        pcm = kc.resample(pcm, rate, kc.SAMPLE_RATE)
    return pcm, lost


def show_info(sess: wire.BoardSession, mic: wire.MicStream, seconds: float = 4.0):
    print("Speak now - AudioLevel from the board (about 10 per second):")
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        mic.pump(0.1)
        if mic.level:
            lv = mic.level
            db = 20 * np.log10(max(lv.rms, 1) / 32767)
            bar = "#" * int(max(0, db + 60) / 2)
            print(f"\r  rms {lv.rms:5d} ({db:6.1f} dBFS) peak {lv.peak:5d}{' CLIP' if lv.clipped else '     '} {bar:<30}",
                  end="", flush=True)
            mic.level = None
    print()
    pcm, lost = record_take(mic, 1.0, mic.rate)
    print(f"1 s test stream: {len(pcm)} samples, {lost} lost chunks, rms {kc.rms_dbfs(pcm):.1f} dBFS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True, help="serial port, e.g. COM5, /dev/ttyACM0, /dev/cu.usbmodem1101")
    ap.add_argument("--out", type=Path, default=Path("dataset"))
    ap.add_argument("--speaker", default="me")
    ap.add_argument("--session", default="s01")
    ap.add_argument("--labels", nargs="+", default=kc.KEYWORDS)
    ap.add_argument("--takes", type=int, default=10)
    ap.add_argument("--gain", type=int, default=60, help="board mic gain 0-100 %% (workshop default 60)")
    ap.add_argument("--seconds", type=float, default=1.5, help="audio recorded per take before trimming to 1 s")
    ap.add_argument("--board-rate", type=int, default=wire.MIC_RATE_HZ,
                    help="sample rate of the board stream (16000 on the prebuilt firmware)")
    ap.add_argument("--no-prompt", action="store_true", help="record continuously without Enter")
    ap.add_argument("--info", action="store_true", help="print BoardInfo + live mic level and exit")
    ap.add_argument("--settle", type=float, default=wire.SETTLE_S, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    bad = [lb for lb in args.labels if lb not in kc.LABELS]
    if bad:
        ap.error(f"unknown label(s) {bad}")
    if not kc.FILENAME_RE.match(f"{args.session}_{args.speaker}_board_0000.wav"):
        ap.error("session must look like s01 and speaker may contain only letters, digits and '-'")

    try:
        sess = wire.BoardSession.open(args.port, settle_s=args.settle)
    except wire.WireError as e:
        print(f"ERROR: {e}")
        return 2
    try:
        info = sess.wait_board_info(need_cap=wire.CAP_MIC, need_name="collect.py (board microphone)")
        print(f"Board: {info.describe()}")
        mic = wire.MicStream(sess, args.board_rate)
        mic.enable(args.gain)
        if args.info:
            show_info(sess, mic)
            return 0

        print(f"Saving to {args.out.resolve()}  (speaker={args.speaker}, session={args.session}, device=board)")
        for label in args.labels:
            what = {kc.SILENCE: "stay quiet (background noise only)",
                    kc.UNKNOWN: "say any OTHER word (not a keyword)"}.get(label, f'say  "{label}"')
            print(f"\n=== {label}: {args.takes} takes - {what}")
            t = 0
            while t < args.takes:
                if not args.no_prompt:
                    if input(f"  [{t + 1}/{args.takes}] Enter = record, q = quit > ").strip().lower() == "q":
                        return 0
                else:
                    print(f"  [{t + 1}/{args.takes}] recording...", flush=True)
                try:
                    take, lost = record_take(mic, args.seconds, args.board_rate)
                except wire.WireError as e:
                    print(f"    [retry] {e}")
                    continue
                if lost:
                    print(f"    [retry] {lost} audio chunk(s) lost on USB (seq gap) - take discarded")
                    continue
                clip = kc.center_on_energy(take, kc.CLIP_SAMPLES)
                path = kc.clip_path(args.out, label, args.session, args.speaker, "board")
                kc.write_wav(path, clip)
                peak = int(np.max(np.abs(clip.astype(np.int32))))
                note = "  [!] clipped - use a lower --gain" if peak >= 32000 else ""
                print(f"    saved {path}  rms {kc.rms_dbfs(clip):6.1f} dBFS  peak {peak}{note}")
                t += 1
    except wire.WrongBoard as e:
        print(f"ERROR: {e}")
        return 3
    except wire.WireError as e:
        print(f"ERROR: {e}")
        return 2
    finally:
        sess.close()
    print("\nDone. Next: python train.py --data", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

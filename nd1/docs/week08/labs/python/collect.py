#!/usr/bin/env python3
"""Record labelled 1 s keyword clips from the ES3C28P board microphone over USB.

Flash ``labs/firmware/audio-logger`` first. The firmware waits for one-byte commands
on the native USB Serial/JTAG port:

    'p'  ping             -> text line  "PONG KWS-LOGGER v1"
    'i'  level info       -> text line  "INFO slot0_dbfs=... slot1_dbfs=... mic_slot=0 gain_db=30.0"
    'r'  record 1.5 s     -> binary frame:
            b"KWS1" | uint32 n_samples | uint32 sample_rate | int16 pcm[n] | uint32 checksum
         (little-endian; checksum = sum of the pcm bytes modulo 2**32)

Clips are trimmed to the loudest 1.0 s and saved as

    <out>/<label>/<session>_<speaker>_board_<index>.wav

which is the same layout as collect_pc_mic.py, so you can mix both sources.

Examples
    python collect.py --port COM5 --ping
    python collect.py --port /dev/ttyACM0 --info
    python collect.py --port /dev/cu.usbmodem1101 --speaker alice --session s01 --takes 20
"""
from __future__ import annotations

import argparse
import struct
import sys
import time
from pathlib import Path

import numpy as np

import kws_common as kc

MAGIC = b"KWS1"


class ProtocolError(RuntimeError):
    pass


def open_port(port: str, baud: int = 115200):
    import serial  # pyserial

    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud          # ignored by USB Serial/JTAG, required by pyserial
    ser.timeout = 0.2
    ser.dtr = False              # do not toggle reset / boot lines when opening
    ser.rts = False
    ser.open()
    time.sleep(0.2)
    ser.reset_input_buffer()
    return ser


def read_line(ser, prefix: str, timeout: float = 3.0) -> str:
    """Return the first text line that starts with prefix (other log lines are skipped)."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        line = ser.readline().decode("utf-8", "replace").strip()
        if line.startswith(prefix):
            return line
    raise ProtocolError(f"no '{prefix}' line within {timeout:.1f} s - is audio-logger flashed?")


def _read_exact(ser, n: int, deadline: float) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        if time.monotonic() > deadline:
            raise ProtocolError(f"timeout: got {len(buf)} of {n} bytes")
        buf += ser.read(n - len(buf))
    return bytes(buf)


def read_frame(ser, timeout: float = 5.0) -> tuple[np.ndarray, int]:
    """Skip any text until the KWS1 magic, then read one audio frame."""
    deadline = time.monotonic() + timeout
    window = b""
    while window != MAGIC:
        b = ser.read(1)
        if time.monotonic() > deadline:
            raise ProtocolError("timeout waiting for KWS1 frame header")
        if b:
            window = (window + b)[-4:]
    n, rate = struct.unpack("<II", _read_exact(ser, 8, deadline))
    if not (0 < n <= 10 * kc.SAMPLE_RATE):
        raise ProtocolError(f"implausible sample count {n}")
    payload = _read_exact(ser, 2 * n, deadline)
    (checksum,) = struct.unpack("<I", _read_exact(ser, 4, deadline))
    if (sum(payload) & 0xFFFFFFFF) != checksum:
        raise ProtocolError("checksum mismatch - bytes were lost or log text was mixed into the stream")
    return np.frombuffer(payload, dtype="<i2").astype(np.int16), rate


def record_take(ser) -> np.ndarray:
    ser.reset_input_buffer()
    ser.write(b"r")
    ser.flush()
    pcm, rate = read_frame(ser)
    if rate != kc.SAMPLE_RATE:
        raise ProtocolError(f"board sends {rate} Hz, expected {kc.SAMPLE_RATE} Hz")
    return pcm


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", required=True, help="serial port, e.g. COM5, /dev/ttyACM0, /dev/cu.usbmodem1101")
    ap.add_argument("--out", type=Path, default=Path("dataset"))
    ap.add_argument("--speaker", default="me")
    ap.add_argument("--session", default="s01")
    ap.add_argument("--labels", nargs="+", default=kc.KEYWORDS)
    ap.add_argument("--takes", type=int, default=10)
    ap.add_argument("--no-prompt", action="store_true", help="record continuously without Enter")
    ap.add_argument("--ping", action="store_true", help="check the firmware and exit")
    ap.add_argument("--info", action="store_true", help="print per-slot microphone level and exit")
    args = ap.parse_args(argv)

    bad = [lb for lb in args.labels if lb not in kc.LABELS]
    if bad:
        ap.error(f"unknown label(s) {bad}")
    if not kc.FILENAME_RE.match(f"{args.session}_{args.speaker}_board_0000.wav"):
        ap.error("session must look like s01 and speaker may contain only letters, digits and '-'")

    ser = open_port(args.port)
    try:
        ser.write(b"p")
        print(read_line(ser, "PONG"))
        if args.ping:
            return 0
        if args.info:
            ser.write(b"i")
            print(read_line(ser, "INFO"))
            print("Speak while running --info: the slot whose level rises is the microphone slot.")
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
                try:
                    take = record_take(ser)
                except ProtocolError as e:
                    print(f"    [retry] {e}")
                    continue
                clip = kc.center_on_energy(take, kc.CLIP_SAMPLES)
                path = kc.clip_path(args.out, label, args.session, args.speaker, "board")
                kc.write_wav(path, clip)
                peak = int(np.max(np.abs(clip.astype(np.int32))))
                note = "  [!] clipped - lower gain_db in the firmware" if peak >= 32000 else ""
                print(f"    saved {path}  rms {kc.rms_dbfs(clip):6.1f} dBFS  peak {peak}{note}")
                t += 1
    finally:
        ser.close()
    print("\nDone. Next: python train.py --data", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

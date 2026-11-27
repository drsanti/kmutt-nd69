"""Example 06: time-domain waveform + level meter ON the ES3C28P screen (no firmware).

An oscilloscope-style sweep (min/max envelope per pixel column, ~2 s per screen) with a
live RMS level bar in dBFS. Tap the waveform to cycle the vertical zoom.

    python examples/06_board_waveform.py                  # board mic  -> board screen
    python examples/06_board_waveform.py pc               # laptop mic -> board screen
    python examples/06_board_waveform.py board COM5 30    # source, port, seconds
"""
import sys
import time

import numpy as np

try:
    import robotos_edge as rk
    from robotos_edge.hardware.display import TOUCH_DOWN
except ImportError:
    print("Install the robotos_edge wheel first (see the lab README).")
    raise

WAVE = dict(x=4, y=68, w=312, h=110)          # waveform plot
METER_X, METER_Y, METER_W, METER_H = 4, 186, 312, 14
ZOOMS = [32767, 8000, 2000, 500]              # full-scale sample value per zoom step


def audio_blocks(source, board):
    """Yield int16 16 kHz blocks from the board mic ("board") or the laptop mic ("pc")."""
    if source == "board":
        yield from board.stream_audio()
        return
    import queue
    import sounddevice as sd

    q = queue.Queue()
    with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=800,
                        callback=lambda data, frames, t, status: q.put(data[:, 0].copy())):
        while True:
            block = q.get()
            board.session.poll(0)              # keep reading the board link (touches, page events)
            yield block


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "board"
    port = sys.argv[2] if len(sys.argv) > 2 else None
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    zoom = {"i": 1}

    with rk.Board(port=port, gain=80) as board:
        def paint(d):
            d.clear()
            d.text(4, 48, f"time domain  zoom x{32767 // ZOOMS[zoom['i']]:<4}  mic: {source}", rk.Color.GRAY)
            scope.full_scale = ZOOMS[zoom["i"]]
            scope.reset()

        disp = rk.Display(board, name="WAVE", hint="robotos_edge example 06")
        scope = rk.WaveformSweep(disp, **WAVE, full_scale=ZOOMS[zoom["i"]])
        disp.on_shown = paint
        paint(disp)
        disp.flush()

        level, t_end, updates, t0 = -90.0, time.monotonic() + seconds, 0, time.monotonic()
        try:
            for block in audio_blocks(source, board):
                rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2))) + 1e-9
                level = max(20 * np.log10(rms / 32768), level - 1.5)      # fast attack, slow release
                if not scope.push(block):
                    continue
                frac = min(max((level + 60) / 60, 0.0), 1.0)              # -60..0 dBFS -> 0..1
                fill = int(frac * METER_W)
                c = rk.Color.GREEN if level < -12 else rk.Color.YELLOW if level < -3 else rk.Color.RED
                disp.fill_rect(METER_X, METER_Y, fill, METER_H, c)
                disp.fill_rect(METER_X + fill, METER_Y, METER_W - fill, METER_H, rk.Color.DARK)
                disp.text(METER_X, METER_Y + METER_H + 2, f"{level:6.1f} dBFS ", rk.Color.WHITE)
                for t in disp.touches():
                    if t.event == TOUCH_DOWN and WAVE["y"] <= t.y < WAVE["y"] + WAVE["h"]:
                        zoom["i"] = (zoom["i"] + 1) % len(ZOOMS)
                        paint(disp)
                        print(f"zoom -> full scale {ZOOMS[zoom['i']]}")
                disp.flush()
                updates += 1
                if time.monotonic() > t_end:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            dt = time.monotonic() - t0
            print(f"{updates} screen updates in {dt:.1f} s ({updates / max(dt, 1e-6):.1f} per s); "
                  f"dropped {scope.dropped_samples / 16000:.1f} s of audio; link: {disp.stats}")
            disp.close()


if __name__ == "__main__":
    main()

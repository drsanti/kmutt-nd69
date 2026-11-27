"""Example 05: live visualization ON the ES3C28P screen, drawn from Python (no firmware).

Shows a sweeping log-mel spectrogram and, if a trained model is found, live keyword
probabilities with a threshold line. Tap the bar area to move the threshold. Switch to
another tab on the board and back: the page repaints itself.

    python examples/05_board_display.py                   # board mic  -> board screen
    python examples/05_board_display.py pc                # laptop mic -> board screen
    python examples/05_board_display.py board COM5 30     # source, port, seconds

Audio source: `board` (default) streams the ES3C28P microphone over USB; `pc` records with
your computer microphone and uses the board only as a display.
"""
import sys
import time
from pathlib import Path

import numpy as np

try:
    import robotos_edge as rk
    from robotos_edge.audio import features as kc
    from robotos_edge.hardware.display import TOUCH_DOWN
except ImportError:
    print("Install the robotos_edge wheel first (see the lab README).")
    raise

SPEC_X, SPEC_Y, SPEC_W, SPEC_H = 4, 50, 156, 80      # spectrogram area (2 px per mel band)
BAR_X, BAR_Y, BAR_W, BAR_H = 162, 50, 156, 168       # probability bars (26 px per bar)
HOP_S = 0.1                                          # screen update period


def find_model():
    for c in ("artifacts/model_int8.tflite", "../artifacts/model_int8.tflite"):
        if Path(c).exists():
            return c
    return None


def audio_blocks(source, board):
    """Yield int16 16 kHz blocks from the laptop mic ("pc") or the board mic ("board")."""
    if source == "board":
        yield from board.stream_audio()
        return
    import queue
    import sounddevice as sd

    q = queue.Queue()
    with sd.InputStream(samplerate=kc.SAMPLE_RATE, channels=1, dtype="int16", blocksize=800,
                        callback=lambda data, frames, t, status: q.put(data[:, 0].copy())):
        while True:
            block = q.get()
            board.session.poll(0)          # keep reading the board link (touches, page events)
            yield block


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "board"
    port = sys.argv[2] if len(sys.argv) > 2 else None
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    model = find_model()
    interp = kc.make_interpreter(model) if model else None
    labels = ["red", "grn", "blu", "off", "sil", "unk"]
    state = {"threshold": 0.8, "col": 0, "probs": np.zeros(len(labels))}

    def paint_static(d):
        d.clear(rk.Color.BLACK)
        d.text(SPEC_X, 136, "log-mel (40)", rk.Color.GRAY)
        d.text(SPEC_X, 154, "model: " + ("int8" if model else "none"), rk.Color.GRAY)
        d.text(SPEC_X, 172, "mic: " + source, rk.Color.GRAY)
        d.text(SPEC_X, 190, f"thr {state['threshold']:.2f} (tap)", rk.Color.YELLOW)   # the yellow line
        state["col"] = 0

    with rk.Board(port=port, gain=80) as board:
        disp = rk.Display(board, name="VIZ", hint="robotos_edge example 05", on_shown=paint_static)
        paint_static(disp)
        disp.flush()
        ring = np.zeros(kc.CLIP_SAMPLES, dtype=np.int16)
        hop_samples = int(kc.SAMPLE_RATE * HOP_S)
        acc = 0
        t_end = time.monotonic() + seconds
        n_frames, t0 = 0, time.monotonic()
        try:
            for block in audio_blocks(source, board):
                ring = np.concatenate([ring[len(block):], block])
                acc += len(block)
                if acc < hop_samples:
                    continue
                acc = 0
                feats = kc.log_mel(ring)                          # 49 frames x 40 bands
                new_cols = feats[-int(HOP_S / 0.02):]             # frames from the last hop
                img = rk.colormap(new_cols.T[::-1], vmin=-8, vmax=6)   # bands x frames, low freq at bottom
                img = np.repeat(img, 2, axis=0)                   # 2 px per band -> 80 px tall
                x = SPEC_X + state["col"]
                w = min(img.shape[1], SPEC_W - state["col"])
                disp.image(x, SPEC_Y, img[:, :w])
                state["col"] = (state["col"] + w) % SPEC_W
                disp.vline(SPEC_X + state["col"], SPEC_Y, SPEC_H, rk.Color.WHITE)   # sweep cursor
                if interp is not None:
                    p = kc.run_tflite(interp, feats)
                    state["probs"] = 0.6 * state["probs"] + 0.4 * p
                    top = int(np.argmax(state["probs"]))
                    disp.bars(state["probs"], labels, BAR_X, BAR_Y, BAR_W, BAR_H,
                              threshold=state["threshold"],
                              highlight=top if top < 4 and state["probs"][top] >= state["threshold"] else None)
                for t in disp.touches():
                    plot_h = BAR_H - 36                       # bars() leaves two 16 px label rows + 4 px
                    if t.event == TOUCH_DOWN and t.x >= BAR_X and BAR_Y <= t.y < BAR_Y + plot_h:
                        state["threshold"] = 1 - (t.y - BAR_Y) / plot_h
                        disp.text(SPEC_X, 190, f"thr {state['threshold']:.2f} (tap)", rk.Color.YELLOW)
                        print(f"threshold -> {state['threshold']:.2f}")
                disp.flush()
                n_frames += 1
                if time.monotonic() > t_end:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            dt = time.monotonic() - t0
            print(f"{n_frames} screen updates in {dt:.1f} s ({n_frames / max(dt, 1e-6):.1f} per s); link: {disp.stats}")
            disp.close()


if __name__ == "__main__":
    main()

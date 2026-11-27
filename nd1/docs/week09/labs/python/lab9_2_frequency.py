"""Lab 9.2 — Frequency domain: spectrum of a motion, and what the gesture model sees.

Takes one 2 s window (100 samples at 50 Hz) per gesture, computes the magnitude spectrum of
|a|, finds the dominant frequency, and shows the normalised 100 x 6 window the model gets.

    python lab9_2_frequency.py                         # the 4 sample gestures in samples/
    python lab9_2_frequency.py --replay imu_dataset/shake/s01_me_ws28p_0000.csv   # your own take (collect-imu)
"""
from pathlib import Path

import numpy as np

import robotos_edge as rk
from robotos_edge.imu import features as ic
from lab_common import intro, parse_args, replay_files

FS = 50.0                                   # sample rate (Hz)


def spectrum(a_mag):
    """Return (freqs_hz, magnitude) of one window of |a| samples."""
    # TODO 1: remove the mean (gravity, 0 Hz) and take the magnitude of the real FFT
    mag = np.zeros(len(a_mag) // 2 + 1)
    # TODO 2: the frequency (Hz) of each FFT bin; the last one must be FS / 2 (Nyquist)
    freqs = np.arange(len(mag), dtype=float)
    return freqs, mag


def main():
    args = parse_args(__doc__)
    intro(__doc__, args,
          do='Nothing to do: it analyses the 4 recordings in samples/ (or the files after --replay) and opens a plot window.',
          look='The dominant frequency of each gesture (printed, and a red line in the plot): shake peaks near 11.5 Hz. The bottom row is exactly what the gesture model receives (100 samples x 6 channels).')
    if args.replay is None:
        args.replay = []
    files = replay_files(args)
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, len(files), figsize=(3.2 * len(files), 6), squeeze=False)
    for k, f in enumerate(files):
        win = np.array([s.accel + s.gyro for s in rk.ImuReplay(f, realtime=False)])[: ic.WINDOW]
        a_mag = np.sqrt((win[:, :3] ** 2).sum(axis=1))
        freqs, mag = spectrum(a_mag)
        # TODO 3: the dominant frequency in Hz (ignore bin 0, the leftover DC)
        peak_hz = 0.0
        name = Path(f).stem
        print(f"{name:8s} dominant {peak_hz:5.2f} Hz   resolution {freqs[1]:.2f} Hz   Nyquist {freqs[-1]:.1f} Hz")
        axes[0, k].plot(freqs, mag)
        axes[0, k].axvline(peak_hz, color="r", ls="--")
        axes[0, k].set_title(f"{name}: peak {peak_hz:.1f} Hz")
        axes[0, k].set_xlabel("Hz")
        axes[1, k].imshow(ic.normalise(win).T, aspect="auto", cmap="viridis", vmin=-2, vmax=2)
        axes[1, k].set_yticks(range(6), ic.CHANNELS)
        axes[1, k].set_xlabel("sample (model input)")
    fig.suptitle("Lab 9.2 — spectrum of |a| (top) and the model's normalised 100 x 6 window (bottom)")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
